# LangGraph 与工作流

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/11-agent-core/04-langgraph.md`](../../exercises/11-agent-core/04-langgraph.md)

## 本章定位

- **本章角色**：用「图」表达 Agent 工作流：节点、边、状态、条件分支、循环；并了解人机协同与 checkpoint。
- **说明**：API 会变；本章抓**思想**。练习可用伪图/自研微型图执行器代替真实库。

## 学习目标

1. 用节点/边/状态描述一个 Agent 流程。
2. 实现条件分支与循环终止。
3. 理解 checkpoint 对长任务/恢复的价值。
4. 知道人机协同节点用在何处。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 图/节点/边、状态、条件分支、循环 | 能建模 |
| **建议掌握** | 人机协同、checkpoint | 能设计 |
| **了解即可** | 与其他编排对比 | 地图 |

---

## 1. 为何用图而不是一层 for

线性 for 适合简单 ReAct。  
复杂时出现：

```text
检索失败 → 改写查询再检索
需要人工批准才能执行 shell
分支：客服 vs 技术路径
子流程：调研 → 写作 → 审阅
```

图让控制流显式、可可视化、可暂停恢复。

---

## 2. 必掌握：节点 / 边 / 状态

```text
State = {messages, step, status, ...}
Node = 状态 → 部分状态更新
Edge = 下一跳（固定或条件）
```

伪代码（**增量更新**直觉，贴近真实图库）：

```python
def llm_node(state):
    ...
    return {"messages": [assistant]}  # 增量，不是整表重写

def tool_node(state):
    ...
    return {"messages": tool_msgs}

def route(state):
    if has_tool_calls(state):
        return "tools"
    return "end"
```

真实 LangGraph 一类库用 **reducer**（如对 `messages` 做 append）合并节点返回值；  
你只返回「本步新增」，框架负责接到历史后面。

图：

```text
START → llm → (route) → tools → llm → ...
                      ↘ end
```

---

## 3. 必掌握：条件分支与循环

- **条件边**：根据 state 选下一节点  
- **循环**：tools → llm → tools；用 `step` / `max_steps` 防死循环  
- **汇合**：多分支可 merge 回公共节点（字段是替换还是 append，由 reducer / 合并策略决定）

---

## 4. 建议掌握：人机协同与 checkpoint

### Human-in-the-loop

在执行高风险工具前插入 `approve` 节点：暂停，等外部事件继续。

### Checkpoint

每步把 state 持久化：

- 进程崩溃可恢复
- 长时间等待人工
- 时间旅行调试（进阶）

存储：内存 / SQLite / Postgres 等。

---

## 5. 了解即可：其他编排

纯手写状态机、Temporal 工作流、规则引擎……  
LangGraph 一类把「LLM 工作流」产品化；思想仍是状态+转移。

---

## 6. 微型图执行器（学习用，非 LangGraph 语义）

下面是**玩具执行器**：演示节点跳转。  
`{**state, **update}` 是**浅覆盖**——与真实库的 reducer **不同**。若节点只返回 `{"messages": [new]}`，这里会**丢掉历史**。

```python
def merge_state(state: dict, update: dict, list_append_keys=frozenset({"messages"})) -> dict:
    out = {**state}
    for k, v in update.items():
        if k in list_append_keys and isinstance(v, list):
            out[k] = list(out.get(k) or []) + v  # 模拟 messages reducer
        else:
            out[k] = v
    return out


def run_graph(nodes, edges, router, state, start="llm", max_visits=20):
    cur = start
    for _ in range(max_visits):
        state = merge_state(state, nodes[cur](state))
        nxt = router(cur, state) if cur in router else edges[cur]
        if nxt == "end":
            return state
        cur = nxt
    raise RuntimeError("graph exceeded max visits")
```

学完对照真实库：哪些字段 append、哪些替换、checkpoint 存什么。

---

## 7. 练习指引

[`exercises/11-agent-core/04-langgraph.md`](../../exercises/11-agent-core/04-langgraph.md)

---

## 8. 小结与下一站

### 下一章

[`05-agent-memory.md`](./05-agent-memory.md) —— 短期/长期记忆。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Agent Framework 概览](./03-agent-frameworks.md)
- 下一章：[Agent Memory](./05-agent-memory.md)
