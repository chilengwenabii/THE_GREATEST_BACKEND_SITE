import sqlite3
import os

DB_PATH = "backend/the_greatest.db"

def migrate_tasks_table():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # Add timeline_notes
        if 'timeline_notes' not in columns:
            print("Adding timeline_notes column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN timeline_notes TEXT")
            
        # Add proposed_deadline
        if 'proposed_deadline' not in columns:
            print("Adding proposed_deadline column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN proposed_deadline TIMESTAMP")
            
        # Add timeline_status
        if 'timeline_status' not in columns:
            print("Adding timeline_status column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN timeline_status VARCHAR(50) DEFAULT 'pending'")
            
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_tasks_table()
