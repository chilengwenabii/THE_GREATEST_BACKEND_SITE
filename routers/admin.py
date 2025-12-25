from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db_connection
from auth import get_current_admin, get_internal_admin
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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM role_requests ORDER BY requested_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching role requests: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.put("/role-requests/{request_id}")
def update_role_request(
    request_id: str,
    update_data: RoleRequestUpdate,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update the role request
        update_dict = {"status": update_data.status, "updated_at": datetime.utcnow().isoformat()}
        if update_data.admin_notes:
            update_dict["admin_notes"] = update_data.admin_notes

        if update_data.status == "approved":
            update_dict["approved_at"] = datetime.utcnow().isoformat()
            update_dict["approved_by"] = current_admin.id

        # Build update query
        set_parts = []
        values = []
        for key, value in update_dict.items():
            set_parts.append(f"{key} = ?")
            values.append(value)
        values.append(request_id)

        cursor.execute(f"UPDATE role_requests SET {', '.join(set_parts)} WHERE id = ?", values)

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Role request not found")

        # If approved, update the user's role
        if update_data.status == "approved":
            cursor.execute("SELECT user_id, requested_role FROM role_requests WHERE id = ?", (request_id,))
            request_data = cursor.fetchone()
            if request_data:
                cursor.execute("UPDATE family_members SET role = ? WHERE id = ?", 
                             (request_data['requested_role'], request_data['user_id']))

        conn.commit()
        return {"message": "Role request updated successfully"}
    except Exception as e:
        print(f"Error updating role request: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# Deleted Projects Management
@router.get("/deleted-projects", response_model=List[DeletedProject])
def get_deleted_projects(current_admin: FamilyMember = Depends(get_current_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM deleted_projects ORDER BY deleted_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching deleted projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.delete("/projects/{project_id}")
def soft_delete_project(
    project_id: str,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get project details before deletion
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project_row = cursor.fetchone()
        if not project_row:
            raise HTTPException(status_code=404, detail="Project not found")

        project = dict(project_row)

        # Move to deleted_projects table
        deleted_project_data = {
            "original_project_id": project['id'],
            "title": project['title'],
            "description": project.get('description'),
            "created_by": project.get('created_by'),
            "deleted_by": current_admin.id,
            "deleted_at": datetime.utcnow().isoformat()
        }

        cursor.execute("""
            INSERT INTO deleted_projects (original_project_id, title, description, created_by, deleted_by, deleted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (deleted_project_data['original_project_id'], deleted_project_data['title'], 
              deleted_project_data['description'], deleted_project_data['created_by'], 
              deleted_project_data['deleted_by'], deleted_project_data['deleted_at']))

        # Soft delete the project
        cursor.execute("UPDATE projects SET deleted_at = ? WHERE id = ?", 
                      (datetime.utcnow().isoformat(), project_id))

        conn.commit()
        return {"message": "Project deleted successfully"}
    except Exception as e:
        print(f"Error deleting project: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.post("/projects/{project_id}/restore")
def restore_project(
    project_id: str,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Remove soft delete
        cursor.execute("UPDATE projects SET deleted_at = NULL WHERE id = ?", (project_id,))

        # Remove from deleted_projects table
        cursor.execute("DELETE FROM deleted_projects WHERE original_project_id = ?", (project_id,))

        conn.commit()
        return {"message": "Project restored successfully"}
    except Exception as e:
        print(f"Error restoring project: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# Audit Log
@router.get("/audit-log", response_model=List[AuditLog])
def get_audit_log(
    limit: int = 100,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM admin_audit_log ORDER BY action_timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching audit log: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# User Role Management
@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    new_role: str,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get current user data
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (user_id,))
        old_user_row = cursor.fetchone()
        if not old_user_row:
            raise HTTPException(status_code=404, detail="User not found")

        old_user = dict(old_user_row)

        # Update user role
        cursor.execute("UPDATE family_members SET role = ? WHERE id = ?", (new_role, user_id))

        # Log the action (simplified)
        print(f"Admin {current_admin.id} updated role for user {user_id} from {old_user['role']} to {new_role}")

        conn.commit()
        return {"message": "User role updated successfully"}
    except Exception as e:
        print(f"Error updating user role: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# Role Definitions
@router.get("/role-definitions")
def get_role_definitions(current_admin: FamilyMember = Depends(get_current_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM role_definitions WHERE is_active = 1")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching role definitions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# User Management
@router.get("/users/count")
def get_users_count(current_admin: FamilyMember = Depends(get_current_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM family_members")
        count = cursor.fetchone()[0]
        return {"count": count}
    except Exception as e:
        print(f"Error fetching users count: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.get("/users")
def get_users_list(
    skip: int = 0,
    limit: int = 100,
    current_admin: FamilyMember = Depends(get_internal_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM family_members LIMIT ? OFFSET ?", (limit, skip))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching users list: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.get("/users/{user_id}")
def get_user_details(
    user_id: str,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)
    except Exception as e:
        print(f"Error fetching user details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    update_data: dict,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get current user data for audit
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (user_id,))
        old_user_row = cursor.fetchone()
        if not old_user_row:
            raise HTTPException(status_code=404, detail="User not found")

        old_user = dict(old_user_row)

        # Update user
        update_data["updated_at"] = datetime.utcnow().isoformat()
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = ?")
            values.append(value)
        values.append(user_id)

        cursor.execute(f"UPDATE family_members SET {', '.join(set_parts)} WHERE id = ?", values)

        # Log the action (simplified)
        print(f"Admin {current_admin.id} updated user {user_id}")

        conn.commit()
        return {"message": "User updated successfully"}
    except Exception as e:
        print(f"Error updating user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_admin: FamilyMember = Depends(get_current_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get user data for audit
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        user = dict(user_row)

        # Soft delete by setting is_active to False
        cursor.execute("UPDATE family_members SET is_active = 0 WHERE id = ?", (user_id,))

        # Log the action (simplified)
        print(f"Admin {current_admin.id} deleted user {user_id}")

        conn.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()
