from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session as flask_session
from flask_login import login_required, current_user
from datetime import date
from sqlalchemy import text
from app import db
from app.models import WorkoutSession, StrengthLog, Exercise, PersonalRecord, WorkoutTemplate


def parse_decimal(value):
    """Parse decimal number accepting both comma (5,54) and period (5.54)."""
    if value is None or value == '':
        return None
    try:
        # Replace comma with period for European format
        cleaned = str(value).replace(',', '.')
        return float(cleaned)
    except (ValueError, TypeError):
        return None

workouts_bp = Blueprint('workouts', __name__)


def check_strength_volume_spike(user_id):
    """Check for strength volume spikes."""
    try:
        result = db.session.execute(
            text('SELECT * FROM check_strength_volume_spike(:user_id) WHERE is_spike = true LIMIT 3'),
            {'user_id': user_id}
        ).fetchall()

        alerts = []
        for row in result:
            alerts.append({
                'muscle_group': row.muscle_group,
                'increase_percent': float(row.increase_percent),
                'current_volume': float(row.current_volume),
                'previous_volume': float(row.previous_volume)
            })
        return alerts
    except Exception:
        return []


@workouts_bp.route('/')
@login_required
def index():
    """List workout sessions."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    sessions = WorkoutSession.query.filter_by(
        user_id=current_user.user_id,
        session_type='upper_body'
    ).order_by(
        WorkoutSession.session_date.desc()
    ).paginate(page=page, per_page=per_page)

    return render_template('workouts/index.html', sessions=sessions)


@workouts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_session():
    """Start a new workout session."""
    if request.method == 'POST':
        session_date = request.form.get('session_date', date.today())
        notes = request.form.get('notes', '')
        template_id = request.form.get('template_id', type=int)

        # Check for existing session today
        existing = WorkoutSession.get_today_session(
            current_user.user_id,
            session_type='upper_body'
        )

        if existing and str(existing.session_date) == str(session_date):
            flash('You already have a session for this date. Continue logging there.', 'info')
            return redirect(url_for('workouts.log_exercise', session_id=existing.session_id))

        # Create new session
        session = WorkoutSession(
            user_id=current_user.user_id,
            session_date=session_date,
            session_type='upper_body',
            notes=notes
        )
        db.session.add(session)
        db.session.commit()

        # If template selected, store it in flask session for pre-loading
        if template_id:
            flask_session['active_template_id'] = template_id
            flash('Workout started with template!', 'success')
        else:
            flask_session.pop('active_template_id', None)
            flash('Workout session started!', 'success')

        return redirect(url_for('workouts.log_exercise', session_id=session.session_id))

    # GET request
    exercises = Exercise.get_strength_exercises()
    templates = WorkoutTemplate.get_user_templates(current_user.user_id)

    # Check if template_id passed in URL (from template view page)
    preselected_template = request.args.get('template', type=int)

    return render_template(
        'workouts/new_session.html',
        exercises=exercises,
        today=date.today(),
        templates=templates,
        preselected_template=preselected_template
    )


@workouts_bp.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    """View a workout session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    logs = session.strength_logs.all()

    return render_template('workouts/view_session.html', session=session, logs=logs)


@workouts_bp.route('/session/<int:session_id>/log', methods=['GET', 'POST'])
@login_required
def log_exercise(session_id):
    """Log exercises to a session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    just_logged = False  # Track if a set was just logged (for auto-starting rest timer)

    if request.method == 'POST':
        exercise_id = request.form.get('exercise_id', type=int)
        sets = request.form.get('sets', type=int)
        reps = request.form.get('reps', type=int)
        reps_list = request.form.get('reps_list', '')  # Comma-separated reps for each set
        weight_kg = parse_decimal(request.form.get('weight_kg'))
        rpe = request.form.get('rpe', type=int)
        rest_seconds = request.form.get('rest_seconds', type=int)
        warmup_sets = request.form.get('warmup_sets', type=int) or 0
        template_exercise_id = request.form.get('template_exercise_id', type=int)

        if not all([exercise_id, sets, reps]):
            flash('Exercise, sets, and reps are required.', 'error')
        else:
            # Parse reps_list into individual set reps
            individual_reps = []
            if reps_list:
                individual_reps = [int(r.strip()) for r in reps_list.split(',') if r.strip().isdigit()]

            # Get previous PR before logging
            previous_pr = PersonalRecord.get_exercise_pr(
                current_user.user_id, exercise_id, '1RM'
            )
            previous_pr_value = float(previous_pr.value) if previous_pr else None

            best_estimated_1rm = 0
            logs_created = []

            # Create individual log entries for each working set
            if individual_reps and len(individual_reps) == sets:
                for set_num, set_reps in enumerate(individual_reps, start=1):
                    log = StrengthLog(
                        session_id=session_id,
                        exercise_id=exercise_id,
                        sets=1,
                        reps=set_reps,
                        weight_kg=weight_kg,
                        rpe=rpe,
                        rest_seconds=rest_seconds,
                        warmup_sets=warmup_sets if set_num == 1 else 0,
                        template_exercise_id=template_exercise_id,
                        set_number=set_num
                    )
                    db.session.add(log)
                    logs_created.append(log)
                    if log.estimated_1rm and log.estimated_1rm > best_estimated_1rm:
                        best_estimated_1rm = log.estimated_1rm
            else:
                # Fallback: single batch log (all same reps)
                log = StrengthLog(
                    session_id=session_id,
                    exercise_id=exercise_id,
                    sets=sets,
                    reps=reps,
                    weight_kg=weight_kg,
                    rpe=rpe,
                    rest_seconds=rest_seconds,
                    warmup_sets=warmup_sets,
                    template_exercise_id=template_exercise_id,
                    set_number=None
                )
                db.session.add(log)
                logs_created.append(log)
                best_estimated_1rm = log.estimated_1rm or 0

            db.session.commit()

            just_logged = True  # Set was logged successfully

            # Check for PR using best 1RM from all sets
            pr_data = None
            if weight_kg and best_estimated_1rm:
                is_pr = PersonalRecord.check_and_update_pr(
                    user_id=current_user.user_id,
                    exercise_id=exercise_id,
                    record_type='1RM',
                    new_value=best_estimated_1rm,
                    date_achieved=session.session_date
                )
                if is_pr:
                    exercise = Exercise.query.get(exercise_id)
                    pr_data = {
                        'exercise_name': exercise.name,
                        'new_value': best_estimated_1rm,
                        'previous_value': previous_pr_value,
                        'improvement': round(best_estimated_1rm - previous_pr_value, 1) if previous_pr_value else None
                    }
                    flash(f'PR_DATA:{pr_data["exercise_name"]}:{pr_data["new_value"]}:{pr_data["previous_value"] or 0}', 'pr')
                else:
                    flash('Sets logged successfully.', 'success')
            else:
                flash('Sets logged successfully.', 'success')

    exercises = Exercise.get_strength_exercises()
    current_logs = session.strength_logs.all()

    # Check for volume spikes
    volume_spikes = check_strength_volume_spike(current_user.user_id)

    # Check for active template
    template_data = None
    active_template_id = flask_session.get('active_template_id')
    if active_template_id:
        template = WorkoutTemplate.query.get(active_template_id)
        if template and template.user_id == current_user.user_id:
            template_data = {
                'id': template.template_id,
                'name': template.name,
                'exercises': template.get_exercises_with_last_performance(current_user.user_id)
            }

    return render_template(
        'workouts/log_exercise.html',
        session=session,
        exercises=exercises,
        current_logs=current_logs,
        volume_spikes=volume_spikes,
        just_logged=just_logged,
        template_data=template_data
    )


@workouts_bp.route('/session/<int:session_id>/finish', methods=['POST'])
@login_required
def finish_session(session_id):
    """Finish a workout session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    duration = request.form.get('duration_minutes', type=int)
    notes = request.form.get('notes', '')

    session.duration_minutes = duration
    session.notes = notes
    db.session.commit()

    flash('Workout completed!', 'success')
    return redirect(url_for('workouts.view_session', session_id=session_id))


@workouts_bp.route('/exercise/<int:exercise_id>/history')
@login_required
def exercise_history(exercise_id):
    """View history for an exercise."""
    exercise = Exercise.query.get_or_404(exercise_id)
    history = StrengthLog.get_exercise_history(current_user.user_id, exercise_id, limit=20)
    best_1rm = StrengthLog.get_best_1rm(current_user.user_id, exercise_id)

    return render_template(
        'workouts/exercise_history.html',
        exercise=exercise,
        history=history,
        best_1rm=best_1rm
    )


@workouts_bp.route('/exercise/<int:exercise_id>/substitutes')
@login_required
def get_substitutes(exercise_id):
    """Get exercise substitutes with last performance (for AJAX)."""
    exercise = Exercise.query.get_or_404(exercise_id)
    substitutes = exercise.get_substitutes_with_history(current_user.user_id)

    return jsonify({
        'exercise': exercise.name,
        'substitutes': substitutes
    })


@workouts_bp.route('/exercise/<int:exercise_id>/last-performance')
@login_required
def last_performance(exercise_id):
    """Get last performance for an exercise (for AJAX)."""
    last = StrengthLog.get_last_performance(current_user.user_id, exercise_id)

    if last:
        return jsonify({
            'found': True,
            'sets': last.sets,
            'reps': last.reps,
            'weight_kg': float(last.weight_kg) if last.weight_kg else None,
            'rpe': last.rpe,
            'date': str(last.session.session_date)
        })

    return jsonify({'found': False})


@workouts_bp.route('/log/<int:log_id>/delete', methods=['POST'])
@login_required
def delete_log(log_id):
    """Delete a strength log entry (or multiple if log_ids provided)."""
    # Check for multiple log IDs (grouped sets deletion)
    log_ids_str = request.form.get('log_ids', '')
    if log_ids_str:
        log_ids = [int(lid) for lid in log_ids_str.split(',') if lid.strip().isdigit()]
    else:
        log_ids = [log_id]

    session_obj = None
    for lid in log_ids:
        log = StrengthLog.query.get(lid)
        if log:
            if log.session.user_id != current_user.user_id:
                flash('Access denied.', 'error')
                return redirect(url_for('workouts.index'))
            session_obj = log.session
            db.session.delete(log)

    db.session.commit()

    flash('Log entry deleted.', 'success')
    if session_obj:
        return redirect(url_for('workouts.log_exercise', session_id=session_obj.session_id))
    return redirect(url_for('workouts.index'))


@workouts_bp.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    """Delete a workout session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    db.session.delete(session)
    db.session.commit()

    flash('Workout session deleted.', 'success')
    return redirect(url_for('workouts.index'))
