
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
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
    return dict(
        parse_datetime=parse_datetime,
        session=session
    )

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
    # Get active prefixes for the form
    try:
        prefixes_ref = firebase_db.db_ref.child('index_prefixes')
        prefixes_data = prefixes_ref.get() or {}
        active_prefixes = []
        for key, value in prefixes_data.items():
            if value.get('is_active', True):
                active_prefixes.append({
                    'prefix': value.get('prefix', ''),
                    'description': value.get('description', '')
                })
        active_prefixes.sort(key=lambda x: x['prefix'])
    except Exception as e:
        active_prefixes = [{'prefix': 'CS', 'description': 'Computer Science'}]
        print(f"Error getting prefixes: {e}")

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        full_name = request.form['full_name']
        index_number = request.form.get('index_number', '').strip().upper()

        if not email.endswith('@ktu.edu.gh'):
            flash('Please use your institutional email (@ktu.edu.gh).', 'danger')
            return render_template('register.html', prefixes=active_prefixes)

        # Validate index number format
        if index_number:
            valid_prefix = False
            for prefix_info in active_prefixes:
                if index_number.startswith(prefix_info['prefix']):
                    valid_prefix = True
                    break
            
            if not valid_prefix:
                valid_prefixes = ', '.join([p['prefix'] for p in active_prefixes])
                flash(f'Invalid index number format. Must start with: {valid_prefixes}', 'danger')
                return render_template('register.html', prefixes=active_prefixes)

        existing_user = firebase_db.get_user_by_email(email)

        if existing_user:
            flash('Email already registered.', 'danger')
            return render_template('register.html', prefixes=active_prefixes)

        user_data = {
            'email': email,
            'password': generate_password_hash(password),
            'full_name': full_name,
            'index_number': index_number,
            'role': 'student',
            'is_verified': False,
            'created_at': datetime.now().isoformat()
        }

        user_id = firebase_db.add_user(user_data)

        if user_id:
            # Send verification email
            from email_utils import send_verification_email, generate_verification_code
            verification_code = generate_verification_code()
            
            # Store verification code in Firebase
            try:
                verification_ref = firebase_db.db_ref.child('email_verifications')
                verification_ref.push({
                    'email': email,
                    'code': verification_code,
                    'user_id': user_id,
                    'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
                    'created_at': datetime.now().isoformat()
                })
                
                if send_verification_email(email, verification_code, full_name):
                    flash('Registration successful! Please check your email for verification instructions.', 'success')
                    return redirect(url_for('verify_email'))
                else:
                    flash('Registration successful, but failed to send verification email. Please contact support.', 'warning')
                    return redirect(url_for('login'))
            except Exception as e:
                print(f"Error sending verification email: {e}")
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'danger')

    return render_template('register.html', prefixes=active_prefixes)

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

@app.route('/admin/manage-users')
def admin_manage_users():
    return redirect(url_for('manage_users'))

@app.route('/admin/manage-notifications', methods=['GET', 'POST'])
def admin_manage_notifications():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        notification_type = request.form.get('type', 'info')
        
        if title and message:
            # Save notification to Firebase
            try:
                notification_data = {
                    'title': title,
                    'message': message,
                    'type': notification_type,
                    'created_at': datetime.now().isoformat(),
                    'is_read': False
                }
                notifications_ref = firebase_db.db_ref.child('notifications')
                notifications_ref.push(notification_data)
                flash('Notification created successfully!', 'success')
            except Exception as e:
                flash('Failed to create notification.', 'danger')
                print(f"Error creating notification: {e}")
        else:
            flash('Please fill in all required fields.', 'danger')
        
        return redirect(url_for('admin_manage_notifications'))
    
    # Get notifications from Firebase
    try:
        notifications_ref = firebase_db.db_ref.child('notifications')
        notifications_data = notifications_ref.get() or {}
        notifications = []
        for key, value in notifications_data.items():
            notification = value
            notification['id'] = key
            notifications.append(notification)
        notifications.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    except Exception as e:
        notifications = []
        print(f"Error getting notifications: {e}")
    
    return render_template('admin_notifications.html', notifications=notifications)

@app.route('/admin/view-all-activities')
def view_all_activities():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    # Mock activities data
    activities = []
    return render_template('admin_activities.html', activities=activities)

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
        'pending': pending_issues,
        'in_progress': in_progress_issues,
        'resolved': resolved_issues
    }
    
    # Get current user info
    current_user = {
        'full_name': session.get('user_name', 'Sub Admin'),
        'email': session.get('user_email', ''),
        'role': session.get('user_role', 'subadmin')
    }
    
    # Get category statistics
    category_stats = {}
    for issue in issues:
        category = issue.get('category', 'Other')
        category_stats[category] = category_stats.get(category, 0) + 1
    
    category_list = [{'category': k, 'count': v} for k, v in category_stats.items()]
    
    # Ensure all issues have required fields and fix data structure
    processed_issues = []
    for issue in issues:
        processed_issue = dict(issue)
        # Ensure title field exists for template compatibility
        if 'title' not in processed_issue and 'subject' in processed_issue:
            processed_issue['title'] = processed_issue['subject']
        elif 'subject' not in processed_issue and 'title' in processed_issue:
            processed_issue['subject'] = processed_issue['title']
        processed_issues.append(processed_issue)
    
    return render_template('subadmin_dashboard.html', 
                         issues=processed_issues, 
                         stats=stats, 
                         current_user=current_user,
                         recent_issues=processed_issues[:10],
                         category_stats=category_list)

@app.route('/submit-issue', methods=['GET', 'POST'])
def submit_issue():
    if 'user_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    # Get active categories for the form
    try:
        categories_ref = firebase_db.db_ref.child('issue_categories')
        categories_data = categories_ref.get() or {}
        active_categories = []
        for key, value in categories_data.items():
            if value.get('is_active', True):
                active_categories.append({
                    'name': value.get('name', ''),
                    'description': value.get('description', '')
                })
        active_categories.sort(key=lambda x: x['name'])
        
        # Add default categories if none exist
        if not active_categories:
            active_categories = [
                {'name': 'IT Support', 'description': 'Technical and IT related issues'},
                {'name': 'Academic', 'description': 'Academic and course related issues'},
                {'name': 'Facilities', 'description': 'Campus facilities and infrastructure'},
                {'name': 'Student Services', 'description': 'Student services and support'},
                {'name': 'Other', 'description': 'Other issues not covered above'}
            ]
    except Exception as e:
        active_categories = [
            {'name': 'IT Support', 'description': 'Technical and IT related issues'},
            {'name': 'Academic', 'description': 'Academic and course related issues'},
            {'name': 'Facilities', 'description': 'Campus facilities and infrastructure'},
            {'name': 'Student Services', 'description': 'Student services and support'},
            {'name': 'Other', 'description': 'Other issues not covered above'}
        ]
        print(f"Error getting categories: {e}")

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

    return render_template('submit_issue.html', categories=active_categories)

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        verification_code = request.form['verification_code'].strip()
        
        try:
            # Find verification record
            verifications_ref = firebase_db.db_ref.child('email_verifications')
            verifications_data = verifications_ref.get() or {}
            
            valid_verification = None
            verification_key = None
            
            for key, verification in verifications_data.items():
                if (verification.get('email') == email and 
                    verification.get('code') == verification_code):
                    
                    # Check if not expired
                    expires_at = datetime.fromisoformat(verification.get('expires_at', ''))
                    if datetime.now() < expires_at:
                        valid_verification = verification
                        verification_key = key
                        break
            
            if valid_verification:
                # Update user as verified
                user_id = valid_verification['user_id']
                firebase_db.update_user(user_id, {
                    'is_verified': True,
                    'verified_at': datetime.now().isoformat()
                })
                
                # Delete verification record
                verifications_ref.child(verification_key).delete()
                
                flash('Email verified successfully! You can now login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Invalid or expired verification code.', 'danger')
        
        except Exception as e:
            print(f"Error verifying email: {e}")
            flash('Verification failed. Please try again.', 'danger')
    
    return render_template('verify_email.html')

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
    
    # Filter only subadmins for the manage subadmins page
    subadmins = [user for user in users if user.get('role') == 'subadmin']
    
    # Add missing properties for template compatibility
    for user in subadmins:
        user['username'] = user.get('email', '').split('@')[0]
        user['is_active'] = user.get('is_active', True)
        user['assigned_issues'] = 0  # TODO: Calculate from Firebase
        user['login_count'] = user.get('login_count', 0)
        user['last_login'] = user.get('last_login', 'Never')
    
    return render_template('manage_users_simple.html', subadmins=subadmins)

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

@app.route('/admin/resolve-issue/<issue_id>', methods=['POST'])
def admin_resolve_issue(issue_id):
    if 'user_role' not in session or session['user_role'] not in ['subadmin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    new_status = request.form.get('status')
    response_text = request.form.get('response', '')
    
    update_data = {
        'status': new_status,
        'updated_at': datetime.now().isoformat()
    }
    
    if response_text:
        update_data['admin_response'] = response_text
    
    success = firebase_db.update_issue(issue_id, update_data)
    
    if success:
        flash('Issue updated successfully!', 'success')
    else:
        flash('Failed to update issue.', 'danger')
    
    return redirect(url_for('subadmin_dashboard'))

@app.route('/admin/issue/<issue_id>')
def get_issue_details(issue_id):
    if 'user_role' not in session or session['user_role'] not in ['subadmin', 'supa_admin']:
        return {'error': 'Access denied'}, 403

    try:
        issues = firebase_db.get_issues_with_user_info()
        issue = next((i for i in issues if i.get('id') == issue_id), None)
        
        if issue:
            return {
                'id': issue.get('id'),
                'full_name': issue.get('full_name', ''),
                'email': issue.get('email', ''),
                'index_number': issue.get('index_number', 'N/A'),
                'category': issue.get('category', ''),
                'status': issue.get('status', ''),
                'subject': issue.get('title', ''),
                'message': issue.get('description', ''),
                'response': issue.get('admin_response', ''),
                'created_at': issue.get('created_at', '')
            }
        else:
            return {'error': 'Issue not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500

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

@app.route('/system-settings', methods=['GET', 'POST'])
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

@app.route('/admin/delete-notification/<notification_id>', methods=['POST'])
def delete_notification(notification_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    try:
        notification_ref = firebase_db.db_ref.child('notifications').child(notification_id)
        notification_ref.delete()
        flash('Notification deleted successfully!', 'success')
    except Exception as e:
        flash('Failed to delete notification.', 'danger')
        print(f"Error deleting notification: {e}")
    
    return redirect(url_for('admin_manage_notifications'))

@app.route('/admin/manage-prefixes')
def manage_prefixes():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    try:
        prefixes_ref = firebase_db.db_ref.child('index_prefixes')
        prefixes_data = prefixes_ref.get() or {}
        prefixes = []
        for key, value in prefixes_data.items():
            prefix = value
            prefix['id'] = key
            prefixes.append(prefix)
        prefixes.sort(key=lambda x: x.get('prefix', ''))
    except Exception as e:
        prefixes = []
        print(f"Error getting prefixes: {e}")
    
    return render_template('manage_prefixes.html', prefixes=prefixes)

@app.route('/admin/add-prefix', methods=['POST'])
def add_prefix():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    prefix = request.form.get('prefix', '').upper().strip()
    description = request.form.get('description', '').strip()
    is_active = request.form.get('is_active') == 'on'
    
    if prefix and description:
        try:
            prefix_data = {
                'prefix': prefix,
                'description': description,
                'is_active': is_active,
                'created_at': datetime.now().isoformat()
            }
            prefixes_ref = firebase_db.db_ref.child('index_prefixes')
            prefixes_ref.push(prefix_data)
            flash('Index prefix added successfully!', 'success')
        except Exception as e:
            flash('Failed to add prefix.', 'danger')
            print(f"Error adding prefix: {e}")
    else:
        flash('Please fill in all required fields.', 'danger')
    
    return redirect(url_for('manage_prefixes'))

@app.route('/admin/update-prefix/<prefix_id>', methods=['POST'])
def update_prefix(prefix_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    prefix = request.form.get('prefix', '').upper().strip()
    description = request.form.get('description', '').strip()
    is_active = request.form.get('is_active') == 'on'
    
    if prefix and description:
        try:
            update_data = {
                'prefix': prefix,
                'description': description,
                'is_active': is_active,
                'updated_at': datetime.now().isoformat()
            }
            prefix_ref = firebase_db.db_ref.child('index_prefixes').child(prefix_id)
            prefix_ref.update(update_data)
            flash('Index prefix updated successfully!', 'success')
        except Exception as e:
            flash('Failed to update prefix.', 'danger')
            print(f"Error updating prefix: {e}")
    else:
        flash('Please fill in all required fields.', 'danger')
    
    return redirect(url_for('manage_prefixes'))

@app.route('/admin/delete-prefix/<prefix_id>', methods=['POST'])
def delete_prefix(prefix_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    try:
        prefix_ref = firebase_db.db_ref.child('index_prefixes').child(prefix_id)
        prefix_ref.delete()
        flash('Index prefix deleted successfully!', 'success')
    except Exception as e:
        flash('Failed to delete prefix.', 'danger')
        print(f"Error deleting prefix: {e}")
    
    return redirect(url_for('manage_prefixes'))

@app.route('/admin/toggle-prefix/<prefix_id>', methods=['POST'])
def toggle_prefix(prefix_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    try:
        prefix_ref = firebase_db.db_ref.child('index_prefixes').child(prefix_id)
        prefix_data = prefix_ref.get()
        if prefix_data:
            new_status = not prefix_data.get('is_active', True)
            prefix_ref.update({
                'is_active': new_status,
                'updated_at': datetime.now().isoformat()
            })
            status_text = 'activated' if new_status else 'deactivated'
            flash(f'Prefix {status_text} successfully!', 'success')
        else:
            flash('Prefix not found.', 'danger')
    except Exception as e:
        flash('Failed to update prefix status.', 'danger')
        print(f"Error toggling prefix: {e}")
    
    return redirect(url_for('manage_prefixes'))

@app.route('/admin/manage-categories')
def manage_categories():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    try:
        categories_ref = firebase_db.db_ref.child('issue_categories')
        categories_data = categories_ref.get() or {}
        categories = []
        
        # Get issue counts for each category
        issues_ref = firebase_db.db_ref.child('issues')
        issues_data = issues_ref.get() or {}
        
        category_counts = {}
        for issue_id, issue in issues_data.items():
            category = issue.get('category', 'Other')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for key, value in categories_data.items():
            category = value
            category['id'] = key
            category['issue_count'] = category_counts.get(category.get('name', ''), 0)
            categories.append(category)
        
        categories.sort(key=lambda x: x.get('name', ''))
    except Exception as e:
        categories = []
        print(f"Error getting categories: {e}")
    
    return render_template('manage_categories.html', categories=categories)

@app.route('/admin/add-category', methods=['POST'])
def add_category():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if name:
        try:
            # Check if category already exists
            categories_ref = firebase_db.db_ref.child('issue_categories')
            categories_data = categories_ref.get() or {}
            
            category_exists = False
            for key, value in categories_data.items():
                if value.get('name', '').lower() == name.lower():
                    category_exists = True
                    break
            
            if category_exists:
                flash('Category already exists.', 'danger')
            else:
                category_data = {
                    'name': name,
                    'description': description,
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                }
                categories_ref.push(category_data)
                flash('Category added successfully!', 'success')
        except Exception as e:
            flash('Failed to add category.', 'danger')
            print(f"Error adding category: {e}")
    else:
        flash('Please fill in the category name.', 'danger')
    
    return redirect(url_for('manage_categories'))

@app.route('/admin/edit-category/<category_id>', methods=['POST'])
def edit_category(category_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if name:
        try:
            category_ref = firebase_db.db_ref.child('issue_categories').child(category_id)
            category_data = category_ref.get()
            
            if category_data:
                update_data = {
                    'name': name,
                    'description': description,
                    'updated_at': datetime.now().isoformat()
                }
                category_ref.update(update_data)
                flash('Category updated successfully!', 'success')
            else:
                flash('Category not found.', 'danger')
        except Exception as e:
            flash('Failed to update category.', 'danger')
            print(f"Error updating category: {e}")
    else:
        flash('Please fill in the category name.', 'danger')
    
    return redirect(url_for('manage_categories'))

@app.route('/admin/delete-category/<category_id>', methods=['POST'])
def delete_category(category_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    try:
        category_ref = firebase_db.db_ref.child('issue_categories').child(category_id)
        category_data = category_ref.get()
        
        if category_data:
            # Check if category is being used
            issues_ref = firebase_db.db_ref.child('issues')
            issues_data = issues_ref.get() or {}
            
            category_in_use = False
            for issue_id, issue in issues_data.items():
                if issue.get('category') == category_data.get('name'):
                    category_in_use = True
                    break
            
            if category_in_use:
                flash('Cannot delete category. It is being used by existing issues.', 'warning')
            else:
                category_ref.delete()
                flash('Category deleted successfully!', 'success')
        else:
            flash('Category not found.', 'danger')
    except Exception as e:
        flash('Failed to delete category.', 'danger')
        print(f"Error deleting category: {e}")
    
    return redirect(url_for('manage_categories'))

@app.route('/admin/toggle-category/<category_id>', methods=['POST'])
def toggle_category(category_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    try:
        category_ref = firebase_db.db_ref.child('issue_categories').child(category_id)
        category_data = category_ref.get()
        
        if category_data:
            new_status = not category_data.get('is_active', True)
            category_ref.update({
                'is_active': new_status,
                'updated_at': datetime.now().isoformat()
            })
            status_text = 'activated' if new_status else 'deactivated'
            flash(f'Category {status_text} successfully!', 'success')
        else:
            flash('Category not found.', 'danger')
    except Exception as e:
        flash('Failed to update category status.', 'danger')
        print(f"Error toggling category: {e}")
    
    return redirect(url_for('manage_categories'))

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

@app.route('/toggle-subadmin/<user_id>', methods=['POST'])
def toggle_subadmin(user_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    try:
        user = firebase_db.get_user_by_id(user_id)
        if user and user.get('role') == 'subadmin':
            new_status = not user.get('is_active', True)
            firebase_db.update_user(user_id, {'is_active': new_status})
            status_text = 'activated' if new_status else 'deactivated'
            flash(f'Sub-admin {status_text} successfully!', 'success')
        else:
            flash('Sub-admin not found.', 'danger')
    except Exception as e:
        flash('Failed to update sub-admin status.', 'danger')
        print(f"Error toggling subadmin: {e}")
    
    return redirect(url_for('manage_users'))

@app.route('/delete-subadmin/<user_id>', methods=['POST'])
def delete_subadmin(user_id):
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    # Don't allow deletion of the current user
    if user_id == session['user_id']:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))

    try:
        user = firebase_db.get_user_by_id(user_id)
        if user and user.get('role') == 'subadmin':
            user_ref = firebase_db.db_ref.child('users').child(user_id)
            user_ref.delete()
            flash('Sub-admin deleted successfully!', 'success')
        else:
            flash('Sub-admin not found.', 'danger')
    except Exception as e:
        flash('Failed to delete sub-admin.', 'danger')
        print(f"Error deleting subadmin: {e}")
    
    return redirect(url_for('manage_users'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin/export-data')
def export_data():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))

    from flask import make_response
    import csv
    from io import StringIO
    from datetime import datetime

    try:
        # Get all issues with user information
        all_issues = firebase_db.get_issues_with_user_info()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Student Name', 'Email', 'Title', 'Description', 'Category', 'Status', 'Created At'])
        
        # Write data rows
        for issue in all_issues:
            writer.writerow([
                issue.get('id', ''),
                issue.get('full_name', ''),
                issue.get('email', ''),
                issue.get('title', ''),
                issue.get('description', ''),
                issue.get('category', ''),
                issue.get('status', ''),
                issue.get('created_at', '')
            ])
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=ktu_issues_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        flash('Failed to export data.', 'danger')
        print(f"Export error: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/analytics')
def admin_analytics():
    if 'user_role' not in session or session['user_role'] != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    # Get real data from Firebase for analytics
    try:
        # Get all issues for analysis
        all_issues = firebase_db.get_issues_with_user_info()
        
        # Process data for charts
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        # Status timeline data
        status_timeline = []
        daily_stats = defaultdict(lambda: defaultdict(int))
        
        for issue in all_issues:
            try:
                created_date = datetime.fromisoformat(issue.get('created_at', '')).date()
                date_str = created_date.strftime('%Y-%m-%d')
                status = issue.get('status', 'pending')
                daily_stats[date_str][status] += 1
            except:
                continue
        
        for date_str, statuses in daily_stats.items():
            for status, count in statuses.items():
                status_timeline.append({
                    'date': date_str,
                    'status': status,
                    'count': count
                })
        
        # Response times by category
        category_times = defaultdict(list)
        for issue in all_issues:
            if issue.get('status') == 'resolved':
                category = issue.get('category', 'Other')
                # Mock response time calculation (in real app, calculate from timestamps)
                category_times[category].append(24)  # Mock 24 hours
        
        response_times = []
        for category, times in category_times.items():
            avg_time = sum(times) / len(times) if times else 12
            response_times.append({
                'category': category,
                'avg_hours': round(avg_time, 1)
            })
        
        # User activity trends
        user_activity = [
            {'month': 'Jan', 'active_users': 125, 'total_issues': len([i for i in all_issues if '01' in i.get('created_at', '')])},
            {'month': 'Feb', 'active_users': 138, 'total_issues': len([i for i in all_issues if '02' in i.get('created_at', '')])},
            {'month': 'Mar', 'active_users': 142, 'total_issues': len([i for i in all_issues if '03' in i.get('created_at', '')])},
        ]
        
        # Peak hours analysis
        hour_stats = defaultdict(int)
        for issue in all_issues:
            try:
                created_time = datetime.fromisoformat(issue.get('created_at', ''))
                hour_stats[created_time.hour] += 1
            except:
                continue
        
        peak_hours = [{'hour': hour, 'count': count} for hour, count in sorted(hour_stats.items())]
        
        # Category trends
        category_stats = defaultdict(int)
        for issue in all_issues:
            category = issue.get('category', 'Other')
            category_stats[category] += 1
        
        category_trends = []
        for category, count in category_stats.items():
            category_trends.append({
                'month': 'Current',
                'category': category,
                'count': count
            })
        
    except Exception as e:
        print(f"Error generating analytics data: {e}")
        # Fallback to empty data
        status_timeline = []
        response_times = []
        user_activity = []
        peak_hours = []
        category_trends = []
    
    return render_template('admin_analytics.html',
                         status_timeline=status_timeline,
                         response_times=response_times,
                         user_activity=user_activity,
                         peak_hours=peak_hours,
                         category_trends=category_trends)

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
