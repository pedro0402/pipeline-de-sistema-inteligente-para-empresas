from unittest.mock import MagicMock, patch
from datetime import date, datetime
from rest_framework.test import APIRequestFactory
from rest_framework import status

from api.views import opportunity_detail

def make_opportunity(**kwargs):
    opp = MagicMock()
    opp.id = kwargs.get("id", 1)
    opp.source_id = kwargs.get("source_id", 1)
    opp.title = kwargs.get("title", "Edital Teste")
    opp.description = kwargs.get("description", "Descrição do edital")
    opp.organization = kwargs.get("organization", "CNPq")
    opp.deadline = kwargs.get("deadline", date(2026, 12, 31))
    opp.link = kwargs.get("link", "https://example.com/edital/1")
    opp.location = kwargs.get("location", "Maceió, AL")
    opp.collected_at = kwargs.get("collected_at", datetime(2026, 4, 28, 10, 0, 0))
    return opp


def make_analysis(**kwargs):
    analysis = MagicMock()
    analysis.id = kwargs.get("id", 1)
    analysis.opportunity_id = kwargs.get("opportunity_id", 1)
    analysis.summary = kwargs.get("summary", "Resumo da análise")
    analysis.relevance_score = kwargs.get("relevance_score", 8)
    analysis.recommended_action = kwargs.get("recommended_action", "Inscrever-se")
    analysis.analyzed_at = kwargs.get("analyzed_at", datetime(2026, 4, 28, 10, 0, 0))
    return analysis


def make_source(**kwargs):
    source = MagicMock()
    source.id = kwargs.get("id", 1)
    source.name = kwargs.get("name", "Prosas")
    source.base_url = kwargs.get("base_url", "https://prosas.com.br")
    return source


factory = APIRequestFactory()


class TestOpportunityDetailStatus:
    @patch("api.views.SessionLocal")
    def test_retorna_200_quando_encontrado(self, mock_session_cls):
        opp = make_opportunity()
        source = make_source()

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [opp, source, None]

        request = factory.get("/opportunities/1")
        response = opportunity_detail(request, pk=1)

        assert response.status_code == 200

    @patch("api.views.SessionLocal")
    def test_retorna_404_quando_nao_encontrado(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None

        request = factory.get("/opportunities/999")
        response = opportunity_detail(request, pk=999)

        assert response.status_code == 404

    @patch("api.views.SessionLocal")
    def test_mensagem_404(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None

        request = factory.get("/opportunities/999")
        response = opportunity_detail(request, pk=999)

        assert response.data["detail"] == "Oportunidade não encontrada."


class TestOpportunityDetailCampos:
    @patch("api.views.SessionLocal")
    def test_campos_retornados(self, mock_session_cls):
        opp = make_opportunity(title="Edital CAPES", organization="CAPES")
        source = make_source(name="CAPES")

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [opp, source, None]

        request = factory.get("/opportunities/1")
        response = opportunity_detail(request, pk=1)

        assert response.data["title"] == "Edital CAPES"
        assert response.data["organization"] == "CAPES"
        assert response.data["link"] == "https://example.com/edital/1"

    @patch("api.views.SessionLocal")
    def test_retorna_source_embutido(self, mock_session_cls):
        opp = make_opportunity()
        source = make_source(name="Prosas")

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [opp, source, None]

        request = factory.get("/opportunities/1")
        response = opportunity_detail(request, pk=1)

        assert response.data["source"]["name"] == "Prosas"

    @patch("api.views.SessionLocal")
    def test_retorna_analysis_embutido(self, mock_session_cls):
        opp = make_opportunity()
        source = make_source()
        analysis = make_analysis(relevance_score=9)

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [opp, source, analysis]

        request = factory.get("/opportunities/1")
        response = opportunity_detail(request, pk=1)

        assert response.data["analysis"]["relevance_score"] == 9

    @patch("api.views.SessionLocal")
    def test_analysis_none_quando_nao_existe(self, mock_session_cls):
        opp = make_opportunity()
        source = make_source()

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [opp, source, None]

        request = factory.get("/opportunities/1")
        response = opportunity_detail(request, pk=1)

        assert response.data["analysis"] is None