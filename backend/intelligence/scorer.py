import re
import unicodedata


def _normalize(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFD", text)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return without_accents.lower()


def _parse_interests(interests_str):
    if not interests_str:
        return []
    return [kw.strip() for kw in interests_str.split(",") if kw.strip()]


def score_opportunity(profile, edital):
    keywords = _parse_interests(profile.interests)
    if not keywords:
        return {"relevance_score": 0, "summary": "", "recommended_action": "Ignorar"}

    edital_text = _normalize(
        f"{edital.get('title', '')} {edital.get('description', '')}"
    )

    matched = [kw for kw in keywords if re.search(r"\b" + re.escape(_normalize(kw)) + r"\b", edital_text)]

    score = round((len(matched) / len(keywords)) * 10)

    if matched:
        summary = f"Palavras encontradas: {', '.join(matched)}."
    else:
        summary = "Nenhuma palavra de interesse encontrada."

    if score >= 6:
        recommended_action = "Candidatar-se"
    elif score >= 3:
        recommended_action = "Monitorar"
    else:
        recommended_action = "Ignorar"

    return {
        "relevance_score": score,
        "summary": summary,
        "recommended_action": recommended_action,
    }
