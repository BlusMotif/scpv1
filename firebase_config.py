
import firebase_admin
from firebase_admin import credentials, db
import json
import os
from datetime import datetime
import uuid

def initialize_firebase():
    """Initialize Firebase with credentials and database URL"""
    try:
        # Check if Firebase app is already initialized
        try:
            firebase_admin.get_app()
            print("Firebase already initialized")
            return True
        except ValueError:
            pass
        
        # Load Firebase credentials
        if os.path.exists('firebase_credentials.json'):
            cred = credentials.Certificate('firebase_credentials.json')
        else:
            print("Firebase credentials file not found, using default credentials")
            cred = credentials.ApplicationDefault()
        
        # Initialize Firebase with your Realtime Database URL
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://scpv2-fa488-default-rtdb.firebaseio.com/'
        })
        
        print("Firebase initialized successfully with Realtime Database")
        return True
        
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False

class RealtimeDB:
    """Firebase Realtime Database integration"""
    
    def __init__(self):
        self.db_ref = db.reference()
    
    def add_user(self, user_data):
        """Add user to Firebase Realtime Database"""
        try:
            users_ref = self.db_ref.child('users')
            new_user_ref = users_ref.push(user_data)
            return new_user_ref.key
        except Exception as e:
            print(f"Error adding user to Firebase: {e}")
            return None
    
    def get_user(self, user_id):
        """Get user from Firebase Realtime Database"""
        try:
            user_ref = self.db_ref.child('users').child(user_id)
            user_data = user_ref.get()
            if user_data:
                return {'id': user_id, **user_data}
            return None
        except Exception as e:
            print(f"Error getting user from Firebase: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email from Firebase Realtime Database"""
        try:
            users_ref = self.db_ref.child('users')
            users = users_ref.order_by_child('email').equal_to(email).get()
            
            if users:
                for user_id, user_data in users.items():
                    return {'id': user_id, **user_data}
            return None
        except Exception as e:
            print(f"Error getting user by email from Firebase: {e}")
            return None
    
    def update_user(self, user_id, data):
        """Update user in Firebase Realtime Database"""
        try:
            user_ref = self.db_ref.child('users').child(user_id)
            user_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating user in Firebase: {e}")
            return False
    
    def get_all_users(self):
        """Get all users from Firebase Realtime Database"""
        try:
            users_ref = self.db_ref.child('users')
            users_data = users_ref.get()
            
            if users_data:
                users = []
                for user_id, user_data in users_data.items():
                    users.append({'id': user_id, **user_data})
                return users
            return []
        except Exception as e:
            print(f"Error getting all users from Firebase: {e}")
            return []
    
    def add_issue(self, issue_data):
        """Add issue to Firebase Realtime Database"""
        try:
            issues_ref = self.db_ref.child('issues')
            new_issue_ref = issues_ref.push(issue_data)
            return new_issue_ref.key
        except Exception as e:
            print(f"Error adding issue to Firebase: {e}")
            return None
    
    def get_issues(self, user_id=None, limit=None):
        """Get issues from Firebase Realtime Database"""
        try:
            issues_ref = self.db_ref.child('issues')
            
            if user_id:
                issues_data = issues_ref.order_by_child('user_id').equal_to(user_id).get()
            else:
                issues_data = issues_ref.get()
            
            if issues_data:
                issues = []
                for issue_id, issue_data in issues_data.items():
                    issues.append({'id': issue_id, **issue_data})
                
                # Sort by created_at (newest first)
                issues.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
                if limit:
                    issues = issues[:limit]
                
                return issues
            return []
        except Exception as e:
            print(f"Error getting issues from Firebase: {e}")
            return []
    
    def update_issue(self, issue_id, data):
        """Update issue in Firebase Realtime Database"""
        try:
            issue_ref = self.db_ref.child('issues').child(issue_id)
            issue_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating issue in Firebase: {e}")
            return False
    
    def delete_issue(self, issue_id):
        """Delete issue from Firebase Realtime Database"""
        try:
            issue_ref = self.db_ref.child('issues').child(issue_id)
            issue_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting issue from Firebase: {e}")
            return False
    
    def get_issues_with_user_info(self, limit=None):
        """Get issues with user information from Firebase Realtime Database"""
        try:
            issues = self.get_issues(limit=limit)
            
            for issue in issues:
                user_id = issue.get('user_id')
                if user_id:
                    user = self.get_user(user_id)
                    if user:
                        issue['full_name'] = user.get('full_name', 'Unknown')
                        issue['email'] = user.get('email', 'Unknown')
                    else:
                        issue['full_name'] = 'Unknown User'
                        issue['email'] = 'Unknown'
                else:
                    issue['full_name'] = 'Unknown User'
                    issue['email'] = 'Unknown'
            
            return issues
        except Exception as e:
            print(f"Error getting issues with user info from Firebase: {e}")
            return []
    
    def get_statistics(self):
        """Get system statistics from Firebase Realtime Database"""
        try:
            users_ref = self.db_ref.child('users')
            issues_ref = self.db_ref.child('issues')
            
            users_data = users_ref.get()
            issues_data = issues_ref.get()
            
            total_users = len(users_data) if users_data else 0
            total_issues = len(issues_data) if issues_data else 0
            
            pending_issues = 0
            if issues_data:
                for issue_data in issues_data.values():
                    if issue_data.get('status') == 'pending':
                        pending_issues += 1
            
            return {
                'total_users': total_users,
                'total_issues': total_issues,
                'pending_issues': pending_issues
            }
        except Exception as e:
            print(f"Error getting statistics from Firebase: {e}")
            return {'total_users': 0, 'total_issues': 0, 'pending_issues': 0}

def get_realtime_db():
    """Get Firebase Realtime Database reference"""
    return RealtimeDB()
