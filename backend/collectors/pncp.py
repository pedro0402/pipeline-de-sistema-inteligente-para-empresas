import time
from datetime import datetime

import requests

from processing.opportunity_filters import is_active_deadline
from processing.pncp import normalize_pncp_link
from processing.prosas import parse_deadline


SOURCE_NAME = "PNCP"
SOURCE_URL = "https://pncp.gov.br"
SEARCH_URL = f"{SOURCE_URL}/api/search"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
PAGE_SIZE = 50
# A busca aberta do PNCP retorna milhões de resultados; como a ordenação é por
# data de publicação decrescente, coletamos apenas as páginas mais recentes.
MAX_PAGES = 5
MAX_RETRIES = 5
RETRY_BACKOFF_SECONDS = 1.5


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
    # A API do PNCP derruba conexões de forma intermitente (WAF/rate limit),
    # então cada página é tentada com retry e backoff exponencial.
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
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
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as error:
            if isinstance(error, requests.HTTPError) and error.response is not None and error.response.status_code < 500:
                raise
            last_error = error
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))

    raise last_error


def scrape_pncp():
    opportunities = []
    seen_links = set()
    page = 1

    while page <= MAX_PAGES:
        try:
            items = _fetch_page(page)
        except Exception as error:
            # Mantém o que já foi coletado em vez de perder tudo.
            print(f"  [PNCP] página {page} falhou após {MAX_RETRIES} tentativas: {error}")
            break

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
            link = normalize_pncp_link(raw_link, SOURCE_URL)

            if not link or link in seen_links or not _is_edital_title(title):
                continue

            deadline_raw = item.get("data_fim_vigencia") or item.get("data_encerramento_proposta")
            if not is_active_deadline(parse_deadline(deadline_raw)):
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
