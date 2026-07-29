from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from models.base import Base
from enums import SocialPlatform

__all__ = ["SocialLink", "NodeSocialLink", "SocialPlatform"]


class SocialLink(Base):
    __tablename__ = "social_links"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(SocialPlatform), nullable=False)
    url = Column(String(500), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="social_media")


class NodeSocialLink(Base):
    __tablename__ = "node_social_links"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(SocialPlatform), nullable=False)
    url = Column(String(500), nullable=False)

    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)

    node = relationship("Node", back_populates="social_media")
