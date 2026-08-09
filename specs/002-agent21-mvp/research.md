# Research: Agent21 MVP

## 1. 单一真源与适配策略

**Decision**: `AGENTS.md`、`.agents/skills/` 和 `.mcp.json` 分别作为指令、Skills 和 MCP 权威源；
原生支持直接复用，只有客户端格式不同才转换。

**Rationale**: Codex、OpenCode 和 Pi 均支持 `AGENTS.md`；OpenCode 和 Pi 明确支持 `.agents/skills`。
Claude Code 使用 `CLAUDE.md`，因此只生成这一最小兼容文件。

**Alternatives considered**: 为每个工具维护原生文件会重新引入多个真源；以 `CLAUDE.md` 为主源会降低跨工具标准兼容性。

## 2. Codex 项目配置

**Decision**: Codex 指令和 Skills 直接复用；MCP 转换到可信项目中的 `.codex/config.toml`，
每个服务器使用 `[mcp_servers.<name>]` 表。

**Rationale**: 官方 OpenAI 文档确认项目级 `.codex/config.toml` 受支持，Codex 从项目根向工作目录加载
`AGENTS.md`。[Configuration Reference](https://developers.openai.com/codex/config-reference)、
[MCP](https://developers.openai.com/codex/mcp)、
[AGENTS.md](https://developers.openai.com/codex/guides/agents-md)。

**Alternatives considered**: 修改 `~/.codex/config.toml` 违反项目作用域；直接复制 JSON 无法形成合法 TOML。

## 3. 其他 Agent 能力边界

**Decision**:

- Claude Code: `AGENTS.md -> CLAUDE.md`；MCP 原生复用根 `.mcp.json`；Skills 兼容链接仅在契约明确时生成。
- Cursor: 根 `AGENTS.md` 直接复用；MCP 转换为 `.cursor/mcp.json`；不生成冗余 rules。
- OpenCode: 指令与 `.agents/skills` 直接复用；MVP 不生成 MCP 配置。
- Pi: 指令与 `.agents/skills` 直接复用；MCP 标记 unsupported，并提示可选扩展而不自动安装。

**Rationale**: 这些选择基于各产品官方文档的当前项目级路径，并优先减少托管输出。

**Alternatives considered**: 自动安装 Pi MCP 扩展或生成未经证实的 Claude Skills 路径会扩大供应链和兼容风险。

## 4. 模型与 schema 实现

**Decision**: 使用 dataclass 和显式字段校验实现配置/manifest 模型，YAML 只负责序列化；
JSON Schema 作为版本化契约和测试输入，不引入运行时 jsonschema 依赖。

**Rationale**: 运行时仅需简单、稳定的 schema v1；显式校验更容易给出领域错误并拒绝未知字段。

**Alternatives considered**: Pydantic 或 jsonschema 功能更全，但 MVP 字段少，引入运行时依赖不符合最小化原则。

## 5. 项目根与安全路径

**Decision**: 当前工作目录是唯一项目根；配置路径必须相对、禁止 `..`、盘符和控制字符；
对现有路径与最近存在父目录解析符号链接后再验证包含关系。

**Rationale**: 不向父级搜索可避免扩大写入范围，解析后校验能阻止 symlink 逃逸。

**Alternatives considered**: 自动发现 Git 根更方便但与 MVP 明确作用域冲突。

## 6. 无副作用 adapter

**Decision**: adapter protocol 只提供 `detect`、`capabilities`、`plan`、`doctor_checks`，
输出统一 `PlannedArtifact`；全部文件 I/O 由核心事务执行器完成。

**Rationale**: 统一执行器才能集中实施边界、未托管保护、锁、原子写入、回滚和 manifest 提交。

**Alternatives considered**: adapter 自行写入实现较快，但会复制安全逻辑并难以证明幂等。

## 7. 同步与事务

**Decision**: `sync` 使用 `plan -> validate -> lock -> stage -> apply -> manifest`；
transaction journal 保存目标前态，manifest 最后提交，异常按逆序恢复。

**Rationale**: 所有冲突在写入前发现；同目录临时文件和项目内临时目录支持原子 replace；journal 使部分失败可恢复。

**Alternatives considered**: 逐文件即时写入无法保证多输出一致性。

## 8. 并发锁

**Decision**: 通过 `O_CREAT | O_EXCL` 创建 `.agents/.lock`；存在锁时写入命令失败；
doctor 报告疑似 stale lock，但 MVP 不自动删除。

**Rationale**: 标准库足以防止两个写入进程同时开始，保守拒绝比误删活跃锁更安全。

**Alternatives considered**: 新增 filelock 依赖或自动破锁都会扩大实现与风险。

## 9. Skill 安装

**Decision**: 本地与 Git 来源都先复制/clone 到项目内 transaction 临时目录，验证安全 slug、
根级 `SKILL.md` 和链接边界，排除 `.git` 后原子移动；remove 只处理 manifest 中未漂移的托管 Skill。

**Rationale**: 失败不得改变 Skills 或 manifest，且 Agent21 不执行 Skill 内容、不保存 Git 凭证。

**Alternatives considered**: 直接复制 Git 工作区会携带仓库元数据并难以回滚。

## 10. MCP 转换与脱敏

**Decision**: 只解析 `.mcp.json` 的 `mcpServers` 对象；保留权威文件未知字段，但转换器仅处理
stdio `command/args/env` 和 HTTP `url/headers` 的已声明字段；日志只显示服务器名和字段名，不显示值。

**Rationale**: 最小字段集覆盖常见传输，避免把客户端私有选项误转；凭证仍由环境变量或权威文件管理。

**Alternatives considered**: 任意 JSON 到 TOML 的通用转换会生成客户端不支持的配置。

## 11. Doctor 输出

**Decision**: 检查结果使用 `pass/info/unsupported/blocked`，按稳定 `check_id` 排序；只有 blocked
导致退出 1，用法错误退出 2。输出断言结构和关键字段，不锁定完整自然语言。

**Rationale**: 稳定结构支持人类诊断与契约测试，同时允许后续改善文案。

**Alternatives considered**: 只输出自由文本难以测试；所有警告都非零会使可选环境缺失阻断日常工作。

## 12. 推迟能力

**Decision**: 推迟 WorkBuddy/Qoder、Skill registry/update、自动冲突迁移、自动破锁、真实 Agent 控制、
全局配置、Web UI、遥测和 OpenCode/Pi MCP 自动配置。

**Rationale**: 这些能力不属于 MVP 验收，且会扩大写入范围、网络依赖或兼容承诺。

**Alternatives considered**: 一次实现所有附件设想会降低交付质量并违反 YAGNI。
