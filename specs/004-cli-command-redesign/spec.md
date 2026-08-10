# Feature Specification: CLI 命令重构与 Agent 管理

**Feature Branch**: `004-cli-command-redesign`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "命令可不可以简化？支持命令加减 agent；init 改名且自动同步；移除死参数 --yes；新增 status 状态总览；disable 支持 dry-run 预览并事务回收产物；无参命令交互式选择 Agent；Agent 名不再作为位置参数。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 一条命令让项目用起来 (Priority: P1)

用户把 Agent21 接入一个新项目时，不再需要理解 init 与 sync 两步：运行 `agent21 --agents codex,cursor`
非交互直接启用指定 Agent；或直接运行 `agent21`，在交互提示中选择要启用的 Agent。
工具自动建立缺失的权威源、启用所选 Agent，并立即生成各 Agent 的配置产物。
对已接入的项目重复运行等价于增量启用，不会重复或误关。

**Why this priority**: 这是 Agent21 的首次体验入口。当前「init 只建真源、须再手动 sync」的
两步流程是用户困惑的首要来源，简化它直接决定新用户能否一次成功。

**Independent Test**: 在一个空目录用 `--agents` 指定启用（非交互），验证权威源与指定 Agent
产物一次性生成；再执行一次确认幂等无漂移。另在 TTY 模拟交互选择，验证所选即所得。

**Acceptance Scenarios**:

1. **Given** 一个空项目目录，**When** 用户运行 `agent21 --agents codex,cursor`，
   **Then** 自动创建 `AGENTS.md`、`.agents/`（config、manifest、skills），只启用 codex
   与 cursor，并生成各自配置产物
2. **Given** 一个空项目目录且处于可交互终端，**When** 用户运行 `agent21`，
   **Then** 弹出全部已注册 Agent 的选择列表，用户选择后仅启用所选 Agent 并生成产物
3. **Given** 一个已启用 opencode 的项目，**When** 用户运行 `agent21 --agents codex`，
   **Then** codex 被启用且 opencode 仍保持启用，两次运行结果无漂移

---

### User Story 2 - 用命令增减 Agent (Priority: P1)

用户通过命令管理启用的 Agent，不再需要手工编辑 `.agents/config.yaml`：
新增用 `agent21 --agents codex`（或 `agent21 enable --agents codex`）；移除用
`agent21 disable --agents codex`。移除前可用 `--dry-run` 预览将删除的托管产物；
实际移除会事务化删除该 Agent 的托管产物。

**Why this priority**: 「加 Agent 合并、减 Agent 并回收产物」是管理多个工具的核心操作，
且回收涉及删除文件，安全性与可预览性是用户信任的前提。

**Independent Test**: 对已接入项目分别执行启用与 disable（含 `--dry-run` 与真实执行），
验证启用集合变化、产物生成与回收、以及未托管文件始终不受影响。

**Acceptance Scenarios**:

1. **Given** 一个已接入且启用 codex 的项目，**When** 用户运行 `agent21 disable --agents codex --dry-run`，
   **Then** 列出将删除的托管产物清单，不修改 config、不删除任何文件
2. **Given** 上述项目，**When** 用户运行 `agent21 disable --agents codex`，**Then** config
   中 codex 被禁用，其全部托管产物被删除，其他 Agent 的产物与用户自建文件保持不变
3. **Given** 一个已接入的项目，**When** 用户运行 `agent21 --agents codex`，**Then** codex
   被启用并生成产物，此前已启用的 Agent 不受影响

---

### User Story 3 - 一眼看清当前状态 (Priority: P2)

用户运行 `agent21 status` 即可获得项目接入总览：每个已注册 Agent 的启用状态、
本机可用性、已生成的托管产物，以及当前存在的关键健康问题（复用 doctor 的阻塞项与修复指引）。

**Why this priority**: 管理多个 Agent 时，用户需要快速确认「谁启用了、本机装没装、同步了什么」，
减少逐一查阅配置与清单的负担。

**Independent Test**: 分别对未初始化、已初始化、存在阻塞问题的项目运行 `agent21 status`，
验证状态表内容与阻塞项展示，且命令始终只读、不改动任何文件。

**Acceptance Scenarios**:

1. **Given** 一个已接入并启用多个 Agent 的项目，**When** 用户运行 `agent21 status`，
   **Then** 每个已注册 Agent 显示启用状态、本机可用性和已同步产物
2. **Given** 一个存在配置或漂移问题的项目，**When** 用户运行 `agent21 status`，
   **Then** 状态表后列出全部阻塞项及修复指引
3. **Given** 一个未初始化的目录，**When** 用户运行 `agent21 status`，
   **Then** 显示未初始化提示与接入指引，且退出码不表示致命错误

---

### User Story 4 - 干净一致的命令面与引导 (Priority: P3)

命令帮助、错误引导与文档保持一致：移除无实际作用的 `--yes` 死参数与已废弃的 `init`
命令；Agent 名不再作为位置参数，避免"命令 vs Agent 名"歧义，全部通过显式 `--agents`
或交互选择指定；所有需要「先接入」的命令在未初始化时报出同一句可执行引导。

**Why this priority**: 这是收尾质量项。死参数与旧命令会误导用户与自动化脚本，
一致引导降低出错后的恢复成本，显式参数消除歧义判断使命令面可长期演进。

**Independent Test**: 运行 `agent21 --help` 验证不再出现 `--yes` 与 `init`；在未初始化
目录运行 `sync`、`skill` 系列命令，验证都给出同一句接入引导；裸 Agent 名作为位置参数
报错并引导使用 `--agents`。

**Acceptance Scenarios**:

1. **Given** 已安装最新版 Agent21，**When** 用户运行 `agent21 --help`，
   **Then** 帮助中不再出现 `--yes`、`-y` 或 `init` 命令
2. **Given** 一个未初始化的目录，**When** 用户运行 `agent21 sync`，
   **Then** 报错并给出 `run 'agent21' first` 的可执行引导，退出码为 1
3. **Given** 用户输入 `agent21 codex`（Agent 名作为位置参数），**Then** 报未知命令
   错误并提示改用 `--agents codex`

---

### Edge Cases

- 未初始化目录运行无参默认命令：交互（TTY）环境自动建立权威源后继续；非 TTY 环境引导
  使用 `--agents`，不写任何文件
- 已初始化 + TTY + 无参交互留空：保持当前启用状态不动，不额外启用任何 Agent
- 非 TTY + 无参：报错引导使用 `--agents codex,cursor` 显式指定，不启用、不写文件、不挂起
- 交互选择输入：留空=全部、非法编号提示重输、重复编号去重、Ctrl+C 取消且不写文件
- 本机没有任何 Agent 可检测：交互列表仍展示全部已注册 Agent；非 TTY 提示用 `--agents`
- 裸 Agent 名 `agent21 codex`：报 `No such command`，引导使用 `--agents codex`
- `disable` 目标 Agent 当前未启用：明确提示而非静默无操作
- `disable` 时该 Agent 产物已被用户手工改动（漂移）：删除前报告漂移与修复路径，不静默删除
- `disable` 回收遇到权限或平台限制：删除失败回滚并报告，不留半删状态
- 已初始化 + TTY 交互勾选未安装 Agent：config 记录启用、sync 显示 skipped，装好后重跑即生效

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 支持无子命令时执行默认启用命令：`agent21 --agents codex,cursor`
  非交互启用指定 Agent（逗号分隔），缺失的权威源自动建立，随后立即同步生成产物
- **FR-002**: 系统 MUST 在可交互终端（TTY）运行无参 `agent21` 时展示**全部已注册 Agent**
  的选择列表，让用户选择要启用的 Agent，随后合并启用并同步
- **FR-003**: 系统 MUST 在非交互环境（非 TTY）运行无参 `agent21` 时，不执行任何启用或
  写操作，并报错引导用户使用 `--agents` 显式指定要启用的 Agent（不得挂起等待输入）
- **FR-004**: 系统 MUST 在已初始化项目上运行无参 `agent21` 时仍提供交互选择，展示当前
  已启用状态，且选择结果**只增不减**（未选中的已启用 Agent 保持启用）
- **FR-005**: 系统 MUST 在交互列表中对本机检测到 CLI 可执行文件的 Agent 标记 `[已安装]`；
  标记规则基于 Agent 的能力定义，不针对特定 Agent 特判
- **FR-006**: 系统 MUST 在交互选择留空时，对全新项目启用全部已注册 Agent，对已初始化
  项目保持当前启用状态不变
- **FR-007**: 系统 MUST 支持 `agent21 enable --agents codex,cursor` 作为默认命令的显式
  等价形式；`enable` 不带 `--agents` 时与无参默认命令走相同的交互/非交互逻辑
- **FR-008**: 系统 MUST 支持 `--mode`（auto/copy/symlink，默认 auto）仅于首次建立
  config 时生效；对既有项目不覆盖已有同步模式
- **FR-009**: 系统 MUST 支持 `agent21 disable --agents codex,cursor`：更新 config 为禁用，
  并事务化删除这些 Agent 的全部托管产物
- **FR-010**: 系统 MUST 支持 `agent21 disable --agents codex --dry-run`：仅预览将删除的
  托管产物，不修改 config、不删除任何文件
- **FR-011**: 系统 MUST 确保 disable 只删除 manifest 中标记为托管且属于目标 Agent
  的路径；用户自建或未托管文件在任何情况下不被删除
- **FR-012**: 系统 MUST 在 disable 删除失败时回滚到删除前状态，不留下半删产物
- **FR-013**: 系统 MUST 支持 `agent21 status` 只读展示每个已注册 Agent 的启用状态、
  本机可用性与已同步产物，并追加展示当前阻塞项及修复指引
- **FR-014**: 系统 MUST 移除 `--yes`/`-y` 死参数；`--help` 与文档中不再出现
- **FR-015**: 系统 MUST 移除 `init` 命令；Agent 名不再作为位置参数解析；`sync`、`skill`
  系列等命令在未初始化时报错并给出统一引导 `run 'agent21' first`

### Configuration, Compatibility & Safety *(mandatory for Agent21 behavior changes)*

- **Authoritative Inputs**: `AGENTS.md`、`.agents/config.yaml`、`.agents/skills/`、
  `.mcp.json`（保持不变，仍为唯一权威源）
- **Managed Outputs**: 各 Agent 产物（`CLAUDE.md`、`.claude/skills/`、`.codex/config.toml`、
  `.cursor/mcp.json`、`opencode.json`、`.codebuddy/skills/`、`.qoder/skills/` 等）；
  disable 时这些托管产物被事务化删除，删除记录可回滚
- **Affected Agents**: 全部七个已注册 Agent（claude、codex、cursor、opencode、pi、
  workbuddy、qoder）。命令层重构，不改变各 Agent 的指令/Skills/MCP 能力分类与产物内容
- **Platforms / Sync Modes**: Linux、macOS、Windows；auto、copy、symlink。产物回收
  与写入走同一事务机制，需在三平台验证；Windows 上符号链接不可用时按既有降级策略
- **Recovery & Drift**: 默认命令与 enable 保持幂等；disable 删除前可 dry-run 预览、
  删除走事务（备份到临时目录、失败回滚）；被手工改动的托管产物在删除前须报告漂移
  而非静默删除
- **Security Boundary**: 写入范围始终限于当前项目；只删除 manifest 明确标记的托管
  路径，绝不触碰用户资产；status/doctor 只读；错误与诊断不输出凭证；交互仅接受本地
  编号选择，不执行任何输入内容

### Key Entities *(include if feature involves data)*

- **AgentSelection**: `.agents/config.yaml` 中每个 Agent 的启用开关，由默认命令、
  enable/disable 增删，是 status 与 sync 的判断依据
- **ManagedArtifact**: `.agents/manifest.yaml` 中标记为托管的目标路径，是「只删托管
  产物」的安全边界依据
- **HealthCheckResult**: doctor 的输出模型，status 复用它展示阻塞项与修复指引

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新用户在空项目从安装到「启用指定 Agent 且产物生成」的可用命令数不超过 1 条
- **SC-002**: `disable --dry-run` 预览的待删清单与实际执行删除的文件集合 100% 一致
- **SC-003**: 执行 disable 后，非目标 Agent 的托管产物与全部用户自建文件 0 丢失
- **SC-004**: 默认命令、enable、disable、status 四个命令的自动化测试在
  Linux、macOS、Windows 三个平台全部通过
- **SC-005**: `agent21 --help` 输出中不包含 `--yes`、`-y` 与 `init` 字样；
  未初始化目录下 `sync`/`skill` 的报错都包含 `run 'agent21' first`
- **SC-006**: 交互选择列表始终展示全部已注册 Agent，不因本机检测结果遗漏任何 Agent

## Assumptions

- 交互式选择是用户主动决策行为，选定结果落盘后 sync 仍保持确定性幂等；交互本身不引入
  对同步结果的随机性（宪章 III 的确定性适用于选定后的同步过程）
- 已初始化项目上无参交互留空 = 保持当前启用状态不变；全新项目留空 = 启用全部已注册 Agent
- `enable` 不带 `--agents` 时与无参默认命令共享同一套交互/非交互逻辑，保证单一语义
- 交互标记规则基于 `capability.executable`：存在且 PATH 可调起 → `[已安装]`；
  executable 为 None（如 workbuddy）或无 CLI → 无标记但始终可选，不做 Agent 特判
- `--agents` 参数使用逗号分隔多个 Agent 名（`--agents codex,cursor`），与旧 `init` 参数一致
- 裸 Agent 名作为位置参数不再被解析为启用命令，统一报未知命令并引导使用 `--agents`
- `disable` 默认直接执行事务删除，不设独立确认开关；由 `--dry-run` 预览、仅删托管
  路径、事务回滚三重机制提供安全保护
- 移除 `init` 命令时不保留任何兼容别名（用户明确要求不做兼容），仅引导文本统一指向
  `run 'agent21' first`
- `enable` 保留为显式命令以提升帮助可读性，与默认命令完全等价，不作为历史兼容负担
