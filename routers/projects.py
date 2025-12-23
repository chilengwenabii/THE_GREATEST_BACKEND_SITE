from fastapi import APIRouter, Depends, HTTPException, status
from database import get_supabase_client
from auth import get_current_user
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter()

class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "active"

class ProjectResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    created_by: str
    created_at: str
    updated_at: str

@router.get("/", response_model=List[ProjectResponse])
def get_projects(current_user = Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        response = supabase.table('projects').select('*').eq('created_by', current_user.id).execute()
        return [ProjectResponse(**project) for project in response.data]
    except Exception as e:
        print(f"Error getting projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, current_user = Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        project_data = {
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "created_by": current_user.id
        }

        response = supabase.table('projects').insert(project_data).execute()
        return ProjectResponse(**response.data[0])
    except Exception as e:
        print(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, current_user = Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        response = supabase.table('projects').select('*').eq('id', project_id).eq('created_by', current_user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project: ProjectCreate, current_user = Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        # Check if project exists and belongs to user
        response = supabase.table('projects').select('*').eq('id', project_id).eq('created_by', current_user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        update_data = {
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "updated_at": datetime.utcnow().isoformat()
        }

        supabase.table('projects').update(update_data).eq('id', project_id).execute()

        # Return updated project data
        response = supabase.table('projects').select('*').eq('id', project_id).execute()
        return ProjectResponse(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{project_id}")
def delete_project(project_id: str, current_user = Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        # Check if project exists and belongs to user
        response = supabase.table('projects').select('*').eq('id', project_id).eq('created_by', current_user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        supabase.table('projects').delete().eq('id', project_id).execute()
        return {"message": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
