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


def test_scrape_finep_collects_open_calls_from_api(monkeypatch):
    if "collectors.finep" in sys.modules:
        del sys.modules["collectors.finep"]

    finep = importlib.import_module("collectors.finep")
    payload = {
        "items": [
            {
                "id": 754567,
                "titulo": "Finep Mais Inovação Brasil – Rodada 2 – Transição Energética",
                "descricao": "<p>Descrição da chamada</p>",
                "prazoProposto": "2027-08-31T17:00:00.000Z",
                "situacao": {"key": "aberta", "name": "Aberta"},
            },
            {
                "id": 900001,
                "titulo": "Chamada expirada",
                "descricao": "",
                "prazoProposto": "2020-01-01T17:00:00.000Z",
                "situacao": {"key": "aberta", "name": "Aberta"},
            },
        ],
        "lastPage": 1,
    }

    def fake_get(url, params=None, headers=None, timeout=20):
        assert url == finep.FINEP_API_URL
        assert params["filter"] == finep.OPEN_FILTER
        return FakeResponse(payload)

    monkeypatch.setattr(finep.requests, "get", fake_get)

    opportunities = finep.scrape_finep()

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity["title"] == "Finep Mais Inovação Brasil – Rodada 2 – Transição Energética"
    assert opportunity["link"] == "https://www.finep.gov.br/e/chamada-publica/222684/754567"
    assert opportunity["description"] == "<p>Descrição da chamada</p>"
    assert opportunity["deadline"] == "2027-08-31T17:00:00.000Z"
    assert opportunity["source_name"] == "Finep"


def test_scrape_finep_paginates_api_results(monkeypatch):
    if "collectors.finep" in sys.modules:
        del sys.modules["collectors.finep"]

    finep = importlib.import_module("collectors.finep")

    def fake_get(url, params=None, headers=None, timeout=20):
        page = params["page"]
        if page == 1:
            return FakeResponse(
                {
                    "items": [
                        {
                            "id": 100,
                            "titulo": "Chamada 1",
                            "descricao": "",
                            "prazoProposto": "2027-01-01T17:00:00.000Z",
                        }
                    ],
                    "lastPage": 2,
                }
            )
        return FakeResponse(
            {
                "items": [
                    {
                        "id": 101,
                        "titulo": "Chamada 2",
                        "descricao": "",
                        "prazoProposto": "2027-02-01T17:00:00.000Z",
                    }
                ],
                "lastPage": 2,
            }
        )

    monkeypatch.setattr(finep.requests, "get", fake_get)

    opportunities = finep.scrape_finep()

    assert len(opportunities) == 2
    assert [item["title"] for item in opportunities] == ["Chamada 1", "Chamada 2"]
