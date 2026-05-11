from __future__ import annotations

from pathlib import Path

import app as dashboard_app
from pipeline.models import PipelineRun


def test_build_token_report_dict_aggregates_phase_and_reviewer_tokens() -> None:
    run = PipelineRun(
        run_id="run-token-1",
        title="Token Run",
        created_at="2026-03-29T10:00:00",
    )
    run.phases[0].result = {
        "duration": 1.5,
        "cache_read_tokens": 100,
        "cache_write_tokens": 50,
        "thinking_budget": 10,
        "km_model": "claude-sonnet-4-6",
    }
    run.phases[1].result = {
        "duration": 2.0,
        "results": {
            "google": {
                "ki_name": "Gemini",
                "duration": 1.9,
                "cache_read_tokens": 30,
                "cache_write_tokens": 20,
                "thinking_budget": 5,
            }
        },
    }
    run.phases[2].result = {
        "duration": 0.8,
        "cache_read_tokens": 40,
        "cache_write_tokens": 10,
        "thinking_budget": 2,
    }

    report = dashboard_app._build_token_report_dict(run)

    assert report["run_id"] == "run-token-1"
    assert report["totals"]["cache_read_tokens"] == 170
    assert report["totals"]["cache_write_tokens"] == 80
    assert report["totals"]["thinking_tokens"] == 17
    assert len(report["phases"]) == 5
    assert report["phases"][1]["reviewers"][0]["reviewer_name"] == "Gemini"


def test_phase2_and_phase3_reports_are_written_to_configured_dirs(
    monkeypatch, tmp_path: Path
) -> None:
    review_dir = tmp_path / "review_ergebnisse"
    konsolidierung_dir = tmp_path / "konsolidierungen"
    token_dir = tmp_path / "token_reports"
    monkeypatch.setattr(
        dashboard_app,
        "_load_config",
        lambda: {
            "review_results_dir": {"path": str(review_dir)},
            "konsolidierungen_dir": {"path": str(konsolidierung_dir)},
            "token_reports_dir": {"path": str(token_dir)},
        },
    )

    run = PipelineRun(
        run_id="run-save-1",
        title="Run Save",
        created_at="2026-03-29T12:00:00",
    )
    phase2_result = {
        "results": {"r1": {"ki_name": "Reviewer 1", "role": "Role", "duration": 2.1, "text": "OK"}},
        "errors": {},
    }
    phase3_result = {"consolidation_text": "Konsolidiertes Ergebnis"}

    phase2_target = dashboard_app._save_phase2_report(run, phase2_result)
    phase3_target = dashboard_app._save_phase3_report(run, phase3_result)

    assert phase2_target.exists()
    assert phase2_target.parent == review_dir
    assert "Reviewer 1" in phase2_target.read_text(encoding="utf-8")

    assert phase3_target.exists()
    assert phase3_target.parent == konsolidierung_dir
    assert "Konsolidiertes Ergebnis" in phase3_target.read_text(encoding="utf-8")
