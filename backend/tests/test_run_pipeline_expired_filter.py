import importlib
import sys
from datetime import date


def test_process_removes_expired_opportunities(monkeypatch, capsys):
    if "run_pipeline" in sys.modules:
        del sys.modules["run_pipeline"]

    run_pipeline = importlib.import_module("run_pipeline")

    raw_items = [
        {
            "title": "Edital ativo",
            "description": "desc",
            "link": "https://example.com/ativo",
            "deadline": "2026-12-31",
            "source_name": "Prosas",
            "source_url": "https://prosas.com.br",
        },
        {
            "title": "Edital expirado",
            "description": "desc",
            "link": "https://example.com/expirado",
            "deadline": "2024-01-01",
            "source_name": "Prosas",
            "source_url": "https://prosas.com.br",
        },
    ]

    monkeypatch.setattr(
        run_pipeline,
        "process_prosas_opportunities",
        lambda items: [
            {
                "title": "Edital ativo",
                "description": "desc",
                "link": "https://example.com/ativo",
                "deadline": date(2026, 12, 31),
                "source_name": "Prosas",
                "source_url": "https://prosas.com.br",
            },
            {
                "title": "Edital expirado",
                "description": "desc",
                "link": "https://example.com/expirado",
                "deadline": date(2024, 1, 1),
                "source_name": "Prosas",
                "source_url": "https://prosas.com.br",
            },
        ],
    )
    monkeypatch.setattr(run_pipeline, "process_pncp_opportunities", lambda items: [])
    monkeypatch.setattr(run_pipeline, "process_finep_opportunities", lambda items: [])

    result = run_pipeline.process(raw_items)
    captured = capsys.readouterr()

    assert len(result) == 1
    assert result[0]["title"] == "Edital ativo"
    assert "expirado" in captured.out.lower()
