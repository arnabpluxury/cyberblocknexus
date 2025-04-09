from flask import Flask
from models import db, User
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

# Initialize the database
db.init_app(app)

def create_admin_user(username, email, password):
    """Create a new admin user"""
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User {username} already exists.")
            return
        
        # Create new admin user
        admin_user = User(
            username=username,
            email=email,
            is_admin=True,
            created_at=datetime.utcnow(),
            is_active=True
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
