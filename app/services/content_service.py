"""Lógica de negocio de contenidos: listados, autoría, permisos y archivos."""
from typing import BinaryIO

from fastapi import HTTPException

from core import storage
from enums import ContentStatus, ContentType
from models.content import Content
from models.user import User
from repositories.content_repository import ContentRepository
from schemas.common import Page, PageMeta
from schemas.content import ContentCreate, ContentResponse, ContentUpdate

# Roles que pueden editar contenido ajeno
CONTENT_MODERATOR_ROLES = ("admin", "node_leader")


class ContentService:
    def __init__(self, contents: ContentRepository):
        self.contents = contents

    # ── Consultas ──

    def list_all(
        self,
        *,
        content_type: ContentType | None,
        search: str | None,
        page: int,
        per_page: int,
    ) -> Page[ContentResponse]:
        """Listado de admin: todo el contenido, sin filtrar por autor ni estado."""
        return self._paginate(
            page,
            per_page,
            content_type=content_type,
            search=search,
            newest_first=True,
        )

    def list_public(
        self,
        *,
        content_type: ContentType | None,
        status: ContentStatus | None,
        search: str | None,
        page: int,
        per_page: int,
    ) -> Page[ContentResponse]:
        """Listado público: por defecto solo contenido activo."""
        return self._paginate(
            page,
            per_page,
            content_type=content_type,
            status=status or ContentStatus.active,
            search=search,
        )

    def list_own(
        self,
        current_user: User,
        *,
        content_type: ContentType | None,
        page: int,
        per_page: int,
    ) -> Page[ContentResponse]:
        return self._paginate(
            page,
            per_page,
            content_type=content_type,
            author_id=current_user.id,
        )

    def get(self, content_id: int) -> ContentResponse:
        return ContentResponse.model_validate(self._require_content(content_id))

    # ── Escritura ──

    def create(self, current_user: User, payload: ContentCreate) -> ContentResponse:
        content = self.contents.save(
            Content(**payload.model_dump(), author_id=current_user.id)
        )
        return ContentResponse.model_validate(content)

    def update(self, current_user: User, content_id: int, payload: ContentUpdate) -> ContentResponse:
        content = self._require_editable(current_user, content_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(content, field, value)

        self.contents.save(content)
        return ContentResponse.model_validate(content)

    def toggle_status(self, current_user: User, content_id: int) -> ContentResponse:
        content = self._require_editable(current_user, content_id)

        content.status = (
            ContentStatus.inactive
            if content.status == ContentStatus.active
            else ContentStatus.active
        )
        self.contents.save(content)
        return ContentResponse.model_validate(content)

    def attach_file(
        self, current_user: User, content_id: int, file: BinaryIO, filename: str | None
    ) -> ContentResponse:
        content = self._require_editable(current_user, content_id)

        saved_name = storage.save_document(
            file, storage.DOCS_DIR, f"content_{content_id}_{filename}"
        )
        content.file_path = saved_name
        content.file_url = saved_name

        self.contents.save(content)
        return ContentResponse.model_validate(content)

    def set_cover_image(self, current_user: User, content_id: int, image_bytes: bytes) -> ContentResponse:
        content = self._require_editable(current_user, content_id)

        content.cover_image = storage.save_image(
            image_bytes, storage.COVERS_DIR, f"content_{content_id}_cover"
        )
        content.cover_image_url = None

        self.contents.save(content)
        return ContentResponse.model_validate(content)

    def delete(self, current_user: User, content_id: int) -> int:
        content = self._require_content(content_id)

        # Borrar es más restrictivo que editar: solo el autor o un admin
        if content.author_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")

        self.contents.delete(content)
        return content_id

    # ── Helpers ──

    def _paginate(self, page: int, per_page: int, **filters) -> Page[ContentResponse]:
        offset = (page - 1) * per_page
        contents, total = self.contents.search(offset=offset, limit=per_page, **filters)

        return Page(
            items=[ContentResponse.model_validate(c) for c in contents],
            meta=PageMeta.build(page, per_page, total),
        )

    def _require_content(self, content_id: int) -> Content:
        content = self.contents.get(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        return content

    def _require_editable(self, current_user: User, content_id: int) -> Content:
        content = self._require_content(content_id)

        if (
            content.author_id != current_user.id
            and current_user.role.value not in CONTENT_MODERATOR_ROLES
        ):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        return content
