# 练习：LangGraph 与工作流（教学玩具）

> 对应文档：[`docs/11-agent-core/04-langgraph.md`](../../docs/11-agent-core/04-langgraph.md)  
> 状态：`已完成出题`  
> 建议用时：70～110 分钟（含热身）  
> Python：`≥ 3.11`

## 练习说明

1. 先读完文档「必掌握」（节点 / 边 / 状态 / 条件分支 / 循环）再做题；人机与 checkpoint 做进阶题时用得到。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **本章不绑定真实 LangGraph 库**。你要实现的是**教学玩具执行器**：用 `merge_state` 的 **reducer / append** 语义合并节点增量；命名、签名、类名都**不必**与官方 API 一一对应（见 [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)）。
4. FakeLLM 的 `complete(...)` **必须返回 assistant `dict`**（至少含 `"role": "assistant"`），不要返回 `str`。
5. 工具执行前先 `authorize(role, tool, args)`，再查 registry；未授权不得调用工具函数。
6. 建议代码目录：

```text
playground/11-agent-core/04-langgraph/
```

7. 先自己做完，再看文末「提示与参考答案」。答案不是唯一写法，能通过验收、意图清晰即可。

---

## 热身题（建议先做）

> 每题几分钟。用来把「增量更新」「浅覆盖会丢历史」踩一遍。

### W1. 浅覆盖会丢掉 `messages`

**给定**：

```python
state = {"messages": [{"role": "user", "content": "hi"}], "step": 0}
update = {"messages": [{"role": "assistant", "content": "ok"}], "step": 1}
```

**要求**：分别用 `{**state, **update}` 与「append 语义」合并，对比 `messages` 长度。

**验收**：能口头说明——浅覆盖后长度为 1；正确 append 后长度为 2。

---

### W2. 节点只返回增量

**给定**：一个假 `llm_node(state) -> dict`。

**要求**：节点返回的 `messages` 应是「本步新增的列表」（通常 1 条），而不是整份历史；`step` 返回新标量。

**验收**：对空历史调用一次后，调用方用 append 合并，历史长度为 1。

---

### W3. FakeLLM 返回 dict

**要求**：实现同步 `FakeLLM.complete(messages, tools=None) -> dict`：若最后一条 user 含「计算」，返回带 `tool_calls` 的 assistant dict；否则返回纯文本 `"你好"`。

**验收**：

```python
msg = FakeLLM().complete([{"role": "user", "content": "计算 1+2"}])
assert isinstance(msg, dict) and msg["role"] == "assistant"
assert msg.get("tool_calls")  # 非空
assert not isinstance(msg, str)
```

---

## 基础题（必做）

### B1. 状态：TypedDict 或 dataclass

定义图上流动的状态（二选一或并用）。至少包含：

| 字段 | 类型直觉 | 合并约定 |
|------|----------|----------|
| `messages` | `list[dict]` | **append**（reducer） |
| `step` | `int` | 替换 |
| `status` | `str` | 替换：`running` / `waiting` / `done` / `failed` / `max_steps` |
| `max_steps` | `int` | 替换（配置型字段） |

要求：

1. 用 `TypedDict`（`total=False` 亦可）**或** `@dataclass` 写出类型。
2. 用文字或注释标明：哪些 key 走 list append，哪些走替换。
3. 初始 state 示例：一条 user 消息，`step=0`，`status="running"`，`max_steps=8`。

**验收**：别人只看你的类型定义，能知道 `messages` 绝不能用浅覆盖合并。

---

### B2. 节点函数：`llm_node` / `tools_node`

实现两个节点（签名自定，但输入为 state、输出为**部分更新** dict）：

```python
def llm_node(state: dict) -> dict:
    """调 FakeLLM；返回新增 assistant 消息 + step+1。"""

def tools_node(state: dict) -> dict:
    """
    取最近一条 assistant 的 tool_calls；
    对每个 call：authorize → registry 执行 → 追加 role=tool 消息。
    """
```

约定：

1. FakeLLM 返回 assistant **dict**。
2. `authorize(role, tool_name, args) -> bool`：**先**授权，**再** `registry[name](**args)`；拒绝时 tool 消息 `content` 写清原因，**不要**假装成功。
3. 节点内**不要**决定下一跳（那是边 / router 的事）。
4. 不要原地 `state["messages"].append(...)` 再 `return state`；返回增量。

可先注册一个假工具：

```python
def echo(text: str = "") -> str:
    return f"echo:{text}"

REGISTRY = {"echo": echo}

def authorize(role: str, tool: str, args: dict) -> bool:
    # 教学：禁止 shell；echo 允许
    return tool != "shell"
```

**验收**：单独对 state 调一次 `llm_node`（用户说「计算」），增量里有 `tool_calls`；再 `merge` 后调 `tools_node`，能看到 `role=tool` 消息。

---

### B3. 边 / 条件边 + 玩具执行器

实现教学玩具（名字可自定，例如 `merge_state` + `run_graph`；**勿**抄官方类名当绑定）：

```python
def merge_state(
    state: dict,
    update: dict,
    list_append_keys: frozenset[str] = frozenset({"messages"}),
) -> dict:
    """指定 key list-append，其余替换。教学玩具，非库 API。"""

def run_graph(
    nodes: dict[str, Callable[[dict], dict]],
    router: Callable[[str, dict], str],
    state: dict,
    *,
    start: str = "llm",
    max_visits: int = 20,
) -> dict:
    """执行节点 → 合并 → 路由；nxt=='end' 则结束；超 max_visits 抛错。"""
```

条件路由示例：

```text
llm → (有 tool_calls?) → tools → llm → ...
     ↘ end
```

`tools` 之后固定回 `llm`（固定边也可用 router 表达）。

**验收**：假节点跑通 `llm → tools → llm → end`；最终 `messages[-1]["content"]` 为最终答；全程 `messages` 历史不被冲掉。

---

### B4. 循环上限：`max_steps` + `max_visits`

1. 在 `route_after_llm`（或统一 router）里：若 `state["step"] >= state["max_steps"]`，走 `end`，并可把 `status` 标为 `"max_steps"`（在节点或结束前更新均可，需可观测）。
2. 构造坏路由：永远返回下一节点、永不 `"end"`，断言 `run_graph(..., max_visits=5)` 抛出 `RuntimeError`（文案含 `max visits` 即可）。

**验收**：两条保险丝都能证明生效（断言或清晰打印）。

---

## 进阶题（建议至少做 1 题）

### A1. 中断 / 人审节点（假实现）

加入 `approve_node`：

```text
... →（准备执行危险工具）→ approve → waiting（本轮 end，靠外层续跑）
                              ↘ approval=allow → exec_tool
                              ↘ approval=deny  → done
```

要求：

1. `approval is None` 时返回 `status="waiting"`，**不**执行工具；router 对本轮返回 `"end"`（挂起）。
2. 外层模拟人类：改 `state["approval"]="allow"` 或 `"deny"` 后再次 `run_graph`（可从 `approve` 起步）。
3. **不要**在节点里用阻塞式 `input()` 当产品方案（CLI 演示可另说，题解里注明为何不适合服务端）。

**验收**：默认路径进入 `waiting`；拒绝后 `pending_tool` 清空且有拒答消息；允许后能执行工具。

---

### A2. Checkpoint 草图（JSONL）

实现：

```python
def save_checkpoint(path: Path, thread_id: str, step: int, state: dict) -> None: ...
def load_latest(path: Path, thread_id: str) -> dict | None: ...
```

每步（或每次进入 `waiting`）追加一行 JSON。`state` 必须可 JSON 序列化。

**验收**：写入 waiting 快照 → 进程「假装重启」→ `load_latest` → 写入 `approval` → 续跑成功。

---

## 挑战题（可选）

### C1. 把手写 Agent 两路径映射到图

对照手写 Agent 章的两路径：

| 路径 | 手写 loop | 图拓扑 |
|------|-----------|--------|
| 普通问答 | LLM 直接最终答 | `llm → end` |
| 工具环 | LLM → tools → LLM → … | `llm ⇄ tools` 直至无 tool_calls / 触顶 |

要求：

1. 用同一套玩具 `run_graph` + FakeLLM，跑通上述两路径（各写一组断言）。
2. 用一段文字（≥5 句）说明：**图没有让模型变聪明**，只是把控制流显式化；简单 tool-loop 不必强行上图。
3. 再次强调：你的执行器是**教学玩具**，与官方 LangGraph **思想对齐、API 不对齐**。

**验收**：两路径 demo 可跑；书面结论说清「何时一层 for 足够」。

---

## 验收标准（本章通过线）

- [ ] （建议）热身 W1～W3 建立「append ≠ 浅覆盖」手感
- [ ] **通过线**：B1～B4 全部完成；`merge_state` 对 `messages` 为 append；假图跑通；循环上限可证明
- [ ] FakeLLM 返回 dict；工具路径上 **authorize 在 registry 调用前**
- [ ] 能口述：为何勿与真实 LangGraph API 一一对应
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

> 每题先给**思路**，再给带注释的**参考实现**。教学玩具命名可改；语义（messages append、max_visits、authorize 前置）不要改。

### W1 思路 + 参考答案

**思路**：`{**a, **b}` 同名 key 以后者为准，列表会被整表替换。

**参考答案**

```python
state = {"messages": [{"role": "user", "content": "hi"}], "step": 0}
update = {"messages": [{"role": "assistant", "content": "ok"}], "step": 1}

shallow = {**state, **update}
assert len(shallow["messages"]) == 1  # 历史丢了

appended = {
    **state,
    "messages": state["messages"] + update["messages"],
    "step": update["step"],
}
assert len(appended["messages"]) == 2
```

---

### W2 思路 + 参考答案

**思路**：节点声明「本步改了什么」；合并层负责接到旧 state。

**参考答案**

```python
def llm_node(state: dict) -> dict:
    return {
        "messages": [{"role": "assistant", "content": "hi", "tool_calls": None}],
        "step": state.get("step", 0) + 1,
    }


def merge(state: dict, update: dict) -> dict:
    out = {**state}
    out["messages"] = list(out.get("messages") or []) + list(update.get("messages") or [])
    if "step" in update:
        out["step"] = update["step"]
    return out


s0 = {"messages": [], "step": 0}
s1 = merge(s0, llm_node(s0))
assert len(s1["messages"]) == 1 and s1["step"] == 1
```

---

### W3 思路 + 参考答案

**思路**：统一契约 `complete -> dict`，与 [`CONVENTIONS.md`](../../docs/CONVENTIONS.md) 一致。

**参考答案**

```python
class FakeLLM:
    def complete(self, messages: list[dict], tools: list | None = None) -> dict:
        text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                text = str(m.get("content") or "")
                break
        if "计算" in text:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {
                            "name": "echo",
                            "arguments": {"text": text},
                        },
                    }
                ],
            }
        return {"role": "assistant", "content": "你好", "tool_calls": None}


msg = FakeLLM().complete([{"role": "user", "content": "计算 1+2"}])
assert isinstance(msg, dict) and msg["role"] == "assistant"
assert msg.get("tool_calls")
```

---

### B1 思路 + 参考答案

**思路**：类型是文档；合并约定写进注释，避免以后「有的 append 有的静默覆盖」。

**参考答案**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypedDict


class AgentState(TypedDict, total=False):
    messages: list[dict]
    step: int
    status: str
    max_steps: int
    pending_tool: dict | None
    approval: Literal["allow", "deny"] | None


@dataclass
class GraphState:
    """也可用 dataclass；合并时仍按字段约定，而非依赖库 reducer API。"""

    messages: list[dict] = field(default_factory=list)  # APPEND
    step: int = 0  # REPLACE
    status: str = "running"  # REPLACE
    max_steps: int = 8  # REPLACE


def initial_state(user_text: str) -> dict:
    return {
        "messages": [{"role": "user", "content": user_text}],
        "step": 0,
        "status": "running",
        "max_steps": 8,
    }


# 合并约定（写进模块顶注释亦可）：
# - messages: list append（reducer）
# - step / status / max_steps / pending_tool / approval: 替换
```

---

### B2 思路 + 参考答案

**思路**：

1. 节点 = 副作用边界 + 增量；路由另算。
2. **authorize → registry**，顺序反了就会在拒绝前执行副作用。
3. arguments 若是 JSON 字符串需 `json.loads`；本题 FakeLLM 直接给 dict 更简单。

**参考答案**

```python
from __future__ import annotations

import json
from typing import Any, Callable


def echo(text: str = "") -> str:
    return f"echo:{text}"


REGISTRY: dict[str, Callable[..., Any]] = {"echo": echo}


def authorize(role: str, tool: str, args: dict) -> bool:
    """工具 ACL：想调用 ≠ 允许执行。必须在 registry 调用之前。"""
    if tool == "shell":
        return False
    return tool in REGISTRY


class FakeLLM:
    def complete(self, messages: list[dict], tools: list | None = None) -> dict:
        last_user = next(
            (m for m in reversed(messages) if m.get("role") == "user"),
            {"content": ""},
        )
        text = str(last_user.get("content") or "")
        tool_done = any(m.get("role") == "tool" for m in messages)
        if ("计算" in text or "搜索" in text) and not tool_done:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "c1",
                        "function": {"name": "echo", "arguments": {"text": text}},
                    }
                ],
            }
        return {"role": "assistant", "content": f"最终答复：已处理「{text}」"}


LLM = FakeLLM()


def llm_node(state: dict) -> dict:
    assistant = LLM.complete(state["messages"])
    assert isinstance(assistant, dict) and assistant.get("role") == "assistant"
    return {"messages": [assistant], "step": state.get("step", 0) + 1}


def _parse_args(raw: Any) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw) if raw.strip() else {}
    return {}


def tools_node(state: dict) -> dict:
    last = state["messages"][-1]
    role = "agent"  # 教学用角色名；生产按会话角色
    outs: list[dict] = []
    for call in last.get("tool_calls") or []:
        fn = call.get("function") or {}
        name = fn.get("name") or call.get("name")
        args = _parse_args(fn.get("arguments", call.get("arguments")))
        # 1) 先授权
        if not authorize(role, name, args):
            outs.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": f"denied: {name}",
                }
            )
            continue
        # 2) 再查 registry 并执行
        impl = REGISTRY.get(name)
        if impl is None:
            outs.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": f"unknown tool: {name}",
                }
            )
            continue
        try:
            result = impl(**args)
            outs.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": str(result),
                }
            )
        except Exception as exc:
            outs.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": f"error: {exc}",
                }
            )
    return {"messages": outs, "step": state.get("step", 0) + 1}
```

---

### B3 思路 + 参考答案

**思路**：玩具执行器 = `for` + merge + router；`list_append_keys` 模拟字段级 reducer，**不是**官方 `add_messages` API。

**参考答案**

```python
from __future__ import annotations

from collections.abc import Callable


def merge_state(
    state: dict,
    update: dict,
    list_append_keys: frozenset[str] = frozenset({"messages"}),
) -> dict:
    """教学玩具合并层：思想对齐真实图库的 reducer，API 不对齐。"""
    out = {**state}
    for k, v in update.items():
        if k in list_append_keys and isinstance(v, list):
            out[k] = list(out.get(k) or []) + v
        else:
            out[k] = v
    return out


def run_graph(
    nodes: dict[str, Callable[[dict], dict]],
    router: Callable[[str, dict], str],
    state: dict,
    *,
    start: str = "llm",
    max_visits: int = 20,
    list_append_keys: frozenset[str] = frozenset({"messages"}),
) -> dict:
    cur = start
    for _ in range(max_visits):
        if cur not in nodes:
            raise KeyError(f"unknown node: {cur}")
        state = merge_state(state, nodes[cur](state), list_append_keys=list_append_keys)
        nxt = router(cur, state)
        if nxt == "end":
            if state.get("status") == "running":
                state = {**state, "status": "done"}
            return state
        cur = nxt
    raise RuntimeError("graph exceeded max visits")


def router(cur: str, state: dict) -> str:
    if state.get("step", 0) >= state.get("max_steps", 8):
        return "end"
    if cur == "llm":
        last = state["messages"][-1] if state["messages"] else {}
        if last.get("tool_calls"):
            return "tools"
        return "end"
    if cur == "tools":
        return "llm"
    return "end"


# ---- 跑通 llm → tools → llm → end（依赖 B2 的 llm_node / tools_node）----
final = run_graph(
    nodes={"llm": llm_node, "tools": tools_node},
    router=router,
    state={
        "messages": [{"role": "user", "content": "请计算 1+2"}],
        "step": 0,
        "status": "running",
        "max_steps": 8,
    },
    start="llm",
)
assert any(m.get("role") == "tool" for m in final["messages"])
assert final["messages"][-1]["role"] == "assistant"
assert final["messages"][-1].get("content")
assert final["status"] == "done"
```

---

### B4 思路 + 参考答案

**思路**：业务顶（`max_steps`）防正常环空转；拓扑顶（`max_visits`）防坏路由。

**参考答案**

```python
def router_with_cap(cur: str, state: dict) -> str:
    if state.get("step", 0) >= state.get("max_steps", 8):
        return "end"
    if cur == "llm":
        last = state["messages"][-1] if state["messages"] else {}
        return "tools" if last.get("tool_calls") else "end"
    if cur == "tools":
        return "llm"
    return "end"


def forever_llm(state: dict) -> dict:
    return {
        "messages": [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "x", "function": {"name": "echo", "arguments": {}}}],
            }
        ],
        "step": state.get("step", 0) + 1,
    }


# 坏路由：永不 end
bad_router = lambda cur, s: "llm"

try:
    run_graph(
        nodes={"llm": forever_llm},
        router=bad_router,
        state={"messages": [], "step": 0, "status": "running", "max_steps": 100},
        start="llm",
        max_visits=5,
    )
    raise AssertionError("should have raised")
except RuntimeError as exc:
    assert "max visits" in str(exc)


# max_steps：router_with_cap 在 step>=max_steps 时 end（配合始终要工具的 llm_node 即可观测）
```


---

### A1 思路 + 参考答案

**思路**：人审 = 把图停在可序列化 `waiting`；批准是**外层事件**写回 state，不是节点内阻塞。

**参考答案**

```python
def approve_node(state: dict) -> dict:
    decision = state.get("approval")  # None | allow | deny
    pending = state.get("pending_tool")
    if decision is None:
        return {"status": "waiting", "pending_tool": pending}
    if decision == "deny":
        return {
            "status": "done",
            "pending_tool": None,
            "approval": None,
            "messages": [{"role": "assistant", "content": "已拒绝执行该工具"}],
            "step": state.get("step", 0) + 1,
        }
    # allow：放行，真正执行交给 exec_tool
    return {"status": "running", "approval": None, "step": state.get("step", 0) + 1}


def exec_tool_node(state: dict) -> dict:
    pending = state.get("pending_tool") or {}
    name = pending.get("name", "")
    args = pending.get("arguments") or {}
    if not authorize("agent", name, args):
        return {
            "messages": [{"role": "tool", "content": f"denied: {name}"}],
            "pending_tool": None,
            "step": state.get("step", 0) + 1,
        }
    fn = REGISTRY.get(name)
    content = str(fn(**args)) if fn else f"unknown: {name}"
    return {
        "messages": [{"role": "tool", "content": content}],
        "pending_tool": None,
        "step": state.get("step", 0) + 1,
    }


def router_hitl(cur: str, state: dict) -> str:
    if cur == "approve":
        if state.get("status") == "waiting":
            return "end"  # 本轮挂起
        if state.get("status") == "done":
            return "end"
        return "exec_tool"
    if cur == "exec_tool":
        return "end"
    return "end"


st = {
    "messages": [],
    "step": 0,
    "status": "running",
    "max_steps": 8,
    "pending_tool": {"name": "echo", "arguments": {"text": "rm"}},
    "approval": None,
}
nodes = {"approve": approve_node, "exec_tool": exec_tool_node}
st = run_graph(nodes=nodes, router=router_hitl, state=st, start="approve")
assert st["status"] == "waiting"
st["approval"] = "deny"
st = run_graph(nodes=nodes, router=router_hitl, state=st, start="approve")
assert st["status"] == "done" and st.get("pending_tool") is None
# 服务端勿用 input() 阻塞；用 checkpoint + 回调写回 approval。
```


---

### A2 思路 + 参考答案

**思路**：checkpoint 存的是「能恢复执行的 state」，不是只有最终答案的日志。

**参考答案**

```python
from __future__ import annotations

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
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("thread_id") == thread_id:
                latest = rec
    return latest


path = Path("playground/11-agent-core/04-langgraph/checkpoints.jsonl")
thread = "demo-1"
waiting = {
    "messages": [{"role": "user", "content": "删库"}],
    "step": 2,
    "status": "waiting",
    "pending_tool": {"name": "echo", "arguments": {"text": "danger"}},
    "approval": None,
    "max_steps": 8,
}
save_checkpoint(path, thread, step=2, state=waiting)
rec = load_latest(path, thread)
assert rec is not None and rec["state"]["status"] == "waiting"
state = rec["state"]
state["approval"] = "allow"
state["status"] = "running"
# 然后 run_graph(start="approve", ...)
```

---

### C1 思路 + 参考答案

**思路**：两路径只是 router 在「有无 tool_calls」上的分支；图的价值在复杂分支 / 人机 / 恢复，不在「多几个节点就更聪明」。

**参考答案**

```python
# 路径 1：普通问答 → llm → end
plain = run_graph(
    nodes={"llm": llm_node, "tools": tools_node},
    router=router,
    state={
        "messages": [{"role": "user", "content": "你好"}],
        "step": 0,
        "status": "running",
        "max_steps": 8,
    },
)
assert plain["messages"][-1]["content"]
assert not any(m.get("role") == "tool" for m in plain["messages"])

# 路径 2：工具环 → llm → tools → llm → end
toolish = run_graph(
    nodes={"llm": llm_node, "tools": tools_node},
    router=router,
    state={
        "messages": [{"role": "user", "content": "请计算合计"}],
        "step": 0,
        "status": "running",
        "max_steps": 8,
    },
)
assert any(m.get("role") == "tool" for m in toolish["messages"])
assert toolish["messages"][-1]["role"] == "assistant"
```

**书面结论（示例）**：手写 `for` 与图都能表达 LLM↔Tools，差别在控制流是否显式。普通问答只是 `llm→end`，并不更聪明；工具环显式化是为了插入 approve / checkpoint。图不提升推理质量。简单场景优先 tool-loop；本执行器是**教学玩具**，思想对齐、**勿**与官方 API 一一对应。

---

## 导航

- 文档：[`docs/11-agent-core/04-langgraph.md`](../../docs/11-agent-core/04-langgraph.md)  
- 上一练习：[`03-agent-frameworks.md`](./03-agent-frameworks.md)  
- 下一练习：[`05-agent-memory.md`](./05-agent-memory.md)
