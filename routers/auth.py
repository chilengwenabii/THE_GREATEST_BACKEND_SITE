"""
Authentication Router: Login and Registration endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel

from database import get_db
from models import FamilyMemberORM
from auth import create_access_token, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

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
    role: str = None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    existing_user = db.query(FamilyMemberORM).filter(
        FamilyMemberORM.username == user.username
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(FamilyMemberORM).filter(
        FamilyMemberORM.email == user.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    password_hash = get_password_hash(user.password)
    db_user = FamilyMemberORM(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=password_hash,
        role=user.role,
        status="active",
        is_active=True,
        is_online=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id
    }


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token"""
    # Try to find user by username (case-insensitive)
    user = db.query(FamilyMemberORM).filter(
        FamilyMemberORM.username.ilike(credentials.username)
    ).first()
    
    # If not found by username, try email
    if not user:
        user = db.query(FamilyMemberORM).filter(
            FamilyMemberORM.email.ilike(credentials.username)
        ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }
