import requests

from processing.finep import FINEP_API_URL, FINEP_REQUEST_HEADERS, FINEP_SOURCE_URL, build_finep_link
from processing.opportunity_filters import is_active_deadline
from processing.prosas import parse_deadline


SOURCE_NAME = "Finep"
SOURCE_URL = FINEP_SOURCE_URL
OPEN_FILTER = "situacao eq 'aberta'"
PAGE_SIZE = 50


def _fetch_page(page):
    response = requests.get(
        FINEP_API_URL,
        params={
            "filter": OPEN_FILTER,
            "sort": "dataDePublicacao:desc",
            "page": page,
            "pageSize": PAGE_SIZE,
        },
        headers=FINEP_REQUEST_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def scrape_finep():
    opportunities = []
    seen_links = set()
    page = 1

    while True:
        payload = _fetch_page(page)
        items = payload.get("items") or []
        if not items:
            break

        for item in items:
            api_id = item.get("id")
            if not api_id:
                continue

            deadline_raw = item.get("prazoProposto")
            if not is_active_deadline(parse_deadline(deadline_raw)):
                continue

            link = build_finep_link(api_id)
            if link in seen_links:
                continue

            opportunities.append(
                {
                    "title": (item.get("titulo") or "Chamada Finep").strip(),
                    "description": item.get("descricao") or "",
                    "link": link,
                    "deadline": deadline_raw,
                    "source_name": SOURCE_NAME,
                    "source_url": SOURCE_URL,
                }
            )
            seen_links.add(link)

        if page >= payload.get("lastPage", 1):
            break
        page += 1

    print(f"  [Finep] {len(opportunities)} editais coletados ({page} páginas)")
    return opportunities
