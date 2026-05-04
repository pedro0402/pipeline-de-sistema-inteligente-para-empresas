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
PAGE_SIZE = 50


def _is_edital_title(title):
    return "edital" in (title or "").strip().lower()


def _parse_pncp_publication_datetime(value):
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _fetch_page(page):
    response = requests.get(
        SEARCH_URL,
        params={
            "tipos_documento": "edital",
            "status": "aberta",
            "pagina": page,
            "tam_pagina": PAGE_SIZE,
            "ordenacao": "data_publicacao_pncp_desc",
        },
        headers=REQUEST_HEADERS,
        timeout=20,
    )
    if response.status_code == 400:
        return None
    response.raise_for_status()
    return response.json().get("items") or []


def scrape_pncp():
    opportunities = []
    seen_links = set()
    page = 1

    while True:
        items = _fetch_page(page)
        if items is None or not items:
            break

        items = sorted(
            items,
            key=lambda it: _parse_pncp_publication_datetime(it.get("data_publicacao_pncp")) or datetime.min,
            reverse=True,
        )

        for item in items:
            title = (item.get("title") or "Edital PNCP").strip()
            raw_link = item.get("item_url", "")
            link = urljoin(SOURCE_URL, raw_link)

            if not link or link in seen_links or not _is_edital_title(title):
                continue

            opportunities.append(
                {
                    "title": title,
                    "description": item.get("description") or "",
                    "link": link,
                    "deadline": item.get("data_fim_vigencia") or item.get("data_encerramento_proposta"),
                    "source_name": SOURCE_NAME,
                    "source_url": SOURCE_URL,
                }
            )
            seen_links.add(link)

        page += 1

    print(f"  [PNCP] {len(opportunities)} editais coletados ({page - 1} páginas)")
    return opportunities
