from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
app.secret_key = "firebase-student-report-system-key"

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Simple validation for testing
        if email and password:
            session['user_email'] = email
            
            # Determine user role and redirect to appropriate dashboard
            if email == 'admin@ktu.edu.gh':
                session['user_role'] = 'supa_admin'
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            elif email.startswith('subadmin'):
                session['user_role'] = 'subadmin'
                flash('Sub-admin login successful!', 'success')
                return redirect(url_for('subadmin_dashboard'))
            else:
                session['user_role'] = 'student'
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
        else:
            flash('Please enter email and password.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        
        if not email.endswith('@ktu.edu.gh'):
            flash('Please use your institutional email (@ktu.edu.gh).', 'danger')
        elif email and password and full_name:
            # Store user role in session for demo purposes
            if email == 'admin@ktu.edu.gh':
                session['user_role'] = 'supa_admin'
            elif email.startswith('subadmin'):
                session['user_role'] = 'subadmin'
            else:
                session['user_role'] = 'student'
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Please fill all fields.', 'danger')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('user_role', 'student')
    
    if user_role == 'supa_admin':
        return redirect(url_for('admin_dashboard'))
    elif user_role == 'subadmin':
        return redirect(url_for('subadmin_dashboard'))
    else:
        # Student dashboard
        stats = {
            'total_issues': 5,
            'pending_issues': 2,
            'resolved_issues': 3,
            'in_progress_issues': 0
        }
        
        recent_issues = [
            {'id': 1, 'title': 'Broken projector in Room 101', 'status': 'pending', 'date': '2024-01-15', 'message': 'The projector is not working'},
            {'id': 2, 'title': 'WiFi connectivity issues', 'status': 'resolved', 'date': '2024-01-14', 'message': 'Cannot connect to campus WiFi'}
        ]
        
        return render_template('student_dashboard.html', stats=stats, recent_issues=recent_issues)

@app.route('/student/dashboard')
def student_dashboard():
    return dashboard()

@app.route('/submit-issue', methods=['GET', 'POST'])
def submit_issue():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        
        if title and description and category:
            flash('Issue submitted successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Please fill all fields.', 'danger')
    
    return render_template('submit_issue.html')

@app.route('/my-issues')
def my_issues():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    return render_template('my_issues.html')

@app.route('/settings')
def settings():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    return render_template('settings.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    # Mock admin dashboard data
    stats = {
        'total_users': 156,
        'total_issues': 89,
        'pending_issues': 23,
        'resolved_issues': 66,
        'categories': 8,
        'subadmins': 3
    }
    
    user_stats = {
        'total_users': 156,
        'active_users': 142,
        'new_users_today': 8,
        'verified_users': 134
    }
    
    issue_stats = {
        'total_issues': 89,
        'pending_issues': 23,
        'resolved_issues': 66,
        'in_progress_issues': 12
    }
    
    category_stats = [
        {'name': 'IT Support', 'count': 35, 'percentage': 39},
        {'name': 'Facilities', 'count': 28, 'percentage': 31},
        {'name': 'Academic', 'count': 15, 'percentage': 17},
        {'name': 'Student Services', 'count': 11, 'percentage': 13}
    ]
    
    recent_issues = [
        {
            'id': 1,
            'title': 'Network connectivity issue',
            'student': 'John Doe',
            'category': 'IT Support',
            'status': 'Pending',
            'date': '2025-08-19',
            'subject': 'Network connectivity issue',
            'full_name': 'John Doe',
            'message': 'Unable to connect to campus WiFi network consistently.'
        },
        {
            'id': 2,
            'title': 'Library access problem',
            'student': 'Jane Smith',
            'category': 'Facilities',
            'status': 'In Progress',
            'date': '2025-08-18',
            'subject': 'Library access problem',
            'full_name': 'Jane Smith',
            'message': 'Student ID card not working at library entrance scanner.'
        }
    ]
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         user_stats=user_stats,
                         issue_stats=issue_stats,
                         category_stats=category_stats,
                         recent_issues=recent_issues)

@app.route('/subadmin/dashboard')
def subadmin_dashboard():
    if 'user_email' not in session or session.get('user_role') != 'subadmin':
        flash('Access denied. Sub-admin only.', 'danger')
        return redirect(url_for('login'))
    
    # Mock subadmin dashboard data
    stats = {
        'assigned_issues': 15,
        'resolved_today': 3,
        'pending_issues': 12,
        'total_resolved': 45
    }
    
    recent_issues = [
        {
            'id': 1,
            'title': 'Student ID card issue',
            'student': 'Alice Johnson',
            'category': 'Student Services',
            'status': 'Pending',
            'date': '2025-08-19'
        }
    ]
    
    category_stats = [
        {'name': 'IT Support', 'count': 8},
        {'name': 'Facilities', 'count': 4},
        {'name': 'Student Services', 'count': 3}
    ]
    
    return render_template('subadmin_dashboard.html', 
                         stats=stats, 
                         recent_issues=recent_issues,
                         category_stats=category_stats)

@app.route('/admin/analytics')
def admin_analytics():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    # Mock analytics data for template
    status_timeline = [
        {'date': '2025-08-15', 'pending': 10, 'resolved': 5},
        {'date': '2025-08-16', 'pending': 12, 'resolved': 8},
        {'date': '2025-08-17', 'pending': 15, 'resolved': 12},
        {'date': '2025-08-18', 'pending': 18, 'resolved': 15},
        {'date': '2025-08-19', 'pending': 23, 'resolved': 20}
    ]
    
    response_times = [2.5, 3.1, 1.8, 4.2, 2.9, 3.5, 2.1]
    user_activity = [45, 52, 38, 61, 48, 55, 42]
    peak_hours = [8, 12, 15, 18, 22, 35, 28, 15, 12, 8, 5, 3]
    category_trends = [
        {'category': 'IT Support', 'count': 35},
        {'category': 'Facilities', 'count': 28},
        {'category': 'Academic', 'count': 15},
        {'category': 'Student Services', 'count': 11}
    ]
    
    return render_template('admin_analytics.html',
                         status_timeline=status_timeline,
                         response_times=response_times,
                         user_activity=user_activity,
                         peak_hours=peak_hours,
                         category_trends=category_trends)

@app.route('/admin/manage-categories')
def admin_manage_categories():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    return render_template('manage_categories.html')

@app.route('/admin/create-subadmin')
def admin_create_subadmin():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    return render_template('create_subadmin.html')

@app.route('/admin/manage-subadmins')
def admin_manage_subadmins():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    return render_template('manage_subadmins.html')

@app.route('/admin/system-settings')
def admin_system_settings():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    # Mock settings data
    settings_by_category = {
        'general': [
            {'key': 'site_name', 'value': 'KTU Student Report System', 'type': 'text'},
            {'key': 'maintenance_mode', 'value': False, 'type': 'boolean'}
        ],
        'appearance': [
            {'key': 'theme', 'value': 'light', 'type': 'select', 'options': ['light', 'dark']},
            {'key': 'logo_url', 'value': '/static/ktu-logo.png', 'type': 'text'}
        ],
        'notifications': [
            {'key': 'email_notifications', 'value': True, 'type': 'boolean'},
            {'key': 'sms_notifications', 'value': False, 'type': 'boolean'}
        ]
    }
    
    return render_template('system_settings.html', settings_by_category=settings_by_category)

@app.route('/admin/system-logs')
def admin_system_logs():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    return render_template('system_logs.html')

@app.route('/admin/notifications')
def admin_notifications():
    if 'user_email' not in session or session.get('user_role') != 'supa_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('login'))
    
    return render_template('admin_notifications.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if email.endswith('@ktu.edu.gh'):
            flash('Password reset instructions sent to your email.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Please use your institutional email (@ktu.edu.gh).', 'danger')
    
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("Starting Simple Firebase Student Report System...")
    print("Server will be available at: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
