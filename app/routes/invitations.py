from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
from database import get_db
from schemas.invitation import InvitationCreate, InvitationResponse, InvitationValidate
from models import Invitation, User, InvitationStatus
from core.security import get_current_user, get_current_node_leader
from core.email import email_service

router = APIRouter(
    prefix="/invitations",
    tags=["invitations"]
)

@router.post("/invitation", response_model=dict)
async def create_invitation(
    invitation_data: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_node_leader)
):
    if current_user.role == "node_leader" and invitation_data.role != "member":
        raise HTTPException(
            status_code=403,
            detail="Node leaders can only invite members"
        )
    
    if current_user.role == "node_leader" and invitation_data.node_id != current_user.node_id:
        raise HTTPException(
            status_code=403,
            detail="Node leaders can only invite to their own node"
        )
    
    existing = db.query(Invitation).filter(
        Invitation.email == invitation_data.email,
        Invitation.status == InvitationStatus.pending
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already has a pending invitation"
        )
    
    token = secrets.token_urlsafe(32)
    
    new_invitation = Invitation(
        email=invitation_data.email,
        token=token,
        role=invitation_data.role,
        node_id=invitation_data.node_id,
        invited_by=current_user.id
    )
    
    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    
    await email_service.send_invitation_email(
        invitation_data.email,
        token,
        invitation_data.role
    )
    
    return {
        "status": 200,
        "message": "Invitation sent successfully",
        "data": InvitationResponse.from_orm(new_invitation)
    }

@router.post("/invitation/validate", response_model=dict)
async def validate_invitation(
    data: InvitationValidate,
    db: Session = Depends(get_db)
):
    invitation = db.query(Invitation).filter(
        Invitation.token == data.token,
        Invitation.status == InvitationStatus.pending
    ).first()
    
    if not invitation:
        return {
            "status": 400,
            "message": "Invalid or expired invitation",
            "data": None
        }
    
    if invitation.expires_at < datetime.utcnow():
        invitation.status = InvitationStatus.expired
        db.commit()
        return {
            "status": 400,
            "message": "Invitation has expired",
            "data": None
        }
    
    return {
        "status": 200,
        "message": "Invitation is valid",
        "data": {
            "email": invitation.email,
            "role": invitation.role,
            "node_id": invitation.node_id
        }
    }

@router.get("/invitations", response_model=dict)
async def get_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_node_leader)
):
    query = db.query(Invitation)
    
    if current_user.role == "node_leader":
        query = query.filter(Invitation.invited_by == current_user.id)
    
    invitations = query.all()
    
    return {
        "status": 200,
        "message": "Invitations retrieved successfully",
        "data": [InvitationResponse.from_orm(inv) for inv in invitations]
    }
