from pydantic import BaseModel, EmailStr, ConfigDict
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
    
    model_config = ConfigDict(from_attributes=True)

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
    research_line: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    social_media: Optional[List[SocialLinkBase]] = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    status: UserStatus
    node_id: Optional[int] = None
    about: Optional[str] = None
    degree: Optional[str] = None
    postgraduate: Optional[str] = None
    expertise_area: Optional[str] = None
    research_line: Optional[str] = None
    profile_picture: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    social_media: List[SocialLink] = []
    
    model_config = ConfigDict(from_attributes=True)

class UserListItem(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    node_id: Optional[int] = None
    node_code: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
