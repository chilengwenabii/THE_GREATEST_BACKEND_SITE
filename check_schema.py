import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'the_greatest.db')

def check_schema():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get table info
    cursor.execute('PRAGMA table_info(family_members)')
    columns = cursor.fetchall()

    print("Current family_members table schema:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    conn.close()

if __name__ == "__main__":
    check_schema()
