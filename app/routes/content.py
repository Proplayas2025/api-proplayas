from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from pathlib import Path
from database import get_db
from schemas.content import ContentResponse, ContentCreate, ContentUpdate
from models import Content, User
from models.content import ContentType, ContentStatus
from core.security import get_current_user, get_current_admin
from core.config import settings
from core.image import save_optimized_image

router = APIRouter(
    prefix="/content",
    tags=["content"]
)


@router.get("/all", response_model=dict)
async def get_all_content(
    content_type: Optional[ContentType] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Admin only: returns ALL content regardless of author or status."""
    query = db.query(Content)

    if content_type:
        query = query.filter(Content.content_type == content_type)

    total = query.count()
    offset = (page - 1) * per_page
    content_list = query.order_by(Content.id.desc()).offset(offset).limit(per_page).all()

    return {
        "status": 200,
        "message": "All content retrieved successfully",
        "data": [ContentResponse.from_orm(c) for c in content_list],
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": (total + per_page - 1) // per_page
        }
    }


@router.get("", response_model=dict)
async def get_content(
    content_type: Optional[ContentType] = None,
    status: Optional[ContentStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Content)
    
    if content_type:
        query = query.filter(Content.content_type == content_type)
    
    if status:
        query = query.filter(Content.status == status)
    else:
        query = query.filter(Content.status == ContentStatus.published)
    
    offset = (page - 1) * per_page
    content_list = query.offset(offset).limit(per_page).all()
    total = query.count()
    
    return {
        "status": 200,
        "message": "Content retrieved successfully",
        "data": [ContentResponse.from_orm(c) for c in content_list],
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": (total + per_page - 1) // per_page
        }
    }

@router.get("/own", response_model=dict)
async def get_own_content(
    content_type: Optional[ContentType] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Content).filter(Content.author_id == current_user.id)
    
    if content_type:
        query = query.filter(Content.content_type == content_type)
    
    offset = (page - 1) * per_page
    content_list = query.offset(offset).limit(per_page).all()
    total = query.count()
    
    return {
        "status": 200,
        "message": "Content retrieved successfully",
        "data": [ContentResponse.from_orm(c) for c in content_list],
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": (total + per_page - 1) // per_page
        }
    }

@router.get("/{content_id}", response_model=dict)
async def get_content_by_id(
    content_id: int,
    db: Session = Depends(get_db)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return {
        "status": 200,
        "message": "Content retrieved successfully",
        "data": ContentResponse.from_orm(content)
    }

@router.post("", response_model=dict)
async def create_content(
    content_data: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_content = Content(
        **content_data.dict(),
        author_id=current_user.id
    )
    
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    
    return {
        "status": 200,
        "message": "Content created successfully",
        "data": ContentResponse.from_orm(new_content)
    }

@router.put("/{content_id}/toggle-status", response_model=dict)
async def toggle_content_status(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.author_id != current_user.id and current_user.role.value not in ["admin", "node_leader"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Cycle through statuses: draft -> published -> archived -> draft
    if content.status == ContentStatus.draft:
        content.status = ContentStatus.published
    elif content.status == ContentStatus.published:
        content.status = ContentStatus.archived
    else:
        content.status = ContentStatus.draft
    
    db.commit()
    db.refresh(content)
    
    return {
        "status": 200,
        "message": "Content status updated successfully",
        "data": ContentResponse.from_orm(content)
    }

@router.put("/{content_id}", response_model=dict)
async def update_content(
    content_id: int,
    content_update: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.author_id != current_user.id and current_user.role.value not in ["admin", "node_leader"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    for field, value in content_update.dict(exclude_unset=True).items():
        setattr(content, field, value)
    
    db.commit()
    db.refresh(content)
    
    return {
        "status": 200,
        "message": "Content updated successfully",
        "data": ContentResponse.from_orm(content)
    }

@router.post("/{content_id}/upload-file", response_model=dict)
async def upload_file(
    content_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.author_id != current_user.id and current_user.role.value not in ["admin", "node_leader"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR) / "docs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    file_name = f"content_{content_id}_{file.filename}"
    file_path = upload_dir / file_name
    
    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update content — save just filename, frontend constructs full URL
    content.file_path = file_name
    content.file_url = file_name
    
    db.commit()
    db.refresh(content)
    
    return {
        "status": 200,
        "message": "File uploaded successfully",
        "data": ContentResponse.from_orm(content)
    }

@router.post("/{content_id}/upload-cover-image", response_model=dict)
async def upload_cover_image(
    content_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.author_id != current_user.id and current_user.role.value not in ["admin", "node_leader"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR) / "covers"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Read image bytes and optimize to WebP
    image_bytes = await image.read()
    image_name = f"content_{content_id}_cover"
    output_path = upload_dir / image_name
    final_path = save_optimized_image(image_bytes, output_path)
    
    # Update content — save just filename, frontend constructs full URL via baseUrl
    content.cover_image = final_path.name
    content.cover_image_url = None
    
    db.commit()
    db.refresh(content)
    
    return {
        "status": 200,
        "message": "Cover image uploaded successfully",
        "data": ContentResponse.from_orm(content)
    }

@router.delete("/{content_id}", response_model=dict)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.author_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(content)
    db.commit()
    
    return {
        "status": 200,
        "message": "Content deleted successfully",
        "data": {"id": content_id}
    }
