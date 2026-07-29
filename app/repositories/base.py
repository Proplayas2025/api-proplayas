"""Repositorio base: operaciones CRUD genéricas sobre un modelo ORM.

Los repositorios son *dumb*: solo construyen consultas y persisten. Cualquier
validación o regla de negocio vive en `services/`.
"""
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, entity_id: int) -> ModelT | None:
        return self.db.query(self.model).filter(self.model.id == entity_id).first()

    def list_all(self) -> list[ModelT]:
        return self.db.query(self.model).all()

    def add(self, entity: ModelT) -> ModelT:
        """Agrega la entidad a la sesión y hace flush (sin cerrar la transacción)."""
        self.db.add(entity)
        self.db.flush()
        return entity

    def save(self, entity: ModelT) -> ModelT:
        """Persiste la entidad y refresca su estado desde la BD."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.commit()

    def commit(self) -> None:
        self.db.commit()

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, entity: ModelT) -> None:
        self.db.refresh(entity)
