import sqlite3
import os

DB_PATH = "backend/the_greatest.db"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("--- Tables ---")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
            
        print("\n--- Columns in 'messages' ---")
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)

        print("\n--- Columns in 'announcement_reads' ---")
        cursor.execute("PRAGMA table_info(announcement_reads)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        print("\n--- Columns in 'announcements' ---")
        cursor.execute("PRAGMA table_info(announcements)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        print("\n--- Columns in 'tasks' ---")
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_db()
