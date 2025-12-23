from database import get_supabase_client
from auth import get_password_hash

def create_tables():
    supabase = get_supabase_client()

    # Create projects table if it doesn't exist
    try:
        # Check if projects table exists by trying to select from it
        response = supabase.table('projects').select('*').limit(1).execute()
        print("Projects table already exists")
    except Exception as e:
        print(f"Projects table might not exist: {e}")
        print("Please create the projects table in Supabase with the following structure:")
        print("""
        CREATE TABLE projects (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_by UUID REFERENCES family_members(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """)

    # Add last_seen column to family_members table if it doesn't exist
    try:
        # Try to update a user with last_seen to see if column exists
        test_user = supabase.table('family_members').select('id').limit(1).execute()
        if test_user.data:
            user_id = test_user.data[0]['id']
            supabase.table('family_members').update({
                'last_seen': '2024-01-01T00:00:00Z'
            }).eq('id', user_id).execute()
            print("last_seen column exists")
        else:
            print("No users found to test last_seen column")
    except Exception as e:
        print(f"last_seen column might not exist: {e}")
        print("Please add the last_seen column to family_members table:")
        print("ALTER TABLE family_members ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;")

def insert_admin_user():
    supabase = get_supabase_client()

    # Check if admin already exists
    response = supabase.table('family_members').select('*').eq('username', 'God_Firt').execute()
    if response.data:
        print("Admin user already exists")
        return

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
    create_tables()
    insert_admin_user()
