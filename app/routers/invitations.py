from fastapi import APIRouter, Depends

from core.security import get_current_admin, get_current_node_leader
from dependencies import get_invitation_service
from enums import InvitationStatus
from models import User
from schemas.invitation import InviteNodeLeaderCreate, InviteNodeMemberCreate
from services.invitation_service import InvitationService

router = APIRouter(
    prefix="/invitations",
    tags=["invitations"]
)


@router.post("/node-leader", response_model=dict)
async def invite_node_leader(
    data: InviteNodeLeaderCreate,
    current_user: User = Depends(get_current_admin),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """Admin: invita a un líder de nodo y envía el email con el token."""
    invitation = await invitation_service.invite_node_leader(current_user, data)

    return {
        "status": 200,
        "message": "Invitación enviada exitosamente",
        "data": invitation,
    }


@router.post("/member", response_model=dict)
async def invite_member(
    data: InviteNodeMemberCreate,
    current_user: User = Depends(get_current_node_leader),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """Líder de nodo: invita a un miembro a su nodo."""
    invitation = await invitation_service.invite_member(current_user, data)

    return {
        "status": 200,
        "message": "Invitación enviada exitosamente",
        "data": invitation,
    }


@router.get("", response_model=dict)
async def get_invitations(
    status: InvitationStatus = InvitationStatus.pending,
    current_user: User = Depends(get_current_node_leader),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """Invitaciones visibles para el usuario según su rol."""
    return {
        "status": 200,
        "message": "Invitaciones obtenidas exitosamente",
        "data": invitation_service.list_invitations(current_user, status),
    }


@router.post("/accept", response_model=dict)
async def accept_invitation(
    data: dict,
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """Registra al usuario invitado y consume la invitación."""
    return {
        "status": 201,
        "message": "Registro exitoso",
        "data": invitation_service.accept(data),
    }


@router.get("/{token}", response_model=dict)
async def validate_invitation(
    token: str,
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """Valida un token de invitación y devuelve los datos para precargar el registro."""
    return invitation_service.validate_token(token).model_dump()


@router.delete("/{invitation_id}", response_model=dict)
async def cancel_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_node_leader),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """Cancela una invitación pendiente."""
    invitation_service.cancel(current_user, invitation_id)

    return {
        "status": 200,
        "message": "Invitación cancelada exitosamente",
        "data": None,
    }
