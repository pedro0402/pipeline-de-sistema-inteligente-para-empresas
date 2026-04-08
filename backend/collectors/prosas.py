from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SOURCE_NAME = "Prosas"
SOURCE_URL = "https://prosas.com.br"
EDITAIS_URL = "https://produtos.prosas.com.br/editais"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


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

    return opportunities
