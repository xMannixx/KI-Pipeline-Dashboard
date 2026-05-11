from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from pipeline import state_machine as sm
from pipeline.config_alias import normalize_teamleiter_aliases, reset_alias_warning_for_tests


def _setup_temp_audit(monkeypatch, tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    audit_file = data_dir / "audit.jsonl"
    monkeypatch.setattr(sm, "DATA_DIR", data_dir)
    monkeypatch.setattr(sm, "AUDIT_FILE", audit_file)
    return audit_file


def test_teamleiter_alias_prefers_primary_keys() -> None:
    cfg = {
        "teamleiter": {"provider": "openai", "model": "o3"},
        "konzertmeister": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        "teamleiter_choices": [{"label": "Primary", "provider": "openai", "model": "o3"}],
        "konzertmeister_choices": [
            {"label": "Legacy", "provider": "anthropic", "model": "claude-sonnet-4-6"}
        ],
    }

    normalized = normalize_teamleiter_aliases(cfg)

    assert normalized["teamleiter"]["model"] == "o3"
    assert normalized["konzertmeister"]["model"] == "o3"
    assert normalized["teamleiter_choices"][0]["model"] == "o3"
    assert normalized["konzertmeister_choices"][0]["model"] == "o3"


def test_teamleiter_alias_logs_legacy_warning_once(caplog) -> None:
    reset_alias_warning_for_tests()
    caplog.set_level(logging.WARNING)
    logger = logging.getLogger("tests.alias")

    legacy_cfg = {
        "konzertmeister": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        "konzertmeister_choices": [
            {"label": "Legacy", "provider": "anthropic", "model": "claude-sonnet-4-6"}
        ],
    }

    normalize_teamleiter_aliases(dict(legacy_cfg), logger=logger)
    normalize_teamleiter_aliases(dict(legacy_cfg), logger=logger)

    warnings = [r for r in caplog.records if "Deprecated config keys" in r.message]
    assert len(warnings) == 1


def test_audit_rotation_creates_backup_and_keeps_writing(monkeypatch, tmp_path: Path) -> None:
    audit_file = _setup_temp_audit(monkeypatch, tmp_path)
    monkeypatch.setattr(sm, "AUDIT_MAX_BYTES", 250)
    monkeypatch.setattr(sm, "AUDIT_BACKUP_COUNT", 3)

    for idx in range(25):
        sm._audit("run-rotation", "phase_started", 0, extra={"idx": idx, "blob": "x" * 40})

    rotated = audit_file.with_name("audit.jsonl.1")
    assert audit_file.exists()
    assert rotated.exists()

    sm._audit("run-rotation", "phase_ready_for_review", 0, extra={"idx": 999})
    assert audit_file.read_text(encoding="utf-8").strip() != ""


def test_audit_parallel_calls_keep_all_entries(monkeypatch, tmp_path: Path) -> None:
    audit_file = _setup_temp_audit(monkeypatch, tmp_path)
    monkeypatch.setattr(sm, "AUDIT_MAX_BYTES", 100_000_000)
    monkeypatch.setattr(sm, "AUDIT_BACKUP_COUNT", 3)

    workers = 4
    per_worker = 30

    def _writer(worker_id: int) -> None:
        for idx in range(per_worker):
            sm._audit(
                f"run-{worker_id}",
                "phase_started",
                0,
                extra={"worker_id": worker_id, "idx": idx},
            )

    threads = [threading.Thread(target=_writer, args=(wid,)) for wid in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == workers * per_worker
    for line in lines:
        parsed = json.loads(line)
        assert "run_id" in parsed
        assert "action" in parsed
