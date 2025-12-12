#!/usr/bin/env python3
"""
Test script to check backend startup and Supabase connection
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing backend imports...")

    # Test database import
    from database import engine, Base, test_supabase_connection
    print("✓ Database module imported successfully")

    # Test Supabase connection
    print("Testing Supabase connection...")
    test_supabase_connection()

    # Test main app import
    from main import app
    print("✓ Main app imported successfully")

    # Test routers import
    from routers import auth, chat, files, projects, users
    print("✓ All routers imported successfully")

    print("\n🎉 Backend startup test completed successfully!")
    print("The backend should run locally without issues.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during startup test: {e}")
    sys.exit(1)
