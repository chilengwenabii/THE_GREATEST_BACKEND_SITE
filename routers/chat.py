from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Conversation, Message
from auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ConversationCreate(BaseModel):
    title: str | None = None
    participant_ids: List[int]

class MessageCreate(BaseModel):
    content: str
    conversation_id: int
    message_type: str = "text"
    file_url: str | None = None

class MessageResponse(BaseModel):
    id: int
    content: str
    message_type: str
    file_url: str | None
    sender_id: int
    sender_username: str
    conversation_id: int
    created_at: str

class ConversationResponse(BaseModel):
    id: int
    title: str | None
    participants: List[dict]
    messages: List[MessageResponse]
    created_at: str
    updated_at: str | None

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    conv: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create conversation
    db_conv = Conversation(title=conv.title)
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)

    # Add participants
    participants = []
    for user_id in conv.participant_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            participants.append(user)

    db_conv.participants.extend(participants)
    db.commit()
    db.refresh(db_conv)

    return {
        "id": db_conv.id,
        "title": db_conv.title,
        "participants": [{"id": p.id, "username": p.username, "full_name": p.full_name} for p in db_conv.participants],
        "messages": [],
        "created_at": db_conv.created_at.isoformat(),
        "updated_at": db_conv.updated_at.isoformat() if db_conv.updated_at else None
    }

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversations = db.query(Conversation).filter(
        Conversation.participants.any(id=current_user.id)
    ).all()

    result = []
    for conv in conversations:
        messages = []
        for msg in conv.messages:
            messages.append({
                "id": msg.id,
                "content": msg.content,
                "message_type": msg.message_type,
                "file_url": msg.file_url,
                "sender_id": msg.sender_id,
                "sender_username": msg.sender.username,
                "conversation_id": msg.conversation_id,
                "created_at": msg.created_at.isoformat()
            })

        result.append({
            "id": conv.id,
            "title": conv.title,
            "participants": [{"id": p.id, "username": p.username, "full_name": p.full_name} for p in conv.participants],
            "messages": messages,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
        })

    return result

@router.post("/messages", response_model=MessageResponse)
def send_message(
    msg: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if conversation exists and user is participant
    conv = db.query(Conversation).filter(Conversation.id == msg.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user not in conv.participants:
        raise HTTPException(status_code=403, detail="Not authorized to send message in this conversation")

    # Create message
    db_msg = Message(
        content=msg.content,
        message_type=msg.message_type,
        file_url=msg.file_url,
        sender_id=current_user.id,
        conversation_id=msg.conversation_id
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    # Update conversation updated_at
    conv.updated_at = db_msg.created_at
    db.commit()

    return {
        "id": db_msg.id,
        "content": db_msg.content,
        "message_type": db_msg.message_type,
        "file_url": db_msg.file_url,
        "sender_id": db_msg.sender_id,
        "sender_username": db_msg.sender.username,
        "conversation_id": db_msg.conversation_id,
        "created_at": db_msg.created_at.isoformat()
    }

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if conversation exists and user is participant
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user not in conv.participants:
        raise HTTPException(status_code=403, detail="Not authorized to view this conversation")

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()

    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "content": msg.content,
            "message_type": msg.message_type,
            "file_url": msg.file_url,
            "sender_id": msg.sender_id,
            "sender_username": msg.sender.username,
            "conversation_id": msg.conversation_id,
            "created_at": msg.created_at.isoformat()
        })

    return result
