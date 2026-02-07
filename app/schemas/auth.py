from pydantic import BaseModel, EmailStr
from typing import Optional, List


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    node_id: Optional[int] = None
    route: Optional[str] = None


class SocialMediaItem(BaseModel):
    platform: str
    url: str


class RegisterNodeLeaderRequest(BaseModel):
    token: str
    # Datos del usuario
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    about_user: Optional[str] = None
    degree: Optional[str] = None
    postgraduate: Optional[str] = None
    expertise_area: Optional[str] = None
    research_work: Optional[str] = None
    country_user: Optional[str] = None
    city_user: Optional[str] = None
    social_media: Optional[List[SocialMediaItem]] = None
    # Datos del nodo
    node_type: Optional[str] = None
    node_name: Optional[str] = None
    about_node: Optional[str] = None
    country_node: Optional[str] = None
    city_node: Optional[str] = None
    coordinates: Optional[str] = None
    alt_places: Optional[str] = None
    joined_in: Optional[int] = None
    social_media_node: Optional[List[SocialMediaItem]] = None
    memorandum: Optional[str] = None


class RegisterNodeMemberRequest(BaseModel):
    token: str
    name: str
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    about_user: Optional[str] = None
    expertise_area: Optional[str] = None
    research_work: Optional[str] = None
    country_user: Optional[str] = None
    city_user: Optional[str] = None
    social_media: Optional[List[SocialMediaItem]] = None
