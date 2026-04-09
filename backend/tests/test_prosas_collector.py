import importlib
import sys


HTML_FIXTURE = """
<html>
  <body>
    <article class="opportunity">
      <a class="opportunity-link" href="/oportunidade/1">Edital Prosas 1</a>
      <div class="opportunity-description"><p>Financiamento para projetos de inovacao.</p></div>
      <span class="opportunity-deadline">2026-05-20</span>
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
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")


def test_scrape_prosas_collects_raw_opportunities(monkeypatch):
    if "collectors.prosas" in sys.modules:
        del sys.modules["collectors.prosas"]

    prosas = importlib.import_module("collectors.prosas")

    monkeypatch.setattr(
        prosas.requests,
        "get",
        lambda url, headers=None, timeout=20: FakeResponse(HTML_FIXTURE),
    )

    opportunities = prosas.scrape_prosas()

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity["title"] == "Edital Prosas 1"
    assert opportunity["description"] == "<p>Financiamento para projetos de inovacao.</p>"
    assert opportunity["link"] == "https://prosas.com.br/oportunidade/1"
    assert opportunity["deadline"] == "2026-05-20"
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
