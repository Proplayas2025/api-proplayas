from sqlalchemy import or_

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def search(
        self,
        *,
        search: str | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> tuple[list[User], int]:
        """Devuelve (usuarios de la página, total que coincide con el filtro)."""
        query = self.db.query(User)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_filter),
                    User.email.ilike(search_filter),
                    User.username.ilike(search_filter),
                )
            )

        return query.offset(offset).limit(limit).all(), query.count()

    def count_by_node(self, node_id: int) -> int:
        return self.db.query(User).filter(User.node_id == node_id).count()
