# Research: 扩展 Agent 支持

## 1. Agent 能力矩阵

**Decision**: 七个 Agent 的能力分类以 [adapter-matrix.md](contracts/adapter-matrix.md) 为权威契约。

**Rationale**: Constitution 要求 instructions、Skills、MCP 分别分类，不能用“Agent 已支持”掩盖子能力缺失。
OpenCode、Qoder、Pi 上游资料和用户确认的 WorkBuddy 路径已足以锁定项目级行为。

**Alternatives considered**: 延续 `unsupported` 会与工具现状和用户目标冲突；把所有能力标为 native 会掩盖
OpenCode 格式转换、Pi 第三方依赖以及 WorkBuddy/Qoder Skills 路径差异。

## 2. OpenCode MCP 输出

**Decision**: 将根 `.mcp.json` 转换为项目根 `opencode.json` 的顶层 `mcp` 对象。stdio 服务器转换为
`type: local`，将 `command` 与 `args` 合并为命令数组，将 `env` 改名为 `environment`；HTTP 服务器转换为
`type: remote` 并保留 `url`、`headers`。`disabled` 反转为 `enabled`；`cwd`、`timeout` 在目标支持时保留。

**Rationale**: OpenCode 官方配置只接受工具专用结构，且项目配置路径是 `opencode.json`。项目
`.agents/skills` 与 `AGENTS.md` 已被原生发现，不需要额外输出。

**Alternatives considered**: 直接复制 `.mcp.json` 不合法；写入全局配置违反项目边界；实现通用 JSON/JSONC
合并会扩大所有权和注释保真问题，因此既有未托管 `opencode.json` 继续按冲突策略拒绝覆盖。

**References**: [OpenCode Config](https://opencode.ai/docs/config/)、
[OpenCode MCP](https://opencode.ai/docs/mcp-servers/)、[OpenCode Skills](https://opencode.ai/docs/skills)

## 3. OpenCode 字段验证

**Decision**: 每个服务器必须恰好属于 local 或 remote。local 要求非空字符串 `command`，`args` 必须为字符串数组；
remote 要求非空 `url`。目标不支持、互斥冲突或类型错误字段在写入前产生含服务器名和字段名、不含值的错误。

**Rationale**: 静默丢字段会造成“同步成功但工具行为不同”，违反规格 FR-004；先验证全部服务器可保持事务原子性。

**Alternatives considered**: 透传所有字段会让 OpenCode 拒绝配置；忽略未知字段无法证明语义等价。

## 4. Pi MCP adapter

**Decision**: Pi 保持原生读取 `AGENTS.md` 和 `.agents/skills`；MCP 分类为 `compatible`，由用户显式安装的
`pi-mcp-adapter` 直接读取根 `.mcp.json`。Agent21 只检查 `pi-mcp-adapter` 可执行文件，不安装、不更新、不运行它。

**Rationale**: 上游包提供 `pi-mcp-adapter` bin，推荐安装命令为 `pi install npm:pi-mcp-adapter`，并将根
`.mcp.json` 作为首选项目配置。存在性检查无副作用，也不会读取用户凭证。

**Alternatives considered**: 自动调用 `pi install` 会执行第三方代码并修改全局环境；生成 `.pi/mcp.json` 会产生
第二真源；调用 adapter 或 MCP server 做在线探测会扩大 doctor 的副作用。

**References**: [pi-mcp-adapter](https://github.com/nicobailon/pi-mcp-adapter)、
[Pi README](https://github.com/earendil-works/pi/tree/main/packages/coding-agent)

## 5. WorkBuddy 项目配置

**Decision**: WorkBuddy 使用稳定 slug `workbuddy`。项目根没有 `CODEBUDDY.md` 时，WorkBuddy 原生加载
`AGENTS.md`；`.agents/skills` 按同步模式映射到 `.codebuddy/skills`；根 `.mcp.json` 原生复用。
Agent21 不读写用户级 `~/.codebuddy`。

**Rationale**: 官方规则文档明确 `AGENTS.md` 是 `CODEBUDDY.md` 不存在时的原生兼容入口；`.codebuddy/rules`
是带元数据和加载策略的附加规则体系，不是同步统一指令的必需目标。目录级 Skills 目标继续由现有冲突保护管理。

**Alternatives considered**: 将 `AGENTS.md` 复制到 `.codebuddy/rules` 会制造第二份指令且格式语义不等价；
生成 `CODEBUDDY.md` 也会覆盖原生 fallback；将产品 slug 改成 `codebuddy` 会混淆两个产品；写用户目录违反边界。

**References**: [WorkBuddy/CodeBuddy Rules](https://www.workbuddy.cn/docs/ide/User-guide/Rules)

## 6. Qoder 项目配置

**Decision**: Qoder 原生读取根 `AGENTS.md` 和 `.mcp.json`；`.agents/skills` 映射为
`.qoder/skills`。检测命令使用官方 CLI `qodercli`。

**Rationale**: Qoder 官方文档明确项目 Skills 为 `.qoder/skills/<name>/SKILL.md`，项目范围 MCP 为根
`.mcp.json`，CLI/Action 可加载根 `AGENTS.md`。

**Alternatives considered**: 把 Skills 或 MCP 保持 unsupported 已与当前官方能力不符；生成第二份 MCP 会破坏单一真源。

**References**: [Qoder Skills](https://docs.qoder.com/extensions/skills)、
[Qoder MCP](https://docs.qoder.com/cli/mcp-servers)、[Qoder Action](https://docs.qoder.com/en/cli/qoder-action)

## 7. WorkBuddy 环境检测

**Decision**: WorkBuddy 作为“configuration-only” Agent：没有可靠、跨平台的 CLI 可执行契约时，默认初始化不自动
检测启用；用户通过 `--agents workbuddy` 显式启用后，sync 仍生成项目配置。doctor 报告“安装状态不可由 CLI
确认”，而不是伪报 executable unavailable。

**Rationale**: WorkBuddy 是桌面产品，项目配置仍需提交供团队共享。把未证实的命令名写入 scanner 会导致所有
显式选择均被 sync 跳过。

**Alternatives considered**: 猜测 `workbuddy` 可执行文件不可验证；扫描平台应用目录复杂且不覆盖企业分发方式。

## 8. 配置 schema 向后兼容

**Decision**: 保持 `schema_version: 1`。`claude/codex/cursor/opencode/pi` 继续必填；`workbuddy/qoder` 为已知可选字段。
旧配置读取时补为 disabled；新初始化和下一次保存稳定写出七个 Agent。未知 Agent 仍拒绝。

**Rationale**: 这是兼容的加法扩展，不需要强迫所有 0.1.x 项目先迁移，也不弱化对旧必填字段和未知字段的严格校验。

**Alternatives considered**: schema v2 需要新增迁移命令；把所有缺失 Agent 默认为 disabled 会掩盖损坏的旧配置；
要求七个字段会使已发布版本创建的项目立即不可读。

## 9. 可选依赖诊断

**Decision**: 为 adapter capability 增加可选的依赖可执行文件和安装提示元数据。仅当对应 Agent、能力和非空 MCP
来源同时启用时，sync/doctor 才报告 Pi adapter 状态；缺失为 `unsupported`/`skipped`，检测到命令只证明
“可发现”而不声称版本兼容或运行加载成功，也不阻断 Pi 的指令和 Skills。

**Rationale**: 共享元数据可避免在 core 中硬编码 Pi 名称，并为后续可选兼容层复用。

**Alternatives considered**: 在 `sync.py`/`doctor.py` 写 Pi 特例会泄漏 adapter 私有约定；将依赖缺失设为全局 blocked
会错误阻断 Pi 的其他原生能力；运行 `pi` 或 adapter 探测版本/加载状态会执行第三方代码并扩大 doctor 副作用。

## 10. 测试与发布边界

**Decision**: 先更新契约 fixture/矩阵并增加失败测试；随后实现 adapter、迁移、诊断和同步。目标测试覆盖字段错误、
未托管冲突、重复同步、缺失依赖、旧配置、三平台路径和不泄露凭证；最终运行 `nox -s pr`、`nox -s main`、
`nox -s package`，远端 Main Gate 作为合并证据。

**Rationale**: 本功能改变公共兼容矩阵、schema 行为、生成物和外部依赖诊断，属于需要完整回归的大范围行为变更。

**Alternatives considered**: 只跑 adapter 单测无法覆盖事务、旧配置和跨平台路径；真实启动所有第三方 Agent 会让
默认测试依赖外部安装和在线服务。
