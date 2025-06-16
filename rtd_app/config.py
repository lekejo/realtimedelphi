import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db') # Default for dev
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory DB for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for simpler form tests (if using Flask-WTF)
    SERVER_NAME = 'localhost.localdomain' # Required for url_for outside app context in tests
    DEBUG = False # Ensure debug is false for tests unless specifically testing debug features
    LOGIN_DISABLED = False # Ensure login is enabled for testing auth, can be overridden
    BCRYPT_LOG_ROUNDS = 4 # Speed up bcrypt hashing for tests
