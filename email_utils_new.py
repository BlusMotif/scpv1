import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from datetime import datetime, timedelta

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def generate_reset_token():
    """Generate a secure reset token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def validate_institutional_email(email):
    """Validate that email belongs to the institution"""
    return email.endswith('@ktu.edu.gh')

def send_email(to_email, subject, body, is_html=False):
    """Send email using GMass SMTP configuration"""
    try:
        # GMass SMTP configuration
        smtp_server = "smtp.gmass.co"
        smtp_port = 587  # Using TLS port
        smtp_username = "gmass"
        smtp_password = "a7f361ce-fc7b-41c3-8b2f-d163dd30d95b"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"KTU Student Portal <{smtp_username}@gmass.co>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(smtp_username, smtp_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(f"{smtp_username}@gmass.co", to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_verification_email(to_email, verification_code, full_name):
    """Send verification email to new users"""
    subject = "Verify Your KTU Student Portal Account"
    
    body = f"""
Dear {full_name},

Welcome to the Koforidua Technical University Student Portal!

To complete your registration and activate your account, please use the following verification code:

🔐 Verification Code: {verification_code}

This code will expire in 24 hours for security purposes.

Steps to verify your account:
1. Return to the login page
2. Click on "Verify Account"
3. Enter your email and the verification code above
4. Your account will be activated immediately

If you didn't create this account, please ignore this email or contact our IT support team.

For technical support, contact: support@ktu.edu.gh

Best regards,
KTU IT Support Team
Koforidua Technical University

---
This is an automated message. Please do not reply to this email.
    """
    
    return send_email(to_email, subject, body)

def send_password_reset_email(to_email, reset_code, full_name):
    """Send password reset email"""
    subject = "Reset Your KTU Student Portal Password"
    
    body = f"""
Dear {full_name},

You have requested to reset your password for the KTU Student Portal.

🔐 Password Reset Code: {reset_code}

This code will expire in 1 hour for security purposes.

Steps to reset your password:
1. Return to the password reset page
2. Enter your email and the reset code above
3. Create a new secure password
4. Your password will be updated immediately

If you didn't request this password reset, please ignore this email or contact our IT support team immediately.

For technical support, contact: support@ktu.edu.gh

Best regards,
KTU IT Support Team
Koforidua Technical University

---
This is an automated message. Please do not reply to this email.
    """
    
    return send_email(to_email, subject, body)
