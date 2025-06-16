from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from app import db, socketio # Import socketio
from flask_socketio import join_room, leave_room # Import specific socketio functions
from app.models import Participant, Study, Question, Answer
from datetime import datetime
from sqlalchemy import func # For aggregate functions
import numpy as np # For median calculation

survey_bp = Blueprint('survey', __name__, url_prefix='/survey')


# Socket.IO event handlers
@socketio.on('join_study_room')
def handle_join_study_room(data):
    study_id = data.get('study_id')
    if study_id:
        join_room(str(study_id)) # Rooms are typically strings

@socketio.on('leave_study_room')
def handle_leave_study_room(data):
    study_id = data.get('study_id')
    if study_id:
        leave_room(str(study_id))

@survey_bp.route('/<access_code>', methods=['GET', 'POST'])
def display_and_submit_questionnaire(access_code):
    participant = Participant.query.filter_by(access_code=access_code).first()

    if not participant:
        flash('Invalid or expired access code.', 'error')
        return render_template('survey/invalid_access.html', message="Invalid or expired access code."), 404

    study = Study.query.get(participant.study_id)

    if not study:
        flash('Associated study not found. Please contact administrator.', 'error')
        return render_template('survey/invalid_access.html', message="Associated study not found. Please contact administrator."), 500

    questions = study.questions.order_by(Question.id).all()

    if not questions and request.method == 'GET': # Only show "no questions" if GET, POST might be an error
        return render_template('survey/invalid_access.html', message="This study currently has no questions. Please check back later."), 200

    if request.method == 'POST':
        if not questions: # Should not happen if study setup is correct
            flash('Cannot submit answers, study has no questions.', 'error')
            return redirect(url_for('survey.display_and_submit_questionnaire', access_code=access_code))

        answers_changed = False
        for question in questions:
            numerical_response_str = request.form.get(f'numerical_q_{question.id}')
            text_response = request.form.get(f'text_q_{question.id}')

            numerical_response = None
            if numerical_response_str is not None and numerical_response_str.strip() != '':
                try:
                    numerical_response = int(numerical_response_str)
                    if question.question_type == 'scale': # Validate against scale if applicable
                        if not (question.scale_min <= numerical_response <= question.scale_max):
                            flash(f"Answer for question '{question.text[:30]}...' is outside the allowed scale ({question.scale_min}-{question.scale_max}).", 'error')
                            # Continue to save other answers, or redirect immediately:
                            # return redirect(url_for('survey.display_and_submit_questionnaire', access_code=access_code))
                            numerical_response = None # Do not save invalid numerical response
                except ValueError:
                    flash(f"Invalid numerical input for question '{question.text[:30]}...'. Please enter a whole number.", 'error')
                    # Continue or redirect
                    numerical_response = None # Do not save invalid

            # Check if there's any data to save for this question
            if numerical_response is not None or (text_response is not None and text_response.strip() != ''):
                existing_answer = Answer.query.filter_by(
                    participant_id=participant.id,
                    question_id=question.id
                ).first()

                if existing_answer:
                    changed_locally = False
                    if existing_answer.numerical_response != numerical_response:
                        existing_answer.numerical_response = numerical_response
                        changed_locally = True
                    if existing_answer.text_response != text_response:
                        existing_answer.text_response = text_response
                        changed_locally = True
                    if changed_locally:
                        existing_answer.last_updated = datetime.utcnow()
                        answers_changed = True
                else:
                    new_answer = Answer(
                        participant_id=participant.id,
                        question_id=question.id,
                        numerical_response=numerical_response,
                        text_response=text_response
                    )
                    db.session.add(new_answer)
                    answers_changed = True

        if answers_changed:
            if participant.status == 'invited':
                participant.status = 'started'
            # Add logic for 'completed' status later if needed
            # For example, check if all questions have an answer
            # all_answered = True
            # for q in questions:
            #     ans = Answer.query.filter_by(participant_id=participant.id, question_id=q.id).first()
            #     if not ans or (q.question_type == 'scale' and ans.numerical_response is None) and (not ans.text_response):
            #         all_answered = False
            #         break
            # if all_answered:
            #    participant.status = 'completed'

            db.session.commit()
            flash('Your answers have been saved successfully!', 'success')
        else:
            flash('No changes detected in your answers.', 'info')

        return redirect(url_for('survey.display_and_submit_questionnaire', access_code=access_code))


    if request.method == 'POST':
        # ... (existing POST logic for saving answers)
        # Ensure 'answers_changed' is correctly determined
        answers_changed = False # This needs to be properly set by the answer saving logic

        # Simplified version of answer saving for brevity in this diff
        # Assume answers are processed and 'answers_changed' is set.
        # This part should effectively be the same as the prior version's POST block,
        # but with the commit and emit logic carefully placed.

        # --- Start of example answer processing (replace with full logic) ---
        _processed_questions_in_post = set()
        for question in questions:
            numerical_response_str = request.form.get(f'numerical_q_{question.id}')
            text_response = request.form.get(f'text_q_{question.id}')
            # ... (validation and conversion logic as before) ...
            numerical_response = None
            if numerical_response_str and numerical_response_str.strip():
                try:
                    numerical_response = int(numerical_response_str)
                    # ... (scale validation) ...
                except ValueError:
                    pass # Flash error

            if numerical_response is not None or (text_response and text_response.strip()):
                _processed_questions_in_post.add(question.id)
                existing_answer = Answer.query.filter_by(participant_id=participant.id, question_id=question.id).first()
                if existing_answer:
                    if existing_answer.numerical_response != numerical_response or existing_answer.text_response != text_response:
                        existing_answer.numerical_response = numerical_response
                        existing_answer.text_response = text_response
                        existing_answer.last_updated = datetime.utcnow()
                        answers_changed = True
                else:
                    db.session.add(Answer(participant_id=participant.id, question_id=question.id, numerical_response=numerical_response, text_response=text_response))
                    answers_changed = True

        if answers_changed:
            if participant.status == 'invited':
                participant.status = 'started'
            db.session.commit() # Commit changes to make them visible for stat recalculation
            flash('Your answers have been saved successfully!', 'success')

            # Emit updates for all questions in the study, as any could be affected by new global stats
            for q_to_update in questions:
                feedback_payload = _get_updated_feedback_for_question(
                    study.id,
                    q_to_update.id,
                    participant.id # Exclude this participant's new/updated reason from immediate broadcast
                )
                if feedback_payload:
                    # print(f"Emitting for study {study.id}, question {q_to_update.id}")
                    socketio.emit('feedback_updated', feedback_payload, room=str(study.id))
        else:
            flash('No changes detected in your answers.', 'info')

        return redirect(url_for('survey.display_and_submit_questionnaire', access_code=access_code))

    # --- End of POST ---

    # --- Start of GET ---
    participant_answers = Answer.query.filter_by(participant_id=participant.id).all()
    answers_map = {ans.question_id: ans for ans in participant_answers}

    group_stats_map = {}
    qualitative_feedback_map = {}
    if questions: # Only try to load feedback if there are questions
        for question_to_load in questions:
            _load_question_feedback_data(study.id, question_to_load.id, participant.id, group_stats_map, qualitative_feedback_map)

    return render_template('survey/questionnaire.html',
                           participant=participant,
                           study=study,
                           questions=questions,
                           answers_map=answers_map,
                           group_stats_map=group_stats_map,
                           qualitative_feedback_map=qualitative_feedback_map)
    # --- End of GET ---


def _get_updated_feedback_for_question(study_id, question_id, current_participant_id_to_exclude):
    """
    Helper function to calculate and return updated feedback for a specific question.
    This will be used for Socket.IO emissions.
    """
    question = Question.query.get(question_id)
    if not question:
        return None

    # Calculate group stats
    stats_data = {'count': 0, 'average': None, 'median': None}
    if question.question_type == 'scale':
        all_responses = db.session.query(Answer.numerical_response)\
            .join(Participant, Answer.participant_id == Participant.id)\
            .filter(Participant.study_id == study_id)\
            .filter(Answer.question_id == question_id)\
            .filter(Answer.numerical_response.isnot(None))\
            .all()
        numerical_values = [r[0] for r in all_responses]
        if numerical_values:
            stats_data['count'] = len(numerical_values)
            stats_data['average'] = np.mean(numerical_values)
            stats_data['median'] = np.median(numerical_values)

    # Fetch anonymous qualitative reasons (excluding the specified participant)
    text_responses = db.session.query(Answer.text_response)\
        .join(Participant, Answer.participant_id == Participant.id)\
        .filter(Participant.study_id == study_id)\
        .filter(Answer.question_id == question_id)\
        .filter(Answer.participant_id != current_participant_id_to_exclude)\
        .filter(Answer.text_response.isnot(None))\
        .filter(func.length(Answer.text_response) > 0)\
        .all()
    reasons_for_others = [r[0] for r in text_responses]

    return {
        'question_id': question_id,
        'stats': stats_data,
        'reasons': reasons_for_others
    }

def _load_question_feedback_data(study_id, question_id, current_participant_id, group_stats_map_ref, qualitative_feedback_map_ref):
    """
    Helper to load initial feedback data for a question for the GET request.
    Qualitative feedback here IS for the current user (shows all others).
    """
    question = Question.query.get(question_id)
    if not question: return

    if question.question_type == 'scale':
        all_responses = db.session.query(Answer.numerical_response)\
            .join(Participant, Answer.participant_id == Participant.id)\
            .filter(Participant.study_id == study_id)\
            .filter(Answer.question_id == question_id)\
            .filter(Answer.numerical_response.isnot(None)).all()
        numerical_values = [r[0] for r in all_responses]
        if numerical_values:
            group_stats_map_ref[question_id] = {
                'count': len(numerical_values),
                'average': np.mean(numerical_values),
                'median': np.median(numerical_values)
            }
        else:
            group_stats_map_ref[question_id] = {'count': 0, 'average': None, 'median': None}

    text_responses = db.session.query(Answer.text_response)\
        .join(Participant, Answer.participant_id == Participant.id)\
        .filter(Participant.study_id == study_id)\
        .filter(Answer.question_id == question_id)\
        .filter(Answer.participant_id != current_participant_id)\
        .filter(Answer.text_response.isnot(None))\
        .filter(func.length(Answer.text_response) > 0).all()
    qualitative_feedback_map_ref[question_id] = [r[0] for r in text_responses]


# In the POST part of display_and_submit_questionnaire, after db.session.commit():
# ... (inside the `if request.method == 'POST':` block)
# After `db.session.commit()`
#
#         if answers_changed: # only emit if something actually changed
#             # For each question that might have been affected by this user's save
#             # (i.e., all questions they submitted an answer for)
#             # We need to re-calculate stats and reasons *for others*
#             # and emit this to the study room.
#
#             # Determine which questions were actually part of this submission
#             # For simplicity, let's assume all questions in the study could be affected
#             # if we don't track which specific ones were submitted in this POST.
#             # A more optimized way would be to check which answers were new/changed.
#
#             for question_in_study in questions:
#                 updated_feedback = _get_updated_feedback_for_question(
#                     study.id,
#                     question_in_study.id,
#                     participant.id # Exclude this participant's reasons from the broadcast
#                 )
#                 if updated_feedback:
#                     socketio.emit('feedback_updated', updated_feedback, room=str(study.id))
#
# ... the rest of the POST handling (redirect)
# This change needs to be integrated into the existing POST logic carefully.
# The stub above is a conceptual placement. Let's refine the actual POST handler.

# Refined POST handling section within display_and_submit_questionnaire:

    # if request.method == 'POST':
    #     ... (existing POST logic up to db.session.commit()) ...
    #     if answers_changed:
    #         db.session.commit() # Commit first to make data available for re-query
    #         flash('Your answers have been saved successfully!', 'success')

    #         # Emit updates for all questions in the study
    #         for q_to_update in questions:
    #             feedback_payload = _get_updated_feedback_for_question(
    #                 study.id,
    #                 q_to_update.id,
    #                 participant.id # Exclude this participant's new/updated reason from immediate broadcast to self via this channel
    #             )
    #             if feedback_payload:
    #                 socketio.emit('feedback_updated', feedback_payload, room=str(study.id))
    #     else:
    #         flash('No changes detected in your answers.', 'info')
    #     return redirect(url_for('survey.display_and_submit_questionnaire', access_code=access_code))

# The above comments show where the new emit logic should go.
# I will now integrate it into the actual function.
# The actual modification will be a replacement of the POST block.
# The GET block also needs the _load_question_feedback_data helper.
