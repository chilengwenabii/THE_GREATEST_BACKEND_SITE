import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'the_greatest.db')

def fix_schema():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Fix projects table
        cursor.execute('PRAGMA table_info(projects)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'external_links' not in columns:
            print("Adding 'external_links' to projects...")
            cursor.execute('ALTER TABLE projects ADD COLUMN external_links TEXT')
        if 'priority' not in columns:
            print("Adding 'priority' to projects...")
            cursor.execute('ALTER TABLE projects ADD COLUMN priority VARCHAR(20) DEFAULT "medium"')
        if 'deadline' not in columns:
            print("Adding 'deadline' to projects...")
            cursor.execute('ALTER TABLE projects ADD COLUMN deadline DATETIME')
        if 'tags' not in columns:
            print("Adding 'tags' to projects...")
            cursor.execute('ALTER TABLE projects ADD COLUMN tags VARCHAR(255)')
        if 'progress' not in columns:
            print("Adding 'progress' to projects...")
            cursor.execute('ALTER TABLE projects ADD COLUMN progress INTEGER DEFAULT 0')

        # Fix tasks table
        cursor.execute('PRAGMA table_info(tasks)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'deadline' not in columns:
            print("Adding 'deadline' to tasks...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN deadline DATETIME')
        if 'is_approved' not in columns:
            print("Adding 'is_approved' to tasks...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN is_approved BOOLEAN DEFAULT 1')
        if 'alert_count' not in columns:
            print("Adding 'alert_count' to tasks...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN alert_count INTEGER DEFAULT 0')
        if 'links' not in columns:
            print("Adding 'links' to tasks...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN links TEXT')
        if 'priority' not in columns:
            print("Adding 'priority' to tasks...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT "medium"')
        if 'estimated_days' not in columns:
            print("Adding 'estimated_days' to tasks...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN estimated_days INTEGER')
        if 'timeline_confirmed_at' not in columns:
            print("Adding 'timeline_confirmed_at' to tasks...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN timeline_confirmed_at DATETIME')

        # Fix files table
        cursor.execute('PRAGMA table_info(files)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'project_id' not in columns:
            print("Adding 'project_id' to files...")
            cursor.execute('ALTER TABLE files ADD COLUMN project_id INTEGER')
        if 'task_id' not in columns:
            print("Adding 'task_id' to files...")
            cursor.execute('ALTER TABLE files ADD COLUMN task_id INTEGER')

        # Fix conversations table
        cursor.execute('PRAGMA table_info(conversations)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'project_id' not in columns:
            print("Adding 'project_id' to conversations...")
            cursor.execute('ALTER TABLE conversations ADD COLUMN project_id INTEGER')

        # Fix messages table
        cursor.execute('PRAGMA table_info(messages)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'reply_to_id' not in columns:
            print("Adding 'reply_to_id' to messages...")
            cursor.execute('ALTER TABLE messages ADD COLUMN reply_to_id INTEGER')

        conn.commit()
        print("Schema fixed successfully")
    except Exception as e:
        print(f"Error fixing schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
