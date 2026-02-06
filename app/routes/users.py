from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import shutil
from database import get_db
from schemas.user import UserResponse, UserListItem, UserUpdate
from models import User
from core.security import get_current_user, get_current_admin
from core.config import settings

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("", response_model=dict)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    offset = (page - 1) * per_page
    
    users = db.query(User).offset(offset).limit(per_page).all()
    total = db.query(User).count()
    
    return {
        "status": 200,
        "message": "Users retrieved successfully",
        "data": [UserListItem.from_orm(user) for user in users],
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": (total + per_page - 1) // per_page
        }
    }

@router.get("/me", response_model=dict)
async def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return {
        "status": 200,
        "message": "User profile retrieved successfully",
        "data": UserResponse.from_orm(current_user)
    }

@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "status": 200,
        "message": "User retrieved successfully",
        "data": UserResponse.from_orm(user)
    }

@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return {
        "status": 200,
        "message": "User updated successfully",
        "data": UserResponse.from_orm(user)
    }

@router.post("/upload-profile-picture", response_model=dict)
async def upload_user_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR) / "profiles"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    image_name = f"user_{current_user.id}_profile.{file_extension}"
    image_path = upload_dir / image_name
    
    # Save file
    with image_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user
    current_user.profile_picture = str(image_path)
    db.commit()
    db.refresh(current_user)
    
    return {
        "status": 200,
        "message": "Profile picture uploaded successfully",
        "data": UserResponse.from_orm(current_user)
    }

@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {
        "status": 200,
        "message": "User deleted successfully",
        "data": {"id": user_id}
    }
