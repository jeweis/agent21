---

description: "Task list for CLI command redesign"
---

# Tasks: CLI 命令重构与 Agent 管理

**Input**: Design documents from `/specs/004-cli-command-redesign/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED for behavior changes. Write the failing test before implementation.

**Organization**: Tasks are grouped by user story. Foundational tasks block all stories.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 确认行为变更前的基线，确保后续改动可追踪

- [X] T001 运行 `uv run pytest` 确认现有 190 项测试全绿，记录基线（任何行为变更前必须通过）

**Checkpoint**: 基线确认完成

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 跨命令面共享的核心机制——产物回收、默认命令框架、死参数清理。任何 US 都依赖这些基础。

**⚠️ CRITICAL**: 本阶段完成前，任何用户故事都不能开始。

- [X] T002 [P] 编写失败测试：`apply_transaction` 的 retire 事务删除（备份/回滚/只删托管路径）在 tests/unit/test_fs.py
- [X] T003 [P] 编写失败测试：`SyncResult.retired` 字段与 sync 计算 retired（旧 manifest − 本次计划 − unavailable_agents）在 tests/integration/test_sync_retirement.py
- [X] T004 [P] 实现 `apply_transaction` retire 参数与事务内删除逻辑（backup 到 `.agents/.tmp/<txn>/backup`、journal 记录、失败回滚）在 src/agent21/fs.py
- [X] T005 [P] 实现 `SyncResult.retired` 字段（默认空元组）在 src/agent21/models.py
- [X] T006 [US4] 移除 `--yes`/`-y` Option 与 `assume_yes` 参数及 `del assume_yes`（死参数清理）在 src/agent21/cli.py、src/agent21/init.py
- [X] T007 [US4] 更新所有调用 `initialize_project(..., assume_yes=True)` 的测试（tests/integration、tests/compatibility、tests/contract 等约 20 处）移除该参数
- [X] T008 [US4] 统一未初始化引导消息为 `run 'agent21' first` 在 src/agent21/sync.py、src/agent21/skills.py、src/agent21/doctor.py
- [X] T009 [US4] 编写契约测试：`--help` 不再含 `--yes`/`-y`/`init`；未初始化 `sync`/`skill` 引导含 `run 'agent21' first` 在 tests/contract/test_cli_public_surface.py

**Checkpoint**: Foundation ready - 用户故事实现可开始

---

## Phase 3: User Story 1 - 一条命令让项目用起来 (Priority: P1) 🎯 MVP

**Goal**: 默认命令 enable：`agent21 --agents codex,cursor` 非交互启用；无参时 TTY 交互选择、非 TTY 引导 `--agents`；缺失真源自动建立；幂等追加。

**Independent Test**: 空目录 `agent21 --agents codex,cursor` 后真源与 codex/cursor 产物一次性生成；重复执行幂等。

### Tests for User Story 1 (REQUIRED for behavior changes) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] 契约测试：`--agents` 逗号分隔解析 + 无子命令走默认 enable + 裸 Agent 名报 `No such command` 在 tests/contract/test_cli_default_command.py
- [X] T011 [P] [US1] 单元测试：`parse_selection` 交互编号解析纯函数（空=全部/保持现状、非法编号、重复去重）在 tests/unit/test_selection.py
- [X] T012 [P] [US1] 集成测试：空目录 `agent21 --agents codex,cursor` 建立真源并生成产物 在 tests/integration/test_default_command.py
- [X] T013 [P] [US1] 集成测试：默认命令幂等 + 追加不误关（opencode 保持启用）在 tests/integration/test_default_command.py

### Implementation for User Story 1

- [X] T014 [US1] 重构 cli.py：`Typer(invoke_without_command=True)` + callback 用 `ctx.invoked_subcommand is None` 判断默认路径 + `--agents`/`--mode` 参数 + `enable` 显式命令 在 src/agent21/cli.py
- [X] T015 [P] [US1] 实现 `parse_selection` 纯函数与交互选择封装（编号列表、`[已安装]` 标记、is_tty 判断）在 src/agent21/selection.py
- [X] T016 [US1] 接入交互/非 TTY 路径到默认 enable：TTY 交互选择、非 TTY 报错引导 `--agents`（退出码 1）、未初始化自动建真源 在 src/agent21/cli.py
- [X] T017 [US1] e2e：子进程验证 `agent21 --agents codex` 真实 argv 与交互输入模拟 在 tests/e2e/test_default_command.py

**Checkpoint**: User Story 1 独立可用（MVP）

---

## Phase 4: User Story 2 - 用命令增减 Agent (Priority: P1)

**Goal**: `disable --agents codex --dry-run` 预览；`disable --agents codex` 事务化回收该 Agent 托管产物（只删托管路径、可回滚、漂移保护、未启用提示）。

**Independent Test**: 已启用 codex 项目上 dry-run 预览与实际删除集合一致；执行后只删 codex 产物，未托管文件保留。

### Tests for User Story 2 (REQUIRED for behavior changes) ⚠️

- [X] T018 [P] [US2] 集成测试：`disable --dry-run` 输出 would retire 清单且不写盘不改 config，与执行删除集合一致 在 tests/integration/test_disable.py
- [X] T019 [P] [US2] 集成测试：`disable` 事务删除只删目标 Agent 托管产物，未托管文件与其它 Agent 产物保留 在 tests/integration/test_disable.py
- [X] T020 [P] [US2] 集成测试：`disable` 未启用提示、漂移产物报告而非静默删、重复 disable 幂等 在 tests/integration/test_disable.py

### Implementation for User Story 2

- [X] T021 [US2] 实现 `disable` 命令（`--agents` 逗号分隔 + `--dry-run`），dry-run 复用 sync retired 预览 在 src/agent21/cli.py
- [X] T022 [US2] disable 接入 config 更新（enabled=false）与 sync retired 事务删除，输出 `disabled:` 与 `retired:` 在 src/agent21/cli.py、src/agent21/sync.py

**Checkpoint**: User Story 1 与 2 均独立可用

---

## Phase 5: User Story 3 - 一眼看清当前状态 (Priority: P2)

**Goal**: `status` 只读展示每个已注册 Agent 的启用状态、本机可用性（含 `none-required`）、已同步产物，并追加 doctor `blocked` 项与 action；未初始化宽容显示接入指引。

**Independent Test**: 对未初始化、已初始化、存在阻塞问题的项目运行 `status`，验证状态表与 blocked 展示且只读。

### Tests for User Story 3 (REQUIRED for behavior changes) ⚠️

- [X] T023 [P] [US3] 集成测试：`status` 状态表（启用/可用/产物三列）+ 命令只读不改文件 在 tests/integration/test_status.py
- [X] T024 [P] [US3] 集成测试：`status` 追加 doctor blocked 与 action、未初始化宽容提示、退出码非致命 在 tests/integration/test_status.py

### Implementation for User Story 3

- [X] T025 [US3] 实现 `status` 命令：复用 detect_agents + config + manifest + diagnose_project 聚合状态，尾部追加 blocked 在 src/agent21/cli.py（超 80 行则拆 src/agent21/status.py）

**Checkpoint**: 三个用户故事均可独立验证

---

## Phase 6: User Story 4 - 干净一致的命令面与引导 (Priority: P3)

**Goal**: 移除 `init` 命令与 `--yes`；Agent 名不再作为位置参数（裸名报 `No such command` 引导 `--agents`）；help 与文档一致；迁移既有 CLI 测试。

**Independent Test**: `--help` 无 `--yes`/`-y`/`init`；未初始化 `sync`/`skill` 统一引导；裸名报错。

### Tests for User Story 4 (REQUIRED for behavior changes) ⚠️

- [X] T026 [P] [US4] 契约测试：裸 Agent 名位置参数报 `No such command` 并提示 `--agents` 在 tests/contract/test_cli_default_command.py
- [X] T027 [P] [US4] 契约测试：`agent21 enable --agents codex` 与默认命令等价 在 tests/contract/test_cli_default_command.py

### Implementation for User Story 4

- [X] T028 [US4] 移除 `init_command` 与 `--yes` 在 src/agent21/cli.py（T006 已删参数，此处删命令）
- [X] T029 [US4] 迁移既有 CLI `init` 测试到新命令面：tests/contract/test_init_cli_contract.py 改 `enable`/默认命令断言、tests/e2e/test_installed_cli.py 改 `--agents`
- [X] T030 [US4] 更新 tests/integration/test_init_workflow.py 使 `initialize_project` 测试适配新签名（assume_yes 已移除）与 enable 合并语义断言

**Checkpoint**: 命令面干净一致

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 文档、门禁与跨平台验证

- [ ] T031 [P] 重写 README 命令表与快速开始为 `agent21`/`--agents`/`enable`/`disable`/`status`，移除 `init`/`--yes` 在 README.md
- [ ] T032 [P] 同步 docs/ 与 specs/003 相关文档的 CLI 引用（init/--yes → 新命令面）
- [ ] T033 运行 `uv run ruff check . && uv run ruff format --check . && uv run mypy src/agent21/`
- [ ] T034 运行 `uv run nox -s pr`（格式、lint、mypy、快速测试、覆盖率）全绿
- [ ] T035 运行 `uv run nox -s main`（含兼容性、快照、跨平台契约）全绿
- [ ] T036 运行 `uv run nox -s package` 构建并干净安装，CLI 冒烟（`agent21 --help`、默认命令、disable、status）
- [ ] T037 运行 specs/004-cli-command-redesign/quickstart.md 全部场景验证
- [ ] T038 运行 `uv run agent21 doctor` 捕获干净或已说明的报告
- [ ] T039 确认全部函数 ≤80 行、单文件 ≤1000 行；无死参数/未使用 import 残留

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，先行确认基线
- **Foundational (Phase 2)**: 依赖 Setup；BLOCKS 所有用户故事
- **User Stories (Phase 3-6)**: 依赖 Foundational；P1→P2→P3 顺序或并行
- **Polish (Phase 7)**: 依赖所有所需用户故事完成

### User Story Dependencies

- **US1 (P1)**: 依赖 Foundational（cli 框架、retired、引导统一）
- **US2 (P1)**: 依赖 Foundational（retired/fs retire）；复用 US1 的 cli 框架与 config 更新，但独立可测
- **US3 (P2)**: 依赖 Foundational；独立可测
- **US4 (P3)**: 依赖 Foundational（--yes/引导清理在其内）；与 US1-3 的 cli.py 同文件，建议在 US1-3 后串行

### Within Each User Story

- 测试 MUST 先写并确认 FAIL，再实现
- 纯函数（parse_selection）→ 命令接入 → 集成

### Parallel Opportunities

- T002/T003（两个失败测试，不同文件）可并行
- T010/T011/T012/T013（US1 四个测试，不同文件）可并行
- T015 [P] 与 T014/T016 文件不同（selection.py vs cli.py）可并行
- T018/T019/T020（US2 测试）可并行
- T023/T024（US3 测试）可并行
- T031/T032（文档）可并行
- 注意：cli.py 被 US1/2/3/4 共享，同文件任务不可并行（串行演进）

---

## Parallel Example: Foundational

```bash
Task: "T002 失败测试 apply_transaction retire 在 tests/unit/test_fs.py"
Task: "T003 失败测试 SyncResult.retired 在 tests/integration/test_sync_retirement.py"
```

## Parallel Example: User Story 1

```bash
Task: "T010 契约测试默认命令 在 tests/contract/test_cli_default_command.py"
Task: "T011 单元测试 parse_selection 在 tests/unit/test_selection.py"
Task: "T012 集成测试首次一站式 在 tests/integration/test_default_command.py"
Task: "T013 集成测试幂等追加 在 tests/integration/test_default_command.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（retired/fs retire/cli 框架/--yes 清理/引导统一）
3. 完成 Phase 3: User Story 1（默认命令 + 交互 + 非 TTY 引导）
4. **STOP and VALIDATE**: 独立验证 US1

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 默认命令 → 独立测试 → MVP
3. US2 disable 回收 → 独立测试
4. US3 status → 独立测试
5. US4 命令面收尾 → 独立测试
6. Polish 门禁与文档

---

## Notes

- [P] 任务 = 不同文件、无依赖
- [USx] 标签映射到 spec.md 用户故事
- cli.py 为共享文件，相关任务不标 [P]，按 US1→US2→US3→US4 串行演进
- 行为变更测试先行（宪法 V）；文档/纯机械变更需记录为何不影响行为
- 每个逻辑组完成后提交
- 避免：模糊任务、同文件并行冲突、跨故事依赖破坏独立性
