from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Announcement, FamilyMember
from auth import get_current_admin
from datetime import datetime

router = APIRouter()

class AnnouncementCreate(BaseModel):
    title: str
    content: str

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    created_by: int
    creator: dict
    created_at: datetime

@router.get("/", response_model=list[AnnouncementResponse])
def get_all_announcements(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    announcements = db.query(Announcement).all()
    result = []
    for announcement in announcements:
        result.append({
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "created_by": announcement.created_by,
            "creator": {
                "id": announcement.creator.id,
                "username": announcement.creator.username,
                "full_name": announcement.creator.full_name
            },
            "created_at": announcement.created_at
        })
    return result

@router.post("/", response_model=AnnouncementResponse)
def create_announcement(
    announcement: AnnouncementCreate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_announcement = Announcement(
        title=announcement.title,
        content=announcement.content,
        created_by=current_admin.id
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return {
        "id": db_announcement.id,
        "title": db_announcement.title,
        "content": db_announcement.content,
        "created_by": db_announcement.created_by,
        "creator": {
            "id": db_announcement.creator.id,
            "username": db_announcement.creator.username,
            "full_name": db_announcement.creator.full_name
        },
        "created_at": db_announcement.created_at
    }

@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    update_data = announcement_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_announcement, field, value)

    db.commit()
    db.refresh(db_announcement)
    return {
        "id": db_announcement.id,
        "title": db_announcement.title,
        "content": db_announcement.content,
        "created_by": db_announcement.created_by,
        "creator": {
            "id": db_announcement.creator.id,
            "username": db_announcement.creator.username,
            "full_name": db_announcement.creator.full_name
        },
        "created_at": db_announcement.created_at
    }

@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    db.delete(db_announcement)
    db.commit()
    return {"message": "Announcement deleted successfully"}
