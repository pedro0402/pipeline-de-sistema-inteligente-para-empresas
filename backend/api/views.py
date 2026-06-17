import json
from datetime import date

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sqlalchemy import or_

from core.database import SessionLocal
from models.company_profile import CompanyProfile
from models.user import User
from models.opportunity import Opportunity
from models.opportunity_analysis import OpportunityAnalysis
from models.source import Source

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from processing.finep import normalize_finep_link
from processing.pncp import normalize_pncp_link


def _active_opportunities_filter():
    return or_(
        Opportunity.deadline.is_(None),
        Opportunity.deadline >= date.today(),
    )


def _valid_finep_links_filter():
    return or_(
        ~Source.name.ilike("finep%"),
        Opportunity.link.ilike("%/e/chamada-publica/%"),
        Opportunity.link.ilike("%/chamadas-publicas/chamadapublica/%"),
    )


def _safe_json_loads(value, default=None):
    if default is None:
        default = []

    if not value:
        return default

    try:
        return json.loads(value)
    except Exception:
        return default


def _set_if_attr(obj, field, value):
    """
    Só seta o campo se ele existir no model.
    Isso evita erro caso o banco/model ainda não tenha cnpj, phone, website etc.
    """
    if hasattr(obj, field):
        setattr(obj, field, value)


def _serialize_company(company):
    created_at = getattr(company, "created_at", None)

    return {
        "id": company.id,
        "name": getattr(company, "name", None),
        "cnpj": getattr(company, "cnpj", None),
        "sector": getattr(company, "sector", None),
        "size": getattr(company, "size", None),
        "location": getattr(company, "location", None),
        "website": getattr(company, "website", None),
        "phone": getattr(company, "phone", None),
        "annual_revenue": getattr(company, "annual_revenue", None),
        "discovery_source": getattr(company, "discovery_source", None),
        "interests": _safe_json_loads(getattr(company, "interests", None), []),
        "created_at": created_at.isoformat() if created_at else None,
    }


def _serialize_opportunity(opp, source=None, analysis=None):
    source_name = source.name if source else None

    if source_name == "PNCP":
        link = normalize_pncp_link(opp.link)
    elif source_name == "Finep":
        link = normalize_finep_link(opp.link)
    else:
        link = opp.link

    return {
        "id": opp.id,
        "title": opp.title,
        "description": opp.description,
        "organization": opp.organization,
        "deadline": str(opp.deadline) if opp.deadline else None,
        "link": link,
        "location": opp.location,
        "collected_at": opp.collected_at.isoformat() if opp.collected_at else None,
        "source": (
            {
                "id": source.id,
                "name": source.name,
                "base_url": source.base_url
            }
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
    return Response({"status": "ok"})


@api_view(["GET"])
def list_opportunities(request):
    session = SessionLocal()

    try:
        query = (
            session.query(Opportunity)
            .join(Source, Opportunity.source_id == Source.id)
            .filter(_active_opportunities_filter())
            .filter(_valid_finep_links_filter())
        )

        search = request.query_params.get("search")

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Opportunity.title.ilike(pattern)
                | Opportunity.description.ilike(pattern)
            )

        organization = request.query_params.get("organization")

        if organization:
            query = query.filter(
                Opportunity.organization.ilike(f"%{organization}%")
            )

        location = request.query_params.get("location")

        if location:
            query = query.filter(
                Opportunity.location.ilike(f"%{location}%")
            )

        total = query.count()

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except ValueError:
            page = 1

        try:
            page_size = min(
                100,
                max(1, int(request.query_params.get("page_size", 20)))
            )
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
            source = (
                session.query(Source)
                .filter(Source.id == opp.source_id)
                .first()
            )

            analysis = (
                session.query(OpportunityAnalysis)
                .filter(OpportunityAnalysis.opportunity_id == opp.id)
                .first()
            )

            data.append(
                _serialize_opportunity(
                    opp,
                    source=source,
                    analysis=analysis
                )
            )

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": data
        })

    finally:
        session.close()


@api_view(["GET"])
def top_opportunities(request):
    session = SessionLocal()

    try:
        try:
            limit = min(
                50,
                max(1, int(request.query_params.get("limit", 10)))
            )
        except ValueError:
            limit = 10

        rows = (
            session.query(Opportunity, OpportunityAnalysis)
            .join(
                OpportunityAnalysis,
                OpportunityAnalysis.opportunity_id == Opportunity.id
            )
            .join(Source, Opportunity.source_id == Source.id)
            .filter(_active_opportunities_filter())
            .filter(_valid_finep_links_filter())
            .filter(OpportunityAnalysis.relevance_score.isnot(None))
            .order_by(OpportunityAnalysis.relevance_score.desc())
            .limit(limit)
            .all()
        )

        data = []

        for opp, analysis in rows:
            source = (
                session.query(Source)
                .filter(Source.id == opp.source_id)
                .first()
            )

            data.append(
                _serialize_opportunity(
                    opp,
                    source=source,
                    analysis=analysis
                )
            )

        return Response({
            "count": len(data),
            "results": data
        })

    finally:
        session.close()


@api_view(["GET"])
def opportunity_detail(request, pk):
    session = SessionLocal()

    try:
        opp = (
            session.query(Opportunity)
            .join(Source, Opportunity.source_id == Source.id)
            .filter(Opportunity.id == pk)
            .filter(_active_opportunities_filter())
            .filter(_valid_finep_links_filter())
            .first()
        )

        if opp is None:
            return Response(
                {"detail": "Oportunidade não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        source = (
            session.query(Source)
            .filter(Source.id == opp.source_id)
            .first()
        )

        analysis = (
            session.query(OpportunityAnalysis)
            .filter(OpportunityAnalysis.opportunity_id == opp.id)
            .first()
        )

        return Response(
            _serialize_opportunity(
                opp,
                source=source,
                analysis=analysis
            )
        )

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
            interests=json.dumps([]),
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
            {
                "error": "Erro ao processar registro.",
                "details": str(e)
            },
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

        if not check_password_hash(user.password_hash, password):
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


@api_view(["GET", "PUT"])
def interests_view(request):
    session = SessionLocal()

    try:
        if request.method == "GET":
            user_id = request.query_params.get("user_id")

            user = (
                session.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if not user:
                return Response(
                    {"error": "Usuário não encontrado"},
                    status=404
                )

            company = (
                session.query(CompanyProfile)
                .filter(CompanyProfile.id == user.company_id)
                .first()
            )

            return Response({
                "interests": _safe_json_loads(
                    getattr(company, "interests", None),
                    []
                )
            })

        data = request.data

        interests = data.get("interests", [])
        user_id = data.get("user_id")

        user = (
            session.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return Response(
                {"error": "Usuário não encontrado"},
                status=404
            )

        company = (
            session.query(CompanyProfile)
            .filter(CompanyProfile.id == user.company_id)
            .first()
        )

        company.interests = json.dumps(interests)
        session.commit()

        return Response({
            "message": "Atualizado com sucesso",
            "interests": interests
        })

    finally:
        session.close()


@api_view(["POST"])
def run_pipeline_and_save(request):
    user_id = request.data.get("user_id")
    search = (request.data.get("search") or "").strip()

    if not user_id:
        return Response(
            {"error": "user_id é obrigatório."},
            status=400
        )

    session = SessionLocal()

    try:
        user = (
            session.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return Response(
                {"error": "Usuário não encontrado."},
                status=404
            )

        company_id = user.company_id

    finally:
        session.close()

    try:
        from run_pipeline import main as run_pipeline_main

        run_pipeline_main(company_id)

    except Exception as error:
        return Response(
            {
                "error": "Erro ao executar pipeline.",
                "details": str(error)
            },
            status=500
        )

    session = SessionLocal()

    try:
        query = (
            session.query(Opportunity, OpportunityAnalysis)
            .join(
                OpportunityAnalysis,
                OpportunityAnalysis.opportunity_id == Opportunity.id
            )
            .join(Source, Opportunity.source_id == Source.id)
            .filter(_active_opportunities_filter())
            .filter(_valid_finep_links_filter())
            .filter(OpportunityAnalysis.relevance_score.isnot(None))
            .filter(OpportunityAnalysis.relevance_score >= 6)
        )

        if search:
            pattern = f"%{search}%"

            query = query.filter(
                Opportunity.title.ilike(pattern)
                | Opportunity.description.ilike(pattern)
                | Opportunity.organization.ilike(pattern)
                | Opportunity.location.ilike(pattern)
            )

        rows = (
            query.order_by(OpportunityAnalysis.relevance_score.desc())
            .limit(100)
            .all()
        )

        data = []

        for opp, analysis in rows:
            source = (
                session.query(Source)
                .filter(Source.id == opp.source_id)
                .first()
            )

            data.append(
                _serialize_opportunity(
                    opp,
                    source=source,
                    analysis=analysis
                )
            )

        return Response({
            "message": "Pipeline executado e oportunidades salvas no banco.",
            "count": len(data),
            "results": data
        })

    finally:
        session.close()


@api_view(["GET", "PUT"])
def company_profile_view(request):
    session = SessionLocal()

    try:
        if request.method == "GET":
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response(
                    {"error": "user_id é obrigatório."},
                    status=400
                )

            user = (
                session.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if not user:
                return Response(
                    {"error": "Usuário não encontrado."},
                    status=404
                )

            company = (
                session.query(CompanyProfile)
                .filter(CompanyProfile.id == user.company_id)
                .first()
            )

            if not company:
                return Response(
                    {"error": "Empresa não encontrada."},
                    status=404
                )

            return Response(_serialize_company(company))

        data = request.data
        user_id = data.get("user_id")

        if not user_id:
            return Response(
                {"error": "user_id é obrigatório."},
                status=400
            )

        user = (
            session.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return Response(
                {"error": "Usuário não encontrado."},
                status=404
            )

        company = (
            session.query(CompanyProfile)
            .filter(CompanyProfile.id == user.company_id)
            .first()
        )

        if not company:
            return Response(
                {"error": "Empresa não encontrada."},
                status=404
            )

        _set_if_attr(company, "name", data.get("name", company.name))
        _set_if_attr(company, "cnpj", data.get("cnpj", getattr(company, "cnpj", None)))
        _set_if_attr(company, "sector", data.get("sector", company.sector))
        _set_if_attr(company, "size", data.get("size", company.size))
        _set_if_attr(company, "location", data.get("location", company.location))
        _set_if_attr(company, "website", data.get("website", getattr(company, "website", None)))
        _set_if_attr(company, "phone", data.get("phone", getattr(company, "phone", None)))
        _set_if_attr(company, "annual_revenue", data.get("annual_revenue", getattr(company, "annual_revenue", None)))
        _set_if_attr(company, "discovery_source", data.get("discovery_source", getattr(company, "discovery_source", None)))

        interests = data.get("interests")

        if interests is not None and hasattr(company, "interests"):
            company.interests = json.dumps(interests)

        session.commit()

        return Response({
            "message": "Perfil da empresa atualizado com sucesso.",
            "company": _serialize_company(company)
        })

    except Exception as error:
        session.rollback()

        return Response(
            {
                "error": "Erro ao processar perfil da empresa.",
                "details": str(error)
            },
            status=500
        )

    finally:
        session.close()