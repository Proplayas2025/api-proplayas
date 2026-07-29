from sqlalchemy import or_

from models.node import Node
from repositories.base import BaseRepository


class NodeRepository(BaseRepository[Node]):
    model = Node

    def get_by_code(self, code: str) -> Node | None:
        return self.db.query(Node).filter(Node.code == code).first()

    def get_by_leader(self, leader_id: int) -> Node | None:
        return self.db.query(Node).filter(Node.leader_id == leader_id).first()

    def search(
        self,
        *,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Node], int]:
        """Devuelve (nodos de la página, total que coincide con el filtro)."""
        query = self.db.query(Node)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Node.name.ilike(search_filter),
                    Node.code.ilike(search_filter),
                    Node.country.ilike(search_filter),
                    Node.city.ilike(search_filter),
                )
            )

        return query.offset(offset).limit(limit).all(), query.count()

    def list_codes_with_prefix(self, prefix: str) -> list[str]:
        """Códigos de nodo que empiezan con el prefijo dado (ej. 'A' → A01, A02...)."""
        rows = self.db.query(Node.code).filter(Node.code.like(f"{prefix}%")).all()
        return [code for (code,) in rows]
