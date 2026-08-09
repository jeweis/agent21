"""Integration tests for project and transaction health checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.doctor import diagnose_project
from agent21.init import initialize_project


@pytest.mark.integration
def test_doctor_reports_dangling_transaction_and_stale_lock(tmp_path: Path) -> None:
    """Interrupted write state is reported as blocked with a repair action."""

    initialize_project(tmp_path, agents=(), assume_yes=True)
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

    initialize_project(tmp_path, agents=(), assume_yes=True)

    results = diagnose_project(tmp_path)

    assert results == sorted(results, key=lambda item: (item.check_id, item.subject))
