from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from database import get_db
from models import FamilyMemberORM, ProjectORM, TaskORM, AdminAuditLogORM, TaskUpdateORM
from auth import get_current_user_orm
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/stats")
def get_general_stats(db: Session = Depends(get_db), current_user: FamilyMemberORM = Depends(get_current_user_orm)):
    """Get high-level dashboard metrics"""
    
    # 1. Total Active Operatives (Users)
    total_users = db.query(FamilyMemberORM).filter(FamilyMemberORM.is_active == True).count()
    online_users = db.query(FamilyMemberORM).filter(FamilyMemberORM.is_online == True).count()
    
    # 2. Task Velocity (Tasks completed in last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    completed_recent = db.query(TaskORM).filter(
        and_(TaskORM.status == 'completed', TaskORM.updated_at >= seven_days_ago)
    ).count()
    
    # 3. Global Compliance (Percentage of on-time tasks)
    total_completed_tasks = db.query(TaskORM).filter(TaskORM.status == 'completed').count()
    # Assuming 'deadline' exists and we check if updated_at <= deadline
    # This is an approximation for now
    on_time_tasks = db.query(TaskORM).filter(
        and_(
            TaskORM.status == 'completed', 
            TaskORM.updated_at <= TaskORM.deadline
        )
    ).count() if total_completed_tasks > 0 else 0
    
    compliance_rate = (on_time_tasks / total_completed_tasks * 100) if total_completed_tasks > 0 else 100

    # 4. Avg Completion Time (Simple placeholder logic or complex calc)
    # For now returning a mock or simple calc
    
    return {
        "active_operatives": total_users,
        "online_operatives": online_users,
        "task_velocity": completed_recent,
        "global_compliance": round(compliance_rate, 1)
    }

@router.get("/projects")
def get_project_analytics(db: Session = Depends(get_db), current_user: FamilyMemberORM = Depends(get_current_user_orm)):
    """Get active project status and progress"""
    projects = db.query(ProjectORM).filter(ProjectORM.deleted_at == None).all()
    
    return [
        {
            "id": p.id,
            "name": p.title,
            "progress": p.progress,
            "status": p.status,
            "priority": p.priority
        }
        for p in projects
    ]

@router.get("/performance")
def get_user_performance(db: Session = Depends(get_db), current_user: FamilyMemberORM = Depends(get_current_user_orm)):
    """Get top performers based on completed tasks"""
    # Simply counting completed tasks as "points" for now
    top_users = db.query(
        FamilyMemberORM.id,
        FamilyMemberORM.full_name,
        FamilyMemberORM.role,
        FamilyMemberORM.avatar_url,
        func.count(TaskORM.id).label("tasks_completed")
    ).join(TaskORM, FamilyMemberORM.id == TaskORM.assigned_to)\
     .filter(TaskORM.status == 'completed')\
     .group_by(FamilyMemberORM.id)\
     .order_by(desc("tasks_completed"))\
     .limit(5)\
     .all()

    return [
        {
            "id": u.id,
            "name": u.full_name,
            "role": u.role,
            "points": u.tasks_completed * 100, # Arbitrary points logic
            "avatar": u.full_name[0] if u.full_name else "?"
        }
        for u in top_users
    ]

@router.get("/activity")
def get_activity_feed(db: Session = Depends(get_db), current_user: FamilyMemberORM = Depends(get_current_user_orm)):
    """Get recent system activity from audit logs or task updates"""
    # Creating a mixed feed from task updates and new tasks
    
    recent_tasks = db.query(TaskORM).order_by(TaskORM.created_at.desc()).limit(10).all()
    
    # We ideally need a unified Activity table, but we will mock structure from Tasks for now
    feed = []
    
    for t in recent_tasks:
        feed.append({
            "id": t.id,
            "action": "New_Objective",
            "user": t.creator.full_name if t.creator else "System",
            "time": t.created_at.strftime("%H:%M") if t.created_at else "Now"
        })
        
    return feed
