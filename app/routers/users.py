from fastapi import APIRouter, Depends, File, Query, UploadFile

from core.security import get_current_admin, get_current_user
from dependencies import get_user_service
from models import User
from schemas.auth import ChangePasswordRequest
from schemas.user import UserUpdate
from services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("", response_model=dict)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    current_user: User = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    """Admin: listado paginado de usuarios con búsqueda por nombre, email o username."""
    page_result = user_service.list_users(page, per_page, search)

    return {
        "status": 200,
        "message": "Users retrieved successfully",
        "data": page_result.items,
        "meta": page_result.meta,
    }


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Perfil del usuario autenticado."""
    return {
        "status": 200,
        "message": "User profile retrieved successfully",
        "data": user_service.get_profile(current_user),
    }


@router.put("/me", response_model=dict)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Actualiza el perfil propio, incluidas sus redes sociales."""
    return {
        "status": 200,
        "message": "Profile updated successfully",
        "data": user_service.update_own_profile(current_user, user_update),
    }


@router.put("/me/change-password", response_model=dict)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Cambia la contraseña del usuario autenticado."""
    user_service.change_password(current_user, data)

    return {
        "status": 200,
        "message": "Contraseña actualizada correctamente.",
        "data": None,
    }


@router.get("/profile/{username}", response_model=dict)
async def get_public_profile(
    username: str,
    user_service: UserService = Depends(get_user_service),
):
    """Perfil público de un usuario por username."""
    return {
        "status": 200,
        "message": "User profile retrieved successfully",
        "data": user_service.get_by_username(username),
    }


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Detalle de un usuario por id."""
    return {
        "status": 200,
        "message": "User retrieved successfully",
        "data": user_service.get_by_id(user_id),
    }


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Actualiza un usuario: solo el propio dueño o un admin."""
    return {
        "status": 200,
        "message": "User updated successfully",
        "data": user_service.update_user(current_user, user_id, user_update),
    }


@router.put("/{user_id}/toggle-status", response_model=dict)
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    """Admin: alterna el estado de un usuario entre active/inactive."""
    return {
        "status": 200,
        "message": "User status updated successfully",
        "data": user_service.toggle_status(current_user, user_id),
    }


@router.post("/upload-profile-picture", response_model=dict)
async def upload_user_profile_picture(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Sube y optimiza la foto de perfil del usuario autenticado."""
    image_bytes = await image.read()

    return {
        "status": 200,
        "message": "Profile picture uploaded successfully",
        "data": user_service.set_profile_picture(current_user, image_bytes),
    }


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    """Admin: elimina un usuario."""
    return {
        "status": 200,
        "message": "User deleted successfully",
        "data": {"id": user_service.delete_user(user_id)},
    }
