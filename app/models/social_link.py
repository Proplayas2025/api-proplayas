from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
import enum

class SocialPlatform(str, enum.Enum):
    linkedin = "linkedin"
    github = "github"
    twitter = "twitter"
    website = "website"
    facebook = "facebook"
    instagram = "instagram"
    youtube = "youtube"
    research_gate = "research_gate"
    phone = "phone"

class SocialLink(Base):
    __tablename__ = "social_links"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(SocialPlatform), nullable=False)
    url = Column(String(500), nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="social_links")

class NodeSocialLink(Base):
    __tablename__ = "node_social_links"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(SocialPlatform), nullable=False)
    url = Column(String(500), nullable=False)
    
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    
    node = relationship("Node", back_populates="social_links")
