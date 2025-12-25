from database import get_db_connection
from auth import get_password_hash

def insert_admin_user():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate proper password hash for 'THANKYOU_GOD_0@9'
    password_hash = get_password_hash('THANKYOU_GOD_0@9')

    user_data = (
        "God_Firt",
        "admin@thegreatest.com",
        "System Administrator",
        password_hash,
        "admin",
        "active",  # status
        None,      # avatar_url
        1,         # is_active
        0,         # is_online
        None       # last_seen
    )

    try:
        cursor.execute("""
            INSERT INTO family_members
            (username, email, full_name, password_hash, role, status, avatar_url, is_active, is_online, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, user_data)

        conn.commit()
        print("Admin user inserted successfully")
    except Exception as e:
        print(f"Error inserting admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    insert_admin_user()
