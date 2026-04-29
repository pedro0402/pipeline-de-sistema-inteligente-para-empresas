from unittest.mock import MagicMock, patch
from datetime import date, datetime
from rest_framework.test import APIRequestFactory

from api.views import top_opportunities


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


class TestTopOpportunitiesStatus:
    @patch("api.views.SessionLocal")
    def test_retorna_200(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities/top")
        response = top_opportunities(request)

        assert response.status_code == 200

    @patch("api.views.SessionLocal")
    def test_estrutura_da_resposta(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities/top")
        response = top_opportunities(request)

        assert "count" in response.data
        assert "results" in response.data


class TestTopOpportunitiesResultados:
    @patch("api.views.SessionLocal")
    def test_retorna_oportunidades_com_score(self, mock_session_cls):
        opp = make_opportunity()
        analysis = make_analysis(relevance_score=9)
        source = make_source()

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.limit.return_value.all.return_value = [(opp, analysis)]
        query_mock.first.return_value = source

        request = factory.get("/opportunities/top")
        response = top_opportunities(request)

        assert response.data["count"] == 1
        assert response.data["results"][0]["analysis"]["relevance_score"] == 9

    @patch("api.views.SessionLocal")
    def test_lista_vazia_sem_analises(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities/top")
        response = top_opportunities(request)

        assert response.data["count"] == 0
        assert response.data["results"] == []

    @patch("api.views.SessionLocal")
    def test_campos_da_oportunidade(self, mock_session_cls):
        opp = make_opportunity(title="Edital FINEP", organization="FINEP")
        analysis = make_analysis(relevance_score=10)
        source = make_source(name="FINEP")

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.limit.return_value.all.return_value = [(opp, analysis)]
        query_mock.first.return_value = source

        request = factory.get("/opportunities/top")
        response = top_opportunities(request)

        result = response.data["results"][0]
        assert result["title"] == "Edital FINEP"
        assert result["organization"] == "FINEP"
        assert result["analysis"]["relevance_score"] == 10


class TestTopOpportunitiesLimit:
    @patch("api.views.SessionLocal")
    def test_limit_default_e_10(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        limit_mock = query_mock.order_by.return_value.limit
        limit_mock.return_value.all.return_value = []

        request = factory.get("/opportunities/top")
        top_opportunities(request)

        limit_mock.assert_called_once_with(10)

    @patch("api.views.SessionLocal")
    def test_limit_maximo_50(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        limit_mock = query_mock.order_by.return_value.limit
        limit_mock.return_value.all.return_value = []

        request = factory.get("/opportunities/top", {"limit": "999"})
        top_opportunities(request)

        limit_mock.assert_called_once_with(50)

    @patch("api.views.SessionLocal")
    def test_limit_invalido_cai_para_10(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        limit_mock = query_mock.order_by.return_value.limit
        limit_mock.return_value.all.return_value = []

        request = factory.get("/opportunities/top", {"limit": "abc"})
        top_opportunities(request)

        limit_mock.assert_called_once_with(10)