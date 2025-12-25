import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'the_greatest.db')

def migrate_family_members():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Check current schema
        cursor.execute('PRAGMA table_info(family_members)')
        current_columns = {col[1]: col[2] for col in cursor.fetchall()}

        print("Current columns:", list(current_columns.keys()))

        # Always recreate the table with the correct schema
        print("Recreating family_members table with correct schema...")

        # Backup existing data
        cursor.execute('SELECT * FROM family_members')
        existing_data = cursor.fetchall()

        # Get column names for backup
        cursor.execute('PRAGMA table_info(family_members)')
        old_columns = [col[1] for col in cursor.fetchall()]

        # Drop and recreate table
        cursor.execute('DROP TABLE family_members')

        # Create table with correct schema
        cursor.execute('''
            CREATE TABLE family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                avatar_url VARCHAR(255),
                status VARCHAR(20) DEFAULT 'active',
                is_active BOOLEAN DEFAULT 1,
                is_online BOOLEAN DEFAULT 0,
                last_seen DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Restore data if we have any
        if existing_data:
            print(f"Restoring {len(existing_data)} existing records...")
            for row in existing_data:
                # Map old data to new schema
                # Assuming old order: id, username, email, full_name, phone, hashed_password, is_active, is_online, last_seen, created_at
                old_row = dict(zip(old_columns, row))
                new_data = (
                    old_row.get('id'),
                    old_row.get('username'),
                    old_row.get('email'),
                    old_row.get('full_name'),
                    old_row.get('phone'),
                    old_row.get('hashed_password'),  # This will be password_hash now
                    old_row.get('role', 'user'),
                    old_row.get('avatar_url'),
                    old_row.get('status', 'active'),
                    old_row.get('is_active', 1),
                    old_row.get('is_online', 0),
                    old_row.get('last_seen'),
                    old_row.get('created_at'),
                    old_row.get('updated_at')
                )
                cursor.execute('''
                    INSERT INTO family_members
                    (id, username, email, full_name, phone, password_hash, role, avatar_url, status, is_active, is_online, last_seen, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', new_data)

        conn.commit()
        print("Migration completed successfully")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_family_members()
