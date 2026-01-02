"""
The Greatest API - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from decouple import config
import os

from database import get_db, init_db, SessionLocal
from models import FamilyMemberORM
from auth import get_password_hash

# =============================================================================
# App Configuration
# =============================================================================

app = FastAPI(title="The Greatest API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://localhost:3007",
        "http://localhost:3008",
        "http://localhost:3009",
        "http://localhost:3010",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
        "http://127.0.0.1:3005",
        "http://127.0.0.1:5173", # Standard Vite port
        "https://the-greatestsite.vercel.app",  # Production frontend
        config("FRONTEND_URL", default="https://the-greatestsite.vercel.app"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Startup Events
# =============================================================================

@app.on_event("startup")
def on_startup():
    """Initialize database and create default admin on startup"""
    # Initialize tables (if they don't exist)
    init_db()
    
    # Create default admin user if configured
    create_default_admin()


def create_default_admin():
    """Create default admin user from environment variables or use defaults"""
    admin_email = config("DEFAULT_ADMIN_EMAIL", default="admin@thegreatest.app")
    admin_password = config("DEFAULT_ADMIN_PASSWORD", default="11111111")
    admin_username = config("DEFAULT_ADMIN_USERNAME", default="admin")
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing = db.query(FamilyMemberORM).filter(
            FamilyMemberORM.email == admin_email
        ).first()
        
        if existing:
            print(f"✓ Admin user '{admin_email}' already exists.")
            return
        
        # Create admin
        admin = FamilyMemberORM(
            username=admin_username,
            email=admin_email,
            full_name="Administrator",
            password_hash=get_password_hash(admin_password),
            role="admin",
            status="active",
            is_active=True,
            is_online=False
        )
        db.add(admin)
        db.commit()
        print(f"✓ Default admin '{admin_username}' created successfully.")
    except Exception as e:
        print(f"✗ Error creating default admin: {e}")
        db.rollback()
    finally:
        db.close()


# =============================================================================
# Include Routers
# =============================================================================

from routers import auth, chat, files, projects, users, tasks, announcements, admin, search

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(announcements.router, prefix="/announcements", tags=["announcements"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(search.router, prefix="/search", tags=["search"])


# =============================================================================
# Static Files
# =============================================================================

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Mount static files directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
def read_root():
    return {"message": "Welcome to The Greatest API", "version": "2.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
