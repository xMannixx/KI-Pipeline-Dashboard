"""
Phase 5: Cursor Bridge — Option A (Filesystem).
Writes the Cursor task as a .md file into the configured workspace folder.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pipeline.config_alias import dashboard_config_path, load_dashboard_config, resolve_project_path


def _get_workspace_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    cfg = load_dashboard_config(dashboard_config_path(repo_root))
    raw = cfg.get("cursor_bridge", {}).get("workspace")
    return resolve_project_path(raw, default_relative="data/cursor_auftraege")


def write_cursor_task(task_content: str, title: str = "auftrag") -> dict:
    """
    Write the Cursor task YAML to the configured workspace folder.
    Returns: {success, file_path, filename, error}
    """
    try:
        workspace = _get_workspace_path()
        workspace.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:40]

        # Strip any markdown code fences the LLM may have wrapped around the YAML
        content = task_content.strip()
        if content.startswith("```yaml"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        filename = f"CURSOR_AUFTRAG_{safe_title}_{ts}.yaml"
        file_path = workspace / filename
        file_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "file_path": str(file_path),
            "filename": filename,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": None,
            "filename": None,
            "error": str(e),
        }
