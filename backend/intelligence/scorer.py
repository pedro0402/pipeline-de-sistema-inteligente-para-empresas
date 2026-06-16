import json
import re
import unicodedata


def _normalize(text):
    if not text:
        return ""

    text = str(text)

    nfkd = unicodedata.normalize("NFD", text)
    without_accents = "".join(
        c for c in nfkd
        if not unicodedata.combining(c)
    )

    return without_accents.lower()


def _parse_interests(interests_value):
    if not interests_value:
        return []

    if isinstance(interests_value, list):
        return [
            str(interest).strip()
            for interest in interests_value
            if str(interest).strip()
        ]

    try:
        parsed = json.loads(interests_value)

        if isinstance(parsed, list):
            return [
                str(interest).strip()
                for interest in parsed
                if str(interest).strip()
            ]

    except Exception:
        pass

    return [
        kw.strip()
        for kw in str(interests_value).split(",")
        if kw.strip()
    ]


def _contains_keyword(text, keyword):
    normalized_keyword = _normalize(keyword)

    if not normalized_keyword:
        return False

    pattern = r"\b" + re.escape(normalized_keyword) + r"\b"

    return re.search(pattern, text) is not None


def score_opportunity(profile, edital):
    keywords = _parse_interests(getattr(profile, "interests", None))

    edital_text = _normalize(
        f"""
        {edital.get('title', '')}
        {edital.get('description', '')}
        {edital.get('processed_text', '')}
        {edital.get('organization', '')}
        {edital.get('source_name', '')}
        {edital.get('location', '')}
        """
    )

    if not keywords:
        return {
            "relevance_score": 0,
            "summary": "Empresa sem interesses cadastrados.",
            "recommended_action": "Cadastrar interesses da empresa."
        }

    matched = [
        keyword
        for keyword in keywords
        if _contains_keyword(edital_text, keyword)
    ]

    score = 0

    if matched:
        score += len(matched) * 3

    strategic_keywords = [
        "edital",
        "chamada publica",
        "fomento",
        "subvencao",
        "financiamento",
        "licitacao",
        "contratacao",
        "projeto",
        "inovacao",
        "tecnologia",
        "pesquisa",
        "desenvolvimento",
        "sustentabilidade",
        "saude",
        "educacao",
        "infraestrutura",
        "inteligencia artificial",
    ]

    strategic_matches = [
        keyword
        for keyword in strategic_keywords
        if _contains_keyword(edital_text, keyword)
    ]

    score += len(strategic_matches) * 0.5

    sector = getattr(profile, "sector", None)

    if sector and _contains_keyword(edital_text, sector):
        score += 2

    location = getattr(profile, "location", None)

    if location and _contains_keyword(edital_text, location):
        score += 1

    score = min(score, 10)
    score = round(score, 1)

    if matched:
        summary = f"Interesses encontrados: {', '.join(matched)}."
    else:
        summary = "Nenhum interesse direto encontrado, mas a oportunidade pode conter termos estratégicos."

    if strategic_matches:
        summary += f" Termos estratégicos encontrados: {', '.join(strategic_matches[:5])}."

    if score >= 7:
        recommended_action = "Alta prioridade: avaliar candidatura."
    elif score >= 4:
        recommended_action = "Média prioridade: analisar requisitos."
    elif score > 0:
        recommended_action = "Baixa prioridade: monitorar oportunidade."
    else:
        recommended_action = "Ignorar."

    return {
        "relevance_score": score,
        "summary": summary,
        "recommended_action": recommended_action,
    }