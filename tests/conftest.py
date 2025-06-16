import pytest
from app import create_app, db as _db, bcrypt as _bcrypt # Use create_app
from app.models import User
from rtd_app.config import TestingConfig # Import TestingConfig directly

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    _app = create_app(config_name='testing') # Use the factory with testing config

    with _app.app_context():
        _db.create_all()

        if not User.query.filter_by(username='testadmin').first():
            # Use User's set_password method which uses bcrypt from the app context
            test_admin = User(username='testadmin')
            test_admin.set_password('password') # bcrypt is app-context aware now
            _db.session.add(test_admin)
            _db.session.commit()

        if not User.query.filter_by(username='testuser').first():
            test_user = User(username='testuser')
            test_user.set_password('password123')
            _db.session.add(test_user)
            _db.session.commit()

    yield _app # Use the app created by the factory

    with _app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app): # app fixture is now correctly configured
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app): # app fixture provides the correct context
    """Function-scoped test database."""
    with app.app_context():
        yield _db
        # No need to clean up here if using in-memory SQLite, as it's per session.
        # If tests were modifying a persistent DB and function scope was desired for db changes,
        # then _db.session.rollback() or specific deletions would go here.

@pytest.fixture(scope='function') # runner should also be function scoped if client is
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def login_test_user(client, db, app): # Added app to ensure context for user creation if needed
    # db fixture already provides app_context for its operations
    def _login(username='testadmin', password='password'):
        # User should exist from app fixture setup, but check just in case or for flexibility
        user = User.query.filter_by(username=username).first()
        if not user:
            # This part is tricky if bcrypt isn't available or app_context not set for set_password
            # However, User.set_password uses bcrypt instance from app, which should be fine
            # as long as 'app' context is active or bcrypt was init'd with an app.
            # The `db` fixture ensures an app_context for its yield.
            with app.app_context(): # Explicitly ensure context for user creation
                user = User(username=username)
                user.set_password(password) # This needs bcrypt from an app
                _db.session.add(user)
                _db.session.commit()

        return client.post('/admin/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    return _login
