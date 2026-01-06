from database import SessionLocal
from models import FamilyMemberORM
from auth import verify_password
from decouple import config

def test_auth():
    username = "Admin"
    password = "1"
    
    db = SessionLocal()
    try:
        user = db.query(FamilyMemberORM).filter(FamilyMemberORM.username.ilike(username)).first()
        if not user:
            print(f"User {username} not found")
            return
        
        print(f"User found: {user.username}")
        print(f"Role: {user.role}")
        print(f"Status: {user.status}")
        print(f"Is Active: {user.is_active}")
        
        is_valid = verify_password(password, user.password_hash)
        print(f"Password '1' valid: {is_valid}")
        
        if is_valid and user.role == 'admin':
            if user.is_active and user.status == 'active':
                print("Login should succeed and user is fully authorized")
            else:
                print("Login should succeed but account may have issues (not active/active status)")
        else:
            print("Login should fail")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_auth()
