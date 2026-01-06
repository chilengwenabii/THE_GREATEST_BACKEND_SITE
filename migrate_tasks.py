"""
Migration script to add missing columns to the tasks table.
Run this script once to update the database schema.
"""
import sqlite3
import os

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), 'the_greatest.db')

def migrate():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(tasks)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"Existing columns: {existing_columns}")
    
    # Columns to add (column_name, column_definition)
    columns_to_add = [
        ("progress", "INTEGER DEFAULT 0"),
        ("estimated_hours", "REAL"),
        ("actual_hours", "REAL"),
        ("tags", "VARCHAR(255)"),
        ("is_private", "BOOLEAN DEFAULT 0"),
        ("parent_id", "INTEGER REFERENCES tasks(id) ON DELETE CASCADE"),
        ("team_id", "VARCHAR(50)"),
    ]
    
    for col_name, col_def in columns_to_add:
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE tasks ADD COLUMN {col_name} {col_def}"
                print(f"Executing: {sql}")
                cursor.execute(sql)
                print(f"  [OK] Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"  [ERROR] Error adding column {col_name}: {e}")
        else:
            print(f"  [SKIP] Column already exists: {col_name}")
    
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
