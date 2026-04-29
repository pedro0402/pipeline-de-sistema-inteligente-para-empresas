from datetime import date

from processing.finep import process_finep_opportunities


def test_process_finep_opportunities_cleans_raw_data():
    raw_opportunities = [
        {
            "title": "  Finep Mais Inovação Brasil – Rodada 2  ",
            "description": "<p>Chamada para apoio à inovação</p>",
            "link": "https://www.finep.gov.br/chamadas-publicas/chamadapublica/774",
            "deadline": "Prazo para envio de propostas até: 30/09/2026",
            "source_name": "Finep",
            "source_url": "https://www.finep.gov.br",
        }
    ]

    cleaned_opportunities = process_finep_opportunities(raw_opportunities)

    assert len(cleaned_opportunities) == 1
    cleaned = cleaned_opportunities[0]
    assert cleaned["title"] == "Finep Mais Inovação Brasil – Rodada 2"
    assert cleaned["description"] == "Chamada para apoio à inovação"
    assert cleaned["deadline"] == date(2026, 9, 30)
    assert cleaned["link"] == "https://www.finep.gov.br/chamadas-publicas/chamadapublica/774"
    assert cleaned["source_name"] == "Finep"
    assert cleaned["source_url"] == "https://www.finep.gov.br"
