from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_restful import Api
from flask_admin import Admin
from flaskblog.admin import CustomModelView

from flaskblog.celery import make_celery
from flaskblog.config import Config
from celery import Celery
celery = Celery('flaskblog', broker='redis://localhost:6379/0')


db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()
ext_celery = FlaskCeleryExt(create_celery_app=make_celery) # Create the celery app
api = Api()
admin = Admin()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)
    ext_celery.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    api.init_app(app)
    admin.init_app(app)
    from flaskblog.users.routes import users
    from flaskblog.events.routes import events
    from flaskblog.main.routes import main
    from flaskblog.errors.handlers import errors
    from flaskblog.api.routes import restfulapi
    app.register_blueprint(users)
    app.register_blueprint(events)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    app.register_blueprint(restfulapi)

    from flaskblog.models import User, Event, Worker, Organizer, Worker_Event, BlackList
    admin.add_view(CustomModelView(User, db.session))
    admin.add_view(CustomModelView(Event, db.session))
    admin.add_view(CustomModelView(Worker, db.session))
    admin.add_view(CustomModelView(Organizer, db.session))
    admin.add_view(CustomModelView(Worker_Event, db.session))
    admin.add_view(CustomModelView(BlackList, db.session))
    return app

