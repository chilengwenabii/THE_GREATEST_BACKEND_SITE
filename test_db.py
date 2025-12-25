#!/usr/bin/env python3

from database import get_supabase_client

def test_database():
    supabase = get_supabase_client()
    try:
        # Check if family_members table exists and get its structure
        response = supabase.table('family_members').select('*').limit(1).execute()
        print('✓ family_members table exists')

        if response.data:
            print('Sample data:', response.data[0])
            print('Available columns:', list(response.data[0].keys()))
        else:
            print('Table exists but no data')

        # Try to get table info using raw SQL
        try:
            info_response = supabase.rpc('get_table_info', {'table_name': 'family_members'}).execute()
            print('Table info:', info_response.data)
        except:
            print('Could not get table info via RPC')

    except Exception as e:
        print(f'✗ Error accessing family_members table: {e}')

        # Try to see what tables exist
        try:
            # This might not work depending on Supabase permissions
            tables_response = supabase.table('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
            print('Available tables:', [row['table_name'] for row in tables_response.data])
        except Exception as e2:
            print(f'Could not list tables: {e2}')

if __name__ == "__main__":
    test_database()
