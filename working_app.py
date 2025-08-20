
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import os

def parse_datetime(date_string):
    """Parse datetime string for template display"""
    try:
        if isinstance(date_string, str):
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        return str(date_string)
    except:
        return str(date_string)

# Firebase integration
from firebase_config import RealtimeDB, initialize_firebase

app = Flask(__name__)
app.secret_key = "student-report-system-firebase-secret-key"

@app.context_processor
def utility_processor():
    return dict(parse_datetime=parse_datetime)

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
            user_id = firebase_db.add_user(admin_data)
            if user_id:
                print("Default admin user created successfully")
            else:
                print("Failed to create default admin user")

        # Check if subadmin user exists
        subadmin_user = firebase_db.get_user_by_email('subadmin@ktu.edu.gh')
        if not subadmin_user:
            subadmin_data = {
                'email': 'subadmin@ktu.edu.gh',
                'password': generate_password_hash('subadmin123'),
                'full_name': 'Sub Admin',
                'role': 'subadmin',
                'is_verified': True,
                'created_at': datetime.now().isoformat()
            }
            user_id = firebase_db.add_user(subadmin_data)
            if user_id:
                print("Default subadmin user created successfully")

        # Check if student user exists
        student_user = firebase_db.get_user_by_email('student@ktu.edu.gh')
        if not student_user:
            student_data = {
                'email': 'student@ktu.edu.gh',
                'password': generate_password_hash('student123'),
                'full_name': 'Test Student',
                'role': 'student',
                'is_verified': True,
                'created_at': datetime.now().isoformat()
            }
            user_id = firebase_db.add_user(student_data)
            if user_id:
                print("Default student user created successfully")

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
    
    # Calculate statistics for student dashboard
    total_issues = len(issues)
    pending = len([i for i in issues if i.get('status') == 'pending'])
    in_progress = len([i for i in issues if i.get('status') == 'in_progress'])
    resolved = len([i for i in issues if i.get('status') == 'resolved'])
    
    stats = {
        'total': total_issues,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved
    }
    
    return render_template('student_dashboard.html', issues=issues, stats=stats)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    # Get statistics
    stats = firebase_db.get_statistics()
    
    # Get all users for user statistics
    all_users = firebase_db.get_all_users()
    
    # Calculate user statistics
    total_users = len(all_users)
    students = len([u for u in all_users if u.get('role') == 'student'])
    subadmins = len([u for u in all_users if u.get('role') == 'subadmin'])
    verified_users = len([u for u in all_users if u.get('is_verified')])
    
    user_stats = {
        'total_users': total_users,
        'students': students,
        'subadmins': subadmins,
        'verified_users': verified_users
    }
    
    # Get all issues for enhanced statistics
    all_issues = firebase_db.get_issues()
    
    # Calculate enhanced stats
    stats['total'] = len(all_issues)
    stats['pending'] = len([i for i in all_issues if i.get('status') == 'pending'])
    stats['in_progress'] = len([i for i in all_issues if i.get('status') == 'in_progress'])
    stats['resolved'] = len([i for i in all_issues if i.get('status') == 'resolved'])

    # Get recent issues with user info
    issues = firebase_db.get_issues_with_user_info(limit=20)
    
    # Mock data for charts (you can enhance this with real data later)
    daily_stats = []
    category_stats = []
    recent_activities = []
    notifications = []

    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         user_stats=user_stats,
                         issues=issues,
                         daily_stats=daily_stats,
                         category_stats=category_stats,
                         recent_activities=recent_activities,
                         notifications=notifications)

@app.route('/subadmin-dashboard')
def subadmin_dashboard():
    if 'user_role' not in session or session['user_role'] not in ['subadmin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    issues = firebase_db.get_issues_with_user_info()
    
    # Calculate statistics for subadmin dashboard
    total_issues = len(issues)
    pending_issues = len([i for i in issues if i.get('status') == 'pending'])
    in_progress_issues = len([i for i in issues if i.get('status') == 'in_progress'])
    resolved_issues = len([i for i in issues if i.get('status') == 'resolved'])
    
    stats = {
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'in_progress_issues': in_progress_issues,
        'resolved_issues': resolved_issues
    }
    
    return render_template('subadmin_dashboard.html', issues=issues, stats=stats)

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

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        
        if not email.endswith('@ktu.edu.gh'):
            flash('Please use your institutional email (@ktu.edu.gh).', 'danger')
            return render_template('forgot_password.html')
        
        user = firebase_db.get_user_by_email(email)
        if user:
            flash('If this email exists in our system, you will receive password reset instructions.', 'info')
        else:
            flash('If this email exists in our system, you will receive password reset instructions.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/manage-users')
def manage_users():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    users = firebase_db.get_all_users()
    return render_template('manage_subadmins.html', users=users)

@app.route('/create-subadmin', methods=['GET', 'POST'])
def create_subadmin():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        full_name = request.form['full_name']

        if not email.endswith('@ktu.edu.gh'):
            flash('Please use institutional email (@ktu.edu.gh).', 'danger')
            return render_template('create_subadmin.html')

        existing_user = firebase_db.get_user_by_email(email)
        if existing_user:
            flash('Email already registered.', 'danger')
            return render_template('create_subadmin.html')

        user_data = {
            'email': email,
            'password': generate_password_hash(password),
            'full_name': full_name,
            'role': 'subadmin',
            'is_verified': True,
            'created_at': datetime.now().isoformat()
        }

        user_id = firebase_db.add_user(user_data)
        if user_id:
            flash('Sub-admin created successfully!', 'success')
            return redirect(url_for('manage_users'))
        else:
            flash('Failed to create sub-admin.', 'danger')

    return render_template('create_subadmin.html')

@app.route('/update-issue-status/<issue_id>', methods=['POST'])
def update_issue_status(issue_id):
    if 'user_role' not in session or session['user_role'] not in ['subadmin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    new_status = request.form['status']
    success = firebase_db.update_issue(issue_id, {'status': new_status})
    
    if success:
        flash('Issue status updated successfully!', 'success')
    else:
        flash('Failed to update issue status.', 'danger')
    
    return redirect(url_for('subadmin_dashboard'))

@app.route('/delete-issue/<issue_id>', methods=['POST'])
def delete_issue(issue_id):
    if 'user_role' not in session or session['user_role'] not in ['subadmin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    success = firebase_db.delete_issue(issue_id)
    
    if success:
        flash('Issue deleted successfully!', 'success')
    else:
        flash('Failed to delete issue.', 'danger')
    
    return redirect(url_for('subadmin_dashboard'))

@app.route('/my-issues')
def my_issues():
    if 'user_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    issues = firebase_db.get_issues(user_id=session['user_id'])
    return render_template('my_issues.html', issues=issues)

@app.route('/admin/system-settings', methods=['GET', 'POST'])
def system_settings():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle system settings updates in Firebase
        settings_data = {
            'app_name': request.form.get('app_name', 'Student Report System'),
            'maintenance_mode': request.form.get('maintenance_mode') == 'on',
            'email_notifications': request.form.get('email_notifications') == 'on',
            'max_issues_per_user': int(request.form.get('max_issues_per_user', 10)),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save settings to Firebase
        try:
            settings_ref = firebase_db.db_ref.child('system_settings')
            settings_ref.set(settings_data)
            flash('System settings updated successfully!', 'success')
        except Exception as e:
            flash('Failed to update system settings.', 'danger')
            print(f"Error updating settings: {e}")
    
    # Get current settings from Firebase
    try:
        settings_ref = firebase_db.db_ref.child('system_settings')
        current_settings = settings_ref.get() or {}
    except Exception as e:
        current_settings = {}
        print(f"Error getting settings: {e}")
    
    # Group settings by category for template
    settings_by_category = {
        'General': [
            {'key': 'app_name', 'name': 'Application Name', 'value': current_settings.get('app_name', 'Student Report System'), 'type': 'text'},
        ],
        'System': [
            {'key': 'maintenance_mode', 'name': 'Maintenance Mode', 'value': current_settings.get('maintenance_mode', False), 'type': 'checkbox'},
            {'key': 'email_notifications', 'name': 'Email Notifications', 'value': current_settings.get('email_notifications', True), 'type': 'checkbox'},
            {'key': 'max_issues_per_user', 'name': 'Max Issues Per User', 'value': current_settings.get('max_issues_per_user', 10), 'type': 'number'},
        ]
    }
    
    return render_template('system_settings.html', settings=current_settings, settings_by_category=settings_by_category)

@app.route('/admin/users/update-role/<user_id>', methods=['POST'])
def update_user_role(user_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    new_role = request.form.get('role')
    if new_role in ['student', 'subadmin', 'supa_admin']:
        success = firebase_db.update_user(user_id, {'role': new_role})
        if success:
            flash('User role updated successfully!', 'success')
        else:
            flash('Failed to update user role.', 'danger')
    else:
        flash('Invalid role specified.', 'danger')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    # Don't allow deletion of the current user
    if user_id == session['user_id']:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))

    try:
        user_ref = firebase_db.db_ref.child('users').child(user_id)
        user_ref.delete()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash('Failed to delete user.', 'danger')
        print(f"Error deleting user: {e}")
    
    return redirect(url_for('manage_users'))

@app.route('/about')
def about():
    return render_template('about.html')

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
    app.run(host='0.0.0.0', port=5000, debug=False)
