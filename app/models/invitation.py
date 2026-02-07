from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, Text
from datetime import datetime, timedelta
from database import Base
from models.user import UserRole
import enum

class InvitationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"

class Invitation(Base):
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(Text, unique=True, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False)
    node_type = Column(String(100), nullable=True)
    status = Column(SQLEnum(InvitationStatus), nullable=False, default=InvitationStatus.pending)
    
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
