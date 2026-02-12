from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pathlib import Path
from database import get_db
from schemas.user import UserResponse, UserListItem, UserUpdate
from models import User, Node, SocialLink
from models.social_link import SocialPlatform
from core.security import get_current_user, get_current_admin
from core.config import settings
from core.image import save_optimized_image

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("", response_model=dict)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    offset = (page - 1) * per_page
    query = db.query(User)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                User.name.ilike(search_filter),
                User.email.ilike(search_filter),
                User.username.ilike(search_filter),
            )
        )

    users = query.offset(offset).limit(per_page).all()
    total = query.count()
    
    # Enrich with node_code
    result = []
    for user in users:
        item = UserListItem.from_orm(user)
        if user.node_id:
            node = db.query(Node).filter(Node.id == user.node_id).first()
            if node:
                item.node_code = node.code
        result.append(item)
    
    return {
        "status": 200,
        "message": "Users retrieved successfully",
        "data": result,
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

@router.put("/me", response_model=dict)
async def update_current_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = user_update.dict(exclude_unset=True, exclude={"social_media"})
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    # Manejar social_media si se proporciona
    if user_update.social_media is not None:
        # Eliminar links existentes
        db.query(SocialLink).filter(SocialLink.user_id == current_user.id).delete()
        
        # Crear nuevos links
        for link_data in user_update.social_media:
            try:
                platform = SocialPlatform(link_data.platform)
            except ValueError:
                continue
            
            new_link = SocialLink(
                platform=platform,
                url=link_data.url,
                user_id=current_user.id
            )
            db.add(new_link)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "status": 200,
        "message": "Profile updated successfully",
        "data": UserResponse.from_orm(current_user)
    }

@router.get("/profile/{username}", response_model=dict)
async def get_public_profile(
    username: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "status": 200,
        "message": "User profile retrieved successfully",
        "data": UserResponse.from_orm(user)
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
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True, exclude={"social_media"})
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Manejar social_media si se proporciona
    if user_update.social_media is not None:
        # Eliminar links existentes
        db.query(SocialLink).filter(SocialLink.user_id == user.id).delete()
        
        # Crear nuevos links
        for link_data in user_update.social_media:
            try:
                platform = SocialPlatform(link_data.platform)
            except ValueError:
                continue
            
            new_link = SocialLink(
                platform=platform,
                url=link_data.url,
                user_id=user.id
            )
            db.add(new_link)
    
    db.commit()
    db.refresh(user)
    
    return {
        "status": 200,
        "message": "User updated successfully",
        "data": UserResponse.from_orm(user)
    }

@router.put("/{user_id}/toggle-status", response_model=dict)
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Admin only: toggle user status between active/inactive."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio estado")

    from models.user import UserStatus
    if user.status == UserStatus.active:
        user.status = UserStatus.inactive
    else:
        user.status = UserStatus.active

    db.commit()
    db.refresh(user)

    return {
        "status": 200,
        "message": "User status updated successfully",
        "data": UserListItem.from_orm(user)
    }


@router.post("/upload-profile-picture", response_model=dict)
async def upload_user_profile_picture(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR) / "profiles"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Read image bytes and optimize to WebP
    image_bytes = await image.read()
    image_name = f"user_{current_user.id}_profile"
    output_path = upload_dir / image_name
    final_path = save_optimized_image(image_bytes, output_path)
    
    # Update user — save just filename
    current_user.profile_picture = final_path.name
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
