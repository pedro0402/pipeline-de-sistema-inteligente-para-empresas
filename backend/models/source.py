from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    base_url = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
