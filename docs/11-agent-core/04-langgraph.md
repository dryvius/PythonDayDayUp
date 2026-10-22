# LangGraph 与工作流

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/11-agent-core/04-langgraph.md`](../../exercises/11-agent-core/04-langgraph.md)

## 本章定位

- **模块目标**：理解 Agent 本质，能手写并使用框架构建 Agent。
- **本章角色**：用「图」表达 Agent 工作流：节点、边、状态、条件分支、循环；并了解人机协同与 checkpoint。
- **说明**：API 会变；本章抓**思想**。练习可用伪图/自研微型图执行器代替真实库。
- **前置**：手写 tool-loop（[`02-handwritten-agent.md`](./02-handwritten-agent.md)）、框架何时上（[`03-agent-frameworks.md`](./03-agent-frameworks.md)）。
- **约定提醒**（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）：本章玩具执行器必须讲清 **reducer / append** 语义；**勿与真实 LangGraph API 一一对应**。

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

上一章手写 Agent 的核心是：

```text
for step in range(max_steps):
    调 LLM → 有 tool_calls 就执行 → 写回 messages → 再调 LLM
```

这层 `for` **足够**覆盖大量「LLM ↔ Tools」场景。图不是为了炫技，而是当控制流**不再是一条直线**时，把「下一步去哪」从隐式 `if` 堆里抽成显式结构。

### 1.1 线性 for 何时开始疼

#### 为什么一层 for 会不够？

复杂产品里常见这些形状（不是「再多写几个 if」那么简单）：

```text
检索失败 → 改写查询再检索（局部重试子环）
需要人工批准才能执行 shell（中途暂停、等外部事件）
分支：客服路径 vs 技术路径（不同节点序列）
子流程：调研 → 写作 → 审阅（可复用子图）
某步失败 → 补偿 / 降级路径（不是直接 return 错误字符串）
```

在一层 `for` 里硬塞，会出现：

| 症状 | 后果 |
|------|------|
| `status` / `phase` 枚举爆炸 | 读代码要脑内模拟状态机 |
| 暂停/恢复靠全局变量或外挂 | 崩溃后难以接着跑 |
| 分支用深层 `if/elif` | 可视化、评审、单测都难 |
| 子流程想复用 | 只能复制粘贴一段 loop |

图的价值：

> **把控制流显式化**：节点是「做什么」，边是「下一步」，状态是「携带什么」；可可视化、可暂停恢复、可插入人机节点。

#### 怎么写（先用文字建模，不碰库）

同一需求，先画图再写代码：

```text
START
  → retrieve
      → (ok?) ──yes──→ write
      │                → review → END
      └──no──→ rewrite_query → retrieve（受 max_retries 约束）
```

对照「一层 for」心智：

```text
for 里：下一步藏在一堆 if 里
图里：下一步是边（固定边或条件边）
```

#### 跑一下（用伪代码对比两种表达）

```python
# 线性 for：控制流埋在分支里
def run_linear(state: dict) -> dict:
    while state["step"] < state["max_steps"]:
        state["step"] += 1
        if state["phase"] == "retrieve":
            state = retrieve(state)
            state["phase"] = "write" if state["docs"] else "rewrite"
        elif state["phase"] == "rewrite":
            state = rewrite_query(state)
            state["phase"] = "retrieve"
        elif state["phase"] == "write":
            state = write(state)
            state["phase"] = "review"
        elif state["phase"] == "review":
            state = review(state)
            break
    return state


# 图：节点只负责「改状态」，路由负责「下一跳」
# （完整玩具执行器见第 6 节；此处只建立形状直觉）
NODES = {
    "retrieve": retrieve,
    "rewrite": rewrite_query,
    "write": write,
    "review": review,
}

def route(node: str, state: dict) -> str:
    if node == "retrieve":
        return "write" if state.get("docs") else "rewrite"
    if node == "rewrite":
        return "retrieve"
    if node == "write":
        return "review"
    return "end"
```

两种都能跑；差别在**可读性与扩展点**：加人机批准、checkpoint、子图复用时，图的边界更清晰。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 一上来就装 LangGraph | 被 API 绑住，没学会「状态 + 转移」 |
| 凡 Agent 都上图 | 简单 tool-loop 被过度设计，调试更慢 |
| 把图当成「自动变聪明」 | 图只编排；智能仍来自模型与工具设计 |
| 用图逃避终止条件 | 循环边没有 `max_steps` / `max_visits` 一样会死 |

#### 对照：手写 loop vs 图

| 维度 | 一层 for / 状态机 | 图编排 |
|------|-------------------|--------|
| 典型形状 | LLM ↔ Tools | 分支、子环、人机、多阶段流水线 |
| 下一步在哪 | `if` / `phase` | 边 / router |
| 暂停恢复 | 自己序列化整个 Agent | checkpoint 是一等公民（思想层面） |
| 学习路径 | 先掌握（第 2 章） | 控制流变复杂后再上（本章） |

可以先记一句：

> **能用清晰的 tool-loop 解决的，先不要上图；需要显式分支、暂停、恢复时，再把 loop 升格为图。**

---

## 2. 必掌握：节点 / 边 / 状态

图编排只有三个零件。把它们钉死，后面条件边、人机、checkpoint 都是在这三者上长出来的。

### 2.1 总览：三件套

```text
State = {messages, step, status, ...}   # 图上流动的数据
Node  = 状态 → 部分状态更新             # 一步计算 / 一次副作用边界
Edge  = 下一跳（固定或条件）            # 控制流
```

心智图（经典 tool-loop 升格为图）：

```text
START → llm → (route) → tools → llm → ...
                      ↘ end
```

### 2.2 状态（State）：图上唯一的「真相」

#### 为什么状态要显式？

手写 Agent 里 `self.messages` / `self.step` 散落在对象字段上；图把它们收成**一份可传递、可持久化的 state**。  
checkpoint、时间旅行、多人机会话，都依赖「任意一步之后的 state 能被完整保存」。

#### 怎么写（最小字段）

练习与教学至少包含：

```python
state = {
    "messages": [],          # 对话与工具轨迹（列表，通常 append）
    "step": 0,               # 已执行步数 / 访问计数相关
    "status": "running",     # running | waiting | done | failed | max_steps
}
```

常见扩展字段（按需，勿一次塞满）：

| 字段 | 用途 | 合并直觉 |
|------|------|----------|
| `messages` | LLM / tool 轨迹 | **append**（reducer） |
| `step` / `visits` | 防死循环 | **替换**（取新值） |
| `status` | 生命周期 | **替换** |
| `docs` / `draft` | 业务中间产物 | 多为替换；列表也可 append |
| `pending_tool` | 等人批准的工具调用 | 替换；批准后清空 |
| `trace` | 评测/排障事件 | 常 append |

关键原则：

1. **节点只返回「本步更新」**，不是每次拷贝整张世界状态再改完交回（可读性与合并策略都更差）。
2. **合并策略按字段约定**：列表字段常 append；标量常替换。这就是 reducer 思想（见 2.4 与第 6 节）。

#### 跑一下

```python
# 初始
state = {"messages": [{"role": "user", "content": "1+2?"}], "step": 0, "status": "running"}

# 某节点返回「增量」
update = {
    "messages": [{"role": "assistant", "content": None, "tool_calls": [...]}],
    "step": 1,
}

# 合并后（messages append，step 替换）——语义示意，非库 API
state = {
    "messages": state["messages"] + update["messages"],
    "step": update["step"],
    "status": state["status"],
}
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| state 里塞不可序列化对象（裸连接、线程锁） | checkpoint 存不下 / 恢复失败 |
| 把「整个 Agent 实例」当 state | 无法清晰差分与回放 |
| 所有字段都整表覆盖 | `messages` 历史被冲掉（玩具执行器最常见坑） |
| 字段无约定、有的 append 有的静默覆盖 | 汇合节点后数据「偶发丢失」 |

#### 对照：手写 Agent 字段 → 图 state

| 手写 Agent | 图 state |
|------------|----------|
| `self.messages` | `state["messages"]` |
| `for step in range(...)` | `state["step"]` + 边循环 |
| `return final` / 提前 return | `status=done` + 边到 `end` |
| `self.trace.append(...)` | `trace` 字段或旁路日志 |

### 2.3 节点（Node）：状态 → 部分更新

#### 为什么节点要「只返回增量」？

若每个节点都 `return 全新完整 state`，你会忍不住在节点里复制粘贴未改字段；漏拷一次就丢数据。  
约定「只声明本步改了什么」，由**合并层（reducer）**接到现有 state 上——这是图库与本章玩具执行器的共同思想（实现细节不同）。

#### 怎么写

```python
def llm_node(state: dict) -> dict:
    """调用模型；只返回本步新增的消息与步数。"""
    assistant = fake_llm.complete(state["messages"], tools=TOOL_DEFS)
    return {
        "messages": [assistant],  # 增量：一条新消息
        "step": state["step"] + 1,
    }


def tool_node(state: dict) -> dict:
    """执行最近一条 assistant 的 tool_calls；返回多条 tool 消息。"""
    last = state["messages"][-1]
    tool_msgs = [run_tool_call(c, REGISTRY) for c in (last.get("tool_calls") or [])]
    return {
        "messages": tool_msgs,  # 增量：多条 tool 消息
        "step": state["step"] + 1,
    }
```

节点职责边界建议：

| 适合放进节点 | 不适合塞进节点 |
|--------------|----------------|
| 调 LLM、执行工具、改写查询、写草稿 | 决定「下一节点是谁」（那是边/router） |
| 更新 `status` / 业务字段 | 自己 `while` 再开一个无限子循环（难 checkpoint） |
| 校验、截断、打 trace 事件 | 偷偷改全局单例当「隐藏 state」 |

#### 跑一下

```python
state0 = {
    "messages": [{"role": "user", "content": "计算 1+2"}],
    "step": 0,
    "status": "running",
}

u1 = llm_node(state0)
# u1 ≈ {"messages": [assistant_with_tool_calls], "step": 1}

state1 = merge_state(state0, u1)  # merge_state 见第 6 节
u2 = tool_node(state1)
state2 = merge_state(state1, u2)
# state2["messages"] 长度 = 1 user + 1 assistant + N tool
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 节点里 `state["messages"].append(...)` 再 `return state` | 原地突变 + 返回全量，和「增量 + reducer」混用，难推理 |
| 节点返回 `{"messages": state["messages"] + [new]}` 而合并又是 append | **双重 append** 或语义混乱 |
| 节点内部再 `for` 跑完整条 Agent | 图失去「一步一节点」的暂停粒度 |
| 节点抛未捕获异常 | 无失败边 / 无 `status=failed` 时，整图直接崩 |

#### 对照：函数式更新 vs 原地修改

```python
# 推荐思想：纯增量（便于测试与合并）
return {"messages": [new_msg], "step": state["step"] + 1}

# 教学上避免：原地改再返回全量（和 reducer 模型冲突）
state["messages"].append(new_msg)
return state
```

真实库会用 TypedDict / 注解声明每个字段的 reducer；本章只用「约定哪些 key append」表达同一思想。

### 2.4 边（Edge）与合并（Reducer）直觉

#### 为什么要区分「固定边」和「条件边」？

- **固定边**：`tools → llm` 永远成立，不必看 state。  
- **条件边**：`llm` 之后可能去 `tools` 或 `end`，必须读 state（有没有 `tool_calls`、`step` 是否触顶等）。

Reducer / 合并则回答另一个问题：**节点返回的更新如何接到旧 state 上？**

```text
真实图库常见：messages 字段配置为 append（或 add_messages）
本章玩具：list_append_keys={"messages"} 模拟同一直觉
切记：这是语义对照，不是 API 对照
```

#### 怎么写（路由函数形状）

```python
def route_after_llm(state: dict) -> str:
    if state["step"] >= state.get("max_steps", 8):
        return "end"
    last = state["messages"][-1] if state["messages"] else {}
    if last.get("tool_calls"):
        return "tools"
    return "end"
```

固定边可用表：

```python
EDGES = {
    "tools": "llm",   # 工具执行完一定回到 llm
}
```

#### 跑一下

```python
# 假状态：刚跑完 llm，带 tool_calls
state = {
    "messages": [
        {"role": "user", "content": "算一下"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", ...}]},
    ],
    "step": 1,
    "max_steps": 8,
}
assert route_after_llm(state) == "tools"

# 假状态：llm 已给出最终文本
state["messages"][-1] = {"role": "assistant", "content": "答案是 3"}
assert route_after_llm(state) == "end"
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 路由里执行工具 / 调 LLM | 边变成「隐藏节点」，图不再可读 |
| 忘记 `max_steps` 判断 | `llm → tools → llm` 死循环 |
| 以为 `{**state, **update}` 等于 reducer | **浅覆盖会丢掉 messages 历史**（第 6 节必踩） |
| 把库的 `add_messages` 名称背进玩具代码 | 与 CONVENTIONS 冲突：思想对齐即可 |

#### 对照：边 vs 节点职责

| | 节点 | 边 / router |
|--|------|-------------|
| 输入 | state | 当前节点名 + state（玩具里常见） |
| 输出 | 部分状态更新 | 下一个节点名或 `end` |
| 可否有副作用 | 可以（I/O） | 应尽量纯（只做决策） |

---

## 3. 必掌握：条件分支与循环

有了节点与边，Agent 工作流的「形状」主要由**条件边**和**回边（循环）**决定。

### 3.1 条件分支

#### 为什么需要条件边？

同一入口，不同 state 要走不同技能链：

```text
intent == "billing" → 客服知识库 → 答复模板
intent == "bug"     → 日志检索 → 技术摘要 → 建单（可选）
```

若不用条件边，你只能写一个巨型节点内部 `if`——图的可视化与单测粒度都会变差。

#### 怎么写

```python
def classify_node(state: dict) -> dict:
    text = state["messages"][-1]["content"]
    intent = "billing" if "账单" in text else "bug"
    return {"intent": intent, "step": state["step"] + 1}


def route_after_classify(state: dict) -> str:
    return "billing_rag" if state.get("intent") == "billing" else "tech_probe"
```

汇合（多分支回到公共节点）时：

```text
billing_rag ──┐
              ├──→ answer → end
tech_probe  ──┘
```

字段合并规则必须事先约定：`messages` append；`intent` 替换；两边都写 `draft` 时以后写为准或显式冲突检测。

#### 跑一下

```python
state = {
    "messages": [{"role": "user", "content": "我的账单不对"}],
    "step": 0,
    "status": "running",
}
state = merge_state(state, classify_node(state))
assert route_after_classify(state) == "billing_rag"
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 分支条件依赖「节点局部变量」而非 state | 无法 checkpoint / 重放 |
| 两分支都 append 同一业务列表却无幂等 | 汇合后重复条目 |
| 条件边漏掉 default | 未知 intent 时 router 返回 `None`，执行器炸 |

#### 对照：if/else 链 vs 条件边

```python
# if 链：结构在代码控制流里
if intent == "billing":
    ...
else:
    ...

# 条件边：结构在图拓扑里（便于画图与插桩）
classify → (route) → billing_rag | tech_probe → answer
```

### 3.2 循环与终止

#### 为什么图里也会有循环？

tool-loop 本身就是环：

```text
llm → tools → llm → tools → ... → end
```

检索改写也是环：

```text
retrieve → (不够好?) → rewrite → retrieve
```

循环不是问题；**没有终止条件的循环**才是问题。

#### 怎么写（两层保险丝）

1. **业务终止**：无 `tool_calls`、检索分数够、审阅通过 → 走 `end`  
2. **硬顶终止**：`step >= max_steps` 或执行器 `max_visits` → 强制 `end` / 抛错 / `status=max_steps`

```python
def route_after_llm(state: dict) -> str:
    if state["step"] >= state["max_steps"]:
        return "end"
    last = state["messages"][-1]
    if last.get("tool_calls"):
        return "tools"
    return "end"


def route_after_retrieve(state: dict) -> str:
    if state.get("retrieve_retries", 0) >= 3:
        return "answer_degraded"  # 降级出口，避免死拧
    if state.get("docs"):
        return "write"
    return "rewrite"
```

`rewrite` 节点内递增 `retrieve_retries`；**终止条件写在 router 或专用 guard 节点**，不要指望模型「自己记得停」。

#### 跑一下（防死循环断言）

```python
def run_with_guard(nodes, router, state, start="llm", max_visits=20):
    cur = start
    for _ in range(max_visits):
        state = merge_state(state, nodes[cur](state))
        nxt = router(cur, state)
        if nxt == "end":
            return state
        cur = nxt
    raise RuntimeError("graph exceeded max visits")


# 构造一个永远返回 tools 的坏路由，确认硬顶生效
bad_nodes = {"llm": lambda s: {"step": s["step"] + 1, "messages": [{"role": "assistant", "tool_calls": [1]}]}}
bad_router = lambda cur, s: "llm"  # 无 end
try:
    run_with_guard(bad_nodes, bad_router, {"messages": [], "step": 0}, max_visits=5)
    assert False, "should have raised"
except RuntimeError as e:
    assert "max visits" in str(e)
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 只靠模型「别太长」 | 账单级死循环 |
| `max_steps` 只增不检查 | 字段有了却从不路由到 end |
| 重试计数放在节点闭包变量 | 恢复 checkpoint 后计数丢失或错乱 |
| 循环边回到「会重复副作用」的节点且无幂等 | 重复扣费、重复建单 |

#### 对照：for 的 max_steps vs 图的双硬顶

| 机制 | 手写 for | 图 |
|------|----------|-----|
| 业务停 | 无 tool_calls 就 return | 条件边到 `end` |
| 步数顶 | `for step in range(max_steps)` | `state["step"]` + router 判断 |
| 拓扑顶 | （天然单环） | `max_visits` 防止乱边/坏路由跑飞 |

练习要求（B4）：必须能证明超限时抛错或强制 end——这是图与 loop 的共同底线。

---

## 4. 建议掌握：人机协同与 checkpoint

复杂工作流几乎总会碰到：**不能全自动执行**，以及**跑到一半必须能停、能等、能续**。人机协同解决「谁批准」；checkpoint 解决「停在哪、如何续」。

### 4.1 Human-in-the-loop（人机协同）

#### 为什么需要人工节点？

高风险副作用不该由模型直接落锤：

```text
执行 shell / 删数据 / 转账 / 给外部发邮件 / 改生产配置
```

模式：在危险节点**之前**插入 `approve`（或 `interrupt`）节点——图进入 `waiting`，把「待批准事项」写入 state，等外部事件（UI 按钮、工单、回调）再继续。

#### 怎么写（状态机形状）

```text
... → plan_tool → approve → (denied? → end / revise)
                         ↘ (approved) → exec_tool → ...
```

```python
def approve_node(state: dict) -> dict:
    """不执行工具；只把图停在可序列化的等待态。"""
    pending = state.get("pending_tool")
    decision = state.get("approval")  # None | "allow" | "deny"
    if decision is None:
        return {
            "status": "waiting",
            "pending_tool": pending,
            # messages 可选：追加一条 system/notice，便于 UI 展示
        }
    if decision == "deny":
        return {
            "status": "done",
            "pending_tool": None,
            "messages": [{"role": "assistant", "content": "已拒绝执行该工具"}],
        }
    # allow：放行；真正执行交给下一节点 exec_tool
    return {"status": "running", "approval": None}


def route_after_approve(state: dict) -> str:
    if state.get("status") == "waiting":
        return "end"  # 对执行器而言：本轮先停；外层保存 checkpoint
    if state.get("status") == "done":
        return "end"
    return "exec_tool"
```

外层驱动（伪代码）：

```python
state = run_until_wait_or_end(graph, state)  # 内部遇 waiting 就停
save_checkpoint(thread_id, state)

# ... 人类在 UI 点「允许」...
state = load_checkpoint(thread_id)
state["approval"] = "allow"
state = run_until_wait_or_end(graph, state)  # 从 approve / exec_tool 续跑
```

#### 跑一下（默认拒绝）

```python
state = {
    "messages": [],
    "step": 2,
    "status": "running",
    "pending_tool": {"name": "run_shell", "arguments": {"cmd": "rm -rf /"}},
    "approval": None,
}
state = merge_state(state, approve_node(state))
assert state["status"] == "waiting"
assert route_after_approve(state) == "end"  # 本轮停止并靠 checkpoint 挂起

# 模拟人类拒绝
state["approval"] = "deny"
state = merge_state(state, approve_node(state))
assert state["status"] == "done"
assert state["pending_tool"] is None
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 在 `approve` 节点里 `input()` 阻塞进程 | 无法水平扩展；Web 服务会卡死 worker |
| 批准信息只存在内存 UI、不写 state | 恢复后不知道批的是哪次调用 |
| 危险工具仍可从别的边绕过 approve | ACL 形同虚设 |
| waiting 时继续自动跑下一节点 | 「人机」名存实亡 |

#### 对照：同步 input vs 异步挂起

| 方式 | 适用 | 问题 |
|------|------|------|
| CLI `input("批准吗?")` | 本地演示 | 不能进服务端 |
| `status=waiting` + checkpoint + 回调 | 产品形态 | 要设计 thread/session id |
| 工单系统 / 双人复核 | 强合规 | 延迟高，图要能久挂 |

### 4.2 Checkpoint（检查点）

#### 为什么需要 checkpoint？

每步（或每个节点后）把 state 持久化，换来三种能力：

1. **进程崩溃可恢复**：worker 挂了，换机器 load 再跑  
2. **长时间等待人工**：waiting 可以是分钟、小时、天  
3. **时间旅行调试（进阶）**：回到某步 state，换边/换参数重放  

没有 checkpoint 的图，只是「好看一点的 for」。

#### 怎么写（接口草图，非库 API）

```python
import json
from pathlib import Path
from typing import Any


def save_checkpoint(path: Path, thread_id: str, step: int, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"thread_id": thread_id, "step": step, "state": state}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_latest(path: Path, thread_id: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    latest = None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["thread_id"] == thread_id:
                latest = rec
    return latest
```

存储选型直觉：

| 存储 | 适合 |
|------|------|
| 内存 dict | 单测、演示 |
| JSONL / SQLite | 本地、作业、小型服务 |
| Postgres 等 | 多实例、要事务与查询 |

存什么：

```text
必须可序列化的 state 快照
可选：当前节点名、图版本号、时间戳
不要存：未关闭的连接、线程、匿名函数
```

#### 跑一下

```python
path = Path("playground_checkpoints.jsonl")
thread = "demo-1"
state = {"messages": [{"role": "user", "content": "hi"}], "step": 1, "status": "waiting"}
save_checkpoint(path, thread, step=1, state=state)

rec = load_latest(path, thread)
assert rec is not None
assert rec["state"]["status"] == "waiting"

# 续跑前写入批准
state = rec["state"]
state["approval"] = "allow"
state["status"] = "running"
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 只存最终答案 | 无法恢复到「下一步该跑哪个节点」 |
| state 含不可 JSON 化对象 | 保存阶段就失败 |
| 多 worker 无 thread_id 隔离 | 串话、互相覆盖 |
| 图逻辑升级后硬 load 旧快照 | 字段缺失；需要版本位或迁移 |
| 每字符流式输出都 checkpoint | I/O 过重；通常按节点边界存 |

#### 对照：日志 vs checkpoint

| | 轨迹日志 / trace | checkpoint |
|--|------------------|------------|
| 目的 | 评测、排障、审计 | **恢复执行** |
| 完整性 | 可只记事件 | 必须能重建 state |
| 失败时 | 「知道崩在哪」 | 「能从那一步接着跑」 |

练习 A2：设计「每步追加写入 JSONL」的接口——先把草图写对，再考虑压缩与后端存储。

---

## 5. 了解即可：其他编排

LangGraph 一类库把「LLM 工作流」产品化；思想仍是**状态 + 转移**。同思想还有：

| 方向 | 直觉 | 和本章关系 |
|------|------|------------|
| 纯手写状态机 | `phase` + `match/if` | 图的底层；简单场景足够 |
| Temporal 等通用工作流 | 长事务、重试、定时 | 偏工程编排；LLM 只是一步 Activity |
| 规则引擎 | 条件 → 动作表 | 适合确定性强的业务，不擅长开放推理 |
| 纯 tool-loop 框架 | 固定 ReAct 环 | 无复杂分支时更轻 |

选型一句：

> 需要 LLM 决策的**显式分支 / 人机 / 可恢复**，优先考虑图思想；需要跨天补偿事务，再看通用工作流引擎。

API 名会变；把「节点、边、状态、条件、checkpoint」地图留下来即可。

---

## 6. 微型图执行器（学习用，非 LangGraph 语义）

本节给一个**玩具执行器**：演示节点跳转与合并。  
目标是练会思想，**不是**复刻 LangGraph API。对照真实库时只问：哪些字段 append、哪些替换、checkpoint 存什么。

### 6.1 为什么不能用裸 `{**state, **update}`？

#### 为什么？

浅合并在标量上「看起来对」，在 `messages` 上是错的：

```python
state = {"messages": [m1, m2], "step": 1}
update = {"messages": [m3], "step": 2}
merged = {**state, **update}
# merged["messages"] == [m3]  ← 历史丢了！
```

真实图库对 `messages` 一类字段使用 **reducer（如 append / add_messages）**：节点只返回「本步新增列表」，框架接到历史后面。  
本章用 `list_append_keys` **模拟同一语义**——命名与签名都不必与库一致。

#### 怎么写（合并层）

```python
def merge_state(
    state: dict,
    update: dict,
    list_append_keys: frozenset[str] = frozenset({"messages"}),
) -> dict:
    """教学用合并：指定 key 做 list append，其余 key 替换。

    这是 reducer 直觉，不是 LangGraph 的公开 API。
    """
    out = {**state}
    for k, v in update.items():
        if k in list_append_keys and isinstance(v, list):
            out[k] = list(out.get(k) or []) + v
        else:
            out[k] = v
    return out
```

#### 跑一下

```python
s0 = {"messages": [{"role": "user", "content": "hi"}], "step": 0, "status": "running"}
s1 = merge_state(s0, {"messages": [{"role": "assistant", "content": "ok"}], "step": 1})
assert len(s1["messages"]) == 2
assert s1["step"] == 1

# 对比错误合并
wrong = {**s0, **{"messages": [{"role": "assistant", "content": "ok"}]}}
assert len(wrong["messages"]) == 1  # 历史被覆盖——这正是要避免的
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 节点返回全量 `messages` 且合并又 append | 重复历史 |
| 把 `trace` 也需要 append 却忘了加入 `list_append_keys` | trace 被替换成最后一跳 |
| 对 dict 字段做浅覆盖期望深合并 | 嵌套键丢失 |
| 以为玩具 `router(cur, state)` 等于某库的 `add_conditional_edges` | 违反 CONVENTIONS：勿一一对应 |

#### 对照：玩具 vs 真实库（只对照思想）

| 思想 | 本章玩具 | 真实图库（概念级） |
|------|----------|---------------------|
| 增量 messages | `list_append_keys` | 字段级 reducer / add_messages |
| 条件跳转 | `router(cur, state) -> str` | 条件边注册（API 名会变） |
| 停图 | 返回 `"end"` | END 哨兵 / 编译图出口 |
| 持久化 | 自写 JSONL | checkpointer 后端 |

### 6.2 执行器主循环

#### 为什么还要 `max_visits`？

即使节点内有 `max_steps`，坏路由（或忘写 end）仍可能在拓扑上空转。  
`max_visits` 是执行器级保险丝，与业务 `max_steps` 互补。

#### 怎么写

```python
from typing import Callable


def run_graph(
    nodes: dict[str, Callable[[dict], dict]],
    edges: dict[str, str],
    router: dict[str, Callable[[dict], str]] | Callable[[str, dict], str],
    state: dict,
    start: str = "llm",
    max_visits: int = 20,
    list_append_keys: frozenset[str] = frozenset({"messages"}),
) -> dict:
    """按节点执行并跳转；合并默认对 messages 做 append。

    router 两种用法（任选，保持简单）：
    - 字典：{节点名: (state)->下一节点}
    - 函数：(当前节点, state)->下一节点
    """
    cur = start
    for _ in range(max_visits):
        if cur not in nodes:
            raise KeyError(f"unknown node: {cur}")
        state = merge_state(state, nodes[cur](state), list_append_keys=list_append_keys)

        if callable(router) and not isinstance(router, dict):
            nxt = router(cur, state)
        elif cur in router:
            nxt = router[cur](state)
        else:
            nxt = edges[cur]

        if nxt == "end":
            state = {**state, "status": state.get("status") or "done"}
            return state
        cur = nxt
    raise RuntimeError("graph exceeded max visits")
```

#### 跑一下（假节点跑通 llm→tools→llm→end）

```python
def llm(state: dict) -> dict:
    # 第一步要工具；第二步给最终答
    tool_done = any(m.get("role") == "tool" for m in state["messages"])
    if not tool_done:
        return {
            "messages": [{
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "c1", "function": {"name": "echo", "arguments": "{}"}}],
            }],
            "step": state.get("step", 0) + 1,
        }
    return {
        "messages": [{"role": "assistant", "content": "完成"}],
        "step": state.get("step", 0) + 1,
    }


def tools(state: dict) -> dict:
    return {
        "messages": [{"role": "tool", "tool_call_id": "c1", "content": "ok"}],
        "step": state.get("step", 0) + 1,
    }


def router(cur: str, state: dict) -> str:
    if cur == "llm":
        last = state["messages"][-1]
        if last.get("tool_calls"):
            return "tools"
        return "end"
    if cur == "tools":
        return "llm"
    return "end"


final = run_graph(
    nodes={"llm": llm, "tools": tools},
    edges={},
    router=router,
    state={"messages": [{"role": "user", "content": "go"}], "step": 0, "status": "running"},
    start="llm",
)
assert final["messages"][-1]["content"] == "完成"
assert final["step"] == 3  # llm, tools, llm
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| `edges["llm"] = "tools"` 写死且不再 route | 第二次 llm 仍被塞去 tools |
| 在 `run_graph` 里默认浅覆盖合并 | 作业 B3 看似跑通，messages 其实残缺 |
| `max_visits` 很大、节点有外部副作用 | 账单级重复调用 |
| 追求与库方法同名同参 | 学成「假绑定」，换版本即废 |

#### 对照：学完后看真实库时问什么

打开官方最小例子时，只记差异笔记（练习 C1 可选）：

1. state 如何声明？字段 reducer 怎么标？  
2. 条件边注册长什么样？（名字可不记死）  
3. 人机中断是节点内 interrupt，还是边外挂起？  
4. checkpoint 最小后端是内存还是 sqlite？  
5. 与本章玩具：哪些思想同、哪些 API 不同？

---

## 7. 练习指引

[`exercises/11-agent-core/04-langgraph.md`](../../exercises/11-agent-core/04-langgraph.md)

建议顺序：

1. **B1** 先画 llm/tools/end 与条件路由（不写码）  
2. **B2** 定 state 字段与合并约定（messages append）  
3. **B3** 实现/改写 `merge_state` + `run_graph`，假节点跑通环  
4. **B4** 证明 `max_visits` / `max_steps` 生效  
5. **A1/A2** 选做：approve 等待态 或 JSONL checkpoint  

---

## 8. 小结与下一站

### 自检

- [ ] 能说明何时该用图、何时一层 for 足够  
- [ ] 能画出节点/边，并写出 state 最小字段  
- [ ] 能解释 messages 为何要 append（reducer），而非浅覆盖  
- [ ] 条件边 + 循环有双硬顶（业务结束 + max_visits/max_steps）  
- [ ] 知道 approve 如何把图停在 `waiting`，checkpoint 存什么  

### 下一章

[`05-agent-memory.md`](./05-agent-memory.md) —— 短期/长期记忆。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Agent Framework 概览](./03-agent-frameworks.md)
- 下一章：[Agent Memory](./05-agent-memory.md)
