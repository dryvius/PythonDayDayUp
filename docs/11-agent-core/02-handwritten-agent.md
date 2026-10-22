# 手写一个 Agent

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：4～7 小时（建议先用 FakeLLM 把状态机与终止条件跑绿，再换真模型）  
> 对应练习：[`exercises/11-agent-core/02-handwritten-agent.md`](../../exercises/11-agent-core/02-handwritten-agent.md)  
> 运行环境：Python ≥ 3.11 · 教学可用同步 `complete`（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）

## 本章定位

- **模块目标**：理解 Agent 本质，能手写并使用框架构建 Agent。
- **本章角色**：不靠重框架，手写 tool-loop Agent；建立状态机与错误恢复直觉。
- **价值**：框架换代你也不慌——循环本质相同。
- **产出**：可单测的 `Agent.run` + FakeLLM。
- **前置**：[`01-tool-calling.md`](./01-tool-calling.md) 的工具定义、`run_tool_call`、终止条件。
- **下一座桥**：[`03-agent-frameworks.md`](./03-agent-frameworks.md) —— 何时引入框架、如何对照源码找「等价物」。

## 学习目标（学完应能做到）

1. 分清古典 ReAct 文本协议与现代 tool_calls 循环；说清「思想同源、协议不同」。
2. 用状态机描述 Agent 运行，并指出每条终止边。
3. 实现可运行的最小 Agent（含 `messages` 与 `trace`）。
4. 用 FakeLLM 稳定测通「要工具 / 不要工具 / 工具后收尾」三条路径。
5. 加入错误恢复、重复调用熔断、`max_steps`；知道规划变体先扫盲、后扩展。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | tool loop、状态机、最小实现、终止条件 | 能手写跑通并测 |
| **建议掌握** | 错误恢复、FakeLLM、轨迹 | 更稳、可测 |
| **了解即可** | 规划算法变体 | 扫盲；下一章图编排再展开 |

---

## 1. ReAct 思想 vs 现代 tool-loop

这一节会刻意写细——后面所有「状态机、最小 Agent、FakeLLM」都建立在同一个判断上：

> **本章默认实现的是 tool-loop（结构化 tool_calls 环），不是古典 ReAct 文本协议；但思想同源。**

### 1.1 为什么要先分清两种形态？

网上文章常混用「ReAct Agent」「Tool Agent」「Function Calling Agent」。  
若不分协议，你会：

1. 在提示里硬造 `Thought:` / `Action:` 解析，却和 OpenAI/Anthropic 的 `tool_calls` 字段打架  
2. 以为「没有 Thought 散文就不是 Agent」  
3. 换框架时找不到对应物（其实都是同一条环）

古典论文 ReAct（Reason + Act）强调的是**交替推理与行动**；现代 API 把「行动」收成结构化 `tool_calls`，「推理」常被协议吸收，不必再从文本里抠。

### 1.2 古典 ReAct：文本协议

#### 为什么需要了解古典形态？

评测论文、旧教程、部分「纯文本工具」场景仍会出现。知道它，才能读懂别人的 prompt，也避免在现代 API 上重复造轮子。

#### 怎么写（协议心智）

在**提示文本**里显式交替：

```text
Thought → Action(tool) → Observation → … → Final Answer
```

模型输出往往长这样（示意）：

```text
Thought: 用户要算 1+2，我需要计算器
Action: calculator
Action Input: {"expr": "1+2"}
```

宿主解析字符串 → 调工具 → 再把 Observation 拼回提示：

```text
Observation: 3
Thought: 已经有结果了
Final Answer: 结果是 3
```

#### 跑一下（概念级：不用真模型）

```python
# 教学：用规则「假装」古典 ReAct 解析（生产勿用正则扛协议）
raw = """Thought: need calc
Action: calculator
Action Input: {"expr": "1+2"}"""

def parse_react_action(text: str) -> tuple[str, str] | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name, args = None, None
    for ln in lines:
        if ln.startswith("Action:") and "Input" not in ln:
            name = ln.split(":", 1)[1].strip()
        elif ln.startswith("Action Input:"):
            args = ln.split(":", 1)[1].strip()
    if name and args is not None:
        return name, args
    return None

print(parse_react_action(raw))  # ('calculator', '{"expr": "1+2"}')
```

你会立刻感到痛点：模型多写一行空格、改字段名、夹杂 Markdown，解析就脆。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把 Thought 当必须字段 | 现代 API 常常没有独立 Thought 文本 |
| 用脆弱正则解析 Action | 格式漂移 → 整轮失败 |
| 以为 Observation 是模型自己编的 | Observation 必须是**宿主执行工具后**写回的 |

#### 对照：文本协议 vs 结构化协议

| 维度 | 古典 ReAct（文本） | 现代 tool-loop |
| --- | --- | --- |
| 行动载体 | 提示里的 `Action` / `Action Input` 字符串 | 响应里的 `tool_calls`（结构化） |
| Thought | 常显式输出 | 常被吸收；可有 `content` 旁白 |
| 解析责任 | 你的字符串解析器 | SDK / API 字段 |
| 观测回传 | 拼进下一轮 prompt 文本 | `role: tool` + `tool_call_id` 消息 |
| 本章默认 | 了解即可 | **必掌握、动手实现** |

### 1.3 现代 tool-loop：结构化工具环

#### 为什么生产更偏 tool-loop？

1. **可校验**：`arguments` 走 JSON / Schema（上一章）  
2. **可对齐**：`tool_call_id` 把「哪次调用」与「哪条结果」钉死  
3. **可并行**：一次响应可含多个 `tool_calls`  
4. **可观测**：轨迹里记 name / id / 耗时，而不是从散文抠

#### 怎么写（环的一句话）

```text
用户 → 模型（带 tools）
       ↓ 若有 tool_calls
     宿主执行工具 → role=tool 写回 messages
       ↓
     再调模型 → … → 无 tool_calls → 最终 content
```

#### 跑一下（消息形状，不用真 LLM）

```python
messages: list[dict] = [
    {"role": "user", "content": "算一下 1+2"},
]

# 第 1 轮：模型要工具（示意）
assistant_1 = {
    "role": "assistant",
    "content": None,
    "tool_calls": [{
        "id": "call_1",
        "type": "function",
        "function": {"name": "calculator", "arguments": '{"expr": "1+2"}'},
    }],
}
messages.append(assistant_1)

# 宿主执行后回传
messages.append({
    "role": "tool",
    "tool_call_id": "call_1",
    "content": '{"ok": true, "value": 3}',
})

# 第 2 轮：模型给最终答（示意）
assistant_2 = {"role": "assistant", "content": "1+2=3"}
messages.append(assistant_2)

assert messages[-1]["content"] == "1+2=3"
print("tool-loop shape ok, steps=", len(messages))
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 有 `tool_calls` 仍把 `content` 当最终答 | 提前结束，工具白调 |
| 回传 tool 时丢掉 `tool_call_id` | 厂商拒识 / 模型对不上 |
| 把古典 `Observation:` 字符串塞进 user | 协议错位，评测与真实 API 行为不一致 |

#### 对照：一句话钉死

```text
ReAct 思想 = 交替「想」与「做」
tool-loop 实现 = 用 tool_calls + tool 消息把「做」工程化
```

下文「手写 Agent」**默认指 tool-loop**，不是古典文本协议。

---

## 2. 必掌握：状态机直觉

这一节会刻意写细——没有状态机，你会把「循环 + if」写成一锅粥，终止条件也说不清。

### 2.1 为什么要用状态机描述 Agent？

Agent.run 不是「调一次 LLM」，而是一条**带分叉与终止**的路径：

- 还要不要工具？  
- 工具失败了走哪？  
- 步数用尽怎么停？  
- 重复乱调怎么熔断？

用状态命名这些节点，排障、单测、观测（模块 12）都有锚点。

### 2.2 怎么写：状态与转移

#### 主路径

```text
IDLE → CALLING_LLM → (NEED_TOOLS → EXECUTING_TOOLS → CALLING_LLM)* → DONE
                                                      ↘ FAILED
```

读法：

1. `IDLE`：尚未开始 / 刚构造好  
2. `CALLING_LLM`：带着当前 `messages`（和 tools）请求模型  
3. 若响应含 `tool_calls` → `NEED_TOOLS` → `EXECUTING_TOOLS` → 再回 `CALLING_LLM`  
4. 若无 `tool_calls` → `DONE`（最终答）  
5. 任意不可恢复错误 / 熔断 / 触顶策略判定失败 → `FAILED`  
6. `max_steps` 用尽：可记为 `DONE`（强制结束语）或单独 `MAX_STEPS`；本章用 `status` 字段区分

#### 状态里至少有

```python
messages: list[dict]
step: int
status: str  # running | done | failed | max_steps
```

建议另存 `trace: list[dict]`（每步事件），便于评测与排障（模块 12）。

```python
from dataclasses import dataclass, field
from typing import Literal

Status = Literal["idle", "running", "done", "failed", "max_steps"]


@dataclass
class AgentState:
    messages: list[dict] = field(default_factory=list)
    step: int = 0
    status: Status = "idle"
    trace: list[dict] = field(default_factory=list)
    last_error: str | None = None
```

#### 终止边（必须能指出来）

| 从 | 到 | 条件 |
| --- | --- | --- |
| CALLING_LLM | DONE | 无 `tool_calls`，取 `content` |
| CALLING_LLM / EXECUTING_TOOLS | FAILED | LLM 超时超限、连续非法参数、策略判定不可恢复 |
| 任意运行中 | max_steps / DONE | `step > max_steps` 仍未最终答 |
| EXECUTING_TOOLS 之后 | CALLING_LLM | 工具结果已写入 messages（含错误 JSON） |
| 运行中 | FAILED / 提前 DONE | 重复相同 tool_call 熔断 |

### 2.3 跑一下：用枚举把转移「说成人话」

```python
from enum import Enum, auto


class Phase(Enum):
    IDLE = auto()
    CALLING_LLM = auto()
    EXECUTING_TOOLS = auto()
    DONE = auto()
    FAILED = auto()


def next_phase(phase: Phase, *, has_tool_calls: bool, fatal: bool) -> Phase:
    if fatal:
        return Phase.FAILED
    if phase is Phase.IDLE:
        return Phase.CALLING_LLM
    if phase is Phase.CALLING_LLM:
        return Phase.EXECUTING_TOOLS if has_tool_calls else Phase.DONE
    if phase is Phase.EXECUTING_TOOLS:
        return Phase.CALLING_LLM
    return phase


assert next_phase(Phase.IDLE, has_tool_calls=False, fatal=False) is Phase.CALLING_LLM
assert next_phase(Phase.CALLING_LLM, has_tool_calls=True, fatal=False) is Phase.EXECUTING_TOOLS
assert next_phase(Phase.CALLING_LLM, has_tool_calls=False, fatal=False) is Phase.DONE
assert next_phase(Phase.CALLING_LLM, has_tool_calls=True, fatal=True) is Phase.FAILED
print("state transitions ok")
```

真实 `Agent.run` 不必真的用 `Enum` 驱动；**心智模型**要有。实现上常用 `for step in range(...)` + `status` 字符串，与上图同构。

### 2.4 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只有「成功 / 失败」两态 | 分不清触顶、熔断、工具可恢复错误 |
| 不记 `step` | `max_steps` 无法落地；观测也没锚点 |
| `trace` 与 `messages` 混用 | 评测要事件流时只好再解析 messages，脆 |
| 工具错误直接 `FAILED` | 模型失去「改参再试」的机会（见 §5） |

### 2.5 对照：循环代码 ↔ 状态机

| 代码位置 | 状态 |
| --- | --- |
| `run` 入口、`messages.append(user)` | IDLE → running |
| `llm.complete(...)` | CALLING_LLM |
| `for call in tool_calls: run_tool_call(...)` | EXECUTING_TOOLS |
| `return content` | DONE |
| `return "达到最大步数…"` | max_steps |
| 熔断 / 不可恢复 | FAILED |

可以先记一句：

> **状态机是设计语言；`for` 循环是实现手法。** 两者说的是同一件事。

---

## 3. 必掌握：最小 Agent 实现

这一节会刻意写细——目标不是「看起来像 Agent」，而是：**一条可跑、可测、可解释终止原因的 tool-loop。**

### 3.1 为什么要先写最小实现？

框架（LangChain / LangGraph / 自研）最终都落到：

```text
调模型 →（可选）执行工具 → 写回 → 再调模型 → 停
```

你先手写一遍，读源码时才能对照「等价物」，而不是被类名淹没。

### 3.2 怎么写：依赖与骨架

依赖上一章的 `run_tool_call` / `build_tool_defs`；未知工具与非法 JSON **必须**结构化回传（见 [`01-tool-calling.md`](./01-tool-calling.md)）。

教学可用同步 `complete`；项目线偏好 `async`（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）。

下面给出教学版辅助函数（与上一章同构，便于本章自洽粘贴）：

```python
import json
from typing import Any, Callable


def build_tool_defs(tools: dict[str, Callable[..., Any]]) -> list[dict]:
    """最小示意：真实项目应用 JSON Schema / 装饰器生成。"""
    defs = []
    for name, fn in tools.items():
        defs.append({
            "type": "function",
            "function": {
                "name": name,
                "description": (fn.__doc__ or name).strip().splitlines()[0],
                "parameters": {
                    "type": "object",
                    "properties": {"expr": {"type": "string"}},
                    "required": ["expr"],
                },
            },
        })
    return defs


def run_tool_call(tool_call: dict, registry: dict[str, Callable[..., Any]]) -> dict:
    name = tool_call["function"]["name"]
    raw = tool_call["function"]["arguments"]
    call_id = tool_call["id"]
    try:
        args = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as exc:
        content = json.dumps({"ok": False, "error": f"invalid json: {exc}"}, ensure_ascii=False)
        return {"role": "tool", "tool_call_id": call_id, "content": content}
    if name not in registry:
        content = json.dumps({"ok": False, "error": f"unknown tool: {name}"}, ensure_ascii=False)
        return {"role": "tool", "tool_call_id": call_id, "content": content}
    try:
        result = registry[name](**args)
        content = json.dumps({"ok": True, "result": result}, ensure_ascii=False)
    except Exception as exc:
        content = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return {"role": "tool", "tool_call_id": call_id, "content": content}
```

#### Agent 本体

```python
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Agent:
    # 教学可用同步 complete；项目线偏好 async（见 CONVENTIONS）
    llm: Any  # complete(messages, tools=None) -> assistant_message(dict)
    tools: dict[str, Callable[..., Any]]
    max_steps: int = 5
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        tool_defs = build_tool_defs(self.tools)
        last_sig: str | None = None
        repeats = 0

        for step in range(1, self.max_steps + 1):
            self.trace.append({"type": "llm", "step": step})
            assistant = self.llm.complete(self.messages, tools=tool_defs)
            self.messages.append(assistant)

            tool_calls = assistant.get("tool_calls") or []
            if not tool_calls:
                return assistant.get("content") or ""

            # content 与 tool_calls 可同时存在：先执行工具，勿当最终答
            sig = str([
                (
                    c.get("function", {}).get("name"),
                    c.get("function", {}).get("arguments"),
                )
                for c in tool_calls
            ])
            if sig == last_sig:
                repeats += 1
                if repeats >= 2:
                    return "检测到重复工具调用，已停止"
            else:
                repeats = 0
                last_sig = sig

            for call in tool_calls:
                self.trace.append({
                    "type": "tool_call",
                    "name": call["function"]["name"],
                    "step": step,
                })
                tool_msg = run_tool_call(call, self.tools)  # 校验 + 错误 JSON
                self.messages.append(tool_msg)

        return "达到最大步数，已停止"
```

读循环时对照状态机：

```text
for step ...          → 推进 step / 仍在 running
llm.complete          → CALLING_LLM
无 tool_calls → return → DONE
有 tool_calls         → EXECUTING_TOOLS，再下一轮 CALLING_LLM
循环耗尽              → max_steps
重复 sig              → 熔断提前停（可视为 FAILED 或特殊 DONE）
```

### 3.3 跑一下：接上计算器工具

```python
def calculator(expr: str) -> float:
    """计算简单算术表达式（教学用；生产请用安全解析器）。"""
    # 极简：仅演示；勿 eval 不可信输入
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        raise ValueError("unsupported expr")
    return float(eval(expr))  # 教学演示；生产禁用裸 eval


class ScriptedLLM:
    """按轮次返回固定 assistant 消息，便于本地跑通。"""

    def __init__(self, script: list[dict]):
        self.script = list(script)
        self.i = 0

    def complete(self, messages: list[dict], tools=None) -> dict:
        if self.i >= len(self.script):
            return {"role": "assistant", "content": "(script exhausted)"}
        msg = self.script[self.i]
        self.i += 1
        return msg


llm = ScriptedLLM([
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call_1",
            "type": "function",
            "function": {"name": "calculator", "arguments": '{"expr": "1+2"}'},
        }],
    },
    {"role": "assistant", "content": "答案是 3"},
])

agent = Agent(llm=llm, tools={"calculator": calculator}, max_steps=5)
answer = agent.run("请计算 1+2")
print(answer)                 # 答案是 3
print(len(agent.trace) >= 2)  # True：至少 1 次 llm + 1 次 tool_call
```

期望轨迹形状（示意）：

```text
{"type": "llm", "step": 1}
{"type": "tool_call", "name": "calculator", "step": 1}
{"type": "llm", "step": 2}
```

### 3.4 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `messages` 跨多次 `run` 不清空也不分 session | 串话；上轮 tool 结果污染本轮 |
| 看见 `content` 非空就 `return` | 忽略同包的 `tool_calls` |
| `max_steps` 很大却无超时 | 真模型挂死、账单爆炸 |
| 在 Agent 里直接 `eval` / 执行未 ACL 工具 | 安全事故（模块 12） |
| 把 `trace` 当成给模型看的 history | 模型只应看 `messages` 协议字段 |

### 3.5 对照：最小 Agent 各部件职责

| 部件 | 职责 | 不该做的事 |
| --- | --- | --- |
| `llm.complete` | 产出下一则 assistant | 自己去调业务工具 |
| `tools` 注册表 | 名称 → 可调用实现 | 绕过校验直接 `**kwargs` |
| `run_tool_call` | 解析、校验、执行、错误 JSON | 抛到外层打断整环（可恢复错误应回传） |
| `Agent.run` | 状态推进与终止 | 把业务规则写死在 prompt 解析里 |
| `trace` | 给人 / 评测看的事件流 | 替代 `messages` |

口诀：

> **模型负责选工具；宿主负责执行与停表；轨迹负责事后说清发生了什么。**

---

## 4. 建议掌握：FakeLLM（可测）

这一节会刻意写细——没有 FakeLLM，CI 要么依赖 Key，要么红绿不定。

### 4.1 为什么必须有 FakeLLM？

1. **确定性**：关键词 / 轮次规则 → 固定 `tool_calls` 或 `content`  
2. **可覆盖路径**：要工具 / 不要工具 / 工具后收尾 / 触顶 / 非法参数  
3. **符合约定**：返回 **assistant dict**，不是 `str`（见 CONVENTIONS）  
4. **双模式**：本地与 CI 走 Fake；有 Key 再换真模型，业务代码不改

教学可用同步：

```text
def complete(messages, tools=None) -> dict
```

项目与生产偏好：

```text
async def complete(messages, tools=None, **kwargs) -> dict
```

### 4.2 怎么写：三条必测路径

```python
class FakeLLM:
    def complete(self, messages: list[dict], tools=None) -> dict:
        last = messages[-1]["content"] if messages else ""
        # 已有 tool 结果 → 给最终答
        if messages and messages[-1].get("role") == "tool":
            return {
                "role": "assistant",
                "content": f"根据工具结果：{messages[-1].get('content')}",
            }
        # 关键词触发工具
        if isinstance(last, str) and ("计算" in last or "算" in last):
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "arguments": '{"expr": "1+2"}',
                    },
                }],
            }
        return {"role": "assistant", "content": f"ECHO:{last}"}
```

原则：确定性、覆盖「要工具 / 不要工具 / 工具后收尾」三条路径。

进阶时可按「第几次 `complete`」分支（测 `max_steps`），或检查 `tools` 参数是否传入（防忘记挂 tools）。

### 4.3 跑一下：三条路径断言

```python
def calculator(expr: str) -> float:
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        raise ValueError("unsupported expr")
    return float(eval(expr))


def test_chat_no_tool():
    agent = Agent(llm=FakeLLM(), tools={"calculator": calculator})
    out = agent.run("你好")
    assert out.startswith("ECHO:")
    assert not any(t.get("type") == "tool_call" for t in agent.trace)


def test_calc_uses_tool():
    agent = Agent(llm=FakeLLM(), tools={"calculator": calculator})
    out = agent.run("请计算 1+2")
    assert "根据工具结果" in out
    assert any(t.get("name") == "calculator" for t in agent.trace)


def test_max_steps_stops():
    class AlwaysToolLLM:
        def complete(self, messages, tools=None):
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_x",
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "arguments": '{"expr": "1+1"}',
                    },
                }],
            }

    agent = Agent(llm=AlwaysToolLLM(), tools={"calculator": calculator}, max_steps=3)
    out = agent.run("算")
    # 同一 sig 会触发重复熔断，或触顶；两种都是「确定停止」
    assert "停止" in out
    assert len([t for t in agent.trace if t["type"] == "llm"]) <= 3


test_chat_no_tool()
test_calc_uses_tool()
test_max_steps_stops()
print("FakeLLM paths ok")
```

### 4.4 易错点

| 错法 | 会发生什么 |
| --- | --- |
| FakeLLM 太聪明 / 太随机 | CI 红绿不定 |
| `complete` 直接返回 `str` | 与 CONVENTIONS 及真客户端形状不一致 |
| 只测最终字符串，不测是否乱调工具 | 回归时「答对了但多调了危险工具」测不出来 |
| Fake 与真模型分支写两套 Agent | 维护成本翻倍；应只换 `llm` 注入 |
| 关键词过宽（如凡「一」都触发） | 闲聊路径误进工具环 |

### 4.5 对照：FakeLLM vs 真模型

| 维度 | FakeLLM | 真模型 |
| --- | --- | --- |
| 目的 | 测环、测终止、测恢复 | 测质量、测 prompt |
| CI | 必跑 | 可选 / 标 slow |
| 输入敏感度 | 关键词 / 脚本轮次 | 语义 |
| 失败模式 | 你写的规则 | 超时、拒识、胡调工具 |

可以先记一句：

> **FakeLLM 测的是你的编排正确性；真模型测的是任务质量。** 两者都要，但默认 CI 只绑前者。

---

## 5. 建议掌握：错误恢复

这一节会刻意写细——「工具扔异常就整 Agent 崩掉」在生产不可接受；但「无限再试一次」会烧钱。

### 5.1 为什么错误要回传给模型，而不是直接抛？

工具失败常常是**可恢复**的：

- 参数写错 → 模型改参  
- 选错工具 → 模型换工具  
- 临时超时 → 有限退避后再问模型

把错误收成 **tool 消息里的结构化 JSON**，环还能转；直接 `raise` 会打断状态机，丢掉「让模型决策」的机会。

### 5.2 怎么写：策略表

| 情况 | 策略 |
|------|------|
| 工具抛异常 | 错误 JSON 进 tool 消息，让模型改参或换工具 |
| 非法 arguments | 校验失败信息回传，计数；连续失败则 FAILED |
| LLM 超时 | 有限退避；超限 FAILED |
| 重复相同 tool_call | 熔断（见 §3） |
| 空 content 且无 tool_calls | 视为失败或重试一次 |

不要无限 extra 轮「再试一次」烧钱。

#### 连续非法参数：计数熔断示意

```python
@dataclass
class Agent:
    llm: Any
    tools: dict[str, Callable[..., Any]]
    max_steps: int = 5
    max_arg_failures: int = 2
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        tool_defs = build_tool_defs(self.tools)
        arg_failures = 0

        for step in range(1, self.max_steps + 1):
            self.trace.append({"type": "llm", "step": step})
            try:
                assistant = self.llm.complete(self.messages, tools=tool_defs)
            except TimeoutError:
                self.trace.append({"type": "error", "step": step, "error": "llm_timeout"})
                return "模型超时，已停止"

            self.messages.append(assistant)
            tool_calls = assistant.get("tool_calls") or []
            if not tool_calls:
                content = assistant.get("content")
                if content is None or content == "":
                    return "模型未返回答案，已停止"
                return content

            for call in tool_calls:
                tool_msg = run_tool_call(call, self.tools)
                self.messages.append(tool_msg)
                self.trace.append({
                    "type": "tool_call",
                    "name": call["function"]["name"],
                    "step": step,
                })
                # 粗判：错误 JSON → 累计；真实项目可解析 ok 字段
                if '"ok": false' in tool_msg["content"] or '"ok":false' in tool_msg["content"]:
                    arg_failures += 1
                    if arg_failures >= self.max_arg_failures:
                        return "连续工具失败，已停止"
                else:
                    arg_failures = 0

        return "达到最大步数，已停止"
```

要点：

- **可恢复错误** → 进 messages，继续 CALLING_LLM  
- **不可恢复 / 超限** → 明确结束语或 `status=failed`，并写 trace  
- 重复 sig 熔断与 `max_steps` 一样，属于**停表机制**，不是业务异常

### 5.3 跑一下：工具抛错 → 模型致歉收尾

```python
def search(query: str) -> list[str]:
    """假搜索：特定 query 抛错，其余返回片段。"""
    if query == "boom":
        raise RuntimeError("upstream 500")
    return [f"doc:{query}"]


class RecoverFakeLLM:
    def complete(self, messages: list[dict], tools=None) -> dict:
        last = messages[-1]
        if last.get("role") == "tool":
            body = last.get("content") or ""
            if "upstream 500" in body or '"ok": false' in body:
                return {"role": "assistant", "content": "搜索暂时不可用，请稍后再试。"}
            return {"role": "assistant", "content": f"找到：{body}"}
        if isinstance(last.get("content"), str) and "搜索" in last["content"]:
            q = "boom" if "爆炸" in last["content"] else "rag"
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_s",
                    "type": "function",
                    "function": {
                        "name": "search",
                        "arguments": json.dumps({"query": q}, ensure_ascii=False),
                    },
                }],
            }
        return {"role": "assistant", "content": "ECHO"}


# 为 search 补一个更宽的 build：演示时也可手写 tool_defs
def build_tool_defs(tools: dict[str, Callable[..., Any]]) -> list[dict]:
    out = []
    for name, fn in tools.items():
        props = {"query": {"type": "string"}} if name == "search" else {"expr": {"type": "string"}}
        req = ["query"] if name == "search" else ["expr"]
        out.append({
            "type": "function",
            "function": {
                "name": name,
                "description": (fn.__doc__ or name).strip().splitlines()[0],
                "parameters": {"type": "object", "properties": props, "required": req},
            },
        })
    return out


agent = Agent(llm=RecoverFakeLLM(), tools={"search": search}, max_steps=5)
print(agent.run("请搜索爆炸新闻"))
# 搜索暂时不可用，请稍后再试。
```

### 5.4 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 工具异常不写回，直接 raise | 环断了；用户只看到 500 |
| 错误信息对模型不友好（堆栈刷屏） | 模型改不好参；context 被污染 |
| 失败也无限重试 | 账单与延迟双爆 |
| 把「可恢复工具错误」直接标 FAILED | 浪费本可成功的下一轮 |
| 空 content 当成功 | 静默空答，评测难查 |

### 5.5 对照：错误类型与落点

| 错误类型 | 典型落点 | 谁决策下一步 |
| --- | --- | --- |
| 非法 JSON / 校验失败 | tool 消息 JSON | 模型（改参）或计数后宿主停 |
| 业务异常（上游 500） | tool 消息 JSON | 模型（换工具 / 致歉） |
| LLM 超时 | trace + 有限退避 | 宿主 |
| 重复 tool_call | 熔断返回值 | 宿主 |
| max_steps | 强制结束语 | 宿主 |
| 权限拒绝（ACL） | 错误 JSON 或直接 FAILED | 宿主策略（模块 12） |

---

## 6. 常见坑

按「出现频率 × 杀伤力」排列；写代码前扫一眼。

1. **把 `messages` 在每次 `run` 间不清空也不分 session → 串话**  
   - 做法：每次 `run` 新建 Agent，或显式 `reset()` / 传入 `session_id` 隔离存储。

2. **只测最终字符串，不测是否乱调工具**  
   - 做法：断言 `trace` 里 tool 名集合；闲聊路径 `tool_call` 计数为 0。

3. **FakeLLM 太聪明/太随机 → CI 红绿不定**  
   - 做法：关键词或脚本轮次；禁止 `random` / 真网络。

4. **`max_steps` 很大却无超时 → 挂死**  
   - 做法：步数上限 + 单次 LLM/工具超时 + 总超时三层。

5. **在 Agent 里直接执行未 ACL 的危险工具**  
   - 做法：`authorize(role, name, args)` 嵌进 `run_tool_call`（模块 12）；本章至少留扩展点。

6. **把古典 ReAct 文本解析塞进现代 tool_calls 路径**  
   - 做法：生产走结构化字段；文本协议仅作阅读/考古。

7. **`content` 与 `tool_calls` 同时存在时当最终答**  
   - 做法：有 `tool_calls` 必须先执行；`content` 可当旁白进 history。

#### 对照：坑 → 状态机症状

| 坑 | 状态机上的表现 |
| --- | --- |
| 串话 | 一进 CALLING_LLM 就带着陌生 tool 结果 |
| 无超时 | 卡在 CALLING_LLM / EXECUTING_TOOLS |
| 无熔断 | EXECUTING_TOOLS ↔ CALLING_LLM 空转 |
| 提前当最终答 | 从未进入 EXECUTING_TOOLS 却 DONE |

---

## 7. 了解即可：规划变体

先把 tool loop 做稳，再在「计划节点」上扩展（下一章图编排更合适）。

### 7.1 为什么现在只扫盲？

Plan-and-Execute、Reflection、Tree-of-Thoughts 等名字很炫，但共享底座仍是：

```text
状态 + 模型调用 +（可选）工具 + 终止条件
```

底座不稳时上规划，只会多几种「更贵的空转方式」。

### 7.2 变体地图（对照用）

| 变体 | 多出来的节点（直觉） | 和本章 tool-loop 的关系 |
| --- | --- | --- |
| **Plan-and-Execute** | 先产出计划列表，再逐步执行 | 在 CALLING_LLM 前多一个 `PLANNING`；执行仍常是 tool-loop |
| **Reflection** | 答完再自我检查一轮 | DONE 前多一次 `REFLECT` → 可能回到 CALLING_LLM |
| **Tree-of-Thoughts** | 多分支搜索/剪枝 | 状态从「单路径」变成「树」；成本陡增 |
| **古典 ReAct 文本** | Thought/Action 字符串协议 | 思想近亲；协议不同（见 §1） |

### 7.3 怎么扩展（预告，不要求本章实现）

```text
IDLE → PLAN → CALLING_LLM → (TOOLS ↔ LLM)* → REFLECT → DONE
                                      ↘ FAILED
```

落地时优先问三句：

1. 计划存在哪？（messages / 独立 `plan: list[str]` / checkpoint）  
2. 失败是重计划还是重试当前步？  
3. 预算怎么算？（计划轮 + 执行轮 + 反思轮都吃 `max_steps` / 钱）

下一章读框架源码时，对照你的手写实现逐项找「等价物」，比通读文档更快。图编排见 [`04-langgraph.md`](./04-langgraph.md)。

### 7.4 易错点（扫盲级）

| 错法 | 会发生什么 |
| --- | --- |
| 一上来就上 ToT | 费用与复杂度失控，调试更难 |
| 把「多 prompt」误当成新范式 | 常只是多了几次 CALLING_LLM |
| 计划不进 trace | 出事故时无法复盘「当时打算做什么」 |

---

## 8. 练习指引

[`exercises/11-agent-core/02-handwritten-agent.md`](../../exercises/11-agent-core/02-handwritten-agent.md)

建议顺序：

1. **B1** 画出状态机与终止边  
2. **B2～B3** FakeLLM + `Agent.run` 两条主路径  
3. **B4** `max_steps` / 熔断  
4. **A1～A2** 错误恢复与轨迹  
5. 有 Key 再做 **C1** 真模型双模式  

实战集成见 [Project 5：Tool Agent](../projects/05-tool-agent.md)。

---

## 9. 小结与下一站

### 记住这几句

1. **ReAct 是思想；tool-loop 是现代工程形态。** 本章实现后者。  
2. **状态机让终止条件可说清**；`for` + `status` + `trace` 是常见落地。  
3. **最小 Agent = LLM + tools + max_steps + 回传协议。**  
4. **FakeLLM 测编排；真模型测质量。** CI 必须 Fake 绿。  
5. **错误先结构化回传，再有界停表**；规划变体等底座稳了再说。

### 自检

- [ ] 能画出状态机并指出终止边  
- [ ] 能说明古典 ReAct 文本协议与 tool-loop 的差异  
- [ ] FakeLLM 下能测「算数走工具 / 闲聊不走工具」  
- [ ] 触顶与重复调用有确定行为  
- [ ] 工具异常会回传错误 JSON 而不是直接打崩进程  

### 下一章

[`03-agent-frameworks.md`](./03-agent-frameworks.md) —— 何时引入框架、如何读源码。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Tool Calling](./01-tool-calling.md)
- 下一章：[Agent Framework 概览](./03-agent-frameworks.md)
- 约定：[CONVENTIONS.md](../CONVENTIONS.md)
- 实战：[Project 5：Tool Agent](../projects/05-tool-agent.md)
