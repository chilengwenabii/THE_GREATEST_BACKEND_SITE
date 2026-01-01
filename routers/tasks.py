"""
Tasks Router: Task CRUD endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import FamilyMemberORM, FamilyMember, TaskORM
from auth import get_current_admin, get_current_user

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    assigned_to: Optional[int] = None
    assigned_user: Optional[UserInfo] = None
    created_by: int
    creator: UserInfo
    created_at: datetime
    updated_at: Optional[datetime] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/me", response_model=list[TaskResponse])
def get_my_tasks(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tasks assigned to the current user"""
    tasks = db.query(TaskORM).filter(TaskORM.assigned_to == current_user.id).all()
    result = []
    
    for task in tasks:
        # Get creator info
        creator = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.created_by).first()
        creator_info = UserInfo(
            id=creator.id,
            username=creator.username,
            full_name=creator.full_name
        ) if creator else UserInfo(id=0, username="Unknown", full_name="Unknown")
        
        # Current user info for assigned_user
        assigned_user_info = UserInfo(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name
        )
        
        result.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            assigned_to=task.assigned_to,
            assigned_user=assigned_user_info,
            created_by=task.created_by,
            creator=creator_info,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))
    
    return result


@router.get("/", response_model=list[TaskResponse])
def get_all_tasks(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all tasks (admin only)"""
    tasks = db.query(TaskORM).all()
    result = []
    
    for task in tasks:
        # Get creator info
        creator = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.created_by).first()
        creator_info = UserInfo(
            id=creator.id,
            username=creator.username,
            full_name=creator.full_name
        ) if creator else UserInfo(id=0, username="Unknown", full_name="Unknown")
        
        # Get assigned user info
        assigned_user_info = None
        if task.assigned_to:
            assigned = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.assigned_to).first()
            if assigned:
                assigned_user_info = UserInfo(
                    id=assigned.id,
                    username=assigned.username,
                    full_name=assigned.full_name
                )
        
        result.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            assigned_to=task.assigned_to,
            assigned_user=assigned_user_info,
            created_by=task.created_by,
            creator=creator_info,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))
    
    return result


@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new task (admin only)"""
    # Validate assigned user if provided
    if task.assigned_to:
        assigned_user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
    
    db_task = TaskORM(
        title=task.title,
        description=task.description,
        status=task.status,
        assigned_to=task.assigned_to,
        created_by=current_admin.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Get creator info
    creator = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == current_admin.id).first()
    creator_info = UserInfo(
        id=creator.id,
        username=creator.username,
        full_name=creator.full_name
    )
    
    # Get assigned user info
    assigned_user_info = None
    if db_task.assigned_to:
        assigned = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == db_task.assigned_to).first()
        if assigned:
            assigned_user_info = UserInfo(
                id=assigned.id,
                username=assigned.username,
                full_name=assigned.full_name
            )
    
    return TaskResponse(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        assigned_to=db_task.assigned_to,
        assigned_user=assigned_user_info,
        created_by=db_task.created_by,
        creator=creator_info,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at
    )


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a task (admin only)"""
    db_task = db.query(TaskORM).filter(TaskORM.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Validate assigned user if provided
    if task_update.assigned_to:
        assigned_user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task_update.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    
    # Get creator info
    creator = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == db_task.created_by).first()
    creator_info = UserInfo(
        id=creator.id,
        username=creator.username,
        full_name=creator.full_name
    ) if creator else UserInfo(id=0, username="Unknown", full_name="Unknown")
    
    # Get assigned user info
    assigned_user_info = None
    if db_task.assigned_to:
        assigned = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == db_task.assigned_to).first()
        if assigned:
            assigned_user_info = UserInfo(
                id=assigned.id,
                username=assigned.username,
                full_name=assigned.full_name
            )
    
    return TaskResponse(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        assigned_to=db_task.assigned_to,
        assigned_user=assigned_user_info,
        created_by=db_task.created_by,
        creator=creator_info,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at
    )


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a task (admin only)"""
    db_task = db.query(TaskORM).filter(TaskORM.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    
    return {"message": "Task deleted successfully"}
