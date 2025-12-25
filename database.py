import sqlite3
import os
from typing import Optional

# SQLite database configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'the_greatest.db')

def get_db_connection():
    """Get a SQLite database connection"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        print(f"Failed to connect to SQLite database: {e}")
        raise

def test_sqlite_connection():
    """Test SQLite database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM family_members")
        count = cursor.fetchone()[0]
        print(f"Successfully connected to SQLite database. Users count: {count}")
        conn.close()
        return True
    except Exception as e:
        print(f"Failed to connect to SQLite database: {e}")
        return False

def get_db():
    """Get the database connection (for compatibility with existing routers)"""
    return get_db_connection()

# For backward compatibility
def get_supabase_client():
    """Backward compatibility function that returns SQLite connection"""
    return get_db_connection()
