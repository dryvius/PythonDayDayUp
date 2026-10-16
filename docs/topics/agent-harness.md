# 专题：Agent Harness 总览

> 非主线模块。把「评测环」与「运行时外壳」画在一张图上，避免名词打架。

## 两种 Harness（别混）

| 名称 | 含义 | 本仓库落点 |
|------|------|------------|
| **Eval harness** | 题集 → 跑 Agent → 断言 → baseline | [`12/01` §4](../12-agent-production/01-evaluation.md) + [`playground/.../evaluation/`](../../playground/12-agent-production/evaluation/) |
| **Runtime harness** | tool-loop + ACL + 超时 + trace +（可选）沙箱 | 模块 11 手写 Agent + 12 安全/观测 |

业界口语里的 “agent harness” 常指后者；本课评测章说的 harness 默认是 **Eval**。

## Runtime 外壳一张图

```text
                    ┌─ API 认证 / 配额
请求 ──────────────►│
                    ├─ Runtime Harness
                    │    ├─ messages / session
                    │    ├─ LLM complete(messages, tools) → assistant
                    │    ├─ authorize(role, tool, args)
                    │    ├─ 执行工具（限流 / 截断 / 幂等）
                    │    ├─ max_steps / 总超时
                    │    └─ trace_id + spans（允许列表）
                    └─ 响应 / Job 状态
                           │
Eval harness ──────────────┴──► cases.jsonl 回归
```

## 最小可跑路径

1. 跑通 Eval：`python playground/12-agent-production/evaluation/run_eval.py --write-baseline`  
2. 手写 Agent 的 `trace` 事件类型与 `check_trace` 对齐  
3. 接上 `authorize`（[`03-security`](../12-agent-production/03-security.md)）后再谈沙箱  

## 导航

- 专题首页：[README.md](./README.md)
- Eval：[../12-agent-production/01-evaluation.md](../12-agent-production/01-evaluation.md)
- Tool / Agent：[../11-agent-core/01-tool-calling.md](../11-agent-core/01-tool-calling.md) · [../11-agent-core/02-handwritten-agent.md](../11-agent-core/02-handwritten-agent.md)
