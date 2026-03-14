from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from app.models import WorkoutSession, StrengthLog, RunningLog, PersonalRecord, RecoveryLog

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page."""
    user_id = current_user.user_id

    # Get stats
    stats = get_dashboard_stats(user_id)

    # Recent workouts
    recent_workouts = WorkoutSession.get_user_sessions(user_id, limit=5)

    # Recent PRs
    recent_prs = PersonalRecord.get_recent_prs(user_id, limit=5)

    # Today's recovery
    today_recovery = RecoveryLog.get_today_log(user_id)

    # Weekly recovery average
    recovery_avg = RecoveryLog.get_weekly_average(user_id)

    # Check for volume spikes
    volume_alerts = check_volume_spikes(user_id)

    return render_template(
        'dashboard/index.html',
        stats=stats,
        recent_workouts=recent_workouts,
        recent_prs=recent_prs,
        today_recovery=today_recovery,
        recovery_avg=recovery_avg,
        volume_alerts=volume_alerts,
        now=datetime.now()
    )


def get_dashboard_stats(user_id):
    """Calculate dashboard statistics."""
    from app import db
    from sqlalchemy import func

    # Current week boundaries
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Total workouts
    total_workouts = WorkoutSession.query.filter_by(user_id=user_id).count()

    # Workouts this week
    workouts_this_week = WorkoutSession.query.filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.session_date >= week_start
    ).count()

    # Strength sessions this week
    strength_this_week = WorkoutSession.query.filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.session_date >= week_start,
        WorkoutSession.session_type == 'upper_body'
    ).count()

    # Running sessions this week
    running_this_week = WorkoutSession.query.filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.session_date >= week_start,
        WorkoutSession.session_type == 'running'
    ).count()

    # Weekly running distance
    weekly_distance = RunningLog.get_weekly_mileage(user_id)

    # Weekly volume (strength)
    weekly_volume = db.session.query(
        func.sum(StrengthLog.sets * StrengthLog.reps * StrengthLog.weight_kg)
    ).join(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.session_date >= week_start
    ).scalar() or 0

    # Consistency streak
    streak = calculate_streak(user_id)

    return {
        'total_workouts': total_workouts,
        'workouts_this_week': workouts_this_week,
        'strength_this_week': strength_this_week,
        'running_this_week': running_this_week,
        'weekly_distance': round(weekly_distance, 2),
        'weekly_volume': round(float(weekly_volume), 0),
        'streak': streak,
        'strength_target': current_user.weekly_strength_target or 2,
        'running_target': current_user.weekly_running_target or 4
    }


def calculate_streak(user_id):
    """Calculate workout streak (days with workout, allowing 1 rest day)."""
    sessions = WorkoutSession.query.filter_by(user_id=user_id).order_by(
        WorkoutSession.session_date.desc()
    ).all()

    if not sessions:
        return 0

    streak = 0
    check_date = date.today()

    session_dates = {s.session_date for s in sessions}

    while True:
        if check_date in session_dates:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            # Allow one rest day
            check_date -= timedelta(days=1)
            if check_date not in session_dates:
                break
            # Continue if workout exists after rest day

        if streak > 365:
            break

    return streak


def check_volume_spikes(user_id):
    """Check for volume spikes in running and strength."""
    from app import db
    from sqlalchemy import text

    alerts = []

    # Check running volume spike
    try:
        result = db.session.execute(
            text('SELECT * FROM check_running_volume_spike(:user_id) LIMIT 1'),
            {'user_id': user_id}
        ).fetchone()

        if result and result.is_spike:
            alerts.append({
                'type': 'running',
                'message': f'Running mileage increased by {result.increase_percent}% this week!',
                'severity': 'warning'
            })
    except Exception:
        pass

    # Check strength volume spike
    try:
        result = db.session.execute(
            text('SELECT * FROM check_strength_volume_spike(:user_id) WHERE is_spike = true LIMIT 1'),
            {'user_id': user_id}
        ).fetchone()

        if result:
            alerts.append({
                'type': 'strength',
                'message': f'{result.muscle_group} volume increased by {result.increase_percent}%!',
                'severity': 'warning'
            })
    except Exception:
        pass

    return alerts


@dashboard_bp.route('/quick-log')
@login_required
def quick_log():
    """Quick log selection page."""
    return render_template('dashboard/quick_log.html')
