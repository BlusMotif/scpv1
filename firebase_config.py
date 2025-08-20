
import firebase_admin
from firebase_admin import credentials, auth, firestore, db
import os
import json

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        return True
    except ValueError:
        # Firebase not initialized, proceed with initialization
        pass
    
    try:
        # Use the credentials file path
        cred_path = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')
        
        # Check if credentials file exists
        if not os.path.exists(cred_path):
            print(f"Firebase credentials file not found at: {cred_path}")
            print("Using default Firebase Realtime Database URL...")
            # Initialize with default settings for development
            firebase_admin.initialize_app(options={
                'databaseURL': 'https://scpv2-fa488-default-rtdb.firebaseio.com/'
            })
            print("Firebase initialized with default settings")
            return True
        
        # Load credentials and get database URL
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': cred_data.get('databaseURL', 'https://scpv2-fa488-default-rtdb.firebaseio.com/')
        })
        print("Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        print("Attempting fallback initialization...")
        try:
            # Fallback initialization for development
            firebase_admin.initialize_app(options={
                'databaseURL': 'https://scpv2-fa488-default-rtdb.firebaseio.com/'
            })
            print("Firebase initialized with fallback settings")
            return True
        except Exception as fallback_error:
            print(f"Fallback initialization also failed: {fallback_error}")
            return False

def get_realtime_db():
    """Get Firebase Realtime Database reference"""
    try:
        return db.reference()
    except Exception as e:
        print(f"Error getting Realtime Database: {e}")
        return None

def get_firestore_client():
    """Get Firestore database client"""
    try:
        return firestore.client()
    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        return None

# Realtime Database operations
class RealtimeDB:
    def __init__(self):
        self.db = get_realtime_db()
    
    def add_user(self, user_data):
        """Add user to Realtime Database"""
        try:
            users_ref = self.db.child('users')
            new_user_ref = users_ref.push(user_data)
            return new_user_ref.key
        except Exception as e:
            print(f"Error adding user to Realtime Database: {e}")
            return None
    
    def get_user(self, user_id):
        """Get user from Realtime Database"""
        try:
            user_ref = self.db.child('users').child(user_id)
            user_data = user_ref.get()
            if user_data:
                return {'id': user_id, **user_data}
            return None
        except Exception as e:
            print(f"Error getting user from Realtime Database: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email from Realtime Database"""
        try:
            users_ref = self.db.child('users')
            users = users_ref.order_by_child('email').equal_to(email).get()
            
            if users:
                for user_id, user_data in users.items():
                    return {'id': user_id, **user_data}
            return None
        except Exception as e:
            print(f"Error getting user by email from Realtime Database: {e}")
            return None
    
    def update_user(self, user_id, data):
        """Update user in Realtime Database"""
        try:
            user_ref = self.db.child('users').child(user_id)
            user_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating user in Realtime Database: {e}")
            return False
    
    def get_all_users(self):
        """Get all users from Realtime Database"""
        try:
            users_ref = self.db.child('users')
            users_data = users_ref.get()
            
            if not users_data:
                return []
            
            users = []
            for user_id, user_data in users_data.items():
                users.append({'id': user_id, **user_data})
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def add_issue(self, issue_data):
        """Add issue to Realtime Database"""
        try:
            issues_ref = self.db.child('issues')
            new_issue_ref = issues_ref.push(issue_data)
            return new_issue_ref.key
        except Exception as e:
            print(f"Error adding issue to Realtime Database: {e}")
            return None
    
    def get_issues(self, user_id=None, limit=None):
        """Get issues from Realtime Database"""
        try:
            issues_ref = self.db.child('issues')
            
            if user_id:
                issues_data = issues_ref.order_by_child('user_id').equal_to(user_id).get()
            else:
                issues_data = issues_ref.get()
            
            if not issues_data:
                return []
            
            issues = []
            for issue_id, issue_data in issues_data.items():
                issues.append({'id': issue_id, **issue_data})
            
            # Sort by created_at (newest first)
            issues.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            if limit:
                issues = issues[:limit]
                
            return issues
        except Exception as e:
            print(f"Error getting issues from Realtime Database: {e}")
            return []
    
    def update_issue(self, issue_id, data):
        """Update issue in Realtime Database"""
        try:
            issue_ref = self.db.child('issues').child(issue_id)
            issue_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating issue: {e}")
            return False
    
    def delete_issue(self, issue_id):
        """Delete issue from Realtime Database"""
        try:
            issue_ref = self.db.child('issues').child(issue_id)
            issue_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting issue: {e}")
            return False
    
    def get_issues_with_user_info(self, limit=None):
        """Get issues with user information"""
        try:
            issues = self.get_issues(limit=limit)
            users_ref = self.db.child('users')
            
            for issue in issues:
                user_id = issue.get('user_id')
                if user_id:
                    user_data = users_ref.child(user_id).get()
                    if user_data:
                        issue['full_name'] = user_data.get('full_name', 'Unknown')
                        issue['email'] = user_data.get('email', 'Unknown')
                    else:
                        issue['full_name'] = 'Unknown User'
                        issue['email'] = 'Unknown'
                        
            return issues
        except Exception as e:
            print(f"Error getting issues with user info: {e}")
            return []
    
    def get_statistics(self):
        """Get system statistics"""
        try:
            users_data = self.db.child('users').get()
            issues_data = self.db.child('issues').get()
            
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
            print(f"Error getting statistics: {e}")
            return {'total_users': 0, 'total_issues': 0, 'pending_issues': 0}

# Initialize Firebase when module is imported
initialize_firebase()
