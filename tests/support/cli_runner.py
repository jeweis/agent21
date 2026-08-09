"""CLI runner helpers that capture stdout, stderr, and exit status."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Sequence
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path


@dataclass(frozen=True)
class CliResult:
    """Normalized command result shared by in-process and subprocess tests."""

    exit_code: int
    stdout: str
    stderr: str
    args: tuple[str, ...]

    @property
    def combined_output(self) -> str:
        """Return stdout and stderr in display order for diagnostic assertions."""

        return f"{self.stdout}{self.stderr}"


def run_callable_cli(
    command: Callable[[Sequence[str]], int | None],
    args: Sequence[str] = (),
) -> CliResult:
    """Run a Python CLI callable while capturing process-style output."""

    stdout = StringIO()
    stderr = StringIO()
    exit_code = 0

    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            result = command(tuple(args))
            if isinstance(result, int):
                exit_code = result
        except SystemExit as exc:
            exit_code = _system_exit_code(exc)

    return CliResult(exit_code, stdout.getvalue(), stderr.getvalue(), tuple(args))


def run_subprocess_cli(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: float = 10,
) -> CliResult:
    """Run an external command with deterministic text capture."""

    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    completed = subprocess.run(
        tuple(args),
        cwd=cwd,
        env=process_env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return CliResult(completed.returncode, completed.stdout, completed.stderr, tuple(args))


def _system_exit_code(exc: SystemExit) -> int:
    """Translate SystemExit payloads to conventional process exit codes."""

    if exc.code is None:
        return 0
    if isinstance(exc.code, int):
        return exc.code
    return 1
