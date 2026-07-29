from sqlalchemy import or_

from enums import ContentStatus, ContentType
from models.content import Content
from repositories.base import BaseRepository


class ContentRepository(BaseRepository[Content]):
    model = Content

    def search(
        self,
        *,
        content_type: ContentType | None = None,
        status: ContentStatus | None = None,
        search: str | None = None,
        author_id: int | None = None,
        offset: int = 0,
        limit: int = 10,
        newest_first: bool = False,
    ) -> tuple[list[Content], int]:
        """Devuelve (contenidos de la página, total que coincide con los filtros)."""
        query = self.db.query(Content)

        if author_id is not None:
            query = query.filter(Content.author_id == author_id)

        if content_type:
            query = query.filter(Content.content_type == content_type)

        if status:
            query = query.filter(Content.status == status)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Content.title.ilike(search_filter),
                    Content.description.ilike(search_filter),
                )
            )

        total = query.count()

        if newest_first:
            query = query.order_by(Content.id.desc())

        return query.offset(offset).limit(limit).all(), total
