import importlib
import sys


def _reload_database_module():
    if "core.database" in sys.modules:
        return importlib.reload(sys.modules["core.database"])
    return importlib.import_module("core.database")


def _reload_model_modules():
    for module_name in ["models.source", "models.opportunity"]:
        if module_name in sys.modules:
            del sys.modules[module_name]


def test_save_to_db_persists_and_deduplicates_links(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    _reload_model_modules()
    database_module = _reload_database_module()
    source_module = importlib.import_module("models.source")
    opportunity_module = importlib.import_module("models.opportunity")

    database_module.Base.metadata.create_all(bind=database_module.engine)

    if "run_pipeline" in sys.modules:
        del sys.modules["run_pipeline"]
    run_pipeline = importlib.import_module("run_pipeline")

    monkeypatch.setattr(run_pipeline, "SessionLocal", database_module.SessionLocal)
    monkeypatch.setattr(run_pipeline, "Source", source_module.Source)
    monkeypatch.setattr(run_pipeline, "Opportunity", opportunity_module.Opportunity)

    items = [
        {
            "title": "Edital A",
            "description": "Descricao A",
            "link": "https://prosas.com.br/oportunidade/a",
            "deadline": None,
            "source_name": "Prosas",
            "source_url": "https://prosas.com.br",
        },
        {
            "title": "Edital A Duplicado",
            "description": "Descricao duplicada",
            "link": "https://prosas.com.br/oportunidade/a",
            "deadline": None,
            "source_name": "Prosas",
            "source_url": "https://prosas.com.br",
        },
    ]

    run_pipeline.save_to_db(items)

    session = database_module.SessionLocal()
    sources = session.query(source_module.Source).all()
    opportunities = session.query(opportunity_module.Opportunity).all()

    assert len(sources) == 1
    assert len(opportunities) == 1
    assert opportunities[0].title == "Edital A"
    assert opportunities[0].organization == "Prosas"

    session.close()
