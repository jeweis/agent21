# Validation Report: 扩展 Agent 支持

**Date**: 2026-08-09  
**Platform**: macOS, Python 3.14.3  
**Result**: PASS

## Story Evidence

| Story | Evidence | Result |
| --- | --- | --- |
| OpenCode MCP | 本地/远程字段转换、精确 JSON 基线、空源、冲突安全、20 次幂等 | PASS |
| Pi MCP adapter | `pi-mcp-adapter` 可检测/缺失诊断、不执行/不安装、无全局或重复输出 | PASS |
| WorkBuddy | `.codebuddy/rules/agent21.md`、`.codebuddy/skills`、根 MCP 原生复用、configuration-only 同步、20 次幂等 | PASS |
| Qoder | `qodercli` 检测、根指令/MCP 原生复用、`.qoder/skills`、缺失可执行文件时 manifest 保留、20 次幂等 | PASS |

隔离故事命令共运行 15 个目标用例，全部通过。真实第三方 Agent 未被自动安装或执行；Pi 运行态按设计仅报告“可检测但未确认加载”。

## Quality Gates

- `uv run nox -s pr`: PASS；ruff format/check、mypy、165 项快速测试。
- `uv run nox -s main`: PASS；179 项全量测试，总覆盖率 89.48%，核心覆盖率 91%。
- `uv run nox -s package`: PASS；构建 `agent21-0.1.1` wheel/sdist，twine strict、干净安装、CLI 与 Skill 生命周期冒烟均通过。
- `git diff --check`: PASS。
- 源码规模：最大文件 416 行；所有函数不超过 80 行。
- 敏感信息扫描：未发现真实 token/API key；仅有既有脱敏测试夹具。

## Platform Scope

本机执行 macOS 门禁；Linux/Windows 行为由 compatibility 测试与 GitHub Actions 矩阵覆盖。未在本机启动 OpenCode、Pi、WorkBuddy 或 Qoder 本体，因此不声称确认第三方工具运行态或版本兼容性。
