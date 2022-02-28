from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from decouple import config
from flask_migrate import Migrate
from flask_mail import Mail
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.secret_key = 'secret123'

app.config['SQLALCHEMY_DATABASE_URI'] =  ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
#app.config['UPLOAD_FOLDER'] = config('UPLOAD_FOLDER')


mail = Mail(app)

from articleapp import routes
