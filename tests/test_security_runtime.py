from __future__ import annotations

import app as dashboard_app


def test_resolve_secret_key_uses_env(monkeypatch) -> None:
    monkeypatch.setenv("FLASK_SECRET_KEY", "stable-test-key")
    assert dashboard_app._resolve_secret_key() == "stable-test-key"


def test_resolve_secret_key_falls_back_to_random_bytes(monkeypatch) -> None:
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    key = dashboard_app._resolve_secret_key()
    assert isinstance(key, bytes)
    assert len(key) == 24
