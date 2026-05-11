from __future__ import annotations

import copy
import logging
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

_deprecation_logged = False
_ALLOWED_PROVIDERS = {"anthropic", "openai", "google", "deepseek"}


def dashboard_config_path(repo_root: Path | None = None) -> Path:
    """
    Prefer `config.toml`; if missing, use `config.example.toml` (fresh clone).
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    primary = root / "config.toml"
    if primary.exists():
        return primary
    fallback = root / "config.example.toml"
    if fallback.exists():
        return fallback
    return primary


def resolve_project_path(raw: str | None, *, default_relative: str) -> Path:
    """
    Paths in config: relative → anchored at repository root; absolute → unchanged.
    """
    text = (raw or "").strip()
    if not text:
        text = default_relative
    p = Path(text)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def reset_alias_warning_for_tests() -> None:
    """Reset one-time deprecation log flag (tests only)."""
    global _deprecation_logged
    _deprecation_logged = False


def _warn_deprecated_once(logger: logging.Logger | None, message: str) -> None:
    global _deprecation_logged
    if _deprecation_logged:
        return
    _deprecation_logged = True
    (logger or logging.getLogger("aethos.dashboard")).warning(message)


def normalize_teamleiter_aliases(
    cfg: dict[str, Any],
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Normalize teamleiter/konzertmeister config keys with teamleiter priority."""
    has_teamleiter = isinstance(cfg.get("teamleiter"), dict)
    has_konzertmeister = isinstance(cfg.get("konzertmeister"), dict)
    has_teamleiter_choices = isinstance(cfg.get("teamleiter_choices"), list)
    has_konzertmeister_choices = isinstance(cfg.get("konzertmeister_choices"), list)

    if (has_konzertmeister and not has_teamleiter) or (
        has_konzertmeister_choices and not has_teamleiter_choices
    ):
        _warn_deprecated_once(
            logger,
            "Deprecated config keys [konzertmeister]/[[konzertmeister_choices]] in use. "
            "Please migrate to [teamleiter]/[[teamleiter_choices]].",
        )

    selected_teamleiter = (
        cfg["teamleiter"] if has_teamleiter else cfg.get("konzertmeister", {}) or {}
    )
    selected_choices = (
        cfg["teamleiter_choices"]
        if has_teamleiter_choices
        else cfg.get("konzertmeister_choices", []) or []
    )

    cfg["teamleiter"] = copy.deepcopy(selected_teamleiter)
    cfg["konzertmeister"] = copy.deepcopy(selected_teamleiter)
    cfg["teamleiter_choices"] = copy.deepcopy(selected_choices)
    cfg["konzertmeister_choices"] = copy.deepcopy(selected_choices)
    return cfg


def _require_non_empty_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid config value for '{field}': expected non-empty string.")
    return value.strip()


def _validate_provider(value: Any, field: str) -> str:
    provider = _require_non_empty_str(value, field)
    if provider not in _ALLOWED_PROVIDERS:
        raise ValueError(
            f"Invalid config value for '{field}': "
            f"unsupported provider '{provider}'. Allowed: {sorted(_ALLOWED_PROVIDERS)}."
        )
    return provider


def _validate_path_value(value: Any, field: str) -> str:
    text = _require_non_empty_str(value, field)
    if "\x00" in text:
        raise ValueError(f"Invalid config value for '{field}': null byte is not allowed.")
    return text


def _validate_path_section(cfg: dict[str, Any], section: str) -> None:
    section_cfg = cfg.get(section)
    if section_cfg is None:
        return
    if not isinstance(section_cfg, dict):
        raise ValueError(f"Invalid config section '{section}': expected table/object.")
    if "path" in section_cfg:
        _validate_path_value(section_cfg["path"], f"{section}.path")


def validate_dashboard_config(cfg: dict[str, Any]) -> dict[str, Any]:
    teamleiter = cfg.get("teamleiter")
    if not isinstance(teamleiter, dict):
        raise ValueError("Invalid config section 'teamleiter': expected table/object.")
    _validate_provider(teamleiter.get("provider"), "teamleiter.provider")
    _require_non_empty_str(teamleiter.get("model"), "teamleiter.model")

    choices = cfg.get("teamleiter_choices", [])
    if not isinstance(choices, list):
        raise ValueError("Invalid config section 'teamleiter_choices': expected list.")
    for idx, choice in enumerate(choices):
        if not isinstance(choice, dict):
            raise ValueError(
                f"Invalid config value for 'teamleiter_choices[{idx}]': expected table/object."
            )
        _require_non_empty_str(choice.get("label"), f"teamleiter_choices[{idx}].label")
        _validate_provider(choice.get("provider"), f"teamleiter_choices[{idx}].provider")
        _require_non_empty_str(choice.get("model"), f"teamleiter_choices[{idx}].model")

    workspace_roots = cfg.get("workspace_roots", [])
    if not isinstance(workspace_roots, list):
        raise ValueError("Invalid config section 'workspace_roots': expected list.")
    if not workspace_roots:
        raise ValueError("Invalid config: at least one [[workspace_roots]] entry is required.")
    for idx, root in enumerate(workspace_roots):
        if not isinstance(root, dict):
            raise ValueError(f"Invalid config value for 'workspace_roots[{idx}]': expected table/object.")
        _validate_path_value(root.get("path"), f"workspace_roots[{idx}].path")

    for section in (
        "cursor_bridge",
        "auftraege_dir",
        "review_results_dir",
        "konsolidierungen_dir",
        "token_reports_dir",
        "docs_dir",
        "systemprompts_dir",
        "current_state_sheet_dir",
    ):
        _validate_path_section(cfg, section)

    anthropic_cfg = cfg.get("anthropic")
    if anthropic_cfg is not None:
        if not isinstance(anthropic_cfg, dict):
            raise ValueError("Invalid config section 'anthropic': expected table/object.")
        ttl = anthropic_cfg.get("prompt_cache_ttl", "5m")
        if ttl not in ("5m", "1h"):
            raise ValueError("Invalid config value for 'anthropic.prompt_cache_ttl': use '5m' or '1h'.")

    return cfg


def load_dashboard_config(config_path: Path, logger: logging.Logger | None = None) -> dict[str, Any]:
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
    normalized = normalize_teamleiter_aliases(raw, logger=logger)
    return validate_dashboard_config(normalized)
