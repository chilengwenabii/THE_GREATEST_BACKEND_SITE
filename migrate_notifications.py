import sqlite3
import os

DB_PATH = "backend/the_greatest.db"

def migrate_notifications():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check messages table for is_read
        cursor.execute("PRAGMA table_info(messages)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_read' not in columns:
            print("Adding is_read column to messages...")
            cursor.execute("ALTER TABLE messages ADD COLUMN is_read BOOLEAN DEFAULT 0")
            
        # Create announcement_reads table if not exists
        print("Creating announcement_reads table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcement_reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            announcement_id INTEGER NOT NULL,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES family_members (id) ON DELETE CASCADE,
            FOREIGN KEY (announcement_id) REFERENCES announcements (id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
        print("Notification migration completed successfully.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_notifications()
