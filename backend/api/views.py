import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.database import SessionLocal
from models.company_profile import CompanyProfile
from models.user import User

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

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
def health(request):
    """
    GET /health

    Health check para monitoramento do serviço (ex.: Render).
    """
    return Response({"status": "ok"})


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

@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método não permitido."},
            status=405
        )
    
    session = SessionLocal()

    try:
        data = json.loads(request.body)
        email = data.get("email")
        existing_user = (
            session.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            return JsonResponse(
                {"error": "Email já registrado."},
                status=400
            )
        
        company = CompanyProfile(
            name=data.get("company_name"),
            cnpj=data.get("cnpj"),
            sector=data.get("sector"),
            size=data.get("size"),
            location=data.get("location"),
            website=data.get("website"),
            phone=data.get("phone"),
            annual_revenue=data.get("annual_revenue"),
            discovery_source=data.get("discovery_source"),
        )

        session.add(company)
        session.flush()

        user = User(
            company_id=company.id,
            name=data.get("name"),
            email=data.get("email"),
            password_hash=generate_password_hash(data.get("password")),
        )

        session.add(user)
        session.commit()

        return JsonResponse(
            {
                "message": "Registro bem-sucedido.",
                "company_id": company.id,
                "user_id": user.id,
            },
            status=201
        )
    except Exception as e:
        session.rollback()

        return JsonResponse(
            {"error": "Erro ao processar registro.", "details": str(e)},
            status=500
        )
    finally:
        session.close()

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método não permitido."},
            status=405
        )

    session = SessionLocal()

    try:
        data = json.loads(request.body)

        email = data.get("email")
        password = data.get("password")

        user = (
            session.query(User)
            .filter(User.email == email)
            .first()
        )

        if not user:
            return JsonResponse(
                {"error": "Usuário não encontrado."},
                status=401
            )

        if not check_password_hash(
            user.password_hash,
            password
        ):
            return JsonResponse(
                {"error": "Senha inválida."},
                status=401
            )

        return JsonResponse({
            "message": "Login realizado com sucesso.",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "company_id": user.company_id
            }
        })

    except Exception as e:
        return JsonResponse(
            {
                "error": "Erro ao realizar login.",
                "details": str(e)
            },
            status=500
        )

    finally:
        session.close()