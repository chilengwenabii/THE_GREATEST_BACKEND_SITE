"""
Tasks Router: Task CRUD endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import FamilyMemberORM, FamilyMember, TaskORM, FileORM, TaskUpdateORM, TaskAssigneeORM
from auth import get_current_admin, get_current_user

router = APIRouter()


# =============================================================================
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"
    assigned_to: Optional[int] = None
    priority: Optional[str] = "medium"
    links: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_days: Optional[int] = None
    timeline_confirmed_at: Optional[datetime] = None
    assigned_user_ids: Optional[List[int]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    priority: Optional[str] = None
    links: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_days: Optional[int] = None
    timeline_confirmed_at: Optional[datetime] = None
    is_approved: Optional[bool] = None
    assigned_user_ids: Optional[List[int]] = None


class TaskUpdateCreate(BaseModel):
    content: str


class TaskUpdateResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime


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
    deadline: Optional[datetime] = None
    is_approved: bool
    alert_count: int
    estimated_days: Optional[int] = None
    timeline_confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    priority: str = "medium"
    links: Optional[str] = None
    priority: str = "medium"
    links: Optional[str] = None
    files: List[dict] = []
    assignees: List[UserInfo] = []


# =============================================================================
# Helper Functions
# =============================================================================

def get_task_response(task: TaskORM, db: Session) -> TaskResponse:
    creator = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.created_by).first()
    creator_info = UserInfo(
        id=creator.id,
        username=creator.username,
        full_name=creator.full_name
    ) if creator else UserInfo(id=0, username="Unknown", full_name="Unknown")
    
    assigned_user_info = None
    if task.assigned_to:
        assigned = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.assigned_to).first()
        if assigned:
            assigned_user_info = UserInfo(
                id=assigned.id,
                username=assigned.username,
                full_name=assigned.full_name
            )
            
    files = db.query(FileORM).filter(FileORM.task_id == task.id).all()
    file_list = [
        {
            "id": f.id,
            "filename": f.filename,
            "file_path": f.file_path,
            "file_size": f.file_size,
            "content_type": f.content_type
        }
        for f in files
    ]

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        assigned_to=task.assigned_to,
        assigned_user=assigned_user_info,
        created_by=task.created_by,
        creator=creator_info,
        deadline=task.deadline,
        is_approved=task.is_approved,
        alert_count=task.alert_count,
        estimated_days=task.estimated_days,
        timeline_confirmed_at=task.timeline_confirmed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        priority=task.priority,
        links=task.links,
        files=file_list,
        assignees=[
            {
                "id": a.user.id,
                "username": a.user.username,
                "full_name": a.user.full_name,
                "avatar_url": a.user.avatar_url
            }
            for a in task.assignees
        ]
    )


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/me", response_model=list[TaskResponse])
def get_my_tasks(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tasks assigned to the current user"""
    tasks = db.query(TaskORM).outerjoin(TaskAssigneeORM).filter(
        (TaskORM.assigned_to == current_user.id) | (TaskAssigneeORM.user_id == current_user.id)
    ).distinct().all()
    
    return [get_task_response(task, db) for task in tasks]


@router.get("/", response_model=list[TaskResponse])
def get_all_tasks(
    current_user: FamilyMember = Depends(get_current_user), # Allow users to see all (approved) tasks
    db: Session = Depends(get_db)
):
    """Get all tasks"""
    query = db.query(TaskORM)
    if current_user.role != 'admin':
        query = query.filter(TaskORM.is_approved == True)
    
    tasks = query.all()
    return [get_task_response(task, db) for task in tasks]


@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new task (users can self-assign but need approval)"""
    is_admin = current_user.role == "admin"
    
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
        created_by=current_user.id,
        deadline=task.deadline,
        priority=task.priority or "medium",
        links=task.links,
        is_approved=is_admin # Admins are auto-approved
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Add multiple assignees if provided
    if task.assigned_user_ids:
        for user_id in task.assigned_user_ids:
            assignee = TaskAssigneeORM(task_id=db_task.id, user_id=user_id)
            db.add(assignee)
        db.commit()
    
    # Get creator info
    creator_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name
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
        deadline=db_task.deadline,
        is_approved=db_task.is_approved,
        alert_count=db_task.alert_count,
        estimated_days=db_task.estimated_days,
        timeline_confirmed_at=db_task.timeline_confirmed_at,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        priority=db_task.priority,
        links=db_task.links,
        files=[]
    )


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a task (creator or admin only, approval field admin only)"""
    db_task = db.query(TaskORM).filter(TaskORM.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    is_admin = current_user.role == "admin"
    if db_task.created_by != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
    
    # Validate assigned user if provided
    if task_update.assigned_to:
        assigned_user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task_update.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Only admin can change approval status
    if 'is_approved' in update_data and not is_admin:
        del update_data['is_approved']
        
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    # Handle multiple assignees update
    if task_update.assigned_user_ids is not None:
        # Clear existing
        db.query(TaskAssigneeORM).filter(TaskAssigneeORM.task_id == task_id).delete()
        # Add new
        for user_id in task_update.assigned_user_ids:
            assignee = TaskAssigneeORM(task_id=task_id, user_id=user_id)
            db.add(assignee)
    
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
        deadline=db_task.deadline,
        is_approved=db_task.is_approved,
        alert_count=db_task.alert_count,
        estimated_days=db_task.estimated_days,
        timeline_confirmed_at=db_task.timeline_confirmed_at,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        priority=db_task.priority,
        links=db_task.links,
        files=[] # Add files retrieval if needed
    )


    assignees: List[UserInfo] = []
    timeline_notes: Optional[str] = None
    proposed_deadline: Optional[datetime] = None
    timeline_status: Optional[str] = None


class TimelineConfirm(BaseModel):
    estimated_days: Optional[int] = None
    timeline_notes: Optional[str] = None
    proposed_deadline: Optional[datetime] = None
    action: str = "confirm" # confirm, reject


@router.post("/{task_id}/confirm-timeline", response_model=TaskResponse)
def confirm_task_timeline(
    task_id: int,
    confirm: TimelineConfirm,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User confirms how many days it will take to complete the task"""
    db_task = db.query(TaskORM).filter(TaskORM.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check if user is assigned directly or via assignees table
    is_assigned = db_task.assigned_to == current_user.id
    is_in_assignees = any(a.user_id == current_user.id for a in db_task.assignees)
    
    if not (is_assigned or is_in_assignees) and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only the assigned user can confirm the timeline")
        
    if confirm.action == "reject":
        db_task.timeline_status = "rejected"
        db_task.status = "on_hold" # Change main status to on_hold or similar
    else:
        db_task.timeline_status = "confirmed"
        db_task.status = "in_progress" 
        if confirm.estimated_days:
            db_task.estimated_days = confirm.estimated_days
            
    db_task.timeline_notes = confirm.timeline_notes
    db_task.proposed_deadline = confirm.proposed_deadline
    db_task.timeline_confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_task)
    
    # Return full response
    return get_task_response(db_task, db)


def get_task_response(task: TaskORM, db: Session) -> TaskResponse:
    creator = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.created_by).first()
    creator_info = UserInfo(
        id=creator.id,
        username=creator.username,
        full_name=creator.full_name
    ) if creator else UserInfo(id=0, username="Unknown", full_name="Unknown")
    
    assigned_user_info = None
    if task.assigned_to:
        assigned = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == task.assigned_to).first()
        if assigned:
            assigned_user_info = UserInfo(
                id=assigned.id,
                username=assigned.username,
                full_name=assigned.full_name
            )
            
    files = db.query(FileORM).filter(FileORM.task_id == task.id).all()
    file_list = [
        {
            "id": f.id,
            "filename": f.filename,
            "file_path": f.file_path,
            "file_size": f.file_size,
            "content_type": f.content_type
        }
        for f in files
    ]

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        assigned_to=task.assigned_to,
        assigned_user=assigned_user_info,
        created_by=task.created_by,
        creator=creator_info,
        deadline=task.deadline,
        is_approved=task.is_approved,
        alert_count=task.alert_count,
        estimated_days=task.estimated_days,
        timeline_confirmed_at=task.timeline_confirmed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        priority=task.priority,
        links=task.links,
        files=file_list,
        assignees=[
            {
                "id": a.user.id,
                "username": a.user.username,
                "full_name": a.user.full_name,
                "avatar_url": a.user.avatar_url
            }
            for a in task.assignees
        ],
        timeline_notes=task.timeline_notes,
        proposed_deadline=task.proposed_deadline,
        timeline_status=task.timeline_status
    )

@router.post("/{task_id}/progress", response_model=TaskUpdateResponse)
def add_task_progress(
    task_id: int,
    update: TaskUpdateCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a daily progress update for a task"""
    db_task = db.query(TaskORM).filter(TaskORM.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if db_task.assigned_to != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only assigned user can add progress")
        
    db_update = TaskUpdateORM(
        task_id=task_id,
        user_id=current_user.id,
        content=update.content
    )
    db.add(db_update)
    
    # Reset alert/activity logic if needed? 
    # For now just record.
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_update)
    
    return TaskUpdateResponse(
        id=db_update.id,
        task_id=db_update.task_id,
        user_id=db_update.user_id,
        content=db_update.content,
        created_at=db_update.created_at
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
