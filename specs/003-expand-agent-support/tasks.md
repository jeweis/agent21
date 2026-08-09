# Tasks: 扩展 Agent 支持

**Input**: `/specs/003-expand-agent-support/` 下的 spec、plan、research、data-model、contracts 与 quickstart

**Tests**: 所有行为变更必须先添加失败测试，再实现并记录对应验证证据。

**Organization**: 任务按基础能力与四个用户故事分组；每个故事均可单独验收。

## Phase 1: Setup（契约基线）

**Purpose**: 锁定七个 Agent 的公共清单、能力矩阵与测试输入。

- [X] T001 更新七个 Agent 的契约夹具与能力状态，确保 WorkBuddy 使用 `.codebuddy/` 体系，在 `tests/fixtures/adapter_contracts/*.json` 和 `specs/001-agent21-foundation/contracts/adapter-matrix.md` 中记录真实支持范围
- [X] T002 [P] 为新增 Agent 和 MCP 依赖元数据添加失败的模型/契约测试到 `tests/unit/test_models.py`、`tests/adapters/test_adapter_matrix.py` 和 `tests/contract/test_adapter_contract_schema.py`
- [X] T003 [P] 为旧五 Agent 配置加载、新七 Agent 配置序列化、未知 Agent 拒绝添加失败测试到 `tests/unit/test_config.py` 和 `tests/integration/test_config_migration.py`

---

## Phase 2: Foundational（阻塞前置）

**Purpose**: 建立所有故事共用的注册、检测、依赖诊断和安全同步语义。

**⚠️ CRITICAL**: 本阶段完成前不得实现任何单一 Agent 故事。

- [X] T004 实现七个登记 Agent、向后兼容 schema v1 归一化与稳定序列化，修改 `src/agent21/models.py` 和 `src/agent21/config.py` 使 T002-T003 通过
- [X] T005 为 `qodercli` 检测、WorkBuddy configuration-only 状态和任意依赖可执行文件检查添加失败测试到 `tests/unit/test_project.py`、`tests/integration/test_init_workflow.py` 和 `tests/integration/test_doctor_workflow.py`
- [X] T006 实现登记清单与可执行检测解耦，修改 `src/agent21/scanner.py` 和 `src/agent21/init.py`，保证 WorkBuddy 可显式选择但不伪报本机 CLI 可用
- [X] T007 为“已启用但临时不可用的 Agent 不丢失既有 manifest 所有权”添加失败回归测试到 `tests/integration/test_sync_workflow.py` 和 `tests/integration/test_failure_recovery.py`
- [X] T008 在 `src/agent21/sync.py` 中实现 configuration-only 同步、缺失可执行文件精确跳过和被跳过 Agent 的既有 manifest 条目保留，使 T007 通过
- [X] T009 在 `src/agent21/doctor.py` 中实现通用 Agent 可执行文件、configuration-only 与可选 MCP 依赖诊断，确保只检查存在性、不执行命令且不输出敏感值
- [X] T010 运行 `uv run pytest tests/unit/test_models.py tests/unit/test_config.py tests/integration/test_config_migration.py tests/integration/test_init_workflow.py tests/integration/test_sync_workflow.py tests/integration/test_doctor_workflow.py tests/integration/test_failure_recovery.py` 并记录基础阶段通过结果

**Checkpoint**: 七个 Agent 可稳定配置，所有故事共享的选择、检测、诊断、事务与 manifest 语义已就绪。

---

## Phase 3: User Story 1 - 统一 OpenCode MCP 配置（Priority: P1）🎯 MVP

**Goal**: 将权威 `.mcp.json` 的受支持本地和远程服务器确定性转换为项目 `opencode.json`。

**Independent Test**: 只启用 OpenCode，验证 dry-run、首次同步、重复同步、doctor、未知字段和未托管冲突。

### Tests for User Story 1

- [X] T011 [P] [US1] 为本地/远程 MCP 精确字段映射、稳定排序、disabled/timeout 与未知字段拒绝添加失败单元测试到 `tests/unit/test_mcp.py`
- [X] T012 [P] [US1] 为 OpenCode capability、空 MCP、transform 目标与稳定快照添加失败测试到 `tests/adapters/test_opencode_adapter.py` 和 `tests/adapters/test_adapter_snapshots.py`
- [X] T013 [P] [US1] 为 OpenCode dry-run、幂等同步、未托管 `opencode.json` 冲突和无半写添加失败集成测试到 `tests/integration/test_mcp_config.py` 和 `tests/integration/test_failure_recovery.py`

### Implementation for User Story 1

- [X] T014 [US1] 在 `src/agent21/mcp.py` 实现 OpenCode 本地/远程服务器逐字段验证与稳定 JSON 转换，错误仅暴露服务器名和字段名
- [X] T015 [US1] 在 `src/agent21/adapters/opencode.py` 声明 MCP transform 并规划唯一托管目标 `opencode.json`
- [X] T016 [US1] 在 `src/agent21/adapters/__init__.py` 注册更新后的 OpenCode adapter，并审查/更新对应快照使 T011-T013 通过
- [X] T017 [US1] 连续执行 20 次 OpenCode 同输入同步测试，并运行 `uv run pytest tests/unit/test_mcp.py tests/adapters/test_opencode_adapter.py tests/adapters/test_adapter_snapshots.py tests/integration/test_mcp_config.py`

**Checkpoint**: OpenCode MCP 可独立使用、冲突安全且重复同步零差异。

---

## Phase 4: User Story 2 - 让 Pi 使用统一 MCP 配置（Priority: P1）

**Goal**: 将 Pi MCP 声明为依赖 `pi-mcp-adapter` 的兼容能力，缺失时给出安全、准确的诊断。

**Independent Test**: 只启用 Pi，分别模拟 adapter 可检测和缺失；验证不安装、不执行、不写用户全局目录且不生成 MCP 副本。

### Tests for User Story 2

- [X] T018 [P] [US2] 为 Pi MCP dependency 元数据、零托管输出和能力分类添加失败测试到 `tests/adapters/test_pi_adapter.py`
- [X] T019 [P] [US2] 为 adapter 可检测/缺失/运行态不可离线确认的 doctor 结果添加失败测试到 `tests/integration/test_doctor_workflow.py`
- [X] T020 [P] [US2] 为 sync 不执行或安装 adapter、不写 `~/.pi`、其他 Agent 不受影响添加失败安全测试到 `tests/integration/test_sync_workflow.py` 和 `tests/integration/test_project_boundary.py`

### Implementation for User Story 2

- [X] T021 [US2] 在 `src/agent21/adapters/pi.py` 声明 `pi-mcp-adapter` 依赖、静态安装提示和无输出兼容语义
- [X] T022 [US2] 完成 `src/agent21/doctor.py` 与 `src/agent21/sync.py` 的 Pi 依赖接线，只在启用 Pi 且 MCP 非空时报告依赖状态
- [X] T023 [US2] 移除或改写 `tests/adapters/test_native_adapters.py` 中 Pi MCP unsupported 的旧断言，并运行 `uv run pytest tests/adapters/test_pi_adapter.py tests/integration/test_doctor_workflow.py tests/integration/test_sync_workflow.py tests/integration/test_project_boundary.py`

**Checkpoint**: Pi 继续原生读取指令/Skills，MCP 依赖状态准确且不会触发第三方代码。

---

## Phase 5: User Story 3 - 在团队项目中启用 WorkBuddy（Priority: P2）

**Goal**: 支持显式选择 WorkBuddy，并将项目规则和 Skills 同步到 `.codebuddy/`，根 `.mcp.json` 保持原生复用。

**Independent Test**: 只启用 WorkBuddy，验证 init、dry-run、同步、重复同步、doctor、copy/symlink/auto 和未托管冲突。

### Tests for User Story 3

- [X] T024 [P] [US3] 为 WorkBuddy configuration-only capability、原生 `AGENTS.md` 与 `.codebuddy/skills` 规划添加失败测试到 `tests/adapters/test_workbuddy_adapter.py`
- [X] T025 [P] [US3] 为 WorkBuddy 初始化、dry-run、幂等同步、根 MCP 原生复用和 doctor 添加失败集成测试到 `tests/integration/test_expanded_agent_workflows.py`
- [X] T026 [P] [US3] 为 `.codebuddy/skills/` 未托管同名内容保护和不生成指令副本添加失败测试到 `tests/integration/test_sync_workflow.py`

### Implementation for User Story 3

- [X] T027 [US3] 创建 `src/agent21/adapters/workbuddy.py`，只规划 `.codebuddy/skills`，不得创建指令/MCP 副本或写 `~/.codebuddy`
- [X] T028 [US3] 在 `src/agent21/adapters/__init__.py` 注册 WorkBuddy adapter，并让 T024-T026 在 copy、symlink 和 auto 适用场景通过
- [X] T029 [US3] 连续执行 20 次 WorkBuddy 同输入同步测试，并运行 `uv run pytest tests/adapters/test_workbuddy_adapter.py tests/integration/test_expanded_agent_workflows.py tests/integration/test_sync_workflow.py`

**Checkpoint**: WorkBuddy 可独立配置，并准确复用腾讯 CodeBuddy 配置体系而不与产品名称混淆。

---

## Phase 6: User Story 4 - 在团队项目中启用 Qoder（Priority: P2）

**Goal**: 支持 Qoder 检测、选择和诊断；原生复用根指令/MCP，只为 Skills 生成 `.qoder/skills`。

**Independent Test**: 只启用 Qoder，验证 qodercli 检测、init、dry-run、同步、重复同步、doctor 和未托管冲突。

### Tests for User Story 4

- [X] T030 [P] [US4] 为 Qoder capability、`.qoder/skills` 规划和零指令/MCP 副本添加失败测试到 `tests/adapters/test_qoder_adapter.py`
- [X] T031 [P] [US4] 为 Qoder 可执行文件检测、初始化、幂等同步和 doctor 添加失败集成测试到 `tests/integration/test_expanded_agent_workflows.py`
- [X] T032 [P] [US4] 为 `.qoder/skills` 未托管内容保护和缺失 qodercli 时既有 manifest 保留添加失败测试到 `tests/integration/test_sync_workflow.py`

### Implementation for User Story 4

- [X] T033 [US4] 创建 `src/agent21/adapters/qoder.py`，声明 instructions/MCP native、Skills compatible 并只规划 `.qoder/skills`
- [X] T034 [US4] 在 `src/agent21/adapters/__init__.py` 注册 Qoder adapter，并完成 `qodercli` 检测接线使 T030-T032 通过
- [X] T035 [US4] 连续执行 20 次 Qoder 同输入同步测试，并运行 `uv run pytest tests/adapters/test_qoder_adapter.py tests/integration/test_expanded_agent_workflows.py tests/integration/test_sync_workflow.py`

**Checkpoint**: Qoder 可独立使用且能力报告、托管目标和冲突语义准确。

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 对外文档、七 Agent 回归、跨平台和发布前证据。

- [X] T036 [P] 更新 `README.md` 的七 Agent 使用说明与能力矩阵，明确 WorkBuddy 复用 `.codebuddy`、Pi 依赖和 OpenCode 转换边界
- [X] T037 [P] 更新 `docs/adapter-testing.md`、`docs/testing-traceability.md` 和 `docs/release-validation.md` 的新增 adapter 验证与发布门禁
- [X] T038 更新 `tests/adapters/test_native_capability_contract.py`、`tests/adapters/test_adapter_contract_semantics.py` 和 `tests/contract/test_cli_public_surface.py`，确保公共帮助与七 Agent 契约一致
- [X] T039 运行 `uv run pytest -m "adapter or contract"` 和 `uv run pytest -m "integration or safety"`，修复所有新增与回归失败
- [X] T040 运行 `uv run nox -s pr`、`uv run nox -s main` 和 `uv run nox -s package`，记录 lint、格式、类型、测试、覆盖率和构建结果
- [X] T041 按 `specs/003-expand-agent-support/quickstart.md` 完成四个隔离场景、dry-run、重复同步、冲突和 doctor 验证，并将证据写入 `specs/003-expand-agent-support/validation-report.md`
- [X] T042 复核所有新增/实质变更文件与方法注释、1000 行文件/80 行函数边界、凭证脱敏、Constitution Check 和完整 diff

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → 所有用户故事 → Phase 7。
- US1 与 US2 同为 P1，但共享基础依赖后可独立验收；本次顺序执行 US1 → US2。
- US3 与 US4 在 Phase 2 后彼此独立；本次顺序执行以减少共享 registry 与集成测试文件冲突。
- 每个故事严格执行：失败测试 → 实现 → 目标测试 → 独立 checkpoint。
- 文档任务 T036-T037 可并行，但必须在实现稳定后校对真实行为。

## Implementation Strategy

1. 先完成 schema、registry、scanner、doctor、sync 的最小共用扩展。
2. 依次交付 OpenCode MCP、Pi adapter、WorkBuddy、Qoder，每个故事独立验证。
3. 最后统一更新公共文档，运行 PR/Main/Package 门禁和 quickstart。
4. 不自动安装第三方 adapter、不修改用户全局配置、不发布未经验证的能力声明。
