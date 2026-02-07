from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from base64 import b64decode
from database import get_db
from schemas.auth import LoginRequest, LoginResponse
from core.security import verify_password, create_access_token
from models import User, Node

router = APIRouter(
    tags=["auth"]
)


@router.post("/login", response_model=dict)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        password = b64decode(credentials.password).decode("utf-8")
    except Exception:
        password = credentials.password

    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(password, user.password):
        return {
            "status": 401,
            "message": "Credenciales incorrectas",
            "data": None,
        }

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )

    # Obtener el código del nodo si el usuario tiene uno
    node_code = None
    if user.node_id:
        node = db.query(Node).filter(Node.id == user.node_id).first()
        if node:
            node_code = node.code

    return {
        "status": 200,
        "message": "Inicio de sesión exitoso",
        "data": {
            "token": access_token,
            "role": user.role.value,
            "node_id": node_code,  # Devuelve el código del nodo (ej: "A01") en lugar del ID numérico
        },
    }


@router.post("/logout")
async def logout():
    return {
        "status": 200,
        "message": "Sesión cerrada exitosamente",
        "data": [],
    }


@router.post("/recover-password")
async def recover_password(data: dict):
    # TODO: Implementar envío de email con token de recuperación
    return {
        "status": 501,
        "message": "Funcionalidad de recuperación de contraseña no implementada aún",
        "data": None,
    }


@router.post("/set-new-password")
async def set_new_password(data: dict):
    # TODO: Implementar cambio de contraseña con token
    return {
        "status": 501,
        "message": "Funcionalidad de cambio de contraseña no implementada aún",
        "data": None,
    }
