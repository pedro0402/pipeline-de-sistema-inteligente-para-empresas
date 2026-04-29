from collectors.finep import scrape_finep
from collectors.pncp import scrape_pncp
from collectors.prosas import scrape_prosas
from core.database import SessionLocal
from models.opportunity import Opportunity
from models.source import Source
from processing.finep import process_finep_opportunities
from processing.pncp import process_pncp_opportunities
from processing.prosas import process_prosas_opportunities


def collect():
    return scrape_prosas() + scrape_pncp() + scrape_finep()


def process(items):
    prosas_items = [item for item in items if item.get("source_name") == "Prosas"]
    pncp_items = [item for item in items if item.get("source_name") == "PNCP"]
    finep_items = [item for item in items if item.get("source_name") == "Finep"]

    return (
        process_prosas_opportunities(prosas_items)
        + process_pncp_opportunities(pncp_items)
        + process_finep_opportunities(finep_items)
    )


def analyze(items):
    return items


def report(items):
    print(f"oportunidades processadas: {len(items)}")


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

            session.add(
                Opportunity(
                    source_id=source.id,
                    title=item["title"],
                    description=item.get("description"),
                    organization=source_name,
                    deadline=item.get("deadline"),
                    link=link,
                    location=item.get("location"),
                )
            )
            seen_links.add(link)

        session.commit()
    finally:
        session.close()


def main():
    print("collect")
    items = collect()
    print("process")
    items = process(items)
    print("analyze")
    items = analyze(items)
    print("save")
    save_to_db(items)
    print("report")
    report(items)
    return items


if __name__ == "__main__":
    main()
