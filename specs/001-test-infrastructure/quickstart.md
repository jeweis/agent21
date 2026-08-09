# Quickstart: Agent21 测试基础设施

本指南描述实现完成后的验证入口，用于证明测试基础设施满足规格。

## Prerequisites

- Git
- uv
- Python 3.11、3.12、3.13 或 3.14
- 不需要真实第三方 Agent、MCP 服务、远程 Skill 仓库或真实凭证

## 1. Prepare the Environment

```bash
uv sync --locked --group dev
```

Expected:

- 环境严格按 lockfile 同步。
- 测试和质量工具可用。
- 不修改用户全局 Python 环境。

## 2. Run the Contributor Gate

```bash
uv run nox -s pr
```

Expected:

- 格式、lint、类型、unit、adapter、contract、integration、safety 快速子集和覆盖率全部通过。
- 整体覆盖率不低于 80%，核心区域不低于 90%。
- 任一失败返回非零状态，并提供可本地复现的场景信息。

详细会话定义见 [validation-sessions.md](contracts/validation-sessions.md)。

## 3. Run Targeted Safety Validation

```bash
uv run pytest -m safety
```

Expected:

- 所有写入发生在隔离临时项目中。
- 路径越界、未托管文件、权限和敏感信息场景通过。
- 项目外哨兵和受保护文件保持不变。

## 4. Review Stable Output Changes

先运行只读比较：

```bash
uv run pytest -m snapshot
```

只有在产品契约有意变化时才更新：

```bash
uv run pytest -m snapshot --snapshot-update
git diff -- tests
uv run pytest -m snapshot
```

Expected:

- 未批准的输出漂移在第一次运行中失败并展示差异。
- 更新后必须能从 diff 看出具体契约变化。
- CI 从不自动更新快照。

## 5. Run the Current-Platform Full Gate

```bash
uv run nox -s main
```

Expected:

- PR Gate 全部检查再次通过。
- E2E、snapshot、safety 和当前平台 compatibility 通过。
- 不支持的链接能力按产品契约回退或可诊断失败，不以宽泛跳过伪装通过。

跨平台矩阵和阻断规则见 [ci-gates.md](contracts/ci-gates.md)。

## 6. Validate the Distribution

```bash
uv run nox -s package
```

Expected:

- sdist 和 wheel 构建成功且元数据有效。
- 干净环境可分别安装所需分发物。
- 安装后可以 import 包，并成功执行 help、version、init、sync、doctor 与 Skill 生命周期。

## 7. Validate a Release Candidate

```bash
uv run nox -s release
```

本地命令只验证当前平台。真正的 Release Gate 还必须由 CI 聚合 Linux、macOS、Windows
结果并完成受保护环境审批。任何失败或缺失结果都会阻断发布。

## 8. Verify CLI Contract Coverage

```bash
uv run pytest -m contract tests/contract
```

Expected:

- 已实现的 MVP 命令符合 [Agent21 CLI Test Contract](contracts/agent21-cli-contract.md)。
- 未实现的后续命令不计入 MVP 通过率，也不会被报告为已支持。

## Troubleshooting

- **Marker not found**: marker 拼写或注册错误；`--strict-markers` 必须保持启用。
- **Snapshot differs only by path**: 检查规范化器是否遗漏临时根、分隔符或链接目标。
- **Permission test skipped**: 查看能力探测原因；安全门禁不得因整个平台宽泛跳过。
- **Package smoke fails**: 在干净环境复现，确认 sdist、wheel、入口点和运行时依赖均完整。
- **Coverage misses subprocesses**: 按 coverage 官方方案启用 subprocess 数据收集，
  不得通过排除 E2E 相关生产代码绕过门槛。
