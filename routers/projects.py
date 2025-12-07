from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Project
from auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "active"

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_by: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    projects = db.query(Project).filter(Project.created_by == current_user.id).all()
    return projects

@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_project = Project(
        title=project.title,
        description=project.description,
        status=project.status,
        created_by=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.created_by == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project: ProjectCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_project = db.query(Project).filter(Project.id == project_id, Project.created_by == current_user.id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_project.title = project.title
    db_project.description = project.description
    db_project.status = project.status
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_project = db.query(Project).filter(Project.id == project_id, Project.created_by == current_user.id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted"}
