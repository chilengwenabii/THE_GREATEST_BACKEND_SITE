# Database Schema Documentation

This document describes the current Supabase database schema with UUID primary keys.

## Table: family_members

**Purpose**: Stores user account information and authentication data.

**Columns**:
- `id` UUID PRIMARY KEY - Unique identifier (auto-generated)
- `username` CHARACTER VARYING - User's login username
- `full_name` CHARACTER VARYING - User's full display name
- `email` CHARACTER VARYING - User's email address
- `password_hash` CHARACTER VARYING - Hashed password
- `role` TEXT - User role (admin, user, animator, etc.)
- `avatar_url` TEXT - Profile picture URL
- `status` TEXT - Account status (active, inactive, etc.)
- `created_at` TIMESTAMP WITH TIME ZONE - Account creation timestamp
- `updated_at` TIMESTAMP WITH TIME ZONE - Last profile update timestamp
- `is_active` BOOLEAN - Account activation status
- `is_online` BOOLEAN - Current online status
- `last_seen` TIMESTAMP WITH TIME ZONE - Last activity timestamp
- `phone` CHARACTER VARYING - Optional phone number

## Table: conversations

**Purpose**: Stores chat conversation metadata.

**Columns**:
- `id` SERIAL PRIMARY KEY - Auto-incrementing unique identifier
- `title` VARCHAR(255) - Conversation title/name
- `created_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() - Creation timestamp
- `updated_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() - Last update timestamp

## Table: messages

**Purpose**: Stores individual chat messages.

**Columns**:
- `id` SERIAL PRIMARY KEY - Auto-incrementing unique identifier
- `content` TEXT NOT NULL - Message content
- `message_type` VARCHAR(50) DEFAULT 'text' - Type of message (text, file, etc.)
- `file_url` VARCHAR(255) - URL for attached files
- `sender_id` INTEGER REFERENCES family_members(id) ON DELETE CASCADE - Message sender
- `conversation_id` INTEGER REFERENCES conversations(id) ON DELETE CASCADE - Parent conversation
- `created_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() - Message timestamp

## Table: files

**Purpose**: Stores uploaded file metadata.

**Columns**:
- `id` SERIAL PRIMARY KEY - Auto-incrementing unique identifier
- `filename` VARCHAR(255) NOT NULL - Original filename
- `file_path` VARCHAR(255) NOT NULL - Server file path
- `file_size` INTEGER NOT NULL - File size in bytes
- `content_type` VARCHAR(100) NOT NULL - MIME content type
- `uploaded_by` INTEGER REFERENCES family_members(id) ON DELETE CASCADE - Uploader user ID
- `uploaded_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() - Upload timestamp

## Table: projects

**Purpose**: Stores project information.

**Columns**:
- `id` SERIAL PRIMARY KEY - Auto-incrementing unique identifier
- `title` VARCHAR(255) NOT NULL - Project title
- `description` TEXT - Project description
- `status` VARCHAR(50) DEFAULT 'active' - Project status
- `created_by` INTEGER REFERENCES family_members(id) ON DELETE CASCADE - Creator user ID
- `created_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() - Creation timestamp
- `updated_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW() - Last update timestamp

## Table: family_member_conversations

**Purpose**: Many-to-many relationship between users and conversations.

**Columns**:
- `family_member_id` INTEGER REFERENCES family_members(id) ON DELETE CASCADE
- `conversation_id` INTEGER REFERENCES conversations(id) ON DELETE CASCADE
- PRIMARY KEY (family_member_id, conversation_id)

## Indexes

- `idx_family_members_username` ON family_members(username) - For faster username lookups

## Required Database Updates

To fix user registration and enable full functionality, run these SQL commands in your Supabase SQL editor:

```sql
-- Add missing columns to family_members table
ALTER TABLE family_members ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';
ALTER TABLE family_members ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);
ALTER TABLE family_members ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE family_members ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';

-- Create missing tables
CREATE TABLE IF NOT EXISTS role_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES family_members(id) ON DELETE CASCADE,
    current_role VARCHAR(50),
    requested_role VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by INTEGER REFERENCES family_members(id),
    admin_notes TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deleted_projects (
    id SERIAL PRIMARY KEY,
    original_project_id INTEGER,
    title VARCHAR(255),
    description TEXT,
    created_by INTEGER,
    deleted_by INTEGER REFERENCES family_members(id),
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_audit_log (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES family_members(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS role_definitions (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default roles
INSERT INTO role_definitions (role_name, description, permissions) VALUES
('admin', 'Full system administrator', '{"all": true}'),
('user', 'Regular user', '{"read": true, "write": true}'),
('animator', 'Animation specialist', '{"read": true, "write": true, "animate": true}')
ON CONFLICT (role_name) DO NOTHING;
```

## Registration Process Requirements

For successful user registration, the following fields must be provided and stored:

**Required Fields**:
- username (unique)
- email (unique)
- full_name
- hashed_password

**Optional Fields**:
- phone
- role (defaults to 'user')
- avatar_url
- is_active (defaults to true)
- is_online (defaults to false)

**Auto-generated Fields**:
- id (auto-increment)
- created_at (current timestamp)
- updated_at (current timestamp)
- last_seen (null initially)
