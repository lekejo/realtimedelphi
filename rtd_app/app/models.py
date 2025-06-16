from datetime import datetime
from app import db, bcrypt # Import bcrypt
from flask_login import UserMixin # Import UserMixin

class User(db.Model, UserMixin): # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    studies = db.relationship('Study', backref='admin', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Study(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.relationship('Question', backref='study', lazy='dynamic', cascade="all, delete-orphan")
    participants = db.relationship('Participant', backref='study', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Study {self.title}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(64), nullable=False)  # 'scale' or 'open_ended'
    scale_min = db.Column(db.Integer, nullable=True) # Only for 'scale' type
    scale_max = db.Column(db.Integer, nullable=True) # Only for 'scale' type
    answers = db.relationship('Answer', backref='question', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Question {self.text[:30]}...>'

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    access_code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    status = db.Column(db.String(64), default='invited') # e.g., 'invited', 'started', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='participant', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Participant {self.access_code}>'

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    numerical_response = db.Column(db.Integer, nullable=True)
    text_response = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Answer q:{self.question_id} p:{self.participant_id}>'
