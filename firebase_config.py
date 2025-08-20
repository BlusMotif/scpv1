import json
import os
from datetime import datetime
import uuid

class MockRealtimeDB:
    def __init__(self):
        self.data_file = 'local_database.json'
        self.data = self.load_data()

    def load_data(self):
        """Load data from local JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'users': {}, 'issues': {}}

    def save_data(self):
        """Save data to local JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def add_user(self, user_data):
        """Add user to database"""
        try:
            user_id = str(uuid.uuid4())
            self.data['users'][user_id] = user_data
            self.save_data()
            return user_id
        except Exception as e:
            print(f"Error adding user: {e}")
            return None

    def get_user(self, user_id):
        """Get user from database"""
        try:
            user_data = self.data['users'].get(user_id)
            if user_data:
                return {'id': user_id, **user_data}
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def get_user_by_email(self, email):
        """Get user by email from database"""
        try:
            for user_id, user_data in self.data['users'].items():
                if user_data.get('email') == email:
                    return {'id': user_id, **user_data}
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def update_user(self, user_id, data):
        """Update user in database"""
        try:
            if user_id in self.data['users']:
                self.data['users'][user_id].update(data)
                self.save_data()
                return True
            return False
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def get_all_users(self):
        """Get all users from database"""
        try:
            users = []
            for user_id, user_data in self.data['users'].items():
                users.append({'id': user_id, **user_data})
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    def add_issue(self, issue_data):
        """Add issue to database"""
        try:
            issue_id = str(uuid.uuid4())
            self.data['issues'][issue_id] = issue_data
            self.save_data()
            return issue_id
        except Exception as e:
            print(f"Error adding issue: {e}")
            return None

    def get_issues(self, user_id=None, limit=None):
        """Get issues from database"""
        try:
            issues = []
            for issue_id, issue_data in self.data['issues'].items():
                if user_id and issue_data.get('user_id') != user_id:
                    continue
                issues.append({'id': issue_id, **issue_data})

            # Sort by created_at (newest first)
            issues.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            if limit:
                issues = issues[:limit]

            return issues
        except Exception as e:
            print(f"Error getting issues: {e}")
            return []

    def update_issue(self, issue_id, data):
        """Update issue in database"""
        try:
            if issue_id in self.data['issues']:
                self.data['issues'][issue_id].update(data)
                self.save_data()
                return True
            return False
        except Exception as e:
            print(f"Error updating issue: {e}")
            return False

    def delete_issue(self, issue_id):
        """Delete issue from database"""
        try:
            if issue_id in self.data['issues']:
                del self.data['issues'][issue_id]
                self.save_data()
                return True
            return False
        except Exception as e:
            print(f"Error deleting issue: {e}")
            return False

    def get_issues_with_user_info(self, limit=None):
        """Get issues with user information"""
        try:
            issues = self.get_issues(limit=limit)

            for issue in issues:
                user_id = issue.get('user_id')
                if user_id and user_id in self.data['users']:
                    user_data = self.data['users'][user_id]
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
            total_users = len(self.data['users'])
            total_issues = len(self.data['issues'])

            pending_issues = 0
            for issue_data in self.data['issues'].values():
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

# Use mock database instead of Firebase for now
def initialize_firebase():
    """Initialize mock database system"""
    print("Using local mock database (no Firebase connection needed)")
    return True

def get_realtime_db():
    """Get mock database reference"""
    return MockRealtimeDB()

# Database class for compatibility
class RealtimeDB(MockRealtimeDB):
    pass