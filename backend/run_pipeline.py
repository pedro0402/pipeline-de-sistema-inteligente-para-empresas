import argparse
from types import SimpleNamespace

from sqlalchemy import text

from collectors.finep import scrape_finep
from collectors.pncp import scrape_pncp
from collectors.prosas import scrape_prosas
from core.database import SessionLocal
from intelligence.scorer import score_opportunity
from models.opportunity import Opportunity
from models.opportunity_analysis import OpportunityAnalysis
from models.source import Source
from processing.finep import process_finep_opportunities
from processing.opportunity_filters import filter_active_opportunities
from processing.pncp import process_pncp_opportunities
from processing.prosas import process_prosas_opportunities
from processing.text_processor import build_processed_text

RELEVANCE_THRESHOLD = 6

_COMPANY_PROFILE_COLUMNS = (
    "SELECT id, name, sector, size, location, interests "
    "FROM company_profile"
)


def _row_to_profile(row):
    return SimpleNamespace(**dict(row))


def load_company(company_id):
    session = SessionLocal()
    try:
        row = session.execute(
            text(f"{_COMPANY_PROFILE_COLUMNS} WHERE id = :id"),
            {"id": company_id},
        ).mappings().first()
        if row is None:
            raise ValueError(f"Empresa com id={company_id} não encontrada.")
        return _row_to_profile(row)
    finally:
        session.close()


def load_all_companies():
    session = SessionLocal()
    try:
        rows = session.execute(
            text(f"{_COMPANY_PROFILE_COLUMNS} ORDER BY id")
        ).mappings().all()
        return [_row_to_profile(row) for row in rows]
    finally:
        session.close()


def collect():
    collectors = [
        ("Prosas", scrape_prosas),
        ("PNCP", scrape_pncp),
        ("Finep", scrape_finep),
    ]

    items = []
    for name, collector in collectors:
        try:
            items += collector()
        except Exception as error:
            # Falha em uma fonte não deve derrubar o pipeline inteiro.
            print(f"  [{name}] falha na coleta, fonte ignorada: {error}")

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
    active = filter_active_opportunities(result)
    expired_count = len(result) - len(active)
    if expired_count:
        print(f"  {expired_count} edital(is) expirado(s) removido(s)")
    print(f"  {len(active)}/{total} editais processados")
    return active


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


def run_for_profile(profile, items):
    print(f"\n===== empresa: {profile.name} (id={profile.id}) =====")

    # Cópia rasa de cada item para que o score de uma empresa não contamine a outra.
    items = [dict(item) for item in items]

    print("[4/5] avaliando relevância...")
    items = score(items, profile)

    print("[5/5] filtrando e salvando...")
    items = filter_relevant(items)
    save_to_db(items)

    report(items)
    return items


def main(company_id=None):
    if company_id is not None:
        print(f"carregando empresa id={company_id}")
        profiles = [load_company(company_id)]
    else:
        print("carregando todas as empresas cadastradas")
        profiles = load_all_companies()
        if not profiles:
            raise ValueError("Nenhuma empresa cadastrada em company_profile.")
        print(f"  {len(profiles)} empresa(s): " + ", ".join(p.name for p in profiles))

    print("\n[1/5] coletando editais...")
    items = collect()

    print("\n[2/5] processando...")
    items = process(items)

    print("\n[3/5] preparando textos...")
    items = analyze(items)

    results = {}
    for profile in profiles:
        results[profile.id] = run_for_profile(profile, items)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de editais relevantes por empresa.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--company-id",
        type=int,
        help="ID da empresa em company_profile (ex: --company-id 1)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Executa o pipeline para todas as empresas cadastradas",
    )
    args = parser.parse_args()
    main(None if args.all else args.company_id)
