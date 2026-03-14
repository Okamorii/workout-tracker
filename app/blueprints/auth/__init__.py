from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Account is deactivated.', 'error')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            user.update_last_login()

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))

        flash('Invalid username or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register.html')

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            username = request.form.get('username')
            email = request.form.get('email')

            # Check if username/email already taken by another user
            if username != current_user.username:
                if User.query.filter_by(username=username).first():
                    flash('Username already taken.', 'error')
                    return render_template('auth/profile.html')

            if email != current_user.email:
                if User.query.filter_by(email=email).first():
                    flash('Email already registered.', 'error')
                    return render_template('auth/profile.html')

            current_user.username = username
            current_user.email = email
            db.session.commit()
            flash('Profile updated successfully.', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('auth/profile.html')

            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('auth/profile.html')

            if len(new_password) < 8:
                flash('Password must be at least 8 characters.', 'error')
                return render_template('auth/profile.html')

            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully.', 'success')

        elif action == 'update_targets':
            strength_target = request.form.get('weekly_strength_target', type=int)
            running_target = request.form.get('weekly_running_target', type=int)

            if strength_target is not None and 0 <= strength_target <= 14:
                current_user.weekly_strength_target = strength_target
            if running_target is not None and 0 <= running_target <= 14:
                current_user.weekly_running_target = running_target

            db.session.commit()
            flash('Weekly targets updated.', 'success')

    return render_template('auth/profile.html')
