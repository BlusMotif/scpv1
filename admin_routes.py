import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, make_response, jsonify
from werkzeug.security import generate_password_hash
import json
import csv
from io import StringIO
from datetime import datetime, timedelta
import os

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    conn = sqlite3.connect('university_issues.db')
    conn.row_factory = sqlite3.Row
    return conn

def log_admin_activity(admin_id, action, target_type=None, target_id=None, details=None):
    """Log admin activity for tracking purposes."""
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_id, action, target_type, target_id, details, request.environ.get('REMOTE_ADDR', 'Unknown')))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging admin activity: {e}")

def get_system_setting(key, default=None):
    """Get a system setting value."""
    try:
        conn = get_db_connection()
        setting = conn.execute('SELECT value FROM system_settings WHERE key = ?', (key,)).fetchone()
        conn.close()
        return setting['value'] if setting else default
    except:
        return default

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    from app import parse_datetime
    conn = get_db_connection()
    
    # Get issues with student information
    issues = conn.execute('''
        SELECT issues.*, users.full_name, users.index_number, users.email 
        FROM issues 
        JOIN users ON issues.student_id = users.id 
        ORDER BY issues.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Get comprehensive statistics
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved
        FROM issues
    ''').fetchone()
    
    # Get user statistics
    user_stats = conn.execute('''
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN role = 'student' THEN 1 ELSE 0 END) as students,
            SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admins,
            SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified_users
        FROM users
    ''').fetchone()
    
    # Get category statistics
    category_stats = conn.execute('''
        SELECT category, COUNT(*) as count
        FROM issues
        GROUP BY category
        ORDER BY count DESC
    ''').fetchall()
    
    # Get priority statistics
    priority_stats = conn.execute('''
        SELECT 
            COALESCE(priority, 'Medium') as priority, 
            COUNT(*) as count
        FROM issues
        GROUP BY priority
        ORDER BY 
            CASE priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                WHEN 'Low' THEN 4 
                ELSE 5 
            END
    ''').fetchall()
    
    # Get monthly statistics for charts (last 12 months)
    monthly_stats = conn.execute('''
        SELECT 
            strftime('%Y-%m', created_at) as month,
            COUNT(*) as count
        FROM issues
        WHERE created_at >= date('now', '-12 months')
        GROUP BY month
        ORDER BY month
    ''').fetchall()
    
    # Get daily statistics for the last 30 days
    daily_stats = conn.execute('''
        SELECT 
            date(created_at) as day,
            COUNT(*) as count
        FROM issues
        WHERE created_at >= date('now', '-30 days')
        GROUP BY day
        ORDER BY day
    ''').fetchall()
    
    # Get recent admin activities
    recent_activities = conn.execute('''
        SELECT al.*, u.full_name as admin_name
        FROM admin_logs al
        JOIN users u ON al.admin_id = u.id
        ORDER BY al.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Get system notifications
    notifications = conn.execute('''
        SELECT * FROM system_notifications
        WHERE is_read = 0
        ORDER BY created_at DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         issues=issues, 
                         stats=stats,
                         user_stats=user_stats,
                         category_stats=category_stats,
                         priority_stats=priority_stats,
                         monthly_stats=monthly_stats,
                         daily_stats=daily_stats,
                         recent_activities=recent_activities,
                         notifications=notifications,
                         parse_datetime=parse_datetime)

@admin_bp.route('/admin/create-subadmin', methods=['GET', 'POST'])
def create_subadmin():
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate required fields
        if not all([username, email, full_name, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('create_subadmin.html')
        
        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('create_subadmin.html')
        
        # Validate password length
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('create_subadmin.html')
        
        conn = get_db_connection()
        
        # Check if username exists
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists.', 'danger')
            conn.close()
            return render_template('create_subadmin.html')
        
        # Check if email exists
        existing_email = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing_email:
            flash('Email already registered.', 'danger')
            conn.close()
            return render_template('create_subadmin.html')
        
        password_hash = generate_password_hash(password)
        
        conn.execute(
            'INSERT INTO users (username, email, full_name, index_number, level, gender, password, role, is_verified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (username, email, full_name, 'SUB' + username.upper(), 'Staff', 'M', password_hash, 'subadmin', True)
        )
        conn.commit()
        conn.close()
        
        flash('Sub-admin account created successfully.', 'success')
        return redirect(url_for('admin.manage_subadmins'))
    
    return render_template('create_subadmin.html')

@admin_bp.route('/admin/manage-subadmins')
def manage_subadmins():
    """Manage sub-administrators."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    subadmins = conn.execute('''
        SELECT 
            id, username, email, full_name, is_active, 
            last_login, login_count, created_at,
            (SELECT COUNT(*) FROM issues WHERE assigned_to = users.id) as assigned_issues
        FROM users 
        WHERE role = 'subadmin'
        ORDER BY created_at DESC
    ''').fetchall()
    
    # Get recent activities for each subadmin
    activities = conn.execute('''
        SELECT al.*, u.username
        FROM admin_logs al
        JOIN users u ON al.admin_id = u.id
        WHERE u.role = 'subadmin'
        ORDER BY al.created_at DESC
        LIMIT 20
    ''').fetchall()
    
    conn.close()
    
    return render_template('manage_subadmins.html', subadmins=subadmins, activities=activities)

@admin_bp.route('/admin/toggle-subadmin/<int:subadmin_id>', methods=['POST'])
def toggle_subadmin(subadmin_id):
    """Toggle sub-admin active status."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get current status
    subadmin = conn.execute('SELECT is_active, username FROM users WHERE id = ? AND role = "subadmin"', (subadmin_id,)).fetchone()
    
    if subadmin:
        new_status = not subadmin['is_active']
        conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, subadmin_id))
        conn.commit()
        
        action = 'activate' if new_status else 'deactivate'
        log_admin_activity(g.user['id'], f'{action}_subadmin', 'user', subadmin_id, f'{action.title()}d subadmin {subadmin["username"]}')
        
        flash(f'Sub-admin {subadmin["username"]} {"activated" if new_status else "deactivated"} successfully.', 'success')
    else:
        flash('Sub-admin not found.', 'danger')
    
    conn.close()
    return redirect(url_for('admin.manage_subadmins'))

@admin_bp.route('/admin/delete-subadmin/<int:subadmin_id>', methods=['POST'])
def delete_subadmin(subadmin_id):
    """Delete a sub-admin account."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get subadmin info before deletion
    subadmin = conn.execute('SELECT username FROM users WHERE id = ? AND role = "subadmin"', (subadmin_id,)).fetchone()
    
    if subadmin:
        # Delete the subadmin
        conn.execute('DELETE FROM users WHERE id = ? AND role = "subadmin"', (subadmin_id,))
        conn.commit()
        
        log_admin_activity(g.user['id'], 'delete_subadmin', 'user', subadmin_id, f'Deleted subadmin {subadmin["username"]}')
        
        flash(f'Sub-admin {subadmin["username"]} deleted successfully.', 'success')
    else:
        flash('Sub-admin not found.', 'danger')
    
    conn.close()
    return redirect(url_for('admin.manage_subadmins'))

@admin_bp.route('/subadmin/dashboard')
def subadmin_dashboard():
    """Sub-admin dashboard with limited access to student issues only."""
    if g.user is None or g.user['role'] not in ['subadmin']:
        flash('Access denied. Sub-admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get student issues statistics only
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_issues,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved
        FROM issues
        JOIN users ON issues.student_id = users.id
        WHERE users.role = 'student'
    ''').fetchone()
    
    # Get recent student issues
    recent_issues = conn.execute('''
        SELECT i.*, u.full_name, u.email, u.index_number
        FROM issues i
        JOIN users u ON i.student_id = u.id
        WHERE u.role = 'student'
        ORDER BY i.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Get category statistics for students only
    category_stats = conn.execute('''
        SELECT i.category, COUNT(*) as count
        FROM issues i
        JOIN users u ON i.student_id = u.id
        WHERE u.role = 'student'
        GROUP BY i.category
        ORDER BY count DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('subadmin_dashboard.html',
                         stats=stats,
                         recent_issues=recent_issues,
                         category_stats=category_stats)

@admin_bp.route('/admin/manage-categories')
def manage_categories():
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()
    
    return render_template('manage_categories.html', categories=categories)

@admin_bp.route('/admin/add-category', methods=['POST'])
def add_category():
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    name = request.form['name']
    description = request.form['description']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
    conn.commit()
    conn.close()
    
    flash('Category added successfully.', 'success')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/admin/delete-category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()
    
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/admin/manage-prefixes')
def manage_prefixes():
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    prefixes = conn.execute('SELECT * FROM index_prefixes ORDER BY prefix').fetchall()
    conn.close()
    
    return render_template('manage_prefixes.html', prefixes=prefixes)

@admin_bp.route('/admin/add-prefix', methods=['POST'])
def add_prefix():
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    prefix = request.form['prefix'].upper()
    description = request.form['description']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO index_prefixes (prefix, description) VALUES (?, ?)', (prefix, description))
    conn.commit()
    conn.close()
    
    flash('Index prefix added successfully.', 'success')
    return redirect(url_for('admin.manage_prefixes'))

@admin_bp.route('/admin/delete-prefix/<int:prefix_id>', methods=['POST'])
def delete_prefix(prefix_id):
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM index_prefixes WHERE id = ?', (prefix_id,))
    conn.commit()
    conn.close()
    
    flash('Index prefix deleted successfully.', 'success')
    return redirect(url_for('admin.manage_prefixes'))


@admin_bp.route('/admin/update-setting', methods=['POST'])
def update_setting():
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    key = request.form['key']
    value = request.form['value']
    
    conn = get_db_connection()
    conn.execute('UPDATE system_settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', (value, key))
    conn.commit()
    conn.close()
    
    flash('Setting updated successfully.', 'success')
    return redirect(url_for('admin.system_settings'))

@admin_bp.route('/admin/resolve-issue/<int:issue_id>', methods=['POST'])
def resolve_issue(issue_id):
    if g.user is None or g.user['role'] not in ['admin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    
    status = request.form.get('status')
    response = request.form.get('response')
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE issues SET status = ?, response = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (status, response, issue_id)
    )
    conn.commit()
    conn.close()
    
    flash('Issue updated successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/delete-issue/<int:issue_id>', methods=['POST'])
def admin_delete_issue(issue_id):
    if g.user is None or g.user['role'] not in ['admin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM issues WHERE id = ?', (issue_id,))
    conn.commit()
    conn.close()
    
    flash('Issue deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/export-data')
def export_data():
    if g.user is None or g.user['role'] not in ['admin', 'supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Log admin activity
    log_admin_activity(g.user['id'], 'export_data', 'issues', None, 'Exported issues data')
    
    issues = conn.execute('''
        SELECT 
            issues.id,
            users.full_name,
            users.index_number,
            users.email,
            issues.subject,
            issues.category,
            issues.message,
            issues.status,
            issues.priority,
            issues.response,
            issues.created_at,
            issues.updated_at
        FROM issues
        JOIN users ON issues.student_id = users.id
        ORDER BY issues.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Student Name', 'Index Number', 'Email', 'Subject', 'Category', 'Message', 'Status', 'Priority', 'Response', 'Created At', 'Updated At'])
    
    for issue in issues:
        writer.writerow([
            issue['id'],
            issue['full_name'],
            issue['index_number'],
            issue['email'],
            issue['subject'],
            issue['category'],
            issue['message'],
            issue['status'],
            issue['priority'] or 'Medium',
            issue['response'],
            issue['created_at'],
            issue['updated_at']
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=ktu_issues_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

@admin_bp.route('/admin/settings')
def admin_settings():
    from flask import g
    if not g.user or g.user['role'] not in ['supa_admin']:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (g.user['username'],)).fetchone()
    
    # Get system settings grouped by category
    settings = conn.execute('''
        SELECT * FROM system_settings 
        ORDER BY category, key
    ''').fetchall()
    
    # Group settings by category
    settings_by_category = {}
    for setting in settings:
        category = setting['category']
        if category not in settings_by_category:
            settings_by_category[category] = []
        settings_by_category[category].append(setting)
    
    conn.close()
    
    return render_template('admin_settings.html', 
                         user=user, 
                         settings_by_category=settings_by_category)

@admin_bp.route('/admin/update-password', methods=['POST'])
def update_password():
    from flask import g
    if not g.user or g.user['role'] not in ['supa_admin']:
        return redirect(url_for('login'))
    
    password = request.form['password']
    password_confirm = request.form['password_confirm']
    
    if password != password_confirm:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('admin.admin_settings'))
    
    password_hash = generate_password_hash(password)
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE username = ?', (password_hash, g.user['username']))
    conn.commit()
    conn.close()
    
    # Log admin activity
    log_admin_activity(g.user['id'], 'update_password', 'user', g.user['id'], 'Updated own password')
    
    flash('Password updated successfully.', 'success')
    return redirect(url_for('admin.admin_settings'))

# New comprehensive admin routes

@admin_bp.route('/admin/analytics')
def analytics():
    """Advanced analytics dashboard with charts and graphs."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get comprehensive analytics data
    # Issues by status over time
    status_timeline = conn.execute('''
        SELECT 
            date(created_at) as date,
            status,
            COUNT(*) as count
        FROM issues
        WHERE created_at >= date('now', '-90 days')
        GROUP BY date, status
        ORDER BY date
    ''').fetchall()
    
    # Response time analytics
    response_times = conn.execute('''
        SELECT 
            AVG(julianday(updated_at) - julianday(created_at)) * 24 as avg_hours,
            category
        FROM issues
        WHERE status = 'resolved' AND response IS NOT NULL
        GROUP BY category
    ''').fetchall()
    
    # User activity analytics
    user_activity = conn.execute('''
        SELECT 
            strftime('%Y-%m', created_at) as month,
            COUNT(DISTINCT student_id) as active_users,
            COUNT(*) as total_issues
        FROM issues
        WHERE created_at >= date('now', '-12 months')
        GROUP BY month
        ORDER BY month
    ''').fetchall()
    
    # Peak hours analysis
    peak_hours = conn.execute('''
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as count
        FROM issues
        GROUP BY hour
        ORDER BY hour
    ''').fetchall()
    
    # Category trends
    category_trends = conn.execute('''
        SELECT 
            category,
            strftime('%Y-%m', created_at) as month,
            COUNT(*) as count
        FROM issues
        WHERE created_at >= date('now', '-6 months')
        GROUP BY category, month
        ORDER BY month, category
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_analytics.html',
                         status_timeline=status_timeline,
                         response_times=response_times,
                         user_activity=user_activity,
                         peak_hours=peak_hours,
                         category_trends=category_trends)

@admin_bp.route('/admin/system-settings', methods=['GET', 'POST'])
def system_settings():
    """Comprehensive system settings management."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Update multiple settings
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                conn.execute('''
                    UPDATE system_settings 
                    SET value = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE key = ?
                ''', (value, setting_key))
        
        conn.commit()
        log_admin_activity(g.user['id'], 'update_system_settings', 'settings', None, 'Updated system settings')
        flash('System settings updated successfully.', 'success')
        return redirect(url_for('admin.system_settings'))
    
    # Get all settings grouped by category
    settings = conn.execute('''
        SELECT * FROM system_settings 
        ORDER BY category, key
    ''').fetchall()
    
    settings_by_category = {}
    for setting in settings:
        category = setting['category']
        if category not in settings_by_category:
            settings_by_category[category] = []
        settings_by_category[category].append(setting)
    
    conn.close()
    
    return render_template('system_settings.html', settings_by_category=settings_by_category)

@admin_bp.route('/admin/system-logs')
def system_logs():
    """View system activity logs."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    # Get total count
    total_logs = conn.execute('SELECT COUNT(*) as count FROM admin_logs').fetchone()['count']
    
    # Get logs with admin info
    logs = conn.execute('''
        SELECT al.*, u.full_name as admin_name, u.username
        FROM admin_logs al
        JOIN users u ON al.admin_id = u.id
        ORDER BY al.created_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    
    conn.close()
    
    # Calculate pagination info
    total_pages = (total_logs + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('system_logs.html',
                         logs=logs,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         total_logs=total_logs)

@admin_bp.route('/admin/notifications')
def notifications():
    """Manage system notifications."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    notifications = conn.execute('''
        SELECT * FROM system_notifications
        ORDER BY created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_notifications.html', notifications=notifications)

@admin_bp.route('/admin/create-notification', methods=['POST'])
def create_notification():
    """Create a new system notification."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        flash('Access denied. Supa Admin only.', 'danger')
        return redirect(url_for('login'))
    
    title = request.form['title']
    message = request.form['message']
    notification_type = request.form.get('type', 'info')
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO system_notifications (title, message, type)
        VALUES (?, ?, ?)
    ''', (title, message, notification_type))
    conn.commit()
    conn.close()
    
    log_admin_activity(g.user['id'], 'create_notification', 'notification', None, f'Created notification: {title}')
    flash('Notification created successfully.', 'success')
    return redirect(url_for('admin.notifications'))

@admin_bp.route('/admin/api/chart-data/<chart_type>')
def chart_data(chart_type):
    """API endpoint for chart data."""
    if g.user is None or g.user['role'] not in ['supa_admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db_connection()
    
    if chart_type == 'issues_by_month':
        data = conn.execute('''
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as count
            FROM issues
            WHERE created_at >= date('now', '-12 months')
            GROUP BY month
            ORDER BY month
        ''').fetchall()
        
    elif chart_type == 'issues_by_category':
        data = conn.execute('''
            SELECT category, COUNT(*) as count
            FROM issues
            GROUP BY category
            ORDER BY count DESC
        ''').fetchall()
        
    elif chart_type == 'issues_by_status':
        data = conn.execute('''
            SELECT status, COUNT(*) as count
            FROM issues
            GROUP BY status
        ''').fetchall()
        
    elif chart_type == 'daily_activity':
        data = conn.execute('''
            SELECT 
                date(created_at) as date,
                COUNT(*) as count
            FROM issues
            WHERE created_at >= date('now', '-30 days')
            GROUP BY date
            ORDER BY date
        ''').fetchall()
        
    else:
        conn.close()
        return jsonify({'error': 'Invalid chart type'}), 400
    
    conn.close()
    
    # Convert to JSON-serializable format
    result = [dict(row) for row in data]
    return jsonify(result)
