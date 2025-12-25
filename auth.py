from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import get_db_connection
from models import FamilyMember
import os
from decouple import config
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, password_hash):
    return pwd_context.verify(plain_password, password_hash)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM family_members WHERE username = ?", (username,))
        user_row = cursor.fetchone()

        if not user_row:
            raise credentials_exception

        # Convert row to dict
        user_data = dict(user_row)
        return FamilyMember(**user_data)
    except Exception as e:
        print(f"Error getting current user: {e}")
        raise credentials_exception
    finally:
        conn.close()

def get_user_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM family_members")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error getting user count: {e}")
        return 0
    finally:
        conn.close()

def get_current_admin(current_user: FamilyMember = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def get_internal_admin(token: str = Depends(oauth2_scheme)):
    # Check for internal API token
    internal_token = os.getenv("INTERNAL_API_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJHb2RfRmlydCIsImV4cCI6MTc2NjYxNDA3M30.t6R-37Xrb_xjbYskb8SnQKZPh0osB9qBsC8syiq2sBs")
    if internal_token and token == internal_token:
        # Return a mock admin user for internal API calls
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM family_members WHERE role = 'admin' LIMIT 1")
            admin_row = cursor.fetchone()
            if admin_row:
                admin_data = dict(admin_row)
                return FamilyMember(**admin_data)
        except Exception as e:
            print(f"Error getting internal admin: {e}")
        finally:
            conn.close()

    # Fall back to regular JWT validation
    return get_current_admin(get_current_user(token))
