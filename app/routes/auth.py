from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from base64 import b64decode
from database import get_db
from schemas.auth import LoginRequest, LoginResponse, RecoverPasswordRequest, SetNewPasswordRequest
from core.security import verify_password, create_access_token, decode_token, get_password_hash
from core.email import email_service
from core.config import settings
from models import User, Node
from jose import JWTError

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
        return JSONResponse(
            status_code=401,
            content={
                "status": 401,
                "message": "Credenciales incorrectas",
                "data": None,
            }
        )

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
async def recover_password(data: RecoverPasswordRequest, db: Session = Depends(get_db)):
    # Siempre retornar el mismo mensaje para no revelar si el email existe
    success_message = "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."

    user = db.query(User).filter(User.email == data.email).first()

    if user:
        # Generar token con propósito específico y expiración de 30 minutos
        reset_token = create_access_token(
            data={"sub": user.email, "purpose": "password_reset"},
            expires_delta=timedelta(minutes=30)
        )
        await email_service.send_password_reset_email(user.email, reset_token)

    return {
        "status": 200,
        "message": success_message,
        "data": None,
    }


@router.post("/set-new-password")
async def set_new_password(data: SetNewPasswordRequest, db: Session = Depends(get_db)):
    # Validar y decodificar el token
    try:
        payload = decode_token(data.token)
    except HTTPException:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "El enlace de recuperación es inválido o ha expirado.",
                "data": None,
            }
        )

    # Verificar que el token sea de tipo password_reset
    if payload.get("purpose") != "password_reset":
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Token inválido.",
                "data": None,
            }
        )

    # Decodificar contraseñas de base64
    try:
        password = b64decode(data.password).decode("utf-8")
        confirm_password = b64decode(data.confirm_password).decode("utf-8")
    except Exception:
        password = data.password
        confirm_password = data.confirm_password

    # Validar que las contraseñas coincidan
    if password != confirm_password:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Las contraseñas no coinciden.",
                "data": None,
            }
        )

    # Validar longitud mínima
    if len(password) < 8:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "La contraseña debe tener al menos 8 caracteres.",
                "data": None,
            }
        )

    # Buscar usuario por email del token
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "No se pudo encontrar la cuenta asociada.",
                "data": None,
            }
        )

    # Actualizar contraseña
    user.password = get_password_hash(password)
    db.commit()

    return {
        "status": 200,
        "message": "Tu contraseña ha sido actualizada correctamente.",
        "data": None,
    }
