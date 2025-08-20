import os
import sqlite3
from werkzeug.security import generate_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

# Initialize database first
def setup_db():
    if os.path.exists('university_issues.db'):
        os.remove('university_issues.db')
    
    conn = sqlite3.connect('university_issues.db')
    cursor = conn.cursor()
    
    # Create essential tables
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            index_number TEXT UNIQUE NOT NULL,
            level TEXT NOT NULL,
            gender TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            verification_code TEXT,
            reset_token TEXT,
            reset_token_expires TIMESTAMP,
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            priority TEXT DEFAULT 'Medium',
            assigned_to INTEGER,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE index_prefixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefix TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE system_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert basic data
    cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', ('Academic Issues', 'Academic problems'))
    cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', ('Technical Issues', 'Technical problems'))
    cursor.execute('INSERT INTO index_prefixes (prefix, description) VALUES (?, ?)', ('CS', 'Computer Science'))
    
    # Create admin user
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO users (username, email, full_name, index_number, level, gender, password, role, is_verified, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('supa_admin', 'admin@ktu.edu.gh', 'System Administrator', 'ADM001', 'Staff', 'M', admin_password, 'supa_admin', True, True))
    
    conn.commit()
    conn.close()
    print("Database setup complete!")

if __name__ == '__main__':
    print("Setting up database...")
    setup_db()
    
    print("Starting Flask application...")
    # Import the main app after database is ready
    from app import app
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
