import sqlite3

def check_users():
    conn = sqlite3.connect('the_greatest.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, full_name, role FROM family_members")
    users = cursor.fetchall()
    
    print("Users in DB:")
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Full Name: {user[2]}, Role: {user[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_users()
