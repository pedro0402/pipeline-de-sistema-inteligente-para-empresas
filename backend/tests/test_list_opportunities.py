import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from rest_framework.test import APIRequestFactory

from api.views import list_opportunities

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


def make_source(**kwargs):
    source = MagicMock()
    source.id = kwargs.get("id", 1)
    source.name = kwargs.get("name", "Prosas")
    source.base_url = kwargs.get("base_url", "https://prosas.com.br")
    return source


factory = APIRequestFactory()


#Testes de oportunidades

class TestListOpportunitiesStatus:
    @patch("api.views.SessionLocal")
    def test_retorna_200(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities")
        response = list_opportunities(request)

        assert response.status_code == 200

    @patch("api.views.SessionLocal")
    def test_estrutura_da_resposta(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities")
        response = list_opportunities(request)

        assert "count" in response.data
        assert "page" in response.data
        assert "page_size" in response.data
        assert "results" in response.data


class TestListOpportunitiesResultados:
    @patch("api.views.SessionLocal")
    def test_retorna_oportunidades(self, mock_session_cls):
        opp = make_opportunity()
        source = make_source()

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [opp]
        query_mock.first.return_value = source

        request = factory.get("/opportunities")
        response = list_opportunities(request)

        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    @patch("api.views.SessionLocal")
    def test_campos_da_oportunidade(self, mock_session_cls):
        opp = make_opportunity(title="Edital FAPEAL", organization="FAPEAL")
        source = make_source(name="FAPEAL")

        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [opp]
        query_mock.first.return_value = source

        request = factory.get("/opportunities")
        response = list_opportunities(request)

        result = response.data["results"][0]
        assert result["title"] == "Edital FAPEAL"
        assert result["organization"] == "FAPEAL"
        assert result["link"] == "https://example.com/edital/1"

    @patch("api.views.SessionLocal")
    def test_lista_vazia(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities")
        response = list_opportunities(request)

        assert response.data["count"] == 0
        assert response.data["results"] == []


class TestListOpportunitiesPaginacao:
    @patch("api.views.SessionLocal")
    def test_page_default_e_1(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities")
        response = list_opportunities(request)

        assert response.data["page"] == 1

    @patch("api.views.SessionLocal")
    def test_page_size_default_e_20(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities")
        response = list_opportunities(request)

        assert response.data["page_size"] == 20

    @patch("api.views.SessionLocal")
    def test_page_size_maximo_100(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities", {"page_size": "999"})
        response = list_opportunities(request)

        assert response.data["page_size"] == 100

    @patch("api.views.SessionLocal")
    def test_page_invalido_cai_para_1(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities", {"page": "abc"})
        response = list_opportunities(request)

        assert response.data["page"] == 1


class TestListOpportunitiesFiltros:
    @patch("api.views.SessionLocal")
    def test_filtro_search_aplicado(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities", {"search": "pesquisa"})
        response = list_opportunities(request)

        assert query_mock.filter.called
        assert response.status_code == 200

    @patch("api.views.SessionLocal")
    def test_filtro_organization_aplicado(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities", {"organization": "CNPq"})
        response = list_opportunities(request)

        assert query_mock.filter.called
        assert response.status_code == 200

    @patch("api.views.SessionLocal")
    def test_filtro_location_aplicado(self, mock_session_cls):
        session = MagicMock()
        mock_session_cls.return_value = session
        query_mock = MagicMock()
        session.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        request = factory.get("/opportunities", {"location": "Maceió"})
        response = list_opportunities(request)

        assert query_mock.filter.called
        assert response.status_code == 200