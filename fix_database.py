"""
Fix database script for HackBlockNexus
This script will directly modify the database schema to match what the application expects
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

# Database path
DB_PATH = 'hackblocknexus.db'

def fix_database():
    """Fix the database schema to match what the application expects"""
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if the user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    if cursor.fetchone():
        # Get the columns in the user table
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Check if points column exists, if not add it
        if 'points' not in columns:
            print("Adding 'points' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN points INTEGER DEFAULT 0")
        
        # Check if updated_at column exists, if not add it
        if 'updated_at' not in columns:
            print("Adding 'updated_at' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN updated_at TIMESTAMP")
        
        # Check if is_active column exists, if not add it
        if 'is_active' not in columns:
            print("Adding 'is_active' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
        
        # Check if last_login column exists, if not add it
        if 'last_login' not in columns:
            print("Adding 'last_login' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN last_login TIMESTAMP")
    else:
        print("User table doesn't exist. Creating it...")
        cursor.execute('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            points INTEGER DEFAULT 0,
            updated_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP
        )
        ''')
    
    # Commit the changes
    conn.commit()
    print("Database schema fixed successfully!")
    
    # Close the connection
    conn.close()

def create_admin_user(username, email, password):
    """Create a new admin user if it doesn't exist"""
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
            "INSERT INTO user (username, email, password_hash, is_admin, created_at, points, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, email, password_hash, True, created_at, 0, True)
        )
        conn.commit()
        print(f"Admin user '{username}' created successfully!")
        print(f"Email: {email}")
        print("You can now log in to the admin panel with these credentials.")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    # Fix the database schema
    fix_database()
    
    # Admin credentials
    admin_username = "admin"
    admin_email = "admin@hackblocknexus.com"
    admin_password = "Admin@123"  # You should change this to a secure password
    
    # Create admin user
    create_admin_user(admin_username, admin_email, admin_password)
