from datetime import date

from processing.opportunity_filters import filter_active_opportunities, is_active_deadline


def test_is_active_deadline_keeps_future_and_today_deadlines():
    today = date(2026, 6, 16)

    assert is_active_deadline(date(2026, 6, 16), today=today) is True
    assert is_active_deadline(date(2026, 12, 31), today=today) is True


def test_is_active_deadline_rejects_past_deadlines():
    today = date(2026, 6, 16)

    assert is_active_deadline(date(2026, 6, 15), today=today) is False
    assert is_active_deadline(date(2024, 1, 1), today=today) is False


def test_is_active_deadline_keeps_missing_deadline():
    today = date(2026, 6, 16)

    assert is_active_deadline(None, today=today) is True


def test_filter_active_opportunities_removes_expired_items():
    today = date(2026, 6, 16)
    opportunities = [
        {"title": "Ativo", "deadline": date(2026, 6, 30)},
        {"title": "Expirado", "deadline": date(2026, 1, 1)},
        {"title": "Sem prazo", "deadline": None},
    ]

    result = filter_active_opportunities(opportunities, today=today)

    assert [item["title"] for item in result] == ["Ativo", "Sem prazo"]
