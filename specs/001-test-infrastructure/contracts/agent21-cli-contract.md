# Agent21 CLI Test Contract

本文件定义 MVP 测试基础设施必须保护的最低公共 CLI 契约；它不规定完整文案或业务实现。

## Command Surface

| Command | Minimum contract |
| --- | --- |
| `agent21 --help` | 成功退出并列出所有已实现公共命令 |
| `agent21 --version` | 成功退出并输出可解析的项目版本 |
| `agent21 init` | 在项目边界内创建声明的权威配置和 manifest；冲突不可静默丢失用户内容 |
| `agent21 sync` | 只处理已启用且已实现的适配器；重复执行产生等价状态 |
| `agent21 doctor` | 报告权威输入、托管产物、适配器、Skills 和 MCP 的健康或漂移状态 |
| `agent21 skill install` | 校验名称、来源和目标边界后安装，并更新 manifest |
| `agent21 skill list` | 无 Skill 时也成功，并以稳定顺序列出当前记录 |
| `agent21 skill remove` | 只删除 manifest 声明的托管 Skill，不删除同名未托管资产 |

`skill update`、全局 `upgrade` 和尚未交付的适配器命令不属于本次 MVP 强制门禁；
一旦被声明为公共能力，必须先更新本契约和测试矩阵。

## Exit Status Semantics

| Status | Meaning |
| --- | --- |
| `0` | 请求成功完成，或只报告非阻塞信息 |
| `1` | 参数已被接受，但操作因配置、冲突、权限、健康或外部依赖问题未完成 |
| `2` | 命令名、选项或参数形式无效 |

其他状态仅可用于无法由应用控制的进程级终止。改变以上语义属于公共契约变更。

## Output Rules

- 正常结果写入 stdout；失败原因和未完成操作写入 stderr。
- 失败信息必须包含失败对象、未完成的动作和可执行的下一步，不要求固定整句文案。
- 路径必须优先显示项目相对形式，不得输出令牌、密钥或 fixture 中的假凭证。
- 列表和诊断项必须具有确定性排序；时间戳和绝对临时路径不得进入稳定快照。
- `doctor` 存在阻塞性错误时必须非零退出；纯建议或未启用能力不得伪装成错误。

## Contract Change Policy

删除或重命名命令、改变主要参数或退出状态语义、重新解释权威来源或默认覆盖策略，
都必须更新规格、迁移说明和快照，并按项目语义化版本政策评估不兼容性。
