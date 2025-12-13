from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Task, FamilyMember
from auth import get_current_admin
from datetime import datetime

router = APIRouter()

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

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    assigned_to: Optional[int] = None
    assigned_user: Optional[dict] = None
    created_by: int
    creator: dict
    created_at: datetime
    updated_at: Optional[datetime] = None

@router.get("/", response_model=list[TaskResponse])
def get_all_tasks(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    tasks = db.query(Task).all()
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "assigned_to": task.assigned_to,
            "assigned_user": {
                "id": task.assigned_user.id,
                "username": task.assigned_user.username,
                "full_name": task.assigned_user.full_name
            } if task.assigned_user else None,
            "created_by": task.created_by,
            "creator": {
                "id": task.creator.id,
                "username": task.creator.username,
                "full_name": task.creator.full_name
            },
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        result.append(task_dict)
    return result

@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if task.assigned_to:
        assigned_user = db.query(FamilyMember).filter(FamilyMember.id == task.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")

    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        assigned_to=task.assigned_to,
        created_by=current_admin.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "status": db_task.status,
        "assigned_to": db_task.assigned_to,
        "assigned_user": {
            "id": db_task.assigned_user.id,
            "username": db_task.assigned_user.username,
            "full_name": db_task.assigned_user.full_name
        } if db_task.assigned_user else None,
        "created_by": db_task.created_by,
        "creator": {
            "id": db_task.creator.id,
            "username": db_task.creator.username,
            "full_name": db_task.creator.full_name
        },
        "created_at": db_task.created_at,
        "updated_at": db_task.updated_at
    }

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_update.assigned_to:
        assigned_user = db.query(FamilyMember).filter(FamilyMember.id == task_update.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")

    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "status": db_task.status,
        "assigned_to": db_task.assigned_to,
        "assigned_user": {
            "id": db_task.assigned_user.id,
            "username": db_task.assigned_user.username,
            "full_name": db_task.assigned_user.full_name
        } if db_task.assigned_user else None,
        "created_by": db_task.created_by,
        "creator": {
            "id": db_task.creator.id,
            "username": db_task.creator.username,
            "full_name": db_task.creator.full_name
        },
        "created_at": db_task.created_at,
        "updated_at": db_task.updated_at
    }

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
