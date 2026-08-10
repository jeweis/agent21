# Implementation Plan: CLI 命令重构与 Agent 管理

**Branch**: `004-cli-command-redesign` | **Date**: 2026-08-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-cli-command-redesign/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

重构 Agent21 命令行面：将「启用并同步」设为默认命令（`agent21` / `agent21 --agents codex,cursor`，
无参时 TTY 交互选择、非 TTY 引导 `--agents`），新增 `disable`（含 `--dry-run` 预览 + 事务化回收
托管产物）与 `status`（状态总览 + doctor 阻塞项），彻底移除 `init` 命令与 `--yes` 死参数，
Agent 名不再作为位置参数（裸名报 `No such command` 并引导 `--agents`），统一未初始化引导为
`run 'agent21' first`。

技术路线：`Typer(invoke_without_command=True)` + `ctx.invoked_subcommand is None` 实现
无子命令默认 enable（无需 argv 重写/命令名判断）；`--agents` 为显式逗号分隔参数，交互选择
编号解析抽为纯函数；sync 通用化 "retired 产物清理" 并扩展 `apply_transaction` 支持事务内
删除；`status` 复用 `detect_agents` + config + manifest + `diagnose_project`。

## Technical Context

**Language/Version**: Python 3.11+（沿用现有项目约束）

**Primary Dependencies**: typer（CLI，已用）、pyyaml（config/manifest，已用）；
开发：pytest、nox、ruff、mypy（已有门禁）

**Storage**: 文件系统——`.agents/config.yaml`（启用状态）、`.agents/manifest.yaml`
（托管产物记录）、`.agents/.tmp`（事务/备份区）

**Testing**: pytest 分层（unit/adapters/contract/integration/e2e/compatibility/safety/
snapshot）+ nox 会话（pr/main/release/package）

**Target Platform**: Linux、macOS、Windows；Python 3.11–3.14

**Project Type**: 项目级 CLI 工具

**Performance Goals**: 不适用吞吐指标；命令应在亚秒内完成校验与规划，无阻塞 IO 以外等待

**Constraints**: 单函数 ≤80 行、单文件 ≤1000 行；只删 manifest 标记的托管路径；未初始化
引导一致；Windows 路径/换行兼容（沿用既有修复）；CLI 命令面为版本化契约，变更需迁移说明

**Scale/Scope**: 7 个已注册 Agent、6 个顶层命令（默认命令 + enable/disable/status/sync/
doctor/skill）、现有约 190 项测试需保持绿色

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Single source**: 权威输入不变（`AGENTS.md`、`.agents/config.yaml`、`.agents/skills/`、
  `.mcp.json`）。本 feature 只重构命令面与产物生命周期：`disable` 删除的是 manifest 标记的
  托管派生产物，不引入新的可独立维护状态。
- **Adapter boundary**: 不修改任何 Agent 的指令/Skills/MCP 能力分类与产物内容；命令层
  重构 + 通用化 sync 回收，不新增 adapter transform。
- **Safe synchronization**: `enable`/默认命令幂等合并、不误关；`disable` 支持 `--dry-run`
  预览与事务化删除（备份到 `.agents/.tmp`、失败回滚）；只删 manifest 托管路径；漂移产物
  在删除前报告而非静默删。
- **Compatibility contract**: CLI 命令面变化（移除 `init`、`--yes`，新增 enable/disable/
  status，默认命令语义）属版本化契约，需更新 README 迁移说明；config/manifest schema
  与各 Agent 产物格式不变；三平台行为一致。
- **Verification**: 失败优先——先写交互编号解析（`parse_selection`）、`retired` 计算、
  disable dry-run、事务删除、未初始化引导测试，再实现；集成测试覆盖默认命令/enable/
  disable/status 端到端；最终 `agent21 doctor` 与门禁验证。
- **Security boundary**: 写入始终限于当前仓库；删除仅针对 manifest 明确标记的托管
  路径；`status`/`doctor` 只读；交互仅接受本地编号输入、不执行任何输入内容；错误与
  诊断不输出凭证；无隐式上传或代码执行。
- **Simplicity**: 最小设计——`invoke_without_command` + `--agents` 显式参数消除歧义、
  交互编号解析为纯函数、sync 回收通用化、status 复用现有诊断。无宪法例外，Complexity
  Tracking 留空。确认函数/文件行数与注释规范满足要求。

## Project Structure

### Documentation (this feature)

```text
specs/004-cli-command-redesign/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── cli-contract.md
│   └── retirement-contract.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

沿用现有单项目结构（Option 1）：

```text
src/agent21/
├── cli.py            # 命令面重构：默认命令(--agents/交互) + enable/disable/status
├── init.py           # 移除 assume_yes；保留 initialize_project 合并逻辑
├── sync.py           # 通用化 retired 产物回收；dry-run 暴露将删除项
├── fs.py             # apply_transaction 支持 retire 事务删除
├── skills.py         # 引导消息更新为 run 'agent21' first
└── status.py         # (可选) status 聚合；或并入 cli.py

tests/
├── unit/             # parse_selection、retired 计算、status 聚合
├── contract/         # CLI 命令面、--agents 解析、未初始化引导、裸名报错
├── integration/      # 默认命令/enable/disable/status 端到端、事务删除
├── e2e/              # 子进程真实 argv + 交互输入模拟
├── compatibility/    # 三平台命令流程
```

**Structure Decision**: 单项目结构，改动集中在 `cli.py`、`sync.py`、`fs.py`；
`status` 逻辑体积小则并入 `cli.py`，超限按职责拆分到 `status.py`。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无宪法例外，此表留空。
