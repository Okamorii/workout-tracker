from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    weekly_strength_target = db.Column(db.Integer, default=2)
    weekly_running_target = db.Column(db.Integer, default=4)

    # Relationships
    workout_sessions = db.relationship('WorkoutSession', backref='user', lazy='dynamic')
    personal_records = db.relationship('PersonalRecord', backref='user', lazy='dynamic')
    recovery_logs = db.relationship('RecoveryLog', backref='user', lazy='dynamic')

    def get_id(self):
        """Override for Flask-Login."""
        return str(self.user_id)

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verify password."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    @property
    def total_workouts(self):
        """Get total workout count."""
        return self.workout_sessions.count()

    @property
    def workouts_this_week(self):
        """Get workouts in current week."""
        from datetime import date, timedelta
        week_start = date.today() - timedelta(days=date.today().weekday())
        return self.workout_sessions.filter(
            WorkoutSession.session_date >= week_start
        ).count()

    def __repr__(self):
        return f'<User {self.username}>'


# Import here to avoid circular imports
from .workout import WorkoutSession
