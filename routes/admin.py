from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from models import db, User, Event, CTFChallenge, Project, ChallengeSolve
from datetime import datetime, timedelta
from functools import wraps
from routes.admin_auth import admin_login_required

admin = Blueprint('admin', __name__)

# This decorator is kept for backward compatibility
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('admin_auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@login_required
@admin_login_required
def dashboard():
    # Calculate statistics
    now = datetime.utcnow()
    stats = {
        'total_users': User.query.count(),
        'new_users_today': User.query.filter(
            User.created_at >= now.replace(hour=0, minute=0, second=0)
        ).count(),
        'active_events': Event.query.filter(Event.date >= now).count(),
        'upcoming_events': Event.query.filter(
            Event.date.between(now, now + timedelta(days=7))
        ).count(),
        'total_challenges': CTFChallenge.query.count(),
        'active_challenges': CTFChallenge.query.filter_by(is_active=True).count(),
        'total_projects': Project.query.count(),
        'new_projects_week': Project.query.filter(
            Project.created_at >= now - timedelta(days=7)
        ).count()
    }

    # Get recent activity
    recent_activity = []  # You'll need to implement an Activity model for this
    
    # Get top users
    top_users = User.query.order_by(User.points.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_activity=recent_activity,
                         top_users=top_users)

@admin.route('/admin/users')
@login_required
@admin_login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.is_admin = 'is_admin' in request.form
        if request.form.get('new_password'):
            user.set_password(request.form['new_password'])
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/edit_user.html', user=user)

@admin.route('/admin/events')
@login_required
@admin_login_required
def events():
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('admin/events.html', events=events)

@admin.route('/admin/event/new', methods=['GET', 'POST'])
@login_required
@admin_login_required
def new_event():
    if request.method == 'POST':
        event = Event(
            title=request.form['title'],
            description=request.form['description'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M'),
            location=request.form['location'],
            event_type=request.form['event_type']
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully', 'success')
        return redirect(url_for('admin.events'))
    return render_template('admin/edit_event.html')

@admin.route('/admin/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form['description']
        event.date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
        event.location = request.form['location']
        event.event_type = request.form['event_type']
        db.session.commit()
        flash('Event updated successfully', 'success')
        return redirect(url_for('admin.events'))
    return render_template('admin/edit_event.html', event=event)

@admin.route('/admin/ctf')
@login_required
@admin_login_required
def ctf_challenges():
    challenges = CTFChallenge.query.all()
    return render_template('admin/ctf_challenges.html', challenges=challenges)

@admin.route('/admin/ctf/new', methods=['GET', 'POST'])
@login_required
@admin_login_required
def new_challenge():
    if request.method == 'POST':
        challenge = CTFChallenge(
            title=request.form['title'],
            description=request.form['description'],
            category=request.form['category'],
            points=int(request.form['points']),
            flag=request.form['flag'],
            difficulty=request.form['difficulty']
        )
        db.session.add(challenge)
        db.session.commit()
        flash('Challenge created successfully', 'success')
        return redirect(url_for('admin.ctf_challenges'))
    return render_template('admin/edit_challenge.html')

@admin.route('/admin/ctf/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_challenge(challenge_id):
    challenge = CTFChallenge.query.get_or_404(challenge_id)
    if request.method == 'POST':
        challenge.title = request.form['title']
        challenge.description = request.form['description']
        challenge.category = request.form['category']
        challenge.points = int(request.form['points'])
        challenge.flag = request.form['flag']
        challenge.difficulty = request.form['difficulty']
        challenge.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Challenge updated successfully', 'success')
        return redirect(url_for('admin.ctf_challenges'))
    return render_template('admin/edit_challenge.html', challenge=challenge)

# API endpoints for AJAX operations
@admin.route('/admin/api/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_login_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        return jsonify({'error': 'Cannot modify your own admin status'}), 400
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'status': 'success', 'is_admin': user.is_admin})

@admin.route('/admin/api/challenge/<int:challenge_id>/toggle-active', methods=['POST'])
@login_required
@admin_login_required
def toggle_challenge(challenge_id):
    challenge = CTFChallenge.query.get_or_404(challenge_id)
    challenge.is_active = not challenge.is_active
    db.session.commit()
    return jsonify({'status': 'success', 'is_active': challenge.is_active})
