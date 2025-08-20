import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash
from email_utils import generate_verification_code, send_verification_email, validate_institutional_email, generate_reset_token, send_password_reset_email

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Import and register blueprints
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

def parse_datetime(date_string):
    """Parse datetime string from database and return formatted string"""
    if not date_string:
        return 'Unknown date'
    try:
        dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return date_string

def get_db_connection():
    conn = sqlite3.connect('university_issues.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with all required tables."""
    if os.path.exists('university_issues.db'):
        os.remove('university_issues.db')
    
    conn = sqlite3.connect('university_issues.db')
    cursor = conn.cursor()
    
    # Create users table
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
    
    # Create issues table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

@app.before_request
def load_logged_in_user():
    username = session.get('username')
    if username is None:
        g.user = None
    else:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user is None:
            g.user = None
        else:
            g.user = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "is_verified": user["is_verified"]
            }

@app.route('/')
def index():
    if g.user:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        error = None
        if user is None:
            error = 'Incorrect email address.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        elif not user['is_verified']:
            error = 'Please verify your email before logging in.'
        
        if error is None:
            session.clear()
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        
        flash(error, 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if g.user is None:
        return redirect(url_for('login'))
    
    if g.user['role'] == 'supa_admin':
        return redirect(url_for('admin.admin_dashboard'))
    elif g.user['role'] == 'subadmin':
        return redirect(url_for('admin.admin_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/student/dashboard')
def student_dashboard():
    if g.user is None or g.user['role'] != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    username = g.user['username']
    issues = conn.execute('''
        SELECT * FROM issues 
        WHERE student_id = (SELECT id FROM users WHERE username = ?)
        ORDER BY created_at DESC
    ''', (username,)).fetchall()
    conn.close()
    
    stats = {
        'pending': sum(1 for issue in issues if issue['status'] == 'pending'),
        'in_progress': sum(1 for issue in issues if issue['status'] == 'in_progress'),
        'resolved': sum(1 for issue in issues if issue['status'] == 'resolved'),
    }
    recent_issues = issues[:5]
    return render_template('student_dashboard.html', 
                         recent_issues=recent_issues, 
                         stats=stats, 
                         parse_datetime=parse_datetime,
                         user=g.user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
    print("Starting Flask server on http://127.0.0.1:5000")
    print("Login credentials: admin@ktu.edu.gh / admin123")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
