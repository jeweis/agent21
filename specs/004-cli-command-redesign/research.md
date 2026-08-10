# Research: CLI 命令重构与 Agent 管理

> 目标：解决 spec 中的技术未知项，为 Phase 1 设计与 Phase 2 任务提供依据。
> 所有结论基于代码事实与实测验证，无遗留 NEEDS CLARIFICATION。

## R1: 默认命令与子命令的共存机制（`--agents` 显式参数）

### 问题
需要"无子命令时执行默认启用命令"（`agent21` / `agent21 --agents codex,cursor`），
同时 `agent21 sync` 等子命令正常分发，且 Agent 名**不再作为位置参数**解析（消除歧义）。

### 实测验证
- Typer 只要注册了子命令，未匹配子命令的 positional 参数不会落到 callback，而是报
  `Missing command`；裸 Agent 名 `agent21 codex` 报 `No such command`（exit 2）。
- `Typer(invoke_without_command=True)` 会在没有子命令被调用时执行 callback，但**有子命令
  时 callback 也会先执行**——需用 `ctx.invoked_subcommand is None` 判断是否为真正默认路径。

### 决策
采用 `Typer(invoke_without_command=True)` + callback 内 `ctx.invoked_subcommand is None`
判断，`--agents` 作为显式逗号分隔参数：

```python
app = typer.Typer(invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context, agents: Annotated[str | None, typer.Option("--agents")] = None):
    if ctx.invoked_subcommand is None:
        return _default_enable(agents)  # 无子命令 → 默认启用
    # 否则子命令（sync/disable/status/...）自行处理
```

实测行为：`agent21`/`agent21 --agents codex` 走默认 enable；`agent21 sync`、
`agent21 disable --agents codex --dry-run` 走子命令且 callback 跳过；`agent21 codex`
报 `No such command`。

### Rationale
- `ctx.invoked_subcommand` 是 Typer/click 原生机制，零自定义命令集合维护。
- Agent 名不再作为位置参数 → 无需 argv 重写、无需"命令名 vs Agent 名"判断、无需
  命令名-名字不相交契约测试（R4 移除）。
- `--agents` 与旧 `init --agents` 参数一致，用户熟悉。

### Alternatives considered
- argv 重写将裸 Agent 名改写为 enable：需要 agent 名集合判断与入口 wrapper，已否决。
- callback 收位置参数：实测不可行（Typer Group 报 Missing command）。

## R2: 交互式选择设计（无参 `agent21`）

### 决策
无参 `agent21` 按环境分三条路径：

| 环境 | 行为 |
|---|---|
| TTY + 全新项目 | 展示全部已注册 Agent，`[已安装]` 标记 PATH 可调起的；用户编号多选（留空=全部）→ 合并启用 → 同步 |
| TTY + 已初始化 | 同样交互，展示当前 `[已启用]`，选择**只增不减**；留空=保持现状 |
| 非 TTY | 不执行任何启用/写操作，报错引导 `--agents codex,cursor`（不挂起） |

- 交互实现用纯 `input()`（零新增依赖）：打印编号列表 → 读取逗号分隔编号 → 解析。
- 编号解析抽为**纯函数**（`parse_selection(text, names) -> tuple[str, ...]`），
  单元测试直接覆盖；I/O 只做薄封装。处理空输入（=全部或保持现状）、非法编号重输、
  重复去重、Ctrl+C 取消不写文件。
- `[已安装]` 标记规则：基于 `capability.executable`——存在命令名且 `shutil.which`
  命中 → `[已安装]`；executable 为 None（workbuddy）或无 CLI → 无标记但始终可选。
  一套规则，无 Agent 特判。

### Rationale
- 交互列出全部已注册 Agent（而非仅检测到的）→ 彻底规避检测漏检（GUI-only、PATH 外
  安装），检测只影响标记不影响可选性（SC-006）。
- 零依赖 `input()` 符合宪章 VI 最小依赖；纯函数解析保证可测。
- 只增不减 + 留空保持现状 → 无参命令永不意外禁用 Agent。
- 非 TTY 引导 `--agents`（而非自动全启用）→ 避免 CI/管道环境意外启用本机 Agent，
  显式指定才是权威路径；`sys.stdin.isatty()` 判断，非 TTY 报错退出码 1。

### Alternatives considered
- 只显示检测到的 Agent：漏检导致用户看不到可选目标，否决。
- 引入 questionary 复选框库：更友好但新增第三方依赖，且宪章要求评估外部依赖必要性，
  否决。
- 非 TTY 自动全启用：在 CI 上可能意外启用/同步，行为不可预期，用户已否决。

## R3: disable 产物回收的事务化设计

### 问题
`apply_transaction`（fs.py）目前只处理本次传入的 artifacts，**从不删除**旧产物。
Agent 被禁用后，其 `.codex/config.toml` 等托管文件会残留成孤儿。

### 代码事实
- sync_project 用 `validated` 重建 manifest；被禁用 Agent 的托管记录会从 manifest 移除，
  但文件不会被删除（fs.py 无删除路径）。
- 现有 `unavailable_agents`（enabled 但 executable 缺失）的产物被保留（sync.py:83-84）。

### 决策
将回收**通用化到 sync 层**（disable 与手动禁用共用）：

- `retired` = 旧 `manifest.managed_artifacts` 中，路径**不在本次 validated targets**
  且 `agent` **不属于 `unavailable_agents`** 的托管产物。
- `apply_transaction` 新增 `retire: Iterable[Path]`：事务内删除——备份到
  `.agents/.tmp/<txn>/backup`、journal 记录、失败回滚；提交后清理备份。
- `SyncResult` 新增 `retired` 字段；`sync --dry-run` 与 `disable --dry-run` 暴露该清单，
  保证预览与实际删除 100% 一致（SC-002）。

### Rationale
- 通用规则同时覆盖 `disable` 与"手动编辑 config 禁用后 sync"，单一机制、无重复逻辑。
- 只删 manifest 标记托管路径，用户自建文件天然不在 `managed_artifacts`，安全（SC-003）。
- 走与写入同一事务机制，可回滚，满足宪法 III。

### Alternatives considered
- disable 命令单独删除：绕过统一事务、与 sync 重复，否决。
- 只摘除 manifest 记录不删文件：产物残留，违背"disable 即回收"预期，否决。

## R4: 命令名与 Agent 名冲突处理（已移除）

### 变更
原设计"命令名与 Agent 名不相交 + 契约测试"**已移除**：Agent 名不再作为位置参数解析，
裸 Agent 名由 Typer 原生报 `No such command`，不存在运行时歧义。命令名与 Agent 名
即使撞名也不影响分发（`agent21 pi` 永远报未知命令，`pi` 只有作为子命令才生效）。
因此无需命令集合维护或不相交测试。

## R5: status 状态聚合

### 决策
新增只读 `status`：读 `.agents/config.yaml`（启用）、`detect_agents()`（PATH 可用性）、
`.agents/manifest.yaml`（托管产物），并复用 `diagnose_project()` 提取全部 `blocked`
结果及其 `action` 追加展示。未初始化时不崩溃，显示接入指引。
可用性列按 `capability.executable`：有命令 → PATH 检测；`None`（workbuddy）→ 显示
"无需 CLI"（同一规则，无特判）。

## R6: 死参数 `--yes` 清理影响面

### 代码事实
- cli.py 定义 `--yes`/`-y` Option 并传入 `initialize_project`；init.py 中 `del assume_yes`
  直接丢弃（完全无效果）。
- 使用点：cli.py、init.py、约 20 处测试调用 `initialize_project(..., assume_yes=True)`、
  README/docs/specs 文档、sync.py 与 skills.py 的引导消息 `run 'agent21 init --yes' first`。

### 决策
- `initialize_project` 签名删除 `assume_yes`；CLI 删除 `--yes`/`-y`。
- 所有测试调用移除该参数；引导消息统一改为 `run 'agent21' first`。
- README/docs/specs 同步清理。

## R7: 未初始化引导一致性

### 现状
- `sync` 已改为 `project not initialized: ...; run 'agent21 init --yes' first`（上轮修复）。
- `skill` 三命令已用 `_load_initialized_manifest` 包装引导（上轮修复）。
- `doctor` 未初始化时报告 blocked + `run agent21 init`。

### 决策
将全部引导统一为 `run 'agent21' first`（默认命令已是接入入口）。`doctor` 的 action
文本同步更新。

## 技术风险与缓解

| 风险 | 缓解 |
|---|---|
| 交互 I/O 与 CliRunner 测试路径 | 编号解析抽纯函数单测；集成用显式 `--agents`；e2e 用子进程 + 输入模拟 |
| 事务删除误删用户文件 | 只删 manifest 托管路径 + dry-run 预览 + 回滚 |
| Windows 删除/路径差异 | 沿用既有 PurePath/posix 归一化；三平台兼容测试 |
| disable 漂移产物删除 | 删除前走 drift 检查，报告而非静默删 |
| 交互在非 TTY 挂起 | `sys.stdin.isatty()` 判断，非 TTY 报错引导 `--agents`（退出码 1），不挂起 |
