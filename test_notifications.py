from sqlalchemy.orm import Session
from database import SessionLocal
from models import MessageORM, TaskORM, TaskAssigneeORM, AnnouncementORM, AnnouncementReadORM, FamilyMemberORM
from sqlalchemy import or_

def test_queries():
    db = SessionLocal()
    try:
        # Mock current user (Admin or first user)
        current_user = db.query(FamilyMemberORM).first()
        if not current_user:
            print("No users found.")
            return

        print(f"Testing queries for user: {current_user.username} (ID: {current_user.id})")

        # 1. Unread Messages
        print("Testing Message/Conversation query...")
        try:
            unread_messages = db.query(MessageORM).join(
                MessageORM.conversation
            ).filter(
                MessageORM.sender_id != current_user.id,
                MessageORM.is_read == False,
            ).count()
            print(f"Unread Messages: {unread_messages}")
        except Exception as e:
            print(f"Message Query Failed: {e}")

        # 2. Pending Tasks
        print("Testing Task/Assignee query...")
        try:
            pending_tasks = db.query(TaskORM).outerjoin(TaskAssigneeORM).filter(
                or_(TaskORM.assigned_to == current_user.id, TaskAssigneeORM.user_id == current_user.id),
                TaskORM.status == 'pending'
            ).distinct().count()
            print(f"Pending Tasks: {pending_tasks}")
        except Exception as e:
            print(f"Task Query Failed: {e}")

        # 3. Announcements
        print("Testing Announcement query...")
        try:
            total_announcements = db.query(AnnouncementORM).count()
            read_announcements = db.query(AnnouncementReadORM).filter(
                AnnouncementReadORM.user_id == current_user.id
            ).count()
            print(f"Total: {total_announcements}, Read: {read_announcements}")
        except Exception as e:
            print(f"Announcement Query Failed: {e}")

    except Exception as e:
        print(f"General Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_queries()
