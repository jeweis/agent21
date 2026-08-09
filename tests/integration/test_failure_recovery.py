"""Integration-level interrupted write recovery tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.fs import PlannedArtifact, TransactionError, apply_transaction


@pytest.mark.integration
@pytest.mark.safety
def test_interrupted_multi_file_write_restores_all_prior_content(tmp_path: Path) -> None:
    """A late apply failure restores earlier targets and removes transaction state."""

    first = tmp_path / "one.txt"
    second = tmp_path / "two.txt"
    first.write_text("one-before\n", encoding="utf-8")
    second.write_text("two-before\n", encoding="utf-8")
    plans = [
        PlannedArtifact("claude", Path("one.txt"), "file", "transform", content=b"one-after\n"),
        PlannedArtifact("cursor", Path("two.txt"), "file", "transform", content=b"two-after\n"),
    ]

    def interrupt(path: Path) -> None:
        if path.name == "two.txt":
            raise OSError("simulated interruption")

    with pytest.raises(TransactionError, match="simulated interruption"):
        apply_transaction(
            tmp_path,
            plans,
            managed_paths={"one.txt", "two.txt"},
            before_replace=interrupt,
        )

    assert first.read_text(encoding="utf-8") == "one-before\n"
    assert second.read_text(encoding="utf-8") == "two-before\n"
    assert not (tmp_path / ".agents/.tmp").exists()
