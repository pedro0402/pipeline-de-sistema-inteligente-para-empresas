from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from core.database import SessionLocal
from models.opportunity import Opportunity
from models.opportunity_analysis import OpportunityAnalysis
from models.source import Source


def _serialize_opportunity(opp, source=None, analysis=None):
    return {
        "id": opp.id,
        "title": opp.title,
        "description": opp.description,
        "organization": opp.organization,
        "deadline": str(opp.deadline) if opp.deadline else None,
        "link": opp.link,
        "location": opp.location,
        "collected_at": opp.collected_at.isoformat() if opp.collected_at else None,
        "source": (
            {"id": source.id, "name": source.name, "base_url": source.base_url}
            if source
            else None
        ),
        "analysis": (
            {
                "id": analysis.id,
                "summary": analysis.summary,
                "relevance_score": analysis.relevance_score,
                "recommended_action": analysis.recommended_action,
            }
            if analysis
            else None
        ),
    }


@api_view(["GET"])
def list_opportunities(request):
    """
    GET /opportunities

    Query params (Filtros opcionais):
        search       : filtra por título ou descrição (case-insensitive)
        organization : filtra por organização
        location     : filtra por localização
        page         : número da página (default 1)
        page_size    : itens por página (default 20, max 100)
    """
    session = SessionLocal()
    try:
        query = session.query(Opportunity)

        search = request.query_params.get("search")
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Opportunity.title.ilike(pattern) | Opportunity.description.ilike(pattern)
            )

        organization = request.query_params.get("organization")
        if organization:
            query = query.filter(Opportunity.organization.ilike(f"%{organization}%"))

        location = request.query_params.get("location")
        if location:
            query = query.filter(Opportunity.location.ilike(f"%{location}%"))

        total = query.count()

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except ValueError:
            page = 1

        try:
            page_size = min(100, max(1, int(request.query_params.get("page_size", 20))))
        except ValueError:
            page_size = 20

        opportunities = (
            query.order_by(Opportunity.collected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        data = []
        for opp in opportunities:
            source = session.query(Source).filter(Source.id == opp.source_id).first()
            analysis = (
                session.query(OpportunityAnalysis)
                .filter(OpportunityAnalysis.opportunity_id == opp.id)
                .first()
            )
            data.append(_serialize_opportunity(opp, source=source, analysis=analysis))

        return Response({"count": total, "page": page, "page_size": page_size, "results": data})
    finally:
        session.close()

@api_view(["GET"])
def top_opportunities(request):
    """
    GET /opportunities/top

    Query params:
        limit : quantidade de resultados (default 10, max 50)
    """
    session = SessionLocal()
    try:
        try:
            limit = min(50, max(1, int(request.query_params.get("limit", 10))))
        except ValueError:
            limit = 10

        rows = (
            session.query(Opportunity, OpportunityAnalysis)
            .join(OpportunityAnalysis, OpportunityAnalysis.opportunity_id == Opportunity.id)
            .filter(OpportunityAnalysis.relevance_score.isnot(None))
            .order_by(OpportunityAnalysis.relevance_score.desc())
            .limit(limit)
            .all()
        )

        data = []
        for opp, analysis in rows:
            source = session.query(Source).filter(Source.id == opp.source_id).first()
            data.append(_serialize_opportunity(opp, source=source, analysis=analysis))

        return Response({"count": len(data), "results": data})
    finally:
        session.close()

@api_view(["GET"])
def opportunity_detail(request, pk):
    """
    GET /opportunities/{id}
    Retorna 404 se não encontrada.
    """
    session = SessionLocal()
    try:
        opp = session.query(Opportunity).filter(Opportunity.id == pk).first()

        if opp is None:
            return Response(
                {"detail": "Oportunidade não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        source = session.query(Source).filter(Source.id == opp.source_id).first()
        analysis = (
            session.query(OpportunityAnalysis)
            .filter(OpportunityAnalysis.opportunity_id == opp.id)
            .first()
        )

        return Response(_serialize_opportunity(opp, source=source, analysis=analysis))
    finally:
        session.close()