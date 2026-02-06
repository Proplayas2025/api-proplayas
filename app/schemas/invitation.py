from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from models.user import UserRole
from models.invitation import InvitationStatus

class InvitationCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    role: UserRole
    node_id: Optional[int] = None
    node_type: Optional[str] = None

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

class InvitationValidate(BaseModel):
    token: str
