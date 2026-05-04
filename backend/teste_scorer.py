from core.database import SessionLocal
from intelligence.scorer import score_opportunity
from models.company_profile import CompanyProfile

session = SessionLocal()
profile = session.query(CompanyProfile).first()
session.expunge(profile)
session.close()

edital = {
    "title": "Finep Mais Inovação Brasil – Rodada 2 – Tecnologias Digitais",
    "description": "Chamada pública para projetos de inovação em tecnologias digitais, inteligência artificial e transformação digital.",
}

print(f"Empresa: {profile.name}")
print(f"Edital: {edital['title']}")
print("Enviando...")

result = score_opportunity(profile, edital)
print(f"Resultado: {result}")
