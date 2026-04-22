from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO

#configure Flask with config.py file
app = Flask(__name__)
app.config.from_object(Config)

#configure websockets
socketio = SocketIO(app)

#initialize database and migration logic via SQLAlchemy and Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#initialize Flasks login manager
login = LoginManager(app)
login.login_view = 'login'

#import the routes, models and sockets modules at the bottom so referencing doesn't lead to errors
from app import routes, models, sockets
