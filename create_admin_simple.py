"""
Simple script to create an admin user for HackBlockNexus
This script uses direct SQL commands to avoid model mismatch issues
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

# Database path
DB_PATH = 'hackblocknexus.db'

def create_admin_user(username, email, password):
    """Create a new admin user using direct SQL"""
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if the user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    if not cursor.fetchone():
        print("User table doesn't exist. Creating it...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    
    # Check if user already exists
    cursor.execute("SELECT id, is_admin FROM user WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        user_id, is_admin = existing_user
        if not is_admin:
            cursor.execute("UPDATE user SET is_admin = 1 WHERE id = ?", (user_id,))
            conn.commit()
            print(f"User {username} already exists. Admin privileges granted.")
        else:
            print(f"Admin user {username} already exists.")
    else:
        # Generate password hash
        password_hash = generate_password_hash(password)
        
        # Insert new admin user
        created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO user (username, email, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, email, password_hash, True, created_at)
        )
        conn.commit()
        print(f"Admin user '{username}' created successfully!")
        print(f"Email: {email}")
        print("You can now log in to the admin panel with these credentials.")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    # Admin credentials
    admin_username = "admin"
    admin_email = "admin@hackblocknexus.com"
    admin_password = "Admin@123"  # You should change this to a secure password
    
    create_admin_user(admin_username, admin_email, admin_password)
