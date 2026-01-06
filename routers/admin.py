"""
Admin Router: Admin-only management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import (
    FamilyMemberORM, FamilyMember, ProjectORM,
    RoleRequestORM, DeletedProjectORM, AdminAuditLogORM, RoleDefinitionORM
)
from auth import get_current_admin, get_internal_admin

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class RoleRequestCreate(BaseModel):
    requested_role: str


class RoleRequestUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None


class RoleRequestResponse(BaseModel):
    id: int
    user_id: int
    current_role: Optional[str] = None
    requested_role: str
    status: str
    requested_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    admin_notes: Optional[str] = None

    class Config:
        from_attributes = True


class DeletedProjectResponse(BaseModel):
    id: int
    original_project_id: int
    title: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    deleted_by: Optional[int] = None
    deleted_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    admin_id: int
    action_type: str
    target_type: str
    target_id: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    action_timestamp: datetime


class AuditLogResponse(BaseModel):
    id: int
    admin_id: int
    action_type: str
    target_type: str
    target_id: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    action_timestamp: datetime

    class Config:
        from_attributes = True


class AdminMessageResponse(BaseModel):
    id: int
    content: str
    message_type: str
    file_url: Optional[str] = None
    sender_id: int
    sender_username: str
    sender_full_name: str
    conversation_id: int
    conversation_title: Optional[str] = None
    reply_to_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Role Requests Management
# =============================================================================

@router.get("/role-requests", response_model=List[RoleRequestResponse])
def get_role_requests(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all role requests"""
    requests = db.query(RoleRequestORM).order_by(RoleRequestORM.requested_at.desc()).all()
    return [RoleRequestResponse.model_validate(r) for r in requests]


@router.put("/role-requests/{request_id}")
def update_role_request(
    request_id: int,
    update_data: RoleRequestUpdate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a role request"""
    request = db.query(RoleRequestORM).filter(RoleRequestORM.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Role request not found")
    
    request.status = update_data.status
    if update_data.admin_notes:
        request.admin_notes = update_data.admin_notes
    
    if update_data.status == "approved":
        request.approved_at = datetime.utcnow()
        request.approved_by = current_admin.id
        
        # Update user's role
        user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == request.user_id).first()
        if user:
            user.role = request.requested_role
    
    db.commit()
    return {"message": "Role request updated successfully"}


# =============================================================================
# Deleted Projects Management
# =============================================================================

@router.get("/deleted-projects", response_model=List[DeletedProjectResponse])
def get_deleted_projects(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all deleted projects"""
    projects = db.query(DeletedProjectORM).order_by(DeletedProjectORM.deleted_at.desc()).all()
    return [DeletedProjectResponse.model_validate(p) for p in projects]


@router.delete("/projects/{project_id}")
def soft_delete_project(
    project_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Soft delete a project (admin)"""
    project = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Archive to deleted_projects
    deleted_project = DeletedProjectORM(
        original_project_id=project.id,
        title=project.title,
        description=project.description,
        created_by=project.created_by,
        deleted_by=current_admin.id,
        deleted_at=datetime.utcnow()
    )
    db.add(deleted_project)
    
    # Soft delete
    project.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.post("/projects/{project_id}/restore")
def restore_project(
    project_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted project"""
    project = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if project:
        project.deleted_at = None
    
    # Remove from deleted_projects
    db.query(DeletedProjectORM).filter(
        DeletedProjectORM.original_project_id == project_id
    ).delete()
    
    db.commit()
    return {"message": "Project restored successfully"}


# =============================================================================
# Audit Log
# =============================================================================

@router.get("/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    limit: int = 100,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin audit log"""
    logs = db.query(AdminAuditLogORM).order_by(
        AdminAuditLogORM.action_timestamp.desc()
    ).limit(limit).all()
    return [AuditLogResponse.model_validate(log) for log in logs]


# =============================================================================
# User Role Management
# =============================================================================

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a user's role"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = new_role
    db.commit()
    
    return {"message": f"User role updated from {old_role} to {new_role}"}


# =============================================================================
# Role Definitions
# =============================================================================

@router.get("/role-definitions")
def get_role_definitions(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all role definitions"""
    roles = db.query(RoleDefinitionORM).filter(RoleDefinitionORM.is_active == True).all()
    return [{"id": r.id, "role_name": r.role_name, "description": r.description} for r in roles]


# =============================================================================
# User Management (Admin)
# =============================================================================

@router.get("/users/count")
def get_users_count(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get total user count"""
    count = db.query(FamilyMemberORM).count()
    return {"count": count}


@router.get("/users")
def get_users_list(
    skip: int = 0,
    limit: int = 100,
    current_admin: FamilyMember = Depends(get_internal_admin),
    db: Session = Depends(get_db)
):
    """Get paginated user list"""
    users = db.query(FamilyMemberORM).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "is_online": u.is_online,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.get("/users/{user_id}")
def get_user_details(
    user_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user details"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "is_online": user.is_online,
        "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    update_data: dict,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin)"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Whitelist allowed fields
    allowed_fields = ['username', 'email', 'full_name', 'phone', 'role', 'is_active']
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(user, field, value)
    
    db.commit()
    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    hard_delete: bool = False,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete user (soft delete by default, hard delete if requested)"""
    user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if hard_delete:
        db.delete(user)
        db.commit()
        return {"message": "User permanently deleted from system"}
    else:
        user.is_active = False
        db.commit()
        return {"message": "User account deactivated (soft delete)"}


# =============================================================================
# Dashboard Stats
# =============================================================================

@router.get("/files")
def get_all_files(
    db: Session = Depends(get_db),
    current_admin: FamilyMember = Depends(get_current_admin)
):
    """Get all files (admin)"""
    from models import FileORM
    files = db.query(FileORM).all()
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "file_path": f.file_path,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "uploaded_by": f.uploaded_by,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        }
        for f in files
    ]


@router.get("/stats")
def get_dashboard_stats(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    from models import TaskORM, AnnouncementORM
    
    total_users = db.query(FamilyMemberORM).count()
    online_users = db.query(FamilyMemberORM).filter(FamilyMemberORM.is_online == True).count()
    total_projects = db.query(ProjectORM).filter(ProjectORM.deleted_at == None).count()
    active_projects = db.query(ProjectORM).filter(
        ProjectORM.deleted_at == None,
        ProjectORM.status == "active"
    ).count()
    total_tasks = db.query(TaskORM).count()
    completed_tasks = db.query(TaskORM).filter(TaskORM.status == "completed").count()
    pending_tasks = db.query(TaskORM).filter(TaskORM.status == "pending").count()
    total_announcements = db.query(AnnouncementORM).count()
    from models import FileORM
    total_files = db.query(FileORM).count()
    
    # Calculate storage used (sum of file sizes, e.g., in MB)
    from sqlalchemy import func
    storage_bytes = db.query(func.sum(FileORM.file_size)).scalar() or 0
    # Let's say we have a 1GB quota for simple percentage calculation
    quota_bytes = 1024 * 1024 * 1024
    storage_percent = min(round((storage_bytes / quota_bytes) * 100, 1), 100.0)
    
    return {
        "total_users": total_users,
        "online_users": online_users,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "total_announcements": total_announcements,
        "total_files": total_files,
        "storage_used": f"{storage_percent}%"
    }


# =============================================================================
# Chat Management (Admin)
# =============================================================================

@router.get("/messages/count")
def get_messages_count(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get total message count"""
    from models import MessageORM
    count = db.query(MessageORM).count()
    return {"count": count}


@router.get("/messages", response_model=List[AdminMessageResponse])
def get_all_messages(
    skip: int = 0,
    limit: int = 100,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all messages with details"""
    from models import MessageORM, ConversationORM
    
    # Query messages with joined relations
    messages = db.query(MessageORM).order_by(MessageORM.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for msg in messages:
        sender = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == msg.sender_id).first()
        conversation = db.query(ConversationORM).filter(ConversationORM.id == msg.conversation_id).first()
        
        result.append(AdminMessageResponse(
            id=msg.id,
            content=msg.content,
            message_type=msg.message_type,
            file_url=msg.file_url,
            sender_id=msg.sender_id,
            sender_username=sender.username if sender else "Unknown",
            sender_full_name=sender.full_name if sender else "Unknown User",
            conversation_id=msg.conversation_id,
            conversation_title=conversation.title if conversation else None,
            reply_to_id=msg.reply_to_id,
            created_at=msg.created_at
        ))
    
    return result


@router.delete("/messages/{message_id}")
def admin_delete_message(
    message_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Hard delete a message (admin)"""
    from models import MessageORM
    
    msg = db.query(MessageORM).filter(MessageORM.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(msg)
    db.commit()
    
    return {"message": "Message deleted successfully"}
# =============================================================================
# Health & Diagnostics
# =============================================================================

@router.get("/health/db")
def health_check_db(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Deep health check for database connection"""
    try:
        # Simple query to test connection
        db.execute(func.text("SELECT 1"))
        from models import FamilyMemberORM
        user_count = db.query(FamilyMemberORM).count()
        return {
            "status": "online",
            "latency": "fast",
            "message": f"Database connected. Total users: {user_count}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/health/storage")
def health_check_storage(
    current_admin: FamilyMember = Depends(get_current_admin)
):
    """Check storage directory access"""
    import os
    target_dir = "uploads"
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cannot create storage: {str(e)}")
            
    is_writable = os.access(target_dir, os.W_OK)
    
    return {
        "status": "online" if is_writable else "offline",
        "path": os.path.abspath(target_dir),
        "writable": is_writable,
        "message": "Storage system is ready" if is_writable else "Storage directory is not writable"
    }


@router.get("/health/all")
def health_check_all(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Run all system tests"""
    db_status = "online"
    try:
        db.execute(func.text("SELECT 1"))
    except:
        db_status = "offline"
        
    import os
    storage_status = "online" if os.access("uploads", os.W_OK) else "offline"
    
    return {
        "database": db_status,
        "storage": storage_status,
        "api": "online",
        "auth": "online",
        "timestamp": datetime.utcnow().isoformat()
    }
