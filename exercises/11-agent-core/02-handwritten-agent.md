# 练习：手写一个 Agent

> 对应文档：[`docs/11-agent-core/02-handwritten-agent.md`](../../docs/11-agent-core/02-handwritten-agent.md)  
> 状态：`已完成出题`  
> 建议用时：80～110 分钟  
> 运行环境：Python ≥ 3.11 · FakeLLM 契约见 [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)  
> 前置：[`01-tool-calling.md`](./01-tool-calling.md) 的 `TOOLS` / `REGISTRY` / `run_tool_call` / `authorize`

## 练习说明

1. 先读文档 §1～§3：古典 ReAct（文本协议）与现代 **tool-loop**（结构化 `tool_calls`）要分清；本章实现后者。
2. 题目分档：**热身 / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **硬约定**：
   - `FakeLLM.complete(messages, tools=None) -> dict`（assistant 消息），**禁止返回 `str`**。
   - 执行工具前调用 `authorize(role, tool, args)`（可复用上一章）；默认拒绝未知工具。
   - `Agent.run` 必须有 `max_steps`；建议维护 `trace` 事件列表。
4. 建议代码目录：

```text
playground/11-agent-core/02-handwritten-agent/
```

5. CI / 本地默认 FakeLLM；真模型只作为可选双模式（C 题）。先做完再看文末答案。

---

## 热身题（建议先做）

### W1. 一句话对照

用自己的话填空（书面即可）：

1. ReAct **思想**强调：交替 ______ 与 ______。
2. 现代 tool-loop 把「行动」收成结构化字段 ______；观测回传用 `role=______` + `tool_call_id`。
3. 本章默认实现的是 ______（填 tool-loop 或古典文本协议）。

**验收**：能口头说清「思想同源、协议不同」。

---

### W2. 消息环形状（不跑真模型）

手写 `messages` 列表，形状为：

```text
user → assistant(tool_calls) → tool → assistant(final)
```

**验收**：最后一条无 `tool_calls`；中间 tool 消息的 `tool_call_id` 与 assistant 提议一致。

---

## 基础题（必做）

### B1. 状态机图与终止边

画出（或用 ASCII / Markdown）Agent 主路径状态机，至少包含：

```text
IDLE → CALLING_LLM → (NEED_TOOLS → EXECUTING_TOOLS → CALLING_LLM)* → DONE
                                                      ↘ FAILED / max_steps
```

书面列出 **≥4 条终止边**（从哪一态、到哪一态、条件是什么）。建议覆盖：

- 无 `tool_calls` → DONE
- `max_steps` 触顶
- 重复 tool_call 熔断
- 不可恢复错误 → FAILED

**验收**：别人只看你的图 + 表，能说清「何时停」。

---

### B2. FakeLLM（关键词三路径）

实现：

```python
class FakeLLM:
    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        ...
```

| 路径 | 条件 | 返回 |
|------|------|------|
| 要工具 | 用户内容含「计算」或「算」 | `tool_calls` → `calculator`（或 `calc`） |
| 不要工具 | 其它闲聊 | `content` 如 `ECHO:...`，无 tool_calls |
| 工具后收尾 | 上一条 `role=="tool"` | 自然语言终答 |

**验收**：`isinstance(complete(...), dict)`；三条路径可单独断言。

---

### B3. `Agent.run` 两条主路径

实现最小 Agent（可 dataclass）：

```python
@dataclass
class Agent:
    llm: Any
    tools: dict[str, Callable[..., Any]]
    max_steps: int = 5
    role: str = "user"  # 传给 authorize
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)

    def run(self, user_input: str) -> str:
        ...
```

要求：

1. 循环内：`complete` → append assistant → 无工具则返回 `content`
2. 有 `tool_calls`：**authorize → 再执行**（经 `run_tool_call`），append tool 消息，继续
3. `content` 与 `tool_calls` 同时存在时，**先执行工具**，勿当最终答
4. 测通两条路径：
   - 闲聊：不出现 `tool_call` 轨迹
   - 计算：轨迹含工具名，最终答依赖 tool 结果

**验收**：FakeLLM 下两条路径断言通过；未知工具被拒绝且不抛崩进程。

---

### B4. `max_steps` / 重复熔断

1. 造一个「永远要工具」的 LLM（每轮相同 `tool_calls`）
2. `max_steps=3` 时，`run` 必须确定停止（触顶文案 **或** 重复熔断文案均可，但要可断言）
3. `trace` 里 `type=="llm"` 的次数 ≤ `max_steps`

**验收**：`assert "停止" in out`（或你约定的结束语关键字）；不会死循环。

---

## 进阶题（建议至少做 1 题）

### A1. 工具错误恢复

实现（或扩展）工具：

```python
def search(query: str) -> list[str]:
    if query == "boom":
        raise RuntimeError("upstream 500")
    return [f"doc:{query}"]
```

要求：

1. 异常由 `run_tool_call` 收成 `ok=false` 的 tool 消息，**不要**让 `Agent.run` 直接 traceback 退出
2. FakeLLM：看到错误 JSON 后返回致歉终答（如「搜索暂时不可用…」）
3. （建议）连续失败计数：超过 `max_arg_failures` 则宿主强制停止

**验收**：`agent.run("请搜索爆炸新闻")` 得到致歉类终答；进程不崩。

---

### A2. 轨迹打印与排障字段

扩展 `trace`，每步至少记录：

| type | 建议字段 |
|------|----------|
| `llm` | `step` |
| `tool_call` | `step`, `name`, （可选）`ok` |
| `error` / `stop` | `reason`（max_steps / repeat / unauthorized…） |

写 `print_trace(agent)`：人类可读地打印事件流。

**验收**：跑完计算路径后，打印顺序大致为 `llm → tool_call → llm`；闲聊路径无 `tool_call`。

---

## 挑战题（可选）

### C1. 真 / 假双模式说明 + 骨架

书面 + 代码骨架（**不要求**本机有 API Key 也能交卷）：

1. 用表格说明：FakeLLM vs 真模型，各自测什么、CI 是否必跑
2. 给出 `LLMClient` Protocol（或 ABC）与工厂函数伪代码：

```python
def build_llm(*, mode: Literal["fake", "real"], **kwargs) -> LLMClient:
    ...
```

3. `Agent` **只依赖** `complete(messages, tools=None) -> dict`，切换模式不改 `Agent.run`
4. 真模型分支可用注释标明「此处接厂商 SDK」，返回值仍必须是 assistant dict

**验收**：别人能按你的骨架注入 Fake / Real；契约不分裂。

---

### C2.（可选加分）`reset` / session 隔离

多次 `run` 不串话：每次 `run` 清空或隔离 `messages`（或提供 `reset()`）。  
**验收**：第二次闲聊的 `messages` 不含第一次的 tool 结果。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W2
- [ ] **通过线**：B1～B4；状态机有终止边；FakeLLM 返回 dict；两路径 + max_steps
- [ ] 工具执行前有 `authorize`（完整实现或明确扩展点 + 未知工具拒绝）
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 双模式骨架
- [ ] 能口述：状态机是设计语言，`for` 是实现手法

---

## 提示与参考答案（先做题再看）

> 可复用上一章的 `authorize` / `run_tool_call` / `parse_arguments`；下列给出自洽粘贴版，便于本章单独跑通。

---

### W1 思路 + 参考答案

**思路**：思想是「想了再做、做了再想」；工程上用 `tool_calls` + `tool` 消息落地。

**参考答案**

1. 推理（Reason）与 行动（Act）
2. `tool_calls`；`tool`
3. tool-loop

---

### W2 思路 + 参考答案

**参考答案**

```python
messages = [
    {"role": "user", "content": "算一下 1+2"},
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": '{"expr":"1+2"}',
                },
            }
        ],
    },
    {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": '{"ok": true, "result": 3}',
    },
    {"role": "assistant", "content": "1+2=3"},
]
assert messages[-1].get("tool_calls") in (None, [])
assert messages[2]["tool_call_id"] == messages[1]["tool_calls"][0]["id"]
```

---

### B1 思路 + 参考答案

**思路**：用状态命名分叉；终止边写清条件，排障才有锚点。

**参考答案（ASCII + 表）**

```text
IDLE → CALLING_LLM → EXECUTING_TOOLS → CALLING_LLM → … → DONE
                 ↘ DONE（无 tool_calls）
                 ↘ FAILED（不可恢复）
任意 running → max_steps（触顶强制结束）
EXECUTING 后若重复 sig → 熔断停止
```

| 从 | 到 | 条件 |
|----|----|------|
| CALLING_LLM | DONE | 无 `tool_calls`，取 content |
| CALLING_LLM | EXECUTING_TOOLS | 存在 `tool_calls` |
| EXECUTING_TOOLS | CALLING_LLM | tool 消息已写回（含错误 JSON） |
| 运行中 | max_steps / 停止语 | `step > max_steps` |
| 运行中 | 熔断停止 | 相同 tool_calls 连续重复 |
| 任意 | FAILED | LLM 超时超限 / 策略判定不可恢复 |

---

### B2 / B3 / B4 思路 + 参考答案

**思路**：

1. FakeLLM 确定性覆盖三路径。
2. `Agent.run` = 状态推进 + 终止；模型选工具，宿主执行与停表。
3. `authorize` 夹在「解析出 name/args」与「registry 调用」之间。

**参考答案（完整可跑骨架）**

```python
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


def authorize(role: str, tool: str, args: dict[str, Any]) -> bool:
    """工具执行前 ACL；默认拒绝未知工具。"""
    _ = args
    allowed = {
        "user": {"calculator", "search", "calc"},
        "admin": {"calculator", "search", "calc"},
    }.get(role, set())
    return tool in allowed


def run_tool_call(
    tool_call: dict[str, Any],
    registry: dict[str, Callable[..., Any]],
    *,
    role: str = "user",
) -> dict[str, Any]:
    call_id = tool_call.get("id") or "missing_id"
    fn_meta = tool_call.get("function") or {}
    name = str(fn_meta.get("name") or "")
    raw = fn_meta.get("arguments")

    def tool_msg(content: str) -> dict[str, Any]:
        return {"role": "tool", "tool_call_id": call_id, "content": content}

    try:
        args = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
    except json.JSONDecodeError as exc:
        return tool_msg(
            json.dumps({"ok": False, "error": f"invalid json: {exc}"}, ensure_ascii=False)
        )

    if not authorize(role, name, args):
        return tool_msg(
            json.dumps(
                {"ok": False, "error": "unauthorized", "name": name},
                ensure_ascii=False,
            )
        )
    if name not in registry:
        return tool_msg(
            json.dumps(
                {"ok": False, "error": f"unknown tool: {name}"},
                ensure_ascii=False,
            )
        )
    try:
        result = registry[name](**args)
        return tool_msg(
            json.dumps({"ok": True, "result": result}, ensure_ascii=False, default=str)
        )
    except Exception as exc:
        return tool_msg(
            json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
        )


def build_tool_defs(tools: dict[str, Callable[..., Any]]) -> list[dict[str, Any]]:
    defs: list[dict[str, Any]] = []
    for name, fn in tools.items():
        if name in {"calculator", "calc"}:
            props, req = {"expr": {"type": "string"}}, ["expr"]
        else:
            props, req = {"query": {"type": "string"}}, ["query"]
        defs.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": (fn.__doc__ or name).strip().splitlines()[0],
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": req,
                    },
                },
            }
        )
    return defs


def calculator(expr: str) -> float:
    """计算简单算术表达式（教学用）。"""
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        raise ValueError("unsupported expr")
    return float(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307


class FakeLLM:
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = tools, kwargs
        if not messages:
            return {"role": "assistant", "content": "EMPTY"}
        last = messages[-1]
        if last.get("role") == "tool":
            return {
                "role": "assistant",
                "content": f"根据工具结果：{last.get('content')}",
            }
        text = str(last.get("content") or "")
        if "计算" in text or "算" in text:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": '{"expr":"1+2"}',
                        },
                    }
                ],
            }
        return {"role": "assistant", "content": f"ECHO:{text}"}


@dataclass
class Agent:
    llm: Any
    tools: dict[str, Callable[..., Any]]
    max_steps: int = 5
    role: str = "user"
    messages: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def run(self, user_input: str) -> str:
        self.messages = [{"role": "user", "content": user_input}]
        self.trace = []
        tool_defs = build_tool_defs(self.tools)
        last_sig: str | None = None
        repeats = 0

        for step in range(1, self.max_steps + 1):
            self.trace.append({"type": "llm", "step": step})
            assistant = self.llm.complete(self.messages, tools=tool_defs)
            if not isinstance(assistant, dict):
                raise TypeError("complete must return assistant dict, not str")
            self.messages.append(assistant)

            tool_calls = assistant.get("tool_calls") or []
            if not tool_calls:
                return str(assistant.get("content") or "")

            sig = str(
                [
                    (
                        c.get("function", {}).get("name"),
                        c.get("function", {}).get("arguments"),
                    )
                    for c in tool_calls
                ]
            )
            if sig == last_sig:
                repeats += 1
                if repeats >= 2:
                    self.trace.append(
                        {"type": "stop", "reason": "repeat_tool_calls", "step": step}
                    )
                    return "检测到重复工具调用，已停止"
            else:
                repeats = 0
                last_sig = sig

            for call in tool_calls:
                name = call.get("function", {}).get("name")
                tool_msg = run_tool_call(call, self.tools, role=self.role)
                self.messages.append(tool_msg)
                ok = True
                try:
                    ok = json.loads(tool_msg["content"]).get("ok", True)
                except json.JSONDecodeError:
                    ok = False
                self.trace.append(
                    {
                        "type": "tool_call",
                        "name": name,
                        "step": step,
                        "ok": ok,
                    }
                )

        self.trace.append({"type": "stop", "reason": "max_steps"})
        return "达到最大步数，已停止"


# ---- B2/B3 验收 ----
def test_chat_no_tool() -> None:
    agent = Agent(llm=FakeLLM(), tools={"calculator": calculator})
    out = agent.run("你好")
    assert out.startswith("ECHO:")
    assert not any(t.get("type") == "tool_call" for t in agent.trace)


def test_calc_uses_tool() -> None:
    agent = Agent(llm=FakeLLM(), tools={"calculator": calculator})
    out = agent.run("请计算 1+2")
    assert "根据工具结果" in out
    assert any(t.get("name") == "calculator" for t in agent.trace)


# ---- B4 验收 ----
def test_max_steps_or_repeat_stops() -> None:
    class AlwaysToolLLM:
        def complete(self, messages, tools=None, **kwargs):
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_x",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": '{"expr":"1+1"}',
                        },
                    }
                ],
            }

    agent = Agent(
        llm=AlwaysToolLLM(),
        tools={"calculator": calculator},
        max_steps=3,
    )
    out = agent.run("算")
    assert "停止" in out
    assert len([t for t in agent.trace if t["type"] == "llm"]) <= 3


test_chat_no_tool()
test_calc_uses_tool()
test_max_steps_or_repeat_stops()
print("B2-B4 ok")
```

---

### A1 思路 + 参考答案

**思路**：可恢复错误进 messages，让模型决策；宿主只在超限时停表。

**参考答案**

```python
def search(query: str) -> list[str]:
    """假搜索：特定 query 抛错。"""
    if query == "boom":
        raise RuntimeError("upstream 500")
    return [f"doc:{query}"]


class RecoverFakeLLM:
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = tools, kwargs
        last = messages[-1]
        if last.get("role") == "tool":
            body = str(last.get("content") or "")
            if "upstream 500" in body or '"ok": false' in body or '"ok":false' in body:
                return {
                    "role": "assistant",
                    "content": "搜索暂时不可用，请稍后再试。",
                }
            return {"role": "assistant", "content": f"找到：{body}"}
        text = str(last.get("content") or "")
        if "搜索" in text:
            q = "boom" if "爆炸" in text else "rag"
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_s",
                        "type": "function",
                        "function": {
                            "name": "search",
                            "arguments": json.dumps({"query": q}, ensure_ascii=False),
                        },
                    }
                ],
            }
        return {"role": "assistant", "content": "ECHO"}


agent = Agent(llm=RecoverFakeLLM(), tools={"search": search}, max_steps=5)
out = agent.run("请搜索爆炸新闻")
assert "不可用" in out
assert any(t.get("type") == "tool_call" for t in agent.trace)
print(out)
```

连续失败熔断（扩展片段）：在 `Agent.run` 的 tool 循环里解析 `ok`，失败则 `failures += 1`，`failures >= max_arg_failures` 时 `return "连续工具失败，已停止"`；成功则清零。

---

### A2 思路 + 参考答案

**思路**：`trace` 给人/评测看；`messages` 给模型看——两者不要混用。

**参考答案**

```python
def print_trace(agent: Agent) -> None:
    for ev in agent.trace:
        typ = ev.get("type")
        if typ == "llm":
            print(f"[step {ev.get('step')}] CALLING_LLM")
        elif typ == "tool_call":
            print(
                f"[step {ev.get('step')}] TOOL {ev.get('name')} ok={ev.get('ok')}"
            )
        elif typ == "stop":
            print(f"[stop] reason={ev.get('reason')}")
        else:
            print(ev)


agent = Agent(llm=FakeLLM(), tools={"calculator": calculator})
agent.run("请计算 1+2")
print_trace(agent)
# 期望类似：
# [step 1] CALLING_LLM
# [step 1] TOOL calculator ok=True
# [step 2] CALLING_LLM
```

---

### C1 思路 + 参考答案

**思路**：Fake 测编排正确性；真模型测任务质量。业务只依赖 Protocol。

**参考答案**

| 维度 | FakeLLM | 真模型 |
|------|---------|--------|
| 目的 | 测环、终止、恢复 | 测质量、prompt |
| CI | 必跑 | 可选 / slow |
| 输入敏感度 | 关键词 / 脚本 | 语义 |
| 失败模式 | 你写的规则 | 超时、拒识、胡调工具 |

```python
from typing import Literal, Protocol


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """返回 assistant 消息 dict（禁止 str）。"""
        ...


def build_llm(*, mode: Literal["fake", "real"], **kwargs: Any) -> LLMClient:
    if mode == "fake":
        return FakeLLM()
    # real: 接厂商 SDK；适配层把响应收成统一 assistant dict
    # return OpenAICompatClient(api_key=kwargs["api_key"], model=kwargs.get("model"))
    raise RuntimeError("real mode not configured in this exercise skeleton")


# 使用：只换 llm，不改 Agent.run
agent = Agent(llm=build_llm(mode="fake"), tools={"calculator": calculator})
print(agent.run("你好"))
```

真模型适配伪代码（注释级即可）：

```python
# class OpenAICompatClient:
#     def complete(self, messages, tools=None, **kwargs) -> dict:
#         resp = vendor.chat(messages=messages, tools=tools, ...)
#         # 把厂商对象 → {"role":"assistant","content":...,"tool_calls":...}
#         return normalize_assistant(resp)
```

---

### C2 思路 + 参考答案

**思路**：每次 `run` 重建 `messages`（上文 Agent 已这样做），或显式 `reset()`。

**参考答案**

```python
@dataclass
class AgentWithReset(Agent):
    def reset(self) -> None:
        self.messages.clear()
        self.trace.clear()


a = AgentWithReset(llm=FakeLLM(), tools={"calculator": calculator})
a.run("请计算 1+2")
assert any(m.get("role") == "tool" for m in a.messages)
a.reset()
assert a.messages == []
out = a.run("你好")
assert out.startswith("ECHO:")
assert not any(m.get("role") == "tool" for m in a.messages)
```

---

### 对照复习（书面自检）

| 手写部件 | 职责 |
|----------|------|
| `llm.complete` | 产出下一则 assistant |
| `authorize` | 执行前放行/拒绝 |
| `run_tool_call` | 解析、执行、错误 JSON |
| `Agent.run` | 状态推进与终止 |
| `trace` | 事后说清发生了什么 |

口诀：**模型负责选工具；宿主负责执行与停表；轨迹负责复盘。**
