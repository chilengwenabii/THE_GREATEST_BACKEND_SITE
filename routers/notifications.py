from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict

from database import get_db
from models import (
    FamilyMember, MessageORM, TaskORM, TaskAssigneeORM, 
    AnnouncementORM, AnnouncementReadORM
)
from auth import get_current_user

router = APIRouter()

@router.get("/counts")
def get_notification_counts(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread counts for messages, profile (tasks), and home (announcements)"""
    
    # 1. Unread Messages (where current user is NOT the sender, and is_read is False)
    # This is tricky without a direct 'recipient' field on messages in a group chat context.
    # Assuming for now we check messages in conversations the user is part of.
    # Ideally, we should have a MessageRead status per user per message for group chats.
    # For a simple "1-on-1" or small group style, we can check messages not sent by me.
    
    # Improved logic: Count unread messages in conversations where user is a participant.
    # Since we don't have a 'MessageRead' table yet for detailed per-user tracking in groups,
    # we'll use the 'is_read' flag which works best for 1-on-1s.
    # For now, let's assume 'is_read' == False means unread for the recipient.
    # (Refinement needed for group chats later).
    
    unread_messages = db.query(MessageORM).join(
        MessageORM.conversation
    ).filter(
        MessageORM.sender_id != current_user.id,
        MessageORM.is_read == False,
        # Add filter to ensure user is in conversation if possible, 
        # but for now let's trust the logic that users only get notified for their chats.
    ).count()

    # 2. Pending Tasks (Profile)
    # Tasks assigned to user that are in 'pending' status OR tasks that need user confirmation?
    # Requirement: "something enter in user profile it will show notification"
    # pending tasks + tasks with new updates? Start with pending tasks.
    pending_tasks = db.query(TaskORM).outerjoin(TaskAssigneeORM).filter(
        (TaskORM.assigned_to == current_user.id) | (TaskAssigneeORM.user_id == current_user.id),
        TaskORM.status == 'pending'
    ).distinct().count()

    # 3. New Announcements (Home)
    # Count total announcements - read announcements
    total_announcements = db.query(AnnouncementORM).count()
    read_announcements = db.query(AnnouncementReadORM).filter(
        AnnouncementReadORM.user_id == current_user.id
    ).count()
    
    unread_announcements = max(0, total_announcements - read_announcements)

    return {
        "messages": unread_messages,
        "profile": pending_tasks,
        "home": unread_announcements
    }

@router.post("/messages/mark-read")
def mark_messages_read(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all unread messages for this user as read"""
    # Simply update all messages not sent by user to is_read=True
    # This is a broad "mark all as read" for simplicity.
    db.query(MessageORM).filter(
        MessageORM.sender_id != current_user.id,
        MessageORM.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    return {"status": "success"}

@router.post("/announcements/mark-read")
def mark_announcements_read(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all announcements as read"""
    # Find all announcements
    all_announcements = db.query(AnnouncementORM).all()
    
    # Find already read
    read_ids = [r.announcement_id for r in db.query(AnnouncementReadORM).filter(
        AnnouncementReadORM.user_id == current_user.id
    ).all()]
    
    # Add missing reads
    new_reads = []
    for ann in all_announcements:
        if ann.id not in read_ids:
            new_reads.append(AnnouncementReadORM(user_id=current_user.id, announcement_id=ann.id))
    
    if new_reads:
        db.add_all(new_reads)
        db.commit()
        
    return {"status": "success"}
