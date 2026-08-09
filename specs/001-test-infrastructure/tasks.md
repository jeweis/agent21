# Tasks: Agent21 测试基础设施

**Input**: Design documents from `specs/001-test-infrastructure/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `.specify/memory/constitution.md`

**Tests**: 行为和测试基础设施契约变更必须测试先行；用户故事测试必须先失败或形成可执行验收检查，再完成实现。

**Organization**: 按用户故事组织，保证每个故事可独立实现、验证和交付。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行，任务修改不同文件且无直接依赖
- **[Story]**: 用户故事编号，如 `[US1]`
- 每个任务包含精确文件路径

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 建立 Python 项目、测试依赖、基础目录和工具入口。

- [X] T001 Create PEP 621 project metadata, Python `>=3.11`, hatchling backend, console script, and dependency groups in `pyproject.toml`
- [X] T002 Generate locked dependency state for all dependency groups in `uv.lock`
- [X] T003 [P] Configure pytest strict markers, branch coverage, snapshot options, and coverage source paths in `pyproject.toml`
- [X] T004 [P] Configure Ruff and mypy project defaults in `pyproject.toml`
- [X] T005 Create Nox session skeleton for `pr`, `main`, `package`, `release`, and targeted sessions in `noxfile.py`
- [X] T006 Create test directory structure and shared fixtures in `tests/conftest.py`, `tests/unit/`, `tests/adapters/`, `tests/contract/`, `tests/integration/`, `tests/e2e/`, `tests/compatibility/`, `tests/fixtures/`, `tests/snapshots/`, and `tests/support/`
- [X] T007 Create minimal source package metadata without business commands in `src/agent21/__init__.py`, `src/agent21/__main__.py`, and `src/agent21/py.typed`
- [X] T008 Create Python and universal ignore patterns in `.gitignore`

**Checkpoint**: 本地依赖、测试目录和验证会话入口存在。

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有用户故事共享的测试支撑能力；完成前不得开始用户故事任务。

- [X] T009 [P] Add fixture isolation tests in `tests/unit/test_project_factory.py`
- [X] T010 [P] Add tree normalization and redaction tests in `tests/unit/test_tree_snapshot.py`
- [X] T011 [P] Add CLI invocation and output capture tests in `tests/unit/test_cli_runner.py`
- [X] T012 [P] Add diagnostic and protected-file assertion tests in `tests/unit/test_assertions.py`
- [X] T013 Implement immutable fixture copy and project-boundary helpers in `tests/support/project_factory.py`
- [X] T014 Implement normalized file-tree snapshots and redaction hooks in `tests/support/tree_snapshot.py`
- [X] T015 Implement in-process and subprocess CLI invocation support in `tests/support/cli_runner.py`
- [X] T016 Implement diagnostic, credential-redaction, idempotency, and protected-file assertions in `tests/support/assertions.py`
- [X] T017 Create isolated fixtures in `tests/fixtures/projects/empty_project/`, `tests/fixtures/projects/agents_project/`, `tests/fixtures/projects/claude_project/`, `tests/fixtures/projects/cursor_project/`, `tests/fixtures/projects/mixed_project/`, and `tests/fixtures/projects/broken_project/`
- [X] T018 [P] Add adapter JSON Schema and planned-contract validation tests in `tests/contract/test_adapter_contract_schema.py`
- [X] T019 [P] Add strict marker registration tests in `tests/unit/test_pytest_markers.py`
- [X] T020 Implement adapter contract loading and schema validation in `tests/support/adapter_contracts.py`
- [X] T021 Create planned adapter contract fixtures in `tests/fixtures/adapter_contracts/`
- [X] T022 Wire targeted pytest and quality sessions into `noxfile.py`

**Checkpoint**: 共享测试工具、fixture、marker、schema 校验和 Nox 基础可用。

## Phase 3: User Story 1 - 贡献者快速验证变更 (Priority: P1) MVP

**Goal**: 贡献者通过单一入口运行日常验证，并获得明确通过或可复现失败结果。

**Independent Test**: 运行 `uv run nox -s pr`，确认格式、lint、类型、unit、adapter、contract、integration、safety 快速子集和覆盖率门禁按契约执行。

### Tests for User Story 1

- [X] T023 [P] [US1] Add Nox PR session contract tests in `tests/contract/test_validation_sessions.py`
- [X] T024 [P] [US1] Add `agent21 --help` and `agent21 --version` contract tests in `tests/contract/test_cli_public_surface.py`
- [X] T025 [P] [US1] Add invalid command and option exit-status tests in `tests/contract/test_cli_exit_status.py`
- [X] T026 [P] [US1] Add global 80% and core 90% coverage policy tests in `tests/contract/test_coverage_policy.py`
- [X] T027 [P] [US1] Add docs-only path-filter contract tests in `tests/contract/test_ci_path_filters.py`

### Implementation for User Story 1

- [X] T028 [US1] Implement minimal CLI entry point with help, version, and stable exit semantics in `src/agent21/cli.py` and `src/agent21/__main__.py`
- [X] T029 [US1] Implement `pr` and targeted Nox sessions with failure propagation in `noxfile.py`
- [X] T030 [US1] Create PR workflow with Linux min/max Python, locked sync, dependency review, and failure artifacts in `.github/workflows/pr.yml`
- [X] T031 [US1] Document contributor validation and failure diagnostics in `docs/testing.md`

**Checkpoint**: US1 可通过 `uv run nox -s pr` 独立验证。

## Phase 4: User Story 2 - 防止 Agent21 损坏用户项目 (Priority: P1)

**Goal**: 验证写入型工作流的隔离、幂等、边界保护与恢复能力。

**Independent Test**: 运行 `uv run pytest -m safety`，确认所有写入发生在临时项目内，未托管文件和项目外哨兵保持不变，非法路径、权限错误和中断均可诊断。

### Tests for User Story 2

- [X] T032 [P] [US2] Add init workflow safety and idempotency tests in `tests/integration/test_init_workflow.py`
- [X] T033 [P] [US2] Add sync drift, unmanaged-file, and no-diff tests in `tests/integration/test_sync_workflow.py`
- [X] T034 [P] [US2] Add legacy configuration migration conflict tests in `tests/integration/test_config_migration.py`
- [X] T035 [P] [US2] Add Skill lifecycle and path-safety tests in `tests/integration/test_skill_lifecycle.py`
- [X] T036 [P] [US2] Add MCP boundary and credential-redaction tests in `tests/integration/test_mcp_config.py`
- [X] T037 [P] [US2] Add permission and interrupted-write recovery tests in `tests/integration/test_failure_recovery.py`
- [X] T038 [P] [US2] Add traversal and symlink boundary tests with external sentinels in `tests/integration/test_project_boundary.py`
- [X] T039 [P] [US2] Add doctor health, drift, unsupported-capability, and blocking-error tests in `tests/integration/test_doctor_workflow.py`

### Implementation for User Story 2

- [X] T040 [US2] Extend project fixture support with protected-byte and external-sentinel helpers in `tests/support/project_factory.py`
- [X] T041 [US2] Extend assertions for recoverable state and secret-safe diagnostics in `tests/support/assertions.py`
- [X] T042 [US2] Add safety fast subset and full safety sessions in `noxfile.py`
- [X] T043 [US2] Document fixture mutation and safety failure triage in `docs/testing.md`

**Checkpoint**: US2 可通过 `uv run pytest -m safety` 独立阻断写入安全回归。

## Phase 5: User Story 3 - 维护适配器与生成文件契约 (Priority: P2)

**Goal**: 建立适配器契约、支持矩阵、稳定输出基线和漂移阻断机制。

**Independent Test**: 运行 `uv run pytest -m "adapter or contract or snapshot"`，确认 planned 适配器不计入通过率，implemented 适配器具有合法契约、能力用例和稳定输出。

### Tests for User Story 3

- [X] T044 [P] [US3] Add adapter matrix status-rule tests in `tests/adapters/test_adapter_matrix.py`
- [X] T045 [P] [US3] Add implemented capability semantic-coverage tests in `tests/adapters/test_adapter_contract_semantics.py`
- [X] T046 [P] [US3] Add native no-redundant-output tests in `tests/adapters/test_native_capability_contract.py`
- [X] T047 [P] [US3] Add compatible/transform output snapshot tests in `tests/adapters/test_adapter_snapshots.py`
- [X] T048 [P] [US3] Add CI snapshot-update prohibition tests in `tests/contract/test_snapshot_policy.py`
- [X] T049 [P] [US3] Add deterministic file-tree baseline tests in `tests/snapshots/test_file_tree_baselines.py`

### Implementation for User Story 3

- [X] T050 [US3] Implement adapter matrix parsing and semantic validation in `tests/support/adapter_contracts.py`
- [X] T051 [US3] Implement syrupy normalizers and snapshot configuration in `tests/conftest.py`
- [X] T052 [US3] Add approved baseline naming and review policy in `tests/snapshots/README.md`
- [X] T053 [US3] Wire adapter, contract, and snapshot sessions into `noxfile.py`
- [X] T054 [US3] Document adapter promotion and baseline review in `docs/adapter-testing.md`

**Checkpoint**: US3 可独立发现适配器契约缺失和生成文件漂移。

## Phase 6: User Story 4 - 发布跨平台可信版本 (Priority: P2)

**Goal**: 在三平台验证构建物可安装、公开命令可调用且失败会阻断发布。

**Independent Test**: 运行 `uv run nox -s package` 和当前平台 `uv run nox -s release`；CI 聚合三平台结果时，任一失败均阻断发布。

### Tests for User Story 4

- [X] T055 [P] [US4] Add package session command-composition tests in `tests/contract/test_package_session.py`
- [X] T056 [P] [US4] Add installed-console-script subprocess tests in `tests/e2e/test_installed_cli.py`
- [X] T057 [P] [US4] Add symlink, copy fallback, readonly, and path capability tests in `tests/compatibility/test_platform_capabilities.py`
- [X] T058 [P] [US4] Add release-gate blocked-state aggregation tests in `tests/contract/test_release_gate.py`
- [X] T059 [P] [US4] Add explicit eight-combination CI matrix tests in `tests/contract/test_ci_matrix.py`

### Implementation for User Story 4

- [X] T060 [US4] Implement package build, metadata, clean-install, import, help, version, and doctor smoke session in `noxfile.py`
- [X] T061 [US4] Implement `main` and `release` Nox sessions in `noxfile.py`
- [X] T062 [US4] Create Main Gate matrix, full validation, build, and pip-audit workflow in `.github/workflows/main.yml`
- [X] T063 [US4] Create trusted-publishing Release Gate with three-platform smoke and protected environment in `.github/workflows/release.yml`
- [X] T064 [US4] Configure Python and GitHub Actions dependency updates in `.github/dependabot.yml`
- [X] T065 [US4] Document release validation and platform triage in `docs/release-validation.md`

**Checkpoint**: US4 可通过 package/release 会话和 CI 契约独立验证。

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 补齐文档、追踪矩阵、最终门禁和维护性检查。

- [X] T066 [P] Add FR/SC-to-test traceability in `docs/testing-traceability.md`
- [X] T067 [P] Add a 15-minute first-contributor validation path in `README.md`
- [X] T068 [P] Add project license, contribution, and security policies in `LICENSE`, `CONTRIBUTING.md`, and `SECURITY.md`
- [X] T069 Add file/function-size review guidance and snapshot-update review checklist in `docs/testing.md`
- [X] T070 Run and record PR, main, and package validation evidence in `specs/001-test-infrastructure/validation-report.md`
- [X] T071 Verify quickstart commands match implemented sessions in `specs/001-test-infrastructure/quickstart.md`
- [X] T072 Review `tests/`, `.github/workflows/`, and `docs/` for credentials, out-of-bound writes, automatic snapshot updates, and planned adapters misreported as implemented

## Dependencies & Execution Order

### Phase Dependencies

- Setup has no dependencies.
- Foundational depends on Setup and blocks all user stories.
- US1, US2, and US3 can begin after Foundational; US4 depends on US1 session conventions.
- Polish depends on all selected user stories.

### User Story Dependencies

- **US1**: Independent after Foundational; suggested MVP.
- **US2**: Independent after Foundational; reuses Nox marker wiring.
- **US3**: Independent after Foundational; shares snapshot support.
- **US4**: Depends on US1 public session behavior and integrates all story markers.

### Within Each User Story

- Complete test tasks before implementation tasks.
- Contract tests define command, session, and CI semantics before wiring Nox or workflows.
- Helper extensions precede tests that consume the new behavior.
- Documentation follows stable command and workflow names.

## Parallel Opportunities

- Setup: T003-T004.
- Foundational tests: T009-T012 and T018-T019.
- US1 tests: T023-T027.
- US2 tests: T032-T039.
- US3 tests: T044-T049.
- US4 tests: T055-T059.
- Polish: T066-T068.

## Independent Acceptance Checks

- **US1**: `uv run nox -s pr` returns correct status and diagnostics; docs-only paths run minimal checks.
- **US2**: `uv run pytest -m safety` proves isolated writes, idempotency, no unmanaged overwrite, no boundary escape, and redaction.
- **US3**: `uv run pytest -m "adapter or contract or snapshot"` proves schema, status, semantic coverage, and reviewed drift.
- **US4**: `uv run nox -s package` plus `uv run nox -s release` prove build/install/CLI smoke and release blocking; CI adds three-platform aggregation.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete US1 and validate `uv run nox -s pr`.
3. Add US2 safety guarantees before relying on file-writing product features.
4. Add US3 adapter contracts, then US4 release gates.

### Incremental Delivery

- Infrastructure helpers first, then contributor gate.
- Safety contracts before product file mutations are accepted.
- Adapter and snapshot coverage grows only for implemented capabilities.
- Release automation becomes publish-capable only after all technical gates pass.

## Notes

- `[P]` tasks touch different files and have no incomplete dependency.
- Planned adapters never count as implemented.
- CI must never update snapshots automatically.
- Product-command integration tests may begin failing before the corresponding product feature is implemented; they remain required and must pass before final feature completion.
