from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import User
from auth import get_current_user, get_password_hash
from datetime import datetime

router = APIRouter()

class UserUpdate(BaseModel):
    username: str = None
    email: str = None
    full_name: str = None
    phone: str = None
    password: str = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone: str = None
    is_online: bool
    last_seen: datetime = None

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    # Update online status
    current_user.is_online = True
    current_user.last_seen = datetime.utcnow()
    db = next(get_db())
    db.commit()
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check for unique constraints
    if user_update.username and user_update.username != current_user.username:
        existing_user = db.query(User).filter(User.username == user_update.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")

    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already taken")

    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    if 'password' in update_data:
        update_data['hashed_password'] = get_password_hash(update_data.pop('password'))

    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/online-count")
def get_online_users_count(db: Session = Depends(get_db)):
    online_count = db.query(User).filter(User.is_online == True).count()
    return {"online_users": online_count}

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.is_online = False
    current_user.last_seen = datetime.utcnow()
    db.commit()
    return {"message": "Logged out successfully"}
