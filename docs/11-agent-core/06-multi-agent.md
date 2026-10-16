# Multi-Agent

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/11-agent-core/06-multi-agent.md`](../../exercises/11-agent-core/06-multi-agent.md)

## 本章定位

- **本章角色**：理解多 Agent 分工模式（路由/流水线/辩论）；明确何时不该上多 Agent。
- **原则**：多 Agent 是组织结构，不是性能魔法；复杂度上升很快。

## 学习目标

1. 描述三种常见协作模式并举例。
2. 设计简单路由器。
3. 能判断「单 Agent + 多工具」是否足够。
4. 了解共享状态与消息协议直觉。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 分工模式、路由/辩论/流水线、何时不用 | 能决策 |
| **建议掌握** | 共享状态与消息协议 | 能设计 |
| **了解即可** | 大规模系统 | 扫盲 |

---

## 1. 为什么要多 Agent

当一个「全能提示」变得：

- 过长、互相冲突
- 工具权限需要隔离
- 角色专业性差异大（研究 vs 写作 vs 审查）

可拆成多个带不同提示/工具集的 Agent，由编排器协作。

---

## 2. 必掌握：协作模式

### 路由（Router）

```text
用户请求 → 路由 Agent/规则 → 专家 Agent
```

适合：意图分类清晰的客服/助手。

### 流水线（Pipeline）

```text
调研 → 大纲 → 写作 → 校对
```

适合：阶段产物明确。

### 辩论 / 评审（Debate / Critic）

```text
提案 Agent ↔ 批评 Agent → 合成
```

适合：需要挑剔检查；成本更高。

---

## 3. 必掌握：何时不该多 Agent

- 任务可用单 Agent + 2～3 工具解决
- 团队还不会做评测与追踪
- 只是为了「架构好看」
- 延迟/费用敏感且收益不清

反模式：五个 Agent 互相转发，没有终止与责任人。

---

## 4. 建议掌握：共享状态、协议与终止

共享：

- 黑板（共享 state dict）
- 消息总线（彼此发 message）

协议字段建议：

```text
from, to, type, payload, trace_id, step, idempotency_key
```

每个 Agent 的工具权限**单独配置**（安全章强化）：  
**Critic / 评审 Agent 默认只读**——检查与建议，不自动获得 `shell` / 写库 / 发信。

### 编排器级护栏

```text
max_handoffs：跨 Agent 转发次数上限（防互相踢皮球）
责任人：最终对用户输出的 Agent 必须唯一明确
超时：整次协作总墙钟预算
费用：累计 tokens / 步数触顶则降级单 Agent 直答
```

```python
def orchestrate(user_text: str, *, max_handoffs: int = 3) -> str:
    handoffs = 0
    agent_name = "router"
    while handoffs <= max_handoffs:
        agent = AGENTS[agent_name]
        result = agent.run(user_text)  # 返回 {reply, next?, done}
        if result.get("done"):
            return result["reply"]  # 责任人产出
        next_name = result.get("next")
        if not next_name or next_name == agent_name:
            return result.get("reply") or "stopped"
        agent_name = next_name
        handoffs += 1
    return "协作步数超限，已停止"
```

错误归属：路由分错 → 记在 router；专家工具失败 → 记在该专家 + 编排器是否降级。评测集可加「路由错误」case。

---

## 5. 了解即可：大规模

上百 Agent 的组织、市场拍卖式任务分配等——研究向；业务上先把 2～3 个专家协作做稳。

---

## 6. 最小路由伪代码

```python
def route(intent: str) -> str:
    if intent == "billing":
        return "billing_agent"
    if intent == "tech":
        return "tech_agent"
    return "general_agent"


def handle(user_text: str) -> str:
    intent = classify(user_text)  # LLM 或规则
    agent = AGENTS[route(intent)]
    return agent.run(user_text)
```

---

## 7. 练习指引

[`exercises/11-agent-core/06-multi-agent.md`](../../exercises/11-agent-core/06-multi-agent.md)

---

## 8. 小结与下一站

### 自检

- [ ] 能说明 Critic 为何默认不给写工具
- [ ] 能设计 `max_handoffs` 与唯一责任人
- [ ] 能判断何时单 Agent 足够

### 模块 11 收官

你已覆盖：Tool → 手写 Agent → 框架认知 → 图编排 → Memory → Multi-Agent。

下一模块：[`../12-agent-production/README.md`](../12-agent-production/README.md) —— 评测、可观测、安全、系统设计。

也可推进 Project 5/6（Tool Agent / Research Agent）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Agent Memory](./05-agent-memory.md)
- 下一模块：[Agent 工程化与生产落地](../12-agent-production/README.md)
