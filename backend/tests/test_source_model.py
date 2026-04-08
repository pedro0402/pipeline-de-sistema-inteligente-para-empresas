import importlib
import sys


def _reload_database_module():
    if "core.database" in sys.modules:
        return importlib.reload(sys.modules["core.database"])
    return importlib.import_module("core.database")


def test_source_model_persists_with_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    if "models.source" in sys.modules:
        del sys.modules["models.source"]

    database_module = _reload_database_module()
    source_module = importlib.import_module("models.source")
    Source = source_module.Source

    database_module.Base.metadata.create_all(bind=database_module.engine)
    session = database_module.SessionLocal()

    source = Source(name="FINEP", base_url="https://www.finep.gov.br")
    session.add(source)
    session.commit()

    stored = session.query(Source).filter_by(name="FINEP").one()
    columns = set(Source.__table__.columns.keys())

    assert Source.__tablename__ == "sources"
    assert columns == {"id", "name", "base_url", "created_at"}
    assert Source.__table__.c.name.type.length == 100
    assert stored.id is not None
    assert stored.base_url == "https://www.finep.gov.br"

    session.close()
