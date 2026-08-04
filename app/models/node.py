from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from models.base import Base
from enums import NodeType, NodeStatus

__all__ = ["Node", "NodeType", "NodeStatus"]


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(SQLEnum(NodeType), nullable=False, default=NodeType.sociedad_civil)
    profile_picture = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    ip_address = Column(String(100), nullable=True)
    coordinates = Column(String(255), nullable=True)
    alt_places = Column(Text, nullable=True)
    joined_in = Column(Integer, nullable=True)
    members_count = Column(Integer, default=0)
    memorandum = Column(Text, nullable=True)
    status = Column(SQLEnum(NodeStatus), nullable=False, default=NodeStatus.active)

    leader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    leader = relationship("User", back_populates="led_node", foreign_keys=[leader_id])
    members = relationship("User", back_populates="node", foreign_keys="User.node_id")
    social_media = relationship("NodeSocialLink", back_populates="node", cascade="all, delete-orphan")
