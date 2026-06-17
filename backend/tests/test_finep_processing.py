from datetime import date

from processing.finep import build_finep_link, is_valid_finep_link, normalize_finep_link, process_finep_opportunities


def test_build_finep_link_uses_new_portal_format():
    assert (
        build_finep_link(754567)
        == "https://www.finep.gov.br/e/chamada-publica/222684/754567"
    )


def test_process_finep_opportunities_cleans_raw_data(monkeypatch):
    from processing import finep as finep_module

    finep_module.resolve_finep_api_id_by_database_id.cache_clear()
    monkeypatch.setattr(
        finep_module,
        "resolve_finep_api_id_by_database_id",
        lambda database_id: 754567 if str(database_id) == "772" else None,
    )

    raw_opportunities = [
        {
            "title": "  Finep Mais Inovação Brasil – Rodada 2  ",
            "description": "<p>Contratação de <strong>serviço</strong> especializado</p>",
            "link": "https://www.finep.gov.br/chamadas-publicas/chamadapublica/772",
            "deadline": "2026-06-30T17:00:00.000-03:00",
            "source_name": "Finep",
            "source_url": "https://www.finep.gov.br",
        }
    ]

    cleaned_opportunities = process_finep_opportunities(raw_opportunities)

    assert len(cleaned_opportunities) == 1
    cleaned = cleaned_opportunities[0]
    assert cleaned["title"] == "Finep Mais Inovação Brasil – Rodada 2"
    assert cleaned["description"] == "Contratação de serviço especializado"
    assert cleaned["deadline"] == date(2026, 6, 30)
    assert cleaned["link"] == "https://www.finep.gov.br/e/chamada-publica/222684/754567"


def test_normalize_finep_link_keeps_new_format():
    link = "https://www.finep.gov.br/e/chamada-publica/222684/968467"
    assert normalize_finep_link(link) == link


def test_is_valid_finep_link_rejects_fake_editais_paths():
    assert is_valid_finep_link("https://finep.gov.br/editais/inovacao-2026") is False
    assert is_valid_finep_link("https://finep.gov.br/editais/ia-2026") is False


def test_is_valid_finep_link_accepts_official_formats():
    assert is_valid_finep_link("https://www.finep.gov.br/e/chamada-publica/222684/754567") is True
    assert is_valid_finep_link("https://www.finep.gov.br/chamadas-publicas/chamadapublica/772") is True
