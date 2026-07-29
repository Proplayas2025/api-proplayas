"""Lógica de negocio de usuarios: perfil, listado, permisos y estado."""
from fastapi import HTTPException

from core import storage
from core.exceptions import AppError
from core.security import decode_client_password, get_password_hash, verify_password
from enums import SocialPlatform, UserStatus
from models.user import User
from repositories.node_repository import NodeRepository
from repositories.social_link_repository import SocialLinkRepository
from repositories.user_repository import UserRepository
from schemas.auth import ChangePasswordRequest
from schemas.common import Page, PageMeta
from schemas.user import SocialLinkBase, UserListItem, UserResponse, UserUpdate

PASSWORD_MIN_LENGTH = 8


class UserService:
    def __init__(
        self,
        users: UserRepository,
        nodes: NodeRepository,
        social_links: SocialLinkRepository,
    ):
        self.users = users
        self.nodes = nodes
        self.social_links = social_links

    # ── Consultas ──

    def list_users(self, page: int, per_page: int, search: str | None) -> Page[UserListItem]:
        """Listado paginado (admin), enriquecido con el código del nodo."""
        offset = (page - 1) * per_page
        users, total = self.users.search(search=search, offset=offset, limit=per_page)

        items = []
        for user in users:
            item = UserListItem.model_validate(user)
            if user.node_id:
                node = self.nodes.get(user.node_id)
                if node:
                    item.node_code = node.code
            items.append(item)

        return Page(items=items, meta=PageMeta.build(page, per_page, total))

    def get_profile(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    def get_by_id(self, user_id: int) -> UserResponse:
        return UserResponse.model_validate(self._require_user(user_id))

    def get_by_username(self, username: str) -> UserResponse:
        user = self.users.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user)

    # ── Escritura ──

    def update_own_profile(self, current_user: User, payload: UserUpdate) -> UserResponse:
        return self._apply_update(current_user, payload)

    def update_user(self, current_user: User, user_id: int, payload: UserUpdate) -> UserResponse:
        if current_user.id != user_id and current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")

        return self._apply_update(self._require_user(user_id), payload)

    def change_password(self, current_user: User, data: ChangePasswordRequest) -> None:
        current_password = decode_client_password(data.current_password)
        new_password = decode_client_password(data.new_password)
        confirm_new_password = decode_client_password(data.confirm_new_password)

        if not verify_password(current_password, current_user.password):
            raise AppError(400, "La contraseña actual es incorrecta.")

        if new_password != confirm_new_password:
            raise AppError(400, "Las contraseñas nuevas no coinciden.")

        if len(new_password) < PASSWORD_MIN_LENGTH:
            raise AppError(400, f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")

        current_user.password = get_password_hash(new_password)
        self.users.save(current_user)

    def toggle_status(self, current_user: User, user_id: int) -> UserListItem:
        """Alterna el estado activo/inactivo de un usuario (solo admin)."""
        user = self._require_user(user_id)

        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes cambiar tu propio estado")

        user.status = (
            UserStatus.inactive if user.status == UserStatus.active else UserStatus.active
        )
        self.users.save(user)

        return UserListItem.model_validate(user)

    def set_profile_picture(self, current_user: User, image_bytes: bytes) -> UserResponse:
        current_user.profile_picture = storage.save_image(
            image_bytes, storage.PROFILES_DIR, f"user_{current_user.id}_profile"
        )
        self.users.save(current_user)
        return UserResponse.model_validate(current_user)

    def delete_user(self, user_id: int) -> int:
        user = self._require_user(user_id)
        self.users.delete(user)
        return user_id

    # ── Helpers ──

    def _require_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def _apply_update(self, user: User, payload: UserUpdate) -> UserResponse:
        update_data = payload.model_dump(exclude_unset=True, exclude={"social_media"})
        for field, value in update_data.items():
            setattr(user, field, value)

        if payload.social_media is not None:
            self._replace_social_media(user.id, payload.social_media)

        self.users.save(user)
        return UserResponse.model_validate(user)

    def _replace_social_media(self, user_id: int, links: list[SocialLinkBase]) -> None:
        """Reemplaza las redes sociales del usuario, ignorando plataformas desconocidas."""
        self.social_links.delete_by_user(user_id)

        for link in links:
            try:
                platform = SocialPlatform(link.platform)
            except ValueError:
                continue
            self.social_links.create_for_user(user_id, platform, link.url)
