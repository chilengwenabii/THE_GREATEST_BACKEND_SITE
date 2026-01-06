import sqlite3
import os

# Database file path
# Database file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "the_greatest.db")

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "deleted_for_ids" not in column_names:
            print("Adding deleted_for_ids column to messages table...")
            cursor.execute("ALTER TABLE messages ADD COLUMN deleted_for_ids TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column deleted_for_ids already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
