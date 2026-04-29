from processing.prosas import clean_html, parse_deadline


def clean_finep_opportunities(raw_opportunities):
    cleaned_opportunities = []

    for opportunity in raw_opportunities:
        cleaned_opportunities.append(
            {
                "title": opportunity["title"].strip(),
                "description": clean_html(opportunity.get("description", "")),
                "link": opportunity["link"],
                "deadline": parse_deadline(opportunity.get("deadline")),
                "source_name": opportunity.get("source_name", "Finep"),
                "source_url": opportunity.get("source_url", "https://www.finep.gov.br"),
            }
        )

    return cleaned_opportunities


def process_finep_opportunities(raw_opportunities):
    return clean_finep_opportunities(raw_opportunities)
