# KTU Student Report System

A comprehensive web-based issue reporting and management system for Koforidua Technical University (KTU) with Firebase integration and role-based access control.

## 🚀 Features

### Authentication & Authorization
- **Firebase Authentication** integration with email verification
- **Role-based access control** (Student, Sub-Admin, Super Admin)
- **Institutional email validation** (@ktu.edu.gh domain)
- **Secure session management** with Flask sessions
- **Password reset functionality** via Firebase

### User Roles & Dashboards

#### Students
- Submit and track issues
- View personal issue statistics
- Access issue history and status updates
- Clean, intuitive dashboard interface

#### Sub-Admins
- Manage student issues within assigned categories
- View student issue statistics and analytics
- Limited administrative permissions
- Issue resolution and status updates

#### Super Admins
- Full system administration access
- Create and manage sub-admin accounts
- System-wide analytics and reporting
- System settings and configuration
- User management and role assignment

### Core Functionality
- **Issue Management**: Submit, track, and resolve issues
- **Category System**: Organized issue categorization
- **Real-time Status Updates**: Track issue progress
- **Email Notifications**: Automated notifications via GMass SMTP
- **Analytics Dashboard**: Comprehensive reporting and statistics
- **System Logs**: Activity tracking and audit trails

## 🛠️ Technology Stack

### Backend
- **Flask** - Python web framework
- **Firebase Admin SDK** - Authentication and Firestore database
- **SQLite** - Local database (hybrid approach)
- **Jinja2** - Template engine
- **Werkzeug** - WSGI utilities

### Frontend
- **Bootstrap 5** - Responsive UI framework
- **FontAwesome** - Icons and visual elements
- **Chart.js** - Data visualization (analytics)
- **JavaScript** - Interactive functionality

### External Services
- **Firebase Authentication** - User management
- **Firestore** - NoSQL document database
- **GMass SMTP** - Email delivery service

## 📁 Project Structure

```
STUDENT REPORT SYSTEM V1/
├── app.py                    # Main Flask application
├── simple_firebase_app.py    # Simplified Firebase testing app
├── admin_routes.py          # Admin route handlers
├── database.py              # SQLite database operations
├── firebase_auth.py         # Firebase authentication wrapper
├── firebase_config.py       # Firebase initialization
├── email_utils.py           # Email notification system
├── init_database.py         # Database initialization
├── firebase_credentials.json # Firebase service account key
├── university_issues.db     # SQLite database file
├── pyproject.toml           # Python dependencies
├── uv.lock                  # Dependency lock file
├── static/                  # Static assets (CSS, images, JS)
│   ├── ktu-logo.png
│   ├── ktu-logo.svg
│   ├── login-design.jpeg
│   └── *.css
├── templates/               # Jinja2 HTML templates
│   ├── base.html           # Base template
│   ├── login.html          # Authentication pages
│   ├── register.html
│   ├── student_dashboard.html
│   ├── admin_dashboard.html
│   ├── subadmin_dashboard.html
│   ├── admin_analytics.html
│   ├── submit_issue.html
│   ├── my_issues.html
│   ├── manage_subadmins.html
│   ├── create_subadmin.html
│   ├── system_settings.html
│   └── *.html
└── .venv/                  # Python virtual environment
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Firebase project with Authentication and Firestore enabled
- GMass SMTP account (optional, for email notifications)

### 1. Clone Repository
```bash
git clone <repository-url>
cd "STUDENT REPORT SYSTEM V1"
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# OR using uv
uv sync
```

### 4. Firebase Configuration
1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication and Firestore
3. Generate service account key
4. Save as `firebase_credentials.json` in project root
5. Update `firebase_config.py` with your project details

### 5. Database Setup
```bash
python init_database.py
```

### 6. Environment Configuration
Create `.env` file (optional):
```env
FLASK_SECRET_KEY=your-secret-key-here
GMAIL_USERNAME=your-gmail@gmail.com
GMAIL_PASSWORD=your-app-password
```

## 🚀 Running the Application

### Development Server
```bash
# Main application
python app.py

# Simplified Firebase testing
python simple_firebase_app.py

# Quick start script
python quick_start.py
```

The application will be available at:
- **Main App**: http://127.0.0.1:5000
- **Firebase App**: http://127.0.0.1:56093

### Production Deployment
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Using uWSGI
uwsgi --http :8000 --wsgi-file app.py --callable app
```

## 👥 User Accounts & Testing

### Default Test Accounts
```
Super Admin:
- Email: admin@ktu.edu.gh
- Password: admin123

Sub-Admin:
- Email: subadmin@ktu.edu.gh  
- Password: subadmin123

Student:
- Email: student@ktu.edu.gh
- Password: student123
```

### Creating New Accounts
1. **Students**: Self-registration with @ktu.edu.gh email
2. **Sub-Admins**: Created by Super Admins via admin dashboard
3. **Super Admins**: Database-level creation or promotion

## 🔐 Security Features

### Authentication Security
- Firebase Authentication with email verification
- Institutional email domain validation
- Secure password requirements (minimum 6 characters)
- Session-based authentication with Flask sessions
- Role-based route protection

### Data Security
- Firebase security rules for Firestore
- SQL injection prevention with parameterized queries
- XSS protection via Jinja2 auto-escaping
- CSRF protection (recommended for production)

### Access Control
- Route-level authorization checks
- Template-level permission rendering
- Role-based feature access
- Admin-only system settings

## 📊 Database Schema

### SQLite Tables
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    full_name TEXT,
    password TEXT,
    role TEXT DEFAULT 'student',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Issues table  
CREATE TABLE issues (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    description TEXT,
    category TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Categories table
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Firebase Collections
```javascript
// Users collection
users: {
  uid: {
    email: string,
    full_name: string,
    role: 'student' | 'subadmin' | 'supa_admin',
    created_at: timestamp,
    last_login: timestamp
  }
}

// Issues collection
issues: {
  id: {
    user_id: string,
    title: string,
    description: string,
    category: string,
    status: 'pending' | 'in_progress' | 'resolved',
    created_at: timestamp,
    updated_at: timestamp
  }
}
```

## 🔧 Configuration

### Firebase Setup
```python
# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore, auth

cred = credentials.Certificate('firebase_credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
```

### Email Configuration
```python
# email_utils.py
SMTP_SERVER = 'smtp.gmass.co'
SMTP_PORT = 587
SMTP_USERNAME = 'gmass'
SMTP_PASSWORD = 'your-gmass-password'
```

### Flask Configuration
```python
# app.py
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

## 🐛 Troubleshooting

### Common Issues

#### Firebase Connection Errors
```bash
# Check credentials file
ls firebase_credentials.json

# Verify Firebase project settings
python -c "import firebase_admin; print('Firebase OK')"
```

#### Template Rendering Errors
- Ensure all route functions return proper context variables
- Check Jinja2 syntax in templates
- Verify template inheritance structure

#### Database Connection Issues
```bash
# Reinitialize database
python init_database.py

# Check database file
ls university_issues.db
```

#### Email Delivery Problems
- Verify GMass SMTP credentials
- Check email template formatting
- Ensure recipient email validation

### Debug Mode
```python
# Enable Flask debug mode
app.run(debug=True, host='127.0.0.1', port=5000)
```

## 📈 Performance Optimization

### Database Optimization
- Index frequently queried columns
- Use connection pooling for production
- Implement query result caching

### Frontend Optimization
- Minify CSS and JavaScript files
- Implement lazy loading for images
- Use CDN for static assets

### Firebase Optimization
- Implement Firestore security rules
- Use compound queries efficiently
- Cache frequently accessed data

## 🔄 API Endpoints

### Authentication Routes
```
POST /login          # User login
POST /register       # User registration  
GET  /logout         # User logout
POST /forgot-password # Password reset
```

### Student Routes
```
GET  /dashboard      # Student dashboard
GET  /submit-issue   # Issue submission form
POST /submit-issue   # Submit new issue
GET  /my-issues      # User's issues
GET  /settings       # User settings
```

### Admin Routes
```
GET  /admin/dashboard        # Admin dashboard
GET  /admin/analytics        # System analytics
GET  /admin/manage-subadmins # Sub-admin management
POST /admin/create-subadmin  # Create sub-admin
GET  /admin/system-settings  # System configuration
GET  /admin/notifications    # System notifications
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Make changes and test thoroughly
4. Commit changes (`git commit -m 'Add new feature'`)
5. Push to branch (`git push origin feature/new-feature`)
6. Create Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Write unit tests for new features
- Update documentation for changes

### Testing
```bash
# Run tests
python -m pytest tests/

# Test coverage
python -m pytest --cov=app tests/
```

## 📝 License

This project is licensed under the MIT License. See `LICENSE` file for details.

## 📞 Support

For technical support or questions:
- **Email**: support@ktu.edu.gh
- **Documentation**: See project wiki
- **Issues**: GitHub Issues page

## 🔮 Future Enhancements

### Planned Features
- [ ] Mobile application (React Native/Flutter)
- [ ] Real-time notifications (WebSocket)
- [ ] Advanced analytics and reporting
- [ ] File attachment support for issues
- [ ] Integration with university systems
- [ ] Multi-language support
- [ ] API for third-party integrations
- [ ] Advanced search and filtering
- [ ] Automated issue assignment
- [ ] SLA tracking and reporting

### Technical Improvements
- [ ] Implement Redis for session storage
- [ ] Add comprehensive test suite
- [ ] Set up CI/CD pipeline
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Performance monitoring
- [ ] Security audit and hardening
- [ ] Database migration system
- [ ] API rate limiting
- [ ] Comprehensive logging system

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Maintained By**: KTU IT Department
