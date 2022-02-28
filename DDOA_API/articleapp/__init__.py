from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from decouple import config
from flask_migrate import Migrate
from flask_mail import Mail
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.secret_key = 'secret123'

app.config['SQLALCHEMY_DATABASE_URI'] =  'postgresql://dpcuxqokeraxpg:2e3ee32cd8a1fe075ff5016c9fe4cfbf6f2799b402cd2a657e9917dcd2446786@ec2-3-217-216-13.compute-1.amazonaws.com:5432/d73nk51puivj4b'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'adarshrawat71@gmail.com'
app.config['MAIL_PASSWORD'] = 'rzdpcujmitoxjtdj'
#app.config['UPLOAD_FOLDER'] = config('UPLOAD_FOLDER')


mail = Mail(app)

from articleapp import routes
