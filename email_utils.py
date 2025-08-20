import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def generate_verification_code():
    """Generate a 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=6))

def generate_reset_token():
    """Generate a secure reset token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def send_verification_email(to_email, verification_code, full_name):
    """Send verification email to user using GMass SMTP."""
    return send_email(
        to_email=to_email,
        subject='KTU CS Department - Email Verification',
        template='verification',
        context={
            'full_name': full_name,
            'verification_code': verification_code
        }
    )

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
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #059669 100%); color: white; padding: 40px 30px; text-align: center; }}
            .content {{ padding: 40px 30px; }}
            .code-box {{ background: #f8f9fa; border: 2px dashed #1e3a8a; padding: 20px; text-align: center; margin: 30px 0; border-radius: 8px; }}
            .code {{ font-size: 32px; font-weight: bold; color: #1e3a8a; letter-spacing: 8px; }}
            .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to KTU Student Portal</h1>
                <p>Please verify your email address</p>
            </div>
            <div class="content">
                <h2>Hello {full_name},</h2>
                <p>Thank you for registering with the KTU CS Department Student Report System.</p>
                <p>To complete your registration, please use the verification code below:</p>
                
                <div class="code-box">
                    <div class="code">{verification_code}</div>
                </div>
                
                <p>Please enter this code on the verification page to activate your account.</p>
                <p>This code will expire in 15 minutes for security purposes.</p>
                    <p>If you didn't create an account with us, please ignore this email.</p>
                
                <p>Best regards,<br>
                <strong>KTU CS Department</strong><br>
                Koforidua Technical University</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2024 Koforidua Technical University - CS Department</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_body, is_html=True)
        

def send_password_reset_email(to_email, reset_token, full_name):
    """Send password reset email to users"""
    reset_link = f"http://localhost:5000/reset-password/{reset_token}"
    subject = "Reset Your KTU Student Portal Password"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #059669 100%); color: white; padding: 40px 30px; text-align: center; }}
            .content {{ padding: 40px 30px; }}
            .reset-button {{ text-align: center; margin: 30px 0; }}
            .btn {{ display: inline-block; background: #1e3a8a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; }}
            .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello {full_name},</h2>
                <p>We received a request to reset your password for your KTU CS Department account.</p>
                
                <div class="reset-button">
                    <a href="{reset_link}" class="btn">Reset Your Password</a>
                </div>
                
                <p>This link will expire in 1 hour for security purposes.</p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                
                <p>Best regards,<br>
                <strong>KTU CS Department</strong><br>
                Koforidua Technical University</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2024 Koforidua Technical University - CS Department</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_body, is_html=True)

def validate_institutional_email(email):
    """Validate that email belongs to the institution."""
    return email.endswith('@ktu.edu.gh')
