from datetime import datetime

from bs4 import BeautifulSoup


def clean_html(value):
    if value is None:
        return ""

    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def parse_deadline(value):
    if not value:
        return None

    return datetime.strptime(value, "%Y-%m-%d").date()


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
