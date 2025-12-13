from supabase import create_client, Client
from decouple import config

# Supabase client configuration
SUPABASE_URL = "https://ppesvgdduwalpnqireaz.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_iKJ3BhovbnmrelVo9ZXt5w_6keSbuLq"

supabase: Client = None
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("Supabase client initialized successfully")
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    supabase = None

def test_supabase_connection():
    if not supabase:
        print("Supabase not configured")
        return

    try:
        # Test connection by fetching user count or a simple query
        response = supabase.table('family_members').select('*', count='exact').limit(1).execute()
        print("Successfully connected to Supabase")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")

def get_supabase_client() -> Client:
    """Get the Supabase client instance"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    return supabase

def get_db():
    """Get the Supabase client instance (for compatibility with existing routers)"""
    return get_supabase_client()
