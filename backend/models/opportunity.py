from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func

from core.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    organization = Column(String(200))
    deadline = Column(Date)
    link = Column(Text, nullable=False, unique=True)
    location = Column(String(100))
    collected_at = Column(DateTime, server_default=func.now())
