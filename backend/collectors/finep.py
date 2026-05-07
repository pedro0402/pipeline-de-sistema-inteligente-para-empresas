from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SOURCE_NAME = "Finep"
SOURCE_URL = "https://www.finep.gov.br"
CHAMADAS_URL = f"{SOURCE_URL}/chamadas-publicas"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def _fetch_page(start):
    response = requests.get(
        CHAMADAS_URL,
        params={"situacao": "aberta", "tFonte": "2", "start": start},
        headers=REQUEST_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _parse_items(soup, seen_links):
    opportunities = []

    items = []
    sections = soup.select("div.item-separator-conteudo")
    if sections:
        for section in sections:
            header = section.select_one("h2.header.results")
            if header is None or "abertas" not in header.get_text(strip=True).lower():
                continue
            items.extend(section.select("div.item"))
    else:
        items = soup.select("div.item")

    for item in items:
        link_tag = item.select_one('h3 a[href*="/chamadas-publicas/chamadapublica/"]')
        if link_tag is None:
            continue

        link = urljoin(SOURCE_URL, link_tag.get("href", ""))
        if not link or link in seen_links:
            continue

        prazo_span = item.select_one("div.prazo span")
        prazo_value = prazo_span.get_text(strip=True) if prazo_span else ""

        opportunities.append(
            {
                "title": link_tag.get_text(strip=True),
                "description": "",
                "link": link,
                "deadline": prazo_value or None,
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
            }
        )
        seen_links.add(link)

    return opportunities


def _get_page_size(soup):
    items = soup.select("div.item")
    return len(items)


def scrape_finep():
    opportunities = []
    seen_links = set()
    start = 0

    first_soup = _fetch_page(start)
    page_items = _parse_items(first_soup, seen_links)
    opportunities.extend(page_items)
    page_size = _get_page_size(first_soup) or 10

    while len(page_items) == page_size:
        start += page_size
        soup = _fetch_page(start)
        page_items = _parse_items(soup, seen_links)
        opportunities.extend(page_items)

    print(f"  [Finep] {len(opportunities)} editais coletados")
    return opportunities
