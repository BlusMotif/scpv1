import sqlite3
from werkzeug.security import generate_password_hash

def get_db():
    import sqlite3
    conn = sqlite3.connect('university_issues.db')
    conn.row_factory = sqlite3.Row
    return conn

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with tables and sample users."""
    # Import and run the complete database initialization
    from init_database import init_complete_database
    init_complete_database()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
