import re
from functools import lru_cache

import requests

from processing.prosas import clean_html, parse_deadline

FINEP_SOURCE_URL = "https://www.finep.gov.br"
FINEP_DETAIL_SITE_ID = 222684
FINEP_API_URL = f"{FINEP_SOURCE_URL}/o/c/chamadapublicas"
FINEP_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def build_finep_link(api_id):
    return f"{FINEP_SOURCE_URL}/e/chamada-publica/{FINEP_DETAIL_SITE_ID}/{api_id}"


@lru_cache(maxsize=512)
def resolve_finep_api_id_by_database_id(database_id):
    try:
        response = requests.get(
            FINEP_API_URL,
            params={"filter": f"databaseId eq {int(database_id)}", "pageSize": 1},
            headers=FINEP_REQUEST_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        items = response.json().get("items") or []
        if not items:
            return None
        return items[0].get("id")
    except Exception:
        return None


def normalize_finep_link(link):
    if not link:
        return link

    if "/e/chamada-publica/" in link:
        return link

    match = re.search(r"/chamadas-publicas/chamadapublica/(\d+)", link)
    if not match:
        return link

    api_id = resolve_finep_api_id_by_database_id(match.group(1))
    if api_id:
        return build_finep_link(api_id)

    return link


def is_valid_finep_link(link):
    if not link:
        return False

    lowered = link.lower()
    if "/editais/" in lowered:
        return False

    return "/e/chamada-publica/" in link or "/chamadas-publicas/chamadapublica/" in link


def clean_finep_opportunities(raw_opportunities):
    cleaned_opportunities = []

    for opportunity in raw_opportunities:
        cleaned_opportunities.append(
            {
                "title": opportunity["title"].strip(),
                "description": clean_html(opportunity.get("description", "")),
                "link": normalize_finep_link(opportunity["link"]),
                "deadline": parse_deadline(opportunity.get("deadline")),
                "source_name": opportunity.get("source_name", "Finep"),
                "source_url": opportunity.get("source_url", FINEP_SOURCE_URL),
            }
        )

    return cleaned_opportunities


def process_finep_opportunities(raw_opportunities):
    return clean_finep_opportunities(raw_opportunities)
