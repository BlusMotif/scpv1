from firebase_admin import auth
from flask import session, flash
import traceback

class FirebaseAuth:
    """Firebase Authentication integration for Flask app"""
    
    @staticmethod
    def create_user(email, password, display_name=None, email_verified=False):
        """Create a new user in Firebase Auth"""
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=email_verified
            )
            return user
        except Exception as e:
            print(f"Error creating Firebase user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email from Firebase Auth"""
        try:
            user = auth.get_user_by_email(email)
            return user
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def verify_password(email, password):
        """Verify user password (Note: Firebase Admin SDK doesn't support password verification directly)"""
        # For password verification, you would typically use Firebase Client SDK on frontend
        # or implement custom token verification
        return True
    
    @staticmethod
    def update_user(uid, **kwargs):
        """Update user in Firebase Auth"""
        try:
            auth.update_user(uid, **kwargs)
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    @staticmethod
    def delete_user(uid):
        """Delete user from Firebase Auth"""
        try:
            auth.delete_user(uid)
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    @staticmethod
    def create_custom_token(uid, additional_claims=None):
        """Create custom token for user"""
        try:
            token = auth.create_custom_token(uid, additional_claims)
            return token
        except Exception as e:
            print(f"Error creating custom token: {e}")
            return None
    
    @staticmethod
    def verify_id_token(id_token):
        """Verify Firebase ID token"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None
    
    @staticmethod
    def set_custom_user_claims(uid, custom_claims):
        """Set custom claims for user (for role-based access)"""
        try:
            auth.set_custom_user_claims(uid, custom_claims)
            return True
        except Exception as e:
            print(f"Error setting custom claims: {e}")
            return False
    
    @staticmethod
    def generate_email_verification_link(email):
        """Generate email verification link"""
        try:
            link = auth.generate_email_verification_link(email)
            return link
        except Exception as e:
            print(f"Error generating email verification link: {e}")
            return None
    
    @staticmethod
    def generate_password_reset_link(email):
        """Generate password reset link"""
        try:
            link = auth.generate_password_reset_link(email)
            return link
        except Exception as e:
            print(f"Error generating password reset link: {e}")
            return None
