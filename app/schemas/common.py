"""Schemas transversales compartidos por todos los recursos."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

ItemT = TypeVar("ItemT")


class Result(BaseModel):
    """Resultado de negocio que viaja con HTTP 200 aunque represente un fallo.

    Se usa solo donde el frontend ya interpreta `status` dentro del body
    (ej. validación de invitaciones), para no romper ese contrato.
    """

    status: int
    message: str
    data: Any = None


class PageMeta(BaseModel):
    """Metadatos de paginación devueltos en la clave `meta` del envelope."""

    current_page: int
    per_page: int
    total: int
    last_page: int

    @classmethod
    def build(cls, page: int, per_page: int, total: int) -> "PageMeta":
        return cls(
            current_page=page,
            per_page=per_page,
            total=total,
            last_page=(total + per_page - 1) // per_page,
        )


class Page(BaseModel, Generic[ItemT]):
    """Resultado paginado que devuelven los services de listado."""

    items: list[ItemT]
    meta: PageMeta
