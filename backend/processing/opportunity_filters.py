from datetime import date


def is_active_deadline(deadline, today=None):
    if deadline is None:
        return True

    reference = today or date.today()
    return deadline >= reference


def filter_active_opportunities(opportunities, today=None):
    return [
        opportunity
        for opportunity in opportunities
        if is_active_deadline(opportunity.get("deadline"), today=today)
    ]
