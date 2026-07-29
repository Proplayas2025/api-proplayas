from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.base import Base

__all__ = ["NodeMember"]


class NodeMember(Base):
    __tablename__ = "node_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    member_code = Column(String(50), unique=True, nullable=False, index=True)
    research_line = Column(Text, nullable=True)
    work_area = Column(String(255), nullable=True)

    user = relationship("User", backref="memberships")
    node = relationship("Node", backref="memberships")
