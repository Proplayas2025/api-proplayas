from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from base64 import b64decode
from database import get_db
from schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from core.security import verify_password, get_password_hash, create_access_token
from models import User, Invitation, InvitationStatus
from datetime import datetime

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login", response_model=dict)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        password = b64decode(credentials.password).decode('utf-8')
    except Exception:
        password = credentials.password
    
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(password, user.password):
        return {
            "status": 401,
            "message": "Credenciales incorrectas",
            "data": None
        }
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    
    return {
        "status": 200,
        "message": "Inicio de sesión exitoso",
        "data": {
            "token": access_token,
            "role": user.role,
            "node_id": user.node_id
        }
    }

@router.post("/register", response_model=dict)
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    invitation = db.query(Invitation).filter(
        Invitation.token == data.invitation_token,
        Invitation.status == InvitationStatus.pending
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation"
        )
    
    if invitation.expires_at < datetime.utcnow():
        invitation.status = InvitationStatus.expired
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )
    
    if invitation.email != data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match invitation"
        )
    
    existing_user = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    try:
        password = b64decode(data.password).decode('utf-8')
    except Exception:
        password = data.password
    
    new_user = User(
        email=data.email,
        name=data.name,
        username=data.username,
        password=get_password_hash(password),
        role=invitation.role,
        node_id=invitation.node_id
    )
    
    db.add(new_user)
    invitation.status = InvitationStatus.accepted
    db.commit()
    db.refresh(new_user)
    
    return {
        "status": 200,
        "message": "Usuario registrado exitosamente",
        "data": {"id": new_user.id, "email": new_user.email}
    }

@router.post("/logout")
async def logout():
    return {
        "status": 200,
        "message": "Logged out successfully",
        "data": []
    }
