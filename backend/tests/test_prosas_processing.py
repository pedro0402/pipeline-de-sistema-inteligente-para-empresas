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
