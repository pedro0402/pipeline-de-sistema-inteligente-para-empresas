from datetime import datetime
from urllib.parse import urljoin

import requests


SOURCE_NAME = "PNCP"
SOURCE_URL = "https://pncp.gov.br"
SEARCH_URL = f"{SOURCE_URL}/api/search"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def _parse_pncp_publication_datetime(value):
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def scrape_pncp(page=1, page_size=20):
    response = requests.get(
        SEARCH_URL,
        params={
            "tipos_documento": "edital",
            "status": "aberta",
            "pagina": page,
            "tam_pagina": page_size,
            "ordenacao": "data_publicacao_pncp_desc",
        },
        headers=REQUEST_HEADERS,
        timeout=20,
    )
    response.raise_for_status()

    payload = response.json()
    items = payload.get("items") or []
    items = sorted(
        items,
        key=lambda it: _parse_pncp_publication_datetime(it.get("data_publicacao_pncp"))
        or datetime.min,
        reverse=True,
    )
    opportunities = []
    seen_links = set()

    for item in items:
        raw_link = item.get("item_url", "")
        link = urljoin(SOURCE_URL, raw_link)

        if not link or link in seen_links:
            continue

        opportunities.append(
            {
                "title": (item.get("title") or "Edital PNCP").strip(),
                "description": item.get("description") or "",
                "link": link,
                "deadline": item.get("data_fim_vigencia")
                or item.get("data_encerramento_proposta"),
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
            }
        )
        seen_links.add(link)

    return opportunities
