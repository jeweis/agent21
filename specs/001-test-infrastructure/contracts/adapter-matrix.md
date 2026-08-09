# Agent Adapter Test Matrix

本矩阵是适配器测试的权威支持登记。MVP 的五个目标 Agent 已完成协议、实现与契约验证，
WorkBuddy 和 Qoder 仍为后续路线图。能力状态变化必须在同一变更中更新实现、契约和测试。

| Agent | Status | Instructions | Skills | MCP | MVP target | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code | implemented | compatible | compatible | native | yes | 生成 CLAUDE.md 与 Skills 映射；MCP 复用根配置 |
| Codex CLI | implemented | native | native | transform | yes | 指令与 Skills 直接复用，MCP 转换为项目级 TOML |
| Cursor | implemented | native | native | transform | yes | 指令与 Skills 直接复用，MCP 转换为 Cursor JSON |
| OpenCode | implemented | native | native | unsupported | yes | 指令和 Skills 原生复用，MVP 明确不支持 MCP |
| Pi | implemented | native | native | unsupported | yes | 指令和 Skills 原生复用，MVP 明确不支持 MCP |
| WorkBuddy | planned | compatible | unsupported | unsupported | no | 属于 P1 路线图，不阻塞 MVP |
| Qoder | planned | native | unsupported | unsupported | no | 属于 P1 路线图，不阻塞 MVP |

## Status Rules

- `planned`: 只有目标分类，不得被测试报告为已支持，不要求进入门禁通过率。
- `implemented`: 产品能力存在，至少一个契约用例必须通过；每项非 `unsupported` 能力
  还必须由语义校验器确认至少关联一个用例。
- `unsupported`: 明确不提供该 Agent；若以后改变，必须先更新产品规格和本矩阵。

JSON Schema 负责结构校验及 `implemented` 至少一个总体契约用例；“每项支持能力至少一个用例”
由适配器契约测试中的语义校验完成，因为它需要跨字段匹配用例覆盖范围。

## Promotion Checklist

将任一 Agent 从 `planned` 提升为 `implemented` 前必须同时完成：

1. 产品规格定义权威输入、托管输出、冲突行为和平台模式。
2. 契约实例通过 `adapter-contract.schema.json`。
3. instructions、skills、MCP 中每项支持能力至少有一个契约测试。
4. 原生能力证明未创建冗余第二真源；映射/转换能力具有稳定输出基线。
5. Linux、macOS、Windows 的适用模式在主分支兼容矩阵中有结果。
