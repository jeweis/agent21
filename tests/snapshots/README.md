# Snapshot Baseline Policy

本目录只保存已经评审通过的稳定输出基线。基线文件名必须使用
`<case-id>__<format>__v<contract-version>.snap`，例如
`cursor-mcp__json__v1_0.snap`。

更新规则：

- 先运行 `uv run pytest -m snapshot` 查看未批准差异。
- 只有产品契约有意变化时，才在本地运行
  `uv run pytest -m snapshot --snapshot-update`。
- 更新后必须审查 `tests/snapshots/` 和相关 adapter fixture 的 diff。
- CI 中禁止使用 `--snapshot-update`，不得自动接受新基线。

