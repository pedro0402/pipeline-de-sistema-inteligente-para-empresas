import re
from datetime import datetime

from bs4 import BeautifulSoup


def clean_html(value):
    if value is None:
        return ""

    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def parse_deadline(value):
    if not value:
        return None

    value = str(value).strip()
    # HTML antigo: "2026-05-20". API Prosas: "2026-04-28T17:00:00.000-03:00"
    if len(value) >= 10 and value[4] == "-" and value[7] == "-":
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    # Formato comum em páginas web: "Prazo para envio... 29/05/2026"
    match_br_date = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", value)
    if match_br_date:
        try:
            return datetime.strptime(match_br_date.group(1), "%d/%m/%Y").date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def clean_prosas_opportunities(raw_opportunities):
    cleaned_opportunities = []

    for opportunity in raw_opportunities:
        cleaned_opportunities.append(
            {
                "title": opportunity["title"].strip(),
                "description": clean_html(opportunity.get("description", "")),
                "link": opportunity["link"],
                "deadline": parse_deadline(opportunity.get("deadline")),
                "source_name": opportunity.get("source_name", "Prosas"),
                "source_url": opportunity.get("source_url", "https://prosas.com.br"),
            }
        )

    return cleaned_opportunities


def process_prosas_opportunities(raw_opportunities):
    return clean_prosas_opportunities(raw_opportunities)
