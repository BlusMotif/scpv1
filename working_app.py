from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "student-report-system-secret-key"

# Database setup
def init_db():
    conn = sqlite3.connect('university_issues.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            is_verified BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create issues table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Insert default admin user if not exists
    cursor.execute('SELECT * FROM users WHERE email = ?', ('admin@ktu.edu.gh',))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (email, password, full_name, role, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin@ktu.edu.gh', generate_password_hash('admin123'), 'Super Admin', 'supa_admin', 1))

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('university_issues.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
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
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']

            flash('Login successful!', 'success')

            if user['role'] == 'supa_admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'subadmin':
                return redirect(url_for('subadmin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        full_name = request.form['full_name']

        if not email.endswith('@ktu.edu.gh'):
            flash('Please use your institutional email (@ktu.edu.gh).', 'danger')
            return render_template('register.html')

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if existing_user:
            flash('Email already registered.', 'danger')
            conn.close()
            return render_template('register.html')

        conn.execute('''
            INSERT INTO users (email, password, full_name, role, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, generate_password_hash(password), full_name, 'student', 1))

        conn.commit()
        conn.close()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/student-dashboard')
def student_dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    issues = conn.execute('''
        SELECT * FROM issues WHERE user_id = ? ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()

    return render_template('student_dashboard.html', issues=issues)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Get statistics
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_issues = conn.execute('SELECT COUNT(*) FROM issues').fetchone()[0]
    pending_issues = conn.execute('SELECT COUNT(*) FROM issues WHERE status = "pending"').fetchone()[0]

    # Get recent issues
    recent_issues = conn.execute('''
        SELECT i.*, u.full_name, u.email 
        FROM issues i 
        JOIN users u ON i.user_id = u.id 
        ORDER BY i.created_at DESC 
        LIMIT 10
    ''').fetchall()

    conn.close()

    stats = {
        'total_users': total_users,
        'total_issues': total_issues,
        'pending_issues': pending_issues
    }

    return render_template('admin_dashboard.html', stats=stats, recent_issues=recent_issues)

@app.route('/subadmin-dashboard')
def subadmin_dashboard():
    if 'user_role' not in session or session['user_role'] not in ['subadmin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    issues = conn.execute('''
        SELECT i.*, u.full_name, u.email 
        FROM issues i 
        JOIN users u ON i.user_id = u.id 
        ORDER BY i.created_at DESC
    ''').fetchall()
    conn.close()

    return render_template('subadmin_dashboard.html', issues=issues)

@app.route('/submit-issue', methods=['GET', 'POST'])
def submit_issue():
    if 'user_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO issues (user_id, title, description, category, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], title, description, category, 'pending'))

        conn.commit()
        conn.close()

        flash('Issue submitted successfully!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('submit_issue.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    print("Starting Student Report System...")
    print("Server will be available at: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)