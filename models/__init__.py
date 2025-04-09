from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Import roles models
from models.roles import Role, Permission, PermissionCategory, user_roles, role_permissions, RoleAuditLog

# Define models that were previously in models.py
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)  # Kept for backward compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    points = db.Column(db.Integer, default=0, nullable=True)
    
    # These fields might not exist in the current database schema
    # We'll add them with nullable=True so they don't cause errors
    updated_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationship with roles - using dynamic to avoid loading all users
    roles = db.relationship('Role', secondary=user_roles, 
                           backref=db.backref('users', lazy='dynamic'))
    # Make relationship optional to avoid errors if table doesn't exist
    solved_challenges = db.relationship('ChallengeSolve', backref='user', lazy=True, 
                                      primaryjoin="User.id == ChallengeSolve.user_id", 
                                      foreign_keys="ChallengeSolve.user_id",
                                      uselist=True, viewonly=True)
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
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
            if role.name.lower() == role_name.lower():
                return True
        return False

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=True)
    event_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    # Make the relationship optional to avoid errors
    registrations = db.relationship('EventRegistration', backref='event', lazy=True,
                                   primaryjoin="Event.id == EventRegistration.event_id",
                                   foreign_keys="EventRegistration.event_id",
                                   viewonly=True)

class EventRegistration(db.Model):
    __tablename__ = 'event_registration'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

class CTFChallenge(db.Model):
    __tablename__ = 'ctf_challenge'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    points = db.Column(db.Integer, default=0, nullable=True)
    flag = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=True)
    # Make relationships optional
    hints = db.relationship('ChallengeHint', backref='challenge', lazy=True,
                          primaryjoin="CTFChallenge.id == ChallengeHint.challenge_id",
                          foreign_keys="ChallengeHint.challenge_id",
                          viewonly=True)
    solves = db.relationship('ChallengeSolve', backref='challenge', lazy=True,
                           primaryjoin="CTFChallenge.id == ChallengeSolve.challenge_id",
                           foreign_keys="ChallengeSolve.challenge_id",
                           viewonly=True)

class ChallengeHint(db.Model):
    __tablename__ = 'challenge_hint'
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('ctf_challenge.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer, default=0, nullable=True)

class ChallengeSolve(db.Model):
    __tablename__ = 'challenge_solve'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('ctf_challenge.id'), nullable=False)
    solved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    github_url = db.Column(db.String(200), nullable=True)
    demo_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    technologies = db.Column(db.String(200), nullable=True)
    likes = db.relationship('ProjectLike', backref='project', lazy=True,
                          primaryjoin="Project.id == ProjectLike.project_id",
                          foreign_keys="ProjectLike.project_id",
                          viewonly=True)

class ProjectLike(db.Model):
    __tablename__ = 'project_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
