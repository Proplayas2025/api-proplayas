"""Lógica de negocio de invitaciones: envío, validación, aceptación y cancelación."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from jose import JWTError, jwt

from core.config import settings
from core.email import email_service
from core.security import create_access_token, decode_client_password, get_password_hash
from enums import (
    InvitationStatus,
    NodeStatus,
    NodeType,
    SocialPlatform,
    UserRole,
    UserStatus,
)
from models.invitation import Invitation
from models.node import Node
from models.node_member import NodeMember
from models.user import User
from repositories.invitation_repository import InvitationRepository
from repositories.node_member_repository import NodeMemberRepository
from repositories.node_repository import NodeRepository
from repositories.social_link_repository import SocialLinkRepository
from repositories.user_repository import UserRepository
from schemas.common import Result
from schemas.invitation import (
    InvitationResponse,
    InviteNodeLeaderCreate,
    InviteNodeMemberCreate,
)
from services.code_service import CodeService

INVITATION_EXPIRY_DAYS = 7


class InvitationService:
    def __init__(
        self,
        invitations: InvitationRepository,
        users: UserRepository,
        nodes: NodeRepository,
        memberships: NodeMemberRepository,
        social_links: SocialLinkRepository,
        codes: CodeService,
    ):
        self.invitations = invitations
        self.users = users
        self.nodes = nodes
        self.memberships = memberships
        self.social_links = social_links
        self.codes = codes

    # ── Envío de invitaciones ──

    async def invite_node_leader(
        self, current_user: User, data: InviteNodeLeaderCreate
    ) -> InvitationResponse:
        """Admin invita a un líder de nodo; el código del nodo se genera aquí."""
        self._assert_no_pending_invitation(data.email)

        node_code = self.codes.generate_node_code(data.node_type)

        token = self._create_token({
            "name": data.name,
            "email": data.email,
            "role_type": "node_leader",
            "node_type": data.node_type,
            "node_code": node_code,
        })

        invitation = self.invitations.save(
            Invitation(
                name=data.name,
                email=data.email,
                token=token,
                role=UserRole.node_leader,
                node_type=data.node_type,
                status=InvitationStatus.pending,
                invited_by=current_user.id,
            )
        )

        await email_service.send_invitation_email(data.email, token, "node_leader")

        return InvitationResponse.model_validate(invitation)

    async def invite_member(
        self, current_user: User, data: InviteNodeMemberCreate
    ) -> InvitationResponse:
        """El líder invita a un miembro de su nodo."""
        self._assert_no_pending_invitation(data.email)

        node = self.nodes.get_by_leader(current_user.id)
        if not node and current_user.role.value != "admin":
            raise HTTPException(status_code=400, detail="No tienes un nodo asignado")

        token = self._create_token({
            "name": data.name,
            "email": data.email,
            "role_type": "member",
            "node_id": node.id if node else None,
            "node_code": node.code if node else None,
        })

        invitation = self.invitations.save(
            Invitation(
                name=data.name,
                email=data.email,
                token=token,
                role=UserRole.member,
                status=InvitationStatus.pending,
                node_id=node.id if node else None,
                invited_by=current_user.id,
            )
        )

        await email_service.send_invitation_email(data.email, token, "member")

        return InvitationResponse.model_validate(invitation)

    # ── Validación y aceptación ──

    def validate_token(self, token: str) -> Result:
        """Valida una invitación pendiente y devuelve los datos precargados del formulario.

        Devuelve siempre HTTP 200: el frontend interpreta `status` dentro del body.
        """
        invitation = self.invitations.get_pending_by_token(token)

        if not invitation:
            return Result(status=400, message="Invitación inválida o ya utilizada")

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.expired
            self.invitations.commit()
            return Result(status=400, message="La invitación ha expirado")

        payload = self._decode_token(token)

        return Result(
            status=200,
            message="Invitación válida",
            data={
                "name": payload.get("name"),
                "email": payload.get("email"),
                "role_type": payload.get("role_type"),
                "node_type": payload.get("node_type"),
                "node_id": payload.get("node_id"),
            },
        )

    def accept(self, data: dict) -> dict:
        """Registra al usuario invitado y marca la invitación como aceptada."""
        token = data.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Token requerido")

        invitation = self.invitations.get_pending_by_token(token)
        if not invitation:
            raise HTTPException(status_code=400, detail="Invitación inválida o ya utilizada")

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.expired
            self.invitations.commit()
            raise HTTPException(status_code=400, detail="La invitación ha expirado")

        payload = self._decode_token(token)
        role_type = payload.get("role_type")

        if invitation.email != data.get("email"):
            raise HTTPException(status_code=400, detail="El email no coincide con la invitación")

        if self.users.get_by_email(data.get("email")):
            raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")

        password = decode_client_password(data.get("password", ""))

        if role_type == "node_leader":
            result = self._register_node_leader(data, payload, password)
        elif role_type == "member":
            result = self._register_member(data, payload, password)
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de rol no soportado: {role_type}")

        invitation.status = InvitationStatus.accepted
        self.invitations.commit()

        return result

    # ── Listado y cancelación ──

    def list_invitations(
        self, current_user: User, status: InvitationStatus
    ) -> list[InvitationResponse]:
        """Admin ve invitaciones de líderes; un líder solo las de miembros que él envió."""
        role = None
        invited_by = None

        if current_user.role.value == "admin":
            role = UserRole.node_leader
        elif current_user.role.value == "node_leader":
            role = UserRole.member
            invited_by = current_user.id

        invitations = self.invitations.list_by_status(status, role=role, invited_by=invited_by)

        return [InvitationResponse.model_validate(inv) for inv in invitations]

    def cancel(self, current_user: User, invitation_id: int) -> None:
        invitation = self.invitations.get(invitation_id)

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitación no encontrada")

        if current_user.role.value == "node_leader" and invitation.invited_by != current_user.id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para cancelar esta invitación"
            )

        if invitation.status != InvitationStatus.pending:
            raise HTTPException(
                status_code=400, detail="Solo se pueden cancelar invitaciones pendientes"
            )

        self.invitations.delete(invitation)

    # ── Registro ──

    def _register_node_leader(self, data: dict, payload: dict, password: str) -> dict:
        """Crea usuario líder + nodo + membresía del líder."""
        node_type = payload.get("node_type", data.get("node_type"))
        node_code = payload.get("node_code") or self.codes.generate_node_code(node_type)

        username = self._require_available_username(data)

        new_user = self.users.add(
            User(
                name=data.get("name", ""),
                username=username,
                email=data.get("email", ""),
                password=get_password_hash(password),
                role=UserRole.node_leader,
                status=UserStatus.active,
                about=data.get("about_user"),
                degree=data.get("degree"),
                postgraduate=data.get("postgraduate"),
                expertise_area=data.get("expertise_area"),
                research_line=data.get("research_line"),
                country=data.get("country_user"),
                city=data.get("city_user"),
            )
        )

        self._create_social_links(new_user.id, data.get("social_media"), is_node=False)

        new_node = self.nodes.add(
            Node(
                name=data.get("node_name", f"Nodo {node_code}"),
                code=node_code,
                type=NodeType(node_type) if node_type else NodeType.sociedad_civil,
                about=data.get("about_node"),
                country=data.get("country_node"),
                city=data.get("city_node"),
                coordinates=data.get("coordinates"),
                alt_places=data.get("alt_places"),
                joined_in=data.get("joined_in") or datetime.utcnow().year,
                memorandum=data.get("memorandum"),
                leader_id=new_user.id,
                members_count=1,
                status=NodeStatus.active,
            )
        )

        new_user.node_id = new_node.id

        # El líder usa como código de miembro el del propio nodo
        self.memberships.add(
            NodeMember(user_id=new_user.id, node_id=new_node.id, member_code=node_code)
        )

        self._create_social_links(new_node.id, data.get("social_media_node"), is_node=True)

        self.users.flush()

        return {"id": new_user.id, "email": new_user.email, "node_code": node_code}

    def _register_member(self, data: dict, payload: dict, password: str) -> dict:
        """Crea usuario miembro + membresía en el nodo de la invitación."""
        node = None
        if payload.get("node_id"):
            node = self.nodes.get(payload["node_id"])
        if not node and payload.get("node_code"):
            node = self.nodes.get_by_code(payload["node_code"])

        if not node:
            raise HTTPException(status_code=400, detail="Nodo no encontrado para esta invitación")

        member_code = self.codes.generate_member_code(node.code)
        username = self._require_available_username(data)

        new_user = self.users.add(
            User(
                name=data.get("name", ""),
                username=username,
                email=data.get("email", ""),
                password=get_password_hash(password),
                role=UserRole.member,
                status=UserStatus.active,
                about=data.get("about_user"),
                expertise_area=data.get("expertise_area"),
                research_line=data.get("research_line"),
                country=data.get("country_user"),
                city=data.get("city_user"),
                node_id=node.id,
            )
        )

        self._create_social_links(new_user.id, data.get("social_media"), is_node=False)

        self.memberships.add(
            NodeMember(
                user_id=new_user.id,
                node_id=node.id,
                member_code=member_code,
            )
        )

        node.members_count = self.users.count_by_node(node.id)

        self.users.flush()

        return {"id": new_user.id, "email": new_user.email, "member_code": member_code}

    # ── Helpers ──

    def _assert_no_pending_invitation(self, email: str) -> None:
        if self.invitations.get_pending_by_email(email):
            raise HTTPException(
                status_code=400, detail="Ya existe una invitación pendiente para este email"
            )

    def _require_available_username(self, data: dict) -> str:
        username = data.get("username") or data.get("email", "").split("@")[0]

        if self.users.get_by_username(username):
            raise HTTPException(
                status_code=400,
                detail=f"El nombre de usuario '{username}' ya está en uso. Por favor elige otro.",
            )

        return username

    def _create_social_links(self, owner_id: int, social_media: list | None, *, is_node: bool) -> None:
        """Crea las redes sociales de un usuario o nodo, ignorando entradas inválidas."""
        for item in social_media or []:
            if not isinstance(item, dict):
                continue

            platform_str = item.get("platform", "")
            url = item.get("url", "")
            if not platform_str or not url:
                continue

            try:
                platform = SocialPlatform(platform_str)
            except ValueError:
                continue

            if is_node:
                self.social_links.create_for_node(owner_id, platform, url)
            else:
                self.social_links.create_for_user(owner_id, platform, url)

    def _create_token(self, data: dict) -> str:
        return create_access_token(data, expires_delta=timedelta(days=INVITATION_EXPIRY_DAYS))

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=400, detail="Token inválido o expirado")
