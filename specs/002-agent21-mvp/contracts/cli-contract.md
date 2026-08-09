# Agent21 MVP CLI Contract

## Commands

| Command | Contract |
| --- | --- |
| `agent21 --help` | 列出 init、sync、doctor、skill 与全局选项 |
| `agent21 --version` | 只输出安装版本并成功退出 |
| `agent21 init` | 初始化当前目录；支持 `--agents`、`--mode`、`--yes` |
| `agent21 sync` | 预校验并同步全部已启用 Agent；支持 `--dry-run` |
| `agent21 doctor` | 只读健康检查；稳定排序；blocked 时退出 1 |
| `agent21 skill install SOURCE` | 安装本地目录或明确 Git URL |
| `agent21 skill list` | 稳定排序；空列表成功 |
| `agent21 skill remove NAME` | 只删除未漂移的托管 Skill |

## Exit Semantics

- `0`: 成功完成，或 doctor 仅含 pass/info/unsupported。
- `1`: 参数形式有效，但操作因配置、冲突、锁、权限、漂移或外部依赖未完成。
- `2`: 命令、选项或参数形式无效。

## Output

- 成功摘要写 stdout；阻塞诊断写 stderr。
- 路径优先显示项目相对形式。
- 结果按 Agent、path、check_id 或 Skill 名称排序。
- 错误必须包含对象、未完成动作和下一步；不得包含 token、key、secret 的值。
- `--dry-run` 输出计划但不得创建锁、临时文件、manifest 或任何适配器产物。
