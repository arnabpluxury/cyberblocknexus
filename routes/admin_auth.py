from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, current_user, logout_user
from models import User, db
from functools import wraps
from datetime import datetime

admin_auth = Blueprint('admin_auth', __name__)

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            flash('Please login with admin credentials to access the admin panel.', 'warning')
            return redirect(url_for('admin_auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@admin_auth.route('/admin/login', methods=['GET', 'POST'])
def login():
    # If user is already authenticated as admin, redirect to admin dashboard
    if current_user.is_authenticated and current_user.is_admin and session.get('admin_authenticated'):
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists, has admin privileges, and password is correct
        if user and user.is_admin and user.check_password(password):
            # Set admin session
            session['admin_authenticated'] = True
            
            # If user is not already logged in, log them in
            if not current_user.is_authenticated:
                login_user(user)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Successfully logged in to admin panel.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials. Please try again.', 'danger')
            
    return render_template('admin/login.html')

@admin_auth.route('/admin/logout')
def logout():
    # Remove admin session
    session.pop('admin_authenticated', None)
    flash('You have been logged out from the admin panel.', 'info')
    
    # Redirect to main site (don't log out from the main site)
    return redirect(url_for('home'))
