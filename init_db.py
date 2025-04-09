"""
Database initialization script for HackBlockNexus
This script will create the MySQL database and tables required for the application.
"""

import os
import sys
import pymysql
from dotenv import load_dotenv
from app import app, db

# Load environment variables
load_dotenv()

def create_database():
    """Create the MySQL database if it doesn't exist"""
    try:
        # Connect to MySQL server without specifying a database
        conn = pymysql.connect(
            host=os.environ.get('MYSQL_HOST'),
            user=os.environ.get('MYSQL_USER'),
            password=os.environ.get('MYSQL_PASSWORD'),
            port=int(os.environ.get('MYSQL_PORT', 3306))
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Create the database if it doesn't exist
        db_name = os.environ.get('MYSQL_DB')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database '{db_name}' created or already exists.")
        
        # Close the connection
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def create_tables():
    """Create all tables defined in the models"""
    try:
        with app.app_context():
            db.create_all()
            print("All tables created successfully.")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def main():
    """Main function to initialize the database"""
    print("Initializing HackBlockNexus database...")
    
    # Create the database
    if not create_database():
        print("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        print("Failed to create tables. Exiting.")
        sys.exit(1)
    
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    main()
