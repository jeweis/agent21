"""Unit tests for shared diagnostic and file-safety assertions."""

from pathlib import Path

import pytest

from tests.support.assertions import (
    assert_diagnostic_contains,
    assert_idempotent,
    assert_no_credentials,
    assert_protected_files_unchanged,
    redact_diagnostics,
)
from tests.support.cli_runner import CliResult
from tests.support.project_factory import capture_protected_files, copy_project_fixture
from tests.support.tree_snapshot import snapshot_tree


def test_assert_diagnostic_contains_requires_reproducible_failure_parts() -> None:
    """Failure diagnostics must identify subject, action, and next step."""

    result = CliResult(
        1,
        "",
        "config.yml could not parse; run agent21 doctor\n",
        ("agent21", "doctor"),
    )

    assert_diagnostic_contains(
        result,
        subject="config.yml",
        action="could not parse",
        next_step="doctor",
    )


def test_assert_no_credentials_flags_unredacted_fixture_secret() -> None:
    """Credential-looking fixture values are never acceptable diagnostics."""

    with pytest.raises(AssertionError):
        assert_no_credentials("token=fixture-secret-token")


def test_redact_diagnostics_preserves_key_name() -> None:
    """Redaction keeps diagnostics useful while removing sensitive values."""

    assert redact_diagnostics("api_key=fixture-secret-token") == "api_key=<REDACTED>"


def test_assert_idempotent_reports_path_level_difference(tmp_path: Path) -> None:
    """Idempotency failures include enough path detail to reproduce drift."""

    root = tmp_path / "project"
    root.mkdir()
    before = snapshot_tree(root)
    (root / "created.txt").write_text("new\n", encoding="utf-8")
    after = snapshot_tree(root)

    with pytest.raises(AssertionError, match=r"created\.txt"):
        assert_idempotent(before, after)


def test_assert_protected_files_unchanged_accepts_unchanged_file(tmp_path: Path) -> None:
    """Protected-file assertions pass when bytes and object type are stable."""

    fixture = copy_project_fixture("mixed_project", tmp_path)
    protected = capture_protected_files(fixture.root, (Path("notes/unmanaged.txt"),))

    assert_protected_files_unchanged(fixture.root, protected)


def test_assert_protected_files_unchanged_detects_byte_change(tmp_path: Path) -> None:
    """Protected-file assertions fail on unmanaged content mutation."""

    fixture = copy_project_fixture("mixed_project", tmp_path)
    protected = capture_protected_files(fixture.root, (Path("notes/unmanaged.txt"),))
    (fixture.root / "notes/unmanaged.txt").write_text("changed\n", encoding="utf-8")

    with pytest.raises(AssertionError, match=r"notes/unmanaged\.txt"):
        assert_protected_files_unchanged(fixture.root, protected)
