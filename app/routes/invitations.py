from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
from database import get_db
from schemas.invitation import (
    InviteNodeLeaderCreate,
    InviteNodeMemberCreate,
    InvitationResponse,
    InvitationValidateResponse,
)
from schemas.auth import RegisterNodeLeaderRequest, RegisterNodeMemberRequest
from models import (
    Invitation, User, Node, NodeMember,
    InvitationStatus, SocialLink, NodeSocialLink,
)
from models.user import UserRole, UserStatus
from models.node import NodeType, NodeStatus
from models.social_link import SocialPlatform
from core.security import (
    get_current_user, get_current_admin, get_current_node_leader,
    get_password_hash,
)
from core.config import settings
from core.codes import generate_node_code, generate_member_code
from core.email import email_service
from base64 import b64decode

router = APIRouter(
    prefix="/invitations",
    tags=["invitations"]
)


def _create_invitation_token(data: dict) -> str:
    """Crea un JWT con los datos de la invitación."""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_invitation_token(token: str) -> dict:
    """Decodifica y valida un JWT de invitación."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")


# ──────────────────────────────────────────────
# Admin invita líder de nodo
# POST /api/invitations/node-leader
# ──────────────────────────────────────────────
@router.post("/node-leader", response_model=dict)
async def invite_node_leader(
    data: InviteNodeLeaderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    # Verificar que no exista invitación pendiente para este email
    existing = db.query(Invitation).filter(
        Invitation.email == data.email,
        Invitation.status == InvitationStatus.pending,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una invitación pendiente para este email")

    # Generar código de nodo automáticamente
    node_code = generate_node_code(db, data.node_type)

    # Crear JWT token con datos de la invitación
    token = _create_invitation_token({
        "name": data.name,
        "email": data.email,
        "role_type": "node_leader",
        "node_type": data.node_type,
        "node_code": node_code,
    })

    # Guardar invitación en BD
    invitation = Invitation(
        name=data.name,
        email=data.email,
        token=token,
        role=UserRole.node_leader,
        node_type=data.node_type,
        status=InvitationStatus.pending,
        invited_by=current_user.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Enviar email
    await email_service.send_invitation_email(data.email, token, "node_leader")

    return {
        "status": 200,
        "message": "Invitación enviada exitosamente",
        "data": InvitationResponse.from_orm(invitation),
    }


# ──────────────────────────────────────────────
# Líder de nodo invita miembro
# POST /api/invitations/member
# ──────────────────────────────────────────────
@router.post("/member", response_model=dict)
async def invite_member(
    data: InviteNodeMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_node_leader),
):
    # Verificar que no exista invitación pendiente
    existing = db.query(Invitation).filter(
        Invitation.email == data.email,
        Invitation.status == InvitationStatus.pending,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una invitación pendiente para este email")

    # Obtener el nodo del líder
    node = db.query(Node).filter(Node.leader_id == current_user.id).first()
    if not node and current_user.role.value != "admin":
        raise HTTPException(status_code=400, detail="No tienes un nodo asignado")

    # Crear JWT token
    token = _create_invitation_token({
        "name": data.name,
        "email": data.email,
        "role_type": "member",
        "node_id": node.id if node else None,
        "node_code": node.code if node else None,
    })

    # Guardar invitación en BD
    invitation = Invitation(
        name=data.name,
        email=data.email,
        token=token,
        role=UserRole.member,
        status=InvitationStatus.pending,
        node_id=node.id if node else None,
        invited_by=current_user.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Enviar email
    await email_service.send_invitation_email(data.email, token, "member")

    return {
        "status": 200,
        "message": "Invitación enviada exitosamente",
        "data": InvitationResponse.from_orm(invitation),
    }


# ──────────────────────────────────────────────
# Validar token de invitación
# GET /api/invitations/{token}
# ──────────────────────────────────────────────
@router.get("/{token}", response_model=dict)
async def validate_invitation(
    token: str,
    db: Session = Depends(get_db),
):
    # Verificar que la invitación existe en BD
    invitation = db.query(Invitation).filter(
        Invitation.token == token,
        Invitation.status == InvitationStatus.pending,
    ).first()

    if not invitation:
        return {
            "status": 400,
            "message": "Invitación inválida o ya utilizada",
            "data": None,
        }

    if invitation.expires_at < datetime.utcnow():
        invitation.status = InvitationStatus.expired
        db.commit()
        return {
            "status": 400,
            "message": "La invitación ha expirado",
            "data": None,
        }

    # Decodificar JWT para devolver datos al frontend
    payload = _decode_invitation_token(token)

    return {
        "status": 200,
        "message": "Invitación válida",
        "data": {
            "name": payload.get("name"),
            "email": payload.get("email"),
            "role_type": payload.get("role_type"),
            "node_type": payload.get("node_type"),
            "node_id": payload.get("node_id"),
        },
    }


# ──────────────────────────────────────────────
# Aceptar invitación y registrar usuario
# POST /api/invitations/accept
# ──────────────────────────────────────────────
@router.post("/accept", response_model=dict)
async def accept_invitation(
    data: dict,
    db: Session = Depends(get_db),
):
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token requerido")

    # Validar invitación en BD
    invitation = db.query(Invitation).filter(
        Invitation.token == token,
        Invitation.status == InvitationStatus.pending,
    ).first()

    if not invitation:
        raise HTTPException(status_code=400, detail="Invitación inválida o ya utilizada")

    if invitation.expires_at < datetime.utcnow():
        invitation.status = InvitationStatus.expired
        db.commit()
        raise HTTPException(status_code=400, detail="La invitación ha expirado")

    # Decodificar token para obtener datos originales
    payload = _decode_invitation_token(token)
    role_type = payload.get("role_type")

    # Verificar que el email coincide
    if invitation.email != data.get("email"):
        raise HTTPException(status_code=400, detail="El email no coincide con la invitación")

    # Verificar que no exista usuario con ese email
    existing_user = db.query(User).filter(User.email == data.get("email")).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")

    # Decodificar contraseña (viene en base64 desde el frontend)
    password = data.get("password", "")
    try:
        password = b64decode(password).decode("utf-8")
    except Exception:
        pass

    if role_type == "node_leader":
        result = _register_node_leader(db, data, payload, password)
    elif role_type == "member":
        result = _register_member(db, data, payload, password)
    else:
        raise HTTPException(status_code=400, detail=f"Tipo de rol no soportado: {role_type}")

    # Marcar invitación como aceptada
    invitation.status = InvitationStatus.accepted
    db.commit()

    return {
        "status": 201,
        "message": "Registro exitoso",
        "data": result,
    }


def _register_node_leader(db: Session, data: dict, payload: dict, password: str) -> dict:
    """Registra un líder de nodo: crea usuario + nodo + NodeMember."""
    node_type = payload.get("node_type", data.get("node_type"))
    node_code = payload.get("node_code") or generate_node_code(db, node_type)

    # Crear el usuario
    username = data.get("username") or data.get("email", "").split("@")[0]

    # Verificar que el username no esté en uso
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        return {
            "status":400,
            "message":"El nombre de usuario '{username}' ya está en uso. Por favor elige otro.",
            "data":[]
        }
        

    new_user = User(
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
        research_work=data.get("research_work"),
        country=data.get("country_user"),
        city=data.get("city_user"),
    )
    db.add(new_user)
    db.flush()

    # Crear redes sociales del usuario
    _create_social_links(db, new_user.id, data.get("social_media"), is_node=False)

    # Crear el nodo
    new_node = Node(
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
    db.add(new_node)
    db.flush()

    # Asignar nodo al usuario
    new_user.node_id = new_node.id

    # Crear registro NodeMember para el líder (su código = código del nodo)
    leader_member = NodeMember(
        user_id=new_user.id,
        node_id=new_node.id,
        member_code=node_code,
    )
    db.add(leader_member)

    # Crear redes sociales del nodo
    _create_social_links(db, new_node.id, data.get("social_media_node"), is_node=True)

    db.flush()

    return {"id": new_user.id, "email": new_user.email, "node_code": node_code}


def _register_member(db: Session, data: dict, payload: dict, password: str) -> dict:
    """Registra un miembro: crea usuario + NodeMember."""
    node_id = payload.get("node_id")
    node_code = payload.get("node_code")

    node = None
    if node_id:
        node = db.query(Node).filter(Node.id == node_id).first()
    if not node and node_code:
        node = db.query(Node).filter(Node.code == node_code).first()

    if not node:
        raise HTTPException(status_code=400, detail="Nodo no encontrado para esta invitación")

    # Generar código de miembro (A01-1, A01-2, etc.)
    member_code = generate_member_code(db, node.code)

    # Verificar que el username no esté en uso
    username = data.get("username") or data.get("email", "").split("@")[0]
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail = f"El nombre de usuario '{username}' ya está en uso. Por favor elige otro."
        )
        
        
    # Crear usuario
    new_user = User(
        name=data.get("name", ""),
        username=username,
        email=data.get("email", ""),
        password=get_password_hash(password),
        role=UserRole.member,
        status=UserStatus.active,
        about=data.get("about_user"),
        expertise_area=data.get("expertise_area"),
        research_work=data.get("research_work"),
        country=data.get("country_user"),
        city=data.get("city_user"),
        node_id=node.id,
    )
    db.add(new_user)
    db.flush()

    # Crear redes sociales del usuario
    _create_social_links(db, new_user.id, data.get("social_media"), is_node=False)

    # Crear registro NodeMember
    node_member = NodeMember(
        user_id=new_user.id,
        node_id=node.id,
        member_code=member_code,
        research_line=data.get("research_work"),
        work_area=data.get("expertise_area"),
    )
    db.add(node_member)

    # Actualizar contador de miembros
    node.members_count = db.query(User).filter(User.node_id == node.id).count()

    db.flush()

    return {"id": new_user.id, "email": new_user.email, "member_code": member_code}


def _create_social_links(db: Session, owner_id: int, social_media: list | None, is_node: bool = False):
    """Crea registros de redes sociales para un usuario o nodo."""
    if not social_media:
        return
    
    for item in social_media:
        if isinstance(item, dict):
            platform_str = item.get("platform", "")
            url = item.get("url", "")
        else:
            continue

        if not platform_str or not url:
            continue

        try:
            platform = SocialPlatform(platform_str)
        except ValueError:
            continue

        if is_node:
            link = NodeSocialLink(platform=platform, url=url, node_id=owner_id)
        else:
            link = SocialLink(platform=platform, url=url, user_id=owner_id)
        db.add(link)


# ──────────────────────────────────────────────
# Listar invitaciones
# GET /api/invitations
# ──────────────────────────────────────────────
@router.get("", response_model=dict)
async def get_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_node_leader),
):
    query = db.query(Invitation)

    # Node leader solo ve las que él envió
    if current_user.role.value == "node_leader":
        query = query.filter(Invitation.invited_by == current_user.id)

    invitations = query.order_by(Invitation.created_at.desc()).all()

    return {
        "status": 200,
        "message": "Invitaciones obtenidas exitosamente",
        "data": [InvitationResponse.from_orm(inv) for inv in invitations],
    }
