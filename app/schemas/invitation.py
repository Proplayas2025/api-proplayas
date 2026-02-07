from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from models.user import UserRole
from models.invitation import InvitationStatus


class InviteNodeLeaderCreate(BaseModel):
    """Admin invita líder de nodo: nombre, email, tipo de nodo"""
    name: str
    email: EmailStr
    node_type: str  # sociedad_civil, cientifico, empresarial, etc.
    code: Optional[str] = None  # se genera automáticamente


class InviteNodeMemberCreate(BaseModel):
    """Líder de nodo invita miembro: nombre, email"""
    name: str
    email: EmailStr


class InvitationResponse(BaseModel):
    id: int
    name: Optional[str] = None
    email: EmailStr
    role: UserRole
    node_type: Optional[str] = None
    status: InvitationStatus
    node_id: Optional[int] = None
    invited_by: int
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True


class InvitationValidateResponse(BaseModel):
    name: str
    email: str
    role_type: str
    node_type: Optional[str] = None
    node_id: Optional[int] = None
