import importlib
import sys


def test_run_pipeline_executes_steps_in_order(monkeypatch, capsys):
    if "run_pipeline" in sys.modules:
        del sys.modules["run_pipeline"]

    run_pipeline = importlib.import_module("run_pipeline")
    executed_steps = []

    monkeypatch.setattr(run_pipeline, "collect", lambda: executed_steps.append("collect") or [])
    monkeypatch.setattr(
        run_pipeline,
        "process",
        lambda items: executed_steps.append("process") or items,
    )
    monkeypatch.setattr(
        run_pipeline,
        "analyze",
        lambda items: executed_steps.append("analyze") or items,
    )
    monkeypatch.setattr(
        run_pipeline,
        "save_to_db",
        lambda items: executed_steps.append("save") or None,
    )
    monkeypatch.setattr(
        run_pipeline,
        "report",
        lambda items: executed_steps.append("report") or None,
    )

    result = run_pipeline.main()
    captured = capsys.readouterr()

    assert executed_steps == ["collect", "process", "analyze", "save", "report"]
    assert result == []
    assert "collect" in captured.out
    assert "process" in captured.out
    assert "analyze" in captured.out
    assert "save" in captured.out
    assert "report" in captured.out
