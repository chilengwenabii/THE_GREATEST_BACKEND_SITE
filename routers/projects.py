"""
Projects Router: Project CRUD endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import FamilyMemberORM, FamilyMember, ProjectORM
from auth import get_current_user

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "active"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    submission_link: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=list[ProjectResponse])
def get_projects(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for current user"""
    projects = db.query(ProjectORM).filter(
        ProjectORM.created_by == current_user.id,
        ProjectORM.deleted_at == None
    ).all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    db_project = ProjectORM(
        title=project.title,
        description=project.description,
        status=project.status,
        created_by=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return ProjectResponse.model_validate(db_project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project"""
    project = db.query(ProjectORM).filter(
        ProjectORM.id == project_id,
        ProjectORM.created_by == current_user.id,
        ProjectORM.deleted_at == None
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(ProjectORM).filter(
        ProjectORM.id == project_id,
        ProjectORM.created_by == current_user.id,
        ProjectORM.deleted_at == None
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project (soft delete)"""
    project = db.query(ProjectORM).filter(
        ProjectORM.id == project_id,
        ProjectORM.created_by == current_user.id,
        ProjectORM.deleted_at == None
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Soft delete
    project.deleted_at = datetime.utcnow()
    db.commit()
    
@router.post("/{project_id}/submit", response_model=ProjectResponse)
def submit_project(
    project_id: int,
    submission: dict,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a project completion link"""
    project = db.query(ProjectORM).filter(
        ProjectORM.id == project_id,
        ProjectORM.created_by == current_user.id,
        ProjectORM.deleted_at == None
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    link = submission.get("link")
    if not link:
        raise HTTPException(status_code=400, detail="Submission link is required")
    
    project.submission_link = link
    project.status = "completed"  # Automatically mark as completed on submission
    project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse.model_validate(project)
