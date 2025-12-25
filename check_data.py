import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'the_greatest.db')

def check_data():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check if family_members table has data
    cursor.execute('SELECT COUNT(*) FROM family_members')
    count = cursor.fetchone()[0]
    print(f"Number of users in family_members: {count}")

    if count > 0:
        cursor.execute('SELECT id, username, email FROM family_members LIMIT 5')
        users = cursor.fetchall()
        print("Sample users:")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")

    conn.close()

if __name__ == "__main__":
    check_data()
