# Release Validation

本文档说明 Agent21 发布候选版本的验证路径、阻断规则和平台失败排查方式。

## Release Gate

Release Gate 由 `.github/workflows/release.yml` 执行，并只对精确的候选提交生效。
候选提交通常来自 `v*` tag，也可以由维护者手动触发 workflow dispatch。

强制检查：

- Linux、Windows、macOS 均运行 `uv run nox -s release`。
- 每个平台至少覆盖 Python 3.11 和 3.14。
- 发布包通过 `uv run nox -s package` 重新构建和验证。
- 任一矩阵任务、构建任务、取消任务或缺失任务都会阻断发布。
- PyPI 上传必须等待 `pypi` 受保护环境审批完成。

## Trusted Publishing

发布工作流使用 PyPI Trusted Publishing，不保存 API token 或密码。
`publish-pypi` job 只授予 `contents: read` 和 `id-token: write` 权限，并通过
`pypa/gh-action-pypi-publish` 交换 OIDC 身份。

维护者需要在 PyPI 项目中配置 GitHub Trusted Publisher，匹配：

- 仓库：Agent21 的 GitHub 仓库。
- Workflow：`.github/workflows/release.yml`。
- Environment：`pypi`。

## Local Candidate Check

发布前在本机运行：

```bash
uv sync --locked --group dev
uv run nox -s release
```

本地验证只能证明当前平台状态。真正发布前仍必须等待 GitHub Actions 的三平台矩阵通过。

## Platform Triage

平台失败必须先按失败类别定位，不要用宽泛跳过掩盖问题。

- 路径或分隔符：确认测试是否在比较前规范化临时根、盘符和路径分隔符。
- 符号链接：先查看能力探测结果；不支持时必须验证 `copy` 回退或可诊断失败。
- 权限：确认失败发生在隔离 fixture 内，且没有写出测试临时根。
- 安装：下载 `release-distributions`，在干净虚拟环境中安装 wheel 和 sdist 构建出的 wheel。
- CLI：复现 `agent21 --help`、`agent21 --version` 和 `agent21 doctor`，保留退出码与 stderr。
- 快照：发布 CI 不允许 `--snapshot-update`；任何漂移都需要单独评审基线 diff。

## Blocking Semantics

Release Gate 状态必须在以下情况保持 blocked：

- 任一平台 `release` session 失败、错误、取消或未运行。
- 包构建、元数据检查、干净安装或公开 CLI 冒烟失败。
- 主分支门禁结果缺失或不能追溯到候选提交。
- 发布环境未审批，或 PyPI Trusted Publishing 配置不匹配。

人工审批只允许进入上传步骤，不能覆盖技术门禁失败。
