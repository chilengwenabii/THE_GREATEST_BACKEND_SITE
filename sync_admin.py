from database import SessionLocal
from models import FamilyMemberORM
from auth import get_password_hash
import os
from decouple import config

def sync_admin():
    admin_email = config("DEFAULT_ADMIN_EMAIL", default="admin@thegreatest.app")
    admin_password = config("DEFAULT_ADMIN_PASSWORD", default="11111111")
    admin_username = config("DEFAULT_ADMIN_USERNAME", default="admin")
    
    db = SessionLocal()
    try:
        # Check if requested admin already exists by username or email
        existing = db.query(FamilyMemberORM).filter(
            (FamilyMemberORM.email == admin_email) | (FamilyMemberORM.username == admin_username)
        ).first()
        
        if existing:
            print(f"Updating existing user '{existing.username}' to admin with requested credentials.")
            existing.username = admin_username
            existing.email = admin_email
            existing.password_hash = get_password_hash(admin_password)
            existing.role = "admin"
            existing.status = "active"
            db.commit()
            print(f"[OK] Admin user '{admin_username}' updated successfully.")
        else:
            # Create admin
            admin = FamilyMemberORM(
                username=admin_username,
                email=admin_email,
                full_name="Administrator",
                password_hash=get_password_hash(admin_password),
                role="admin",
                status="active",
                is_active=True,
                is_online=False
            )
            db.add(admin)
            db.commit()
            print(f"[OK] Default admin '{admin_username}' created successfully.")
    except Exception as e:
        print(f"[!] Error syncing admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_admin()
