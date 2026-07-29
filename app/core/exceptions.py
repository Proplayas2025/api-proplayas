"""Excepciones de negocio.

`AppError` la lanzan los services cuando la respuesta de error debe usar el
envelope estándar de la API (`{status, message, data}`) en vez del `{"detail": ...}`
de FastAPI. El handler se registra en `main.py`.
"""


class AppError(Exception):
    def __init__(self, status_code: int, message: str, data=None):
        self.status_code = status_code
        self.message = message
        self.data = data
        super().__init__(message)
