import re
from bs4 import BeautifulSoup


def remove_html(text):
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)


def normalize_whitespace(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_special_characters(text):
    return re.sub(r"[^\w\s\.,;:!\?\-\(\)\/]", "", text, flags=re.UNICODE)


def truncate(text, max_chars=1000):
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def build_processed_text(title, description, organization=None, deadline=None):
    parts = []

    if title:
        parts.append(f"Título: {title.strip()}")

    if organization:
        parts.append(f"Organização: {organization.strip()}")

    if deadline:
        parts.append(f"Prazo: {deadline}")

    if description:
        clean_desc = remove_html(description)
        clean_desc = normalize_whitespace(clean_desc)
        clean_desc = remove_special_characters(clean_desc)
        clean_desc = truncate(clean_desc)
        if clean_desc:
            parts.append(f"Descrição: {clean_desc}")

    result = "\n".join(parts)
    return result.encode("utf-8", errors="ignore").decode("utf-8")