from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import get_supabase_client
from models import FamilyMember
import os
from decouple import config

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

def authenticate_user(db: Session, username: str, password: str):
    from sqlalchemy import func
    # First try to find by username (case-insensitive)
    user = db.query(FamilyMember).filter(func.lower(FamilyMember.username) == username.lower()).first()
    if not user:
        # If not found by username, try by email (case-insensitive)
        user = db.query(FamilyMember).filter(func.lower(FamilyMember.email) == username.lower()).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

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

    supabase = get_supabase_client()
    try:
        response = supabase.table('family_members').select('*').eq('username', username).execute()
        user_data = response.data

        if not user_data:
            raise credentials_exception

        return FamilyMember(**user_data[0])
    except Exception as e:
        print(f"Error getting current user: {e}")
        raise credentials_exception

def get_user_count():
    supabase = get_supabase_client()
    try:
        response = supabase.table('family_members').select('*', count='exact').execute()
        return response.count
    except Exception as e:
        print(f"Error getting user count: {e}")
        return 0

def get_current_admin(current_user: FamilyMember = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
