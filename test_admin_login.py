from auth import verify_password
from database import get_supabase_client

supabase = get_supabase_client()

# Check for admin user 'God_Firt'
response = supabase.table('family_members').select('*').eq('username', 'God_Firt').execute()
user = response.data[0] if response.data else None

if user:
    print('Admin user found:', user['username'])
    print('Role:', user['role'])
    print('Password hash:', user['password_hash'])

    # Verify the password 'THANKYOU_GOD_0@9'
    is_valid = verify_password('THANKYOU_GOD_0@9', user['password_hash'])
    print('Password verification for THANKYOU_GOD_0@9:', is_valid)

    if is_valid and user['role'] == 'admin':
        print('Admin login is possible with the provided password.')
    else:
        print('Password is incorrect or user is not an admin.')
else:
    print('Admin user not found.')
