from app import db
from datetime import datetime


class WorkoutTemplate(db.Model):
    """Workout template for quick session setup."""
    __tablename__ = 'workout_templates'

    template_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    workout_type = db.Column(db.String(50), default='upper_body')  # upper_body, lower_body, full_body, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('templates', lazy='dynamic'))
    exercises = db.relationship('TemplateExercise', backref='template',
                                lazy='dynamic', cascade='all, delete-orphan',
                                order_by='TemplateExercise.order_index')

    def __repr__(self):
        return f'<WorkoutTemplate {self.name}>'

    @classmethod
    def get_user_templates(cls, user_id, active_only=True):
        """Get all templates for a user."""
        query = cls.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(cls.name).all()

    @classmethod
    def get_by_type(cls, user_id, workout_type):
        """Get templates by workout type."""
        return cls.query.filter_by(
            user_id=user_id,
            workout_type=workout_type,
            is_active=True
        ).order_by(cls.name).all()

    def get_exercises_with_last_performance(self, user_id):
        """Get template exercises with user's last performance for each."""
        from app.models import StrengthLog, Exercise

        result = []
        muscle_groups_worked = set()  # Track which muscle groups have been worked

        for te in self.exercises.order_by(TemplateExercise.order_index).all():
            exercise = Exercise.query.get(te.exercise_id)
            if not exercise:
                continue

            # Get last performance for this exercise (from ANY workout)
            last_log = StrengthLog.query.join(
                StrengthLog.session
            ).filter(
                StrengthLog.exercise_id == te.exercise_id,
                StrengthLog.session.has(user_id=user_id)
            ).order_by(
                StrengthLog.log_id.desc()
            ).first()

            # Calculate suggested warm-up sets based on:
            # 1. Whether this muscle group was already worked
            # 2. Whether it's a compound or isolation exercise
            suggested_warmup = self._calculate_warmup_sets(
                exercise, muscle_groups_worked
            )

            # Mark this muscle group as worked
            if exercise.muscle_group:
                muscle_groups_worked.add(exercise.muscle_group)

            result.append({
                'template_exercise_id': te.template_exercise_id,
                'exercise_id': te.exercise_id,
                'exercise_name': exercise.name,
                'muscle_group': exercise.muscle_group,
                'movement_type': exercise.movement_type,
                'order_index': te.order_index,
                'target_sets': te.target_sets,
                'target_reps': te.target_reps,
                'notes': te.notes,
                'suggested_warmup': suggested_warmup,
                # Last performance data (smart pre-fill)
                'last_sets': last_log.sets if last_log else te.target_sets,
                'last_reps': last_log.reps if last_log else te.target_reps,
                # Use last_log weight, or fall back to starting_weight for first session
                'last_weight': float(last_log.weight_kg) if last_log and last_log.weight_kg else (float(te.starting_weight) if te.starting_weight else None),
                'last_rpe': last_log.rpe if last_log else None,
                'last_date': str(last_log.session.session_date) if last_log else None,
                'has_history': last_log is not None
            })

        return result

    def _calculate_warmup_sets(self, exercise, muscle_groups_worked):
        """Calculate suggested warm-up sets for an exercise.

        Logic:
        - First compound for a muscle group: 3 warm-up sets
        - First isolation for a muscle group: 2 warm-up sets
        - Muscle group already warmed up: 1 warm-up set
        """
        muscle_group = exercise.muscle_group
        is_compound = exercise.movement_type == 'compound'
        already_worked = muscle_group in muscle_groups_worked

        if already_worked:
            # Muscle already warmed up from previous exercise
            return 1
        elif is_compound:
            # First compound movement for this muscle group
            return 3
        else:
            # First isolation movement for this muscle group
            return 2

    def duplicate(self, new_name=None):
        """Create a copy of this template."""
        new_template = WorkoutTemplate(
            user_id=self.user_id,
            name=new_name or f"{self.name} (Copy)",
            description=self.description,
            workout_type=self.workout_type
        )
        db.session.add(new_template)
        db.session.flush()  # Get the new ID

        for te in self.exercises.all():
            new_te = TemplateExercise(
                template_id=new_template.template_id,
                exercise_id=te.exercise_id,
                order_index=te.order_index,
                target_sets=te.target_sets,
                target_reps=te.target_reps,
                starting_weight=te.starting_weight,
                notes=te.notes
            )
            db.session.add(new_te)

        return new_template


class TemplateExercise(db.Model):
    """Exercise within a workout template."""
    __tablename__ = 'template_exercises'

    template_exercise_id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('workout_templates.template_id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)  # Order within template
    target_sets = db.Column(db.Integer, default=3)
    target_reps = db.Column(db.Integer, default=10)
    warmup_sets = db.Column(db.Integer, default=0)  # Suggested warm-up sets
    starting_weight = db.Column(db.Numeric(5, 2))  # Initial weight for first session (no history)
    notes = db.Column(db.String(200))  # e.g., "Warm up with lighter weight first"

    # Relationship to exercise
    exercise = db.relationship('Exercise')

    def __repr__(self):
        return f'<TemplateExercise {self.exercise_id} in template {self.template_id}>'
