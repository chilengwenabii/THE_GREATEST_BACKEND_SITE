from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from decouple import config
from supabase import create_client, Client

# Use SQLite for local development
DATABASE_URL = "sqlite:///./the_greatest.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Supabase client configuration
SUPABASE_URL = "https://ppesvgdduwalpnqireaz.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_iKJ3BhovbnmrelVo9ZXt5w_6keSbuLq"

supabase = None
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
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
