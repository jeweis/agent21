# Feature Specification: Agent21 MVP

**Feature Branch**: `未创建（仓库未配置 before_specify 分支钩子）`

**Created**: 2026-08-09

**Status**: Draft

**Input**: User description: "实现 Agent21 项目级 AI 编程代理统一配置与同步平台的 MVP，
让团队维护一套工程级设置并同步到多个 Agent，完成测试、GitHub 构建和 PyPI 发布准备。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 初始化统一 Agent 配置 (Priority: P1)

作为首次使用 Agent21 的开发者，我希望在现有或空项目中运行初始化，自动发现常见 AI 编程工具，
选择要启用的 Agent，并创建一套可纳入版本控制的权威配置，从而不必逐个工具手工配置。

**Why this priority**: 没有安全、可重复的初始化，后续同步、诊断和团队共享都无法开始。

**Independent Test**: 在空项目、已有 `AGENTS.md` 的项目和含旧工具配置的项目中分别初始化，
验证权威配置与 manifest 正确生成，未托管内容未丢失，重复初始化结果一致。

**Acceptance Scenarios**:

1. **Given** 一个空项目和已检测到的 Agent，**When** 用户接受默认初始化，
   **Then** 系统创建权威配置目录、默认配置、Skills 目录和 manifest，并报告启用结果。
2. **Given** 一个已有 `AGENTS.md` 和 `.mcp.json` 的项目，**When** 用户初始化，
   **Then** 系统复用这些权威来源，不创建内容不同的第二真源。
3. **Given** 目标位置存在同名未托管工具配置，**When** 用户初始化，
   **Then** 系统保留原文件并停止冲突写入，明确说明冲突对象和后续操作。
4. **Given** 非交互环境，**When** 用户提供明确的 Agent 选择，
   **Then** 初始化无需输入提示即可确定性完成。

---

### User Story 2 - 将单一真源同步到多个 Agent (Priority: P1)

作为使用多种 AI 编程工具的团队成员，我希望运行一次同步就为所有已启用 Agent 生成或连接所需配置，
并且重复同步不会产生额外差异，从而让团队只维护 `AGENTS.md`、`.agents/skills/` 和 `.mcp.json`。

**Why this priority**: “一次配置，处处生效”是 Agent21 的核心用户价值。

**Independent Test**: 在启用 Claude Code、Codex、Cursor、OpenCode 和 Pi 的混合项目中同步两次，
验证声明的输出、链接或转换结果正确，第二次执行无额外变化，未启用 Agent 不产生输出。

**Acceptance Scenarios**:

1. **Given** 权威指令、Skills 和 MCP 配置均有效，**When** 用户同步，
   **Then** 每个已启用且已实现 Agent 只产生契约允许的托管输出。
2. **Given** 同一输入已同步完成，**When** 用户再次同步，
   **Then** 文件树和 manifest 保持等价，结果报告为无变化。
3. **Given** 某 Agent 已启用但本机未安装其 CLI，**When** 用户同步，
   **Then** 系统仍生成其配置产物（enabled 即生成，本机是否安装 CLI 不影响）。
4. **Given** 某 Agent 未启用，**When** 用户同步，**Then** 不生成其产物。
5. **Given** 目标路径已存在但未被 agent21 托管（用户自建或旧工具生成），**When** 用户同步，
   **Then** 系统接管并替换该目标（事务内备份旧内容后写入权威配置），并记入托管清单。
6. **Given** 目标路径越出项目边界，**When** 用户同步，
   **Then** 系统可控失败，不修改项目外内容。

---

### User Story 3 - 诊断配置健康与漂移 (Priority: P1)

作为维护者，我希望运行健康检查即可知道权威来源、生成物、Agent、Skills 和 MCP 的状态，
并获得可执行修复建议，从而快速定位团队成员环境不一致或手工修改造成的漂移。

**Why this priority**: 同步工具必须能证明当前状态可信，否则团队无法安全依赖自动生成物。

**Independent Test**: 对健康项目以及分别缺少权威文件、损坏配置、生成物漂移和依赖缺失的项目运行诊断，
验证每个问题被分类、定位并映射为正确退出状态。

**Acceptance Scenarios**:

1. **Given** 所有权威输入和托管输出一致，**When** 用户运行健康检查，
   **Then** 系统返回成功并按稳定顺序报告全部检查项。
2. **Given** 托管输出与权威输入不一致，**When** 用户运行健康检查，
   **Then** 系统报告漂移、受影响 Agent 和建议的同步操作，并返回阻塞状态。
3. **Given** 可选 Agent 未安装或路线图能力未实现，**When** 用户运行健康检查，
   **Then** 系统将其标记为提示或不支持，而不是伪装成已通过。
4. **Given** 配置或 MCP 文件包含凭证，**When** 诊断失败，
   **Then** 输出不得包含凭证值。

---

### User Story 4 - 管理项目级 Skills (Priority: P2)

作为团队维护者，我希望从本地目录或明确的 Git 来源安装 Skill、查看已安装列表并安全移除，
使所有支持统一 Skills 目录的 Agent 共享同一能力集合和来源记录。

**Why this priority**: Skills 是单一配置源的重要组成，但依赖初始化、manifest 和安全文件操作。

**Independent Test**: 安装一个有效本地 Skill，验证文件和 manifest；列出后移除；再用非法名称、
缺失 `SKILL.md`、目标冲突和越界路径验证失败不会破坏现有 Skills。

**Acceptance Scenarios**:

1. **Given** 包含有效 `SKILL.md` 的本地目录，**When** 用户安装，
   **Then** Skill 被复制到统一目录并记录名称、来源和可用元数据。
2. **Given** 一个明确的 Git URL，**When** 用户确认联网安装，
   **Then** 系统在临时位置获取并验证内容后安装，不把仓库元数据作为项目资产复制。
3. **Given** 已安装 Skills，**When** 用户列出，
   **Then** 系统按名称稳定排序展示来源与版本；空列表也成功返回。
4. **Given** 一个由 manifest 管理的 Skill，**When** 用户移除，
   **Then** 只删除该托管目录和对应记录，不影响其他或同名未托管资产。

---

### User Story 5 - 跨平台可靠使用 (Priority: P2)

作为在 Linux、macOS 或 Windows 上工作的开发者，我希望相同项目配置获得等价行为，
且链接能力不可用时系统按声明策略安全回退，从而不需要维护平台专用配置分支。

**Why this priority**: 跨平台一致性决定开源团队能否共享同一仓库配置。

**Independent Test**: 在三个目标平台上执行初始化、同步、诊断和本地 Skill 生命周期，
验证路径、换行、权限和链接差异不会改变单一真源或破坏用户文件。

**Acceptance Scenarios**:

1. **Given** 平台支持符号链接且同步模式允许，**When** 用户同步 Skills，
   **Then** 系统创建指向统一目录的项目内链接并在 manifest 中记录。
2. **Given** 平台或权限不允许符号链接，**When** 使用自动模式同步，
   **Then** 系统回退为受管复制并明确报告，不静默改变权威来源。
3. **Given** 路径包含空格或平台分隔符差异，**When** 执行核心命令，
   **Then** 所有写入仍限制在目标项目中且结果可由诊断验证。

### Edge Cases

- 当前目录不是 Git 仓库或不存在 `AGENTS.md`。
- `.agents/config.yaml`、manifest、`.mcp.json` 格式损坏、为空或包含未知字段。
- 同一项目同时存在权威文件、旧工具配置和已漂移的托管产物。
- 命令执行中途失败、进程被中断或目标磁盘不可写。
- 目标文件、目录或符号链接指向项目外。
- Agent 可执行文件存在但版本命令失败，或工具安装后不可运行。
- Skill 名称包含路径分隔符、父目录跳转、控制字符或与已有资产冲突。
- Git Skill 来源无法访问、仓库缺少 `SKILL.md` 或包含嵌套仓库元数据。
- MCP 配置包含多种 transport、环境变量引用、空服务器列表或敏感值。
- Windows 未启用符号链接权限，或文件名大小写与 POSIX 平台表现不同。
- 用户连续运行同一命令、并发运行两个同步命令或手工修改生成物。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须识别项目根，并将默认写入限制在该根目录内。
- **FR-002**: 系统必须支持交互式初始化和具有明确 Agent 选择的非交互初始化。
- **FR-003**: 初始化必须创建或复用 `.agents/config.yaml`、`.agents/manifest.yaml`、`.agents/skills/`、`AGENTS.md` 和可选 `.mcp.json`，且不得静默覆盖未托管内容。
- **FR-004**: 系统必须检测 Claude Code、Codex、Cursor、OpenCode 和 Pi 的可执行环境，并允许用户覆盖检测结果。
- **FR-005**: 配置必须记录 schema 版本、Agent 启用状态、同步模式、Skills 来源和 MCP 来源，并拒绝无效类型或越界路径。
- **FR-006**: manifest 必须区分托管产物、来源、内容摘要、同步模式和已安装 Skills，且写入顺序确定。
- **FR-007**: 同步必须以 `AGENTS.md`、`.agents/skills/` 和 `.mcp.json` 为单一真源，只处理已启用且已实现的 Agent。
- **FR-008**: 原生能力不得产生冗余副本；兼容映射和转换只能产生适配器契约声明的最小输出。
- **FR-009**: MVP 必须支持 Claude Code、Codex、Cursor、OpenCode 和 Pi 的已声明指令与 Skills 行为，并对其 MCP 能力明确标记为原生、映射、转换或不支持。
- **FR-010**: 同步必须支持 `auto`、`copy` 和 `symlink` 模式；自动模式在链接不可用时必须安全回退并报告。
- **FR-011**: 相同输入、配置、平台和版本的重复同步必须产生等价文件树和 manifest。
- **FR-012**: 写入型操作必须先验证全部目标，采用临时文件与原子替换，并在失败时清理临时状态。
- **FR-013**: 系统不得修改同名未托管文件；冲突必须阻止相关写入并提供明确诊断。
- **FR-014**: 健康检查必须验证权威来源、schema、托管输出摘要、链接目标、Agent 环境、Skills 和 MCP 状态。
- **FR-015**: 健康检查必须区分通过、提示、不支持和阻塞错误，并以是否存在阻塞错误决定退出状态。
- **FR-016**: Skill 管理必须支持本地目录与 Git URL 安装、稳定列表和安全移除；安装前必须验证名称、边界和 `SKILL.md`。
- **FR-017**: Git Skill 安装必须在临时位置进行，失败不得修改统一 Skills 目录或 manifest。
- **FR-018**: 日志、错误和诊断不得输出令牌、密钥或配置中的敏感值。
- **FR-019**: 默认操作必须保持本地优先，不上传项目内容、不修改全局配置，也不执行 Skill 中的代码。
- **FR-020**: 所有公共命令必须支持 `--help`，并遵守成功、操作失败和用法错误的稳定退出语义。
- **FR-021**: 系统必须在 Linux、macOS 和 Windows 上支持核心命令，并对平台能力差异提供可诊断行为。
- **FR-022**: 所有状态报告、列表和生成配置必须具有确定性顺序，避免环境相关时间戳进入内容契约。

### Configuration, Compatibility & Safety *(mandatory for Agent21 behavior changes)*

- **Authoritative Inputs**: `AGENTS.md`、`.agents/config.yaml`、`.agents/skills/` 和 `.mcp.json`；manifest 记录托管状态但不得覆盖这些输入的语义。
- **Managed Outputs**: `CLAUDE.md`、工具专用配置、项目内 Skills 链接或受管副本，以及 `.agents/manifest.yaml` 中对应记录。
- **Affected Agents**: MVP 为 Claude Code、Codex、Cursor、OpenCode、Pi；WorkBuddy 和 Qoder 属于后续路线图，不阻塞 MVP。
- **Platforms / Sync Modes**: Linux、macOS、Windows；`auto`、`copy`、`symlink`。不支持的组合必须明确失败或按契约回退。
- **Recovery & Drift**: 所有写入在执行前校验；托管内容以摘要检测漂移；重复同步无差异；失败不得留下不可识别状态。
- **Security Boundary**: 默认只写项目根；远程 Skill 获取必须显式；不执行 Skill 内容；所有日志与 manifest 对敏感值脱敏。

### Key Entities *(include if feature involves data)*

- **Project Configuration**: 记录 schema 版本、启用 Agent、同步模式以及权威 Skills/MCP 路径。
- **Managed Artifact**: 表示从权威来源派生的文件、目录或链接，包含 Agent、来源、目标、模式和内容摘要。
- **Manifest**: 聚合托管产物、已安装 Skills 和同步版本，用于漂移检测与安全删除。
- **Agent Capability**: 描述 Agent 的 instructions、Skills、MCP 分类和平台支持状态。
- **Skill Package**: 表示名称、来源、版本、安装目录、元数据和托管状态。
- **Health Check Result**: 表示检查项、严重程度、对象、消息和建议操作。
- **Sync Result**: 表示创建、更新、未变化、跳过、冲突和错误的确定性摘要。

### Scope Boundaries

**In Scope**:

- `init`、`sync`、`doctor`、`skill install/list/remove` 和全局 help/version。
- Claude Code、Codex、Cursor、OpenCode、Pi 的 MVP 指令、Skills 和声明的 MCP 映射。
- 本地配置、manifest、原子文件操作、漂移检测、跨平台 copy/symlink 回退。
- 本地与 Git URL Skill 安装，但不执行 Skill 内容。
- 可发布的 Python 包、自动化测试和三平台发布门禁。

**Out of Scope**:

- WorkBuddy/Qoder 高级适配、OpenCode 尚未稳定的 MCP 扩展和真实远程 Agent 控制。
- Skill 注册表、搜索、自动升级、依赖解析或执行 Skill 脚本。
- 全局用户配置迁移、远端配置托管、Web 管理界面和遥测收集。
- 自动合并相互冲突的用户文件；MVP 采用安全拒绝并提供诊断。
- 自动发布到 PyPI 之前绕过 GitHub 环境审批或技术门禁。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新用户可在 2 分钟内完成非交互初始化，并在 5 分钟内完成首次同步与健康检查。
- **SC-002**: 对相同输入连续运行同步 20 次，100% 的运行均不产生额外文件差异或重复 manifest 记录。
- **SC-003**: 对预置的未托管冲突、路径越界、只读目标和中断场景，100% 不发生用户内容丢失或项目外写入。
- **SC-004**: 健康检查能识别预置的 schema 损坏、缺失来源、生成物漂移、断链、Skill 和 MCP 错误，检出率达到 100%。
- **SC-005**: Claude Code、Codex、Cursor、OpenCode 和 Pi 的每项已实现能力均有通过的契约验证，未实现能力均被明确报告。
- **SC-006**: Linux、macOS 和 Windows 均通过初始化、同步、健康检查和本地 Skill 生命周期的发布门禁。
- **SC-007**: 所有公共命令的成功、操作失败和用法错误路径均有自动化验证，且错误输出不包含预置假凭证。
- **SC-008**: 至少 90% 的首次试用者能仅依赖 README 在 15 分钟内完成安装、初始化、同步和诊断。
- **SC-009**: 候选发布物可在三个目标平台的干净环境安装，并成功完成 help、version、初始化、同步和健康检查冒烟流程。

## Assumptions

- 项目使用 Git 版本控制，但核心命令在非 Git 目录中仍会给出明确诊断而非崩溃。
- MVP 使用当前项目目录作为作用域，不自动查找或修改父目录及用户全局配置。
- 远程 Skill 安装只接受 Git 可识别 URL；认证由用户现有 Git 环境处理，Agent21 不存储凭证。
- 未托管冲突的默认策略是安全拒绝，不自动备份、覆盖或合并；后续可独立设计交互式迁移。
- `.mcp.json` 采用常见的 `mcpServers` 对象作为权威结构；不识别的字段被保留在权威文件中，但目标转换只使用已声明字段。
- 自动同步模式优先使用项目内相对符号链接；能力或权限不足时回退到受管复制。
- PyPI 发布优先采用 GitHub OIDC Trusted Publishing，因此不要求把长期 PyPI API token 写入仓库。
