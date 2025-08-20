from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import os

# Firebase integration
from firebase_config import RealtimeDB, initialize_firebase

app = Flask(__name__)
app.secret_key = "student-report-system-firebase-secret-key"

# Initialize Firebase and Database
initialize_firebase()
firebase_db = RealtimeDB()

def init_default_users():
    """Initialize default users if they don't exist"""
    try:
        # Check if admin user exists
        admin_user = firebase_db.get_user_by_email('admin@ktu.edu.gh')
        if not admin_user:
            admin_data = {
                'email': 'admin@ktu.edu.gh',
                'password': generate_password_hash('admin123'),
                'full_name': 'Super Admin',
                'role': 'supa_admin',
                'is_verified': True,
                'created_at': datetime.now().isoformat()
            }
            firebase_db.add_user(admin_data)
            print("Default admin user created")

    except Exception as e:
        print(f"Error initializing default users: {e}")

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        user = firebase_db.get_user_by_email(email)

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

        existing_user = firebase_db.get_user_by_email(email)

        if existing_user:
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        user_data = {
            'email': email,
            'password': generate_password_hash(password),
            'full_name': full_name,
            'role': 'student',
            'is_verified': True,
            'created_at': datetime.now().isoformat()
        }

        user_id = firebase_db.add_user(user_data)

        if user_id:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'danger')

    return render_template('register.html')

@app.route('/student-dashboard')
def student_dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    issues = firebase_db.get_issues(user_id=session['user_id'])
    return render_template('student_dashboard.html', issues=issues)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    # Get statistics
    stats = firebase_db.get_statistics()

    # Get recent issues with user info
    recent_issues = firebase_db.get_issues_with_user_info(limit=10)

    return render_template('admin_dashboard.html', stats=stats, recent_issues=recent_issues)

@app.route('/subadmin-dashboard')
def subadmin_dashboard():
    if 'user_role' not in session or session['user_role'] not in ['subadmin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    issues = firebase_db.get_issues_with_user_info()
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

        issue_data = {
            'user_id': session['user_id'],
            'title': title,
            'description': description,
            'category': category,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }

        issue_id = firebase_db.add_issue(issue_data)

        if issue_id:
            flash('Issue submitted successfully!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Failed to submit issue. Please try again.', 'danger')

    return render_template('submit_issue.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("Initializing Firebase Realtime Database...")
    init_default_users()
    print("Firebase Student Report System initialized successfully!")
    print("Server will be available at: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)