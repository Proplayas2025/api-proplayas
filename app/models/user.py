from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from models.base import Base
from enums import UserRole, UserStatus

__all__ = ["User", "UserRole", "UserStatus"]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.member)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.active)

    about = Column(Text, nullable=True)
    degree = Column(String(255), nullable=True)
    postgraduate = Column(String(255), nullable=True)
    expertise_area = Column(String(255), nullable=True)
    research_line = Column(Text, nullable=True)
    profile_picture = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)

    node = relationship("Node", foreign_keys=[node_id], back_populates="members")
    led_node = relationship("Node", foreign_keys="Node.leader_id", back_populates="leader", uselist=False)
    social_media = relationship("SocialLink", back_populates="user", cascade="all, delete-orphan")
    created_content = relationship("Content", back_populates="author", cascade="all, delete-orphan")
