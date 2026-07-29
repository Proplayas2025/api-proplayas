from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from schemas.user import UserListItem
from models.node import NodeType, NodeStatus

class NodeSocialLink(BaseModel):
    """Schema para redes sociales de nodos (sin user_id)"""
    id: int
    platform: str
    url: str
    
    model_config = ConfigDict(from_attributes=True)

class NodeSocialLinkBase(BaseModel):
    """Schema base para crear/actualizar redes sociales de nodos"""
    platform: str
    url: str

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
    social_media: Optional[List[NodeSocialLinkBase]] = None

class LeaderInfo(BaseModel):
    id: int
    name: str
    email: str
    degree: Optional[str] = None
    postgraduate: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class NodeResponse(NodeBase):
    id: int
    leader_id: Optional[int] = None
    profile_picture: Optional[str] = None
    ip_address: Optional[str] = None
    members_count: int
    status: NodeStatus
    social_media: List[NodeSocialLink] = []
    leader: Optional[LeaderInfo] = None
    
    model_config = ConfigDict(from_attributes=True)

class NodeWithMembers(NodeResponse):
    members: List[UserListItem] = []

    model_config = ConfigDict(from_attributes=True)

class NodeMemberItem(BaseModel):
    """Miembro de un nodo: datos de la membresía + del usuario asociado."""
    id: int
    user_id: int
    node_id: int
    member_code: str
    name: str
    email: str
    username: str
    research_line: Optional[str] = None
    work_area: Optional[str] = None
    status: str

class NodeMemberStatus(BaseModel):
    """Respuesta al alternar el estado de un miembro."""
    id: int
    name: str
    email: str
    status: str
