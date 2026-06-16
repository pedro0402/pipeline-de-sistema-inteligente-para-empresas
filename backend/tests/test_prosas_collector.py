import importlib
import sys


HTML_FIXTURE = """
<html>
  <body>
    <article class="opportunity">
      <a class="opportunity-link" href="/oportunidade/1">Edital Prosas 1</a>
      <div class="opportunity-description"><p>Financiamento para projetos de inovacao.</p></div>
      <span class="opportunity-deadline">2027-05-20</span>
    </article>
  </body>
</html>
"""

HTML_EDITAIS_FIXTURE = """
<html>
  <body>
    <a href="https://prosas.com.br/editais/17560-instituto-rizon-edital-venture-philanthropy-2026"
       title="Edital Orizon 2026">
      <img src="/assets/edital-orizon.webp" title="Edital Orizon 2026" />
    </a>
  </body>
</html>
"""


class FakeResponse:
    def __init__(self, text, status_code=200, json_payload=None):
        self.text = text
        self.status_code = status_code
        self._json_payload = json_payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def json(self):
        if self._json_payload is None:
            raise RuntimeError("JSON payload not configured")
        return self._json_payload


def test_scrape_prosas_collects_raw_opportunities(monkeypatch):
    if "collectors.prosas" in sys.modules:
        del sys.modules["collectors.prosas"]

    prosas = importlib.import_module("collectors.prosas")

    monkeypatch.setattr(
        prosas.requests,
        "get",
        lambda url, headers=None, timeout=20, params=None: FakeResponse(HTML_FIXTURE),
    )

    opportunities = prosas.scrape_prosas()

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity["title"] == "Edital Prosas 1"
    assert opportunity["description"] == "<p>Financiamento para projetos de inovacao.</p>"
    assert opportunity["link"] == "https://prosas.com.br/oportunidade/1"
    assert opportunity["deadline"] == "2027-05-20"
    assert opportunity["source_name"] == "Prosas"
    assert opportunity["source_url"] == "https://prosas.com.br"


def test_scrape_prosas_collects_editais_links_when_no_cards(monkeypatch):
    if "collectors.prosas" in sys.modules:
        del sys.modules["collectors.prosas"]

    prosas = importlib.import_module("collectors.prosas")

    monkeypatch.setattr(
        prosas.requests,
        "get",
        lambda url, headers=None, timeout=20: FakeResponse(HTML_EDITAIS_FIXTURE),
    )

    opportunities = prosas.scrape_prosas()

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity["title"] == "Edital Orizon 2026"
    assert opportunity["description"] == ""
    assert opportunity["link"] == "https://prosas.com.br/editais/17560-instituto-rizon-edital-venture-philanthropy-2026"
    assert opportunity["deadline"] is None


def test_scrape_prosas_falls_back_to_central_api_when_page_has_no_links(monkeypatch):
    if "collectors.prosas" in sys.modules:
        del sys.modules["collectors.prosas"]

    prosas = importlib.import_module("collectors.prosas")
    empty_page = "<html><body><h1>Central de Editais</h1></body></html>"
    api_payload = {
        "data": [
            {
                "id": "123",
                "attributes": {
                    "nome": "Edital de teste",
                    "descricao": "<p>Descricao</p>",
                    "data_limite_inscricao_sem_rascunho": "2027-05-30",
                },
            }
        ]
    }

    def fake_get(url, headers=None, timeout=20, params=None):
        if "inscricoes_abertas" in url:
            return FakeResponse("{}", json_payload=api_payload)
        return FakeResponse(empty_page)

    def fake_post(url, headers=None, json=None, timeout=20):
        return FakeResponse("{}", json_payload={"access_token": "token-teste"})

    monkeypatch.setattr(prosas.requests, "get", fake_get)
    monkeypatch.setattr(prosas.requests, "post", fake_post)

    opportunities = prosas.scrape_prosas()

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity["title"] == "Edital de teste"
    assert opportunity["description"] == "<p>Descricao</p>"
    assert opportunity["link"] == "https://prosas.com.br/editais/123"
    assert opportunity["deadline"] == "2027-05-30"
