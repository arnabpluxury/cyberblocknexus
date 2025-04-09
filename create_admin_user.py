"""
Script to create an admin user for HackBlockNexus
"""

from flask import Flask
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a minimal Flask app
app = Flask(__name__)

# Configure the app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hackblocknexus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import and initialize db after app is created
from models import db, User
db.init_app(app)

def create_admin_user(username, email, password):
    """Create a new admin user"""
    with app.app_context():
        # First, make sure the database tables exist
        db.create_all()
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User {username} already exists.")
            if not existing_user.is_admin:
                existing_user.is_admin = True
                db.session.commit()
                print(f"User {username} has been granted admin privileges.")
            return
        
        # Create new admin user with only the fields that exist in the database
        admin_user = User(
            username=username,
            email=email,
            is_admin=True,
            created_at=datetime.utcnow()
        )
        admin_user.set_password(password)
        
        # Add to database
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully!")
        print(f"Email: {email}")
        print("You can now log in to the admin panel with these credentials.")

if __name__ == "__main__":
    # Admin credentials
    admin_username = "admin"
    admin_email = "admin@hackblocknexus.com"
    admin_password = "Admin@123"  # You should change this to a secure password
    
    create_admin_user(admin_username, admin_email, admin_password)
