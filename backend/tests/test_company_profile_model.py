import importlib
import sys


def _reload_database_module():
    if "core.database" in sys.modules:
        return importlib.reload(sys.modules["core.database"])
    return importlib.import_module("core.database")


def _reload_models_modules():
    for module_name in ["models.company_profile"]:
        if module_name in sys.modules:
            del sys.modules[module_name]


def _create_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    _reload_models_modules()

    database_module = _reload_database_module()
    company_profile_module = importlib.import_module("models.company_profile")

    database_module.Base.metadata.create_all(bind=database_module.engine)
    session = database_module.SessionLocal()

    return session, company_profile_module.CompanyProfile


def test_company_profile_model_persists_with_sqlite(monkeypatch):
    session, CompanyProfile = _create_session(monkeypatch)

    company = CompanyProfile(
        name="Empresa Exemplo",
        sector="Tecnologia",
        size="Média",
        location="São Paulo",
        interests="Inovacao, IA, automacao",
    )
    session.add(company)
    session.commit()

    stored = session.query(CompanyProfile).filter_by(name="Empresa Exemplo").one()
    columns = set(CompanyProfile.__table__.columns.keys())

    assert CompanyProfile.__tablename__ == "company_profile"
    assert columns == {
        "id",
        "name",
        "sector",
        "size",
        "location",
        "interests",
        "created_at",
    }
    assert CompanyProfile.__table__.c.name.type.length == 200
    assert stored.id is not None
    assert stored.sector == "Tecnologia"
    assert stored.interests == "Inovacao, IA, automacao"

    session.close()
