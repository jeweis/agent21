# Tasks: Agent21 MVP

**Input**: Design documents from `specs/002-agent21-mvp/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `.specify/memory/constitution.md`

**Tests**: 所有行为变更测试先行；写入、安全、幂等、漂移、CLI exit、适配器转换和跨平台能力必须先添加失败测试或可执行验收检查。

**Organization**: 核心顺序为 models/project/config/manifest/fs/lock -> init -> adapters/sync -> doctor -> skills -> compatibility/release。

## Phase 1: Setup

- [X] T001 Align Agent21 runtime/dev dependencies, package metadata, and test markers in `pyproject.toml`
- [X] T002 Verify package entry point and Python ignore patterns in `src/agent21/__main__.py` and `.gitignore`
- [X] T003 Create adapter package boundary in `src/agent21/adapters/__init__.py`
- [X] T004 Create MVP integration, E2E, and compatibility fixture roots in `tests/fixtures/projects/`

## Phase 2: Foundational

**Purpose**: 完成前阻塞所有用户故事。

- [X] T005 [P] Add domain model and validation tests in `tests/unit/test_models.py`
- [X] T006 [P] Add project root and path-boundary tests in `tests/unit/test_project.py`
- [X] T007 [P] Add config schema, unknown-field, invalid-type, and deterministic YAML tests in `tests/unit/test_config.py`
- [X] T008 [P] Add manifest schema, stable-order, digest, ownership, and drift tests in `tests/unit/test_manifest.py`
- [X] T009 [P] Add transaction prevalidation, staging, replace, rollback, cleanup, and conflict tests in `tests/unit/test_fs.py`
- [X] T010 [P] Add exclusive lock and stale-lock diagnostic tests in `tests/unit/test_lock.py`
- [X] T011 [P] Add MCP parse, Codex/Cursor transform, and redaction tests in `tests/unit/test_mcp.py`
- [X] T012 Implement domain errors and stable exit classification in `src/agent21/errors.py`
- [X] T013 Implement dataclass models, enums, and digest helpers in `src/agent21/models.py`
- [X] T014 Implement project root, safe relative paths, symlink-aware containment, and display normalization in `src/agent21/project.py`
- [X] T015 Implement config defaults, load/save, strict field validation, and deterministic YAML in `src/agent21/config.py`
- [X] T016 Implement manifest load/save, stable sorting, digest comparison, and ownership checks in `src/agent21/manifest.py`
- [X] T017 Implement transaction staging, atomic replacement, rollback, and cleanup in `src/agent21/fs.py`
- [X] T018 Implement exclusive project lock and stale-lock diagnostics in `src/agent21/lock.py`
- [X] T019 Implement MCP parsing, Codex TOML, Cursor JSON, and redaction helpers in `src/agent21/mcp.py`
- [X] T020 Wire shared domain failures to exit 0/1/2 behavior in `src/agent21/cli.py`

## Phase 3: User Story 1 - 初始化统一 Agent 配置 (Priority: P1)

**Independent Test**: 在空项目、已有权威源和未托管冲突项目中运行非交互 init，验证安全创建、复用、拒绝和幂等。

- [X] T021 [P] [US1] Add init CLI option and exit contract tests in `tests/contract/test_init_cli_contract.py`
- [X] T022 [P] [US1] Add empty-project initialization tests in `tests/integration/test_init_workflow.py`
- [X] T023 [P] [US1] Add existing `AGENTS.md` and `.mcp.json` reuse tests in `tests/integration/test_init_existing_sources.py`
- [X] T024 [P] [US1] Add unmanaged conflict and repeat-init idempotency tests in `tests/integration/test_init_conflicts.py`
- [X] T025 [US1] Implement executable detection and explicit user overrides in `src/agent21/scanner.py`
- [X] T026 [US1] Implement init service for config, manifest, Skills directory, sources, and conflict refusal in `src/agent21/init.py`
- [X] T027 [US1] Implement `agent21 init --agents --mode --yes` and stable result rendering in `src/agent21/cli.py`
- [X] T028 [US1] Add empty, existing-source, legacy-conflict, and non-interactive init fixtures in `tests/fixtures/projects/`

## Phase 4: User Story 2 - 将单一真源同步到多个 Agent (Priority: P1)

**Independent Test**: 同步五个 Agent 两次并运行 dry-run，验证最小输出、未启用跳过、未托管保护和 20 次幂等。

- [X] T029 [P] [US2] Add side-effect-free adapter protocol tests in `tests/adapters/test_adapter_protocol.py`
- [X] T030 [P] [US2] Add Claude instruction/MCP/Skills planning tests in `tests/adapters/test_claude_adapter.py`
- [X] T031 [P] [US2] Add Codex native and `.codex/config.toml` transform tests in `tests/adapters/test_codex_adapter.py`
- [X] T032 [P] [US2] Add Cursor native and `.cursor/mcp.json` transform tests in `tests/adapters/test_cursor_adapter.py`
- [X] T033 [P] [US2] Add OpenCode/Pi native and unsupported-MCP tests in `tests/adapters/test_native_adapters.py`
- [X] T034 [P] [US2] Add dry-run, conflict, escape, disabled-agent, and missing-executable sync tests in `tests/integration/test_sync_workflow.py`
- [X] T035 [P] [US2] Add 20-run file-tree and manifest equivalence tests in `tests/integration/test_sync_idempotency.py`
- [X] T036 [US2] Implement adapter protocol, context, registry, and capability types in `src/agent21/adapters/protocol.py`
- [X] T037 [P] [US2] Implement Claude planning in `src/agent21/adapters/claude.py`
- [X] T038 [P] [US2] Implement Codex planning in `src/agent21/adapters/codex.py`
- [X] T039 [P] [US2] Implement Cursor planning in `src/agent21/adapters/cursor.py`
- [X] T040 [P] [US2] Implement OpenCode planning in `src/agent21/adapters/opencode.py`
- [X] T041 [P] [US2] Implement Pi planning in `src/agent21/adapters/pi.py`
- [X] T042 [US2] Implement sync planning, prevalidation, dry-run, transaction apply, summaries, and manifest commit in `src/agent21/sync.py`
- [X] T043 [US2] Implement `agent21 sync --dry-run` CLI behavior in `src/agent21/cli.py`
- [X] T044 [US2] Promote MVP adapter fixtures and capability matrix to implemented status in `tests/fixtures/adapter_contracts/` and `specs/001-test-infrastructure/contracts/adapter-matrix.md`

## Phase 5: User Story 3 - 诊断配置健康与漂移 (Priority: P1)

**Independent Test**: 对健康、损坏、漂移、断链、残留事务和缺少可选 Agent 的项目运行 doctor，验证稳定分类和退出状态。

- [X] T045 [P] [US3] Add doctor CLI status/output contract tests in `tests/contract/test_doctor_cli_contract.py`
- [X] T046 [P] [US3] Add healthy, damaged, dangling transaction, stale lock, and broken-link tests in `tests/integration/test_doctor_workflow.py`
- [X] T047 [P] [US3] Add artifact drift, affected-agent, repair action, and redaction tests in `tests/integration/test_doctor_drift.py`
- [X] T048 [P] [US3] Add Skills and MCP health classification tests in `tests/integration/test_doctor_sources.py`
- [X] T049 [US3] Implement all project, schema, artifact, lock, transaction, Agent, Skill, and MCP checks in `src/agent21/doctor.py`
- [X] T050 [US3] Implement deterministic result sorting and blocked aggregation in `src/agent21/doctor.py`
- [X] T051 [US3] Implement `agent21 doctor` stdout/stderr split and redacted diagnostics in `src/agent21/cli.py`

## Phase 6: User Story 4 - 管理项目级 Skills (Priority: P2)

**Independent Test**: 安装、列出、移除本地与临时 Git Skill，验证 slug、`SKILL.md`、digest、manifest、漂移拒绝和失败无副作用。

- [X] T052 [P] [US4] Add skill install/list/remove CLI contract tests in `tests/contract/test_skill_cli_contract.py`
- [X] T053 [P] [US4] Add local Skill validation, install, digest, metadata, and manifest tests in `tests/integration/test_skill_lifecycle.py`
- [X] T054 [P] [US4] Add drift-safe managed-only Skill remove tests in `tests/integration/test_skill_remove.py`
- [X] T055 [P] [US4] Add temporary Git clone, `.git` exclusion, invalid repository, and rollback tests in `tests/integration/test_skill_git.py`
- [X] T056 [US4] Implement safe slug, local staging, digest, metadata, and manifest updates in `src/agent21/skills.py`
- [X] T057 [US4] Implement explicit Git source clone, validation, exclusion, and cleanup in `src/agent21/skills.py`
- [X] T058 [US4] Implement managed Skill removal with drift refusal in `src/agent21/skills.py`
- [X] T059 [US4] Implement `agent21 skill install/list/remove` commands in `src/agent21/cli.py`

## Phase 7: User Story 5 - 跨平台可靠使用 (Priority: P2)

**Independent Test**: 在目标平台运行 init/sync/doctor/Skill 生命周期与安装后 CLI 冒烟，验证 auto/copy/symlink、路径空格和权限回退。

- [X] T060 [P] [US5] Add sync-mode, relative-link, Windows fallback, space, separator, and case tests in `tests/compatibility/test_platform_sync_modes.py`
- [X] T061 [P] [US5] Add isolated cross-platform core workflow tests in `tests/compatibility/test_core_workflows.py`
- [X] T062 [P] [US5] Add installed CLI help/version/init/sync/doctor/Skill smoke tests in `tests/e2e/test_installed_cli.py`
- [X] T063 [US5] Implement symlink capability probing, project-relative links, and copy fallback reporting in `src/agent21/fs.py`
- [X] T064 [US5] Finalize cross-platform path, newline, permission, and summary normalization in `src/agent21/project.py`
- [X] T065 [US5] Complete compatibility, package, main, and release sessions in `noxfile.py`
- [X] T066 [US5] Finalize PR matrix and dependency-review gate in `.github/workflows/pr.yml`
- [X] T067 [US5] Finalize Main matrix, full validation, package, and audit gate in `.github/workflows/main.yml`
- [X] T068 [US5] Finalize three-platform smoke and PyPI Trusted Publishing gate in `.github/workflows/release.yml`

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T069 [P] Add install/init/sync/doctor/Skill first-use path in `README.md`
- [X] T070 [P] Update adapter promotion and capability documentation in `docs/adapter-testing.md`
- [X] T071 [P] Update release and platform validation documentation in `docs/release-validation.md`
- [X] T072 [P] Update test commands, coverage, safety, and failure triage in `docs/testing.md`
- [X] T073 Add MVP FR/SC-to-test traceability in `docs/testing-traceability.md`
- [X] T074 Validate and update implemented commands in `specs/002-agent21-mvp/quickstart.md`
- [X] T075 Run and record format, lint, mypy, unit, contract, adapter, integration, safety, compatibility, E2E, package, and release evidence in `specs/002-agent21-mvp/validation-report.md`
- [X] T076 Review `src/agent21/` for size, comments, secrets, project-boundary writes, and redundant truth sources

## Dependencies & Execution Order

- Setup has no dependency; Foundational depends on Setup and blocks all stories.
- US1 -> US2 -> US3 is sequential because sync and doctor depend on initialized config/manifest.
- US4 depends on Foundational and US1; it may overlap adapter work but must integrate with manifest and doctor.
- US5 depends on all public commands; Polish depends on all stories.
- Within each story, test tasks complete before implementation tasks.

## Parallel Opportunities

- Foundational tests: T005-T011.
- US1 tests: T021-T024.
- US2 tests: T029-T035; adapter implementations T037-T041 after T036.
- US3 tests: T045-T048.
- US4 tests: T052-T055.
- US5 tests: T060-T062.
- Polish docs: T069-T072.

## Implementation Strategy

1. Complete Setup and Foundational security primitives.
2. Deliver init, then sync, then doctor as the P1 MVP.
3. Add Skill lifecycle and cross-platform release verification.
4. Do not mark an adapter implemented until its contract, matrix, and tests change together.
5. Keep `001-test-infrastructure` open until all product-dependent integration/package gates pass.
