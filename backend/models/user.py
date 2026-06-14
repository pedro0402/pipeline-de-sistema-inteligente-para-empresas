from sqlalchemy import Column, DateTime, Integer, String, func, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    company_id = Column(
        Integer,
        ForeignKey("company_profile.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(DateTime, server_default=func.now())