import firebase_admin
from firebase_admin import credentials, auth, firestore
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
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False

def get_firestore_client():
    """Get Firestore database client"""
    try:
        return firestore.client()
    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        return None

def verify_firebase_token(id_token):
    """Verify Firebase ID token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None

def create_custom_token(uid):
    """Create custom token for user"""
    try:
        custom_token = auth.create_custom_token(uid)
        return custom_token
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None

def get_user_by_email(email):
    """Get user by email from Firebase Auth"""
    try:
        user = auth.get_user_by_email(email)
        return user
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

def create_firebase_user(email, password, display_name=None):
    """Create user in Firebase Auth"""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False
        )
        return user
    except Exception as e:
        print(f"Error creating Firebase user: {e}")
        return None

def update_user_email_verification(uid, verified=True):
    """Update user email verification status"""
    try:
        auth.update_user(uid, email_verified=verified)
        return True
    except Exception as e:
        print(f"Error updating email verification: {e}")
        return False

def delete_firebase_user(uid):
    """Delete user from Firebase Auth"""
    try:
        auth.delete_user(uid)
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

# Firestore database operations
class FirestoreDB:
    def __init__(self):
        self.db = get_firestore_client()
    
    def add_user(self, user_data):
        """Add user to Firestore"""
        try:
            doc_ref = self.db.collection('users').document()
            doc_ref.set(user_data)
            return doc_ref.id
        except Exception as e:
            print(f"Error adding user to Firestore: {e}")
            return None
    
    def get_user(self, user_id):
        """Get user from Firestore"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user from Firestore: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email from Firestore"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('email', '==', email).limit(1)
            docs = query.stream()
            
            for doc in docs:
                return {'id': doc.id, **doc.to_dict()}
            return None
        except Exception as e:
            print(f"Error getting user by email from Firestore: {e}")
            return None
    
    def update_user(self, user_id, data):
        """Update user in Firestore"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating user in Firestore: {e}")
            return False
    
    def add_issue(self, issue_data):
        """Add issue to Firestore"""
        try:
            doc_ref = self.db.collection('issues').document()
            doc_ref.set(issue_data)
            return doc_ref.id
        except Exception as e:
            print(f"Error adding issue to Firestore: {e}")
            return None
    
    def get_issues(self, limit=None):
        """Get issues from Firestore"""
        try:
            issues_ref = self.db.collection('issues')
            if limit:
                query = issues_ref.limit(limit)
            else:
                query = issues_ref
            
            docs = query.stream()
            issues = []
            for doc in docs:
                issues.append({'id': doc.id, **doc.to_dict()})
            return issues
        except Exception as e:
            print(f"Error getting issues from Firestore: {e}")
            return []

# Initialize Firebase when module is imported
initialize_firebase()
