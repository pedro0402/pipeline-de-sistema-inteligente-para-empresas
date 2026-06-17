from datetime import date

from processing.pncp import process_pncp_opportunities


def test_process_pncp_opportunities_cleans_raw_data():
    raw_opportunities = [
        {
            "title": "  Aviso de Contratação Direta nº 00001/2021  ",
            "description": "<p>Contratação de <strong>serviço</strong> especializado</p>",
            "link": "https://pncp.gov.br/compras/00394502000144/2021/1",
            "deadline": "2026-06-30T17:00:00.000-03:00",
            "source_name": "PNCP",
            "source_url": "https://pncp.gov.br",
        }
    ]

    cleaned_opportunities = process_pncp_opportunities(raw_opportunities)

    assert len(cleaned_opportunities) == 1
    cleaned = cleaned_opportunities[0]
    assert cleaned["title"] == "Aviso de Contratação Direta nº 00001/2021"
    assert cleaned["description"] == "Contratação de serviço especializado"
    assert cleaned["deadline"] == date(2026, 6, 30)
    assert cleaned["link"] == "https://pncp.gov.br/editais/00394502000144/2021/1"
    assert cleaned["source_name"] == "PNCP"
    assert cleaned["source_url"] == "https://pncp.gov.br"
