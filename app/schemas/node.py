from pydantic import BaseModel
from typing import Optional, List
from schemas.user import UserListItem, SocialLink
from models.node import NodeType, NodeStatus

class NodeBase(BaseModel):
    name: str
    code: str
    type: NodeType
    about: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    alt_places: Optional[str] = None
    coordinates: Optional[str] = None
    joined_in: Optional[int] = None
    memorandum: Optional[str] = None

class NodeCreate(NodeBase):
    leader_id: Optional[int] = None
    profile_picture: Optional[str] = None

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[NodeType] = None
    about: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    profile_picture: Optional[str] = None
    alt_places: Optional[str] = None
    coordinates: Optional[str] = None
    joined_in: Optional[int] = None
    memorandum: Optional[str] = None

class LeaderInfo(BaseModel):
    id: int
    name: str
    email: str
    degree: Optional[str] = None
    postgraduate: Optional[str] = None
    
    class Config:
        from_attributes = True

class NodeResponse(NodeBase):
    id: int
    leader_id: Optional[int] = None
    profile_picture: Optional[str] = None
    ip_address: Optional[str] = None
    members_count: int
    status: NodeStatus
    social_media: List[SocialLink] = []
    leader: Optional[LeaderInfo] = None
    
    class Config:
        from_attributes = True

class NodeWithMembers(NodeResponse):
    members: List[UserListItem] = []
    
    class Config:
        from_attributes = True
