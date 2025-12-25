#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from database import get_supabase_client

def test_database_connection():
    """Test Supabase database connection and table structure"""
    supabase = get_supabase_client()

    try:
        # Test family_members table
        response = supabase.table('family_members').select('*').limit(1).execute()
        print('✓ family_members table accessible')

        if response.data:
            print('Sample user:', response.data[0])
            print('Available columns:', list(response.data[0].keys()))
        else:
            print('Table exists but no data')

        # Test projects table
        try:
            response = supabase.table('projects').select('*').limit(1).execute()
            print('✓ projects table accessible')
        except Exception as e:
            print(f'✗ projects table error: {e}')

        # Test announcements table
        try:
            response = supabase.table('announcements').select('*').limit(1).execute()
            print('✓ announcements table accessible')
        except Exception as e:
            print(f'✗ announcements table error: {e}')

        # Test activities table
        try:
            response = supabase.table('activities').select('*').limit(1).execute()
            print('✓ activities table accessible')
        except Exception as e:
            print(f'✗ activities table error: {e}')

        # Test team_members table
        try:
            response = supabase.table('team_members').select('*').limit(1).execute()
            print('✓ team_members table accessible')
        except Exception as e:
            print(f'✗ team_members table error: {e}')

        # Test chat_messages table
        try:
            response = supabase.table('chat_messages').select('*').limit(1).execute()
            print('✓ chat_messages table accessible')
        except Exception as e:
            print(f'✗ chat_messages table error: {e}')

    except Exception as e:
        print(f'✗ Database connection error: {e}')

if __name__ == "__main__":
    test_database_connection()
