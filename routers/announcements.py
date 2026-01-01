"""
Announcements Router: Announcement CRUD endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import FamilyMemberORM, FamilyMember, AnnouncementORM
from auth import get_current_admin

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class AnnouncementCreate(BaseModel):
    title: str
    content: str


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class CreatorInfo(BaseModel):
    id: int
    username: str
    full_name: str


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    created_by: int
    creator: CreatorInfo
    created_at: datetime


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=list[AnnouncementResponse])
def get_all_announcements(
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all announcements (admin only)"""
    announcements = db.query(AnnouncementORM).order_by(AnnouncementORM.created_at.desc()).all()
    result = []
    
    for announcement in announcements:
        creator = db.query(FamilyMemberORM).filter(
            FamilyMemberORM.id == announcement.created_by
        ).first()
        
        creator_info = CreatorInfo(
            id=creator.id,
            username=creator.username,
            full_name=creator.full_name
        ) if creator else CreatorInfo(id=0, username="Unknown", full_name="Unknown")
        
        result.append(AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            created_by=announcement.created_by,
            creator=creator_info,
            created_at=announcement.created_at
        ))
    
    return result


@router.post("/", response_model=AnnouncementResponse)
def create_announcement(
    announcement: AnnouncementCreate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new announcement (admin only)"""
    db_announcement = AnnouncementORM(
        title=announcement.title,
        content=announcement.content,
        created_by=current_admin.id
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    
    creator = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == current_admin.id).first()
    creator_info = CreatorInfo(
        id=creator.id,
        username=creator.username,
        full_name=creator.full_name
    )
    
    return AnnouncementResponse(
        id=db_announcement.id,
        title=db_announcement.title,
        content=db_announcement.content,
        created_by=db_announcement.created_by,
        creator=creator_info,
        created_at=db_announcement.created_at
    )


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an announcement (admin only)"""
    db_announcement = db.query(AnnouncementORM).filter(
        AnnouncementORM.id == announcement_id
    ).first()
    
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    update_data = announcement_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_announcement, field, value)
    
    db.commit()
    db.refresh(db_announcement)
    
    creator = db.query(FamilyMemberORM).filter(
        FamilyMemberORM.id == db_announcement.created_by
    ).first()
    creator_info = CreatorInfo(
        id=creator.id,
        username=creator.username,
        full_name=creator.full_name
    ) if creator else CreatorInfo(id=0, username="Unknown", full_name="Unknown")
    
    return AnnouncementResponse(
        id=db_announcement.id,
        title=db_announcement.title,
        content=db_announcement.content,
        created_by=db_announcement.created_by,
        creator=creator_info,
        created_at=db_announcement.created_at
    )


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    current_admin: FamilyMember = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete an announcement (admin only)"""
    db_announcement = db.query(AnnouncementORM).filter(
        AnnouncementORM.id == announcement_id
    ).first()
    
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    db.delete(db_announcement)
    db.commit()
    
    return {"message": "Announcement deleted successfully"}
