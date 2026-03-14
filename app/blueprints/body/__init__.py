from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime
from decimal import Decimal
from app import db
from app.models import BodyMeasurement

body_bp = Blueprint('body', __name__)


def parse_decimal(value):
    """Parse decimal value, handling comma as decimal separator."""
    if not value:
        return None
    try:
        return Decimal(str(value).replace(',', '.'))
    except:
        return None


@body_bp.route('/')
@login_required
def index():
    """Body measurements overview."""
    latest = BodyMeasurement.get_latest(current_user.user_id)
    measurements = BodyMeasurement.get_user_measurements(current_user.user_id, limit=10)
    comparison = BodyMeasurement.get_comparison(current_user.user_id)

    return render_template(
        'body/index.html',
        latest=latest,
        measurements=measurements,
        comparison=comparison
    )


@body_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_measurement():
    """Add new body measurement."""
    if request.method == 'POST':
        # Parse measurement date from form (string) to date object
        date_str = request.form.get('measurement_date')
        if date_str:
            measurement_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            measurement_date = date.today()

        measurement = BodyMeasurement(
            user_id=current_user.user_id,
            measurement_date=measurement_date,
            weight_kg=parse_decimal(request.form.get('weight_kg')),
            body_fat_pct=parse_decimal(request.form.get('body_fat_pct')),
            chest_cm=parse_decimal(request.form.get('chest_cm')),
            waist_cm=parse_decimal(request.form.get('waist_cm')),
            hips_cm=parse_decimal(request.form.get('hips_cm')),
            left_arm_cm=parse_decimal(request.form.get('left_arm_cm')),
            right_arm_cm=parse_decimal(request.form.get('right_arm_cm')),
            left_thigh_cm=parse_decimal(request.form.get('left_thigh_cm')),
            right_thigh_cm=parse_decimal(request.form.get('right_thigh_cm')),
            left_calf_cm=parse_decimal(request.form.get('left_calf_cm')),
            right_calf_cm=parse_decimal(request.form.get('right_calf_cm')),
            neck_cm=parse_decimal(request.form.get('neck_cm')),
            shoulders_cm=parse_decimal(request.form.get('shoulders_cm')),
            notes=request.form.get('notes', '').strip() or None
        )

        db.session.add(measurement)
        db.session.commit()

        flash('Measurements recorded!', 'success')
        return redirect(url_for('body.index'))

    # Pre-fill with latest values for convenience
    latest = BodyMeasurement.get_latest(current_user.user_id)
    return render_template('body/add.html', latest=latest, today=date.today())


@body_bp.route('/<int:measurement_id>')
@login_required
def view_measurement(measurement_id):
    """View a specific measurement."""
    measurement = BodyMeasurement.query.get_or_404(measurement_id)
    if measurement.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('body.index'))

    return render_template('body/view.html', measurement=measurement)


@body_bp.route('/<int:measurement_id>/delete', methods=['POST'])
@login_required
def delete_measurement(measurement_id):
    """Delete a measurement."""
    measurement = BodyMeasurement.query.get_or_404(measurement_id)
    if measurement.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('body.index'))

    db.session.delete(measurement)
    db.session.commit()
    flash('Measurement deleted.', 'success')
    return redirect(url_for('body.index'))


@body_bp.route('/api/progress/<field>')
@login_required
def progress_data(field):
    """Get progress data for charts."""
    valid_fields = ['weight_kg', 'body_fat_pct', 'chest_cm', 'waist_cm',
                    'hips_cm', 'left_arm_cm', 'right_arm_cm', 'left_thigh_cm',
                    'right_thigh_cm', 'neck_cm', 'shoulders_cm']

    if field not in valid_fields:
        return jsonify({'error': 'Invalid field'}), 400

    weeks = request.args.get('weeks', 12, type=int)
    data = BodyMeasurement.get_progress(current_user.user_id, field, weeks)
    return jsonify(data)


@body_bp.route('/api/summary')
@login_required
def summary():
    """Get summary data for dashboard."""
    latest = BodyMeasurement.get_latest(current_user.user_id)
    comparison = BodyMeasurement.get_comparison(current_user.user_id)

    if not latest:
        return jsonify({'has_data': False})

    return jsonify({
        'has_data': True,
        'latest_date': str(latest.measurement_date),
        'weight': float(latest.weight_kg) if latest.weight_kg else None,
        'body_fat': float(latest.body_fat_pct) if latest.body_fat_pct else None,
        'weight_change': comparison['weight_kg']['change'] if comparison and 'weight_kg' in comparison else None
    })
