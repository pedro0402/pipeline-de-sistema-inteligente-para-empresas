from core.database import SessionLocal, engine, Base
from models.company_profile import CompanyProfile

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        profile = CompanyProfile(
            name="Startup de tecnologia",
            sector="tecnologia e inovação",
            size="pequeno",
            location="maceio",
            interests=(
                "IA, inteligência artificial, tecnologia, machine learning, "
                "LLMs, grandes modelos de linguagem, rede neural, deep learning, big data"
            ),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        print(f"Perfil criado com id={profile.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
