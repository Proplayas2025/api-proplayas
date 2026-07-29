from fastapi import APIRouter, Depends, File, Query, UploadFile

from core.security import get_current_admin, get_current_user
from dependencies import get_node_service
from models import User
from schemas.node import NodeCreate, NodeUpdate
from services.node_service import NodeService

router = APIRouter(
    prefix="/nodes",
    tags=["nodes"]
)


@router.get("", response_model=dict)
async def get_nodes(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    node_service: NodeService = Depends(get_node_service),
):
    """Listado público paginado de nodos con búsqueda por nombre, código, país o ciudad."""
    page_result = node_service.list_nodes(page, per_page, search)

    return {
        "status": 200,
        "message": "Nodes retrieved successfully",
        "data": page_result.items,
        "meta": page_result.meta,
    }


@router.get("/{code}", response_model=dict)
async def get_node(
    code: str,
    node_service: NodeService = Depends(get_node_service),
):
    """Detalle de un nodo por su código (ej. A01)."""
    return {
        "status": 200,
        "message": "Node retrieved successfully",
        "data": node_service.get_by_code(code),
    }


@router.get("/members/{code}", response_model=dict)
async def get_node_members(
    code: str,
    node_service: NodeService = Depends(get_node_service),
):
    """Miembros de un nodo con sus datos de usuario y membresía."""
    return {
        "status": 200,
        "message": "Members retrieved successfully",
        "data": node_service.list_members(code),
    }


@router.post("", response_model=dict)
async def create_node(
    node_data: NodeCreate,
    current_user: User = Depends(get_current_admin),
    node_service: NodeService = Depends(get_node_service),
):
    """Admin: crea un nodo nuevo."""
    return {
        "status": 200,
        "message": "Node created successfully",
        "data": node_service.create_node(node_data),
    }


@router.put("/{node_id}", response_model=dict)
async def update_node(
    node_id: int,
    node_update: NodeUpdate,
    current_user: User = Depends(get_current_user),
    node_service: NodeService = Depends(get_node_service),
):
    """Actualiza un nodo: admin o el líder del propio nodo."""
    return {
        "status": 200,
        "message": "Node updated successfully",
        "data": node_service.update_node(current_user, node_id, node_update),
    }


@router.post("/upload-profile-picture", response_model=dict)
async def upload_node_profile_picture(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    node_service: NodeService = Depends(get_node_service),
):
    """Sube y optimiza la foto de perfil del nodo que lidera el usuario."""
    image_bytes = await image.read()

    return {
        "status": 200,
        "message": "Profile picture uploaded successfully",
        "data": node_service.set_profile_picture(current_user, image_bytes),
    }


@router.post("/upload-memorandum", response_model=dict)
async def upload_node_memorandum(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    node_service: NodeService = Depends(get_node_service),
):
    """Sube el memorando del nodo que lidera el usuario."""
    return {
        "status": 200,
        "message": "Memorandum uploaded successfully",
        "data": node_service.set_memorandum(current_user, file.file, file.filename),
    }


@router.delete("/{node_id}", response_model=dict)
async def delete_node(
    node_id: int,
    current_user: User = Depends(get_current_admin),
    node_service: NodeService = Depends(get_node_service),
):
    """Admin: elimina un nodo."""
    return {
        "status": 200,
        "message": "Node deleted successfully",
        "data": {"id": node_service.delete_node(node_id)},
    }


# ──────────────────────────────────────────────
# Gestión de miembros (bajo /nodes/member/...)
# ──────────────────────────────────────────────

@router.put("/member/{member_id}", response_model=dict)
async def toggle_member_status(
    member_id: int,
    current_user: User = Depends(get_current_user),
    node_service: NodeService = Depends(get_node_service),
):
    """Alterna el estado de un miembro (active/inactive). Admin o líder del nodo."""
    return {
        "status": 200,
        "message": "Member status updated successfully",
        "data": node_service.toggle_member_status(current_user, member_id),
    }


@router.delete("/member/{member_id}", response_model=dict)
async def remove_member_from_node(
    member_id: int,
    current_user: User = Depends(get_current_user),
    node_service: NodeService = Depends(get_node_service),
):
    """Remueve al miembro del nodo (no elimina el usuario, solo la relación)."""
    return {
        "status": 200,
        "message": "Member removed from node successfully",
        "data": {"id": node_service.remove_member(current_user, member_id)},
    }
