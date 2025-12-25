from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import test_sqlite_connection, get_db_connection
from models import FamilyMember
from auth import get_password_hash
import os

# Test SQLite connection on startup
test_sqlite_connection()

app = FastAPI(title="The Greatest API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative dev port
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://127.0.0.1:3001",  # Alternative localhost
        "https://the-greatestsite-v4qt.vercel.app",  # Deployed frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-create default user
def create_default_user():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if default user exists
        cursor.execute("SELECT * FROM family_members WHERE email = ?", ('thegreatest@gmail.com',))
        user_data = cursor.fetchone()

        if not user_data:
            password_hash = get_password_hash("0769636386")
            cursor.execute("""
                INSERT INTO family_members (username, email, full_name, password_hash, role, is_active, is_online)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("THE GREATEST", "thegreatest@gmail.com", "The Greatest", password_hash, "admin", True, False))
            conn.commit()
            print("Default user 'THE GREATEST' created.")
        else:
            print("Default user already exists.")
    except Exception as e:
        print(f"Error creating default user: {e}")
        conn.rollback()
    finally:
        conn.close()

# Create default user on startup
create_default_user()

# Include routers
from routers import auth, chat, files, projects, users, tasks, announcements, admin

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(announcements.router, prefix="/announcements", tags=["announcements"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Welcome to The Greatest API"}
