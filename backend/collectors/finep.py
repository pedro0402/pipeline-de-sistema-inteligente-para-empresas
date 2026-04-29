from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SOURCE_NAME = "Finep"
SOURCE_URL = "https://www.finep.gov.br"
CHAMADAS_ABERTAS_URL = f"{SOURCE_URL}/chamadas-publicas?situacao=aberta&tFonte=2"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def scrape_finep():
    response = requests.get(CHAMADAS_ABERTAS_URL, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    opportunities = []
    seen_links = set()

    items = []
    sections = soup.select("div.item-separator-conteudo")
    if sections:
        for section in sections:
            header = section.select_one("h2.header.results")
            if header is None or "abertas" not in header.get_text(strip=True).lower():
                continue
            items.extend(section.select("div.item"))
    else:
        # Página já filtrada em situação aberta (layout sem blocos por seção)
        items = soup.select("div.item")

    for item in items:
        link_tag = item.select_one('h3 a[href*="/chamadas-publicas/chamadapublica/"]')
        if link_tag is None:
            continue

        link = urljoin(SOURCE_URL, link_tag.get("href", ""))
        if not link or link in seen_links:
            continue

        prazo_value = ""
        prazo_span = item.select_one("div.prazo span")
        if prazo_span is not None:
            prazo_value = prazo_span.get_text(strip=True)

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
