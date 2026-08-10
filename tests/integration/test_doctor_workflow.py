"""Integration tests for project and transaction health checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.doctor import diagnose_project
from agent21.init import initialize_project


@pytest.mark.integration
def test_doctor_reports_dangling_transaction_and_stale_lock(tmp_path: Path) -> None:
    """Interrupted write state is reported as blocked with a repair action."""

    initialize_project(tmp_path, agents=())
    journal = tmp_path / ".agents/.tmp/abandoned/journal.json"
    journal.parent.mkdir(parents=True)
    journal.write_text('{"state":"applying"}\n', encoding="utf-8")
    (tmp_path / ".agents/.lock").write_text("{}\n", encoding="utf-8")

    results = diagnose_project(tmp_path)

    blocked = {result.check_id for result in results if result.status.value == "blocked"}
    assert "transaction.dangling" in blocked
    assert "transaction.lock" in blocked


@pytest.mark.integration
def test_doctor_results_have_stable_order(tmp_path: Path) -> None:
    """Health rows sort by check id and subject for deterministic output."""

    initialize_project(tmp_path, agents=())

    results = diagnose_project(tmp_path)

    assert results == sorted(results, key=lambda item: (item.check_id, item.subject))


@pytest.mark.integration
def test_doctor_reports_workbuddy_as_configuration_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WorkBuddy support does not depend on a guessed CLI executable."""

    initialize_project(tmp_path, agents=("workbuddy",))
    monkeypatch.setattr("agent21.doctor.detect_agents", lambda: {"workbuddy": False})

    results = diagnose_project(tmp_path)

    row = next(result for result in results if result.subject == "workbuddy")
    assert row.check_id == "agent.configuration"
    assert row.status.value == "info"


@pytest.mark.integration
def test_doctor_reports_codebuddy_file_shadowing_agents_md(tmp_path: Path) -> None:
    """WorkBuddy must not claim native AGENTS.md when CODEBUDDY.md takes precedence."""

    initialize_project(tmp_path, agents=("workbuddy",))
    (tmp_path / "CODEBUDDY.md").write_text("# User-owned instructions\n", encoding="utf-8")

    results = diagnose_project(tmp_path)

    row = next(result for result in results if result.check_id == "agent.instructions")
    assert row.subject == "workbuddy:CODEBUDDY.md"
    assert row.status.value == "blocked"
    assert "shadows AGENTS.md" in row.message


@pytest.mark.integration
@pytest.mark.parametrize(
    ("dependency_available", "expected_status", "expected_fragment"),
    [
        (False, "unsupported", "unavailable"),
        (True, "info", "runtime state is not confirmed"),
    ],
)
def test_doctor_reports_pi_adapter_without_executing_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dependency_available: bool,
    expected_status: str,
    expected_fragment: str,
) -> None:
    """Pi dependency diagnostics only use executable discovery."""

    initialize_project(tmp_path, agents=("pi",))
    (tmp_path / ".mcp.json").write_text(
        '{"mcpServers":{"demo":{"command":"demo"}}}\n', encoding="utf-8"
    )
    monkeypatch.setattr("agent21.doctor.detect_agents", lambda: {"pi": True})
    monkeypatch.setattr("agent21.doctor.executable_available", lambda command: dependency_available)

    results = diagnose_project(tmp_path)

    row = next(result for result in results if result.check_id == "agent.dependency")
    assert row.subject == "pi:pi-mcp-adapter"
    assert row.status.value == expected_status
    assert expected_fragment in row.message
    expected_action = None if dependency_available else "pi install npm:pi-mcp-adapter"
    assert row.action == expected_action
