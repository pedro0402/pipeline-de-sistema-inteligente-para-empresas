import argparse

from collectors.finep import scrape_finep
from collectors.pncp import scrape_pncp
from collectors.prosas import scrape_prosas
from core.database import SessionLocal
from intelligence.scorer import score_opportunity
from models.company_profile import CompanyProfile
from models.opportunity import Opportunity
from models.opportunity_analysis import OpportunityAnalysis
from models.source import Source
from processing.finep import process_finep_opportunities
from processing.pncp import process_pncp_opportunities
from processing.prosas import process_prosas_opportunities
from processing.text_processor import build_processed_text

RELEVANCE_THRESHOLD = 6


def load_company(company_id):
    session = SessionLocal()
    try:
        profile = session.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
        if profile is None:
            raise ValueError(f"Empresa com id={company_id} não encontrada.")
        session.expunge(profile)
        return profile
    finally:
        session.close()


def collect():
    items = scrape_prosas() + scrape_pncp() + scrape_finep()
    print(f"  total coletado: {len(items)} editais")
    return items


def process(items):
    total = len(items)
    prosas_items = [item for item in items if item.get("source_name") == "Prosas"]
    pncp_items = [item for item in items if item.get("source_name") == "PNCP"]
    finep_items = [item for item in items if item.get("source_name") == "Finep"]

    result = (
        process_prosas_opportunities(prosas_items)
        + process_pncp_opportunities(pncp_items)
        + process_finep_opportunities(finep_items)
    )
    print(f"  {len(result)}/{total} editais processados")
    return result


def analyze(items):
    total = len(items)
    for i, item in enumerate(items):
        item["processed_text"] = build_processed_text(
            title=item.get("title"),
            description=item.get("description"),
            organization=item.get("source_name"),
            deadline=str(item["deadline"]) if item.get("deadline") else None,
        )
        print(f"\r  [{i + 1}/{total}] textos preparados", end="", flush=True)
    print()
    return items


def score(items, profile):
    total = len(items)
    for i, item in enumerate(items):
        result = score_opportunity(profile, item)
        item.update(result)
        print(f"\r  [{i + 1}/{total}] avaliados  (score={result['relevance_score']}) — {item.get('title', '')[:50]:<50}", end="", flush=True)
    print()
    return items


def filter_relevant(items):
    return [item for item in items if item.get("relevance_score", 0) >= RELEVANCE_THRESHOLD]


def report(items):
    print(f"\n--- {len(items)} edital(is) relevante(s) encontrado(s) ---")
    for item in sorted(items, key=lambda x: x.get("relevance_score", 0), reverse=True):
        print(
            f"  [{item.get('relevance_score', 0)}/10] {item.get('title', '')}\n"
            f"           {item.get('summary', '')}\n"
            f"           Ação: {item.get('recommended_action', '')}\n"
            f"           Link: {item.get('link', '')}\n"
        )


def save_to_db(items):
    session = SessionLocal()
    seen_links = set()

    try:
        for item in items:
            source_name = item.get("source_name", "Prosas")
            source_url = item.get("source_url", "https://prosas.com.br")

            source = (
                session.query(Source)
                .filter(Source.name == source_name, Source.base_url == source_url)
                .first()
            )

            if source is None:
                source = Source(name=source_name, base_url=source_url)
                session.add(source)
                session.flush()

            link = item["link"]

            if link in seen_links:
                continue

            exists = session.query(Opportunity.id).filter(Opportunity.link == link).first()

            if exists is not None:
                continue

            opportunity = Opportunity(
                source_id=source.id,
                title=item["title"],
                description=item.get("description"),
                organization=source_name,
                deadline=item.get("deadline"),
                link=link,
                location=item.get("location"),
            )
            session.add(opportunity)
            session.flush()

            session.add(
                OpportunityAnalysis(
                    opportunity_id=opportunity.id,
                    processed_text=item.get("processed_text"),
                    relevance_score=item.get("relevance_score"),
                    summary=item.get("summary"),
                    recommended_action=item.get("recommended_action"),
                )
            )

            seen_links.add(link)

        session.commit()
    finally:
        session.close()


def main(company_id):
    print(f"carregando empresa id={company_id}")
    profile = load_company(company_id)
    print(f"  empresa: {profile.name}")

    print("\n[1/5] coletando editais...")
    items = collect()

    print("\n[2/5] processando...")
    items = process(items)

    print("\n[3/5] preparando textos...")
    items = analyze(items)

    print("\n[4/5] avaliando relevância...")
    items = score(items, profile)

    print("\n[5/5] filtrando e salvando...")
    items = filter_relevant(items)
    save_to_db(items)

    report(items)
    return items


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de editais relevantes por empresa.")
    parser.add_argument(
        "--company-id",
        type=int,
        required=True,
        help="ID da empresa em company_profile (ex: --company-id 1)",
    )
    args = parser.parse_args()
    main(args.company_id)
