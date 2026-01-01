"""
Search Router: Global search across users, projects, and conversations
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List, Optional

from database import get_db
from models import FamilyMemberORM, ProjectORM, ConversationORM, ConversationParticipantORM
from auth import get_current_user, FamilyMember

router = APIRouter()


# =============================================================================
# Response Schemas
# =============================================================================

class UserSearchResult(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    type: str = "user"

    class Config:
        from_attributes = True


class ProjectSearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    type: str = "project"

    class Config:
        from_attributes = True


class ConversationSearchResult(BaseModel):
    id: int
    title: Optional[str] = None
    participant_names: List[str]
    type: str = "conversation"

    class Config:
        from_attributes = True


class SearchResults(BaseModel):
    users: List[UserSearchResult]
    projects: List[ProjectSearchResult]
    conversations: List[ConversationSearchResult]


# =============================================================================
# Search Endpoint
# =============================================================================

@router.get("/", response_model=SearchResults)
def global_search(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Global search across users, projects, and conversations.
    Returns matching results from all categories.
    """
    search_term = f"%{q.lower()}%"
    
    # Search users
    users = db.query(FamilyMemberORM).filter(
        FamilyMemberORM.is_active == True,
        or_(
            FamilyMemberORM.username.ilike(search_term),
            FamilyMemberORM.full_name.ilike(search_term),
            FamilyMemberORM.email.ilike(search_term)
        )
    ).limit(10).all()
    
    user_results = [
        UserSearchResult(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            role=u.role
        ) for u in users
    ]
    
    # Search projects (only non-deleted)
    projects = db.query(ProjectORM).filter(
        ProjectORM.deleted_at == None,
        or_(
            ProjectORM.title.ilike(search_term),
            ProjectORM.description.ilike(search_term)
        )
    ).limit(10).all()
    
    project_results = [
        ProjectSearchResult(
            id=p.id,
            title=p.title,
            description=p.description[:100] if p.description else None,
            status=p.status or "pending"
        ) for p in projects
    ]
    
    # Search conversations user is part of
    user_conv_ids = [
        p.conversation_id for p in 
        db.query(ConversationParticipantORM).filter(
            ConversationParticipantORM.user_id == current_user.id
        ).all()
    ]
    
    conversations = []
    if user_conv_ids:
        convs = db.query(ConversationORM).filter(
            ConversationORM.id.in_(user_conv_ids),
            or_(
                ConversationORM.title.ilike(search_term),
                ConversationORM.title == None  # Also include untitled conversations
            )
        ).limit(10).all()
        
        for conv in convs:
            # Get participant names
            participant_names = []
            for p in conv.participants:
                user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == p.user_id).first()
                if user and user.id != current_user.id:
                    participant_names.append(user.full_name)
            
            # For untitled convs, check if participant name matches search
            if conv.title:
                if q.lower() in conv.title.lower():
                    conversations.append(ConversationSearchResult(
                        id=conv.id,
                        title=conv.title,
                        participant_names=participant_names
                    ))
            else:
                # Check if any participant name matches
                if any(q.lower() in name.lower() for name in participant_names):
                    conversations.append(ConversationSearchResult(
                        id=conv.id,
                        title=None,
                        participant_names=participant_names
                    ))
    
    return SearchResults(
        users=user_results,
        projects=project_results,
        conversations=conversations
    )
