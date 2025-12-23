from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from database import get_db
from models import File as FileModel
from auth import get_current_user
from models import FamilyMember

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
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
    db_file = FileModel(
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
        "id": str(db_file.id),
        "filename": db_file.filename,
        "file_path": db_file.file_path,
        "file_size": db_file.file_size,
        "content_type": db_file.content_type,
        "uploaded_at": db_file.uploaded_at.isoformat()
    }

@router.get("/files")
def get_files(
    db: Session = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    files = db.query(FileModel).filter(FileModel.uploaded_by == current_user.id).all()
    return [
        {
            "id": str(f.id),
            "filename": f.filename,
            "file_path": f.file_path,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "uploaded_at": f.uploaded_at.isoformat()
        }
        for f in files
    ]

@router.get("/files/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: FamilyMember = Depends(get_current_user)
):
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")

    return FileResponse(
        path=file.file_path,
        filename=file.filename,
        media_type=file.content_type
    )
