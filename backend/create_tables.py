# create_tables.py

from core.database import Base, engine

from models.company_profile import CompanyProfile
from models.user import User
from models.source import Source
from models.opportunity import Opportunity
from models.opportunity_analysis import OpportunityAnalysis

Base.metadata.create_all(bind=engine)

print("Tabelas criadas com sucesso!")