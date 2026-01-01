"""
Chat Router: Conversations and Messages endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import (
    FamilyMemberORM, FamilyMember, 
    ConversationORM, ConversationParticipantORM, MessageORM
)
from auth import get_current_user

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    participant_ids: List[int]


class MessageCreate(BaseModel):
    content: str
    conversation_id: int
    message_type: str = "text"
    file_url: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    content: str
    message_type: str
    file_url: Optional[str] = None
    sender_id: int
    sender_username: str
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ParticipantInfo(BaseModel):
    id: int
    username: str
    full_name: str


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    participants: List[ParticipantInfo]
    messages: List[MessageResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    conv: ConversationCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    # Create conversation
    db_conv = ConversationORM(
        title=conv.title,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    
    # Add current user as participant
    current_participant = ConversationParticipantORM(
        conversation_id=db_conv.id,
        user_id=current_user.id
    )
    db.add(current_participant)
    
    # Add other participants
    participants = []
    for user_id in conv.participant_ids:
        user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == user_id).first()
        if user:
            participant = ConversationParticipantORM(
                conversation_id=db_conv.id,
                user_id=user_id
            )
            db.add(participant)
            participants.append(ParticipantInfo(
                id=user.id,
                username=user.username,
                full_name=user.full_name
            ))
    
    # Add current user to participants list
    current_user_orm = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == current_user.id).first()
    if current_user_orm:
        participants.append(ParticipantInfo(
            id=current_user_orm.id,
            username=current_user_orm.username,
            full_name=current_user_orm.full_name
        ))
    
    db.commit()
    
    return ConversationResponse(
        id=db_conv.id,
        title=db_conv.title,
        participants=participants,
        messages=[],
        created_at=db_conv.created_at,
        updated_at=db_conv.updated_at
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all conversations for current user"""
    # Get conversation IDs where user is a participant
    participant_records = db.query(ConversationParticipantORM).filter(
        ConversationParticipantORM.user_id == current_user.id
    ).all()
    
    conv_ids = [p.conversation_id for p in participant_records]
    
    if not conv_ids:
        return []
    
    conversations = db.query(ConversationORM).filter(
        ConversationORM.id.in_(conv_ids)
    ).all()
    
    result = []
    for conv in conversations:
        # Get participants
        participants = []
        for p in conv.participants:
            user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == p.user_id).first()
            if user:
                participants.append(ParticipantInfo(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name
                ))
        
        # Get messages
        messages = []
        for msg in conv.messages:
            sender = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == msg.sender_id).first()
            messages.append(MessageResponse(
                id=msg.id,
                content=msg.content,
                message_type=msg.message_type,
                file_url=msg.file_url,
                sender_id=msg.sender_id,
                sender_username=sender.username if sender else "Unknown",
                conversation_id=msg.conversation_id,
                created_at=msg.created_at
            ))
        
        result.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            participants=participants,
            messages=messages,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        ))
    
    return result


@router.post("/messages", response_model=MessageResponse)
def send_message(
    msg: MessageCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a conversation"""
    # Check if conversation exists
    conv = db.query(ConversationORM).filter(ConversationORM.id == msg.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if user is a participant
    participant = db.query(ConversationParticipantORM).filter(
        ConversationParticipantORM.conversation_id == msg.conversation_id,
        ConversationParticipantORM.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not authorized to send message in this conversation")
    
    # Create message
    db_msg = MessageORM(
        content=msg.content,
        message_type=msg.message_type,
        file_url=msg.file_url,
        sender_id=current_user.id,
        conversation_id=msg.conversation_id,
        created_at=datetime.utcnow()
    )
    db.add(db_msg)
    
    # Update conversation timestamp
    conv.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_msg)
    
    # Get sender username
    sender = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == current_user.id).first()
    
    return MessageResponse(
        id=db_msg.id,
        content=db_msg.content,
        message_type=db_msg.message_type,
        file_url=db_msg.file_url,
        sender_id=db_msg.sender_id,
        sender_username=sender.username if sender else "Unknown",
        conversation_id=db_msg.conversation_id,
        created_at=db_msg.created_at
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a conversation"""
    # Check if conversation exists
    conv = db.query(ConversationORM).filter(ConversationORM.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if user is a participant
    participant = db.query(ConversationParticipantORM).filter(
        ConversationParticipantORM.conversation_id == conversation_id,
        ConversationParticipantORM.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not authorized to view this conversation")
    
    # Get messages
    messages = db.query(MessageORM).filter(
        MessageORM.conversation_id == conversation_id
    ).order_by(MessageORM.created_at).all()
    
    result = []
    for msg in messages:
        sender = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == msg.sender_id).first()
        result.append(MessageResponse(
            id=msg.id,
            content=msg.content,
            message_type=msg.message_type,
            file_url=msg.file_url,
            sender_id=msg.sender_id,
            sender_username=sender.username if sender else "Unknown",
            conversation_id=msg.conversation_id,
            created_at=msg.created_at
        ))
    
    return result
@router.get("/team-conversation", response_model=ConversationResponse)
def get_or_create_team_conversation(
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get or create the global team conversation that includes ALL users.
    """
    team_title = "THE GREATEST TEAM"
    
    # Try to find existing team conversation by title
    team_conv = db.query(ConversationORM).filter(
        ConversationORM.title == team_title
    ).first()
    
    if not team_conv:
        # Create it if it doesn't exist
        team_conv = ConversationORM(
            title=team_title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(team_conv)
        db.commit()
        db.refresh(team_conv)
    
    # Ensure current user is a participant
    participant = db.query(ConversationParticipantORM).filter(
        ConversationParticipantORM.conversation_id == team_conv.id,
        ConversationParticipantORM.user_id == current_user.id
    ).first()
    
    if not participant:
        participant = ConversationParticipantORM(
            conversation_id=team_conv.id,
            user_id=current_user.id
        )
        db.add(participant)
        db.commit()
    
    # Ensure all other active users are also participants (sync logic)
    # This keeps the team chat populated automatically
    all_users = db.query(FamilyMemberORM).filter(FamilyMemberORM.is_active == True).all()
    existing_participant_ids = db.query(ConversationParticipantORM.user_id).filter(
        ConversationParticipantORM.conversation_id == team_conv.id
    ).all()
    existing_participant_ids = [p[0] for p in existing_participant_ids]
    
    for u in all_users:
        if u.id not in existing_participant_ids:
            new_p = ConversationParticipantORM(
                conversation_id=team_conv.id,
                user_id=u.id
            )
            db.add(new_p)
    
    db.commit()
    db.refresh(team_conv)
    
    # Construct response
    participants = []
    for p in team_conv.participants:
        user = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == p.user_id).first()
        if user:
            participants.append(ParticipantInfo(
                id=user.id,
                username=user.username,
                full_name=user.full_name
            ))
            
    messages = []
    for msg in team_conv.messages:
        sender = db.query(FamilyMemberORM).filter(FamilyMemberORM.id == msg.sender_id).first()
        messages.append(MessageResponse(
            id=msg.id,
            content=msg.content,
            message_type=msg.message_type,
            file_url=msg.file_url,
            sender_id=msg.sender_id,
            sender_username=sender.username if sender else "Unknown",
            conversation_id=msg.conversation_id,
            created_at=msg.created_at
        ))
        
    return ConversationResponse(
        id=team_conv.id,
        title=team_conv.title,
        participants=participants,
        messages=messages,
        created_at=team_conv.created_at,
        updated_at=team_conv.updated_at
    )
