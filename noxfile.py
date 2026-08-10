"""Cross-platform validation sessions shared by contributors and CI."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import nox

nox.options.default_venv_backend = "none"
nox.options.error_on_missing_interpreters = True

FAST_MARKERS = "not e2e and not compatibility and not snapshot and not slow"
CORE_PATHS = (
    "src/agent21/config.py",
    "src/agent21/adapters",
    "src/agent21/skills.py",
    "src/agent21/mcp.py",
)


def _run_quality(session: nox.Session) -> None:
    """Run formatting, linting, and type checks in the locked environment."""
    session.run("ruff", "format", "--check", ".")
    session.run("ruff", "check", ".")
    session.run("mypy", "src", "tests")


def _run_pytest(session: nox.Session, marker: str | None = None) -> None:
    """Run pytest with coverage and enforce overall plus existing core thresholds."""
    args = ["pytest", "--cov=agent21", "--cov-branch", "--cov-report=term-missing"]
    if marker:
        args.extend(["-m", marker])
    session.run(*args)
    session.run("coverage", "report", "--fail-under=80")
    existing_core = [path for path in CORE_PATHS if Path(path).exists()]
    if existing_core:
        session.run(
            "coverage",
            "report",
            f"--include={','.join(existing_core)}",
            "--fail-under=90",
        )


@nox.session(venv_backend="none")
def unit(session: nox.Session) -> None:
    """Run isolated unit tests."""
    session.run("pytest", "-m", "unit")


@nox.session(venv_backend="none")
def adapter(session: nox.Session) -> None:
    """Run adapter tests."""
    session.run("pytest", "-m", "adapter")


@nox.session(venv_backend="none")
def contract(session: nox.Session) -> None:
    """Run public contract tests."""
    session.run("pytest", "-m", "contract")


@nox.session(venv_backend="none")
def integration(session: nox.Session) -> None:
    """Run isolated project workflow tests."""
    session.run("pytest", "-m", "integration")


@nox.session(venv_backend="none")
def safety(session: nox.Session) -> None:
    """Run safety and project-boundary tests."""
    session.run("pytest", "-m", "safety")


@nox.session(venv_backend="none")
def snapshot(session: nox.Session) -> None:
    """Compare stable output snapshots without updating them."""
    session.run("pytest", "-m", "snapshot")


@nox.session(venv_backend="none")
def pr(session: nox.Session) -> None:
    """Run the pull-request validation gate."""
    _run_quality(session)
    _run_pytest(session, FAST_MARKERS)


@nox.session(venv_backend="none")
def main(session: nox.Session) -> None:
    """Run all checks required after merging to the main branch."""
    _run_quality(session)
    _run_pytest(session)


def _venv_executable(root: Path, command: str) -> Path:
    """Return a command path inside a virtual environment on any platform."""
    directory = "Scripts" if os.name == "nt" else "bin"
    suffix = ".exe" if directory == "Scripts" else ""
    return root / directory / f"{command}{suffix}"


def _run_package(session: nox.Session) -> None:
    """Build distributions and smoke-test the installed wheel in a clean environment."""
    shutil.rmtree("dist", ignore_errors=True)
    session.run("python", "-m", "build")
    distributions = [str(path) for path in sorted(Path("dist").iterdir())]
    session.run("twine", "check", "--strict", *distributions)
    wheel = next(Path("dist").glob("*.whl"))
    with tempfile.TemporaryDirectory(prefix="agent21-package-") as temp_dir:
        env_root = Path(temp_dir) / "venv"
        session.run("uv", "venv", str(env_root), "--python", sys.executable)
        python = _venv_executable(env_root, "python")
        agent21 = _venv_executable(env_root, "agent21")
        session.run("uv", "pip", "install", "--python", str(python), str(wheel))
        subprocess.run([python, "-c", "import agent21"], check=True)
        subprocess.run([agent21, "--help"], check=True)
        subprocess.run([agent21, "--version"], check=True)
        project = Path(temp_dir) / "smoke project"
        project.mkdir()
        subprocess.run(
            [agent21, "--agents", "workbuddy", "--mode", "copy"],
            cwd=project,
            check=True,
        )
        subprocess.run([agent21, "sync"], cwd=project, check=True)
        subprocess.run([agent21, "status"], cwd=project, check=True)
        subprocess.run([agent21, "doctor"], cwd=project, check=True)
        skill_source = project / "demo-skill"
        skill_source.mkdir()
        (skill_source / "SKILL.md").write_text("# Package smoke Skill\n", encoding="utf-8")
        subprocess.run([agent21, "skill", "install", "demo-skill"], cwd=project, check=True)
        subprocess.run([agent21, "skill", "list"], cwd=project, check=True)
        subprocess.run([agent21, "skill", "remove", "demo-skill"], cwd=project, check=True)


@nox.session(venv_backend="none")
def package(session: nox.Session) -> None:
    """Run package build and clean-install validation."""
    _run_package(session)


@nox.session(venv_backend="none")
def release(session: nox.Session) -> None:
    """Run current-platform validation for a release candidate."""
    _run_quality(session)
    _run_pytest(session)
    _run_package(session)
