"""
Reset database script for HackBlockNexus
This script will delete the existing database and create a new one with the correct schema
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

# Database path
DB_PATH = 'hackblocknexus.db'

def reset_database():
    """Delete the existing database and create a new one"""
    # Delete the existing database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Deleted existing database: {DB_PATH}")
    
    # Connect to the new SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the user table with a minimal schema
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
    
    # Create the role table
    cursor.execute('''
    CREATE TABLE role (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')
    
    # Create the permission table
    cursor.execute('''
    CREATE TABLE permission (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        category_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES permission_category (id)
    )
    ''')
    
    # Create the permission_category table
    cursor.execute('''
    CREATE TABLE permission_category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')
    
    # Create the user_roles association table
    cursor.execute('''
    CREATE TABLE user_roles (
        user_id INTEGER,
        role_id INTEGER,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES user (id),
        FOREIGN KEY (role_id) REFERENCES role (id)
    )
    ''')
    
    # Create the role_permissions association table
    cursor.execute('''
    CREATE TABLE role_permissions (
        role_id INTEGER,
        permission_id INTEGER,
        PRIMARY KEY (role_id, permission_id),
        FOREIGN KEY (role_id) REFERENCES role (id),
        FOREIGN KEY (permission_id) REFERENCES permission (id)
    )
    ''')
    
    # Commit the changes
    conn.commit()
    print("Created new database with the correct schema")
    
    # Close the connection
    conn.close()

def create_admin_user(username, email, password):
    """Create a new admin user"""
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generate password hash
    password_hash = generate_password_hash(password)
    
    # Insert new admin user
    created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO user (username, email, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, email, password_hash, True, created_at)
    )
    
    # Create default admin role
    cursor.execute(
        "INSERT INTO role (name, description) VALUES (?, ?)",
        ("Admin", "Full administrative access")
    )
    
    # Get the user ID and role ID
    user_id = cursor.lastrowid
    cursor.execute("SELECT id FROM role WHERE name = 'Admin'")
    role_id = cursor.fetchone()[0]
    
    # Assign admin role to the user
    cursor.execute(
        "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
        (user_id, role_id)
    )
    
    # Commit the changes
    conn.commit()
    
    print(f"Admin user '{username}' created successfully!")
    print(f"Email: {email}")
    print("You can now log in to the admin panel with these credentials.")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    # Reset the database
    reset_database()
    
    # Admin credentials
    admin_username = "admin"
    admin_email = "admin@hackblocknexus.com"
    admin_password = "Admin@123"  # You should change this to a secure password
    
    # Create admin user
    create_admin_user(admin_username, admin_email, admin_password)
