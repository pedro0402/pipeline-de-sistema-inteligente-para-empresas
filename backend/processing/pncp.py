from urllib.parse import urljoin

from processing.prosas import clean_html, parse_deadline

PNCP_BASE_URL = "https://pncp.gov.br"


def normalize_pncp_link(raw_link, base_url=PNCP_BASE_URL):
    link = urljoin(base_url, raw_link or "")
    if "/compras/" in link:
        return link.replace("/compras/", "/editais/", 1)
    return link


def clean_pncp_opportunities(raw_opportunities):
    cleaned_opportunities = []

    for opportunity in raw_opportunities:
        cleaned_opportunities.append(
            {
                "title": opportunity["title"].strip(),
                "description": clean_html(opportunity.get("description", "")),
                "link": normalize_pncp_link(opportunity["link"]),
                "deadline": parse_deadline(opportunity.get("deadline")),
                "source_name": opportunity.get("source_name", "PNCP"),
                "source_url": opportunity.get("source_url", "https://pncp.gov.br"),
            }
        )

    return cleaned_opportunities


def process_pncp_opportunities(raw_opportunities):
    return clean_pncp_opportunities(raw_opportunities)
