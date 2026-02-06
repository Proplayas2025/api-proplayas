from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    role: str
    node_id: Optional[int] = None
    route: Optional[str] = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    username: str
    invitation_token: str
    about: Optional[str] = None
    degree: Optional[str] = None
    postgraduate: Optional[str] = None
    expertise_area: Optional[str] = None
    research_work: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
