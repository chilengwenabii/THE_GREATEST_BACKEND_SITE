"""
SQLAlchemy ORM Models and Pydantic Schemas
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# =============================================================================
# SQLAlchemy ORM Models (Database Tables)
# =============================================================================

class FamilyMemberORM(Base):
    """User/Family Member table"""
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    avatar_url = Column(String(255), nullable=True)
    status = Column(String(20), default="active")
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tasks_created = relationship("TaskORM", back_populates="creator", foreign_keys="TaskORM.created_by")
    tasks_assigned = relationship("TaskORM", back_populates="assigned_user", foreign_keys="TaskORM.assigned_to")
    announcements = relationship("AnnouncementORM", back_populates="creator")
    files = relationship("FileORM", back_populates="uploader")
    projects = relationship("ProjectORM", back_populates="creator")
    messages = relationship("MessageORM", back_populates="sender")


class ConversationORM(Base):
    """Chat Conversation table"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship("MessageORM", back_populates="conversation")
    participants = relationship("ConversationParticipantORM", back_populates="conversation")


class ConversationParticipantORM(Base):
    """Many-to-many: Users in Conversations"""
    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))

    conversation = relationship("ConversationORM", back_populates="participants")
    user = relationship("FamilyMemberORM")


class MessageORM(Base):
    """Chat Message table"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")
    file_url = Column(String(255), nullable=True)
    sender_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    sender = relationship("FamilyMemberORM", back_populates="messages")
    conversation = relationship("ConversationORM", back_populates="messages")


class FileORM(Base):
    """Uploaded Files table"""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))
    uploaded_at = Column(DateTime, server_default=func.now())

    # Relationships
    uploader = relationship("FamilyMemberORM", back_populates="files")


class ProjectORM(Base):
    """Projects table"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_by = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    submission_link = Column(String(500), nullable=True)

    # Relationships
    creator = relationship("FamilyMemberORM", back_populates="projects")


class TaskORM(Base):
    """Tasks table"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    assigned_to = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("FamilyMemberORM", back_populates="tasks_created", foreign_keys=[created_by])
    assigned_user = relationship("FamilyMemberORM", back_populates="tasks_assigned", foreign_keys=[assigned_to])


class AnnouncementORM(Base):
    """Announcements table"""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    creator = relationship("FamilyMemberORM", back_populates="announcements")


class RoleRequestORM(Base):
    """Role upgrade requests"""
    __tablename__ = "role_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))
    current_role = Column(String(50))
    requested_role = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    requested_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("family_members.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DeletedProjectORM(Base):
    """Soft-deleted projects archive"""
    __tablename__ = "deleted_projects"

    id = Column(Integer, primary_key=True, index=True)
    original_project_id = Column(Integer)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    deleted_by = Column(Integer, ForeignKey("family_members.id"), nullable=True)
    deleted_at = Column(DateTime, server_default=func.now())


class AdminAuditLogORM(Base):
    """Admin action audit log"""
    __tablename__ = "admin_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"))
    action_type = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(255), nullable=False)
    old_values = Column(Text, nullable=True)  # JSON string
    new_values = Column(Text, nullable=True)  # JSON string
    action_timestamp = Column(DateTime, server_default=func.now())


class RoleDefinitionORM(Base):
    """Role definitions with permissions"""
    __tablename__ = "role_definitions"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


# =============================================================================
# Pydantic Schemas (Request/Response Validation)
# =============================================================================

# --- User/FamilyMember Schemas ---
class FamilyMember(BaseModel):
    """Pydantic model for current user dependency"""
    id: int
    username: str
    email: str
    full_name: str
    password_hash: str
    role: str = "user"
    avatar_url: Optional[str] = None
    status: str = "active"
    phone: Optional[str] = None
    is_active: bool = True
    is_online: bool = False
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_online: bool
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    assigned_to: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None


class Task(TaskBase):
    id: int
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Announcement Schemas ---
class AnnouncementCreate(BaseModel):
    title: str
    content: str


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class Announcement(BaseModel):
    id: int
    title: str
    content: str
    created_by: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- File Schemas ---
class File(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_by: int
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Project Schemas ---
class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "active"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class Project(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submission_link: Optional[str] = None

    class Config:
        from_attributes = True


# --- Conversation/Message Schemas ---
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


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    participants: List[dict]
    messages: List[MessageResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
