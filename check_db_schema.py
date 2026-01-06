import sqlite3

def check_db_schema():
    conn = sqlite3.connect('the_greatest.db')
    cursor = conn.cursor()
    
    # Check tasks table
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    print("Tasks table columns:")
    for col in columns:
        print(f"- {col[1]}")
    
    # Check task_assignees table
    print("\nChecking for task_assignees table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_assignees'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("SUCCESS: task_assignees table exists.")
        cursor.execute("PRAGMA table_info(task_assignees)")
        cols = cursor.fetchall()
        for col in cols:
            print(f"  - {col[1]}")
    else:
        print("WARNING: task_assignees table is MISSING!")
    
    conn.close()

if __name__ == "__main__":
    check_db_schema()
