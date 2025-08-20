# Deployment Guide - KTU Student Report System

## 🚀 Production Deployment Options

### Option 1: Traditional VPS/Server Deployment

#### Prerequisites
- Ubuntu 20.04+ or CentOS 8+ server
- Python 3.8+
- Nginx web server
- SSL certificate (Let's Encrypt recommended)
- Domain name pointing to server

#### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Create application user
sudo useradd -m -s /bin/bash ktuapp
sudo usermod -aG sudo ktuapp
```

#### Step 2: Application Deployment
```bash
# Switch to app user
sudo su - ktuapp

# Clone repository
git clone <repository-url> /home/ktuapp/student-report-system
cd /home/ktuapp/student-report-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
nano .env  # Configure your settings
```

#### Step 3: Gunicorn Configuration
```bash
# Create Gunicorn configuration
sudo nano /etc/supervisor/conf.d/ktu-app.conf
```

```ini
[program:ktu-app]
command=/home/ktuapp/student-report-system/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
directory=/home/ktuapp/student-report-system
user=ktuapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ktu-app.log
```

#### Step 4: Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/ktu-app
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /home/ktuapp/student-report-system/static;
        expires 30d;
    }
}
```

#### Step 5: SSL Setup with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Enable services
sudo ln -s /etc/nginx/sites-available/ktu-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl restart supervisor
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 ktuapp && chown -R ktuapp:ktuapp /app
USER ktuapp

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///university_issues.db
    volumes:
      - ./firebase_credentials.json:/app/firebase_credentials.json:ro
      - app_data:/app/data
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  app_data:
```

### Option 3: Cloud Platform Deployment

#### Heroku Deployment
```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create runtime.txt
echo "python-3.9.18" > runtime.txt

# Deploy
heroku create ktu-student-system
heroku config:set FLASK_ENV=production
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

#### DigitalOcean App Platform
```yaml
# .do/app.yaml
name: ktu-student-system
services:
- name: web
  source_dir: /
  github:
    repo: your-username/student-report-system
    branch: main
  run_command: gunicorn --worker-tmp-dir /dev/shm app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: FLASK_ENV
    value: production
```

#### AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize and deploy
eb init -p python-3.9 ktu-student-system
eb create production
eb deploy
```

## 🔧 Production Configuration

### Environment Variables
```bash
# .env file for production
FLASK_ENV=production
FLASK_SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql://user:pass@localhost/ktu_db
FIREBASE_PROJECT_ID=your-firebase-project
GMAIL_USERNAME=notifications@ktu.edu.gh
GMAIL_PASSWORD=your-app-password
REDIS_URL=redis://localhost:6379/0
```

### Database Migration
```python
# migrate_to_postgresql.py
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_sqlite_to_postgresql():
    # SQLite connection
    sqlite_conn = sqlite3.connect('university_issues.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    # PostgreSQL connection
    pg_conn = psycopg2.connect(
        host='localhost',
        database='ktu_db',
        user='postgres',
        password='password'
    )
    
    # Migration logic here
    # ...
```

### Security Hardening
```python
# security_config.py
from flask_talisman import Talisman

# CSP and security headers
csp = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
    'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
    'img-src': "'self' data: https:",
}

Talisman(app, content_security_policy=csp)
```

### Monitoring Setup
```python
# monitoring.py
import logging
from flask import request
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ktu-app.log'),
        logging.StreamHandler()
    ]
)

@app.before_request
def log_request_info():
    app.logger.info('Request: %s %s', request.method, request.url)

@app.after_request
def log_response_info(response):
    app.logger.info('Response: %s', response.status_code)
    return response
```

## 📊 Performance Optimization

### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_issues_user_id ON issues(user_id);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_created_at ON issues(created_at);
```

### Caching Strategy
```python
# cache_config.py
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@cache.memoize(timeout=300)
def get_dashboard_stats(user_id):
    # Expensive database queries
    pass
```

### Static File Optimization
```nginx
# Nginx static file configuration
location /static {
    alias /home/ktuapp/student-report-system/static;
    expires 1y;
    add_header Cache-Control "public, immutable";
    gzip on;
    gzip_types text/css application/javascript image/svg+xml;
}
```

## 🔍 Monitoring & Logging

### Application Monitoring
```python
# monitoring/health_check.py
from flask import Blueprint, jsonify
import psutil
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    })
```

### Log Rotation
```bash
# /etc/logrotate.d/ktu-app
/var/log/ktu-app.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ktuapp ktuapp
    postrotate
        systemctl reload supervisor
    endscript
}
```

## 🚨 Backup Strategy

### Database Backup
```bash
#!/bin/bash
# backup_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ktuapp/backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# SQLite backup
cp /home/ktuapp/student-report-system/university_issues.db \
   $BACKUP_DIR/university_issues_$DATE.db

# PostgreSQL backup (if using)
pg_dump ktu_db > $BACKUP_DIR/ktu_db_$DATE.sql

# Compress backups older than 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -exec gzip {} \;
find $BACKUP_DIR -name "*.sql" -mtime +7 -exec gzip {} \;

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### Automated Backup Cron
```bash
# Add to crontab
0 2 * * * /home/ktuapp/scripts/backup_db.sh
0 3 * * 0 /home/ktuapp/scripts/backup_files.sh
```

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    - name: Run tests
      run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /home/ktuapp/student-report-system
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart supervisor
```

## 🛡️ Security Checklist

### Pre-Deployment Security
- [ ] Update all dependencies to latest versions
- [ ] Remove debug mode and development settings
- [ ] Set strong, unique secret keys
- [ ] Configure proper Firebase security rules
- [ ] Set up SSL/TLS certificates
- [ ] Configure secure headers (CSP, HSTS, etc.)
- [ ] Implement rate limiting
- [ ] Set up proper file permissions
- [ ] Configure firewall rules
- [ ] Enable audit logging

### Post-Deployment Security
- [ ] Regular security updates
- [ ] Monitor application logs
- [ ] Set up intrusion detection
- [ ] Regular backup testing
- [ ] Security vulnerability scanning
- [ ] Performance monitoring
- [ ] SSL certificate renewal automation

---

**Note**: Always test deployments in a staging environment before production deployment.
