"""Read-only deterministic health checks for Agent21 projects."""

from __future__ import annotations

from pathlib import Path

from agent21.adapters import REGISTRY
from agent21.config import load_config
from agent21.errors import Agent21Error
from agent21.lock import inspect_lock
from agent21.manifest import artifact_is_drifted, load_manifest
from agent21.mcp import McpConfigError, load_mcp_config
from agent21.models import HealthCheckResult, HealthStatus, Manifest, ProjectConfig, digest_path
from agent21.scanner import detect_agents, executable_available


def diagnose_project(root: Path) -> list[HealthCheckResult]:
    """Run all safe read-only checks and return rows in stable display order."""

    root = root.resolve()
    results: list[HealthCheckResult] = []
    config = _load_config_check(root, results)
    manifest = _load_manifest_check(root, results)
    _lock_check(root, results)
    _transaction_check(root, results)
    if config is not None:
        _source_checks(root, config, results)
        _agent_checks(root, config, results)
    if manifest is not None:
        for artifact in manifest.managed_artifacts:
            drifted = artifact_is_drifted(root, artifact)
            results.append(
                HealthCheckResult(
                    "artifact.drift",
                    HealthStatus.BLOCKED if drifted else HealthStatus.PASS,
                    artifact.path,
                    (
                        f"managed artifact for {artifact.agent} has drifted"
                        if drifted
                        else f"managed artifact for {artifact.agent} matches manifest"
                    ),
                    "run agent21 sync" if drifted else None,
                )
            )
        _recorded_skill_checks(root, manifest, results)
    return sorted(results, key=lambda item: (item.check_id, item.subject))


def has_blocked(results: list[HealthCheckResult]) -> bool:
    """Return whether any health row blocks a healthy exit status."""

    return any(result.status is HealthStatus.BLOCKED for result in results)


def _load_config_check(root: Path, results: list[HealthCheckResult]) -> ProjectConfig | None:
    """Load configuration and append a redacted schema result."""

    try:
        config = load_config(root)
    except (Agent21Error, OSError, ValueError) as exc:
        results.append(
            _blocked("project.config", ".agents/config.yaml", str(exc), "run agent21 init")
        )
        return None
    results.append(_passed("project.config", ".agents/config.yaml", "configuration is valid"))
    return config


def _load_manifest_check(root: Path, results: list[HealthCheckResult]) -> Manifest | None:
    """Load manifest and append a schema result."""

    try:
        manifest = load_manifest(root)
    except (Agent21Error, OSError, ValueError) as exc:
        results.append(
            _blocked("project.manifest", ".agents/manifest.yaml", str(exc), "run agent21 init")
        )
        return None
    results.append(_passed("project.manifest", ".agents/manifest.yaml", "manifest is valid"))
    return manifest


def _lock_check(root: Path, results: list[HealthCheckResult]) -> None:
    """Convert the lock helper's diagnostic to the shared health model."""

    diagnostic = inspect_lock(root)
    results.append(
        HealthCheckResult(
            diagnostic.check_id,
            HealthStatus(diagnostic.status),
            diagnostic.subject,
            diagnostic.message,
            diagnostic.action,
        )
    )


def _transaction_check(root: Path, results: list[HealthCheckResult]) -> None:
    """Report journals left by interrupted transactions."""

    journals = sorted((root / ".agents/.tmp").glob("*/journal.json"))
    if journals:
        results.append(
            _blocked(
                "transaction.dangling",
                journals[0].relative_to(root).as_posix(),
                "an incomplete Agent21 transaction requires inspection",
                "inspect the journal and restore or remove the transaction directory",
            )
        )
    else:
        results.append(_passed("transaction.dangling", ".agents/.tmp", "no dangling transaction"))


def _source_checks(root: Path, config: ProjectConfig, results: list[HealthCheckResult]) -> None:
    """Validate authoritative instructions, Skills, and optional MCP sources."""

    instructions = root / str(config.instructions_source)
    results.append(
        _passed(
            "source.instructions",
            str(config.instructions_source),
            "instructions source exists",
        )
        if instructions.is_file()
        else _blocked(
            "source.instructions",
            str(config.instructions_source),
            "instructions source is missing",
            "restore AGENTS.md",
        )
    )
    skills = root / str(config.skills_source)
    if not skills.is_dir():
        results.append(
            _blocked(
                "source.skills",
                str(config.skills_source),
                "Skills source is missing",
                "run agent21 init",
            )
        )
    else:
        results.append(_passed("source.skills", str(config.skills_source), "Skills source exists"))
        for directory in sorted(path for path in skills.iterdir() if path.is_dir()):
            if not (directory / "SKILL.md").is_file():
                results.append(
                    _blocked(
                        "skill.invalid",
                        directory.relative_to(root).as_posix(),
                        "Skill is missing SKILL.md",
                        "repair or remove the invalid Skill",
                    )
                )
    mcp_path = root / str(config.mcp_source)
    if not mcp_path.exists():
        results.append(
            HealthCheckResult(
                "source.mcp",
                HealthStatus.INFO,
                str(config.mcp_source),
                "optional MCP source is absent",
            )
        )
    else:
        try:
            load_mcp_config(mcp_path)
        except (McpConfigError, OSError) as exc:
            results.append(
                _blocked("source.mcp", str(config.mcp_source), str(exc), "repair .mcp.json")
            )
        else:
            results.append(_passed("source.mcp", str(config.mcp_source), "MCP source is valid"))


def _agent_checks(root: Path, config: ProjectConfig, results: list[HealthCheckResult]) -> None:
    """Report enabled Agent executable availability without blocking native config."""

    availability = detect_agents()
    has_mcp = _has_mcp_servers(root, config)
    for agent, selection in sorted(config.agents.items()):
        if not selection.enabled:
            continue
        adapter = REGISTRY.get(agent)
        if adapter is None:
            results.append(
                HealthCheckResult(
                    "agent.adapter", HealthStatus.UNSUPPORTED, agent, "Agent adapter is unavailable"
                )
            )
            continue
        executable = adapter.capability.executable
        if executable is None:
            results.append(
                HealthCheckResult(
                    "agent.configuration",
                    HealthStatus.INFO,
                    agent,
                    "project configuration is supported; installation cannot be confirmed by CLI",
                )
            )
        else:
            available = availability.get(agent, False)
            results.append(
                HealthCheckResult(
                    "agent.executable",
                    HealthStatus.INFO if available else HealthStatus.UNSUPPORTED,
                    agent,
                    "Agent executable is available"
                    if available
                    else "Agent executable is unavailable",
                )
            )
        dependency = adapter.capability.mcp_dependency
        if has_mcp and dependency is not None:
            available = executable_available(dependency.executable)
            results.append(
                HealthCheckResult(
                    "agent.dependency",
                    HealthStatus.INFO if available else HealthStatus.UNSUPPORTED,
                    f"{agent}:{dependency.executable}",
                    (
                        "dependency executable is detectable; runtime state is not confirmed"
                        if available
                        else "dependency executable is unavailable"
                    ),
                    None if available else dependency.install_hint,
                )
            )
        _instruction_shadow_check(root, agent, adapter.capability.instructions_blocker, results)


def _instruction_shadow_check(
    root: Path,
    agent: str,
    blocker: str | None,
    results: list[HealthCheckResult],
) -> None:
    """Report a user-owned file that takes precedence over root AGENTS.md."""

    if blocker is None or not (root / blocker).exists():
        return
    results.append(
        _blocked(
            "agent.instructions",
            f"{agent}:{blocker}",
            f"{blocker} shadows AGENTS.md for {agent}",
            f"remove or reconcile {blocker} so AGENTS.md remains authoritative",
        )
    )


def _has_mcp_servers(root: Path, config: ProjectConfig) -> bool:
    """Return whether the valid optional MCP source contains any servers."""

    path = root / config.mcp_source
    if not path.is_file():
        return False
    try:
        return bool(load_mcp_config(path).servers)
    except (McpConfigError, OSError):
        return False


def _recorded_skill_checks(
    root: Path, manifest: Manifest, results: list[HealthCheckResult]
) -> None:
    """Verify every manifest-owned Skill still has its recorded directory digest."""

    for skill in manifest.skills:
        target = root / skill.path
        drifted = not target.exists() or digest_path(target) != skill.digest
        results.append(
            HealthCheckResult(
                "skill.drift",
                HealthStatus.BLOCKED if drifted else HealthStatus.PASS,
                skill.path,
                "managed Skill has drifted" if drifted else "managed Skill matches manifest",
                "reinstall or remove the Skill" if drifted else None,
            )
        )


def _passed(check_id: str, subject: str, message: str) -> HealthCheckResult:
    """Build a passing result row."""

    return HealthCheckResult(check_id, HealthStatus.PASS, subject, message)


def _blocked(check_id: str, subject: str, message: str, action: str) -> HealthCheckResult:
    """Build a blocking result row."""

    return HealthCheckResult(check_id, HealthStatus.BLOCKED, subject, message, action)
