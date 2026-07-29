"""Inyección de dependencias: sesión → repositorios → servicios.

Los routers solo dependen de los `get_*_service`; nunca construyen repositorios
ni tocan la sesión de SQLAlchemy directamente.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from repositories.content_repository import ContentRepository
from repositories.invitation_repository import InvitationRepository
from repositories.node_member_repository import NodeMemberRepository
from repositories.node_repository import NodeRepository
from repositories.social_link_repository import SocialLinkRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.code_service import CodeService
from services.content_service import ContentService
from services.invitation_service import InvitationService
from services.node_service import NodeService
from services.user_service import UserService


# ── Repositorios ──

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_node_repository(db: Session = Depends(get_db)) -> NodeRepository:
    return NodeRepository(db)


def get_node_member_repository(db: Session = Depends(get_db)) -> NodeMemberRepository:
    return NodeMemberRepository(db)


def get_social_link_repository(db: Session = Depends(get_db)) -> SocialLinkRepository:
    return SocialLinkRepository(db)


def get_content_repository(db: Session = Depends(get_db)) -> ContentRepository:
    return ContentRepository(db)


def get_invitation_repository(db: Session = Depends(get_db)) -> InvitationRepository:
    return InvitationRepository(db)


# ── Servicios ──

def get_code_service(
    nodes: NodeRepository = Depends(get_node_repository),
    memberships: NodeMemberRepository = Depends(get_node_member_repository),
) -> CodeService:
    return CodeService(nodes, memberships)


def get_auth_service(
    users: UserRepository = Depends(get_user_repository),
    nodes: NodeRepository = Depends(get_node_repository),
) -> AuthService:
    return AuthService(users, nodes)


def get_user_service(
    users: UserRepository = Depends(get_user_repository),
    nodes: NodeRepository = Depends(get_node_repository),
    social_links: SocialLinkRepository = Depends(get_social_link_repository),
) -> UserService:
    return UserService(users, nodes, social_links)


def get_node_service(
    nodes: NodeRepository = Depends(get_node_repository),
    users: UserRepository = Depends(get_user_repository),
    memberships: NodeMemberRepository = Depends(get_node_member_repository),
    social_links: SocialLinkRepository = Depends(get_social_link_repository),
) -> NodeService:
    return NodeService(nodes, users, memberships, social_links)


def get_content_service(
    contents: ContentRepository = Depends(get_content_repository),
) -> ContentService:
    return ContentService(contents)


def get_invitation_service(
    invitations: InvitationRepository = Depends(get_invitation_repository),
    users: UserRepository = Depends(get_user_repository),
    nodes: NodeRepository = Depends(get_node_repository),
    memberships: NodeMemberRepository = Depends(get_node_member_repository),
    social_links: SocialLinkRepository = Depends(get_social_link_repository),
    codes: CodeService = Depends(get_code_service),
) -> InvitationService:
    return InvitationService(invitations, users, nodes, memberships, social_links, codes)
