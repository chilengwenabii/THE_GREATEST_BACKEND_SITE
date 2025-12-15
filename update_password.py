from passlib.context import CryptContext
from database import get_supabase_client

# Use pbkdf2_sha256 context to generate hash
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

supabase = get_supabase_client()

# Password to hash
password = '0769636386'

# Generate new hash
new_hash = pwd_context.hash(password)
print(f'New password hash: {new_hash}')

# Update the user in database
response = supabase.table('family_members').update({'password_hash': new_hash}).eq('username', 'THE_GREATEST').execute()

if response.data:
    print('Password hash updated successfully')
else:
    print('Failed to update password hash')
