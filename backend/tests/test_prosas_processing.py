from datetime import date

from processing.prosas import process_prosas_opportunities


def test_process_prosas_opportunities_cleans_raw_data():
    raw_opportunities = [
        {
            "title": "  Edital Prosas 1  ",
            "description": "<p>Financiamento para <strong>projetos</strong> de inovacao.</p>",
            "link": "https://prosas.com.br/oportunidade/1",
            "deadline": "2026-05-20",
            "source_name": "Prosas",
            "source_url": "https://prosas.com.br",
        }
    ]

    cleaned_opportunities = process_prosas_opportunities(raw_opportunities)

    assert len(cleaned_opportunities) == 1
    cleaned = cleaned_opportunities[0]
    assert cleaned["title"] == "Edital Prosas 1"
    assert cleaned["description"] == "Financiamento para projetos de inovacao."
    assert cleaned["deadline"] == date(2026, 5, 20)
    assert cleaned["link"] == "https://prosas.com.br/oportunidade/1"
    assert cleaned["source_name"] == "Prosas"
    assert cleaned["source_url"] == "https://prosas.com.br"


def test_process_prosas_opportunities_parses_iso_deadline_with_timezone():
    raw = [
        {
            "title": "Edital API",
            "description": "",
            "link": "https://prosas.com.br/editais/1",
            "deadline": "2026-04-28T17:00:00.000-03:00",
            "source_name": "Prosas",
            "source_url": "https://prosas.com.br",
        }
    ]
    cleaned = process_prosas_opportunities(raw)[0]
    assert cleaned["deadline"] == date(2026, 4, 28)


def test_process_prosas_opportunities_parses_brazilian_deadline_format():
    raw = [
        {
            "title": "Edital com prazo em pt-BR",
            "description": "",
            "link": "https://prosas.com.br/editais/2",
            "deadline": "Prazo para envio de propostas até: 29/05/2026",
            "source_name": "Prosas",
            "source_url": "https://prosas.com.br",
        }
    ]
    cleaned = process_prosas_opportunities(raw)[0]
    assert cleaned["deadline"] == date(2026, 5, 29)
