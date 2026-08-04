"""Lógica de negocio de nodos: CRUD, archivos y gestión de miembros."""
from typing import BinaryIO

from fastapi import HTTPException

from core import storage
from enums import SocialPlatform, UserStatus
from models.node import Node
from models.user import User
from repositories.node_member_repository import NodeMemberRepository
from repositories.node_repository import NodeRepository
from repositories.social_link_repository import SocialLinkRepository
from repositories.user_repository import UserRepository
from schemas.common import Page, PageMeta
from schemas.node import (
    NodeCreate,
    NodeMemberItem,
    NodeMemberStatus,
    NodeResponse,
    NodeSocialLinkBase,
    NodeUpdate,
)


class NodeService:
    def __init__(
        self,
        nodes: NodeRepository,
        users: UserRepository,
        memberships: NodeMemberRepository,
        social_links: SocialLinkRepository,
    ):
        self.nodes = nodes
        self.users = users
        self.memberships = memberships
        self.social_links = social_links

    # ── Consultas ──

    def list_nodes(self, page: int, per_page: int, search: str | None) -> Page[NodeResponse]:
        offset = (page - 1) * per_page
        nodes, total = self.nodes.search(search=search, offset=offset, limit=per_page)

        return Page(
            items=[NodeResponse.model_validate(node) for node in nodes],
            meta=PageMeta.build(page, per_page, total),
        )

    def get_by_code(self, code: str) -> NodeResponse:
        return NodeResponse.model_validate(self._require_node_by_code(code))

    def list_members(self, code: str) -> list[NodeMemberItem]:
        node = self._require_node_by_code(code)

        return [
            NodeMemberItem(
                id=membership.id,
                user_id=user.id,
                node_id=membership.node_id,
                member_code=membership.member_code,
                name=user.name,
                email=user.email,
                username=user.username,
                research_line=membership.research_line,
                work_area=membership.work_area,
                status=user.status.value,
            )
            for membership, user in self.memberships.list_with_users(node.id)
        ]

    # ── Escritura ──

    def create_node(self, payload: NodeCreate) -> NodeResponse:
        if self.nodes.get_by_code(payload.code):
            raise HTTPException(status_code=400, detail="Node code already exists")

        node = self.nodes.save(Node(**payload.model_dump()))
        return NodeResponse.model_validate(node)

    def update_node(self, current_user: User, node_id: int, payload: NodeUpdate) -> NodeResponse:
        node = self._require_node(node_id)

        if current_user.role.value != "admin" and node.leader_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        update_data = payload.model_dump(exclude_unset=True, exclude={"social_media"})
        for field, value in update_data.items():
            setattr(node, field, value)

        if payload.social_media is not None:
            self._replace_social_media(node.id, payload.social_media)

        self.nodes.save(node)
        return NodeResponse.model_validate(node)

    def set_profile_picture(self, current_user: User, image_bytes: bytes) -> NodeResponse:
        node = self._require_own_node(current_user)

        node.profile_picture = storage.save_image(
            image_bytes, storage.PROFILES_DIR, f"node_{node.id}_profile"
        )
        self.nodes.save(node)
        return NodeResponse.model_validate(node)

    def set_memorandum(self, current_user: User, file: BinaryIO, filename: str | None) -> NodeResponse:
        node = self._require_own_node(current_user)

        extension = storage.extension_of(filename, default="pdf")
        node.memorandum = storage.save_document(
            file, storage.DOCS_DIR, f"node_{node.id}_memorandum.{extension}"
        )
        self.nodes.save(node)
        return NodeResponse.model_validate(node)

    def delete_node(self, node_id: int) -> int:
        node = self._require_node(node_id)
        self.nodes.delete(node)
        return node_id

    def toggle_node_status(self, current_user: User, node_id: int) -> NodeResponse:
        """Alterna el estado del nodo (active ↔ inactive). Solo admin."""
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")

        node = self._require_node(node_id)
        toggled_node = self.nodes.toggle_status(node_id)

        if not toggled_node:
            raise HTTPException(status_code=404, detail="Node not found")

        return NodeResponse.model_validate(toggled_node)

    # ── Miembros ──

    def toggle_member_status(self, current_user: User, member_id: int) -> NodeMemberStatus:
        """Alterna el estado de un miembro. Permitido a admin o al líder de su nodo."""
        member = self._require_member(member_id)

        if current_user.role.value == "node_leader":
            if member.node_id is None:
                raise HTTPException(status_code=404, detail="Member not assigned to any node")
            self._assert_leads_node(current_user, member.node_id)
        elif current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")

        member.status = (
            UserStatus.inactive if member.status == UserStatus.active else UserStatus.active
        )
        self.users.save(member)

        return NodeMemberStatus(
            id=member.id,
            name=member.name,
            email=member.email,
            status=member.status.value,
        )

    def remove_member(self, current_user: User, member_id: int) -> int:
        """Desvincula al miembro de su nodo (no elimina el usuario)."""
        member = self._require_member(member_id)

        if member.node_id is None:
            raise HTTPException(status_code=400, detail="Member not assigned to any node")

        if current_user.role.value == "node_leader":
            self._assert_leads_node(current_user, member.node_id)
        elif current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")

        node_id = member.node_id

        self.memberships.delete_membership(member.id, node_id)
        member.node_id = None
        member.status = UserStatus.inactive

        node = self.nodes.get(node_id)
        if node:
            node.members_count = self.users.count_by_node(node_id)

        self.nodes.commit()
        return member_id

    # ── Helpers ──

    def _require_node(self, node_id: int) -> Node:
        node = self.nodes.get(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        return node

    def _require_node_by_code(self, code: str) -> Node:
        node = self.nodes.get_by_code(code)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        return node

    def _require_member(self, member_id: int) -> User:
        member = self.users.get(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member

    def _require_own_node(self, current_user: User) -> Node:
        """Nodo que lidera el usuario actual (admin y líder solo suben al suyo)."""
        if current_user.role.value not in ("admin", "node_leader"):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        node = self.nodes.get_by_leader(current_user.id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        return node

    def _assert_leads_node(self, current_user: User, node_id: int) -> None:
        node = self.nodes.get(node_id)
        if not node or node.leader_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    def _replace_social_media(self, node_id: int, links: list[NodeSocialLinkBase]) -> None:
        self.social_links.delete_by_node(node_id)

        for link in links:
            self.social_links.create_for_node(node_id, SocialPlatform(link.platform), link.url)
