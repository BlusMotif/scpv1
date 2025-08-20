
import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

def get_db_connection():
    conn = sqlite3.connect('university_issues.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_simple_db():
    """Initialize a simple database for testing"""
    conn = sqlite3.connect('university_issues.db')
    cursor = conn.cursor()
    
    # Drop existing tables to start fresh
    cursor.execute('DROP TABLE IF EXISTS issues')
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS categories')
    
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
            role TEXT NOT NULL DEFAULT 'student',
            is_verified BOOLEAN DEFAULT TRUE,
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
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id)
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
    
    # Create test users
    admin_password = generate_password_hash('admin123')
    student_password = generate_password_hash('student123')
    
    cursor.execute('''
        INSERT INTO users (username, email, full_name, index_number, level, gender, password, role, is_verified, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', 'admin@ktu.edu.gh', 'System Administrator', 'ADM001', 'Staff', 'M', admin_password, 'supa_admin', True, True))
    
    cursor.execute('''
        INSERT INTO users (username, email, full_name, index_number, level, gender, password, role, is_verified, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('student1', 'student@ktu.edu.gh', 'Test Student', 'CS001', '200', 'M', student_password, 'student', True, True))
    
    conn.commit()
    conn.close()
    print("Simple database initialized successfully!")

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
        username = request.form['username'].strip()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        full_name = request.form['full_name'].strip()
        index_number = request.form['index_number'].strip()
        level = request.form['level'].strip()
        gender = request.form['gender'].strip()
        password = request.form['password']
        
        if not email.endswith('@ktu.edu.gh'):
            flash('Please use your institutional email (@ktu.edu.gh)', 'danger')
            return render_template('register.html')
        
        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        
        if existing:
            flash('Username or email already exists.', 'danger')
            conn.close()
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        
        try:
            conn.execute('''
                INSERT INTO users (username, email, full_name, index_number, level, gender, password, role, is_verified, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, full_name, index_number, level, gender, password_hash, 'student', True, True))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if g.user is None:
        return redirect(url_for('login'))
    
    if g.user['role'] == 'supa_admin':
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
    if g.user is None or g.user['role'] != 'supa_admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get statistics
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = "student"').fetchone()['count']
    total_issues = conn.execute('SELECT COUNT(*) as count FROM issues').fetchone()['count']
    pending_issues = conn.execute('SELECT COUNT(*) as count FROM issues WHERE status = "pending"').fetchone()['count']
    resolved_issues = conn.execute('SELECT COUNT(*) as count FROM issues WHERE status = "resolved"').fetchone()['count']
    
    # Get recent issues
    recent_issues = conn.execute('''
        SELECT i.*, u.full_name as student_name 
        FROM issues i 
        JOIN users u ON i.student_id = u.id 
        ORDER BY i.created_at DESC 
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    stats = {
        'total_users': total_users,
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'resolved_issues': resolved_issues
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats,
                         recent_issues=recent_issues,
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
        
        conn.execute('''
            INSERT INTO issues (student_id, subject, category, message, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (g.user['id'], subject, category, message, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        
        flash('Issue submitted successfully!', 'success')
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    conn.close()
    return render_template('submit_issue.html', categories=categories)

@app.route('/my_issues')
def my_issues():
    if g.user is None or g.user['role'] != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    issues = conn.execute('''
        SELECT * FROM issues 
        WHERE student_id = ?
        ORDER BY created_at DESC
    ''', (g.user['id'],)).fetchall()
    conn.close()
    
    return render_template('my_issues.html', issues=issues)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("Initializing database...")
    init_simple_db()
    print("Starting KTU Student Report System...")
    print("Default login credentials:")
    print("Admin: username=admin, password=admin123")
    print("Student: username=student1, password=student123")
    print("Server running at: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
