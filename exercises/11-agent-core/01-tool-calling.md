# 练习：Tool Calling

> 对应文档：[`docs/11-agent-core/01-tool-calling.md`](../../docs/11-agent-core/01-tool-calling.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟  
> 运行环境：Python ≥ 3.11 · FakeLLM 契约见 [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)

## 练习说明

1. 先读完文档「必掌握」（工具定义 → 模型选择 → 执行回传 → 终止条件）再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **硬约定**（与 CONVENTIONS 一致，验收会查）：
   - `FakeLLM.complete(...)` **必须返回 assistant `dict`**（含 `role`，常有 `content` / `tool_calls`），**禁止返回 `str`**。
   - 工具执行前应调用（或预留）`authorize(role, tool, args)`；**默认拒绝未知工具**；通过后再查 `REGISTRY`。
4. 建议代码目录：

```text
playground/11-agent-core/01-tool-calling/
```

5. 全程可用 FakeLLM 离线跑通；不要求真实 API Key。先自己做完，再看文末「提示与参考答案」。

---

## 热身题（建议先做）

> 每题几分钟。用来把「消息形状」和「arguments 是 JSON 字符串」踩一遍。

### W1. assistant 消息形状

**要求**：手写两条 dict：

1. 闲聊终答：`role=assistant`，`content` 为非空字符串，**无** `tool_calls`
2. 要工具：`role=assistant`，`content` 可为 `None`，含一条 `tool_calls`（`id` / `type` / `function.name` / `function.arguments`）

**验收**：`assert isinstance(msg, dict) and msg["role"] == "assistant"`；第二条 `arguments` 是 **str**（JSON 文本），不是已 parse 的 dict。

---

### W2. `json.loads` 参数

**给定**：`raw = '{"query":"RAG","top_k":2}'`  
**要求**：解析成 dict，并用断言确认 `query` / `top_k`。  
**验收**：非法字符串（如 `"{bad"`）会抛 `json.JSONDecodeError`（可 `try/except` 演示）。

---

## 基础题（必做）

### B1. 工具 JSON Schema：`search` / `calc`

实现（或定义常量）`TOOLS: list[dict]`，OpenAI 兼容形，至少包含：

| name | 必填参数 | 说明要点 |
|------|----------|----------|
| `search` | `query` | 可选 `top_k`（整数，建议 1～10） |
| `calc` | `expr` | 简单算术表达式 |

要求：

1. 每项含 `type: "function"` 与 `function.name` / `description` / `parameters`
2. `description` 写清「何时用 / 何时不用」（至少一句边界）
3. `parameters` 为 JSON Schema object（`properties` + `required`）

**验收**：`assert {t["function"]["name"] for t in TOOLS} == {"search", "calc"}`。

---

### B2. REGISTRY 与实现对齐

实现并注册：

```python
def search(query: str, top_k: int = 3) -> list[str]:
    ...


def calc(expr: str) -> dict:
    ...
```

约定：

1. `search` 确定性返回，如 `[f"doc:{query}:{i}" for i in range(top_k)]`
2. `calc` **不要**对任意字符串裸 `eval`；可用白名单字符 + 受控计算，或查表（如 `"1+2*3" → 7`）
3. `REGISTRY: dict[str, Callable] = {"search": search, "calc": calc}`
4. 每个 `TOOLS[].function.name` 都能在 `REGISTRY` 找到

**验收**：`search("RAG", 2)` / `calc("1+2*3")` 成功；`set(REGISTRY) == {"search", "calc"}`。

---

### B3. `authorize` + `run_tool_call`（未知 / 异常 / 成功）

实现：

```python
def authorize(role: str, tool: str, args: dict) -> bool:
    """教学版：未知工具一律拒绝；可按 role 白名单扩展。"""
    ...


def run_tool_call(
    tool_call: dict,
    registry: dict,
    *,
    role: str = "user",
) -> dict:
    """始终返回 role=tool 的消息；content 为 JSON 字符串。"""
    ...
```

约定（顺序不能反）：

1. 解析 `id` / `function.name` / `function.arguments`
2. **先** `authorize(role, name, args_dict)`；拒绝则回传 `{"ok": false, "error": "unauthorized", ...}`，**不要**调用 registry
3. `name not in registry` → `{"ok": false, "error": "unknown_tool", ...}`（默认拒绝未知工具）
4. JSON 非法 / 业务异常 → 捕获后结构化错误 JSON，**勿炸死整环**
5. 成功 → `{"ok": true, "result": ...}`

**验收**：成功、未知工具、工具抛错、未授权（若你做了白名单）四条路径都能拿到 `role=tool` 消息。

---

### B4. 终止条件（书面）

对照文档 §5，用自己的话列出 **≥4 条** Agent / 工具环停止条件，并标明「正常停」还是「安全阀」。

建议至少覆盖：无 `tool_calls`、`max_steps`、重复相同调用、超时/取消（或非法参数连续失败）。

**验收**：清单可对照你后续 `run_tool_loop` / Agent 实现；不是抄标题凑数。

---

## 进阶题（建议至少做 1 题）

### A1. Pydantic `SearchArgs` + 校验失败回传

```python
from pydantic import BaseModel, Field


class SearchArgs(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)
```

要求：

1. `run_tool_call` 在执行 `search` 前用 `SearchArgs.model_validate`
2. `top_k=999` 等非法参数 → `ok=false`，`error` 建议为 `"validation_error"`，**不得**进入 `search` 函数体（可用副作用计数证明）
3. （可选）`CalcArgs` 同样接入

**验收**：坏参数路径断言 `ok is False`；合法参数仍成功。

---

### A2. 多步 messages 模拟 + FakeLLM 三路径

实现关键词驱动 `FakeLLM`：

```python
class FakeLLM:
    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:  # 必须是 assistant dict，禁止 str
        ...
```

路径（确定性）：

| 路径 | 触发 | 期望 |
|------|------|------|
| A 要工具 | 用户含「搜索」或「查一下」 | 返回 `tool_calls`（search） |
| B 不要工具 | 闲聊 | 仅 `content`，无 tool_calls |
| C 工具后收尾 | 上一条 `role=="tool"` | 最终自然语言 `content` |

再手写完整历史跑通：

```text
user → assistant(tool_calls) → tool → assistant(final)
```

可用 `append_assistant_and_tools` 或手写 append。

**验收**：三条路径断言通过；`complete` 返回值 `isinstance(..., dict)`。

---

## 挑战题（可选）

### C1. 并行 `tool_calls`：一失败一成功

用 `asyncio.gather`（同步工具可 `asyncio.to_thread`）并行执行同一轮多个 `tool_calls`：

1. 一条合法 `calc`（成功）
2. 一条非法 / 会失败的 `calc`（或未知工具）

要求：

- 按**原顺序**得到两条 `role=tool` 消息（`tool_call_id` 对齐）
- 一个失败**不能**丢掉另一个成功结果
- 执行前仍走 `authorize`（可在 `run_tool_call` 内统一做）

**验收**：`json.loads(msgs[0]["content"])["ok"] is True` 且另一条 `ok is False`。

---

### C2. `clip_tool_content` 防撑爆 context

```python
MAX_TOOL_CHARS = 4000

def clip_tool_content(content: str, limit: int = MAX_TOOL_CHARS) -> str:
    ...
```

要求：超长时截断并带 `"...[truncated]"`（或等价标记）；在 `run_tool_call` 之后对 `content` 裁剪；用超长假结果断言 `len(content) <= limit`。

**验收**：短内容不变；长内容被截断且声明 truncated。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W2 先做完
- [ ] **通过线**：B1～B4 全部完成；`run_tool_call` 含 authorize / 未知工具拒绝
- [ ] FakeLLM（若做了 A2）返回 dict，覆盖要工具 / 不要工具 / 工具后收尾
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2
- [ ] 能口述：模型只提议、服务端才执行；`tool_call_id` 为何要对齐

---

## 提示与参考答案（先做题再看）

> 每题先给**思路**，再给带注释的**参考实现**。答案不是唯一写法，能通过验收、意图清晰即可。

---

### W1 思路 + 参考答案

**思路**：终答只有 `content`；要工具时把行动放进 `tool_calls`，`arguments` 保持 JSON 字符串以便模拟真实 API。

**参考答案**

```python
chat_msg = {
    "role": "assistant",
    "content": "你好，我是助手。",
}

tool_msg = {
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "search",
                "arguments": '{"query":"RAG","top_k":2}',
            },
        }
    ],
}

assert chat_msg["role"] == "assistant"
assert isinstance(tool_msg["tool_calls"][0]["function"]["arguments"], str)
```

---

### W2 思路 + 参考答案

**思路**：`arguments` 运输层常是 str；业务层先 `loads` 再校验。

**参考答案**

```python
import json

raw = '{"query":"RAG","top_k":2}'
args = json.loads(raw)
assert args["query"] == "RAG" and args["top_k"] == 2

try:
    json.loads("{bad")
    raise AssertionError("should fail")
except json.JSONDecodeError:
    pass
```

---

### B1 思路 + 参考答案

**思路**：`TOOLS` 是给模型看的菜单；名字必须与后厨 `REGISTRY` 对齐；描述写边界可减少乱调。

**参考答案**

```python
TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": (
                "在知识库中搜索文档片段。"
                "用于产品/制度问答；不用于闲聊或纯算术。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索用自然语言查询",
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
            "description": "计算简单算术表达式（如 1+2*3）。仅用于明确计算请求。",
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

assert {t["function"]["name"] for t in TOOLS} == {"search", "calc"}
```

---

### B2 思路 + 参考答案

**思路**：实现要确定性，便于单测；`calc` 用白名单或查表，养成「不瞎 eval」习惯。

**参考答案**

```python
from collections.abc import Callable
from typing import Any


def search(query: str, top_k: int = 3) -> list[str]:
    """教学假检索：确定性返回。"""
    return [f"doc:{query}:{i}" for i in range(top_k)]


def calc(expr: str) -> dict[str, Any]:
    """教学假计算：白名单字符 + 受控 eval；生产请用专用解析器。"""
    allowed = set("0123456789+-*/(). ")
    if not expr or any(ch not in allowed for ch in expr):
        raise ValueError("expr contains unsupported characters")
    value = eval(expr, {"__builtins__": {}}, {})  # noqa: S307  # 仅教学
    return {"expr": expr, "value": value}


REGISTRY: dict[str, Callable[..., Any]] = {
    "search": search,
    "calc": calc,
}

assert set(REGISTRY) == {"search", "calc"}
assert all(t["function"]["name"] in REGISTRY for t in TOOLS)
assert search("RAG", 2) == ["doc:RAG:0", "doc:RAG:1"]
assert calc("1+2*3")["value"] == 7
```

---

### B3 思路 + 参考答案

**思路**：

1. **授权在注册表调用之前**——想调用 ≠ 允许执行。
2. 未知工具、非法 JSON、业务异常一律变成 tool 消息里的错误 JSON，让环能继续。
3. `authorize` 默认：工具名必须在允许集合内；本章允许集合可等于 `registry` 的 key。

**参考答案**

```python
import json
from collections.abc import Callable
from typing import Any


def parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise TypeError(f"arguments must be str|dict, got {type(raw)}")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("arguments JSON must be an object")
    return data


def authorize(role: str, tool: str, args: dict[str, Any]) -> bool:
    """
    教学版 ACL：默认拒绝未知工具。
    扩展点：可按 role 限制危险工具（模块 12 会加深）。
    """
    _ = args  # 参数级规则可在此扩展
    allowed_by_role: dict[str, set[str]] = {
        "user": {"search", "calc"},
        "admin": {"search", "calc"},
        "guest": {"search"},  # guest 不能算数，演示授权拒绝
    }
    allowed = allowed_by_role.get(role, set())
    return tool in allowed


def run_tool_call(
    tool_call: dict[str, Any],
    registry: dict[str, Callable[..., Any]],
    *,
    role: str = "user",
) -> dict[str, Any]:
    """执行单次 tool_call；始终返回 role=tool 消息。"""
    call_id = tool_call.get("id") or "missing_id"
    fn_meta = tool_call.get("function") or {}
    name = str(fn_meta.get("name") or "")
    raw = fn_meta.get("arguments")

    def tool_msg(content: str) -> dict[str, Any]:
        return {"role": "tool", "tool_call_id": call_id, "content": content}

    # 1) 先尽量解析 args，供 authorize 做参数级判断
    try:
        args_dict = parse_arguments(raw) if raw is not None else {}
    except (json.JSONDecodeError, TypeError) as exc:
        return tool_msg(
            json.dumps(
                {"ok": False, "error": "invalid_json", "detail": str(exc)},
                ensure_ascii=False,
            )
        )

    # 2) 授权：在 registry 调用之前
    if not authorize(role, name, args_dict):
        return tool_msg(
            json.dumps(
                {
                    "ok": False,
                    "error": "unauthorized",
                    "name": name,
                    "role": role,
                },
                ensure_ascii=False,
            )
        )

    # 3) 未知工具（双重保险：authorize 已拒，registry 再拒）
    if name not in registry:
        return tool_msg(
            json.dumps(
                {"ok": False, "error": "unknown_tool", "name": name},
                ensure_ascii=False,
            )
        )

    # 4) 执行
    try:
        result = registry[name](**args_dict)
        return tool_msg(
            json.dumps(
                {"ok": True, "result": result},
                ensure_ascii=False,
                default=str,
            )
        )
    except Exception as exc:
        return tool_msg(
            json.dumps(
                {"ok": False, "error": "runtime_error", "detail": str(exc)},
                ensure_ascii=False,
            )
        )


# ---- 验收 ----
ok_call = {
    "id": "c1",
    "type": "function",
    "function": {
        "name": "search",
        "arguments": '{"query":"RAG","top_k":2}',
    },
}
msg = run_tool_call(ok_call, REGISTRY, role="user")
assert msg["role"] == "tool"
assert json.loads(msg["content"])["ok"] is True

unknown = {
    "id": "c2",
    "type": "function",
    "function": {"name": "browse", "arguments": "{}"},
}
assert json.loads(run_tool_call(unknown, REGISTRY)["content"])["error"] in {
    "unauthorized",
    "unknown_tool",
}

boom = {
    "id": "c3",
    "type": "function",
    "function": {
        "name": "calc",
        "arguments": '{"expr":"1+bad"}',
    },
}
assert json.loads(run_tool_call(boom, REGISTRY)["content"])["ok"] is False

# guest 无 calc 权限
denied = run_tool_call(boom, REGISTRY, role="guest")
assert json.loads(denied["content"])["error"] == "unauthorized"
```

---

### B4 思路 + 参考答案

**思路**：正常停靠模型（不再要工具）；异常与预算停靠你的循环。

**参考答案（书面示例）**

| # | 条件 | 类型 |
|---|------|------|
| 1 | 响应无 `tool_calls`，取 `content` 为终答 | 正常停 |
| 2 | `step` 达到 `max_steps` 仍未终答 | 安全阀 |
| 3 | 连续重复相同 `name+arguments` | 安全阀（熔断） |
| 4 | 用户取消 / 总超时 / LLM 超时超限 | 安全阀 |
| 5 | （加分）连续非法参数超过阈值 | 安全阀 |

补充纪律：`content` 与 `tool_calls` 同时存在时，**先执行工具**，勿把 `content` 当最终答。

---

### A1 思路 + 参考答案

**思路**：Schema 与校验同源；校验失败在副作用之前拦下，并给模型可操作的 `validation_error`。

**参考答案**

```python
from pydantic import BaseModel, Field, ValidationError

# 复用 B2 的 search / REGISTRY；这里给 search 加调用计数
_search_hits = {"n": 0}
_orig_search = REGISTRY["search"]


def search_counted(query: str, top_k: int = 3) -> list[str]:
    _search_hits["n"] += 1
    return _orig_search(query, top_k)


REGISTRY["search"] = search_counted


class SearchArgs(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


ARGS_MODELS: dict[str, type[BaseModel]] = {"search": SearchArgs}


def run_tool_call_validated(
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
        args_dict = parse_arguments(raw) if raw is not None else {}
    except (json.JSONDecodeError, TypeError) as exc:
        return tool_msg(
            json.dumps({"ok": False, "error": "invalid_json", "detail": str(exc)})
        )

    if not authorize(role, name, args_dict):
        return tool_msg(
            json.dumps({"ok": False, "error": "unauthorized", "name": name})
        )
    if name not in registry:
        return tool_msg(
            json.dumps({"ok": False, "error": "unknown_tool", "name": name})
        )

    model = ARGS_MODELS.get(name)
    try:
        if model is not None:
            args_dict = model.model_validate(args_dict).model_dump()
        result = registry[name](**args_dict)
        return tool_msg(
            json.dumps({"ok": True, "result": result}, ensure_ascii=False, default=str)
        )
    except ValidationError as exc:
        return tool_msg(
            json.dumps(
                {
                    "ok": False,
                    "error": "validation_error",
                    "detail": exc.errors(),
                },
                ensure_ascii=False,
                default=str,
            )
        )
    except Exception as exc:
        return tool_msg(
            json.dumps({"ok": False, "error": "runtime_error", "detail": str(exc)})
        )


_search_hits["n"] = 0
bad = {
    "id": "bad",
    "type": "function",
    "function": {
        "name": "search",
        "arguments": '{"query":"RAG","top_k":999}',
    },
}
payload = json.loads(run_tool_call_validated(bad, REGISTRY)["content"])
assert payload["ok"] is False and payload["error"] == "validation_error"
assert _search_hits["n"] == 0  # 未进入工具函数体
```

---

### A2 思路 + 参考答案

**思路**：FakeLLM 用关键词 +「上一条是否为 tool」覆盖三路径；返回值永远是 assistant dict。

**参考答案**

```python
from typing import Any


def extract_tool_calls(assistant: dict[str, Any]) -> list[dict[str, Any]]:
    calls = assistant.get("tool_calls") or []
    return calls if isinstance(calls, list) else []


class FakeLLM:
    """规则驱动：要工具 / 不要工具 / 工具后收尾。"""

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
        return {"role": "assistant", "content": f"ECHO:{text}"}


def append_assistant_and_tools(
    messages: list[dict[str, Any]],
    assistant: dict[str, Any],
    registry: dict[str, Callable[..., Any]],
) -> None:
    messages.append(assistant)
    for call in extract_tool_calls(assistant):
        # 若已接 A1，可换成 run_tool_call_validated
        messages.append(run_tool_call(call, registry, role="user"))


llm = FakeLLM()

# B：闲聊
a1 = llm.complete([{"role": "user", "content": "你好"}], tools=TOOLS)
assert isinstance(a1, dict) and not extract_tool_calls(a1)

# A + C：要工具 → 执行 → 收尾
messages: list[dict[str, Any]] = [{"role": "user", "content": "请搜索 RAG"}]
a2 = llm.complete(messages, tools=TOOLS)
assert extract_tool_calls(a2)
append_assistant_and_tools(messages, a2, REGISTRY)
assert messages[-1]["role"] == "tool"
final = llm.complete(messages, tools=TOOLS)
assert "根据工具结果" in str(final.get("content"))
assert not extract_tool_calls(final)
```

---

### C1 思路 + 参考答案

**思路**：`run_tool_call` 内部已把业务失败收成消息，故 `gather` 不会因一个失败丢掉另一个；按输入顺序返回以对齐 `tool_call_id`。

**参考答案**

```python
import asyncio


async def run_many(
    tool_calls: list[dict[str, Any]],
    registry: dict[str, Callable[..., Any]],
    *,
    sem: asyncio.Semaphore,
) -> list[dict[str, Any]]:
    async def one(call: dict[str, Any]) -> dict[str, Any]:
        async with sem:
            return await asyncio.to_thread(run_tool_call, call, registry)

    return list(await asyncio.gather(*(one(c) for c in tool_calls)))


async def demo_partial_failure() -> None:
    calls = [
        {
            "id": "c1",
            "type": "function",
            "function": {"name": "calc", "arguments": '{"expr":"1+1"}'},
        },
        {
            "id": "c2",
            "type": "function",
            "function": {"name": "calc", "arguments": '{"expr":"1+bad"}'},
        },
    ]
    msgs = await run_many(calls, REGISTRY, sem=asyncio.Semaphore(2))
    assert msgs[0]["tool_call_id"] == "c1"
    assert msgs[1]["tool_call_id"] == "c2"
    assert json.loads(msgs[0]["content"])["ok"] is True
    assert json.loads(msgs[1]["content"])["ok"] is False
    print("partial failure preserved")


asyncio.run(demo_partial_failure())
```

---

### C2 思路 + 参考答案

**思路**：截断要声明 `[truncated]`，避免模型以为结果完整而幻觉引用。

**参考答案**

```python
MAX_TOOL_CHARS = 4000


def clip_tool_content(content: str, limit: int = MAX_TOOL_CHARS) -> str:
    if len(content) <= limit:
        return content
    marker = "\n...[truncated]"
    keep = max(0, limit - len(marker))
    return content[:keep] + marker


def run_tool_call_clipped(
    tool_call: dict[str, Any],
    registry: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    msg = run_tool_call(tool_call, registry)
    msg["content"] = clip_tool_content(str(msg.get("content") or ""))
    return msg


short = clip_tool_content("hello", 100)
assert short == "hello"

long = "x" * 5000
clipped = clip_tool_content(long, 100)
assert len(clipped) <= 100
assert "[truncated]" in clipped
```

> 把 B～A 串成 `run_tool_loop` 的完整形态见下一章 [`02-handwritten-agent.md`](./02-handwritten-agent.md) 的 `Agent.run`。
