# Data Model: Agent21 测试基础设施

本功能不引入持久化数据库。以下实体是版本化测试资产、内存对象或可重建验证记录。

## 1. Project Fixture

表示一种可复制、不可原地修改的用户项目初始状态。

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `fixture_id` | string | yes | 稳定唯一标识，如 `mixed-project` |
| `category` | enum | yes | `empty`、`agents`、`legacy`、`mixed`、`broken` |
| `source_path` | relative path | yes | 仓库内只读 fixture 根目录 |
| `assets` | list | yes | 初始文件、目录、链接及内容摘要 |
| `permissions_profile` | enum | yes | `normal`、`readonly-file`、`readonly-dir`、`capability-probed` |
| `corruptions` | list | no | 无效 YAML/JSON、缺字段、非法路径等预置损坏 |
| `protected_paths` | list | yes | 执行后必须保持不变的未托管资产 |
| `expected_boundary` | relative path | yes | 所有允许写入的项目边界 |

**Validation rules**:

- `source_path` 必须位于 `tests/fixtures/projects/` 下且不得作为命令工作目录。
- 每次运行必须复制到独立临时根；并发运行不得共享可写状态。
- `protected_paths` 执行前后必须按字节和对象类型比较。
- 路径越界 fixture 必须同时创建项目外哨兵，以证明外部状态未改变。

## 2. Validation Case

描述一个可独立执行并可追溯到规格的测试场景。

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `case_id` | string | yes | 稳定测试标识 |
| `requirement_ids` | list | yes | 一个或多个 `FR-*` / `SC-*` |
| `layer` | enum | yes | `unit`、`adapter`、`contract`、`integration`、`e2e`、`compatibility` |
| `markers` | list | yes | 已注册 pytest markers |
| `fixture_id` | string | conditional | 文件工作流场景所用 fixture |
| `preconditions` | list | yes | 环境、能力与初始状态 |
| `action` | command/call | yes | 被验证的单一用户动作 |
| `assertions` | list | yes | 退出状态、输出和文件副作用 |
| `platforms` | list | yes | 适用平台或 `all` |
| `network_policy` | enum | yes | 默认 `forbidden`，显式测试可为 `stubbed` |

**Validation rules**:

- 每个用例必须至少映射一个需求并包含可判定断言。
- 平台差异必须由能力探测或明确产品契约触发，不能只依赖宽泛的 `xfail`。
- 安全用例失败不得重试后转为通过；快照用例不得在 CI 自动更新基线。

## 3. Adapter Contract

描述已实现或计划中的 Agent 兼容边界。结构由
[`contracts/adapter-contract.schema.json`](contracts/adapter-contract.schema.json) 约束。

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | yes | 契约格式版本 |
| `agent` | string | yes | Agent 稳定标识 |
| `status` | enum | yes | `implemented`、`planned`、`unsupported` |
| `capabilities` | object | yes | instructions、skills、MCP 的独立分类 |
| `source_inputs` | list | yes | 权威输入路径 |
| `managed_outputs` | list | yes | 允许生成或链接的产物 |
| `platform_modes` | object | yes | 平台与同步模式支持范围 |
| `contract_cases` | list | yes | 证明该契约的 Validation Case 标识 |

**Validation rules**:

- `implemented` 的每项支持能力至少关联一个契约用例。
- `native` 能力不得声明冗余复制输出；转换能力必须列出最小输出集合。
- `planned` 和 `unsupported` 不计入 MVP 通过率，但必须在报告中显式展示。

## 4. Stable Output Baseline

表示用户可见且确定性的已批准输出。

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `baseline_id` | string | yes | 与用例和输出类别关联的稳定标识 |
| `case_id` | string | yes | 产生该输出的 Validation Case |
| `format` | enum | yes | `text`、`json`、`yaml`、`file-tree` |
| `normalizers` | list | yes | 临时根、换行、分隔符、时间戳等规范化规则 |
| `content` | snapshot | yes | 版本库中的批准内容 |
| `status` | enum | yes | `proposed`、`approved`、`superseded` |
| `contract_version` | string | yes | 对应的公开契约版本 |

**State transitions**:

```text
proposed -> approved -> superseded
     |          |
     +-> rejected
```

只有本地显式更新并经过 diff 评审后，`proposed` 才能成为 `approved`。

## 5. Validation Run

记录一次本地或 CI 验证的可重建证据。

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `run_id` | string | yes | 运行唯一标识 |
| `trigger` | enum | yes | `local`、`pull-request`、`main`、`release` |
| `revision` | string | yes | 被验证的提交或候选版本 |
| `session` | string | yes | Nox 会话名 |
| `environment` | object | yes | OS、Python、同步模式和能力探测结果 |
| `case_results` | list | yes | 用例通过、失败、跳过及原因 |
| `coverage` | object | conditional | 整体和核心区域指标 |
| `artifacts` | list | no | 差异、报告、构建产物和日志引用 |
| `status` | enum | yes | `pending`、`running`、`passed`、`failed`、`error`、`cancelled` |

**State transitions**:

```text
pending -> running -> passed
                   -> failed
                   -> error
                   -> cancelled
```

`failed` 表示断言未满足，`error` 表示基础设施无法完成验证；二者都阻断对应门禁。

## 6. Release Gate

聚合候选发布版本的强制验证，不负责实际发布业务逻辑。

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `candidate` | string | yes | 候选版本或 tag |
| `required_runs` | list | yes | 必须通过的 Validation Run |
| `platform_status` | object | yes | Linux、macOS、Windows 状态 |
| `package_status` | object | yes | sdist、wheel、元数据与干净安装状态 |
| `security_status` | object | yes | 依赖审计和敏感信息检查状态 |
| `decision` | enum | yes | `pending`、`blocked`、`ready`、`approved` |
| `evidence` | list | yes | 可追踪报告和审批引用 |

**State transitions**:

```text
pending -> blocked
       -> ready -> approved
```

任一强制运行失败、错误或缺失时只能进入 `blocked`；环境审批不能覆盖失败门禁。

## Relationships

```text
Project Fixture 1 --- * Validation Case
Adapter Contract 1 --- * Validation Case
Validation Case 1 --- 0..* Stable Output Baseline
Validation Run 1 --- * Validation Case Result
Release Gate 1 --- * Validation Run
```
