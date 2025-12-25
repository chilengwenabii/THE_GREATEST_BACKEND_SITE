from fastapi import APIRouter, Depends, HTTPException, status, Form
from datetime import timedelta
from database import get_db_connection
from models import FamilyMember
from auth import create_access_token, get_password_hash, verify_password
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "user"

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

@router.post("/register")
def register(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM family_members WHERE username = ?", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already registered")

        cursor.execute("SELECT id FROM family_members WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
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

        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {
            "message": "User registered successfully to SQLite",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id
        }

    except Exception as e:
        print(f"Error registering user: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Try to find user by username or email (case-insensitive)
        cursor.execute("SELECT * FROM family_members WHERE LOWER(username) = LOWER(?)", (credentials.username,))
        user_row = cursor.fetchone()

        if not user_row:
            cursor.execute("SELECT * FROM family_members WHERE LOWER(email) = LOWER(?)", (credentials.username,))
            user_row = cursor.fetchone()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert row to dict for compatibility
        user = dict(user_row)

        # Verify password
        if not verify_password(credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user['username']}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer", "role": user['role']}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()
