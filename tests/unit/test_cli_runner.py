"""Unit tests for subprocess and in-process CLI runners."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from tests.support.cli_runner import run_callable_cli, run_subprocess_cli


def test_run_callable_cli_captures_stdout_stderr_and_return_code() -> None:
    """In-process callables expose process-like output and status."""

    def fake_cli(args: Sequence[str]) -> int:
        print(f"stdout:{args[0]}")
        print("stderr:problem", file=sys.stderr)
        return 7

    result = run_callable_cli(fake_cli, ("doctor",))

    assert result.exit_code == 7
    assert result.stdout == "stdout:doctor\n"
    assert result.stderr == "stderr:problem\n"


def test_run_callable_cli_translates_system_exit_string_to_failure() -> None:
    """Non-integer SystemExit payloads match Python's failure convention."""

    def fake_cli(_: Sequence[str]) -> int:
        raise SystemExit("bad option")

    result = run_callable_cli(fake_cli)

    assert result.exit_code == 1


def test_run_subprocess_cli_captures_text_output() -> None:
    """Subprocess execution is available for installed-console-script tests."""

    code = "import sys; print('out'); print('err', file=sys.stderr); raise SystemExit(3)"
    result = run_subprocess_cli((sys.executable, "-c", code))

    assert result.exit_code == 3
    assert result.stdout == "out\n"
    assert result.stderr == "err\n"
