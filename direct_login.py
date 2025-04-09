"""
Direct login script for HackBlockNexus
This script provides a direct login route that bypasses SQLAlchemy models
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'development-key'  # Change this in production

# Database path
DB_PATH = 'hackblocknexus.db'

@app.route('/')
def home():
    """Home page route"""
    # Check if user is logged in
    is_logged_in = session.get('logged_in', False)
    is_admin = session.get('is_admin', False)
    username = session.get('username', '')
    
    return render_template('home.html', 
                          is_logged_in=is_logged_in,
                          is_admin=is_admin,
                          username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Connect to the database directly
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user from database
        cursor.execute("SELECT id, username, password_hash, is_admin FROM user WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        # Close the connection
        conn.close()
        
        if user and check_password_hash(user[2], password):
            # Set session variables
            session['logged_in'] = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = bool(user[3])
            
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route"""
    # Check if user is logged in and is admin
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        flash('You must be an admin to access this page', 'danger')
        return redirect(url_for('login'))
    
    return render_template('admin/dashboard.html', username=session.get('username', ''))

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
