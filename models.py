from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Pydantic models for Supabase data operations

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    assigned_to: Optional[int] = None
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None

class Task(TaskBase):
    id: int

class FamilyMemberBase(BaseModel):
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    password_hash: str
    role: str = "user"
    is_active: bool = True
    is_online: bool = False
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None

class FamilyMemberCreate(FamilyMemberBase):
    pass

class FamilyMemberUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None
    last_seen: Optional[datetime] = None

class FamilyMember(FamilyMemberBase):
    id: int

class ConversationBase(BaseModel):
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: Optional[str] = None

class Conversation(ConversationBase):
    id: int

class MessageBase(BaseModel):
    content: str
    message_type: str = "text"
    file_url: Optional[str] = None
    sender_id: int
    conversation_id: int
    created_at: Optional[datetime] = None

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    message_type: Optional[str] = None
    file_url: Optional[str] = None

class Message(MessageBase):
    id: int

class FileBase(BaseModel):
    filename: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_by: int
    uploaded_at: Optional[datetime] = None

class FileCreate(FileBase):
    pass

class FileUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None

class File(FileBase):
    id: int

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "active"
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Project(ProjectBase):
    id: int

class AnnouncementBase(BaseModel):
    title: str
    content: str
    created_by: int
    created_at: Optional[datetime] = None

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class Announcement(AnnouncementBase):
    id: int
