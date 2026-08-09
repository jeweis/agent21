# Implementation Plan: Agent21 MVP

**Branch**: `未创建` | **Date**: 2026-08-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-agent21-mvp/spec.md`

## Summary

实现单包 Python CLI，将 `AGENTS.md`、`.agents/skills/` 和 `.mcp.json` 作为单一真源，
以无副作用 adapter 生成同步计划，再由统一的安全文件事务完成校验、锁定、原子写入、回滚和 manifest 提交。
MVP 覆盖初始化、同步、健康检查、Skill 本地/Git 安装与五个 Agent 的已声明能力；
测试复用 `001-test-infrastructure` 的 fixture、契约、幂等、安全、三平台和发布门禁。

## Technical Context

**Language/Version**: Python 3.11+；兼容 3.11、3.12、3.13、3.14

**Primary Dependencies**: Typer、PyYAML；标准库 `pathlib`、`json`、`hashlib`、`tempfile`、
`shutil`、`subprocess`、`os`；不新增运行时锁、schema 或网络 SDK

**Storage**: 仓库内 YAML/JSON/TOML/Markdown 文件、目录和符号链接；无数据库、无远端状态

**Testing**: pytest 单元/契约/集成/E2E/兼容/安全测试；Nox 门禁；整体分支覆盖率 80%，核心模块 90%

**Target Platform**: Linux、macOS、Windows；PyPI 安装；GitHub Actions 发布

**Project Type**: 单包 Python CLI，`src/` 布局

**Performance Goals**: 非交互初始化低于 2 分钟，首次同步与诊断总计低于 5 分钟；
20 次重复同步无额外差异；常见小项目单次同步目标低于 2 秒（不含 Git 下载）

**Constraints**: 当前工作目录即项目根；默认离线；不修改全局配置；不执行 Skill；
未托管冲突安全拒绝；全部目标预校验；写入持锁并可回滚；输出脱敏且稳定排序

**Scale/Scope**: 6 个公共命令面、5 个 MVP Agent、3 种同步模式、4 类能力状态、3 个操作系统

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate: PASS

- **Single source**: `AGENTS.md`、`.agents/config.yaml`、`.agents/skills/`、`.mcp.json`
  是权威输入；manifest 仅记录托管事实与摘要；adapter 输出不可独立编辑。
- **Adapter boundary**: adapter 只声明能力、检测环境并生成 `PlannedArtifact`，不得写文件。
  Claude/Codex/Cursor/OpenCode/Pi 分别记录 native、compatible、transform、unsupported 能力。
- **Safe synchronization**: `plan -> validate -> lock -> stage -> apply -> manifest` 两阶段流程；
  同目录临时文件与项目内 transaction journal；失败回滚，dangling transaction 由 doctor 阻断。
- **Compatibility contract**: 三平台、`auto/copy/symlink` 和五个 Agent 均有契约；
  链接能力运行时探测；Codex 项目 MCP 使用官方 `.codex/config.toml`。
- **Verification**: 所有写入型行为先写失败测试；复用 001 的安全、幂等、适配器、CLI、package 和 release 门禁。
- **Security boundary**: 所有路径解析后验证项目边界；远程 Skill 仅显式 Git URL；临时 clone；不保存认证信息；输出脱敏。
- **Simplicity**: 运行时仅 Typer 与 PyYAML；不建立插件框架、数据库、遥测、远程注册表或自动冲突合并。

### Post-Design Re-check: PASS

Phase 1 的 schema、数据模型和 CLI/adapter/transaction 契约均保持单一真源和统一写入边界。
五个 adapter 没有直接文件 I/O，Git Skill 与 MCP 转换不引入长期凭证或全局配置写入。
不存在需要豁免的宪章冲突。

## Project Structure

### Documentation (this feature)

```text
specs/002-agent21-mvp/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── config.schema.json
│   ├── manifest.schema.json
│   ├── cli-contract.md
│   ├── adapter-matrix.md
│   └── sync-transaction.md
└── tasks.md
```

### Source Code (repository root)

```text
src/agent21/
├── __init__.py
├── __main__.py
├── cli.py
├── models.py
├── errors.py
├── project.py
├── config.py
├── manifest.py
├── fs.py
├── lock.py
├── scanner.py
├── sync.py
├── doctor.py
├── skills.py
├── mcp.py
└── adapters/
    ├── __init__.py
    ├── protocol.py
    ├── claude.py
    ├── codex.py
    ├── cursor.py
    ├── opencode.py
    └── pi.py
tests/
├── unit/
├── adapters/
├── contract/
├── integration/
├── e2e/
└── compatibility/
```

**Structure Decision**: 核心按安全职责拆分，CLI 保持薄层。adapter 仅生成计划，统一 `fs.py`
处理文件事务，`sync.py` 负责编排，`doctor.py` 只读诊断。模块边界直接对应测试与 90% 核心覆盖率门禁。

## Complexity Tracking

无宪章例外。transaction journal 是满足多文件回滚与可恢复诊断的最小必要复杂度。
