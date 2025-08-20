import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

def get_db_connection():
    conn = sqlite3.connect('university_issues.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            index_number TEXT,
            level TEXT,
            gender TEXT,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            is_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create issues table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    ''')

    # Create categories table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')

    # Insert default categories
    categories = [
        ('Academic', 'Academic related issues'),
        ('Infrastructure', 'Infrastructure and facilities'),
        ('IT Support', 'Information Technology support'),
        ('Administrative', 'Administrative issues'),
        ('Other', 'Other issues')
    ]

    for category in categories:
        conn.execute('INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)', category)

    conn.commit()
    conn.close()

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        conn = get_db_connection()
        g.user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

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

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        index_number = request.form.get('index_number', '').strip().upper()
        level = request.form.get('level', '').strip()
        gender = request.form.get('gender', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not all([username, email, full_name, password]):
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        try:
            conn = get_db_connection()
            # Check if user already exists
            existing_user = conn.execute('SELECT id FROM users WHERE email = ? OR username = ?', (email, username)).fetchone()
            if existing_user:
                flash('Email or username already exists.', 'danger')
                conn.close()
                return render_template('register.html')

            # Create new user
            password_hash = generate_password_hash(password)
            conn.execute('''
                INSERT INTO users (username, email, full_name, index_number, level, gender, password, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (username, email, full_name, index_number, level, gender, password_hash))
            conn.commit()
            conn.close()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if g.user is None:
        return redirect(url_for('login'))

    if g.user['role'] in ['supa_admin', 'subadmin']:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/student/dashboard')
def student_dashboard():
    if g.user is None or g.user['role'] != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    issues = conn.execute('''
        SELECT * FROM issues 
        WHERE student_id = ?
        ORDER BY created_at DESC
    ''', (g.user['id'],)).fetchall()
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
                         user=g.user)

@app.route('/admin/dashboard')
def admin_dashboard():
    if g.user is None or g.user['role'] not in ['supa_admin', 'subadmin']:
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Get statistics
    total_issues = conn.execute('SELECT COUNT(*) as count FROM issues').fetchone()['count']
    pending_issues = conn.execute('SELECT COUNT(*) as count FROM issues WHERE status = "pending"').fetchone()['count']
    resolved_issues = conn.execute('SELECT COUNT(*) as count FROM issues WHERE status = "resolved"').fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = "student"').fetchone()['count']

    # Get recent issues
    recent_issues = conn.execute('''
        SELECT i.*, u.full_name, u.email 
        FROM issues i 
        JOIN users u ON i.student_id = u.id 
        ORDER BY i.created_at DESC 
        LIMIT 10
    ''').fetchall()

    conn.close()

    stats = {
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'resolved_issues': resolved_issues,
        'total_users': total_users
    }

    return render_template('admin_dashboard.html', 
                         recent_issues=recent_issues, 
                         stats=stats,
                         user=g.user)

@app.route('/submit_issue', methods=['GET', 'POST'])
def submit_issue():
    if g.user is None or g.user['role'] != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()

    if request.method == 'POST':
        subject = request.form['subject']
        category = request.form['category']
        message = request.form['message']

        conn.execute(
            'INSERT INTO issues (student_id, subject, category, message, status) VALUES (?, ?, ?, ?, ?)',
            (g.user['id'], subject, category, message, 'pending')
        )
        conn.commit()
        flash('Issue submitted successfully.', 'success')
        return redirect(url_for('student_dashboard'))

    conn.close()
    return render_template('submit_issue.html', categories=categories)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
    print("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True)