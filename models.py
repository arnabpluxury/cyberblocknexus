from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Import the user_roles association table
from models.roles import user_roles, Role, Permission

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)  # Kept for backward compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    points = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    solved_challenges = db.relationship('ChallengeSolve', backref='user', lazy=True)
    
    # Relationship with roles
    roles = db.relationship('Role', secondary=user_roles, 
                           backref=db.backref('users', lazy='dynamic'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def has_permission(self, permission_name):
        """Check if user has a specific permission through any of their roles"""
        # Admin users have all permissions
        if self.is_admin:
            return True
            
        # Check if the user has the permission through any of their roles
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False
        
    def has_role(self, role_name):
        """Check if user has a specific role"""
        # Admin users have all roles implicitly
        if self.is_admin and role_name.lower() == 'admin':
            return True
            
        for role in self.roles:
            if role.name == role_name:
                return True
        return False
        
    def add_role(self, role):
        """Add a role to the user"""
        if role not in self.roles:
            self.roles.append(role)
            
    def remove_role(self, role):
        """Remove a role from the user"""
        if role in self.roles:
            self.roles.remove(role)
            
    def get_permissions(self):
        """Get all permissions the user has through their roles"""
        if self.is_admin:
            return Permission.query.all()
            
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission)
        return list(permissions)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    event_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registrations = db.relationship('EventRegistration', backref='event', lazy=True)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

class CTFChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    points = db.Column(db.Integer, default=0)
    flag = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    hints = db.relationship('ChallengeHint', backref='challenge', lazy=True)
    solves = db.relationship('ChallengeSolve', backref='challenge', lazy=True)

class ChallengeHint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('ctf_challenge.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer, default=0)

class ChallengeSolve(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('ctf_challenge.id'), nullable=False)
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    github_url = db.Column(db.String(200))
    demo_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    technologies = db.Column(db.String(200))
    likes = db.relationship('ProjectLike', backref='project', lazy=True)

class ProjectLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
