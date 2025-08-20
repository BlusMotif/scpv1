#!/usr/bin/env python3
import os
import sys
import traceback

def main():
    try:
        print("Starting Firebase Student Report System...")
        
        # Test Firebase imports
        import firebase_admin
        from firebase_admin import credentials, auth, firestore
        print("✓ Firebase imports successful")
        
        # Initialize Firebase
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
        print("✓ Firebase initialized")
        
        # Initialize Firestore
        db = firestore.client()
        print("✓ Firestore connected")
        
        # Import Flask app
        from flask import Flask, render_template, request, redirect, url_for, session, flash, g
        from werkzeug.security import check_password_hash, generate_password_hash
        from datetime import datetime, timedelta
        
        # Create Flask app
        app = Flask(__name__)
        app.secret_key = "firebase-student-report-system-secret-key"
        
        # Firebase Auth helper
        class FirebaseAuth:
            @staticmethod
            def create_user(email, password, display_name=None, email_verified=False):
                try:
                    user = auth.create_user(
                        email=email,
                        password=password,
                        display_name=display_name,
                        email_verified=email_verified
                    )
                    return user
                except Exception as e:
                    print(f"Error creating user: {e}")
                    return None
            
            @staticmethod
            def get_user_by_email(email):
                try:
                    user = auth.get_user_by_email(email)
                    return user
                except Exception as e:
                    print(f"User not found: {e}")
                    return None
        
        # Routes
        @app.route('/')
        def index():
            return redirect(url_for('login'))
        
        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                
                try:
                    firebase_user = FirebaseAuth.get_user_by_email(email)
                    if firebase_user:
                        session['user_id'] = firebase_user.uid
                        session['user_email'] = firebase_user.email
                        flash('Login successful!', 'success')
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Invalid email or password.', 'danger')
                except Exception as e:
                    flash('Login failed. Please try again.', 'danger')
            
            return render_template('login.html')
        
        @app.route('/register', methods=['GET', 'POST'])
        def register():
            if request.method == 'POST':
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                full_name = request.form.get('full_name', '').strip()
                
                if not email.endswith('@ktu.edu.gh'):
                    flash('Please use your institutional email (@ktu.edu.gh).', 'danger')
                    return render_template('register.html')
                
                try:
                    firebase_user = FirebaseAuth.create_user(
                        email=email,
                        password=password,
                        display_name=full_name,
                        email_verified=False
                    )
                    
                    if firebase_user:
                        # Store user data in Firestore
                        user_data = {
                            'uid': firebase_user.uid,
                            'email': email,
                            'full_name': full_name,
                            'role': 'student',
                            'created_at': datetime.now()
                        }
                        db.collection('users').document(firebase_user.uid).set(user_data)
                        
                        flash('Registration successful! Please log in.', 'success')
                        return redirect(url_for('login'))
                    else:
                        flash('Registration failed. Please try again.', 'danger')
                except Exception as e:
                    flash('Registration failed. Email may already exist.', 'danger')
            
            return render_template('register.html')
        
        @app.route('/dashboard')
        def dashboard():
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            return render_template('dashboard.html')
        
        @app.route('/logout')
        def logout():
            session.clear()
            flash('You have been logged out.', 'info')
            return redirect(url_for('login'))
        
        # Import admin routes
        try:
            from admin_routes import admin_bp
            app.register_blueprint(admin_bp)
            print("✓ Admin routes loaded")
        except Exception as e:
            print(f"Warning: Admin routes not loaded: {e}")
        
        print("✓ Flask app configured")
        print("Starting server on http://127.0.0.1:5000...")
        app.run(host='127.0.0.1', port=5000, debug=True)
        
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Installing firebase-admin...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'firebase-admin'])
        print("Please run the script again.")
        
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()
