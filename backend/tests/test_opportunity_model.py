import importlib
import sys
from datetime import date

from sqlalchemy.exc import IntegrityError


def _reload_database_module():
    if "core.database" in sys.modules:
        return importlib.reload(sys.modules["core.database"])
    return importlib.import_module("core.database")


def _reload_models_modules():
    for module_name in ["models.source", "models.opportunity"]:
        if module_name in sys.modules:
            del sys.modules[module_name]


def _create_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    _reload_models_modules()

    database_module = _reload_database_module()
    source_module = importlib.import_module("models.source")
    opportunity_module = importlib.import_module("models.opportunity")

    database_module.Base.metadata.create_all(bind=database_module.engine)
    session = database_module.SessionLocal()

    return session, source_module.Source, opportunity_module.Opportunity


def test_opportunity_model_persists_with_sqlite(monkeypatch):
    session, Source, Opportunity = _create_session(monkeypatch)

    source = Source(name="FINEP", base_url="https://www.finep.gov.br")
    session.add(source)
    session.commit()

    opportunity = Opportunity(
        source_id=source.id,
        title="Edital de Inovacao 2026",
        description="Fomento para projetos de P&D",
        organization="FINEP",
        deadline=date(2026, 12, 31),
        link="https://finep.gov.br/editais/inovacao-2026",
        location="Brasil",
    )
    session.add(opportunity)
    session.commit()

    stored = session.query(Opportunity).filter_by(link=opportunity.link).one()
    columns = set(Opportunity.__table__.columns.keys())

    assert Opportunity.__tablename__ == "opportunities"
    assert columns == {
        "id",
        "source_id",
        "title",
        "description",
        "organization",
        "deadline",
        "link",
        "location",
        "collected_at",
    }
    assert stored.id is not None
    assert stored.source_id == source.id
    assert stored.title == "Edital de Inovacao 2026"
    assert stored.link == "https://finep.gov.br/editais/inovacao-2026"

    session.close()


def test_opportunity_link_must_be_unique(monkeypatch):
    session, Source, Opportunity = _create_session(monkeypatch)

    source = Source(name="CNPQ", base_url="https://www.gov.br/cnpq")
    session.add(source)
    session.commit()

    first = Opportunity(
        source_id=source.id,
        title="Chamada 1",
        link="https://www.gov.br/cnpq/chamada-1",
    )
    second = Opportunity(
        source_id=source.id,
        title="Chamada duplicada",
        link="https://www.gov.br/cnpq/chamada-1",
    )

    session.add(first)
    session.commit()

    session.add(second)
    try:
        session.commit()
        assert False, "Esperava IntegrityError para link duplicado"
    except IntegrityError:
        session.rollback()

    session.close()
