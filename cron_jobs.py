"""
Daily Alert System: Checks for missed task updates
Run this daily to update task alert counts and toggle red lines.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models import TaskORM, TaskUpdateORM, FamilyMemberORM

def check_task_updates():
    db = SessionLocal()
    try:
        # Get all approved, active tasks (pending or in_progress)
        tasks = db.query(TaskORM).filter(
            TaskORM.is_approved == True,
            TaskORM.status.in_(['pending', 'in_progress'])
        ).all()
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        for task in tasks:
            # Check for updates in the last 24 hours
            recent_update = db.query(TaskUpdateORM).filter(
                TaskUpdateORM.task_id == task.id,
                TaskUpdateORM.created_at >= yesterday
            ).first()
            
            if not recent_update:
                # Increment alert count if no update found
                task.alert_count += 1
                db.commit()
                print(f"Alert: Task '{task.title}' missed daily update. Alert count: {task.alert_count}")
                
        print("✓ Daily task update check completed.")
    except Exception as e:
        print(f"✗ Error in daily check: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_task_updates()
