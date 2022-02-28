from pydoc import resolve
from this import d
from articleapp.forms import( RegisterForm,LoginForm,
                            ArticleForm,RequestPasswordResetForm,
                            UpdateArticleForm,ResetPasswordForm,UpdateProfileForm)
from slugify import slugify 

from werkzeug.utils import secure_filename
from datetime import datetime
import secrets
import os
from articleapp import app
from passlib.hash import sha256_crypt
from functools import wraps
from flask import  (render_template,flash, redirect,
                    url_for,request, session, logging)
from flask_mail import Message
import requests as req
from datetime import datetime
import base64

#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for('login'))
    return wrap

# class UserSchema(ma.ModelSchema):
#     class Meta:
#         model = Users
#         fields = ('id','name','username','email','filename','fill')

# user_schema = UserSchema()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


    
@app.route('/article/<string:id>/<string:slug>')
# @is_logged_in
def article(id,slug):
   profile_img  = 'default.jpg'
   response = req.get('http://127.0.0.1:5050/api/get_article',json = {'slug':slug})
   
   article = response.json()['article']
   article_data = {
            'id':article['id'],
            'title':article['title'],
            'body':article['body'],
            'author':article['author'],
            'created_at':article['created_at'],
            'slug':article['slug'],
            
   }
   return render_template('article.html',article=article_data,profile_img=profile_img)


####################MODIFIED CODE#############################
@app.route('/articles')
def articles():
        return render_template('articles.html')


@app.route('/api/data',methods=['GET'])
def data():
    data = []

    response = req.get('http://127.0.0.1:5050/api/get_all_articles')
    articles = response.json()['articles']
    for article in articles:
        url = url_for('article',id=article['id'],slug=article['slug'])
        title = f"<a href='{url}'>{article['title']}<a/>"

        data.append({
            'id':article['id'],
            'title':title,
            'author':article['author'],
            'updated_at':   article['updated_at']

        })
    return {'data': data}

####################MODIFIED CODE#############################

@app.route('/register',methods=['GET','POST'])
def register():
    form  = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        data = {
        'name' : form.name.data,
        'email' : form.email.data,
        'username' : form.username.data,
        'password' : form.password.data,
        }
       
        response = req.post('http://127.0.0.1:5050/api/register',json=data)

        status =  response.json()['status']
        
        if status == 'success':
            flash('You are now registered and can login','success')
            return redirect(url_for('login'))
        else:
            error = response.json()['status']
            flash(error,'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html',form=form)


@app.route('/update_profile/<string:id>',methods=['GET','POST'])
@app.route('/update_profile',methods=['GET','POST'])
@is_logged_in
def update_profile(id=None):
    
    id = session['id']
    
    form = UpdateProfileForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        fill = request.files['file']
        filename = secure_filename(fill.filename)
        
        # print("TYPE OF FILENAME :-",type(filename))
        # print("FILENAME :-",type(fill))

        data = {
            'id': id,
            'name' : form.name.data,
            'email' : form.email.data,
            'username' : form.username.data,
            'filename' : filename,  
        }
        headers = {'x-access-tokens': session['token']}
        response = req.post('http://127.0.0.1:5050/api/update_profile',json=data,headers=headers)
        
        if response.json().get('message'):
            flash(response.json().get('message'),'danger')
            session.clear()
            return redirect(url_for('login'))
        

        status = response.json()['status']
        if status == 'success':
            flash('Your profile has been updated','success')
            return redirect(url_for('dashboard'))
        else:
            error = response.json()['status']
            flash(f"{error}",'danger')
            return redirect(url_for('update_profile',id=id))
    
    data = {'id':id}
    headers = {'x-access-tokens': session['token']}
    response = req.get('http://127.0.0.1:5050/api/get_user',json=data,headers=headers)
    if response.json().get('message'):
            flash(response.json().get('message'),'danger')
            session.clear()
            return redirect(url_for('login'))
        
    user = response.json()['user']
    image_file = url_for('static', filename='profile_pics/' + user['profile_img'])
    form = UpdateProfileForm(request.form)
    form.name.data = user['name']
    form.email.data = user['email']
    form.username.data =  user['username']
    form.profile_img.data = user['profile_img']
    return render_template('update_profile.html',form=form,image_file=image_file)


@app.route('/login',methods=['GET','POST'])
def login():

    form = LoginForm(request.form)
    
    if request.method == 'POST' and form.validate():
        
        username = form.username.data
        password_candidate = form.password.data
        response = req.post('http://127.0.0.1:5050/api/login',json={'username':username,'password':password_candidate})
        data = response.json()
       
        if data['status'] == 'success':
            session['logged_in'] = True
            session['username'] = username
            session['token'] = data['token']
            session['id'] = data['id']
            flash('You are now logged in','success')
            return redirect(url_for('dashboard'))

        else:
            error  = data['status']
            return render_template('login.html',error=error,form=form)

    return render_template('login.html',form=form)




@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are not logged out","success")
    return redirect(url_for('login'))



@app.route('/dashboard')
@is_logged_in
def dashboard():

    username = session['username']
    headers = {'x-access-tokens': session['token']}
    response = req.get('http://127.0.0.1:5050/api/user_articles',json={'username':username},headers=headers)
    # print("Type of Article is ",type(articles))
    if response.json().get('message'):
            flash(response.json().get('message'),'danger')
            session.clear()
            return redirect(url_for('login'))

    articles = response.json()['articles']  


    if response.json()['status'] == 'success':
        return render_template('dashboard.html',articles=articles)
    else:
        msg = response.json()['status']
        return render_template('dashboard.html',articles=articles)




# Add Article
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        username = session['username']
        data = {'title':title,'body':body,'author':username}
        #execute query
        headers = {'x-access-tokens': session['token']}
        response = req.post('http://127.0.0.1:5050/api/add_article',json=data,headers=headers)

        if response.json().get('message'):
            flash(response.json().get('message'),'danger')
            session.clear()
            return redirect(url_for('add_article'))

        if response.json()['status'] == 'success':
            flash('Article Created Successfully','success')
            return redirect(url_for('dashboard'))
        else:
            error = response.json()['status']
            return render_template('add_article.html',form=form,error=error)

    return render_template('add_article.html',form=form)


# Edit Article
@app.route('/edit_article/<string:id>/<string:slug>',methods=['GET','POST'])
@is_logged_in
def edit_article(id,slug):
    

    response = req.get('http://127.0.0.1:5050/api/get_article',json={'slug':slug})
    article = response.json()['article']

    
    form = UpdateArticleForm(request.form)

    # populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == "POST" and form.validate():
        data = {
        'title' : request.form['title'],
        'body'  : request.form['body'],
        'username' : session['username'],
        'id' : id
        }
        headers = {'x-access-tokens': session['token']}
        response = req.post('http://127.0.0.1:5050/api/edit_article',json=data,headers=headers)
        
        if response.json().get('message'):
            flash(response.json().get('message'),'danger')
            session.clear()
            return redirect(url_for('login'))
        

        if response.json()['status'] == 'success':
            print("Im HERE in success")
            flash('Article Updated','success')
            return redirect(url_for('dashboard'))
        else:
            print("IM HERE in failure")
            error = response.json()['status']
            flash(error,'danger')
            return redirect(url_for('edit_article',id=id,slug=slug))
    
    return render_template('edit_article.html',form=form)


# Delete Article
@app.route('/delete_article/<string:id>/<string:slug>',methods=['POST'])
@is_logged_in
def delete_article(id,slug):
    # delete article with id
    headers = {'x-access-tokens': session['token']}
    response = req.post('http://127.0.0.1:5050/api/delete_article',json={'slug':slug},headers=headers)
    if response.json().get('message'):
            flash(response.json().get('message'),'danger')
            session.clear()
            return redirect(url_for('login'))
        
    if response.json()['status'] == 'success':
        flash('Article Deleted Successfully','success')
        return redirect(url_for('dashboard'))
    else:      
        return render_template('dashboard.html')
    




@app.route('/change_user_password/<string:token>/',methods=['GET','POST'])
def change_user_password(token):
    
    response = req.get('http://127.0.0.1:5050/api/verify_reset_token',json={'token':token})
    form  = ResetPasswordForm(request.form)
    
    if response.json()['status'] == 'success':
        if form.validate_on_submit():
            password = form.password.data
            data = {'token':token,'password':password}
            response = req.post('http://127.0.0.1:5050/api/verify_reset_token',json={'token':token})
            
        
            if response.json()['status'] == 'success':
                flash('Password Changed Successfully','success')
                response = req.post('http://127.0.0.1:5050/api/change_password',json={'token':token,'password':password})
                if response.json()['status'] == 'success':
                    flash('Password Changed Successfully','success')
                    return redirect(url_for('login'))
                else:
                    error = response.json()['status']
                    flash(error,'danger')
                    return redirect(url_for('request_password_reset'))

    return render_template('reset_password.html',form=form)
                



@app.route('/request_password_reset',methods=['GET','POST'])
def request_password_reset():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    form = RequestPasswordResetForm(request.form)
    if form.validate_on_submit():
       response = req.post('http://127.0.0.1:5050/api/request_password_reset',json={'email':form.email.data})
        
       if response.json()['status'] == 'success':
            msg = response.json()['msg']
            flash(msg,'success')
            return redirect(url_for('login'))
       else:
            error = response.json()['status']
            flash(error,'danger')
            return redirect(url_for('request_password_reset'))

    return render_template('request_password_reset.html',form=form)
 


@app.route('/reset_password/<string:token>',methods=['GET','POST'])
def reset_password(token):

    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        headers = {'x-access-tokens': session['token']}
        response = req.get('http://127.0.0.1:5050/api/verify_reset_token',json={'token':token})
        
        
        if response.json()['status'] == 'success':
            form = ResetPasswordForm()  
            if form.validate_on_submit():
                
                response = req.post('http://127.0.0.1:5050/api/change_password',json={'password':form.password.data,'token':token})

                if response.json()['status'] == 'success':
                    msg = response.json()['status']
                    flash(msg,'success')
                    return redirect(url_for('change_user_password',token=token))
                else:
                    error = response.json()['status']
                    flash(error,'danger')
                    return redirect(url_for('request_password_reset'))           
                
        else:
            error = response.json()['status']
            flash(error,'danger')
            return redirect(url_for('request_password_reset'))
            
    response = req.get('http://127.0.0.1:5050/api/verify_reset_token',json={'token':token})

        
    if response.json()['status'] == 'success':
        return render_template('reset_password.html',token=token)
    else:
        error = response.json()['status']
        flash(error,'danger')
        return redirect(url_for('request_password_reset'))
        
 
    
