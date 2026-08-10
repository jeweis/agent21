"""Project synchronization orchestration for Agent21 adapters."""

from __future__ import annotations

from pathlib import Path, PurePath

from agent21 import __version__
from agent21.adapters import REGISTRY, AdapterContext
from agent21.adapters.protocol import ArtifactMode as AdapterMode
from agent21.config import load_config
from agent21.errors import Agent21Error, ConfigError
from agent21.fs import (
    ArtifactConflictError,
    ValidatedArtifact,
    apply_transaction,
    prevalidate_artifacts,
    supports_symlink,
)
from agent21.fs import (
    PlannedArtifact as FilePlan,
)
from agent21.lock import LockAlreadyHeld, ProjectLock
from agent21.manifest import load_manifest, save_manifest
from agent21.mcp import load_mcp_config
from agent21.models import (
    ArtifactKind,
    ArtifactMode,
    ManagedArtifact,
    Manifest,
    ProjectConfig,
    SyncMode,
    SyncResult,
)
from agent21.models import (
    PlannedArtifact as AdapterPlan,
)
from agent21.project import safe_join
from agent21.scanner import executable_available


def sync_project(
    root: Path,
    *,
    dry_run: bool = False,
) -> SyncResult:
    """Plan, validate, and atomically synchronize all enabled Agents.

    只要 Agent 在 config 中 enabled 就生成其配置产物，本机是否安装对应 CLI
    不影响生成（可用性仅作信息展示）。
    """

    root = root.resolve()
    try:
        config = load_config(root)
        manifest = load_manifest(root)
    except Agent21Error as exc:
        raise ConfigError(f"project not initialized: {exc}; run 'agent21' first") from exc
    mcp_path = safe_join(root, config.mcp_source)
    mcp_servers = load_mcp_config(mcp_path).servers if mcp_path.is_file() else {}
    context = AdapterContext(
        instructions_source=config.instructions_source,
        skills_source=config.skills_source,
        mcp_source=config.mcp_source,
        mcp_servers=mcp_servers,
        sync_mode=_adapter_mode(config.sync_mode, root),
    )
    adapter_plans, skipped = _collect_adapter_plans(config, context)

    file_plans = [_to_file_plan(plan) for plan in adapter_plans]
    managed_paths = [artifact.path for artifact in manifest.managed_artifacts]
    try:
        validated = prevalidate_artifacts(root, file_plans)
    except ArtifactConflictError as exc:
        conflict = str(exc).rsplit(": ", 1)[-1]
        return SyncResult(skipped=skipped, conflicts=[conflict])

    created = [item.relative_target.as_posix() for item in validated if not item.exists]
    updated = [
        item.relative_target.as_posix() for item in validated if item.exists and not item.unchanged
    ]
    unchanged = [item.relative_target.as_posix() for item in validated if item.unchanged]
    retired = _compute_retired(manifest.managed_artifacts, validated)
    if dry_run:
        return SyncResult(
            created=created,
            updated=updated,
            unchanged=unchanged,
            retired=retired,
            skipped=skipped,
        )

    artifacts = [_managed_artifact(item.plan.agent, item, config) for item in validated]
    next_manifest = Manifest(
        version=__version__,
        managed_artifacts=artifacts,
        skills=list(manifest.skills),
    ).sorted()
    try:
        with ProjectLock(root, command="sync"):
            transaction = apply_transaction(
                root,
                file_plans,
                managed_paths=managed_paths,
                retire=retired,
                manifest_writer=lambda: save_manifest(root, next_manifest),
            )
    except (ArtifactConflictError, LockAlreadyHeld) as exc:
        return SyncResult(skipped=skipped, conflicts=[str(exc)])
    return SyncResult(
        created=[path.as_posix() for path in transaction.created],
        updated=[path.as_posix() for path in transaction.updated],
        unchanged=[path.as_posix() for path in transaction.unchanged],
        retired=[path.as_posix() for path in transaction.retired],
        skipped=skipped,
    )


def _compute_retired(
    managed_artifacts: list[ManagedArtifact],
    validated: tuple[ValidatedArtifact, ...],
) -> list[str]:
    """计算需回收的托管产物：不再被本次计划覆盖的旧托管目标。"""

    planned = {item.relative_target.as_posix() for item in validated}
    return [artifact.path for artifact in managed_artifacts if artifact.path not in planned]


def _collect_adapter_plans(
    config: ProjectConfig,
    context: AdapterContext,
) -> tuple[list[AdapterPlan], list[str]]:
    """Collect side-effect-free plans and precise skip diagnostics.

    只要 Agent enabled 就收集其计划，不因本机缺少 CLI 而跳过；仅有 pi 的
    可选 MCP 依赖缺失时给出信息性提示（pi 无托管产物，不阻塞生成）。
    """

    adapter_plans = []
    skipped: list[str] = []
    for agent, selection in sorted(config.agents.items()):
        if not selection.enabled:
            continue
        adapter = REGISTRY.get(agent)
        if adapter is None or not adapter.capability.implemented:
            skipped.append(f"{agent}: adapter unsupported")
            continue
        dependency = adapter.capability.mcp_dependency
        if (
            context.mcp_servers
            and dependency is not None
            and not executable_available(dependency.executable)
        ):
            skipped.append(
                f"{agent}: MCP dependency unavailable ({dependency.executable}); "
                f"action: {dependency.install_hint}"
            )
        adapter_plans.extend(adapter.plan(context))
    return adapter_plans, skipped


def _adapter_mode(mode: SyncMode, root: Path) -> AdapterMode:
    """Map project sync policy to the adapter's concrete artifact mode."""

    if mode is SyncMode.SYMLINK or (mode is SyncMode.AUTO and supports_symlink(root)):
        return AdapterMode.SYMLINK
    return AdapterMode.COPY


def _to_file_plan(plan: AdapterPlan) -> FilePlan:
    """Convert a side-effect-free adapter plan to the filesystem transaction shape."""

    target = Path(PurePath(plan.target).as_posix())
    source = None if plan.source is None else Path(PurePath(plan.source).as_posix())
    return FilePlan(
        agent=str(plan.agent),
        target=target,
        kind=str(plan.kind),
        mode=str(plan.mode),
        source=source,
        content=plan.content,
        digest=None,
    )


def _managed_artifact(
    agent: str, validated: ValidatedArtifact, config: ProjectConfig
) -> ManagedArtifact:
    """Create one manifest ownership record from a prevalidated target."""

    plan = validated.plan
    source = plan.source
    return ManagedArtifact(
        agent=agent,
        path=validated.relative_target.as_posix(),
        kind=ArtifactKind(str(plan.kind)),
        mode=ArtifactMode(str(plan.mode)),
        source=(
            source.as_posix() if source is not None else PurePath(config.mcp_source).as_posix()
        ),
        digest=str(validated.digest),
    )
