"""
Files Router: File upload and management endpoints
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime

from database import get_db
from models import FamilyMemberORM, FamilyMember, FileORM
from auth import get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    """Upload a file"""
    # Validate file size (max 10MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Save file info to database
    db_file = FileORM(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        content_type=file.content_type,
        uploaded_by=current_user.id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "file_path": db_file.file_path,
        "file_size": db_file.file_size,
        "content_type": db_file.content_type,
        "uploaded_at": db_file.uploaded_at.isoformat() if db_file.uploaded_at else None
    }


@router.get("/files")
def get_files(
    db: Session = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    """Get all files for current user"""
    files = db.query(FileORM).filter(FileORM.uploaded_by == current_user.id).all()
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "file_path": f.file_path,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        }
        for f in files
    ]


@router.get("/files/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    """Download a file"""
    file = db.query(FileORM).filter(FileORM.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")
    
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file.file_path,
        filename=file.filename,
        media_type=file.content_type
    )


@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    """Delete a file"""
    file = db.query(FileORM).filter(FileORM.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    
    # Delete from disk
    if os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    return {"message": "File deleted successfully"}
