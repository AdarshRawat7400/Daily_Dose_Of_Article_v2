from articleapp.models import Users,Articles

from slugify import slugify 
import jwt
from werkzeug.utils import secure_filename
from datetime import datetime , timedelta
import secrets
import os
from articleapp import app,db,mail,ma
from passlib.hash import sha256_crypt
from functools import wraps
from flask import  (render_template,flash, redirect,jsonify,
                    url_for,request, session, logging,)
from flask_mail import Message
from flask_marshmallow import Marshmallow


class ArticleSchema(ma.Schema):
    class Meta:
        fields = ('id','title','body','author','created_at','updated_at','slug')

article_schema = ArticleSchema()
articles_schema = ArticleSchema(many=True)

def token_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
       token = None
       if 'x-access-tokens' in request.headers:
           token = request.headers['x-access-tokens']
 
       if not token:
           return jsonify({'message': 'a valid token is missing'})
       try:
           data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
           current_user = Users.query.filter_by(id=data['id']).first()
           
       except:
           return jsonify({'message': 'token is invalid'})
 
       return f(current_user, *args, **kwargs)
   return decorator

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)

    return picture_fn


@app.route('/api/login',methods=['GET','POST'])
def login():
    d = request.get_json()
    username = d['username']
    password = d['password']
    user = Users.query.filter_by(username=username).first()
    if user and sha256_crypt.verify(password,user.password):
        token = jwt.encode({'id' : user.id, 'exp' : datetime.utcnow() + timedelta(minutes=45)}, app.config['SECRET_KEY'], "HS256")
        return {'status':'success','id':user.id,'token':token}
    else:
        return {'status':'username or password is incorrect'}


@app.route('/api/register',methods=['GET','POST'])
def register():
    d = request.get_json()
    name = d['name']
    username = d['username']
    password = d['password']
    email = d['email']
    user = Users.query.filter_by(username=username).first()
    if user:
        return {'status':'username already exists'}
    else:
        user = Users(name=name,username=username,password=sha256_crypt.hash(password),email=email)
        db.session.add(user)
        db.session.commit()
        return {'status':'success'}

@app.route('/api/update_profile',methods=['GET','POST'])
@token_required
def update_profile(current_user):
    d = request.get_json()
    id = d['id']
    name = d['name']
    username = d['username']
    email = d['email']
    filename = d['filename']
    

    user = Users.query.filter_by(id=id).first()

    if user.username != username and Users.query.filter_by(username=username).first() is not None:
        error = f'username "{username}"  already exists'
        return {'status':error}
    elif user.email != email and Users.query.filter_by(email=email).first() is not None:
        error = f'email "{email}"  already exists'
        return {'status':error}

    else:
        # if filename != '':
        #         profile_file = save_picture(fill)
        #         user.profile_img = profile_file
        
        Articles.query.filter_by(author=user.username).update(dict(author=user.username))
        user.name = name
        user.username = username
        user.email = email
        db.session.commit()
        return {'status':'success'}
    

@app.route('/api/add_article',methods=['GET','POST'])
@token_required
def add_article(current_user):
    d = request.get_json()
    title = d['title']
    body = d['body']
    username = d['author']
    user = Articles.query.filter_by(author=username).first()
    article = Articles.query.filter_by(slug=slugify(title)).first()
    if article:
        return {'status':'Article title is already taken'}
    
    article = Articles(title=title,body=body,author=username,slug=slugify(title))
    db.session.add(article)
    db.session.commit()
    return {'status':'success'}
    

@app.route('/api/edit_article',methods=['GET','POST'])
@token_required
def edit_article(current_user):
    d = request.get_json()
    id = d['id']
    title = d['title']
    body = d['body']
    article = Articles.query.filter_by(id=id).first()
    if article.slug != slugify(title) and Articles.query.filter_by(slug=slugify(title)).first():
            error = f'Article with title: "{title}" already exists','danger'
            return {'status':error}
    else:
        article.title = title
        article.body = body
        article.slug = slugify(title)
        article.updated_at = datetime.now()
        db.session.commit()
        
        return {'status':'success'}



@app.route('/api/delete_article',methods=['GET','POST'])
@token_required
def delete_article(current_user):
    d = request.get_json()
    slug = d['slug']
    article = Articles.query.filter_by(slug=slug).first()
    db.session.delete(article)
    db.session.commit()
    return {'status':'success'}
    

@app.route('/api/user_articles',methods=['GET','POST'])
@token_required
def user_articles(current_user):
    d = request.get_json()
    username = d['username']
    articles = Articles.query.filter_by(author=username).all()
    
    articles = articles_schema.dump(articles)
    

    return {'articles':articles,'status':'success'}


@app.route('/api/get_article',methods=['GET','POST'])
def get_article():
    d = request.get_json()
    slug = d['slug']
    article = Articles.query.filter_by(slug=slug).first()
    
    article = article_schema.dump(article)
    return {'article':article}
    

@app.route('/api/get_all_articles',methods=['GET','POST'])
def get_all_articles():
    articles = Articles.query.all()
    articles = articles_schema.dump(articles)
    return {'articles':articles}


@app.route('/api/get_user',methods=['GET','POST'])
@token_required
def get_user(current_user):
    d = request.get_json()
    id = d['id']

    user = Users.query.filter_by(id=id).first()
    user = {'id':user.id,'username':user.username,'email':user.email,'name':user.name,'profile_img':user.profile_img}
    return {'user':user}



def send_reset_email(user):
    token = user.get_reset_token()
    # {url_for('change_user_password',token=token,_external=True)}
    url = 'http://127.0.0.1:5000/change_user_password/'+token
    message = Message('Password Reset Request',
                sender='noreply@demo.com',
                recipients=[user.email])
    message.body = f'''To reset your password, visit the following link:
{url}
If you did not make this request ,then simply ignore this email,and  no changes will be made.
'''
    mail.send(message)



@app.route('/api/verify_reset_token',methods=['GET','POST'])
def verify_reset_token():
    token = request.get_json()['token']
    
    user = Users.verify_reset_token(token)
    if user is None:
        print("INVALID USER")
        return {'status':'Invalid or expired token'}
    else:
        return {'status':'success'}



@app.route('/api/request_password_reset',methods=['GET','POST'])
def request_password_reset():
    d = request.get_json()
    email = d['email']
    user = Users.query.filter_by(email=email).first()
    if user is None:
        error = f'No account with that email {email} address exists.'
        return {'status':error}
    else:
        token = user.get_reset_token()
        send_reset_email(user)
        msg = f'An email has been sent to {email} with instructions to reset your password.'
        return {'status':'success','msg':msg}


@app.route('/api/change_password',methods=['GET','POST'])
def change_password():
    d = request.get_json()
    
    token = d['token']
    password = d['password']
    user = Users.verify_reset_token(token)
    print("IM HERE")
    if user is None:
        error = f'Invalid or expired token'
        return {'status':error}
    else:
        user.password = sha256_crypt.hash(password)
        db.session.commit()
        return {'status':'success'}
