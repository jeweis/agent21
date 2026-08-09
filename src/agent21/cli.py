"""Agent21 command-line entry point."""

from pathlib import Path
from typing import Annotated

import typer

from agent21 import __version__
from agent21.doctor import diagnose_project, has_blocked
from agent21.errors import classify_exit
from agent21.init import initialize_project
from agent21.skills import install_skill, list_skills, remove_skill
from agent21.sync import sync_project

app = typer.Typer(
    name="agent21",
    help="Synchronize project-level configuration across AI coding agents.",
    no_args_is_help=True,
)
skill_app = typer.Typer(help="Install, list, and remove project-level Skills.")
app.add_typer(skill_app, name="skill")


def version_callback(value: bool) -> None:
    """Print the installed Agent21 version and stop command processing."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version_requested: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    """Run Agent21 commands."""
    del version_requested


@app.command("init")
def init_command(
    agents: Annotated[
        str | None,
        typer.Option(
            "--agents",
            help=("Comma-separated Agents: claude, codex, cursor, opencode, pi, qoder, workbuddy."),
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option("--mode", help="Synchronization mode: auto, copy, or symlink."),
    ] = "auto",
    assume_yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Accept deterministic initialization defaults."),
    ] = False,
) -> None:
    """Initialize authoritative Agent21 sources in the current project."""

    selected = (
        None
        if agents is None
        else tuple(item.strip() for item in agents.split(",") if item.strip())
    )
    try:
        result = initialize_project(
            Path.cwd(),
            agents=selected,
            mode=mode,
            assume_yes=assume_yes,
        )
    except Exception as exc:
        _fail(exc)
    typer.echo("initialized Agent21 project")
    typer.echo(f"enabled: {', '.join(result.enabled_agents) or 'none'}")
    for path in result.created:
        typer.echo(f"created: {path}")
    for path in result.reused:
        typer.echo(f"reused: {path}")


@app.command("sync")
def sync_command(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the validated plan without writing files."),
    ] = False,
) -> None:
    """Synchronize authoritative sources to enabled Agents."""

    try:
        result = sync_project(Path.cwd(), dry_run=dry_run)
    except Exception as exc:
        _fail(exc)
    for category in ("created", "updated", "unchanged", "skipped"):
        for value in getattr(result, category):
            typer.echo(f"{category}: {value}")
    if result.conflicts or result.errors:
        for value in result.conflicts + result.errors:
            typer.echo(f"blocked: {value}", err=True)
        raise typer.Exit(1)


@app.command("doctor")
def doctor_command() -> None:
    """Run read-only project health and drift checks."""

    results = diagnose_project(Path.cwd())
    for result in results:
        line = f"{result.status.value}: {result.check_id}: {result.subject}: {result.message}"
        if result.action:
            line = f"{line}; action: {result.action}"
        typer.echo(line, err=result.status.value == "blocked")
    if has_blocked(results):
        raise typer.Exit(1)


@skill_app.command("install")
def skill_install_command(
    source: Annotated[str, typer.Argument(help="Project-relative directory or explicit Git URL.")],
    name: Annotated[
        str | None, typer.Option("--name", help="Override the validated Skill slug.")
    ] = None,
) -> None:
    """Install one validated Skill into the unified project directory."""

    try:
        record = install_skill(Path.cwd(), source, name=name)
    except Exception as exc:
        _fail(exc)
    typer.echo(f"installed: {record.name} ({record.source_type.value})")


@skill_app.command("list")
def skill_list_command() -> None:
    """List manifest-owned project Skills in stable order."""

    try:
        records = list_skills(Path.cwd())
    except Exception as exc:
        _fail(exc)
    for record in records:
        version = record.version or "unknown"
        typer.echo(f"{record.name}\t{record.source_type.value}\t{version}\t{record.source}")


@skill_app.command("remove")
def skill_remove_command(
    name: Annotated[str, typer.Argument(help="Managed Skill slug to remove.")],
) -> None:
    """Remove one unchanged Skill owned by the project manifest."""

    try:
        record = remove_skill(Path.cwd(), name)
    except Exception as exc:
        _fail(exc)
    typer.echo(f"removed: {record.name}")


def _fail(error: BaseException) -> None:
    """Render an expected redacted failure and terminate with stable status."""

    typer.echo(f"error: {error}", err=True)
    raise typer.Exit(classify_exit(error))
