#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from database import get_supabase_client
from auth import get_password_hash
from datetime import datetime

def test_register():
    supabase = get_supabase_client()

    try:
        # Test data
        user_data = {
            "username": "testuser123",
            "email": "test@example.com",
            "full_name": "Test User",
            "password_hash": get_password_hash("testpass123"),
            "role": "user",
            "status": "active",
            "avatar_url": None,
            "is_active": True,
            "is_online": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_seen": None
        }

        print("Attempting to insert user data:")
        print(user_data)

        response = supabase.table('family_members').insert(user_data).execute()
        print("Success! Response:", response.data)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_register()
