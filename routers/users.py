from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from database import get_supabase_client
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
    supabase = get_supabase_client()
    try:
        supabase.table('family_members').update({
            'is_online': True,
            'last_seen': datetime.utcnow().isoformat()
        }).eq('id', current_user.id).execute()

        # Return updated user data
        response = supabase.table('family_members').select('*').eq('id', current_user.id).execute()
        user_data = response.data[0]
        return UserResponse(**user_data)
    except Exception as e:
        print(f"Error updating user online status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: FamilyMember = Depends(get_current_user)
):
    supabase = get_supabase_client()

    try:
        # Check for unique constraints
        if user_update.username and user_update.username != current_user.username:
            response = supabase.table('family_members').select('*').eq('username', user_update.username).execute()
            if response.data:
                raise HTTPException(status_code=400, detail="Username already taken")

        if user_update.email and user_update.email != current_user.email:
            response = supabase.table('family_members').select('*').eq('email', user_update.email).execute()
            if response.data:
                raise HTTPException(status_code=400, detail="Email already taken")

        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        if 'password' in update_data:
            update_data['password_hash'] = get_password_hash(update_data.pop('password'))

        update_data['last_seen'] = datetime.utcnow().isoformat()

        supabase.table('family_members').update(update_data).eq('id', current_user.id).execute()

        # Return updated user data
        response = supabase.table('family_members').select('*').eq('id', current_user.id).execute()
        user_data = response.data[0]
        return UserResponse(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/online-count")
def get_online_users_count():
    supabase = get_supabase_client()
    response = supabase.table('family_members').select('*').eq('is_online', True).execute()
    online_count = len(response.data)
    return {"online_users": online_count}

@router.post("/logout")
def logout(current_user: FamilyMember = Depends(get_current_user)):
    supabase = get_supabase_client()
    supabase.table('family_members').update({
        'is_online': False,
        'last_seen': datetime.utcnow().isoformat()
    }).eq('id', current_user.id).execute()
    return {"message": "Logged out successfully"}

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
    supabase = get_supabase_client()
    try:
        response = supabase.table('family_members').select('*').execute()
        return [UserAdminResponse(**user) for user in response.data]
    except Exception as e:
        print(f"Error getting all users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=UserAdminResponse)
def create_user(user: UserCreate, current_admin: FamilyMember = Depends(get_current_admin)):
    supabase = get_supabase_client()

    try:
        # Check for unique constraints
        response = supabase.table('family_members').select('*').eq('username', user.username).execute()
        if response.data:
            raise HTTPException(status_code=400, detail="Username already taken")

        response = supabase.table('family_members').select('*').eq('email', user.email).execute()
        if response.data:
            raise HTTPException(status_code=400, detail="Email already taken")

        password_hash = get_password_hash(user.password)
        user_data = {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "password_hash": password_hash,
            "role": user.role,
            "is_active": True,
            "is_online": False
        }

        response = supabase.table('family_members').insert(user_data).execute()
        return UserAdminResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    supabase = get_supabase_client()

    try:
        # Check if user exists
        response = supabase.table('family_members').select('*').eq('id', user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")

        db_user = response.data[0]

        # Check for unique constraints
        if user_update.username and user_update.username != db_user['username']:
            response = supabase.table('family_members').select('*').eq('username', user_update.username).execute()
            if response.data:
                raise HTTPException(status_code=400, detail="Username already taken")

        if user_update.email and user_update.email != db_user['email']:
            response = supabase.table('family_members').select('*').eq('email', user_update.email).execute()
            if response.data:
                raise HTTPException(status_code=400, detail="Email already taken")

        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        if 'password' in update_data:
            update_data['password_hash'] = get_password_hash(update_data.pop('password'))

        supabase.table('family_members').update(update_data).eq('id', user_id).execute()

        # Return updated user data
        response = supabase.table('family_members').select('*').eq('id', user_id).execute()
        user_data = response.data[0]
        return UserAdminResponse(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{user_id}")
def delete_user(user_id: str, current_admin: FamilyMember = Depends(get_current_admin)):
    supabase = get_supabase_client()

    try:
        # Check if user exists
        response = supabase.table('family_members').select('*').eq('id', user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")

        supabase.table('family_members').delete().eq('id', user_id).execute()
        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
