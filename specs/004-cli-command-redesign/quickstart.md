# Quickstart: CLI 命令重构与 Agent 管理

> 可运行验证场景，证明默认命令、enable/disable、status、回收与引导端到端工作。
> 详细契约见 [cli-contract.md](./contracts/cli-contract.md) 与
> [retirement-contract.md](./contracts/retirement-contract.md)。

## Prerequisites

- Python 3.11+，uv；开发环境 `uv sync --locked --group dev`
- 本机安装若干 Agent executable（codex、opencode 等）以触发自动检测；缺失时验证 skipped
- 隔离临时项目目录运行

## Scenario 1: 一条命令用起来（新项目）

```bash
cd $(mktemp -d)
agent21 --agents codex,opencode      # 非交互：只启用 codex 与 opencode
```

Expected:

- 自动创建 `AGENTS.md`、`.agents/config.yaml`、`.agents/manifest.yaml`、`.agents/skills`
- 只启用 codex 与 opencode，各自托管产物生成（如 `.codex/config.toml`、`opencode.json`）
- 再次运行 `agent21 --agents codex,opencode` 幂等：无额外 created，全部 unchanged

## Scenario 2: 交互式选择（TTY、无参）

```bash
cd $(mktemp -d)
agent21
```

Expected:

- 弹出全部已注册 Agent 列表，检测到 CLI 的标记 `[已安装]`
- 输入 `2,3` 后仅启用所选 Agent 并生成产物；留空则全部启用
- 非交互终端（管道/CI）运行 `agent21`：不写任何文件，报错引导使用
  `agent21 --agents codex,opencode`

## Scenario 3: 指定 Agent 追加（已初始化项目）

```bash
# 前提：项目已启用 opencode
agent21 --agents codex        # 追加 codex，opencode 保持启用
```

Expected:

- codex 被启用且 opencode 仍保持启用，互不误关
- 输出 `enabled: codex, opencode`
- 已初始化 + TTY 无参：交互列表标注 `[已启用]`，留空=保持现状不动

## Scenario 4: disable 预览与回收

```bash
# 前提：项目已启用 codex 且 .codex/config.toml 已生成
agent21 disable --agents codex --dry-run
agent21 disable --agents codex
```

Expected:

- `--dry-run`：输出 `would retire: .codex/config.toml`，不写盘、不改 config、
  文件仍存在
- 执行：config 中 codex 置 false，`.codex/config.toml` 被删除，其他 Agent 产物与
  用户自建文件保持不变
- 重复 `disable --agents codex`：提示 `not enabled: codex`

## Scenario 5: 未托管文件保护与漂移

```bash
# 用户手工创建的未托管文件不得被回收
echo manual > custom.md
agent21 disable --agents codex
test -f custom.md   # 仍存在
```

Expected:

- 回收只删除 manifest 标记的托管路径，`custom.md` 不受影响
- 若 codex 产物被手工改过，`doctor` 报告 drift 并给出 `run agent21 sync`

## Scenario 6: status 总览

```bash
agent21 status
```

Expected:

- 每行一个已注册 Agent：`<name>\t<enabled|disabled>\t<available|missing|none-required>\t<managed targets>`
- 存在配置/漂移问题时，尾部追加 `blocked: ...; action: ...`（复用 doctor 输出）
- 命令只读，不改动任何文件

## Scenario 7: 未初始化引导、裸名报错与死参数清理

```bash
cd $(mktemp -d)
agent21 sync            # 报错 + 引导
agent21 skill list      # 报错 + 引导
agent21 codex           # 报 No such command，引导用 --agents
agent21 --help          # 不再出现 --yes / -y / init
```

Expected:

- `sync`/`skill` 未初始化报错 `project not initialized: ...; run 'agent21' first`，退出码 1
- `agent21 codex` 报 `No such command 'codex'` 并提示 `--agents`
- `--help` 输出不含 `--yes`、`-y`、`init`

## Validation Matrix

| 场景 | 平台 | 验证方式 |
|---|---|---|
| 默认命令 / enable 幂等 | Linux/macOS/Windows | nox pr + main；compatibility 测试 |
| 交互选择解析与标记 | 三平台 | unit（parse_selection 纯函数）+ e2e（子进程输入模拟） |
| disable dry-run 一致性 | 三平台 | 集成测试对比 dry-run 与执行删除集合 |
| 事务删除与回滚 | 三平台 | integration + safety 测试 |
| status 只读 | 三平台 | 集成测试 |
| 未初始化引导 / 裸名报错 | 三平台 | contract + e2e 测试 |
