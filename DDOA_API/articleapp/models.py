from email.policy import default
from articleapp import db,app
from datetime import datetime
import jwt
import time
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from slugify import slugify 
from sqlalchemy import event

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    profile_img = db.Column(db.String(500), nullable=False, default='default.jpg')
    register_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    
    

####### Using TimedJSONWebSignatureSerializer ####################

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)

    def get_reset_token(self, expires_sec=900):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
#################################################################



#### Using JWT Token ####

    # def get_reset_token(self, expires_sec=900):
    #     return jwt.encode({'reset_password': self.username, 'exp': time.time() + expires_sec},
    #                        key=app.config['SECRET_KEY'])

    # @staticmethod
    # def verify_reset_token(token):
    #     try:
    #         username = jwt.decode(token, key=app.config['SECRET_KEY'])['reset_password']
    #         print(username)
    #     except Exception as e:
    #         print(e)
    #         return
    #     return Users.query.filter_by(username=username).first()
####################################################################

class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    author = db.Column(db.String(100))
    body   = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime,default=datetime.now())
    slug = db.Column(db.String(200), unique=True, nullable=False)


    def __repr__(self):
        return '<Article %r>' % self.title
    
    @staticmethod
    def generate_slug(target, value, oldvalue, initiator):
        if value and (not oldvalue or value != oldvalue):
            target.slug = slugify(value)
    
db.event.listen(Articles.title, 'set', Articles.generate_slug, retval=False)
        
    