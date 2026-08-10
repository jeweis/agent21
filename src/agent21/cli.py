"""Agent21 command-line entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agent21 import __version__
from agent21.config import load_config
from agent21.doctor import diagnose_project, has_blocked
from agent21.errors import ConfigError, classify_exit
from agent21.init import initialize_project
from agent21.manifest import load_manifest
from agent21.models import REGISTERED_AGENTS
from agent21.scanner import detect_agents
from agent21.selection import is_tty, select_agents_interactive
from agent21.skills import install_skill, list_skills, remove_skill
from agent21.sync import sync_project

app = typer.Typer(
    name="agent21",
    help="Synchronize project-level configuration across AI coding agents.",
    no_args_is_help=False,
    invoke_without_command=True,
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
    ctx: typer.Context,
    agents: Annotated[
        str | None,
        typer.Option("--agents", help="Comma-separated Agents to enable (e.g. codex,cursor)."),
    ] = None,
    mode: Annotated[
        str, typer.Option("--mode", help="Synchronization mode: auto, copy, or symlink.")
    ] = "auto",
    version_requested: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    """Run Agent21 commands."""
    del version_requested
    if ctx.invoked_subcommand is None:
        _run_enable(agents, mode)


@app.command("enable")
def enable_command(
    agents: Annotated[
        str | None,
        typer.Option("--agents", help="Comma-separated Agents to enable (e.g. codex,cursor)."),
    ] = None,
    mode: Annotated[
        str, typer.Option("--mode", help="Synchronization mode: auto, copy, or symlink.")
    ] = "auto",
) -> None:
    """Enable Agents and synchronize their configuration."""
    _run_enable(agents, mode)


@app.command("disable")
def disable_command(
    agents: Annotated[str, typer.Option("--agents", help="Comma-separated Agents to disable.")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Preview which managed outputs would be removed.")
    ] = False,
) -> None:
    """Disable Agents and retire their managed outputs."""
    _run_disable(agents, dry_run)


@app.command("status")
def status_command() -> None:
    """Show enablement, availability, and managed outputs for every Agent."""
    _run_status()


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
    for category in ("created", "updated", "unchanged", "retired", "skipped"):
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


def _run_enable(agents_arg: str | None, mode: str) -> None:
    """默认启用命令：显式 --agents 非交互，省略时 TTY 交互 / 非 TTY 引导。"""

    root = Path.cwd()
    try:
        selected = _parse_agents_arg(agents_arg)
        if selected is None:
            if not is_tty():
                raise ConfigError(
                    "interactive selection requires a terminal; use --agents codex,cursor"
                )
            enabled = _current_enabled(root)
            chosen = select_agents_interactive(set(enabled))
            if not chosen:
                selected = tuple(enabled) if _has_config(root) else REGISTERED_AGENTS
            else:
                selected = chosen
        init_result = initialize_project(root, agents=selected, mode=mode)
        sync_result = sync_project(root)
    except Exception as exc:
        _fail(exc)
    typer.echo("initialized Agent21 project")
    typer.echo(f"enabled: {', '.join(init_result.enabled_agents) or 'none'}")
    for path in init_result.created:
        typer.echo(f"created: {path}")
    for path in init_result.reused:
        typer.echo(f"reused: {path}")
    for category in ("created", "updated", "unchanged", "retired", "skipped"):
        for value in getattr(sync_result, category):
            typer.echo(f"{category}: {value}")


def _run_disable(agents_arg: str, dry_run: bool) -> None:
    """禁用 Agent 并回收其托管产物；dry-run 只预览。"""

    root = Path.cwd()
    try:
        selected = _parse_agents_arg(agents_arg) or ()
        if not selected:
            raise ConfigError("--agents requires at least one Agent name")
        if dry_run:
            _preview_disable(root, selected)
            return
        _disable_selection(root, selected)
        sync_result = sync_project(root)
    except Exception as exc:
        _fail(exc)
    for name in selected:
        typer.echo(f"disabled: {name}")
    for path in sync_result.retired:
        typer.echo(f"retired: {path}")


def _run_status() -> None:
    """输出每个已注册 Agent 的状态与 doctor 阻塞项。"""

    root = Path.cwd()
    try:
        config = load_config(root)
    except ConfigError:
        typer.echo("project not initialized: run 'agent21' first")
        raise typer.Exit() from None
    try:
        manifest = load_manifest(root)
    except Exception as exc:
        _fail(exc)
    detected = detect_agents()
    by_agent: dict[str, list[str]] = {}
    for artifact in manifest.managed_artifacts:
        by_agent.setdefault(artifact.agent, []).append(artifact.path)
    for agent in REGISTERED_AGENTS:
        selection = config.agents.get(agent)
        enabled = "enabled" if selection is not None and selection.enabled else "disabled"
        availability = _availability_label(agent, detected)
        targets = ", ".join(sorted(by_agent.get(agent, ()))) or "-"
        typer.echo(f"{agent}\t{enabled}\t{availability}\t{targets}")
    blocked = [item for item in diagnose_project(root) if item.status.value == "blocked"]
    for item in blocked:
        action = f"; action: {item.action}" if item.action else ""
        typer.echo(f"blocked: {item.check_id}: {item.subject}: {item.message}{action}", err=True)


def _availability_label(agent: str, detected: dict[str, bool]) -> str:
    """按 Agent 能力返回可用性标签：有 CLI 走 PATH 检测，无需 CLI 显示 none-required。"""

    from agent21.adapters import REGISTRY

    adapter = REGISTRY.get(agent)
    if adapter is None or adapter.capability.executable is None:
        return "none-required"
    return "available" if detected.get(agent, False) else "missing"


def _parse_agents_arg(agents_arg: str | None) -> tuple[str, ...] | None:
    """解析逗号分隔的 --agents；None 返回 None，空串返回空元组。"""

    if agents_arg is None:
        return None
    return tuple(item.strip() for item in agents_arg.split(",") if item.strip())


def _current_enabled(root: Path) -> tuple[str, ...]:
    """读取当前 config 中已启用的 Agent；未初始化返回空。"""

    try:
        config = load_config(root)
    except ConfigError:
        return ()
    return tuple(name for name, selection in config.agents.items() if selection.enabled)


def _has_config(root: Path) -> bool:
    """项目是否已初始化（存在 config 文件）。"""

    return (root / ".agents" / "config.yaml").is_file()


def _preview_disable(root: Path, agents: tuple[str, ...]) -> None:
    """dry-run：列出目标 Agent 的托管产物，不修改 config、不删除文件。"""

    manifest = load_manifest(root)
    retired = sorted(
        artifact.path for artifact in manifest.managed_artifacts if artifact.agent in agents
    )
    for path in retired:
        typer.echo(f"would retire: {path}")


def _disable_selection(root: Path, agents: tuple[str, ...]) -> None:
    """将目标 Agent 置为禁用并写回 config。"""

    from agent21.init import disable_agents

    disable_agents(root, agents)


def _fail(error: BaseException) -> None:
    """Render an expected redacted failure and terminate with stable status."""

    typer.echo(f"error: {error}", err=True)
    raise typer.Exit(classify_exit(error))
