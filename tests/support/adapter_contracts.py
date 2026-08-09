"""适配器契约测试的加载、解析和语义校验工具。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specs" / "001-test-infrastructure"
CONTRACT_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "adapter_contracts"

AGENT_RE = re.compile(r"^[a-z][a-z0-9-]*$")
CASE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CAPABILITIES = ("instructions", "skills", "mcp")
CAPABILITY_MODES = {"native", "compatible", "transform", "unsupported"}
STATUSES = {"implemented", "planned", "unsupported"}
OUTPUT_KINDS = {"file", "directory", "symlink"}
PLATFORMS = ("linux", "macos", "windows")
SYNC_MODES = {"auto", "copy", "symlink", "unsupported"}


@dataclass(frozen=True)
class MatrixEntry:
    """适配器矩阵中的一行权威登记。"""

    agent: str
    status: str
    capabilities: dict[str, str]
    mvp_target: bool
    notes: str


def load_adapter_contracts(directory: Path | None = None) -> list[dict[str, Any]]:
    """按文件名稳定加载适配器契约 fixture。"""
    contract_dir = directory or CONTRACT_FIXTURE_DIR
    return [load_adapter_contract(path) for path in sorted(contract_dir.glob("*.json"))]


def load_adapter_contract(path: Path) -> dict[str, Any]:
    """读取单个 JSON 契约并返回字典。"""
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return data


def load_adapter_matrix(path: Path | None = None) -> dict[str, MatrixEntry]:
    """解析 Markdown 矩阵表，返回以 agent slug 为键的登记。"""
    matrix_path = path or SPEC_ROOT / "contracts" / "adapter-matrix.md"
    entries: dict[str, MatrixEntry] = {}

    for line in matrix_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or "---" in line or "Agent |" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 7:
            continue
        agent, status, instructions, skills, mcp, mvp_target, notes = cells
        slug = slugify_agent(agent)
        entries[slug] = MatrixEntry(
            agent=slug,
            status=status,
            capabilities={
                "instructions": instructions,
                "skills": skills,
                "mcp": mcp,
            },
            mvp_target=mvp_target.lower() == "yes",
            notes=notes,
        )

    if not entries:
        raise AssertionError(f"No adapter matrix rows parsed from {matrix_path}")
    return entries


def slugify_agent(name: str) -> str:
    """将矩阵展示名称转换为契约 fixture 使用的稳定 slug。"""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def validate_contract_schema(contract: dict[str, Any]) -> None:
    """执行 schema 的本地等价校验，避免测试基础设施依赖网络或额外服务。"""
    required = {
        "schema_version",
        "agent",
        "status",
        "capabilities",
        "source_inputs",
        "managed_outputs",
        "platform_modes",
        "contract_cases",
    }
    _assert_keys(contract, required, "adapter contract")
    assert contract["schema_version"] == "1.0", "schema_version must be 1.0"
    assert _is_slug(contract["agent"]), "agent must match slug pattern"
    assert contract["status"] in STATUSES, "status must be a known value"
    _validate_capabilities(contract["capabilities"])
    _validate_repository_paths(contract["source_inputs"])
    _validate_managed_outputs(contract["managed_outputs"])
    _validate_platform_modes(contract["platform_modes"])
    _validate_contract_cases(contract)


def validate_contract_against_matrix(
    contract: dict[str, Any],
    matrix_entry: MatrixEntry,
) -> None:
    """确认 fixture 没有偏离权威适配器矩阵。"""
    assert contract["agent"] == matrix_entry.agent
    assert contract["status"] == matrix_entry.status
    for capability in CAPABILITIES:
        actual = contract["capabilities"][capability]["mode"]
        expected = matrix_entry.capabilities[capability]
        assert actual == expected, f"{contract['agent']} {capability} must be {expected}"


def implemented_contracts(contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """返回真正进入通过率统计的 implemented 契约。"""
    return [contract for contract in contracts if contract["status"] == "implemented"]


def validate_implemented_semantics(contract: dict[str, Any]) -> None:
    """implemented 契约的每项受支持能力都必须有对应用例。"""
    if contract["status"] != "implemented":
        return
    validate_contract_schema(contract)
    cases = set(contract["contract_cases"])
    for capability, detail in contract["capabilities"].items():
        if detail["mode"] == "unsupported":
            continue
        expected_case = f"{contract['agent']}-{capability}"
        assert expected_case in cases, (
            f"{contract['agent']} {capability} must be covered by {expected_case}"
        )


def validate_native_output_policy(contract: dict[str, Any]) -> None:
    """原生能力复用权威输入，不允许把同名权威文件声明为托管副本。"""
    if contract["status"] != "implemented":
        return
    native_exists = any(detail["mode"] == "native" for detail in contract["capabilities"].values())
    if not native_exists:
        return

    source_paths = {Path(path).as_posix() for path in contract["source_inputs"]}
    source_file_names = {Path(path).name for path in source_paths}
    for output in contract["managed_outputs"]:
        output_path = Path(output["path"]).as_posix()
        duplicates_file = output["kind"] == "file" and Path(output_path).name in source_file_names
        assert output_path not in source_paths and not duplicates_file, (
            f"native capability must not duplicate authoritative path {output_path}"
        )


def validate_mapped_outputs_have_snapshots(contract: dict[str, Any]) -> None:
    """兼容映射或转换能力实现后，必须具备可审查的稳定输出基线。"""
    if contract["status"] != "implemented":
        return
    has_mapped_capability = any(
        detail["mode"] in {"compatible", "transform"}
        for detail in contract["capabilities"].values()
    )
    if not has_mapped_capability:
        return
    if not contract["managed_outputs"]:
        return

    snapshot_outputs = [
        output for output in contract["managed_outputs"] if output["snapshot"] is True
    ]
    assert snapshot_outputs, "compatible/transform outputs must include snapshot baselines"


def stable_file_tree(root: Path) -> str:
    """生成确定性文件树基线，仅包含文件路径并统一为 POSIX 分隔符。"""
    paths = []
    for path in root.rglob("*"):
        if path.is_file():
            paths.append(f"file:{path.relative_to(root).as_posix()}")
    return "\n".join(sorted(paths))


def approved_baseline_name(case_id: str, format_name: str, contract_version: str) -> str:
    """构造经评审基线的标准文件名。"""
    assert CASE_RE.fullmatch(case_id), "case_id must be a stable slug"
    assert CASE_RE.fullmatch(format_name), "format must be a stable slug"
    version = contract_version.replace(".", "_")
    return f"{case_id}__{format_name}__v{version}.snap"


def _validate_capabilities(capabilities: Any) -> None:
    assert isinstance(capabilities, dict), "capabilities must be an object"
    _assert_keys(capabilities, set(CAPABILITIES), "capabilities")
    for capability, detail in capabilities.items():
        assert isinstance(detail, dict), f"{capability} must be an object"
        assert set(detail).issubset({"mode", "notes"}), f"{capability} has unknown keys"
        assert detail.get("mode") in CAPABILITY_MODES, f"{capability} mode is invalid"
        if "notes" in detail:
            assert isinstance(detail["notes"], str), f"{capability} notes must be text"


def _validate_repository_paths(paths: Any) -> None:
    assert isinstance(paths, list), "repository paths must be a list"
    assert len(paths) == len(set(paths)), "repository paths must be unique"
    for path in paths:
        assert isinstance(path, str) and path, "repository path must be text"
        assert not Path(path).is_absolute(), "path must be repository-relative"
        assert not re.match(r"^[A-Za-z]:", path), "path must be repository-relative"
        assert ".." not in Path(path).parts, "path must be repository-relative"


def _validate_managed_outputs(outputs: Any) -> None:
    assert isinstance(outputs, list), "managed_outputs must be a list"
    paths: list[str] = []
    for output in outputs:
        assert isinstance(output, dict), "managed output must be an object"
        _assert_keys(output, {"path", "kind", "managed", "snapshot"}, "managed output")
        _validate_repository_paths([output["path"]])
        assert output["kind"] in OUTPUT_KINDS, "managed output kind is invalid"
        assert output["managed"] is True, "managed output must be managed"
        assert isinstance(output["snapshot"], bool), "snapshot must be boolean"
        paths.append(output["path"])
    assert len(paths) == len(set(paths)), "managed output paths must be unique"


def _validate_platform_modes(platform_modes: Any) -> None:
    assert isinstance(platform_modes, dict), "platform_modes must be an object"
    _assert_keys(platform_modes, set(PLATFORMS), "platform_modes")
    for platform, modes in platform_modes.items():
        assert isinstance(modes, list) and modes, f"{platform} modes must be non-empty"
        assert len(modes) == len(set(modes)), f"{platform} modes must be unique"
        assert set(modes).issubset(SYNC_MODES), f"{platform} modes contain invalid value"


def _validate_contract_cases(contract: dict[str, Any]) -> None:
    cases = contract["contract_cases"]
    assert isinstance(cases, list), "contract_cases must be a list"
    assert len(cases) == len(set(cases)), "contract_cases must be unique"
    for case_id in cases:
        assert isinstance(case_id, str), "contract_cases entries must be text"
        assert CASE_RE.fullmatch(case_id), "contract_cases entry must be a slug"
    if contract["status"] == "implemented":
        assert cases, "implemented contract_cases must contain at least one case"


def _assert_keys(data: dict[str, Any], expected: set[str], label: str) -> None:
    missing = expected - set(data)
    extra = set(data) - expected
    assert not missing, f"{label} missing keys: {sorted(missing)}"
    assert not extra, f"{label} has unknown keys: {sorted(extra)}"


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and AGENT_RE.fullmatch(value) is not None
