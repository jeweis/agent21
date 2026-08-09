# Feature Specification: 扩展 Agent 支持

**Feature Branch**: `未创建（仓库未配置 before_specify 分支钩子）`

**Created**: 2026-08-09

**Status**: Draft

**Input**: User description: "Pi 集成 pi-mcp-adapter；OpenCode 增加 MCP；新增 WorkBuddy 和 Qoder。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 统一 OpenCode MCP 配置 (Priority: P1)

作为同时使用 OpenCode 和其他编码 Agent 的开发者，我希望 OpenCode 能使用项目统一维护的 MCP
配置，从而不必再单独复制或维护一份服务器清单。

**Why this priority**: OpenCode 已是当前支持的核心 Agent，但缺少 MCP 适配会直接破坏“一套配置，
多工具生效”的产品承诺。

**Independent Test**: 在只启用 OpenCode 的隔离项目中提供本地和远程 MCP 服务器，执行预览、
同步和健康检查，验证 OpenCode 能使用等价配置，重复同步无额外差异，且未托管设置保持不变。

**Acceptance Scenarios**:

1. **Given** 项目包含有效的本地与远程 MCP 声明且已启用 OpenCode，**When** 用户执行同步，
   **Then** OpenCode 获得语义等价的项目级 MCP 配置，服务器名称、启动参数、环境引用、地址和请求头保持一致。
2. **Given** OpenCode MCP 配置已同步且权威来源未变化，**When** 用户再次同步，
   **Then** 系统报告结果未变化，不产生重复服务器或额外文件差异。
3. **Given** OpenCode 已存在未由 Agent21 管理的配置，**When** 同步需要写入相同目标，
   **Then** 系统不得覆盖或丢弃用户设置，并提供明确的冲突说明和可执行下一步。

---

### User Story 2 - 让 Pi 使用统一 MCP 配置 (Priority: P1)

作为 Pi 用户，我希望通过明确选择的 `pi-mcp-adapter` 使用项目统一 MCP 配置，从而获得与其他
Agent 一致的 MCP 工具，而无需维护 Pi 专用服务器清单。

**Why this priority**: Pi 核心不内置 MCP；若不提供受控的扩展集成，当前统一 MCP 来源无法在 Pi 中生效。

**Independent Test**: 在只启用 Pi 的隔离项目中分别模拟 adapter 可检测、缺失和无法离线确认运行状态，
验证可检测时 Pi 直接消费统一配置，缺失或不可确认时系统不静默安装或执行第三方代码并给出明确诊断。

**Acceptance Scenarios**:

1. **Given** 用户已明确启用 Pi MCP 集成且兼容的 adapter 可用，**When** 用户同步并启动 Pi，
   **Then** Pi 可使用权威 MCP 来源声明的服务器，无需维护第二份服务器配置。
2. **Given** adapter 尚未安装或不可用，**When** 用户同步或运行健康检查，
   **Then** 系统明确报告依赖状态、未完成的能力和修复步骤，不声称 MCP 已生效。
3. **Given** 用户未明确授权获取或启用第三方扩展，**When** 执行初始化、同步或诊断，
   **Then** 系统不得安装、更新或执行该扩展，也不得修改用户全局 Pi 配置。
4. **Given** adapter 或 Pi 扩展加载失败，**When** 用户再次同步，
   **Then** Agent21 管理的其他 Agent 配置保持可恢复且不出现半写状态。

---

### User Story 3 - 在团队项目中启用 WorkBuddy (Priority: P2)

作为使用 WorkBuddy 的团队成员，我希望能在 Agent21 项目配置中选择并诊断 WorkBuddy，
使它复用团队的权威指令和它实际支持的项目能力。

**Why this priority**: WorkBuddy 已出现在最初产品范围中，但当前无法被选择、检测或同步，导致部分团队成员
仍需手工维护配置。

**Independent Test**: 在只启用 WorkBuddy 的隔离项目中执行初始化、预览、同步和健康检查，验证项目规则和
Skills 正确进入 `.codebuddy/` 体系、根 `.mcp.json` 被原生复用，且重复同步保持一致。

**Acceptance Scenarios**:

1. **Given** WorkBuddy 已安装，**When** 用户初始化并选择 WorkBuddy，
   **Then** 项目配置记录该选择，系统报告检测结果和可用能力。
2. **Given** 项目存在权威指令和 Skills，**When** 用户为 WorkBuddy 执行同步，
   **Then** WorkBuddy 可从项目 `.codebuddy/rules/` 和 `.codebuddy/skills/` 使用对应内容，且团队仍只编辑
   Agent21 权威来源。
3. **Given** 项目根存在有效 `.mcp.json`，**When** 用户为 WorkBuddy 执行同步和健康检查，
   **Then** WorkBuddy 原生复用该文件，Agent21 不生成第二份服务器配置。
4. **Given** `.codebuddy/rules/` 或 `.codebuddy/skills/` 中存在同名未托管内容，**When** 用户同步，
   **Then** 系统保留用户内容并明确报告冲突，不覆盖、合并或删除该内容。

---

### User Story 4 - 在团队项目中启用 Qoder (Priority: P2)

作为使用 Qoder 的团队成员，我希望能在 Agent21 项目配置中选择并诊断 Qoder，使它复用团队的
权威指令和它实际支持的项目能力。

**Why this priority**: Qoder 同样属于最初产品范围，补齐后 Agent21 才能覆盖原始方案列出的全部 Agent。

**Independent Test**: 在只启用 Qoder 的隔离项目中执行初始化、预览、同步和健康检查，验证能力分类、
配置结果、冲突保护和重复同步符合统一适配器契约。

**Acceptance Scenarios**:

1. **Given** Qoder 已安装，**When** 用户初始化并选择 Qoder，
   **Then** 项目配置记录该选择，系统报告检测结果和可用能力。
2. **Given** 项目存在权威指令和 Skills，**When** 用户为 Qoder 执行同步，
   **Then** Qoder 可使用其已声明支持的内容，且不产生无必要的冗余副本。
3. **Given** Qoder 不支持某类权威能力，**When** 用户同步或诊断，
   **Then** 系统明确报告不支持状态，不生成未经验证的配置或伪装成功。

### Edge Cases

- 权威 MCP 来源缺失、为空、格式损坏，或仅包含目标 Agent 不支持的服务器选项。
- 同一服务器同时包含启动命令、远程地址、环境引用、请求头、认证信息或未知字段。
- OpenCode、Pi、WorkBuddy 或 Qoder 被启用但本机未安装，或可执行文件无法运行。
- Pi adapter 缺失、可执行文件可检测但运行态无法离线确认，或只能从用户全局环境找到。
- 用户已有未托管的 Agent 专用配置，其中包含与权威来源同名或不同名的设置，包括
  `.codebuddy/rules/` 或 `.codebuddy/skills/` 中的内容。
- 多个新增 Agent 同时启用，其中一个发生冲突或依赖失败。
- `copy`、`symlink` 或 `auto` 模式在 Windows、macOS 和 Linux 上能力不同。
- MCP 配置包含凭证、环境变量占位或认证头时发生解析、转换或诊断错误。
- 用户从旧版配置升级，已有配置尚未包含 WorkBuddy 或 Qoder 字段。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须将 WorkBuddy 和 Qoder 纳入可检测、可选择、可配置和可诊断的 Agent 清单。
- **FR-002**: 系统必须为 OpenCode、Pi、WorkBuddy 和 Qoder 分别声明指令、Skills 和 MCP 能力属于
  原生、兼容映射、转换或不支持，不得以 Agent 整体状态替代单项能力状态。
- **FR-003**: 系统必须让 OpenCode 使用权威 MCP 来源中的已支持服务器配置，并保持用户可观察语义等价。
- **FR-004**: OpenCode MCP 支持必须覆盖项目当前已声明的本地服务器与远程服务器场景；目标不支持的字段
  必须产生明确诊断，不得静默丢弃。
- **FR-005**: 系统必须通过用户指定的 `pi-mcp-adapter` 集成为 Pi 提供权威 MCP 来源中的已支持服务器。
- **FR-006**: Pi MCP 集成必须区分 adapter 可检测、缺失和运行态无法离线确认，并提供不含敏感值的状态说明；
  系统不得在未运行 adapter 的情况下声称已确认版本兼容、启用状态或成功加载。
- **FR-007**: 系统不得在没有用户明确授权时安装、更新或执行 `pi-mcp-adapter`，也不得为完成项目级同步
  静默修改用户全局 Pi 配置。
- **FR-008**: WorkBuddy 必须支持初始化选择、环境检测、同步计划和健康检查；项目规则和 Skills 必须分别
  映射到 `.codebuddy/rules/` 和 `.codebuddy/skills/`，项目 MCP 必须原生复用根 `.mcp.json`。
- **FR-009**: Qoder 必须支持初始化选择、环境检测、同步计划、健康检查和稳定能力报告；能原生读取的权威
  来源必须直接复用，只有经验证的不兼容能力才能产生最小工具专用输出。
- **FR-010**: 系统必须保留旧项目对 Claude Code、Codex、Cursor、OpenCode 和 Pi 的启用状态与行为，
  并为新增 Agent 配置提供确定性的升级路径。
- **FR-011**: 系统必须在写入前验证所有新增或变更的目标；任一未托管冲突不得导致用户文件被覆盖、合并或删除。
- **FR-012**: 同一权威输入、Agent 选择、平台和版本下重复同步必须产生等价结果，不得制造重复配置或 manifest 条目。
- **FR-013**: 当多个 Agent 同步且某一 Agent 无法安全完成时，系统必须准确报告已完成、跳过和阻塞项，
  并保证失败目标不处于半写状态。
- **FR-014**: 健康检查必须验证新增 Agent 的环境、权威来源、托管输出、漂移、依赖状态和能力边界。
- **FR-015**: 所有用户可见输出、诊断和 manifest 必须避免记录 MCP 密钥、令牌、认证头值及第三方扩展凭证。
- **FR-016**: 每项新增的非“不支持”能力必须具有独立验收证据；不支持能力必须被明确报告且不影响其他
  已支持能力正常使用。
- **FR-017**: 用户必须能够在执行写入前预览 OpenCode、Pi、WorkBuddy 和 Qoder 将创建、更新、保持不变、
  跳过或阻塞的结果。
- **FR-018**: 公共帮助和用户文档必须反映七个 Agent 的真实支持范围，并明确区分“目标工具不具备该能力”
  与“Agent21 尚未实现该能力”。

### Configuration, Compatibility & Safety *(mandatory for Agent21 behavior changes)*

- **Authoritative Inputs**: `AGENTS.md`、`.agents/config.yaml`、`.agents/skills/` 和 `.mcp.json` 继续作为
  唯一权威来源；第三方 Pi adapter 只负责消费该来源，不成为新的服务器配置真源。
- **Managed Outputs**: 仅包含各 Agent 经验证所必需的项目级配置、链接或副本，以及 manifest 中可追踪的
  所有权与摘要记录；WorkBuddy 输出限定在项目 `.codebuddy/rules/` 和 `.codebuddy/skills/`，不得为其原生
  MCP 能力生成重复来源。
- **Affected Agents**: OpenCode 的 MCP 从不支持提升为转换或原生复用；Pi 的 MCP 从不支持提升为显式第三方
  兼容集成；WorkBuddy 以 `.codebuddy/` 项目资源体系和根 `.mcp.json` 注册为正式 Agent；Qoder 从未注册
  提升为正式 Agent，并逐项登记其指令、Skills 与 MCP 能力。
- **Platforms / Sync Modes**: Linux、macOS、Windows；`auto`、`copy`、`symlink`。不适用的输出模式必须明确
  报告或按既有安全策略回退。
- **Recovery & Drift**: 同步必须保持确定性、幂等、写前校验、事务恢复、manifest 漂移检测和未托管文件保护；
  新增 Agent 不得绕过现有冲突与回滚语义。
- **Security Boundary**: 默认仅写当前项目；不得上传项目内容、泄露凭证、执行 Skill 内容或静默安装第三方代码；
  任何 Pi adapter 获取或启用必须由用户显式触发并可审计。

### Key Entities *(include if feature involves data)*

- **Agent Capability Profile**: 表示一个 Agent 的标识、检测状态，以及指令、Skills、MCP 三类能力的独立分类。
- **MCP Mapping**: 表示一个权威服务器声明与特定 Agent 可消费配置之间的语义对应、支持状态和诊断结果。
- **External Adapter Dependency**: 表示 Pi MCP 所依赖扩展的来源、可用性、兼容状态和用户授权状态，不包含凭证值。
- **Managed Artifact**: 表示由权威来源派生的 Agent 专用文件、目录或链接及其所有权、摘要和同步状态。
- **Health Check Result**: 表示某个 Agent、能力、依赖或产物的通过、提示、不支持或阻塞状态及修复动作。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 在代表性的隔离项目中，OpenCode 和已启用 Pi adapter 的 Pi 均能使用权威来源声明的全部受支持
  MCP 服务器，验收场景通过率达到 100%。
- **SC-002**: WorkBuddy 和 Qoder 均可在 2 分钟内完成非交互选择、首次同步和健康检查，且支持能力报告准确率
  达到 100%。
- **SC-003**: 对每个新增 Agent 连续同步 20 次，相同输入下 100% 不产生额外文件差异、重复服务器或重复
  manifest 记录。
- **SC-004**: 对预置的未托管冲突、无效 MCP、缺失 adapter、运行态不可确认和中断写入场景，100% 不发生用户
  内容丢失、项目外写入或明文凭证输出。
- **SC-005**: OpenCode、Pi、WorkBuddy 和 Qoder 的每项已声明能力均有可重复的通过证据；未支持能力均被明确
  报告，误报成功率为 0%。
- **SC-006**: Linux、macOS 和 Windows 的目标验证均通过新增 Agent 的初始化、同步、重复同步、诊断及适用的
  恢复场景。
- **SC-007**: 至少 90% 的首次使用者能只依赖公共帮助和 README，在 15 分钟内正确启用任一新增 Agent，
  并能判断 MCP 或其他能力是否实际生效。

## Assumptions

- OpenCode 当前提供项目级本地与远程 MCP 配置能力；具体兼容字段和最低版本在计划阶段以官方资料锁定。
- Pi 核心不内置 MCP，本功能使用用户指定的 `pi-mcp-adapter` 作为显式第三方兼容层，而不将其描述为 Pi 原生能力。
- WorkBuddy 与 CodeBuddy 是不同产品，但 WorkBuddy 的项目资源复用 `.codebuddy/` 配置体系：项目 Skills 位于
  `.codebuddy/skills/`，项目规则位于 `.codebuddy/rules/`，项目 MCP 位于根 `.mcp.json`；用户级
  `~/.codebuddy/` 不属于 Agent21 默认写入范围。
- Qoder 的每类能力以计划阶段验证到的官方项目级行为为准；没有可靠依据的能力默认明确标记为不支持，
  不通过猜测生成配置。
- 新增 Agent 沿用现有 `.agents/config.yaml`、manifest、预览、事务和诊断模型，不新增第二套配置体系。
- 远程下载第三方依赖、修改用户全局配置、自动执行 OAuth 登录及管理 MCP 服务生命周期不属于本功能的默认行为。
- WorkBuddy 和 Qoder 之外的新增 Agent、Skill registry/update、Web UI 和远程配置托管不属于本功能范围。
