from fastapi import APIRouter, Depends

from dependencies import get_auth_service
from schemas.auth import LoginRequest, RecoverPasswordRequest, SetNewPasswordRequest
from services.auth_service import RECOVER_PASSWORD_MESSAGE, AuthService

router = APIRouter(
    tags=["auth"]
)


@router.post("/login", response_model=dict)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Autentica al usuario y devuelve el token de acceso."""
    return {
        "status": 200,
        "message": "Inicio de sesión exitoso",
        "data": auth_service.login(credentials),
    }


@router.post("/logout")
async def logout():
    """Cierre de sesión: el token es stateless, el cliente lo descarta."""
    return {
        "status": 200,
        "message": "Sesión cerrada exitosamente",
        "data": [],
    }


@router.post("/recover-password")
async def recover_password(
    data: RecoverPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Envía el enlace de recuperación de contraseña."""
    await auth_service.recover_password(data.email)

    return {
        "status": 200,
        "message": RECOVER_PASSWORD_MESSAGE,
        "data": None,
    }


@router.post("/set-new-password")
async def set_new_password(
    data: SetNewPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Restablece la contraseña con un token de recuperación."""
    auth_service.set_new_password(data)

    return {
        "status": 200,
        "message": "Tu contraseña ha sido actualizada correctamente.",
        "data": None,
    }
