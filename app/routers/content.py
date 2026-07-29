from fastapi import APIRouter, Depends, File, Query, UploadFile

from core.security import get_current_admin, get_current_user
from dependencies import get_content_service
from enums import ContentStatus, ContentType
from models import User
from schemas.content import ContentCreate, ContentUpdate
from services.content_service import ContentService

router = APIRouter(
    prefix="/content",
    tags=["content"]
)


@router.get("/all", response_model=dict)
async def get_all_content(
    content_type: ContentType | None = None,
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    content_service: ContentService = Depends(get_content_service),
):
    """Admin: todo el contenido, sin importar autor ni estado."""
    page_result = content_service.list_all(
        content_type=content_type, search=search, page=page, per_page=per_page
    )

    return {
        "status": 200,
        "message": "All content retrieved successfully",
        "data": page_result.items,
        "meta": page_result.meta,
    }


@router.get("", response_model=dict)
async def get_content(
    content_type: ContentType | None = None,
    status: ContentStatus | None = None,
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    content_service: ContentService = Depends(get_content_service),
):
    """Vista pública: contenido activo por defecto."""
    page_result = content_service.list_public(
        content_type=content_type,
        status=status,
        search=search,
        page=page,
        per_page=per_page,
    )

    return {
        "status": 200,
        "message": "Content retrieved successfully",
        "data": page_result.items,
        "meta": page_result.meta,
    }


@router.get("/own", response_model=dict)
async def get_own_content(
    content_type: ContentType | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
):
    """Contenido creado por el usuario autenticado."""
    page_result = content_service.list_own(
        current_user, content_type=content_type, page=page, per_page=per_page
    )

    return {
        "status": 200,
        "message": "Content retrieved successfully",
        "data": page_result.items,
        "meta": page_result.meta,
    }


@router.get("/{content_id}", response_model=dict)
async def get_content_by_id(
    content_id: int,
    content_service: ContentService = Depends(get_content_service),
):
    """Detalle de un contenido."""
    return {
        "status": 200,
        "message": "Content retrieved successfully",
        "data": content_service.get(content_id),
    }


@router.post("", response_model=dict)
async def create_content(
    content_data: ContentCreate,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
):
    """Crea contenido con el usuario autenticado como autor."""
    return {
        "status": 200,
        "message": "Content created successfully",
        "data": content_service.create(current_user, content_data),
    }


@router.put("/{content_id}/toggle-status", response_model=dict)
async def toggle_content_status(
    content_id: int,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
):
    """Alterna el estado del contenido entre active/inactive."""
    return {
        "status": 200,
        "message": "Content status updated successfully",
        "data": content_service.toggle_status(current_user, content_id),
    }


@router.put("/{content_id}", response_model=dict)
async def update_content(
    content_id: int,
    content_update: ContentUpdate,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
):
    """Actualiza contenido: autor, admin o líder de nodo."""
    return {
        "status": 200,
        "message": "Content updated successfully",
        "data": content_service.update(current_user, content_id, content_update),
    }


@router.post("/{content_id}/upload-file", response_model=dict)
async def upload_file(
    content_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
):
    """Adjunta un documento al contenido."""
    return {
        "status": 200,
        "message": "File uploaded successfully",
        "data": content_service.attach_file(current_user, content_id, file.file, file.filename),
    }


@router.post("/{content_id}/upload-cover-image", response_model=dict)
async def upload_cover_image(
    content_id: int,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
):
    """Sube y optimiza la imagen de portada del contenido."""
    image_bytes = await image.read()

    return {
        "status": 200,
        "message": "Cover image uploaded successfully",
        "data": content_service.set_cover_image(current_user, content_id, image_bytes),
    }


@router.delete("/{content_id}", response_model=dict)
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
):
    """Elimina contenido: solo el autor o un admin."""
    return {
        "status": 200,
        "message": "Content deleted successfully",
        "data": {"id": content_service.delete(current_user, content_id)},
    }
