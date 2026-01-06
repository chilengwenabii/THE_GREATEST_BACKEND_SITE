import sqlite3
import os

DB_PATH = "backend/the_greatest.db"

def migrate_estimated_days():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # Add estimated_days
        if 'estimated_days' not in columns:
            print("Adding estimated_days column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN estimated_days INTEGER")
        else:
            print("estimated_days column already exists.")
            
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_estimated_days()
