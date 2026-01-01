# Database Schema Documentation

This document describes the SQLite database schema used with SQLAlchemy ORM.

## Table: family_members

**Purpose**: Stores user account information and authentication data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | User's login username |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address |
| `full_name` | VARCHAR(255) | NOT NULL | User's full display name |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password |
| `role` | VARCHAR(50) | DEFAULT 'user' | User role (admin, user, animator) |
| `avatar_url` | VARCHAR(255) | NULLABLE | Profile picture URL |
| `status` | VARCHAR(20) | DEFAULT 'active' | Account status |
| `phone` | VARCHAR(20) | NULLABLE | Phone number |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account activation status |
| `is_online` | BOOLEAN | DEFAULT FALSE | Current online status |
| `last_seen` | DATETIME | NULLABLE | Last activity timestamp |
| `created_at` | DATETIME | DEFAULT NOW | Account creation timestamp |
| `updated_at` | DATETIME | DEFAULT NOW, ON UPDATE | Last profile update timestamp |

## Table: conversations

**Purpose**: Stores chat conversation metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `title` | VARCHAR(255) | NULLABLE | Conversation title/name |
| `created_at` | DATETIME | DEFAULT NOW | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT NOW, ON UPDATE | Last update timestamp |

## Table: conversation_participants

**Purpose**: Many-to-many relationship between users and conversations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `conversation_id` | INTEGER | FK → conversations.id, ON DELETE CASCADE | Parent conversation |
| `user_id` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Participant user |

## Table: messages

**Purpose**: Stores individual chat messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `content` | TEXT | NOT NULL | Message content |
| `message_type` | VARCHAR(50) | DEFAULT 'text' | Type of message (text, file, image) |
| `file_url` | VARCHAR(255) | NULLABLE | URL for attached files |
| `sender_id` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Message sender |
| `conversation_id` | INTEGER | FK → conversations.id, ON DELETE CASCADE | Parent conversation |
| `created_at` | DATETIME | DEFAULT NOW | Message timestamp |

## Table: files

**Purpose**: Stores uploaded file metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `filename` | VARCHAR(255) | NOT NULL | Original filename |
| `file_path` | VARCHAR(255) | NOT NULL | Server file path |
| `file_size` | INTEGER | NOT NULL | File size in bytes |
| `content_type` | VARCHAR(100) | NOT NULL | MIME content type |
| `uploaded_by` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Uploader user ID |
| `uploaded_at` | DATETIME | DEFAULT NOW | Upload timestamp |

## Table: projects

**Purpose**: Stores project information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `title` | VARCHAR(255) | NOT NULL | Project title |
| `description` | TEXT | NULLABLE | Project description |
| `status` | VARCHAR(50) | DEFAULT 'active' | Project status |
| `created_by` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Creator user ID |
| `created_at` | DATETIME | DEFAULT NOW | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT NOW, ON UPDATE | Last update timestamp |
| `deleted_at` | DATETIME | NULLABLE | Soft delete timestamp |

## Table: tasks

**Purpose**: Stores task information for project management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `title` | VARCHAR(255) | NOT NULL | Task title |
| `description` | TEXT | NULLABLE | Task description |
| `status` | VARCHAR(50) | DEFAULT 'pending' | Task status |
| `assigned_to` | INTEGER | FK → family_members.id, ON DELETE SET NULL | Assigned user |
| `created_by` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Creator user ID |
| `created_at` | DATETIME | DEFAULT NOW | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT NOW, ON UPDATE | Last update timestamp |

## Table: announcements

**Purpose**: Stores system announcements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `title` | VARCHAR(255) | NOT NULL | Announcement title |
| `content` | TEXT | NOT NULL | Announcement content |
| `created_by` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Creator user ID |
| `created_at` | DATETIME | DEFAULT NOW | Creation timestamp |

## Table: role_requests

**Purpose**: Stores role upgrade requests from users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `user_id` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Requesting user |
| `current_role` | VARCHAR(50) | NULLABLE | Current role |
| `requested_role` | VARCHAR(50) | NOT NULL | Requested role |
| `status` | VARCHAR(20) | DEFAULT 'pending' | Request status |
| `requested_at` | DATETIME | DEFAULT NOW | Request timestamp |
| `approved_at` | DATETIME | NULLABLE | Approval timestamp |
| `approved_by` | INTEGER | FK → family_members.id | Approving admin |
| `admin_notes` | TEXT | NULLABLE | Admin notes |
| `updated_at` | DATETIME | DEFAULT NOW, ON UPDATE | Last update |

## Table: deleted_projects

**Purpose**: Archive of soft-deleted projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `original_project_id` | INTEGER | | Original project ID |
| `title` | VARCHAR(255) | | Project title |
| `description` | TEXT | NULLABLE | Project description |
| `created_by` | INTEGER | NULLABLE | Original creator |
| `deleted_by` | INTEGER | FK → family_members.id | Deleting admin |
| `deleted_at` | DATETIME | DEFAULT NOW | Deletion timestamp |

## Table: admin_audit_log

**Purpose**: Audit log for admin actions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `admin_id` | INTEGER | FK → family_members.id, ON DELETE CASCADE | Acting admin |
| `action_type` | VARCHAR(100) | NOT NULL | Type of action |
| `target_type` | VARCHAR(50) | NOT NULL | Target entity type |
| `target_id` | VARCHAR(255) | NOT NULL | Target entity ID |
| `old_values` | TEXT | NULLABLE | JSON of old values |
| `new_values` | TEXT | NULLABLE | JSON of new values |
| `action_timestamp` | DATETIME | DEFAULT NOW | Action timestamp |

## Table: role_definitions

**Purpose**: Defines available roles and their permissions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `role_name` | VARCHAR(50) | UNIQUE, NOT NULL | Role name |
| `description` | TEXT | NULLABLE | Role description |
| `permissions` | TEXT | NULLABLE | JSON of permissions |
| `is_active` | BOOLEAN | DEFAULT TRUE | Role active status |
| `created_at` | DATETIME | DEFAULT NOW | Creation timestamp |
