import sqlite3
import os
from werkzeug.security import generate_password_hash

def init_complete_database():
    """Initialize database with all required tables and data."""
    
    # Remove existing database
    if os.path.exists('university_issues.db'):
        os.remove('university_issues.db')
    
    conn = sqlite3.connect('university_issues.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            index_number TEXT UNIQUE NOT NULL,
            level TEXT NOT NULL,
            gender TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            is_verified BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            verification_code TEXT,
            verification_expires TIMESTAMP,
            reset_token TEXT,
            reset_expires TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create issues table
    cursor.execute('''
        CREATE TABLE issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'resolved')),
            priority TEXT DEFAULT 'Medium',
            assigned_to INTEGER,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (assigned_to) REFERENCES users (id)
        )
    ''')
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index_prefixes table
    cursor.execute('''
        CREATE TABLE index_prefixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefix TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create system_settings table
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
    
    # Create admin_logs table
    cursor.execute('''
        CREATE TABLE admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users (id)
        )
    ''')
    
    # Create system_notifications table
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
    
    # Insert default categories
    categories = [
        ('Academic Issues', 'Problems related to courses, grades, or academic policies'),
        ('Technical Issues', 'Problems with systems, software, or hardware'),
        ('Administrative Issues', 'Issues with registration, fees, or administrative processes'),
        ('Faculty Issues', 'Concerns about instructors or teaching quality'),
        ('Facilities Issues', 'Problems with classrooms, labs, or other facilities')
    ]
    
    for name, desc in categories:
        cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, desc))
    
    # Insert default index prefixes
    prefixes = [
        ('CS', 'Computer Science Regular Students'),
        ('CSM', 'Computer Science Morning Students'),
        ('CSE', 'Computer Science Evening Students'),
        ('CSH', 'Computer Science Weekend Students')
    ]
    
    for prefix, desc in prefixes:
        cursor.execute('INSERT INTO index_prefixes (prefix, description) VALUES (?, ?)', (prefix, desc))
    
    # Insert system settings
    settings = [
        ('site_name', 'KTU Student Report System', 'Name of the system', 'general'),
        ('site_description', 'CS Department Issue Reporting System', 'System description', 'general'),
        ('admin_email', 'admin@ktu.edu.gh', 'Primary admin email', 'general'),
        ('max_file_size', '5', 'Maximum file upload size in MB', 'files'),
        ('allowed_file_types', 'pdf,doc,docx,jpg,jpeg,png', 'Allowed file extensions', 'files'),
        ('email_notifications', 'true', 'Enable email notifications', 'notifications'),
        ('auto_assign_issues', 'false', 'Auto-assign issues to available admins', 'workflow'),
        ('maintenance_mode', 'false', 'Enable maintenance mode', 'system'),
        ('registration_enabled', 'true', 'Allow new user registrations', 'system'),
        ('theme_color', '#1e3a8a', 'Primary theme color', 'appearance'),
        ('logo_url', '/static/ktu-logo.png', 'System logo URL', 'appearance')
    ]
    
    for key, value, desc, cat in settings:
        cursor.execute('INSERT INTO system_settings (key, value, description, category) VALUES (?, ?, ?, ?)', (key, value, desc, cat))
    
    # Create admin user
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO users (username, email, full_name, index_number, level, gender, password, role, is_verified, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('supa_admin', 'admin@ktu.edu.gh', 'System Administrator', 'ADM001', 'Staff', 'M', admin_password, 'supa_admin', True, True))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_complete_database()
