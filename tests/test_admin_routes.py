import pytest
from flask import url_for
from app.models import User, Study # Assuming User and Study might be needed

# Basic test: can we reach the login page?
def test_admin_login_page_loads(client):
    response = client.get(url_for('admin.login'))
    assert response.status_code == 200
    assert b"Administrator Login" in response.data # Check for a known string on the login page

# Test that protected admin pages redirect to login if not authenticated
def test_admin_dashboard_redirects_unauthenticated(client):
    response = client.get(url_for('admin.list_studies'), follow_redirects=True)
    # After redirection, we should land on the login page
    assert response.status_code == 200
    assert b"Administrator Login" in response.data
    # Check current path after redirect
    assert request.path == url_for('admin.login')

# Test login functionality
def test_admin_login_successful(client, db, app): # use app fixture for context if needed for User.query
    # 'testadmin' user is created in conftest.py app fixture
    response = client.post(url_for('admin.login'), data={
        'username': 'testadmin',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check for content expected on the admin dashboard (list_studies)
    assert b"Studies" in response.data
    assert b"Create New Study" in response.data
    # Check that we are NOT on the login page anymore
    assert b"Administrator Login" not in response.data
    # Check path is admin dashboard
    assert request.path == url_for('admin.list_studies')


def test_admin_login_failure(client):
    response = client.post(url_for('admin.login'), data={
        'username': 'wronguser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Login Unsuccessful" in response.data # Check for flash error message
    assert b"Administrator Login" in response.data # Should remain on login page


def test_admin_logout(client, login_test_user):
    login_test_user('testadmin', 'password') # Log in the user first

    # Check if actually logged in by trying to access a protected page
    response_check_login = client.get(url_for('admin.list_studies'))
    assert response_check_login.status_code == 200
    assert b"Create New Study" in response_check_login.data # dashboard content

    # Perform logout
    response_logout = client.get(url_for('admin.logout'), follow_redirects=True)
    assert response_logout.status_code == 200
    assert b"You have been logged out" in response_logout.data # Flash message
    assert b"Administrator Login" in response_logout.data # Should be on login page

    # Verify access to protected page is now denied
    response_after_logout = client.get(url_for('admin.list_studies'), follow_redirects=True)
    assert b"Administrator Login" in response_after_logout.data


# Test for create_study route (GET and POST)
def test_create_study_page_loads_authenticated(client, login_test_user):
    login_test_user('testadmin', 'password')
    response = client.get(url_for('admin.create_study'))
    assert response.status_code == 200
    assert b"Create New Study" in response.data

def test_create_study_successful_submission(client, login_test_user, db, app):
    login_test_user('testadmin', 'password')

    # Get the logged-in user from the database
    with app.app_context(): # Ensure app context for db query
        admin_user = User.query.filter_by(username='testadmin').first()
        assert admin_user is not None

    initial_study_count = Study.query.count()

    response = client.post(url_for('admin.create_study'), data={
        'title': 'My New Test Study',
        'description': 'This is a detailed description.',
        'start_date': '2024-01-01',
        'end_date': '2024-01-31'
    }, follow_redirects=True)

    assert response.status_code == 200 # Should redirect to list_studies
    assert b"Study created successfully!" in response.data
    assert request.path == url_for('admin.list_studies')

    with app.app_context(): # Ensure app context for db query
        assert Study.query.count() == initial_study_count + 1
        new_study = Study.query.filter_by(title='My New Test Study').first()
        assert new_study is not None
        assert new_study.admin_id == admin_user.id

def test_create_study_validation_errors(client, login_test_user):
    login_test_user('testadmin', 'password')

    # Test empty title
    response_no_title = client.post(url_for('admin.create_study'), data={
        'title': '',
        'description': 'Description here',
        'start_date': '2024-01-01',
        'end_date': '2024-01-31'
    }, follow_redirects=True)
    assert response_no_title.status_code == 200 # Stays on create_study page
    assert b"Title is required." in response_no_title.data
    assert b"Create New Study" in response_no_title.data # Still on the same page

    # Test end date before start date
    response_date_error = client.post(url_for('admin.create_study'), data={
        'title': 'Date Error Study',
        'description': 'Description',
        'start_date': '2024-02-01',
        'end_date': '2024-01-01' # End date before start date
    }, follow_redirects=True)
    assert response_date_error.status_code == 200
    assert b"End Date must be after Start Date." in response_date_error.data
    assert b"Create New Study" in response_date_error.data


# Example test for CLI command (create-admin)
def test_create_admin_command(runner, app):
    with app.app_context(): # Ensure app context for db operations
        # Check if user already exists (from conftest)
        existing_admin = User.query.filter_by(username='testadmin').first()
        assert existing_admin is not None

        # Try to create existing user
        result_exists = runner.invoke(args=['create-admin', 'testadmin', 'newpass'])
        assert 'User testadmin already exists.' in result_exists.output

        # Create a new admin
        result_new = runner.invoke(args=['create-admin', 'newadmintest', 'securepass123'])
        assert 'Admin user newadmintest created successfully.' in result_new.output
        new_admin = User.query.filter_by(username='newadmintest').first()
        assert new_admin is not None
        assert new_admin.check_password('securepass123')

        # Clean up: remove the newly created admin to keep db state consistent if needed
        # db.session.delete(new_admin)
        # db.session.commit() # This is usually handled by test isolation / db teardown

# Need to import 'request' for path checking
from flask import request
