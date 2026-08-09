"""Tests for managed artifact drift and diagnostic redaction."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.doctor import diagnose_project
from agent21.init import initialize_project
from agent21.sync import sync_project


@pytest.mark.integration
def test_doctor_reports_managed_drift_with_agent_and_action(tmp_path: Path) -> None:
    """A hand-edited generated file points users back to synchronization."""

    initialize_project(tmp_path, agents=("claude",), mode="copy", assume_yes=True)
    sync_project(tmp_path, available_agents={"claude": True})
    (tmp_path / "CLAUDE.md").write_text("drifted\n", encoding="utf-8")

    drift = next(
        item
        for item in diagnose_project(tmp_path)
        if item.check_id == "artifact.drift" and item.subject == "CLAUDE.md"
    )

    assert drift.status.value == "blocked"
    assert "claude" in drift.message
    assert drift.action == "run agent21 sync"


@pytest.mark.integration
@pytest.mark.safety
def test_doctor_never_echoes_mcp_secret_values(tmp_path: Path) -> None:
    """Malformed source diagnostics do not expose credential-looking values."""

    initialize_project(tmp_path, agents=(), assume_yes=True)
    secret = "fixture-secret-token"
    (tmp_path / ".mcp.json").write_text(f'{{"token":"{secret}"', encoding="utf-8")

    rendered = "\n".join(item.message for item in diagnose_project(tmp_path))

    assert secret not in rendered
