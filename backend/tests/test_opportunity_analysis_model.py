import importlib
import sys

from sqlalchemy.exc import IntegrityError


def _reload_database_module():
    if "core.database" in sys.modules:
        return importlib.reload(sys.modules["core.database"])
    return importlib.import_module("core.database")


def _reload_models_modules():
    for module_name in [
        "models.source",
        "models.opportunity",
        "models.opportunity_analysis",
    ]:
        if module_name in sys.modules:
            del sys.modules[module_name]


def _create_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    _reload_models_modules()

    database_module = _reload_database_module()
    source_module = importlib.import_module("models.source")
    opportunity_module = importlib.import_module("models.opportunity")
    analysis_module = importlib.import_module("models.opportunity_analysis")

    database_module.Base.metadata.create_all(bind=database_module.engine)
    session = database_module.SessionLocal()

    return (
        session,
        source_module.Source,
        opportunity_module.Opportunity,
        analysis_module.OpportunityAnalysis,
    )


def _create_opportunity(session, Source, Opportunity):
    source = Source(name="FINEP", base_url="https://www.finep.gov.br")
    session.add(source)
    session.commit()

    opportunity = Opportunity(
        source_id=source.id,
        title="Edital IA 2026",
        link="https://finep.gov.br/editais/ia-2026",
    )
    session.add(opportunity)
    session.commit()
    return opportunity


def test_opportunity_analysis_persists_with_sqlite(monkeypatch):
    session, Source, Opportunity, OpportunityAnalysis = _create_session(monkeypatch)
    opportunity = _create_opportunity(session, Source, Opportunity)

    analysis = OpportunityAnalysis(
        opportunity_id=opportunity.id,
        summary="Boa aderencia para empresa de tecnologia.",
        relevance_score=8,
        recommended_action="Preparar proposta tecnica e cronograma.",
    )
    session.add(analysis)
    session.commit()

    stored = session.query(OpportunityAnalysis).filter_by(opportunity_id=opportunity.id).one()
    columns = set(OpportunityAnalysis.__table__.columns.keys())

    assert OpportunityAnalysis.__tablename__ == "opportunity_analysis"
    assert columns == {
        "id",
        "opportunity_id",
        "summary",
        "relevance_score",
        "recommended_action",
        "analyzed_at",
    }
    assert stored.id is not None
    assert stored.relevance_score == 8

    session.close()


def test_opportunity_analysis_opportunity_id_must_be_unique(monkeypatch):
    session, Source, Opportunity, OpportunityAnalysis = _create_session(monkeypatch)
    opportunity = _create_opportunity(session, Source, Opportunity)

    first = OpportunityAnalysis(opportunity_id=opportunity.id, relevance_score=7)
    second = OpportunityAnalysis(opportunity_id=opportunity.id, relevance_score=9)

    session.add(first)
    session.commit()

    session.add(second)
    try:
        session.commit()
        assert False, "Esperava IntegrityError para opportunity_id duplicado"
    except IntegrityError:
        session.rollback()

    session.close()


def test_opportunity_analysis_relevance_score_range(monkeypatch):
    session, Source, Opportunity, OpportunityAnalysis = _create_session(monkeypatch)
    opportunity = _create_opportunity(session, Source, Opportunity)

    invalid_analysis = OpportunityAnalysis(
        opportunity_id=opportunity.id,
        relevance_score=11,
    )
    session.add(invalid_analysis)

    try:
        session.commit()
        assert False, "Esperava IntegrityError para relevance_score fora do range 0-10"
    except IntegrityError:
        session.rollback()

    session.close()
