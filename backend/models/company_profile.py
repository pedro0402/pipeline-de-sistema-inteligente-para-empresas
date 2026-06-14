from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class CompanyProfile(Base):
    __tablename__ = "company_profile"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    cnpj = Column(String(18), unique=True)
    sector = Column(String(100))
    size = Column(String(50))
    location = Column(String(100))
    website = Column(String(100))
    phone = Column(String(20))
    annual_revenue = Column(String(100))
    discovery_source = Column(String(100))
    interests = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
