import importlib
import sys


HTML_FIXTURE = """
<html>
  <body>
    <div class="item-separator-conteudo">
      <div class="tit_sep">
        <h2 class="header results">Abertas</h2>
      </div>
      <div class="item">
        <h3>
          <a href="/chamadas-publicas/chamadapublica/774">Finep Mais Inovação Brasil – Rodada 2</a>
        </h3>
        <div class="prazo div"><strong>Prazo para envio de propostas até: </strong><span>30/09/2026</span></div>
      </div>
    </div>
    <div class="item-separator-conteudo">
      <div class="tit_sep">
        <h2 class="header results">Encerradas</h2>
      </div>
      <div class="item">
        <h3>
          <a href="/chamadas-publicas/chamadapublica/700">Chamada Encerrada</a>
        </h3>
        <div class="prazo div"><strong>Prazo para envio de propostas até: </strong><span>01/01/2024</span></div>
      </div>
    </div>
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


def test_scrape_finep_collects_only_open_calls(monkeypatch):
    if "collectors.finep" in sys.modules:
        del sys.modules["collectors.finep"]

    finep = importlib.import_module("collectors.finep")

    def fake_get(url, headers=None, timeout=20):
        assert (
            url
            == "https://www.finep.gov.br/chamadas-publicas?situacao=aberta&tFonte=2"
        )
        return FakeResponse(HTML_FIXTURE)

    monkeypatch.setattr(finep.requests, "get", fake_get)

    opportunities = finep.scrape_finep()

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity["title"] == "Finep Mais Inovação Brasil – Rodada 2"
    assert opportunity["link"] == "https://www.finep.gov.br/chamadas-publicas/chamadapublica/774"
    assert opportunity["deadline"] == "30/09/2026"
    assert opportunity["source_name"] == "Finep"
    assert opportunity["source_url"] == "https://www.finep.gov.br"


def test_scrape_finep_collects_from_filtered_layout_without_sections(monkeypatch):
    if "collectors.finep" in sys.modules:
        del sys.modules["collectors.finep"]

    finep = importlib.import_module("collectors.finep")
    filtered_html = """
    <html>
      <body>
        <div id="conteudoChamada">
          <div class="item">
            <h3>
              <a href="/chamadas-publicas/chamadapublica/784">FIP Startup Inteligência Artificial</a>
            </h3>
            <div class="prazo div"><strong>Prazo para envio de propostas até: </strong><span>28/05/2026</span></div>
          </div>
          <div class="item">
            <h3><a href="/institucional">Link institucional</a></h3>
          </div>
        </div>
      </body>
    </html>
    """

    monkeypatch.setattr(
        finep.requests,
        "get",
        lambda url, headers=None, timeout=20: FakeResponse(filtered_html),
    )

    opportunities = finep.scrape_finep()

    assert len(opportunities) == 1
    assert opportunities[0]["title"] == "FIP Startup Inteligência Artificial"
    assert opportunities[0]["link"] == "https://www.finep.gov.br/chamadas-publicas/chamadapublica/784"
    assert opportunities[0]["deadline"] == "28/05/2026"
