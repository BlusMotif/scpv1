import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash
from email_utils import send_verification_email, generate_verification_code, validate_institutional_email, generate_reset_token, send_password_reset_email
from database import init_db

# Firebase integration
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_auth import FirebaseAuth

# Initialize Firebase
try:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully")
    
    # Initialize Firestore
    db = firestore.client()
    print("Firestore client initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    db = None

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

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        try:
            # Get user from Firebase/Firestore
            if db:
                user_doc = db.collection('users').document(user_id).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    g.user = {
                        'id': user_id,
                        'email': user_data.get('email'),
                        'full_name': user_data.get('full_name'),
                        'role': user_data.get('role', 'student'),
                        'username': user_data.get('username'),
                        'index_number': user_data.get('index_number'),
                        'level': user_data.get('level'),
                        'gender': user_data.get('gender'),
                        'is_verified': user_data.get('is_verified', False)
                    }
                else:
                    g.user = None
            else:
                # Fallback to session data
                g.user = {
                    'id': user_id,
                    'email': session.get('user_email'),
                    'full_name': session.get('user_name'),
                    'role': session.get('user_role', 'student')
                }
        except Exception as e:
            print(f"Error loading user: {e}")
            g.user = None

@app.route('/')
def index():
    if g.user:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

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
        if not all([username, email, full_name, index_number, level, gender, password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        # Validate institutional email
        if not validate_institutional_email(email):
            flash('Please use your institutional email address (@ktu.edu.gh).', 'danger')
            return render_template('register.html')

        try:
            # Check if user already exists in Firebase
            existing_user = FirebaseAuth.get_user_by_email(email)
            if existing_user:
                flash('Email already exists.', 'danger')
                return render_template('register.html')

            # Create Firebase user
            firebase_user = FirebaseAuth.create_user(
                email=email,
                password=password,
                display_name=full_name,
                email_verified=False
            )

            if firebase_user:
                # Store additional user data in Firestore
                user_data = {
                    'uid': firebase_user.uid,
                    'username': username,
                    'email': email,
                    'full_name': full_name,
                    'index_number': index_number,
                    'level': level,
                    'gender': gender,
                    'role': 'student',
                    'is_verified': False,
                    'created_at': datetime.now()
                }
                
                if db:
                    db.collection('users').document(firebase_user.uid).set(user_data)

                # Generate email verification link
                verification_link = FirebaseAuth.generate_email_verification_link(email)
                if verification_link:
                    # Send verification email with Firebase link
                    flash('Registration successful! Please check your email for verification link.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Registration successful! Please verify your email before logging in.', 'success')
                    return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
                return render_template('register.html')

        except Exception as e:
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        code = request.form.get('verification_code', '').strip()
        
        if not email or not code:
            flash('Email and verification code are required.', 'danger')
            return render_template('verify_email.html')
        
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? AND verification_code = ? AND is_verified = 0',
            (email, code)
        ).fetchone()
        
        if user:
            # Check if verification code has expired
            if user['verification_expires'] and datetime.now() > datetime.fromisoformat(user['verification_expires']):
                flash('Verification code has expired. Please register again.', 'danger')
                conn.close()
                return render_template('verify_email.html')
            
            # Activate the user account
            conn.execute(
                'UPDATE users SET is_verified = 1, verification_code = NULL, verification_expires = NULL WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            conn.close()
            
            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid email or verification code.', 'danger')
            conn.close()
            return render_template('verify_email.html')
    
    return render_template('verify_email.html')

@app.route('/resend-verification')
def resend_verification():
    if 'pending_verification' not in session:
        return redirect(url_for('register'))
    
    username = session['pending_verification']
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if user:
        verification_code = generate_verification_code()
        conn.execute('UPDATE users SET verification_code = ? WHERE username = ?', (verification_code, username))
        conn.commit()
        
        send_verification_email(user['email'], verification_code, user['full_name'])
        flash('Verification code resent to your email.', 'info')
    
    conn.close()
    return redirect(url_for('verify_email'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        try:
            # Get Firebase user by email
            firebase_user = FirebaseAuth.get_user_by_email(email)
            
            if firebase_user:
                # Check if email is verified
                if not firebase_user.email_verified:
                    flash('Please verify your email address before logging in.', 'warning')
                    return render_template('login.html')
                
                # Get user data from Firestore
                if db:
                    user_doc = db.collection('users').document(firebase_user.uid).get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        
                        # Store user session
                        session['user_id'] = firebase_user.uid
                        session['user_email'] = firebase_user.email
                        session['user_role'] = user_data.get('role', 'student')
                        session['user_name'] = user_data.get('full_name', '')
                        
                        flash('Login successful!', 'success')
                        
                        # Redirect based on role
                        if user_data.get('role') == 'supa_admin':
                            return redirect(url_for('admin.admin_dashboard'))
                        elif user_data.get('role') == 'subadmin':
                            return redirect(url_for('admin.subadmin_dashboard'))
                        else:
                            return redirect(url_for('dashboard'))
                    else:
                        flash('User profile not found.', 'danger')
                else:
                    # Fallback if Firestore is not available
                    session['user_id'] = firebase_user.uid
                    session['user_email'] = firebase_user.email
                    session['user_role'] = 'student'
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
                
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login failed. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        
        # Validate institutional email
        if not validate_institutional_email(email):
            flash('Please use your institutional email (@ktu.edu.gh)', 'danger')
            return render_template('forgot_password.html')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            reset_token = generate_reset_token()
            conn.execute('UPDATE users SET reset_token = ?, reset_token_expires = datetime("now", "+1 hour") WHERE email = ?', (reset_token, email))
            conn.commit()
            
            send_password_reset_email(email, reset_token, user['full_name'])
            flash('If the email exists, a password reset link has been sent to your email.', 'success')
        else:
            flash('If the email exists, a password reset link has been sent to your email.', 'success')
        
        conn.close()
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE reset_token = ? AND reset_token_expires > datetime("now")', (token,)).fetchone()
    
    if not user:
        conn.close()
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        password_hash = generate_password_hash(new_password)
        conn.execute('UPDATE users SET password = ?, reset_token = NULL, reset_token_expires = NULL WHERE reset_token = ?', (password_hash, token))
        conn.commit()
        conn.close()
        
        flash('Password reset successfully. Please log in with your new password.', 'success')
        return redirect(url_for('login'))
    
    conn.close()
    return render_template('reset_password.html', token=token)

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
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn.execute(
            'INSERT INTO issues (student_id, subject, category, message, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (g.user['id'], subject, category, message, 'pending', created_at)
        )
        conn.commit()
        conn.close()
        
        flash('Issue submitted successfully.', 'success')
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
        WHERE student_id = (SELECT id FROM users WHERE username = ?)
        ORDER BY created_at DESC
    ''', (g.user['username'],)).fetchall()
    conn.close()
    
    return render_template('my_issues.html', issues=issues, parse_datetime=parse_datetime)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if g.user is None:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (g.user['username'],)).fetchone()
    
    if request.method == 'POST':
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        error = None
        if password:
            if password != password_confirm:
                error = 'Passwords do not match.'
            else:
                password_hash = generate_password_hash(password)
                conn.execute('UPDATE users SET password = ? WHERE username = ?', (password_hash, g.user['username']))
                conn.commit()
        
        if error:
            flash(error, 'danger')
        else:
            flash('Settings updated successfully.', 'success')
    
    conn.close()
    return render_template('settings.html', user=user)

@app.route('/about')
def about():
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM system_settings').fetchall()
    conn.close()
    
    site_settings = {setting['key']: setting['value'] for setting in settings}
    return render_template('about.html', settings=site_settings)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
