from fastapi import APIRouter, Depends, HTTPException, status, Form
from datetime import timedelta
from database import get_supabase_client
from models import FamilyMember
from auth import authenticate_user, create_access_token, get_password_hash, get_user_count
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

@router.post("/register", response_model=Token)
def register(user: UserCreate):
    supabase = get_supabase_client()

    # Check if user limit reached (15 users)
    user_count = get_user_count()
    if user_count >= 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User limit reached. No more registrations allowed."
        )

    try:
        # Check if user already exists
        response = supabase.table('family_members').select('*').eq('username', user.username).execute()
        if response.data:
            raise HTTPException(status_code=400, detail="Username already registered")

        response = supabase.table('family_members').select('*').eq('email', user.email).execute()
        if response.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        password_hash = get_password_hash(user.password)
        user_data = {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "password_hash": password_hash,
            "role": "user",
            "is_active": True,
            "is_online": False
        }

        response = supabase.table('family_members').insert(user_data).execute()
        new_user = response.data[0]

        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": new_user['username']}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        print(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest):
    supabase = get_supabase_client()

    try:
        # Try to find user by username or email (case-insensitive)
        response = supabase.table('family_members').select('*').ilike('username', credentials.username).execute()
        user_data = response.data

        if not user_data:
            response = supabase.table('family_members').select('*').ilike('email', credentials.username).execute()
            user_data = response.data

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = user_data[0]

        # Verify password
        if not get_password_hash.verify(credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user['username']}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
