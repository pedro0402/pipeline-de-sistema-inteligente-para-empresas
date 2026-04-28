from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SOURCE_NAME = "Prosas"
SOURCE_URL = "https://prosas.com.br"
EDITAIS_URL = "https://produtos.prosas.com.br/editais"
THIRD_PARTY_TOKEN_URL = f"{SOURCE_URL}/auth/oauth2/token"
THIRD_PARTY_OPEN_OPPORTUNITIES_URL = (
    f"{SOURCE_URL}/selecao/api/v2/third_party/oportunidades/inscricoes_abertas"
)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
THIRD_PARTY_CLIENT_ID = "lsf6jeu7-Wk04P2iSYMdcMhPZUNZqabK8CG6mAfRQ6M"


def scrape_prosas():
    response = requests.get(EDITAIS_URL, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    opportunities = []
    seen_links = set()

    # Strategy 1: explicit card structure (kept for compatibility with tests and future page variants)
    for article in soup.select("article.opportunity"):
        link_tag = article.select_one("a.opportunity-link")
        description_tag = article.select_one("div.opportunity-description")
        deadline_tag = article.select_one("span.opportunity-deadline")

        if link_tag is None:
            continue

        link = urljoin(SOURCE_URL, link_tag.get("href", ""))

        if not link or link in seen_links:
            continue

        opportunities.append(
            {
                "title": link_tag.get_text(strip=True),
                "description": description_tag.decode_contents().strip() if description_tag else "",
                "link": link,
                "deadline": deadline_tag.get_text(strip=True) if deadline_tag else None,
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
            }
        )
        seen_links.add(link)

    # Strategy 2: generic extraction for the central page (links to /editais/...) 
    for link_tag in soup.select('a[href*="prosas.com.br/editais/"], a[href^="/editais/"]'):
        link = urljoin(SOURCE_URL, link_tag.get("href", ""))

        if not link or link in seen_links:
            continue

        title = (link_tag.get("title") or "").strip()
        if not title:
            title = link_tag.get_text(strip=True)
        if not title:
            image = link_tag.find("img")
            if image is not None:
                title = (image.get("title") or image.get("alt") or "").strip()

        opportunities.append(
            {
                "title": title or "Edital Prosas",
                "description": "",
                "link": link,
                "deadline": None,
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
            }
        )
        seen_links.add(link)

    if opportunities:
        return opportunities

    return scrape_prosas_third_party_api()


def scrape_prosas_third_party_api():
    token_response = requests.post(
        THIRD_PARTY_TOKEN_URL,
        headers={**REQUEST_HEADERS, "Content-Type": "application/json"},
        json={
            "grant_type": "client_credentials",
            "client_id": THIRD_PARTY_CLIENT_ID,
            "scope": "public",
        },
        timeout=20,
    )
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")

    if not access_token:
        return []

    response = requests.get(
        THIRD_PARTY_OPEN_OPPORTUNITIES_URL,
        headers={
            **REQUEST_HEADERS,
            "Accept": "application/vnd.api+json",
            "Authorization": f"Bearer {access_token}",
        },
        params={
            "include": "area_interesses,incentivador",
            "page[number]": 1,
            "page[size]": 20,
        },
        timeout=20,
    )
    response.raise_for_status()

    payload = response.json()
    items = payload.get("data") or []
    opportunities = []
    seen_links = set()

    for item in items:
        opportunity_id = item.get("id")
        attributes = item.get("attributes") or {}
        link = f"{SOURCE_URL}/editais/{opportunity_id}" if opportunity_id else ""

        if not link or link in seen_links:
            continue

        opportunities.append(
            {
                "title": (attributes.get("nome") or "Edital Prosas").strip(),
                "description": attributes.get("descricao") or "",
                "link": link,
                "deadline": attributes.get("data_limite_inscricao_sem_rascunho"),
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
            }
        )
        seen_links.add(link)

    return opportunities
