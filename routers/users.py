from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from database import get_db_connection
from models import FamilyMember
from auth import get_current_user, get_password_hash, get_current_admin
from datetime import datetime

router = APIRouter()

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_online: bool
    last_seen: Optional[datetime] = None

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: FamilyMember = Depends(get_current_user)):
    # Update online status
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE family_members
            SET is_online = 1, last_seen = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), current_user.id))

        # Return updated user data
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (current_user.id,))
        user_data = cursor.fetchone()
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return UserResponse(**dict(user_data))
    except Exception as e:
        print(f"Error updating user online status: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: FamilyMember = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check for unique constraints
        if user_update.username and user_update.username != current_user.username:
            cursor.execute("SELECT id FROM family_members WHERE username = ?", (user_update.username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username already taken")

        if user_update.email and user_update.email != current_user.email:
            cursor.execute("SELECT id FROM family_members WHERE email = ?", (user_update.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already taken")

        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        if 'password' in update_data:
            update_data['password_hash'] = get_password_hash(update_data.pop('password'))

        update_data['last_seen'] = datetime.utcnow().isoformat()

        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [current_user.id]
        cursor.execute(f"UPDATE family_members SET {set_clause} WHERE id = ?", values)

        # Return updated user data
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (current_user.id,))
        user_data = cursor.fetchone()
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return UserResponse(**dict(user_data))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.get("/online-count")
def get_online_users_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM family_members WHERE is_online = 1")
        online_count = cursor.fetchone()[0]
        return {"online_users": online_count}
    except Exception as e:
        print(f"Error getting online count: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.post("/logout")
def logout(current_user: FamilyMember = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE family_members
            SET is_online = 0, last_seen = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), current_user.id))
        conn.commit()
        return {"message": "Logged out successfully"}
    except Exception as e:
        print(f"Error logging out: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# Admin CRUD endpoints
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    password: str
    role: Optional[str] = "user"

class UserAdminResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime] = None
    created_at: datetime

@router.get("/", response_model=list[UserAdminResponse])
def get_all_users(current_admin: FamilyMember = Depends(get_current_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM family_members")
        users = cursor.fetchall()
        return [UserAdminResponse(**dict(user)) for user in users]
    except Exception as e:
        print(f"Error getting all users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.post("/", response_model=UserAdminResponse)
def create_user(user: UserCreate, current_admin: FamilyMember = Depends(get_current_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check for unique constraints
        cursor.execute("SELECT id FROM family_members WHERE username = ?", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already taken")

        cursor.execute("SELECT id FROM family_members WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already taken")

        password_hash = get_password_hash(user.password)
        user_data = (
            user.username,
            user.email,
            user.full_name,
            password_hash,
            user.role,
            "active",  # status
            None,      # avatar_url
            1,         # is_active
            0,         # is_online
            None       # last_seen
        )

        cursor.execute("""
            INSERT INTO family_members
            (username, email, full_name, password_hash, role, status, avatar_url, is_active, is_online, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, user_data)

        user_id = cursor.lastrowid
        conn.commit()

        # Return the created user
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (user_id,))
        created_user = cursor.fetchone()
        return UserAdminResponse(**dict(created_user))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.put("/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if user exists
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (user_id,))
        db_user = cursor.fetchone()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        db_user = dict(db_user)

        # Check for unique constraints
        if user_update.username and user_update.username != db_user['username']:
            cursor.execute("SELECT id FROM family_members WHERE username = ?", (user_update.username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username already taken")

        if user_update.email and user_update.email != db_user['email']:
            cursor.execute("SELECT id FROM family_members WHERE email = ?", (user_update.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already taken")

        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        if 'password' in update_data:
            update_data['password_hash'] = get_password_hash(update_data.pop('password'))

        if update_data:
            set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values()) + [user_id]
            cursor.execute(f"UPDATE family_members SET {set_clause} WHERE id = ?", values)

        # Return updated user data
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.commit()
        return UserAdminResponse(**dict(user_data))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.delete("/{user_id}")
def delete_user(user_id: str, current_admin: FamilyMember = Depends(get_current_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if user exists
        cursor.execute("SELECT id FROM family_members WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("DELETE FROM family_members WHERE id = ?", (user_id,))
        conn.commit()
        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()
