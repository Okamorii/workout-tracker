from datetime import datetime, date
from app import db


class WorkoutSession(db.Model):
    """Workout session model."""
    __tablename__ = 'workout_sessions'

    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False, default=date.today)
    session_type = db.Column(db.String(20))  # 'upper_body', 'running', 'other'
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    strength_logs = db.relationship('StrengthLog', backref='session', lazy='dynamic',
                                    cascade='all, delete-orphan')
    running_logs = db.relationship('RunningLog', backref='session', lazy='dynamic',
                                   cascade='all, delete-orphan')

    @property
    def total_volume(self):
        """Calculate total volume for strength session."""
        return sum(
            log.volume for log in self.strength_logs.all()
        )

    @property
    def total_distance(self):
        """Calculate total distance for running session."""
        return sum(
            log.distance_km or 0 for log in self.running_logs.all()
        )

    @classmethod
    def get_user_sessions(cls, user_id, session_type=None, limit=None):
        """Get user's workout sessions."""
        query = cls.query.filter_by(user_id=user_id)
        if session_type:
            query = query.filter_by(session_type=session_type)
        query = query.order_by(cls.session_date.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def get_today_session(cls, user_id, session_type=None):
        """Get today's session if exists."""
        query = cls.query.filter_by(user_id=user_id, session_date=date.today())
        if session_type:
            query = query.filter_by(session_type=session_type)
        return query.first()

    def __repr__(self):
        return f'<WorkoutSession {self.session_date} - {self.session_type}>'


class StrengthLog(db.Model):
    """Strength training log model."""
    __tablename__ = 'strength_logs'

    log_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.session_id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Numeric(6, 2))
    rpe = db.Column(db.Integer)  # 1-10
    rest_seconds = db.Column(db.Integer)
    tempo = db.Column(db.String(20))
    warmup_sets = db.Column(db.Integer, default=0)  # Number of warm-up sets before working sets
    template_exercise_id = db.Column(db.Integer, db.ForeignKey('template_exercises.template_exercise_id', ondelete='SET NULL'))
    set_number = db.Column(db.Integer)  # For per-set logging: 1, 2, 3... NULL = batch entry
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def volume(self):
        """Calculate volume (sets × reps × weight)."""
        return (self.sets or 0) * (self.reps or 0) * float(self.weight_kg or 0)

    @property
    def estimated_1rm(self):
        """Calculate estimated 1RM using Epley formula."""
        if not self.weight_kg or not self.reps:
            return 0
        if self.reps == 1:
            return float(self.weight_kg)
        return round(float(self.weight_kg) * (1 + self.reps / 30), 2)

    @property
    def is_pr(self):
        """Check if this log was a PR at the time it was logged."""
        from app.models import PersonalRecord
        pr = PersonalRecord.query.filter_by(
            user_id=self.session.user_id,
            exercise_id=self.exercise_id,
            record_type='1RM'
        ).order_by(PersonalRecord.date_achieved.desc()).first()

        if pr and pr.date_achieved == self.session.session_date:
            # Check if this log's 1RM matches the PR value
            return abs(float(pr.value) - self.estimated_1rm) < 0.1
        return False

    @classmethod
    def get_last_performance(cls, user_id, exercise_id):
        """Get user's last performance for an exercise."""
        return cls.query.join(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            cls.exercise_id == exercise_id
        ).order_by(WorkoutSession.session_date.desc()).first()

    @classmethod
    def get_exercise_history(cls, user_id, exercise_id, limit=10):
        """Get user's history for an exercise."""
        return cls.query.join(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            cls.exercise_id == exercise_id
        ).order_by(WorkoutSession.session_date.desc()).limit(limit).all()

    @classmethod
    def get_best_1rm(cls, user_id, exercise_id):
        """Get user's best estimated 1RM for an exercise."""
        logs = cls.query.join(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            cls.exercise_id == exercise_id
        ).all()

        if not logs:
            return None

        best = max(logs, key=lambda x: x.estimated_1rm)
        return {
            'weight': best.weight_kg,
            'reps': best.reps,
            'estimated_1rm': best.estimated_1rm,
            'date': best.session.session_date
        }

    def __repr__(self):
        return f'<StrengthLog {self.exercise_id}: {self.sets}x{self.reps}@{self.weight_kg}kg>'


class RunningLog(db.Model):
    """Running log model."""
    __tablename__ = 'running_logs'

    log_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.session_id'), nullable=False)
    run_type = db.Column(db.String(20))  # 'easy', 'tempo', 'interval', 'long', 'other'
    distance_km = db.Column(db.Numeric(6, 2))
    duration_minutes = db.Column(db.Integer)
    avg_pace_per_km = db.Column(db.Numeric(5, 2))
    elevation_gain_meters = db.Column(db.Integer)
    avg_heart_rate = db.Column(db.Integer)
    max_heart_rate = db.Column(db.Integer)
    perceived_effort = db.Column(db.String(20))
    weather_conditions = db.Column(db.String(50))
    route_notes = db.Column(db.Text)
    interval_details = db.Column(db.Text)  # Details for interval runs (e.g., "20min warm up + 5x30s at 4'30")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def pace_per_km(self):
        """Calculate pace per km (duration / distance)."""
        if not self.duration_minutes or not self.distance_km or float(self.distance_km) == 0:
            return None
        return round(self.duration_minutes / float(self.distance_km), 2)

    @property
    def trimp_score(self):
        """Calculate TRIMP score."""
        if not all([self.duration_minutes, self.avg_heart_rate, self.max_heart_rate]):
            return None

        resting_hr = 60  # Default resting HR
        if self.max_heart_rate <= resting_hr:
            return 0

        hr_ratio = (self.avg_heart_rate - resting_hr) / (self.max_heart_rate - resting_hr)
        hr_ratio = max(0, min(1, hr_ratio))  # Clamp between 0 and 1

        import math
        return round(self.duration_minutes * hr_ratio * 0.64 * math.exp(1.92 * hr_ratio), 2)

    @classmethod
    def get_weekly_mileage(cls, user_id):
        """Get current week's total mileage."""
        from datetime import timedelta
        week_start = date.today() - timedelta(days=date.today().weekday())

        result = db.session.query(
            db.func.sum(cls.distance_km)
        ).join(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= week_start
        ).scalar()

        return float(result or 0)

    @classmethod
    def get_user_running_history(cls, user_id, limit=10):
        """Get user's running history."""
        return cls.query.join(WorkoutSession).filter(
            WorkoutSession.user_id == user_id
        ).order_by(WorkoutSession.session_date.desc()).limit(limit).all()

    def __repr__(self):
        return f'<RunningLog {self.run_type}: {self.distance_km}km>'
