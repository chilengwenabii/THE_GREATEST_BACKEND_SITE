import sqlite3
import os
from database import get_db_connection
from auth import get_password_hash

def create_tables():
    """Create all necessary tables in SQLite database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Drop existing tables if they exist
        tables_to_drop = [
            'family_member_conversations',
            'tasks',
            'announcements',
            'projects',
            'files',
            'messages',
            'conversations',
            'family_members'
        ]

        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            except Exception as e:
                print(f"Warning: Could not drop table {table}: {e}")

        # Read and execute the SQL schema
        schema_path = os.path.join(os.path.dirname(__file__), 'family_members.sql')
        with open(schema_path, 'r') as f:
            sql_script = f.read()

        # Execute the entire script
        cursor.executescript(sql_script)
        conn.commit()
        print("All tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()

def insert_admin_user():
    """Insert the default admin user if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if admin already exists
        cursor.execute("SELECT id FROM family_members WHERE username = ?", ('God_Firt',))
        if cursor.fetchone():
            print("Admin user already exists")
            return

        # Generate proper password hash for 'THANKYOU_GOD_0@9'
        password_hash = get_password_hash('THANKYOU_GOD_0@9')

        user_data = (
            'God_Firt',
            'admin@thegreatest.com',
            'System Administrator',
            password_hash,
            'admin',
            'active',
            1,  # is_active
            0,  # is_online
        )

        cursor.execute("""
            INSERT INTO family_members
            (username, email, full_name, password_hash, role, status, is_active, is_online)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, user_data)

        conn.commit()
        print("Admin user inserted successfully")
    except Exception as e:
        print(f"Error inserting admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()
    insert_admin_user()
