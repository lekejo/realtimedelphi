from app.models import User, Study
from datetime import datetime, timedelta

def test_user_password_hashing(db): # db fixture provides app_context
    u = User(username='test_model_user')
    u.set_password('supersecret')
    db.session.add(u)
    db.session.commit() # Commit to ensure it's in the DB for querying if needed

    assert u.password_hash is not None
    assert u.check_password('supersecret')
    assert not u.check_password('incorrect')

def test_study_creation_and_relationships(db): # db fixture
    # Assumes 'testadmin' user is created by the app fixture in conftest.py
    admin_user = User.query.filter_by(username='testadmin').first()
    assert admin_user is not None, "Test admin user not found. Check conftest.py app fixture."

    study_title = "Ethical AI Study"
    s = Study(
        title=study_title,
        description="A study on the ethics of AI development.",
        start_date=datetime.utcnow() - timedelta(days=1), # ensure start date is in past
        end_date=datetime.utcnow() + timedelta(days=30),
        admin_id=admin_user.id
    )
    db.session.add(s)
    db.session.commit()

    assert s.id is not None
    assert s.title == study_title
    assert s.admin == admin_user
    assert s.admin_id == admin_user.id

    # Check relationship back from user
    admin_studies = admin_user.studies.all()
    assert s in admin_studies
    assert len(admin_studies) >= 1 # Could be other studies if db is not perfectly isolated per test.
                                  # For in-memory SQLite, this should be fine.

# Add more model tests here, e.g. for Question, Participant, Answer relationships
# and specific model logic if any.
# For example, testing default values or specific constraints.

def test_participant_defaults(db):
    admin_user = User.query.filter_by(username='testadmin').first()
    study = Study(title="Participant Default Study", admin_id=admin_user.id,
                  start_date=datetime.utcnow(), end_date=datetime.utcnow() + timedelta(days=1))
    db.session.add(study)
    db.session.commit()

    participant = study.participants.first() # Example if a relationship auto-creates or if we add one
    # For now, let's create one
    from app.models import Participant # Local import if not at top
    p = Participant(study_id=study.id, access_code="DEF456")
    db.session.add(p)
    db.session.commit()

    assert p.status == 'invited' # Check default status
    assert p.access_code == "DEF456"
    assert p.created_at is not None
    assert p.study == study
