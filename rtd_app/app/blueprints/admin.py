from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, jsonify
from app import db, bcrypt # Import bcrypt
from app.models import Study, User, Question, Participant, Answer
from datetime import datetime
from sqlalchemy import func
import uuid
import pandas as pd
import io
from collections import Counter
from flask_login import login_user, logout_user, login_required, current_user # Login imports

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# AUTHENTICATION ROUTES
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.list_studies'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.list_studies'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

# PROTECTED ROUTES START HERE
@admin_bp.route('/')
@admin_bp.route('/studies')
@login_required
def list_studies():
    studies = Study.query.all()
    return render_template('admin/studies.html', studies=studies)

@admin_bp.route('/studies/create', methods=['GET', 'POST'])
@login_required
def create_study():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        errors = {}
        if not title:
            errors['title'] = 'Title is required.'

        start_date, end_date = None, None
        if not start_date_str:
            errors['start_date'] = 'Start Date is required.'
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                errors['start_date'] = 'Invalid Start Date format. Please use YYYY-MM-DD.'

        if not end_date_str:
            errors['end_date'] = 'End Date is required.'
        else:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                errors['end_date'] = 'Invalid End Date format. Please use YYYY-MM-DD.'

        if start_date and end_date and start_date >= end_date:
            errors['end_date'] = 'End Date must be after Start Date.'

        if errors:
            for field, msg in errors.items():
                flash(msg, 'danger')
            return render_template('admin/create_study.html', title=title, description=description,
                                   start_date=start_date_str, end_date=end_date_str, errors=errors)

        new_study = Study(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            admin_id=current_user.id # Use logged-in user's ID
        )
        db.session.add(new_study)
        db.session.commit()
        flash('Study created successfully!', 'success')
        return redirect(url_for('admin.list_studies'))

    return render_template('admin/create_study.html')

@admin_bp.route('/studies/<int:study_id>')
@login_required
def study_detail(study_id):
    study = Study.query.get_or_404(study_id)
    questions = study.questions.all()
    participants = study.participants.all()
    return render_template('admin/study_detail.html', study=study, questions=questions, participants=participants)

@admin_bp.route('/studies/<int:study_id>/questions/add', methods=['GET', 'POST'])
@login_required
def add_question(study_id):
    study = Study.query.get_or_404(study_id)
    if request.method == 'POST':
        text = request.form.get('text')
        question_type = request.form.get('question_type')
        scale_min_str = request.form.get('scale_min')
        scale_max_str = request.form.get('scale_max')

        if not text or not question_type:
            flash('Question text and type are required.', 'error')
            return render_template('admin/add_question.html', study=study)

        new_question = Question(study_id=study.id, text=text, question_type=question_type)

        if question_type == 'scale':
            if not scale_min_str or not scale_max_str:
                flash('Scale Min and Scale Max are required for scale questions.', 'error')
                return render_template('admin/add_question.html', study=study, current_text=text, current_type=question_type)
            try:
                scale_min = int(scale_min_str)
                scale_max = int(scale_max_str)
                if scale_min >= scale_max:
                    flash('Scale Min must be less than Scale Max.', 'error')
                    return render_template('admin/add_question.html', study=study, current_text=text, current_type=question_type, current_min=scale_min_str, current_max=scale_max_str)
                new_question.scale_min = scale_min
                new_question.scale_max = scale_max
            except ValueError:
                flash('Scale Min and Scale Max must be integers.', 'error')
                return render_template('admin/add_question.html', study=study, current_text=text, current_type=question_type)

        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.study_detail', study_id=study.id))

    return render_template('admin/add_question.html', study=study)

@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    study_id = question.study_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.study_detail', study_id=study_id))

@admin_bp.route('/studies/<int:study_id>/participants/generate', methods=['POST'])
@login_required
def generate_participants(study_id):
    study = Study.query.get_or_404(study_id)
    try:
        number_of_participants = int(request.form.get('number_of_participants'))
        if number_of_participants <= 0:
            raise ValueError("Number of participants must be a positive integer.")
    except (ValueError, TypeError):
        flash('Invalid number of participants. Please enter a positive integer.', 'error')
        return redirect(url_for('admin.study_detail', study_id=study_id))

    generated_count = 0
    for _ in range(number_of_participants):
        # Basic attempt to ensure access_code is unique.
        # For very high numbers of participants or studies, a more robust check might be needed.
        access_code = str(uuid.uuid4())[:8]
        while Participant.query.filter_by(access_code=access_code).first():
             access_code = str(uuid.uuid4())[:8] # Regenerate if collision (rare)

        participant = Participant(study_id=study.id, access_code=access_code)
        db.session.add(participant)
        generated_count += 1

    if generated_count > 0:
        db.session.commit()
        flash(f'{generated_count} new participant(s) generated successfully.', 'success')
    else:
        flash('No new participants were generated.', 'info')

    return redirect(url_for('admin.study_detail', study_id=study_id))


@admin_bp.route('/studies/<int:study_id>/results')
@login_required
def study_results(study_id):
    study = Study.query.get_or_404(study_id)
    questions = Question.query.filter_by(study_id=study.id).order_by(Question.id).all()

    chart_data = {}
    qualitative_data = {}

    for q in questions:
        # Qualitative data for all question types
        text_responses_query = db.session.query(Answer.text_response)\
            .join(Participant, Answer.participant_id == Participant.id)\
            .filter(Participant.study_id == study.id)\
            .filter(Answer.question_id == q.id)\
            .filter(Answer.text_response.isnot(None))\
            .filter(func.length(Answer.text_response) > 0)\
            .all()
        qualitative_data[q.id] = [r[0] for r in text_responses_query]

        if q.question_type == 'scale':
            numerical_responses_query = db.session.query(Answer.numerical_response)\
                .join(Participant, Answer.participant_id == Participant.id)\
                .filter(Participant.study_id == study.id)\
                .filter(Answer.question_id == q.id)\
                .filter(Answer.numerical_response.isnot(None))\
                .all()

            response_values = [r[0] for r in numerical_responses_query]
            if response_values:
                freq_dist = Counter(response_values)
                labels = list(range(q.scale_min, q.scale_max + 1)) # Ensure all scale values are labels
                counts = [freq_dist.get(label, 0) for label in labels]
                chart_data[q.id] = {'labels': labels, 'data': counts,
                                    'scale_min': q.scale_min, 'scale_max': q.scale_max}
            else: # Still provide structure for chart if no responses yet
                 labels = list(range(q.scale_min, q.scale_max + 1))
                 counts = [0] * len(labels)
                 chart_data[q.id] = {'labels': labels, 'data': counts,
                                    'scale_min': q.scale_min, 'scale_max': q.scale_max}


    return render_template('admin/results.html',
                           study=study,
                           questions=questions,
                           chart_data=chart_data,
                           qualitative_data=qualitative_data)

@admin_bp.route('/studies/<int:study_id>/results/export')
@login_required
def export_study_results(study_id):
    study = Study.query.get_or_404(study_id)

    answers_data = db.session.query(
        Answer.id.label('answer_id'),
        Answer.numerical_response,
        Answer.text_response,
        Answer.last_updated.label('answer_last_updated'), # Alias for clarity
        Participant.access_code.label('participant_access_code'),
        Question.id.label('question_id'),
        Question.text.label('question_text'),
        Question.question_type
    ).join(Participant, Answer.participant_id == Participant.id)\
     .join(Question, Answer.question_id == Question.id)\
     .filter(Participant.study_id == study_id)\
     .order_by(Participant.access_code, Question.id)\
     .all()

    if not answers_data:
        flash('No results to export for this study yet.', 'info')
        # Redirect to results page as it will show "no data" messages
        return redirect(url_for('admin.study_results', study_id=study_id))

    df = pd.DataFrame(answers_data) # SQLAlchemy Core result is directly compatible

    # Reorder for better readability if needed, though direct labels are good
    # df = df[['participant_access_code', 'question_id', 'question_text',
    #          'question_type', 'numerical_response', 'text_response',
    #          'answer_last_updated', 'answer_id']]

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)

    return Response(
        csv_buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename=study_{study.id}_{study.title.replace(' ','_').replace(':','-')}_results.csv"}
    )
