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

# CORS configuration
origins = [
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
    "http://127.0.0.1:5173",
    "https://the-greatestsite.vercel.app",
    config("FRONTEND_URL", default="https://the-greatestsite.vercel.app"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
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
            print(f"[OK] Admin user '{admin_email}' already exists.")
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
        print(f"[OK] Default admin '{admin_username}' created successfully.")
    except Exception as e:
        print(f"[!] Error creating default admin: {e}")
        db.rollback()
    finally:
        db.close()


# =============================================================================
# Include Routers
# =============================================================================

from routers import auth, chat, files, projects, users, tasks, announcements, admin, search, analytics, notifications

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(announcements.router, prefix="/api/v1/announcements", tags=["announcements"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])


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
    return {"message": "VERIFICATION_SUCCESSFUL_THE_GREATEST", "version": "2.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
