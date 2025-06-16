from app import create_app, db, bcrypt, socketio # Import create_app, socketio, db, bcrypt
from app.models import User
import click
from flask.cli import with_appcontext
import os

# Create app instance using the factory
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@click.command('create-admin')
@click.argument('username')
@click.argument('password')
@with_appcontext # Ensures app context is available
def create_admin_command(username, password):
    """Creates a new admin user."""
    if User.query.filter_by(username=username).first():
        click.echo(f'User {username} already exists.')
        return

    # bcrypt is initialized with app, so it's fine here.
    # db is also fine due to with_appcontext.
    admin = User(username=username)
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()
    click.echo(f'Admin user {username} created successfully.')

# Add command to the Flask app instance
app.cli.add_command(create_admin_command)

if __name__ == '__main__':
    # Use the socketio instance that was initialized with the app
    socketio.run(app, debug=app.config.get('DEBUG', True))
