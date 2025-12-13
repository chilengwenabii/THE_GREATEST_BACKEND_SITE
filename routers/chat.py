from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from database import get_db
from models import FamilyMember, Conversation, Message
from auth import get_current_user
from pydantic import BaseModel
from typing import List
from datetime import datetime

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
    supabase: Client = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    try:
        # Create conversation
        conv_data = {
            "title": conv.title,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        response = supabase.table('conversations').insert(conv_data).execute()
        db_conv = response.data[0]

        # Add participants (assuming conversation_participants table)
        participants = []
        for user_id in conv.participant_ids:
            # Check if user exists
            user_response = supabase.table('family_members').select('*').eq('id', user_id).execute()
            if user_response.data:
                user = user_response.data[0]
                participants.append(user)
                # Add to conversation_participants
                supabase.table('conversation_participants').insert({
                    "conversation_id": db_conv['id'],
                    "user_id": user_id
                }).execute()

        return {
            "id": db_conv['id'],
            "title": db_conv['title'],
            "participants": [{"id": p['id'], "username": p['username'], "full_name": p['full_name']} for p in participants],
            "messages": [],
            "created_at": db_conv['created_at'],
            "updated_at": db_conv['updated_at']
        }
    except Exception as e:
        print(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    supabase: Client = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    try:
        # Get conversations where user is participant
        conv_part_response = supabase.table('conversation_participants').select('conversation_id').eq('user_id', current_user.id).execute()
        conv_ids = [cp['conversation_id'] for cp in conv_part_response.data]

        if not conv_ids:
            return []

        # Get conversations
        conv_response = supabase.table('conversations').select('*').in_('id', conv_ids).execute()
        conversations = conv_response.data

        result = []
        for conv in conversations:
            # Get participants
            part_response = supabase.table('conversation_participants').select('user_id, family_members!inner(username, full_name)').eq('conversation_id', conv['id']).execute()
            participants = [{"id": p['user_id'], "username": p['family_members']['username'], "full_name": p['family_members']['full_name']} for p in part_response.data]

            # Get messages
            msg_response = supabase.table('messages').select('*, family_members!inner(username)').eq('conversation_id', conv['id']).order('created_at').execute()
            messages = []
            for msg in msg_response.data:
                messages.append({
                    "id": msg['id'],
                    "content": msg['content'],
                    "message_type": msg['message_type'],
                    "file_url": msg['file_url'],
                    "sender_id": msg['sender_id'],
                    "sender_username": msg['family_members']['username'],
                    "conversation_id": msg['conversation_id'],
                    "created_at": msg['created_at']
                })

            result.append({
                "id": conv['id'],
                "title": conv['title'],
                "participants": participants,
                "messages": messages,
                "created_at": conv['created_at'],
                "updated_at": conv['updated_at']
            })

        return result
    except Exception as e:
        print(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/messages", response_model=MessageResponse)
def send_message(
    msg: MessageCreate,
    supabase: Client = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    try:
        # Check if conversation exists
        conv_response = supabase.table('conversations').select('*').eq('id', msg.conversation_id).execute()
        if not conv_response.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check if user is participant
        part_response = supabase.table('conversation_participants').select('*').eq('conversation_id', msg.conversation_id).eq('user_id', current_user.id).execute()
        if not part_response.data:
            raise HTTPException(status_code=403, detail="Not authorized to send message in this conversation")

        # Create message
        msg_data = {
            "content": msg.content,
            "message_type": msg.message_type,
            "file_url": msg.file_url,
            "sender_id": current_user.id,
            "conversation_id": msg.conversation_id,
            "created_at": datetime.utcnow().isoformat()
        }
        response = supabase.table('messages').insert(msg_data).execute()
        db_msg = response.data[0]

        # Update conversation updated_at
        supabase.table('conversations').update({"updated_at": db_msg['created_at']}).eq('id', msg.conversation_id).execute()

        # Get sender username
        sender_response = supabase.table('family_members').select('username').eq('id', current_user.id).execute()
        sender_username = sender_response.data[0]['username'] if sender_response.data else "Unknown"

        return {
            "id": db_msg['id'],
            "content": db_msg['content'],
            "message_type": db_msg['message_type'],
            "file_url": db_msg['file_url'],
            "sender_id": db_msg['sender_id'],
            "sender_username": sender_username,
            "conversation_id": db_msg['conversation_id'],
            "created_at": db_msg['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    supabase: Client = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    try:
        # Check if conversation exists
        conv_response = supabase.table('conversations').select('*').eq('id', conversation_id).execute()
        if not conv_response.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check if user is participant
        part_response = supabase.table('conversation_participants').select('*').eq('conversation_id', conversation_id).eq('user_id', current_user.id).execute()
        if not part_response.data:
            raise HTTPException(status_code=403, detail="Not authorized to view this conversation")

        # Get messages
        msg_response = supabase.table('messages').select('*, family_members!inner(username)').eq('conversation_id', conversation_id).order('created_at').execute()

        result = []
        for msg in msg_response.data:
            result.append({
                "id": msg['id'],
                "content": msg['content'],
                "message_type": msg['message_type'],
                "file_url": msg['file_url'],
                "sender_id": msg['sender_id'],
                "sender_username": msg['family_members']['username'],
                "conversation_id": msg['conversation_id'],
                "created_at": msg['created_at']
            })

        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
