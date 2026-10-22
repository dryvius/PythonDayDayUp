# 练习：LLM API 实战

> 对应文档：[`docs/09-ai-llm/02-llm-api.md`](../../docs/09-ai-llm/02-llm-api.md)  
> 状态：`已完成出题`  
> 建议用时：70～110 分钟（含热身）  
> Python：`≥ 3.11`

## 练习说明

1. 先读完文档「必掌握」：Chat API 骨架、关键参数、流式拼装、错误与重试；并对照 [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **无 API Key 时必须用 `FakeLLM`**；有 Key 可升级真调用。契约强制：

```text
async def complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    **kwargs,
) -> dict  # assistant 消息：至少含 role；常有 content / tool_calls
```

4. **禁止**让 `FakeLLM.complete` / `async complete` 返回 `str`。纯文本请用 `text_of(message)` 从 dict 取出。早期回声教学若返回 `str`，类名用 `EchoLLM`，**勿命名为 FakeLLM**。
5. 建议代码目录：

```text
playground/09-ai-llm/02-llm-api/
```

可选自测入口（自行创建）：

```bash
python playground/09-ai-llm/02-llm-api/test_client.py
```

6. 先自己做完，再看文末「提示与参考答案」。涉及 Key 的打印务必脱敏。

---

## 热身题（建议先做）

### W1. 认出 assistant 消息

**给定**：

```python
envelope = {
    "choices": [
        {"message": {"role": "assistant", "content": "你好"}}
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 2},
}
```

**要求**：写出业务层真正应追加进 `messages` 历史的对象（哪一层？什么结构？）。

**验收**：能指出是 `choices[0].message`（dict），不是整个 envelope，也不是裸 `"你好"` 字符串。

---

### W2. 角色四件套

**给定**：`system` / `user` / `assistant` / `tool`。

**要求**：用表格写「谁在说话 + 常见用途」，各一行。

**验收**：四行齐全；`tool` 标明是工具执行结果回灌，不是终端用户。

---

### W3. EchoLLM ≠ FakeLLM

**给定**：课程约定。

**要求**：用两行对比：`EchoLLM.complete(prompt) -> str` vs `FakeLLM.complete(messages, ...) -> dict`。

**验收**：明确 FakeLLM **禁止**返回 `str`。

---

## 基础题（必做）

### B1. `build_chat`：构造 messages

**给定**：system 与 user 两段文本。

**要求**：实现：

```python
def build_chat(system: str, user: str) -> list[dict]:
    """返回 [system_msg, user_msg]，role/content 齐全。"""
    ...
```

**验收**：

```python
msgs = build_chat("简洁回答", "用一句话解释 RAG")
assert msgs == [
    {"role": "system", "content": "简洁回答"},
    {"role": "user", "content": "用一句话解释 RAG"},
]
assert all(set(m) >= {"role", "content"} for m in msgs)
```

---

### B2. `FakeLLM.async complete` → dict + `text_of`

**给定**：CONVENTIONS 契约。

**要求**：

1. 实现 `class FakeLLM`，提供：

```python
async def complete(
    self,
    messages: list[dict],
    tools: list[dict] | None = None,
    **kwargs,
) -> dict:
    ...
```

2. Fake 规则：找到**最后一条** `role == "user"` 的 `content`，返回：

```python
{"role": "assistant", "content": "ECHO: " + last_user_content}
```

若没有 user，则 `content` 用 `"ECHO:"`（或你文档化的空回声约定，需在注释写明）。

3. 另写：

```python
def text_of(message: dict) -> str:
    """从 assistant dict 取文本；content 为 None 时返回空串。"""
    ...
```

**验收**：

```python
import asyncio

async def _check() -> None:
    client = FakeLLM()
    msg = await client.complete(build_chat("sys", "hello"))
    assert isinstance(msg, dict)
    assert msg["role"] == "assistant"
    assert msg["content"] == "ECHO: hello"
    assert text_of(msg) == "ECHO: hello"
    assert text_of({"role": "assistant", "content": None}) == ""
    # 禁止返回 str
    assert not isinstance(msg, str)

asyncio.run(_check())
```

---

### B3. temperature 与 `max_output_tokens`（论述 + 可选假实验）

**给定**：任务「从文本提取订单号」，样例句：`订单 ORD-2024-001 已发货`。

**要求**：

1. 书面对比 `temperature=0` 与 `temperature=0.9` 在该任务上的**稳定性**差异（可假想；有 API 可实测各 3 次）。
2. 说明厂商字段可能是 `max_tokens` / `max_completion_tokens` 等，为何适配层要统一成 **`max_output_tokens`**。
3. （可选代码）实现 `apply_sampling(payload, *, temperature, max_output_tokens, max_tokens_field="max_tokens") -> dict`，把统一旋钮写入 payload。

**验收（checklist）**：

- [ ] 写明：抽取/工具参数宜低温；高温更易格式漂移
- [ ] 写明：输出上限字段名差异应在适配层翻译
- [ ] 若实现了 `apply_sampling`，下列断言通过：

```python
p = apply_sampling({"model": "x"}, temperature=0, max_output_tokens=256)
assert p["temperature"] == 0
assert p["max_tokens"] == 256
```

---

### B4. `should_retry`：有纪律的重试判断

**给定**：失败谱——401 / 429 / 503 / timeout / 400。

**要求**：实现：

```python
def should_retry(
    status_code: int | None,
    exc_type: str | None = None,
) -> bool:
    """
    status_code: HTTP 状态；网络超时等可传 None。
    exc_type: 可选，如 "TimeoutError" / "ConnectError"。
    """
    ...
```

约定（与正文一致即可，需在注释写清）：

- `401` / `400`：**不重试**（改 Key / 改请求）
- `429` / `503` / `502`：**可重试**
- `exc_type` 含超时 / 连接类：**可重试**
- 未知组合默认保守：可不重试或按你文档化策略

**验收**：

```python
assert should_retry(401) is False
assert should_retry(400) is False
assert should_retry(429) is True
assert should_retry(503) is True
assert should_retry(None, "TimeoutError") is True
assert should_retry(200) is False
```

---

## 进阶题（建议）

### A1. SSE 文本流式拼装

**给定**：OpenAI 兼容 SSE：`data: {...}`，结束 `data: [DONE]`。

**要求**：

1. 实现 `parse_sse_data_line(line: str) -> dict | None`  
   - 空行 / `:` 注释 → `None`  
   - `data: [DONE]` → `{"done": True}`  
   - 其它 `data: ...` → `json.loads` 后的 dict  
2. 用**异步生成器**模拟若干 delta 行 + `[DONE]`  
3. 消费者拼出完整字符串并断言

**验收**：

```python
import asyncio
import json
from collections.abc import AsyncIterator


async def fake_sse_lines() -> AsyncIterator[str]:
    chunks = ["你", "好", "，", "世界"]
    for c in chunks:
        payload = {"choices": [{"delta": {"content": c}}]}
        yield f"data: {json.dumps(payload, ensure_ascii=False)}"
    yield "data: [DONE]"


async def collect_text() -> str:
    parts: list[str] = []
    async for line in fake_sse_lines():
        event = parse_sse_data_line(line)
        if event is None:
            continue
        if event.get("done"):
            break
        delta = event["choices"][0].get("delta") or {}
        piece = delta.get("content") or ""
        if piece:
            parts.append(piece)
    return "".join(parts)


assert parse_sse_data_line(": ping") is None
assert parse_sse_data_line("data: [DONE]") == {"done": True}
assert asyncio.run(collect_text()) == "你好，世界"
```

---

### A2. `merge_tool_call_delta`：流式 tool_calls 拼装

**给定**：同一 `index` 上 `arguments` 拆成多段 delta。

**要求**：实现：

```python
def empty_assistant() -> dict: ...

def merge_tool_call_delta(assistant: dict, tc_delta: dict) -> None:
    """按 index 归并 id / name / arguments（arguments 字符串追加）。"""
    ...
```

用分片 delta 拼出完整 `tool_calls`，再 `json.loads(arguments)`。

**验收**：

```python
import json

assistant = empty_assistant()
merge_tool_call_delta(
    assistant,
    {
        "index": 0,
        "id": "call_1",
        "function": {"name": "search", "arguments": ""},
    },
)
merge_tool_call_delta(
    assistant,
    {"index": 0, "function": {"arguments": '{"q":"RA'}},
)
merge_tool_call_delta(
    assistant,
    {"index": 0, "function": {"arguments": 'G","k":3}'}},
)

args = json.loads(assistant["tool_calls"][0]["function"]["arguments"])
assert assistant["tool_calls"][0]["function"]["name"] == "search"
assert args == {"q": "RAG", "k": 3}
```

---

### A3. `LLMClient` Protocol 适配

**给定**：业务不应感知真假供应商。

**要求**：

1. 定义 `Protocol`：

```python
from typing import Protocol


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict: ...
```

2. 提供 `FakeLLM` 与另一种实现（例如 `StaticLLM`：固定返回某句；或包装后的「大写回声」）。
3. 业务函数只依赖 Protocol：

```python
async def ask(client: LLMClient, question: str) -> str:
    msg = await client.complete(build_chat("简洁", question))
    return text_of(msg)
```

**验收**：

```python
import asyncio

async def _check() -> None:
    assert await ask(FakeLLM(), "ping") == "ECHO: ping"
    # 第二种实现：自行写 StaticLLM / UpperEchoLLM 等
    # assert await ask(other, "ping") 通过你的约定

asyncio.run(_check())
```

- [ ] 两套实现均可代入 `ask`
- [ ] `complete` 均返回 dict

---

## 挑战题（可选）

### C1. 可选真实 httpx 调用（注意脱敏）

**给定**：你有可用的 Chat Completions 兼容端点与 API Key（若无 Key，本题跳过，不扣通过线）。

**要求**：

1. 用 `httpx`（同步或异步）打一次**非流式** Chat Completions。  
2. 打印：耗时；若有 `usage` 则打印；**Content 可截断打印**。  
3. **脱敏**：禁止打印完整 `Authorization` / API Key；日志里 Key 用 `sk-***` 或根本不打印。  
4. （可选）再打一次 `stream=True`，拼装后与非流式 `content` 对比是否一致（允许空白差异）。

建议把 Key 放环境变量，例如 `LLM_API_KEY`，代码里 `os.environ[...]`。

**验收（checklist）**：

- [ ] 非流式调用成功，拿到 assistant `content`
- [ ] 输出中无完整 Key
- [ ] （可选）流式拼装结果与非流式一致
- [ ] 解析路径取的是 message dict，而不是把 envelope 当消息

---

## 验收标准（本章通过线）

- [ ] （建议）热身 W1～W3
- [ ] **通过线**：B1～B4 完成；`FakeLLM.complete` 返回 **dict** 而非裸 `str`
- [ ] `text_of` 与 `should_retry` 断言通过
- [ ] （建议）A1 或 A2 至少 1 题；A3 强烈建议
- [ ] （可选）C1 真调用且脱敏

---

## 提示与参考答案（先做题再看）

> 每题先给**思路**，再给带注释的完整参考实现。可按你的目录拆文件，但契约不要歪。

W1 参考答案

业务追加的是 `envelope["choices"][0]["message"]`，即  
`{"role": "assistant", "content": "你好"}`。  
`usage` 留给计费/观测，不要和消息历史搅在一起。

---

W2 参考答案

| role | 谁在说话 | 常见用途 |
|------|----------|----------|
| system | 开发者 | 人设、硬约束、输出格式 |
| user | 终端用户 / 调用方 | 本轮问题 |
| assistant | 模型 | 历史回复；可含 tool_calls |
| tool | 工具执行结果 | 把工具输出塞回上下文 |

---

W3 参考答案

- `EchoLLM`：教学用，`complete(prompt: str) -> str`  
- `FakeLLM`：模块 09+ 契约，`async complete(messages, ...) -> dict`  
- FakeLLM **禁止**返回 `str`；取文本用 `text_of`

---

B1 思路 + 参考答案

**思路**：最小可用就是两条消息；别把 system/user 揉成一个字符串。

**参考答案**

```python
def build_chat(system: str, user: str) -> list[dict]:
    """最小可用：system + user。后续可追加 assistant / tool。"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


msgs = build_chat("简洁回答", "用一句话解释 RAG")
assert msgs[0]["role"] == "system"
assert msgs[1]["content"] == "用一句话解释 RAG"
```

---

B2 思路 + 参考答案

**思路**：从后往前找最后一条 user；返回值必须是 assistant dict。

**参考答案**

```python
class FakeLLM:
    """规则驱动假客户端；complete 必须返回 assistant dict。"""

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        last = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last = m.get("content") or ""
                break
        # 无 user 时约定空回声前缀（写进注释，避免隐式魔法）
        return {"role": "assistant", "content": f"ECHO: {last}".rstrip() if last else "ECHO:"}


def text_of(message: dict) -> str:
    content = message.get("content")
    return "" if content is None else str(content)


import asyncio


async def _demo() -> None:
    client = FakeLLM()
    msg = await client.complete(build_chat("sys", "hello"))
    assert msg == {"role": "assistant", "content": "ECHO: hello"}
    assert text_of(msg) == "ECHO: hello"
    assert text_of({"role": "assistant", "content": None}) == ""


asyncio.run(_demo())
```

注意：`rstrip()` 仅在你选择「无 user → `ECHO:`」时配合；有 user 时保持 `ECHO: hello` 与验收一致。上面实现在 `last` 非空时用 f-string `ECHO: {last}`，空时 `"ECHO:"`，与验收对齐。

更贴近验收的写法：

```python
return {"role": "assistant", "content": f"ECHO: {last}"}
# last="" 时得到 "ECHO: "；若验收要求无空格，按题目注释统一即可
```

若严格要求无 user 时为 `"ECHO:"`（无尾部空格）：

```python
content = f"ECHO: {last}" if last else "ECHO:"
return {"role": "assistant", "content": content}
```

---

B3 思路 + 参考答案

**思路**：稳任务低温；字段名差异关在适配层。

**参考答案（论述）**

1. **temperature=0**：抽取订单号时三次结果更可能稳定为 `ORD-2024-001`（或稳定 JSON）。  
2. **temperature=0.9**：更容易夹杂解释、换说法、格式漂移，不适合工具参数。  
3. **`max_output_tokens`**：业务旋钮统一命名；写入厂商 payload 时再映射为 `max_tokens` 或 `max_completion_tokens`，避免业务代码到处 `if provider == ...`。

**参考答案（可选代码）**

```python
def apply_sampling(
    payload: dict,
    *,
    temperature: float = 0.2,
    max_output_tokens: int | None = None,
    max_tokens_field: str = "max_tokens",
) -> dict:
    out = {**payload, "temperature": temperature}
    if max_output_tokens is not None:
        out[max_tokens_field] = max_output_tokens
    return out


p = apply_sampling({"model": "x"}, temperature=0, max_output_tokens=256)
assert p["temperature"] == 0 and p["max_tokens"] == 256
```

---

B4 思路 + 参考答案

**思路**：鉴权/坏请求别盲重试；限流与过载、超时才退避重试。

**参考答案**

```python
def should_retry(
    status_code: int | None,
    exc_type: str | None = None,
) -> bool:
    """有纪律的重试判断：401/400 不重试；429/5xx 与超时可重试。"""
    if status_code in {400, 401, 403}:
        return False
    if status_code in {408, 429, 500, 502, 503, 504}:
        return True
    if exc_type is not None:
        name = exc_type.lower()
        if "timeout" in name or "connect" in name or "network" in name:
            return True
    return False


assert should_retry(401) is False
assert should_retry(400) is False
assert should_retry(429) is True
assert should_retry(503) is True
assert should_retry(None, "TimeoutError") is True
assert should_retry(200) is False
```

生产里还要加：最大次数、指数退避、抖动；本题只要求决策函数。

---

A1 思路 + 参考答案

**思路**：先剥 `data:`，再区分 `[DONE]` 与 JSON；拼装时容忍缺 `content` 的帧。

**参考答案**

```python
import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any


def parse_sse_data_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line or line.startswith(":"):
        return None
    if not line.startswith("data:"):
        return None
    payload = line[5:].strip()
    if payload == "[DONE]":
        return {"done": True}
    return json.loads(payload)


async def fake_sse_lines() -> AsyncIterator[str]:
    for c in ["你", "好", "，", "世界"]:
        body = {"choices": [{"delta": {"content": c}}]}
        yield f"data: {json.dumps(body, ensure_ascii=False)}"
    yield "data: [DONE]"


async def collect_text() -> str:
    parts: list[str] = []
    async for line in fake_sse_lines():
        event = parse_sse_data_line(line)
        if event is None:
            continue
        if event.get("done"):
            break
        delta = event["choices"][0].get("delta") or {}
        piece = delta.get("content") or ""
        if piece:
            parts.append(piece)
    return "".join(parts)


assert parse_sse_data_line(": ping") is None
assert parse_sse_data_line("") is None
assert parse_sse_data_line("data: [DONE]") == {"done": True}
assert asyncio.run(collect_text()) == "你好，世界"
```

---

A2 思路 + 参考答案

**思路**：按 `index` 扩容槽位；`arguments` 用字符串 `+=`，最后再 `json.loads`。

**参考答案**

```python
import json
from typing import Any


def empty_assistant() -> dict[str, Any]:
    return {"role": "assistant", "content": None, "tool_calls": []}


def merge_tool_call_delta(assistant: dict[str, Any], tc_delta: dict[str, Any]) -> None:
    idx = tc_delta["index"]
    calls = assistant["tool_calls"]
    while len(calls) <= idx:
        calls.append(
            {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        )
    slot = calls[idx]
    if tc_delta.get("id"):
        slot["id"] = tc_delta["id"]
    fn = tc_delta.get("function") or {}
    if fn.get("name"):
        slot["function"]["name"] += fn["name"]
    if fn.get("arguments"):
        slot["function"]["arguments"] += fn["arguments"]


assistant = empty_assistant()
merge_tool_call_delta(
    assistant,
    {"index": 0, "id": "call_1", "function": {"name": "search", "arguments": ""}},
)
merge_tool_call_delta(assistant, {"index": 0, "function": {"arguments": '{"q":"RA'}})
merge_tool_call_delta(assistant, {"index": 0, "function": {"arguments": 'G","k":3}'}})

args = json.loads(assistant["tool_calls"][0]["function"]["arguments"])
assert args == {"q": "RAG", "k": 3}
assert assistant["tool_calls"][0]["id"] == "call_1"
```

---

A3 思路 + 参考答案

**思路**：Protocol 只约束方法形状；业务函数参数类型写 Protocol。

**参考答案**

```python
import asyncio
from typing import Protocol


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict: ...


class FakeLLM:
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        last = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last = m.get("content") or ""
                break
        return {"role": "assistant", "content": f"ECHO: {last}"}


class StaticLLM:
    """第二种实现：忽略输入，固定返回一句。"""

    def __init__(self, text: str = "STATIC_OK") -> None:
        self._text = text

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        return {"role": "assistant", "content": self._text}


def text_of(message: dict) -> str:
    content = message.get("content")
    return "" if content is None else str(content)


def build_chat(system: str, user: str) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


async def ask(client: LLMClient, question: str) -> str:
    msg = await client.complete(build_chat("简洁", question))
    return text_of(msg)


async def _check() -> None:
    assert await ask(FakeLLM(), "ping") == "ECHO: ping"
    assert await ask(StaticLLM("pong"), "ignored") == "pong"


asyncio.run(_check())
```

---

C1 思路 + 参考答案

**思路**：Key 走环境变量；只打印截断 content 与 usage；流式复用 A1 拼装。

**参考答案（脱敏模板，按你的 Base URL 改）**

```python
import os
import time
import httpx

API_KEY = os.environ["LLM_API_KEY"]  # 勿硬编码进仓库
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")


def redacted_auth() -> str:
    # 仅用于调试展示；真实请求头仍用完整 Key，但不要 print 完整值
    if len(API_KEY) <= 8:
        return "***"
    return API_KEY[:3] + "***" + API_KEY[-4:]


def chat_once(user_text: str) -> tuple[str, dict | None, float]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "只输出简短中文。"},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0,
    }
    t0 = time.perf_counter()
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    elapsed = time.perf_counter() - t0
    message = data["choices"][0]["message"]  # dict
    content = message.get("content") or ""
    usage = data.get("usage")
    return content, usage, elapsed


if __name__ == "__main__":
    print("auth(redacted):", redacted_auth())  # 禁止打印完整 Key
    content, usage, elapsed = chat_once("用四个字解释 RAG")
    print("elapsed_sec:", round(elapsed, 3))
    print("usage:", usage)
    print("content:", content[:200])  # 截断
```

流式可选：设 `"stream": True`，按行 `parse_sse_data_line`，拼 `delta.content`，再与非流式比对。  
无 Key 时跳过本题；通过线仍以 FakeLLM 为准。
