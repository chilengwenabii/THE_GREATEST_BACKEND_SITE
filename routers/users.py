"""
Users Router: User profile and admin user management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import FamilyMemberORM, FamilyMember, UserResponse
from auth import get_current_user, get_current_admin, get_password_hash

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    password: str
    role: Optional[str] = "user"


class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Current User Endpoints
# =============================================================================

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info and update online status"""
    # Update online status
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == current_user.id).first()
    if user:
        user.is_online = True
        user.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    
    raise HTTPException(status_code=404, detail="User not found")


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for unique constraints
    if user_update.username and user_update.username != user.username:
        existing = db.query(FamilyMemberORM).filter(
            FamilyMemberORM.username == user_update.username
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    if user_update.email and user_update.email != user.email:
        existing = db.query(FamilyMemberORM).filter(
            FamilyMemberORM.email == user_update.email
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.get("/stats")
def get_user_dashboard_stats(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for normal users"""
    from models import TaskORM, ProjectORM
    
    total_users = db.query(FamilyMemberORM).count()
    online_users = db.query(FamilyMemberORM).filter(FamilyMemberORM.is_online == True).count()
    active_projects = db.query(ProjectORM).filter(
        ProjectORM.deleted_at == None,
        ProjectORM.status == "active"
    ).count()
    completed_tasks = db.query(TaskORM).filter(
        TaskORM.status == "completed",
        TaskORM.assigned_to == current_user.id
    ).count()
    pending_tasks = db.query(TaskORM).filter(
        TaskORM.status == "pending",
        TaskORM.assigned_to == current_user.id
    ).count()
    
    return {
        "total_users": total_users,
        "online_users": online_users,
        "active_projects": active_projects,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks
    }


@router.get("/online-count")
def get_online_users_count(db: Session = Depends(get_db)):
    """Get count of online users"""
    count = db.query(FamilyMemberORM).filter(FamilyMemberORM.is_online == True).count()
    return {"online_users": count}


@router.get("/all", response_model=list[UserAdminResponse])
def get_all_users_for_team(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users for team page (regular users can view)"""
    users = db.query(FamilyMemberORM).all()
    return [UserAdminResponse.model_validate(u) for u in users]


@router.post("/logout")
def logout(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout current user"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == current_user.id).first()
    if user:
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.commit()
    return {"message": "Logged out successfully"}


# =============================================================================
# Admin User Management Endpoints
# =============================================================================

@router.get("/", response_model=list[UserAdminResponse])
def get_all_users(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    users = db.query(FamilyMemberORM).all()
    return [UserAdminResponse.model_validate(u) for u in users]


@router.post("/", response_model=UserAdminResponse)
def create_user(
    user: UserCreate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check username uniqueness
    if db.query(FamilyMemberORM).filter(FamilyMemberORM.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check email uniqueness
    if db.query(FamilyMemberORM).filter(FamilyMemberORM.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already taken")
    
    db_user = FamilyMemberORM(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        password_hash=get_password_hash(user.password),
        role=user.role,
        status="active",
        is_active=True,
        is_online=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserAdminResponse.model_validate(db_user)


@router.put("/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check unique constraints if changing username or email
    if user_update.username and user_update.username != user.username:
        if db.query(FamilyMemberORM).filter(FamilyMemberORM.username == user_update.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")
    
    if user_update.email and user_update.email != user.email:
        if db.query(FamilyMemberORM).filter(FamilyMemberORM.email == user_update.email).first():
            raise HTTPException(status_code=400, detail="Email already taken")
    
    update_data = user_update.model_dump(exclude_unset=True)
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserAdminResponse.model_validate(user)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}
