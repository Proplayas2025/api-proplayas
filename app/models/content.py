from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from datetime import datetime
from models.base import Base
from enums import (
    ContentType, ContentStatus,
    EventType, EventFormat, PublicationType,
)

__all__ = [
    "Content", "Chapter",
    "ContentType", "ContentStatus",
    "EventType", "EventFormat", "PublicationType",
]


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(SQLEnum(ContentType), nullable=False)
    status = Column(SQLEnum(ContentStatus), nullable=False, default=ContentStatus.active)

    cover_image = Column(String(255), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    file_path = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=True)
    link = Column(String(500), nullable=True)

    event_type = Column(SQLEnum(EventType), nullable=True)
    event_format = Column(SQLEnum(EventFormat), nullable=True)
    event_date = Column(DateTime(timezone=False), nullable=True)
    location = Column(String(255), nullable=True)
    participants = Column(PG_ARRAY(String), nullable=True)

    book_author = Column(String(255), nullable=True)
    publication_date = Column(DateTime(timezone=False), nullable=True)
    isbn = Column(String(100), nullable=True)

    publication_type = Column(SQLEnum(PublicationType), nullable=True)
    doi = Column(String(255), nullable=True)
    issn = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)

    author = relationship("User", back_populates="created_content")
    chapters = relationship("Chapter", back_populates="series", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    youtube_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    episode_number = Column(Integer, nullable=True)

    series_id = Column(Integer, ForeignKey("content.id"), nullable=False)

    series = relationship("Content", back_populates="chapters")
