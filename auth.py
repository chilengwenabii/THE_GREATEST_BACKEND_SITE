"""
Authentication utilities: password hashing, JWT tokens, and user dependencies
"""
from datetime import datetime, timedelta
from typing import Optional
import os

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from decouple import config

from database import get_db
from models import FamilyMemberORM, FamilyMember

# =============================================================================
# Configuration
# =============================================================================

# Use environment variable, fallback to a default (change in production!)
SECRET_KEY = config("SECRET_KEY", default="your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES", default="60"))

# Internal API token from environment (no hardcoded fallback in production)
INTERNAL_API_TOKEN = config("INTERNAL_API_TOKEN", default="")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# =============================================================================
# Password Utilities
# =============================================================================

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a hash"""
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# =============================================================================
# JWT Token Utilities
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# =============================================================================
# User Dependencies
# =============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> FamilyMember:
    """
    Dependency to get the current authenticated user from JWT token.
    Returns a Pydantic FamilyMember model.
    """
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

    # Query user from database using SQLAlchemy
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.username == username).first()
    
    if not user:
        raise credentials_exception
    
    # Convert ORM model to Pydantic model
    return FamilyMember.model_validate(user)


def get_current_user_orm(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> FamilyMemberORM:
    """
    Dependency to get the current authenticated user as ORM object.
    Useful when you need to update the user or access relationships.
    """
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

    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.username == username).first()
    
    if not user:
        raise credentials_exception
    
    return user


def get_current_admin(
    current_user: FamilyMember = Depends(get_current_user)
) -> FamilyMember:
    """Dependency to ensure current user is an admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_internal_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> FamilyMember:
    """
    Dependency for internal API calls.
    Accepts either the internal API token or a valid admin JWT.
    """
    # Check for internal API token
    if INTERNAL_API_TOKEN and token == INTERNAL_API_TOKEN:
        # Return first admin user for internal API calls
        admin = db.query(FamilyMemberORM).filter(FamilyMemberORM.role == "admin").first()
        if admin:
            return FamilyMember.model_validate(admin)
    
    # Fall back to regular JWT validation
    user = get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return user


# =============================================================================
# Utility Functions
# =============================================================================

def get_user_count(db: Session) -> int:
    """Get total user count"""
    return db.query(FamilyMemberORM).count()
