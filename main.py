from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import User
from auth import get_password_hash
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="The Greatest API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-create default user
def create_default_user():
    from sqlalchemy.orm import sessionmaker
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Check if default user exists
        user = db.query(User).filter(User.username == "THE GREATEST").first()
        if not user:
            hashed_password = get_password_hash("0769636386")
            default_user = User(
                username="THE GREATEST",
                email="thegreatest@gmail.com",
                full_name="The Greatest",
                hashed_password=hashed_password
            )
            db.add(default_user)
            db.commit()
            print("Default user 'THE GREATEST' created.")
        else:
            print("Default user already exists.")
    finally:
        db.close()

# Create default user on startup
create_default_user()

# Include routers
from routers import auth, chat, files, projects, users

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to The Greatest API"}
