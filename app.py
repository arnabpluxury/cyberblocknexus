from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from functools import wraps
import os
import secrets
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Flask configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT')

# Database configuration
# For local testing, use SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hackblocknexus.db'
# For production, uncomment the following line to use MySQL
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:{os.environ.get('MYSQL_PASSWORD')}@{os.environ.get('MYSQL_HOST')}:{os.environ.get('MYSQL_PORT')}/{os.environ.get('MYSQL_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models
from models import db, User, Event, CTFChallenge, Project, ChallengeSolve, EventRegistration, ChallengeHint, ProjectLike

# Initialize database with app
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        # Add email sending logic here
        flash('Your message has been sent!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

# Email verification functions
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except Exception:
        return False

def send_confirmation_email(user):
    token = generate_confirmation_token(user.email)
    user.email_confirm_token = token
    user.token_expiration = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()
    
    confirm_url = url_for('confirm_email', token=token, _external=True)
    subject = "Please confirm your email - HackBlockNexus"
    template = render_template('email/confirm_email.html', confirm_url=confirm_url, user=user)
    
    msg = Message(
        subject,
        recipients=[user.email],
        html=template
    )
    mail.send(msg)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.email_confirmed:
                flash('Please confirm your email before logging in.', 'warning')
                return redirect(url_for('login'))
                
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Send confirmation email
        send_confirmation_email(new_user)
        
        flash('Registration successful! Please check your email to confirm your account.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    if user.email_confirmed:
        flash('Account already confirmed. Please login.', 'info')
    else:
        user.email_confirmed = True
        user.email_confirm_token = None
        user.token_expiration = None
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    
    return redirect(url_for('login'))

@app.route('/resend-confirmation')
@login_required
def resend_confirmation():
    if current_user.email_confirmed:
        flash('Your account is already confirmed.', 'info')
        return redirect(url_for('home'))
    
    send_confirmation_email(current_user)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# CTF routes
@app.route('/ctf')
def ctf_home():
    return render_template('ctf/home.html')

@app.route('/ctf/challenges')
@login_required
def ctf_challenges():
    challenges = Challenge.query.all()
    return render_template('ctf/challenges.html', challenges=challenges)

@app.route('/ctf/challenge/<int:challenge_id>')
@login_required
def ctf_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    return render_template('ctf/challenge.html', challenge=challenge)

@app.route('/ctf/leaderboard')
def ctf_leaderboard():
    users = User.query.order_by(User.points.desc()).all()
    return render_template('ctf/leaderboard.html', users=users)

@app.route('/ctf/submit_flag/<int:challenge_id>', methods=['POST'])
@login_required
def submit_flag(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    flag = request.form.get('flag')
    
    if challenge in current_user.solved_challenges:
        flash('You have already solved this challenge!', 'info')
        return redirect(url_for('ctf_challenge', challenge_id=challenge_id))
        
    if flag == challenge.flag:
        current_user.points += challenge.points
        current_user.solved_challenges.append(challenge)
        db.session.commit()
        flash(f'Correct! You earned {challenge.points} points!', 'success')
    else:
        flash('Incorrect flag. Try again!', 'danger')
    
    return redirect(url_for('ctf_challenge', challenge_id=challenge_id))

# Event routes
@app.route('/events')
def events():
    now = datetime.now()
    upcoming_events = Event.query.filter(Event.date >= now).order_by(Event.date).all()
    past_events = Event.query.filter(Event.date < now).order_by(Event.date.desc()).all()
    return render_template('events.html', upcoming_events=upcoming_events, past_events=past_events)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_detail.html', event=event)

@app.route('/register_event/<int:event_id>')
@login_required
def register_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event not in current_user.registered_events:
        current_user.registered_events.append(event)
        db.session.commit()
        flash(f'Successfully registered for {event.title}!', 'success')
    else:
        flash('You are already registered for this event.', 'info')
    return redirect(url_for('events'))

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    users = User.query.all()
    challenges = Challenge.query.all()
    events = Event.query.all()
    return render_template('admin/dashboard.html', users=users, challenges=challenges, events=events)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/challenges')
@admin_required
def admin_challenges():
    challenges = Challenge.query.all()
    return render_template('admin/ctf_challenges.html', challenges=challenges)

@app.route('/admin/events')
@admin_required
def admin_events():
    events = Event.query.all()
    return render_template('admin/events.html', events=events)

# Context processors
@app.context_processor
def utility_processor():
    def timeago(date):
        now = datetime.now()
        diff = now - date
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    
    return dict(
        timeago=timeago,
        now=datetime.now()  # Add the current datetime to all templates
    )

# Register blueprints
from routes.admin import admin
from routes.admin_auth import admin_auth
from routes.roles import roles_bp

app.register_blueprint(admin)
app.register_blueprint(admin_auth)
app.register_blueprint(roles_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
