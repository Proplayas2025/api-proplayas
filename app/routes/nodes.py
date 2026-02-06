from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import shutil
from database import get_db
from schemas.node import NodeResponse, NodeCreate, NodeUpdate, NodeWithMembers
from schemas.user import UserListItem
from models import Node, User
from models.node_member import NodeMember
from models.user import UserStatus
from core.security import get_current_user, get_current_admin, get_current_node_leader
from core.config import settings

router = APIRouter(
    prefix="/nodes",
    tags=["nodes"]
)

@router.get("", response_model=dict)
async def get_nodes(
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * 10
    
    nodes = db.query(Node).offset(offset).limit(10).all()
    total = db.query(Node).count()
    
    return {
        "status": 200,
        "message": "Nodes retrieved successfully",
        "data": {
            "data": [NodeResponse.from_orm(node) for node in nodes],
            "pagination": {
                "current_page": page,
                "per_page": 10,
                "total": total,
                "last_page": (total + 9) // 10
            }
        }
    }

@router.get("/{code}", response_model=dict)
async def get_node(
    code: str,
    db: Session = Depends(get_db)
):
    node = db.query(Node).filter(Node.code == code).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return {
        "status": 200,
        "message": "Node retrieved successfully",
        "data": NodeResponse.from_orm(node)
    }

@router.get("/members/{code}", response_model=dict)
async def get_node_members(
    code: str,
    db: Session = Depends(get_db)
):
    node = db.query(Node).filter(Node.code == code).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    members = db.query(User).filter(User.node_id == node.id).all()
    
    return {
        "status": 200,
        "message": "Members retrieved successfully",
        "data": [UserListItem.from_orm(member) for member in members]
    }

@router.post("", response_model=dict)
async def create_node(
    node_data: NodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    existing = db.query(Node).filter(Node.code == node_data.code).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Node code already exists")
    
    new_node = Node(**node_data.dict())
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    
    return {
        "status": 200,
        "message": "Node created successfully",
        "data": NodeResponse.from_orm(new_node)
    }

@router.put("/{node_id}", response_model=dict)
async def update_node(
    node_id: int,
    node_update: NodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    node = db.query(Node).filter(Node.id == node_id).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    if current_user.role.value != "admin" and node.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    for field, value in node_update.dict(exclude_unset=True).items():
        setattr(node, field, value)
    
    db.commit()
    db.refresh(node)
    
    return {
        "status": 200,
        "message": "Node updated successfully",
        "data": NodeResponse.from_orm(node)
    }

@router.post("/upload-profile-picture", response_model=dict)
async def upload_node_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Node leader can only upload for their own node
    if current_user.role.value == "node_leader":
        node = db.query(Node).filter(Node.leader_id == current_user.id).first()
    elif current_user.role.value == "admin":
        # Admin needs to specify which node (could be added as query param)
        node = db.query(Node).filter(Node.leader_id == current_user.id).first()
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR) / "profiles"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    image_name = f"node_{node.id}_profile.{file_extension}"
    image_path = upload_dir / image_name
    
    # Save file
    with image_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update node
    node.profile_picture = str(image_path)
    db.commit()
    db.refresh(node)
    
    return {
        "status": 200,
        "message": "Profile picture uploaded successfully",
        "data": NodeResponse.from_orm(node)
    }

@router.post("/upload-memorandum", response_model=dict)
async def upload_node_memorandum(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Node leader can only upload for their own node
    if current_user.role.value == "node_leader":
        node = db.query(Node).filter(Node.leader_id == current_user.id).first()
    elif current_user.role.value == "admin":
        node = db.query(Node).filter(Node.leader_id == current_user.id).first()
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR) / "docs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    doc_name = f"node_{node.id}_memorandum.{file_extension}"
    doc_path = upload_dir / doc_name
    
    # Save file
    with doc_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update node memorandum field with file path
    node.memorandum = str(doc_path)
    db.commit()
    db.refresh(node)
    
    return {
        "status": 200,
        "message": "Memorandum uploaded successfully",
        "data": NodeResponse.from_orm(node)
    }

@router.delete("/{node_id}", response_model=dict)
async def delete_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    node = db.query(Node).filter(Node.id == node_id).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    db.delete(node)
    db.commit()
    
    return {
        "status": 200,
        "message": "Node deleted successfully",
        "data": {"id": node_id}
    }
