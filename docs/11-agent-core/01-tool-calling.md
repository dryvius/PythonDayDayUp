# Tool Calling

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（建议边写 FakeLLM 工具环边跑；无 Key 全程可离线）  
> 对应练习：[`exercises/11-agent-core/01-tool-calling.md`](../../exercises/11-agent-core/01-tool-calling.md)  
> 运行环境：Python ≥ 3.11 · 契约见 [`../CONVENTIONS.md`](../CONVENTIONS.md)

## 本章定位

- **模块目标**：理解 Agent 本质，能手写并使用框架构建 Agent。
- **本章角色**：掌握「工具定义 → 模型选择 → 执行回传 → 循环终止」；这是 Agent **行动能力**的核心协议。
- **你已具备**：模块 09 的结构化输出（`strip → loads → Pydantic`）、HTTP/异步、异常分类；模块 10 的检索直觉（工具常常是「搜一下」）。
- **前置桥**：[`../09-ai-llm/04-structured-output.md`](../09-ai-llm/04-structured-output.md) 里的「工具参数 = 结构化输出」——本章把那座桥走完：参数校验之后还要**执行、回传、再决策**。
- **产出直觉**：能手写可测的工具环骨架；下一章再收成完整 `Agent.run`。
- **目标不是**：背全厂商 SDK 字段名，或一上来接生产级 ACL / 人审（模块 12）。

## 学习目标（学完应能做到）

1. 用 JSON Schema / 函数描述定义工具，并在服务端注册真实实现。
2. 理解模型如何返回 `tool_calls`，并用 FakeLLM 稳定复现「要工具 / 不要工具 / 工具后收尾」。
3. 在服务端校验参数、执行工具，把结果写成 `role: tool` 消息写回 `messages`。
4. 设计安全的循环终止条件（无工具、`max_steps`、重复调用、超时/取消等）。
5. 能说明工具设计原则，以及并行 `tool_calls` 何时可并行、部分失败如何回传。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 工具定义、模型选工具、执行回传、终止条件 | 能实现单轮/多轮工具环，敢写校验与错误 JSON |
| **建议掌握** | 工具设计原则、并行 tool_calls 与失败语义、结果截断 | 能落地稳妥执行器，不撑爆 context |
| **了解即可** | 厂商 strict / structured tool args 差异 | 建立地图；适配层统一，服务端仍二次校验 |

---

## 1. 为什么要学（Agent 与 Tool Calling）

这一节会刻意写细——后面所有「定义、选择、执行、终止」都建立在同一个动机上：

> **没有工具的模型只能说；有工具环的模型可以做事。**

### 1.1 为什么需要 Tool Calling？

没有工具的 Chat：只能根据训练数据与当前上下文**说话**。  
有工具的模型：可以在协议允许下**行动**——搜知识库、查库、算式、调内部 API、读日历……

```text
用户 → 模型
       ↓ 决定调用 search(query=...)
     服务端执行工具
       ↓ result（结构化文本）
     模型基于结果继续推理 / 再调工具 / 给出最终答案
```

这和「让模型在散文里写 `Action: search(...)`」思想同源，但现代 API 用**结构化 `tool_calls`**，服务端解析更稳、可测、可授权。

### 1.2 没有工具环时，常见死法

| 口头说法 | 实际常指的是 | 错位后果 |
| --- | --- | --- |
| 「让模型自己算」 | 纯文本算术 | 大数/日期常错；不可审计 |
| 「把整库塞进 Prompt」 | Context 硬塞 | 贵、慢、超窗；仍不知道实时库存 |
| 「用正则从回答里抠 API 调用」 | 古典 ReAct 文本协议硬解析 | 格式一漂就炸；难测 |
| 「工具结果直接 print」 | 没写回 messages | 模型下一轮看不见结果，只能瞎编 |

### 1.3 本章要练的四段协议

1. **定义**：名称 + 描述 + 参数 Schema（给模型看的菜单）
2. **选择**：`complete(messages, tools=...)` → 可能带 `tool_calls`
3. **执行回传**：校验 → 调用 → `role: tool` + `tool_call_id` 写回历史
4. **终止**：无工具则终答；有界步数 / 熔断 / 超时则强制结束

可以先记一句：

> Tool Calling 的核心不是「调函数」，而是**把行动变成可校验、可回传、可终止的协议**。

### 1.4 对照：结构化输出 → 工具环

| 模块 09 结构化输出 | 本章 Tool Calling |
| --- | --- |
| `content` 里的 JSON | `tool_calls[].function.arguments` 里的 JSON |
| `Pydantic.validate` → 进业务 | `validate` → **执行工具** → 结果再进业务/对话 |
| 失败 repair / 重试 | 失败写成 tool 错误 JSON，让模型改参或换工具 |
| 目标：程序吃得到结构 | 目标：程序吃得到结构 **并且做成事** |

### 1.5 契约提醒：FakeLLM / LLMClient

仓库统一契约（[`CONVENTIONS.md`](../CONVENTIONS.md)）：

```text
async def complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    **kwargs,
) -> dict:  # assistant 消息：至少含 role；常有 content / tool_calls
```

要点：

- **返回 `dict`，不要返回 `str`**（纯文本取 `message["content"]`）
- 教学可用同步 `def complete`；项目线偏好 `async`
- CI / 单测必须可在 FakeLLM 下绿；真模型是可选升级
- 早期语言章的 `EchoLLM.complete(prompt) -> str` **不要命名为 FakeLLM**

### 1.6 易错点（动机层）

| 错法 | 会发生什么 |
| --- | --- |
| 把 Tool Calling 当成「多调一次 HTTP」 | 忽略 messages 历史与 `tool_call_id` 对齐，环断掉 |
| 以为模型会直接执行你的 Python 函数 | 模型只**提议**调用；执行权永远在服务端 |
| 把古典 ReAct 文本协议与现代 `tool_calls` 混为一谈 | 解析策略不同；本章默认现代协议 |
| FakeLLM 返回 `str` | 与 CONVENTIONS / 下一章 Agent 接口分裂 |

---

## 2. 必掌握：工具定义

这一节会刻意写细——定义是模型「菜单」；菜单糊，后面选择、校验、执行全糊。

### 2.1 为什么需要「名称 + 描述 + Schema」？

模型看不到你的 Python 源码。它能看到的是你塞进请求的 **tools 列表**：每个工具告诉它「叫什么、干什么、参数长什么样」。

服务端另有一份 **REGISTRY**：名字 → 真正可调用的函数。两边靠 **name 对齐**。

```text
TOOLS（给模型看）          REGISTRY（给服务端跑）
  name: search       ←→      "search": search_impl
  description...
  parameters schema
```

缺一边：模型乱点菜，或点了菜厨房没有。

### 2.2 怎么写：tools JSON（OpenAI 兼容形）

字段名因厂商略异；教学默认兼容形：

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": (
                "在知识库中搜索相关文档片段。"
                "适用于用户询问产品/制度/文档内容时；"
                "不适用于闲聊或纯算术。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索用的自然语言查询",
                    },
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "返回条数，默认 3",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calc",
            "description": "计算简单算术表达式，如 1+2*3。仅用于明确的计算请求。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expr": {"type": "string", "description": "算术表达式"},
                },
                "required": ["expr"],
            },
        },
    },
]
```

描述写什么（对齐 §6 设计原则）：

1. **做什么**：一句话能力边界  
2. **何时用 / 何时不用**：减少乱调  
3. **参数语义**：每个字段一句人话（Schema 类型不够）

### 2.3 怎么写：REGISTRY 与从函数生成定义（可选）

```python
from collections.abc import Callable
from typing import Any


def search(query: str, top_k: int = 3) -> list[str]:
    """教学假检索：确定性返回，便于单测。"""
    return [f"doc:{query}:{i}" for i in range(top_k)]


def calc(expr: str) -> dict[str, Any]:
    """教学假计算：只允许数字与 + - * / ( )。"""
    allowed = set("0123456789+-*/(). ")
    if not expr or any(ch not in allowed for ch in expr):
        raise ValueError("expr contains unsupported characters")
    # 教学场景：受控 eval；生产请用专用解析器
    value = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
    return {"expr": expr, "value": value}


REGISTRY: dict[str, Callable[..., Any]] = {
    "search": search,
    "calc": calc,
}
```

与模块 09 同源：可用 Pydantic 模型生成 `parameters`，避免「文档一套、校验一套」：

```python
from pydantic import BaseModel, Field


class SearchArgs(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


def tool_parameters_schema(model: type[BaseModel]) -> dict[str, Any]:
    """从 Pydantic 模型抽出 JSON Schema（教学简化）。"""
    return model.model_json_schema()


# 概念上挂到 tools：
# "parameters": tool_parameters_schema(SearchArgs)
```

真正挂到请求的完整 `TOOLS` 形状仍以厂商为准；**原则是：Schema 与校验同源**。

### 2.4 跑一下：定义与注册对齐

```python
assert set(REGISTRY) == {"search", "calc"}
assert all(
    t["function"]["name"] in REGISTRY for t in TOOLS
)
print(search("RAG", top_k=2))
# ['doc:RAG:0', 'doc:RAG:1']
print(calc("1+2*3"))
# {'expr': '1+2*3', 'value': 7}
```

心里检查清单：

- [ ] 每个 `TOOLS[].function.name` 都能在 `REGISTRY` 找到  
- [ ] `required` 与实现默认值一致（缺省时 Python 默认能接住）  
- [ ] `description` 写了「何时不用」，减少误调  

### 2.5 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只注册函数、不给模型 tools | 模型从不发起 tool_calls（或乱猜名字） |
| 名字 `Search` vs `search` 大小写不一致 | 未知工具；环空转 |
| description 只有「搜索」两字 | 模型在闲聊时也乱搜，浪费步数 |
| parameters 无 `required` / 无范围 | `top_k=999` 撑爆下游 |
| Schema 手写一份、Pydantic 另写一份 | 改一边漏一边，模块 09 已踩过 |

### 2.6 对照

| 概念 | 类比 |
| --- | --- |
| `TOOLS` | 餐厅菜单（给客人/模型） |
| `REGISTRY` | 后厨实现（给厨师/服务端） |
| `name` | 菜品编号（两边必须一致） |
| `parameters` Schema | 点菜规则（必选配料、份量上限） |
| 模块 09 `ToolArgs` | 同一份规则的校验器 |

---

## 3. 必掌握：模型选择工具

这一节会刻意写细——「选择」发生在模型侧；你的代码负责**把菜单递过去、把提议接稳**。

### 3.1 为什么需要把 `tools=` 放进请求？

不带 `tools`：模型通常只会吐自然语言 `content`。  
带上 `tools`：模型可以在同一轮返回结构化 `tool_calls`（也可以不调工具，直接终答）。

请求概念形（字段名因厂商而异）：

```text
complete(
  messages=[...],
  tools=TOOLS,          # 菜单
  # tool_choice="auto"  # 常见：auto / none / 强制某工具
)
```

响应可能长这样：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_1",
      "type": "function",
      "function": {
        "name": "search",
        "arguments": "{\"query\":\"RAG\",\"top_k\":3}"
      }
    }
  ]
}
```

注意：`arguments` 常常是 **JSON 字符串**，不是已经 parse 好的对象。

### 3.2 怎么写：读取 `tool_calls` 的最小辅助

```python
import json
from typing import Any


def extract_tool_calls(assistant: dict[str, Any]) -> list[dict[str, Any]]:
    """从 assistant 消息取出 tool_calls；没有则空列表。"""
    calls = assistant.get("tool_calls") or []
    if not isinstance(calls, list):
        return []
    return calls


def parse_arguments(raw: Any) -> dict[str, Any]:
    """arguments 可能是 str 或 dict；统一成 dict。非法则抛 JSONDecodeError。"""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise TypeError(f"arguments must be str|dict, got {type(raw)}")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("arguments JSON must be an object")
    return data
```

要点（先钉死）：

1. `arguments` → `json.loads`（或已是 dict 则跳过）  
2. **必须**再用 Pydantic / Schema 校验，再 `**args` 进函数  
3. 未知工具名 → 结构化错误回传或中止（见 §4），不要静默跳过  

### 3.3 怎么写：FakeLLM（关键词驱动，可测）

真模型非确定性大；教学与 CI 用规则驱动 FakeLLM（契约：`complete(messages, tools=None) -> dict`）：

```python
from typing import Any


class FakeLLM:
    """规则驱动：覆盖「要工具 / 不要工具 / 工具后收尾」。"""

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = tools, kwargs  # 教学可检查 tools 非空；此处忽略
        if not messages:
            return {"role": "assistant", "content": "EMPTY"}

        last = messages[-1]

        # 路径 C：上一轮已是 tool 结果 → 给最终答
        if last.get("role") == "tool":
            return {
                "role": "assistant",
                "content": f"根据工具结果：{last.get('content')}",
            }

        text = str(last.get("content") or "")

        # 路径 A：关键词 → 发起 tool_calls
        if "搜索" in text or "查一下" in text:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_search_1",
                        "type": "function",
                        "function": {
                            "name": "search",
                            "arguments": '{"query":"RAG","top_k":2}',
                        },
                    }
                ],
            }

        if "计算" in text or "算" in text:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_calc_1",
                        "type": "function",
                        "function": {
                            "name": "calc",
                            "arguments": '{"expr":"1+2*3"}',
                        },
                    }
                ],
            }

        # 路径 B：闲聊 → 不调工具
        return {"role": "assistant", "content": f"ECHO:{text}"}
```

异步项目线只需把 `def complete` 改成 `async def complete`，调用处加 `await`——**返回值形状不变**。

### 3.4 跑一下：三条路径

```python
llm = FakeLLM()

# B：闲聊
m1 = [{"role": "user", "content": "你好"}]
a1 = llm.complete(m1, tools=TOOLS)
assert not extract_tool_calls(a1)
print(a1["content"])  # ECHO:你好

# A：要工具
m2 = [{"role": "user", "content": "请搜索 RAG"}]
a2 = llm.complete(m2, tools=TOOLS)
calls = extract_tool_calls(a2)
assert calls and calls[0]["function"]["name"] == "search"
print(calls[0]["function"]["arguments"])

# C：工具后收尾（手写一条 tool 消息）
m3 = m2 + [
    a2,
    {
        "role": "tool",
        "tool_call_id": "call_search_1",
        "content": '["doc:RAG:0","doc:RAG:1"]',
    },
]
a3 = llm.complete(m3, tools=TOOLS)
assert not extract_tool_calls(a3)
print(a3["content"])  # 根据工具结果：...
```

### 3.5 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 直接 `**json.loads(arguments)` 不校验 | 类型错、多字段、越界；副作用工具危险 |
| 忽略 `content` 与 `tool_calls` 可同时存在 | 把旁白当终答，工具没执行（见 §5） |
| FakeLLM 太随机 / 太「聪明」 | CI 红绿不定；应关键词 + 确定性 |
| 流式未拼完 `arguments` 就 `loads` | `JSONDecodeError`；拼装见模块 09 / 02-llm-api |
| 把 `tools` 参数丢掉不传 | 真模型从不选工具；Fake 若依赖 tools 也会偏 |

### 3.6 对照：选择权在谁

| 角色 | 做什么 | 不做什么 |
| --- | --- | --- |
| 模型 | 提议 `name` + `arguments` | 不直接碰你的 DB / 文件系统 |
| 服务端 | 校验、授权、执行、写回 | 不假装「模型已经执行过了」 |
| FakeLLM | 稳定复现路径 A/B/C | 不替代生产 ACL / 人审 |

和模块 09 同一纪律：**运输层**（挂在 `tool_calls`）变了，**数据层**（仍要 validate）没变。

---

## 4. 必掌握：执行与回传

这一节会刻意写细——工具环是否「接得上」，取决于你是否按协议写回 `tool` 消息。

### 4.1 为什么需要「执行 + 写回」两步？

模型只给了提议。若你本地 `print(result)` 却不写回 `messages`，下一轮模型**看不见观察**，只能编造。

正确数据流：

```text
messages
  └─ user
  └─ assistant (含 tool_calls)     ← 先 append 提议
  └─ tool (tool_call_id=call_1)  ← 再 append 每个调用的结果
  └─ （可选更多 tool）
  └─ 再次 complete(...)          ← 模型基于结果继续
```

`tool_call_id` 把「哪一次提议」和「哪一条结果」钉在一起；并行多个调用时尤其重要。

### 4.2 怎么写：`run_tool_call`（校验 + 错误 JSON）

```python
import json
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class SearchArgs(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class CalcArgs(BaseModel):
    expr: str


ARGS_MODELS: dict[str, type[BaseModel]] = {
    "search": SearchArgs,
    "calc": CalcArgs,
}


def run_tool_call(
    tool_call: dict[str, Any],
    registry: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    """执行单次 tool_call，始终返回 role=tool 的消息。"""
    call_id = tool_call.get("id") or "missing_id"
    fn = tool_call.get("function") or {}
    name = fn.get("name") or ""
    raw = fn.get("arguments")

    def tool_msg(content: str) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": content,
        }

    if name not in registry:
        return tool_msg(
            json.dumps(
                {"ok": False, "error": "unknown_tool", "name": name},
                ensure_ascii=False,
            )
        )

    try:
        args_dict = parse_arguments(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        return tool_msg(
            json.dumps(
                {"ok": False, "error": "invalid_json", "detail": str(exc)},
                ensure_ascii=False,
            )
        )

    model = ARGS_MODELS.get(name)
    try:
        if model is not None:
            validated = model.model_validate(args_dict)
            args_dict = validated.model_dump()
        result = registry[name](**args_dict)
        content = json.dumps(
            {"ok": True, "result": result},
            ensure_ascii=False,
            default=str,
        )
    except ValidationError as exc:
        content = json.dumps(
            {
                "ok": False,
                "error": "validation_error",
                "detail": exc.errors(),
            },
            ensure_ascii=False,
            default=str,
        )
    except Exception as exc:  # 工具业务异常：回传，勿直接炸死整环
        content = json.dumps(
            {"ok": False, "error": "runtime_error", "detail": str(exc)},
            ensure_ascii=False,
        )

    return tool_msg(content)
```

设计选择（教学默认）：

| 选择 | 理由 |
| --- | --- |
| 未知工具 / 非法 JSON / 校验失败 → 仍回传 tool 消息 | 让模型有机会改参；整环不因单次坏提议崩溃 |
| `ok` + `error` 结构化 | 模型（和你的日志）能区分「改参数」vs「换工具」vs「换策略」 |
| 业务异常捕获后 JSON 化 | 与模块 06 异常分类一致：边界处翻译，不裸抛进 API |

危险工具的 ACL / 人审在模块 12；本章先养成「结构对 ≠ 允许执行」的肌肉记忆。

### 4.3 怎么写：把一轮工具结果挂回历史

```python
def append_assistant_and_tools(
    messages: list[dict[str, Any]],
    assistant: dict[str, Any],
    registry: dict[str, Callable[..., Any]],
) -> list[dict[str, Any]]:
    """append assistant，再按顺序 append 每个 tool 结果。"""
    messages.append(assistant)
    for call in extract_tool_calls(assistant):
        messages.append(run_tool_call(call, registry))
    return messages
```

顺序建议：

1. 先 append **完整** assistant（含 `tool_calls`）  
2. 再按 `tool_calls` 顺序 append 对应 tool 消息  
3. 然后再 `complete(messages, tools=...)`  

不要只 append tool、丢掉 assistant——多数厂商要求历史成对完整。

### 4.4 跑一下：单轮工具环

```python
llm = FakeLLM()
messages: list[dict[str, Any]] = [
    {"role": "user", "content": "请搜索 RAG"},
]

assistant = llm.complete(messages, tools=TOOLS)
assert extract_tool_calls(assistant)

append_assistant_and_tools(messages, assistant, REGISTRY)

# 此时最后一条应是 tool
assert messages[-1]["role"] == "tool"
print(messages[-1]["content"])
# {"ok": true, "result": ["doc:RAG:0", "doc:RAG:1"]}

final = llm.complete(messages, tools=TOOLS)
print(final["content"])
# 根据工具结果：{"ok": true, "result": [...]}
```

坏参数路径（应停在校验层，不进副作用）：

```python
bad_call = {
    "id": "call_bad",
    "type": "function",
    "function": {
        "name": "search",
        "arguments": '{"query":"RAG","top_k":999}',
    },
}
msg = run_tool_call(bad_call, REGISTRY)
payload = json.loads(msg["content"])
assert payload["ok"] is False
assert payload["error"] == "validation_error"
print("blocked before side effect")
```

### 4.5 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 执行了但不写回 messages | 模型下一轮瞎编「我已经搜过了」 |
| 写回了但 `tool_call_id` 对不上 | 厂商拒识或模型对错结果 |
| 未知工具直接 `raise` 中断整环 | 一次幻觉名字就整次请求 500 |
| 校验错误与运行时错误用同一种文案 | 模型不知道该改参还是换策略 |
| 信任厂商「保证 schema」而跳过 Pydantic | 截断、SDK bug、语义越界仍可能发生 |

### 4.6 对照：消息角色分工

| role | 谁写 | 典型字段 | 含义 |
| --- | --- | --- | --- |
| `user` | 客户端/编排 | `content` | 用户输入 |
| `assistant` | 模型 | `content` / `tool_calls` | 说话或提议行动 |
| `tool` | 服务端 | `tool_call_id` + `content` | 行动观察（给模型看） |
| `system` | 你 | `content` | 全局规则（可含工具使用策略） |

```text
【错误路径】模型提议 → 你本地执行 → 只打日志
【正确路径】模型提议 → 你校验执行 → tool 消息进历史 → 再调模型
```

---

## 5. 必掌握：循环终止条件

这一节会刻意写细——Agent 不会「自己知道该停」；**终止条件是你写的安全阀**。

### 5.1 为什么必须显式终止？

若只写「有 tool_calls 就继续」：

- 模型可能反复调同一工具（死循环）  
- 参数一直非法（烧步数）  
- 网络挂起（烧超时预算）  
- 用户已取消，你还在跑  

生产 Agent 的差异，很大一部分在**何时停、停得是否体面**。

### 5.2 怎么写：工具环伪代码

```text
for step in range(1, max_steps + 1):
  assistant = complete(messages, tools=TOOLS)
  messages.append(assistant)

  tool_calls = assistant.tool_calls or []
  if not tool_calls:
      # 无工具 → 取 content 作为最终回答
      return assistant.content

  # 注意：content 与 tool_calls 可同时存在
  # → 先执行工具，勿把 content 当最终答

  if 检测到重复相同 tool_calls:
      return "重复工具调用，已停止"

  for call in tool_calls:
      messages.append(run_tool_call(call, REGISTRY))

# 走出 for → 强制结束
return "达到最大步数，已停止"
```

最小同步实现（教学；下一章会收成 `Agent` 类）：

```python
from typing import Any


def run_tool_loop(
    llm: FakeLLM,
    user_input: str,
    *,
    tools: list[dict[str, Any]],
    registry: dict[str, Any],
    max_steps: int = 5,
) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_input},
    ]
    last_sig: str | None = None
    repeats = 0

    for _step in range(1, max_steps + 1):
        assistant = llm.complete(messages, tools=tools)
        messages.append(assistant)

        tool_calls = extract_tool_calls(assistant)
        if not tool_calls:
            return str(assistant.get("content") or "")

        # 重复调用熔断：相同 name+arguments 连续出现
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
                return "检测到重复工具调用，已停止"
        else:
            repeats = 0
            last_sig = sig

        for call in tool_calls:
            messages.append(run_tool_call(call, registry))

    return "达到最大步数，已停止"
```

### 5.3 终止条件清单（实现时要处理）

| 条件 | 典型做法 | 备注 |
| --- | --- | --- |
| 无 `tool_calls` | 返回 `content` 为终答 | 主成功路径 |
| `max_steps` | for 走完强制结束 | 必写；默认偏小更安全 |
| `content` + `tool_calls` 同时存在 | **先执行工具** | 勿过早当最终答 |
| `arguments` 非法 / 截断 JSON | 错误 JSON 回传；连续失败可 FAILED | 勿裸 `**args` |
| `finish_reason` | `length` / `content_filter` 等 | 决定重试、截断提示或失败 |
| 用户取消 / 总超时 | 协作取消、整体 deadline | 与模块 05 超时思维一致 |
| 重复相同 tool_call | 熔断 | 防死循环 |
| 危险工具 | 人工确认（模块 12） | 本章只留钩子认知 |

### 5.4 跑一下：闲聊停、搜索走环、触顶停

```python
llm = FakeLLM()

# 闲聊：一步停
print(run_tool_loop(llm, "你好", tools=TOOLS, registry=REGISTRY))
# ECHO:你好

# 搜索：工具后 FakeLLM 给终答
print(run_tool_loop(llm, "请搜索 RAG", tools=TOOLS, registry=REGISTRY))
# 根据工具结果：...

# 触顶：造一个永远要工具的 Fake（示意）
class LoopLLM:
    def complete(self, messages, tools=None, **kwargs):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_x",
                    "type": "function",
                    "function": {
                        "name": "search",
                        "arguments": '{"query":"loop","top_k":1}',
                    },
                }
            ],
        }

print(
    run_tool_loop(
        LoopLLM(),  # type: ignore[arg-type]
        "任何输入",
        tools=TOOLS,
        registry=REGISTRY,
        max_steps=3,
    )
)
# 检测到重复工具调用，已停止  （或达到最大步数）
```

### 5.5 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 看到 `content` 非空就 return | 漏执行并行/附带的 tool_calls |
| `max_steps` 不设或设成极大 | 账单与延迟双爆炸 |
| 非法 arguments 直接崩溃 | 一次坏 JSON 整次会话失败 |
| 重复调用不熔断 | 同一错误工具打成百次 |
| 只测 happy path | 生产第一次 `finish_reason=length` 就手足无措 |

### 5.6 对照：停在哪一层

```text
模型层：不再发起 tool_calls（正常终答）
编排层：max_steps / 重复熔断 / 取消 / 超时（安全阀）
产品层：危险工具人审、预算用尽（模块 12）
```

可以记一句：

> **正常停靠模型；异常与预算停靠你的循环。**

---

## 6. 建议掌握：工具设计原则

这一节会刻意写细——协议写对了，工具设计仍能决定 Agent「聪不聪明、稳不稳」。

### 6.1 为什么工具设计比「多挂几个函数」更重要？

菜单过粗：模型乱点。  
菜单过碎：步数爆炸。  
返回散文：模型下一轮难用。  
失败含糊：模型只会「再试一次同样的错」。

### 6.2 六条原则（怎么落地）

#### 1）单一职责：一个工具一件事

```text
好：search_docs / get_order / send_email
差：do_everything(action, **kwargs)
```

大杂烩工具 = Schema 难写、授权难做、失败难解释。

#### 2）描述写清边界：何时用 / 何时不用

```text
# 弱
"搜索"

# 强
"在内部知识库检索文档片段。用于产品/制度问答。
不用于闲聊、不用于下单、不用于计算。"
```

#### 3）参数少而硬：枚举、范围、默认值

```python
class SearchArgs(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)
    # 避免：filters: dict[str, Any] 这种无边界口袋
```

#### 4）返回结构化：便于模型继续推理

```python
# 更利于下一跳
{"ok": True, "result": [{"id": "d1", "snippet": "..."}]}

# 差：一大段自然语言混着日志
"我找到了一些可能相关的内容，比如说……（省略 2000 字）"
```

#### 5）失败可解释：错误信息对模型友好

```json
{"ok": false, "error": "validation_error", "detail": [{"loc": ["top_k"], "msg": "≤10"}]}
```

比 `"出错了"` 更容易让模型把 `top_k` 改小。

#### 6）无副作用或可幂等：防重试双执行

| 工具类型 | 建议 |
| --- | --- |
| 只读（search / get） | 默认可重试 |
| 写入（create / pay / send） | 业务幂等键；重试同一 `tool_call_id` 不双执行 |
| 外部有副作用 | 模块 12：ACL + 人审 + 审计 |

### 6.3 跑一下：同一能力，两种定义对比

```python
# A. 差：口袋参数
BAD_TOOL = {
    "type": "function",
    "function": {
        "name": "run",
        "description": "做事",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "payload": {"type": "object"},
            },
            "required": ["action"],
        },
    },
}

# B. 好：窄接口
GOOD_TOOL = TOOLS[0]  # 前面的 search
```

用 FakeLLM 时，好菜单更容易写出**确定性规则**（关键词 → 固定工具名）；差菜单会逼你写一堆 `if action == ...`。

### 6.4 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 工具名炫技式缩写 | 模型与人都不理解 `svc_kb_q` |
| 返回 HTML / 巨型 JSON | 撑爆 context（见 §7.5 截断） |
| 把授权写进 description 就算完 | 模型可无视；授权必须在服务端 |
| 写入工具无幂等 | 超时重试 → 双下单 |

### 6.5 对照：好工具 vs 差工具

| 维度 | 好 | 差 |
| --- | --- | --- |
| 职责 | 一事一工具 | 万能 `run` |
| 描述 | 含正/反例边界 | 「通用接口」 |
| 参数 | 少、有范围/枚举 | 无约束 `object` |
| 返回 | 短结构化 | 散文 + 日志 |
| 失败 | 可操作的 error code | `"fail"` |
| 副作用 | 幂等 / 人审 | 盲着重试 |

---

## 7. 建议掌握：并行 tool_calls 与失败语义

这一节会刻意写细——一次响应可含多个 `tool_calls`；并行能降延迟，也会放大失败与顺序问题。

### 7.1 为什么需要并行？

模型可能同时要：

```text
查天气(city=上海) + 查日历(date=今天)
```

两者无数据依赖时，串行浪费 RTT；并行可缩短「观察」就绪时间。  
但若 B 依赖 A 的结果，**不要**并行——应拆成两轮，或由模型在下一轮再调。

### 7.2 怎么写：有界并行执行

```python
import asyncio
from typing import Any


async def run_many(
    tool_calls: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    sem: asyncio.Semaphore,
) -> list[dict[str, Any]]:
    """并行执行多个 tool_calls；按原顺序返回结果，便于对齐 tool_call_id。"""

    async def one(call: dict[str, Any]) -> dict[str, Any]:
        async with sem:
            # 同步工具丢线程池，避免阻塞事件循环
            return await asyncio.to_thread(run_tool_call, call, registry)

    return list(await asyncio.gather(*(one(c) for c in tool_calls)))
```

调用侧仍先 append assistant，再按顺序 extend tool 消息：

```python
async def append_tools_parallel(
    messages: list[dict[str, Any]],
    assistant: dict[str, Any],
    registry: dict[str, Any],
    *,
    max_concurrency: int = 4,
) -> None:
    messages.append(assistant)
    calls = extract_tool_calls(assistant)
    if not calls:
        return
    sem = asyncio.Semaphore(max_concurrency)
    tool_msgs = await run_many(calls, registry, sem=sem)
    messages.extend(tool_msgs)
```

### 7.3 失败语义与依赖规则

| 点 | 做法 |
|----|------|
| 依赖顺序 | `search` 结果要喂给下一步时，**不要**与依赖它的工具并行；串行或拆两轮 |
| 部分失败 | 单个工具错误 → 仍回传该条 tool 错误 JSON；让模型决定改参/换工具，**勿整组静默丢弃** |
| 限流 | 进程内 `Semaphore` + 供应商 RPM；与模块 05/07 限流区分层级 |
| 幂等 | 重试同一 `tool_call_id` / 业务幂等键，防双执行 |
| ACL | 每个 call 都要 `authorize(role, name, args)`（模块 12） |

部分失败示意（gather 不因一个失败而丢掉另一个）：

```python
# run_tool_call 内部已吞业务异常并转为 ok=false
# 因此 gather 拿到的是「每条都有 tool 消息」，而不是 Exception

async def demo_partial_failure() -> None:
    calls = [
        {
            "id": "c1",
            "type": "function",
            "function": {
                "name": "calc",
                "arguments": '{"expr":"1+1"}',
            },
        },
        {
            "id": "c2",
            "type": "function",
            "function": {
                "name": "calc",
                "arguments": '{"expr":"1+bad"}',  # 将 runtime/校验失败
            },
        },
    ]
    sem = asyncio.Semaphore(2)
    msgs = await run_many(calls, REGISTRY, sem=sem)
    assert msgs[0]["tool_call_id"] == "c1"
    assert msgs[1]["tool_call_id"] == "c2"
    assert json.loads(msgs[0]["content"])["ok"] is True
    assert json.loads(msgs[1]["content"])["ok"] is False
    print("partial failure preserved")
```

### 7.4 跑一下：并行 vs 必须串行

```text
【可并行】
tool_calls: [weather(上海), calendar(今天)]
→ gather 同时执行 → 两条 tool 消息 → 再 complete

【必须串行 / 两轮】
第 1 轮：search(query="退货政策")
第 2 轮：模型读完片段后 → draft_reply(citation_ids=[...])
→ 不要在同一轮并行 draft（还没搜索结果）
```

### 7.5 结果截断（防撑爆 context）

工具可能返回整页 HTML、大 JSON、日志墙。整份塞进 messages 会：

- 挤掉系统提示与关键历史  
- 拉高费用与延迟  
- 让模型「找不着重点」  

```python
MAX_TOOL_CHARS = 4000


def clip_tool_content(content: str, limit: int = MAX_TOOL_CHARS) -> str:
    if len(content) <= limit:
        return content
    return content[: limit - 20] + "\n...[truncated]"


def run_tool_call_clipped(
    tool_call: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    msg = run_tool_call(tool_call, registry)
    msg["content"] = clip_tool_content(str(msg.get("content") or ""))
    return msg
```

更大结果的工程做法：

1. 工具内先摘要 / Top-K，再回传短结构  
2. 原始落盘，用 `run_id` / `artifact_id` 关联  
3. **勿**把整份原始 blob 塞进 messages  

### 7.6 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 有依赖仍 `gather` | 下游读到空/旧数据，或竞态 |
| 一个失败就取消整组且不回传 | 模型不知道发生过什么 |
| 无 Semaphore 打爆下游 | DB / 搜索集群被自己打挂 |
| 截断却不声明 `[truncated]` | 模型以为结果完整，引用幻觉 |
| 写入工具并行 + 无幂等 | 双写灾难 |

### 7.7 对照：串行环 vs 并行扇出

```text
【串行环】（默认心智）
LLM → tool_1 → LLM → tool_2 → LLM → final

【并行扇出】（同轮无依赖）
LLM → (tool_1 ∥ tool_2 ∥ tool_3) → LLM → final
```

下一章手写 Agent 默认先串行环；并行是执行器优化，不是「更 Agent」。

---

## 8. 了解即可：厂商能力差异

先建立地图，细节以你选用的 SDK 为准；**适配层 + 服务端二次校验**比背字段名重要。

### 8.1 为什么会有差异？

Tool Calling 是产品能力，不是 Python 语法。各家在下列维度不一致：

- `tools` / `functions` / `tool_choice` 字段名与枚举  
- 是否支持 **strict / structured tool arguments**（参数更贴近 Schema）  
- 不合规时是拒答、尽力生成，还是截断  
- 流式下 `tool_calls` 增量如何拼装（见模块 09 §3 / `02-llm-api`）  
- 并行 tool_calls 是否鼓励、上限多少  

### 8.2 你仍然要做的（无论厂商多「严」）

1. 服务端 Pydantic / Schema **再校验**  
2. 未知工具、非法 JSON、越权 → 结构化拒绝  
3. FakeLLM 路径保证 CI 可绿  
4. 适配层把「选工具」收成统一：`complete(messages, tools=None) -> dict`  

```python
from typing import Any, Protocol


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """返回 assistant 消息 dict。"""
        ...
```

业务只依赖 Protocol；底层可以是 OpenAI 兼容客户端或 FakeLLM。

### 8.3 易错点（地图层）

| 错法 | 会发生什么 |
| --- | --- |
| 业务代码直接依赖某厂商字段路径 | 换模型时大面积改 |
| 以为开了 strict 就永不 ValidationError | 截断、语义错误、SDK 问题仍可能发生 |
| 忽略流式拼装 | 本地非流式绿，生产流式红 |

了解即可：遇到具体厂商再查表；本章目标是**你的工具环在 FakeLLM 上先稳**。

---

## 9. 练习指引

按文档顺序动手，优先 FakeLLM，不要被 Key 堵住：

[`exercises/11-agent-core/01-tool-calling.md`](../../exercises/11-agent-core/01-tool-calling.md)

建议路径：

1. **B1～B2**：`TOOLS` + `REGISTRY` 对齐  
2. **B3**：`run_tool_call`（未知工具 / 异常 / 合法成功）  
3. **B4**：书面列出 ≥4 条终止条件  
4. **A1**：Pydantic 校验失败 → `ok: false` 回传  
5. **A2**：手写完整 messages：user → assistant(tool_calls) → tool → assistant(final)  
6. **C1～C2**（可选）：并行 gather + 部分失败；`clip_tool_content`

与模块 09 对照复习：工具参数管线 = 结构化输出管线换入口。

---

## 10. 小结与下一站

### 记住这些

1. **协议四段**：定义 → 选择 → 执行回传 → 终止。  
2. **模型只提议，服务端才执行**；`tool_call_id` 对齐观察。  
3. **`arguments` 是结构化输出**：`loads` + Pydantic，失败也要可解释回传。  
4. **终止靠你写**：无工具、`max_steps`、重复熔断、超时/取消。  
5. **并行是优化**：无依赖才 gather；部分失败仍逐条回传；大结果要截断。  
6. **FakeLLM 契约**：`complete(messages, tools=None) -> dict`；CI 必须可离线绿。

### 自检

- [ ] 能实现带校验 + 错误 JSON 回传的 `run_tool_call`  
- [ ] 能用 FakeLLM 跑通「闲聊不调工具 / 关键词调工具 / 工具后终答」  
- [ ] 知道 `content` 与 `tool_calls` 同时存在时必须先执行工具  
- [ ] 知道并行时何时必须串行、部分失败如何回传  
- [ ] 会对过大工具结果做截断  
- [ ] 能口述工具设计六条原则中的至少四条  

### 下一章

[`02-handwritten-agent.md`](./02-handwritten-agent.md) —— 把本章工具环收成完整可测的 `Agent.run`（状态机、轨迹、错误恢复）。

## 导航

- 返回模块：[README](./README.md)
- 上一模块桥：[Structured Output](../09-ai-llm/04-structured-output.md)
- 下一章：[手写一个 Agent](./02-handwritten-agent.md)
- 约定：[CONVENTIONS.md](../CONVENTIONS.md)
