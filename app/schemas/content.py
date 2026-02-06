from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.content import (
    ContentType, ContentStatus,
    EventType, EventFormat, PublicationType
)

class ChapterBase(BaseModel):
    title: str
    description: Optional[str] = None
    youtube_url: str
    thumbnail_url: Optional[str] = None
    episode_number: Optional[int] = None

class ChapterCreate(ChapterBase):
    pass

class ChapterResponse(ChapterBase):
    id: int
    series_id: int
    
    class Config:
        from_attributes = True

class ContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: ContentType
    link: Optional[str] = None
    location: Optional[str] = None

class ContentCreate(ContentBase):
    node_id: Optional[int] = None
    event_type: Optional[EventType] = None
    event_format: Optional[EventFormat] = None
    event_date: Optional[datetime] = None
    participants: Optional[List[str]] = None
    book_author: Optional[str] = None
    publication_date: Optional[datetime] = None
    isbn: Optional[str] = None
    publication_type: Optional[PublicationType] = None
    doi: Optional[str] = None
    issn: Optional[str] = None

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ContentStatus] = None
    link: Optional[str] = None
    location: Optional[str] = None
    cover_image: Optional[str] = None
    cover_image_url: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    event_type: Optional[EventType] = None
    event_format: Optional[EventFormat] = None
    event_date: Optional[datetime] = None
    participants: Optional[List[str]] = None
    book_author: Optional[str] = None
    publication_date: Optional[datetime] = None
    isbn: Optional[str] = None
    publication_type: Optional[PublicationType] = None
    doi: Optional[str] = None
    issn: Optional[str] = None

class AuthorInfo(BaseModel):
    id: int
    name: str
    username: str
    email: str
    role: str
    status: str
    
    class Config:
        from_attributes = True

class ContentResponse(ContentBase):
    id: int
    status: ContentStatus
    cover_image: Optional[str] = None
    cover_image_url: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    event_type: Optional[EventType] = None
    event_format: Optional[EventFormat] = None
    event_date: Optional[datetime] = None
    participants: Optional[List[str]] = None
    book_author: Optional[str] = None
    publication_date: Optional[datetime] = None
    isbn: Optional[str] = None
    publication_type: Optional[PublicationType] = None
    doi: Optional[str] = None
    issn: Optional[str] = None
    author_id: int
    node_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    author: Optional[AuthorInfo] = None
    chapters: List[ChapterResponse] = []
    
    class Config:
        from_attributes = True
