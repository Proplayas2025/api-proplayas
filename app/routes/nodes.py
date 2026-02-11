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
from core.image import save_optimized_image

router = APIRouter(
    prefix="/nodes",
    tags=["nodes"]
)

@router.get("", response_model=dict)
async def get_nodes(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page
    
    nodes = db.query(Node).offset(offset).limit(per_page).all()
    total = db.query(Node).count()
    
    return {
        "status": 200,
        "message": "Nodes retrieved successfully",
        "data": [NodeResponse.from_orm(node) for node in nodes],
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": (total + per_page - 1) // per_page
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
    
    # Join NodeMember con User para obtener datos completos
    members_data = (
        db.query(NodeMember, User)
        .join(User, NodeMember.user_id == User.id)
        .filter(NodeMember.node_id == node.id)
        .all()
    )
    
    result = []
    for nm, user in members_data:
        result.append({
            "id": nm.id,
            "user_id": user.id,
            "node_id": nm.node_id,
            "member_code": nm.member_code,
            "name": user.name,
            "email": user.email,
            "username": user.username,
            "research_line": nm.research_line,
            "work_area": nm.work_area,
            "status": user.status.value,
        })
    
    return {
        "status": 200,
        "message": "Members retrieved successfully",
        "data": result
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
    image: UploadFile = File(...),
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
    upload_dir = Path(settings.UPLOAD_DIR) / "profiles"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Read image bytes and optimize to WebP
    image_bytes = await image.read()
    image_name = f"node_{node.id}_profile"
    output_path = upload_dir / image_name
    final_path = save_optimized_image(image_bytes, output_path)
    
    # Update node — save just filename
    node.profile_picture = final_path.name
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
    
    # Update node memorandum field with just filename
    node.memorandum = doc_name
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


# ──────────────────────────────────────────────
# Member management (bajo /nodes/member/...)
# ──────────────────────────────────────────────

@router.put("/member/{member_id}", response_model=dict)
async def toggle_member_status(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle status de un miembro (active/inactive). Admin o líder del nodo."""
    member = db.query(User).filter(User.id == member_id).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Verificar permisos: admin o líder del nodo del miembro
    if current_user.role.value == "node_leader":
        if member.node_id is None:
            raise HTTPException(status_code=404, detail="Member not assigned to any node")
        node = db.query(Node).filter(Node.id == member.node_id).first()
        if not node or node.leader_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    elif current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Toggle status
    if member.status == UserStatus.active:
        member.status = UserStatus.inactive
    else:
        member.status = UserStatus.active
    
    db.commit()
    db.refresh(member)
    
    return {
        "status": 200,
        "message": "Member status updated successfully",
        "data": {
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "status": member.status.value,
        }
    }


@router.delete("/member/{member_id}", response_model=dict)
async def remove_member_from_node(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remover miembro del nodo (no elimina el usuario, solo la relación)."""
    member = db.query(User).filter(User.id == member_id).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if member.node_id is None:
        raise HTTPException(status_code=400, detail="Member not assigned to any node")
    
    # Verificar permisos
    if current_user.role.value == "node_leader":
        node = db.query(Node).filter(Node.id == member.node_id).first()
        if not node or node.leader_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    elif current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    node_id = member.node_id
    
    # Eliminar registro NodeMember
    db.query(NodeMember).filter(NodeMember.user_id == member.id, NodeMember.node_id == node_id).delete()
    
    # Desasignar usuario del nodo
    member.node_id = None
    member.status = UserStatus.inactive
    
    # Actualizar contador de miembros
    node = db.query(Node).filter(Node.id == node_id).first()
    if node:
        node.members_count = db.query(User).filter(User.node_id == node_id).count()
    
    db.commit()
    
    return {
        "status": 200,
        "message": "Member removed from node successfully",
        "data": {"id": member_id}
    }
