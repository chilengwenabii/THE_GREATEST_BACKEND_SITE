import sys
import os
import traceback

# Add the current directory to sys.path to allow importing from it
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("[INFO] Starting backend startup test...")
    
    # Test database import
    import database
    from database import test_connection
    print("[OK] Database module imported successfully")

    # Test models import
    import models
    print("[OK] Models module imported successfully")

    # Test main app import
    from main import app
    print("[OK] Main app imported successfully")

    # Test routers import
    from routers import auth, chat, files, projects, users, tasks, announcements, admin, search, analytics
    print("[OK] All routers imported successfully")

    if test_connection():
        print("[OK] Database connection successful")
    else:
        print("[FAIL] Database connection failed")

    print("[DONE] Startup test completed successfully")
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error during startup test: {e}")
    traceback.print_exc()
    sys.exit(1)
