from database import get_supabase_client
from auth import get_password_hash

def insert_admin_user():
    supabase = get_supabase_client()

    # Generate proper password hash for 'THANKYOU_GOD_0@9'
    password_hash = get_password_hash('THANKYOU_GOD_0@9')

    user_data = {
        "username": "God_Firt",
        "email": "admin@thegreatest.com",
        "full_name": "System Administrator",
        "password_hash": password_hash,
        "role": "admin",
        "is_active": True,
        "is_online": False
    }

    try:
        response = supabase.table('family_members').insert(user_data).execute()
        print("Admin user inserted successfully:", response.data)
    except Exception as e:
        print(f"Error inserting admin user: {e}")

if __name__ == "__main__":
    insert_admin_user()
