from flask import Flask
from rtd_app.config import Config, TestingConfig # Import TestingConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Initialize extensions globally but without an app instance yet
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    # Models need to be imported here or ensure models.py doesn't depend on 'app' directly at import time
    from .models import User
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    app = Flask(__name__)

    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config) # Default configuration

    # Initialize extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import models here if they depend on db being initialized with app
    # or ensure models.py can be imported earlier if structured carefully.
    # from . import models # This might cause circular import if models import 'db' from here at top level

    # Register blueprints
    from .blueprints.admin import admin_bp
    app.register_blueprint(admin_bp)

    from .blueprints.survey import survey_bp
    app.register_blueprint(survey_bp)

    # Security Headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # Basic route
    @app.route('/')
    def index():
        return "Hello, RTD!"

    return app
