from fastapi import APIRouter, Depends, HTTPException, status
from database import get_supabase_client
from auth import get_current_admin
from models import FamilyMember
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class RoleRequestCreate(BaseModel):
    requested_role: str

class RoleRequestUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None

class RoleRequest(BaseModel):
    id: int
    user_id: int
    current_role: str
    requested_role: str
    status: str
    requested_at: str
    approved_at: Optional[str]
    approved_by: Optional[int]
    admin_notes: Optional[str]

class DeletedProject(BaseModel):
    id: int
    original_project_id: int
    title: str
    description: Optional[str]
    created_by: Optional[int]
    deleted_by: Optional[int]
    deleted_at: str

class AuditLog(BaseModel):
    id: int
    admin_id: int
    action_type: str
    target_type: str
    target_id: int
    old_values: Optional[dict]
    new_values: Optional[dict]
    action_timestamp: str

# Role Requests Management
@router.get("/role-requests", response_model=List[RoleRequest])
def get_role_requests(current_admin: FamilyMember = Depends(get_current_admin)):
    supabase = get_supabase_client()
    try:
        response = supabase.table('role_requests').select('*').order('requested_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching role requests: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/role-requests/{request_id}")
def update_role_request(
    request_id: str,
    update_data: RoleRequestUpdate,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    supabase = get_supabase_client()
    try:
        # Update the role request
        update_dict = {"status": update_data.status, "updated_at": datetime.utcnow().isoformat()}
        if update_data.admin_notes:
            update_dict["admin_notes"] = update_data.admin_notes

        if update_data.status == "approved":
            update_dict["approved_at"] = datetime.utcnow().isoformat()
            update_dict["approved_by"] = current_admin.id

        response = supabase.table('role_requests').update(update_dict).eq('id', request_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Role request not found")

        # If approved, update the user's role
        if update_data.status == "approved":
            request_data = response.data[0]
            supabase.table('family_members').update({
                "role": request_data['requested_role']
            }).eq('id', request_data['user_id']).execute()

        return {"message": "Role request updated successfully"}
    except Exception as e:
        print(f"Error updating role request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Deleted Projects Management
@router.get("/deleted-projects", response_model=List[DeletedProject])
def get_deleted_projects(current_admin: FamilyMember = Depends(get_current_admin)):
    supabase = get_supabase_client()
    try:
        response = supabase.table('deleted_projects').select('*').order('deleted_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching deleted projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/projects/{project_id}")
def soft_delete_project(
    project_id: str,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    supabase = get_supabase_client()
    try:
        # Get project details before deletion
        project_response = supabase.table('projects').select('*').eq('id', project_id).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        project = project_response.data[0]

        # Move to deleted_projects table
        deleted_project_data = {
            "original_project_id": project['id'],
            "title": project['title'],
            "description": project.get('description'),
            "created_by": project.get('created_by'),
            "deleted_by": current_admin.id,
            "deleted_at": datetime.utcnow().isoformat()
        }

        supabase.table('deleted_projects').insert(deleted_project_data).execute()

        # Soft delete the project
        supabase.table('projects').update({
            "deleted_at": datetime.utcnow().isoformat()
        }).eq('id', project_id).execute()

        return {"message": "Project deleted successfully"}
    except Exception as e:
        print(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/projects/{project_id}/restore")
def restore_project(
    project_id: str,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    supabase = get_supabase_client()
    try:
        # Remove soft delete
        supabase.table('projects').update({
            "deleted_at": None
        }).eq('id', project_id).execute()

        # Remove from deleted_projects table
        supabase.table('deleted_projects').delete().eq('original_project_id', project_id).execute()

        return {"message": "Project restored successfully"}
    except Exception as e:
        print(f"Error restoring project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Audit Log
@router.get("/audit-log", response_model=List[AuditLog])
def get_audit_log(
    limit: int = 100,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    supabase = get_supabase_client()
    try:
        response = supabase.table('admin_audit_log').select('*').order('action_timestamp', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching audit log: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User Role Management
@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    supabase = get_supabase_client()
    try:
        # Get current user data
        user_response = supabase.table('family_members').select('*').eq('id', user_id).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")

        old_user = user_response.data[0]

        # Update user role
        supabase.table('family_members').update({"role": new_role}).eq('id', user_id).execute()

        # Log the action
        audit_data = {
            "admin_id": current_admin.id,
            "action_type": "update_user_role",
            "target_type": "user",
            "target_id": user_id,
            "old_values": {"role": old_user['role']},
            "new_values": {"role": new_role}
        }
        supabase.table('admin_audit_log').insert(audit_data).execute()

        return {"message": "User role updated successfully"}
    except Exception as e:
        print(f"Error updating user role: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Role Definitions
@router.get("/role-definitions")
def get_role_definitions(current_admin: FamilyMember = Depends(get_current_admin)):
    supabase = get_supabase_client()
    try:
        response = supabase.table('role_definitions').select('*').eq('is_active', True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching role definitions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")