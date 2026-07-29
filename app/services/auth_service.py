"""Lógica de autenticación: login, recuperación y cambio de contraseña por token."""
from datetime import timedelta

from fastapi import HTTPException

from core.email import email_service
from core.exceptions import AppError
from core.security import (
    create_access_token,
    decode_client_password,
    decode_token,
    get_password_hash,
    verify_password,
)
from repositories.node_repository import NodeRepository
from repositories.user_repository import UserRepository
from schemas.auth import LoginRequest, SetNewPasswordRequest

# Mensaje neutro: no revela si el email está registrado
RECOVER_PASSWORD_MESSAGE = (
    "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."
)
PASSWORD_MIN_LENGTH = 8


class AuthService:
    def __init__(self, users: UserRepository, nodes: NodeRepository):
        self.users = users
        self.nodes = nodes

    def login(self, credentials: LoginRequest) -> dict:
        """Valida credenciales y devuelve token, rol y código del nodo del usuario."""
        password = decode_client_password(credentials.password)
        user = self.users.get_by_email(credentials.email)

        if not user or not verify_password(password, user.password):
            raise AppError(401, "Credenciales incorrectas")

        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value}
        )

        # Se devuelve el código del nodo (ej: "A01"), no el id numérico
        node_code = None
        if user.node_id:
            node = self.nodes.get(user.node_id)
            if node:
                node_code = node.code

        return {
            "token": access_token,
            "role": user.role.value,
            "node_id": node_code,
        }

    async def recover_password(self, email: str) -> None:
        """Envía el enlace de recuperación si el email existe (silencioso si no)."""
        user = self.users.get_by_email(email)
        if not user:
            return

        reset_token = create_access_token(
            data={"sub": user.email, "purpose": "password_reset"},
            expires_delta=timedelta(minutes=30),
        )
        await email_service.send_password_reset_email(user.email, reset_token)

    def set_new_password(self, data: SetNewPasswordRequest) -> None:
        """Restablece la contraseña a partir de un token de recuperación válido."""
        try:
            payload = decode_token(data.token)
        except HTTPException:
            raise AppError(400, "El enlace de recuperación es inválido o ha expirado.")

        if payload.get("purpose") != "password_reset":
            raise AppError(400, "Token inválido.")

        password = decode_client_password(data.password)
        confirm_password = decode_client_password(data.confirm_password)

        if password != confirm_password:
            raise AppError(400, "Las contraseñas no coinciden.")

        if len(password) < PASSWORD_MIN_LENGTH:
            raise AppError(400, f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")

        user = self.users.get_by_email(payload.get("sub"))
        if not user:
            raise AppError(400, "No se pudo encontrar la cuenta asociada.")

        user.password = get_password_hash(password)
        self.users.save(user)
