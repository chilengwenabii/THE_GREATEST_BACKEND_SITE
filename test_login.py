from auth import verify_password, get_password_hash
from database import get_supabase_client

supabase = get_supabase_client()

# Check all users
response = supabase.table('family_members').select('*').execute()
users = response.data
print('All users:', users)

# Check by username
response = supabase.table('family_members').select('*').eq('username', 'THE GREATEST').execute()
user = response.data[0] if response.data else None

if not user:
    # Check by email
    response = supabase.table('family_members').select('*').eq('email', 'thegreatest@gmail.com').execute()
    user = response.data[0] if response.data else None

if user:
    print('User found:', user['username'])
    print('Password hash:', user['password_hash'])
    print('Verify password:', verify_password('0769636386', user['password_hash']))
    # Test hashing the password again
    new_hash = get_password_hash('0769636386')
    print('New hash:', new_hash)
    print('Verify new hash:', verify_password('0769636386', new_hash))
else:
    print('User not found')
