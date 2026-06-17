import importlib
import sys


class FakeResponse:
    def __init__(self, json_payload, status_code=200):
        self._json_payload = json_payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def json(self):
        return self._json_payload


def test_scrape_pncp_collects_opportunities(monkeypatch):
    if "collectors.pncp" in sys.modules:
        del sys.modules["collectors.pncp"]

    pncp = importlib.import_module("collectors.pncp")
    payload = {
        "items": [
            {
                "title": "Edital de Chamamento nº 00001/2021",
                "description": "Contratação de serviço especializado",
                "item_url": "/compras/00394502000144/2021/1",
                "data_fim_vigencia": "2026-06-30T17:00",
            }
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=20):
        assert "tipos_documento" in params
        assert params["tipos_documento"] == "edital"
        assert params["status"] == "aberta"
        assert params.get("ordenacao") == "data_publicacao_pncp_desc"
        return FakeResponse(payload)

    monkeypatch.setattr(pncp.requests, "get", fake_get)

    opportunities = pncp.scrape_pncp()

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity["title"] == "Edital de Chamamento nº 00001/2021"
    assert opportunity["description"] == "Contratação de serviço especializado"
    assert opportunity["link"] == "https://pncp.gov.br/editais/00394502000144/2021/1"
    assert opportunity["deadline"] == "2026-06-30T17:00"
    assert opportunity["source_name"] == "PNCP"
    assert opportunity["source_url"] == "https://pncp.gov.br"


def test_scrape_pncp_orders_items_by_publication_date_newest_first(monkeypatch):
    if "collectors.pncp" in sys.modules:
        del sys.modules["collectors.pncp"]

    pncp = importlib.import_module("collectors.pncp")
    payload = {
        "items": [
            {
                "title": "Edital antigo",
                "description": "",
                "item_url": "/compras/111/2021/1",
                "data_fim_vigencia": "2021-08-13T14:00",
                "data_publicacao_pncp": "2021-08-10T07:54:24.328",
            },
            {
                "title": "Edital recente",
                "description": "",
                "item_url": "/compras/222/2026/1",
                "data_fim_vigencia": "2027-05-29T17:00",
                "data_publicacao_pncp": "2026-04-28T19:00:00",
            },
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=20):
        return FakeResponse(payload)

    monkeypatch.setattr(pncp.requests, "get", fake_get)

    opportunities = pncp.scrape_pncp()

    assert [o["title"] for o in opportunities] == ["Edital recente"]


def test_scrape_pncp_ignores_non_edital_titles(monkeypatch):
    if "collectors.pncp" in sys.modules:
        del sys.modules["collectors.pncp"]

    pncp = importlib.import_module("collectors.pncp")
    payload = {
        "items": [
            {
                "title": "Ato que autoriza a Contratação Direta nº 77/2026",
                "description": "",
                "item_url": "/compras/333/2026/1",
                "data_fim_vigencia": "2026-06-30T17:00",
                "data_publicacao_pncp": "2026-04-28T19:10:00",
            },
            {
                "title": "Edital de seleção nº 12/2026",
                "description": "",
                "item_url": "/compras/444/2026/1",
                "data_fim_vigencia": "2026-07-01T17:00",
                "data_publicacao_pncp": "2026-04-28T19:11:00",
            },
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=20):
        return FakeResponse(payload)

    monkeypatch.setattr(pncp.requests, "get", fake_get)

    opportunities = pncp.scrape_pncp()

    assert len(opportunities) == 1
    assert opportunities[0]["title"] == "Edital de seleção nº 12/2026"
