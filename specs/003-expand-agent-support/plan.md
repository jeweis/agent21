# Implementation Plan: 扩展 Agent 支持

**Branch**: `未创建（仓库未配置 before_plan 分支钩子）` | **Date**: 2026-08-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-expand-agent-support/spec.md`

## Summary

在现有 Python CLI 和无副作用 adapter 架构内，将 OpenCode MCP 从 `unsupported` 提升为确定性转换，
将 Pi MCP 提升为依赖 `pi-mcp-adapter` 的显式兼容能力，并把 WorkBuddy、Qoder 注册为正式 Agent。
保持 `AGENTS.md`、`.agents/skills/`、`.mcp.json` 单一真源；WorkBuddy 只生成
`.codebuddy/rules/agent21.md` 与 `.codebuddy/skills`，Qoder 只生成 `.qoder/skills`，两者 MCP
均原生复用根 `.mcp.json`。配置 schema v1 采用向后兼容的加法扩展，旧五 Agent 配置加载时将新增 Agent
默认为禁用。

## Technical Context

**Language/Version**: Python 3.11–3.14

**Primary Dependencies**: Python 标准库、PyYAML、Typer；`pi-mcp-adapter` 是用户显式安装的可选外部依赖，
不成为 Agent21 运行时 Python 依赖

**Storage**: 项目内 YAML/JSON/TOML/Markdown 文件、目录、符号链接和 `.agents/manifest.yaml`

**Testing**: pytest、syrupy、jsonschema、mypy、ruff、nox；适配器契约、单元、集成、安全、快照、兼容性和 e2e

**Target Platform**: Linux、macOS、Windows；WorkBuddy 本体的平台可用性独立于项目配置生成

**Project Type**: 单包 Python CLI

**Performance Goals**: 七个 Agent 的典型项目同步在交互等待范围内完成；相同输入连续 20 次同步无额外差异

**Constraints**: 只写项目根；不自动安装或执行第三方扩展；不覆盖未托管内容；日志不得输出 MCP 凭证；
单文件不超过 1000 行、函数不超过 80 行；新增/实质变更文件和方法含有意义注释

**Scale/Scope**: 7 个 Agent、3 类能力、3 个同步模式、3 个操作系统；本次新增 3 个托管目标和 1 个外部依赖诊断

## Constitution Check

*GATE: Phase 0 前检查，并在 Phase 1 设计后复核。*

### Pre-Research Gate — PASS

- **Single source — PASS**: 权威输入仍为 `AGENTS.md`、`.agents/config.yaml`、`.agents/skills/`、
  `.mcp.json`。新增输出为 `opencode.json`、`.codebuddy/rules/agent21.md`、`.codebuddy/skills`、
  `.qoder/skills`；Pi adapter 直接消费 `.mcp.json`，不产生第二真源。
- **Adapter boundary — PASS**: OpenCode MCP=`transform`；Pi MCP=`compatible`；WorkBuddy instructions/Skills=
  `compatible`、MCP=`native`；Qoder instructions/MCP=`native`、Skills=`compatible`。转换仅处理官方确认的不兼容格式。
- **Safe synchronization — PASS**: 所有输出进入既有 plan→prevalidate→transaction→manifest 流程；重复同步、
  未托管冲突、漂移和回滚均由现有核心统一处理。
- **Compatibility contract — PASS**: schema v1 只做可选字段扩展；旧五 Agent 仍为必填，新 Agent 缺失时默认禁用；
  新配置稳定写出七个 Agent。Linux/macOS/Windows 与 auto/copy/symlink 均有契约。
- **Verification — PASS**: 每项行为先添加失败的 adapter/contract/unit/integration 测试，再实现；最终运行
  PR/Main/Package 相关门禁和 quickstart。
- **Security boundary — PASS**: 不写 `~/.codebuddy`、`~/.pi` 或其他全局目录；不执行 adapter；只通过可执行文件
  存在性检查依赖；诊断不包含服务器值或凭证。
- **Simplicity — PASS**: 复用 adapter protocol、文件事务和 manifest；不引入新依赖、插件管理器或通用配置合并器。

### Post-Design Gate — PASS

- `research.md` 已锁定七个 Agent 的路径、能力分类、迁移和失败语义，没有未解决澄清。
- `data-model.md` 仅为现有模型增加向后兼容 Agent 集合与可选依赖元数据，没有新持久化子系统。
- `contracts/` 明确精确输出、MCP 字段映射、schema 兼容和 doctor 行为；所有 transform/compatible 输出均要求快照。
- `quickstart.md` 覆盖四个故事、重复同步、冲突、缺失 adapter、跨平台和回归验证。
- 未发现宪章例外；Complexity Tracking 保持为空。

## Project Structure

### Documentation (this feature)

```text
specs/003-expand-agent-support/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── adapter-matrix.md
│   ├── cli-contract.md
│   ├── config.schema.json
│   └── mcp-mapping.md
└── tasks.md
```

### Source Code (repository root)

```text
src/agent21/
├── adapters/
│   ├── __init__.py
│   ├── opencode.py
│   ├── pi.py
│   ├── qoder.py
│   ├── workbuddy.py
│   └── protocol.py
├── config.py
├── doctor.py
├── mcp.py
├── models.py
├── scanner.py
└── sync.py

tests/
├── adapters/
├── contract/
├── integration/
├── unit/
├── compatibility/
├── safety/
├── snapshot/
└── fixtures/adapter_contracts/
```

**Structure Decision**: 保持现有单包 CLI。每个工具差异只进入独立 adapter；共享配置解析、依赖检测、
安全写入、manifest 与诊断留在核心模块。新增测试沿用现有测试分层，不创建第二套 harness。

## Complexity Tracking

无宪章例外。
