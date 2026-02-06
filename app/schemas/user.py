from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models.user import UserRole, UserStatus

class SocialLinkBase(BaseModel):
    platform: str
    url: str

class SocialLinkCreate(SocialLinkBase):
    pass

class SocialLink(SocialLinkBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    name: str
    username: str

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.member
    node_id: Optional[int] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    about: Optional[str] = None
    degree: Optional[str] = None
    postgraduate: Optional[str] = None
    expertise_area: Optional[str] = None
    research_work: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    status: UserStatus
    node_id: Optional[int] = None
    about: Optional[str] = None
    degree: Optional[str] = None
    postgraduate: Optional[str] = None
    expertise_area: Optional[str] = None
    research_work: Optional[str] = None
    profile_picture: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    social_links: List[SocialLink] = []
    
    class Config:
        from_attributes = True

class UserListItem(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    node_id: Optional[int] = None
    
    class Config:
        from_attributes = True
