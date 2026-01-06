from database import SessionLocal
from models import FamilyMemberORM
from auth import verify_password
import os

def list_users():
    db = SessionLocal()
    try:
        users = db.query(FamilyMemberORM).all()
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, Role: {u.role}, Status: {u.status}, Active: {u.is_active}")
            if u.username.lower() == "admin":
                is_pass_1 = verify_password("1", u.password_hash)
                print(f"  -> Password '1' matches: {is_pass_1}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
