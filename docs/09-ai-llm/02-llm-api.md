# LLM API 实战

> 所属模块：`09-ai-llm` · AI / LLM 基础与认知地图  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/09-ai-llm/02-llm-api.md`](../../exercises/09-ai-llm/02-llm-api.md)

## 本章定位

- **本章角色**：学会 Chat Completions（或等价 Chat API）的请求结构、关键参数、流式与错误重试；并设计多模型适配层。
- **实践**：有 Key 就打真 API；没有就写 FakeClient，接口保持一致。

## 学习目标

1. 构造标准 messages 请求并解析回复。
2. 理解 temperature 等关键参数的工程影响。
3. 实现流式 SSE 解析，并能拼装文本与流式 `tool_calls`。
4. 对 429/5xx/超时做有纪律的重试。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | Chat API、关键参数、流式拼装、错误与重试 | 能封装客户端 |
| **建议掌握** | 多模型适配层 | 能替换供应商 |
| **了解即可** | 本地推理部署 | 扫盲 |

---

## 1. Chat API 请求骨架

不同厂商字段名略有差异，思想一致：

```python
payload = {
    "model": "gpt-x",
    "messages": [
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "用一句话解释 RAG"},
    ],
    "temperature": 0.2,
}
```

响应直觉：

```text
choices[0].message.content  → 文本回复
usage                       → token 统计（若有）
```

Python 可用官方 SDK 或 `httpx` 直调。建议自己包一层，避免业务代码散落 SDK 细节。

---

## 2. 必掌握：关键参数

| 参数 | 直觉 | Agent 建议 |
|------|------|------------|
| `temperature` | 高更随机，低更稳 | 工具参数/抽取用低；创意可高 |
| 输出上限 | 限制回复长度 | 适配层统一成 `max_output_tokens`；厂商字段可能是 `max_tokens` 或 `max_completion_tokens`（以文档为准；推理模型预算常含隐性 reasoning） |
| `top_p` | 另一种采样控制 | 优先固定一个主旋钮；评测时一次只改一个采样参数 |
| `stop` | 停止序列 | 特殊格式时用 |
| seed（若支持） | 增强可复现 | 评测时有用但不保证绝对一致 |

---

## 3. 必掌握：流式输出

流式：边生成边返回 delta，适合打字机体验与降低首字延迟。  
OpenAI 兼容接口常见形态是 **SSE**：每行 `data: {...}`，结束为 `data: [DONE]`。  
（下列示例假定使用 `httpx`；完整非流式封装见 §7。）

### 3.1 解析 SSE 行

```python
import json
from collections.abc import AsyncIterator
from typing import Any


def parse_sse_data_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line or line.startswith(":"):  # 注释/心跳
        return None
    if not line.startswith("data:"):
        return None
    payload = line[5:].strip()
    if payload == "[DONE]":
        return {"done": True}
    return json.loads(payload)
```

### 3.2 拼装文本 delta → 完整 assistant

```python
async def iter_chat_deltas(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> AsyncIterator[dict[str, Any]]:
    body = {**payload, "stream": True}
    async with client.stream("POST", url, headers=headers, json=body) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            event = parse_sse_data_line(line)
            if event is None:
                continue
            if event.get("done"):
                break
            yield event


async def stream_text(client, url, headers, payload) -> str:
    parts: list[str] = []
    async for event in iter_chat_deltas(client, url, headers, payload):
        delta = event["choices"][0].get("delta") or {}
        piece = delta.get("content") or ""
        if piece:
            parts.append(piece)
            # 这里也可以把 piece 推给前端 SSE
    return "".join(parts)
```

### 3.3 流式 `tool_calls`：按 index 增量拼装

流式里工具调用常被拆成多片：先出 `id`/`name`，再持续追加 `arguments` 字符串碎片。  
必须按 `delta.tool_calls[].index` 归并，最后再 `json.loads`。

```python
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
        slot["function"]["name"] += fn["name"]  # 有的实现整段一次给出
    if fn.get("arguments"):
        slot["function"]["arguments"] += fn["arguments"]


async def stream_assistant_message(client, url, headers, payload) -> dict[str, Any]:
    assistant = empty_assistant()
    content_parts: list[str] = []
    async for event in iter_chat_deltas(client, url, headers, payload):
        choice = event["choices"][0]
        delta = choice.get("delta") or {}
        if delta.get("content"):
            content_parts.append(delta["content"])
        for tc in delta.get("tool_calls") or []:
            merge_tool_call_delta(assistant, tc)
        # finish_reason 可能在最后一帧：stop / tool_calls / length
    if content_parts:
        assistant["content"] = "".join(content_parts)
    if not assistant["tool_calls"]:
        assistant.pop("tool_calls", None)
    return assistant
```

要点：

| 点 | 说明 |
|----|------|
| 写入历史 | 流式结束后仍要得到**完整** assistant dict，再 append 到 messages |
| `finish_reason=length` | arguments 可能被截断 → 校验失败，结构化错误回传或重试 |
| Fake 流式 | 把完整 message 拆成若干 delta yield，方便测拼装逻辑、不依赖真网 |
| 超时 | `httpx` timeout 覆盖建连与读超时；长流式可适当加大 read timeout |

### 3.4 Fake 流式（测拼装、不烧钱）

```python
async def fake_stream_text(text: str, chunk: int = 4) -> AsyncIterator[str]:
    for i in range(0, len(text), chunk):
        yield text[i : i + chunk]


async def collect_fake_text(text: str) -> str:
    parts: list[str] = []
    async for piece in fake_stream_text(text):
        parts.append(piece)
    return "".join(parts)


def assemble_from_complete_message(message: dict[str, Any]) -> dict[str, Any]:
    """测 tool_calls merge：把「完整 message」当成若干 delta 喂给 merge。"""
    assistant = empty_assistant()
    if message.get("content"):
        assistant["content"] = message["content"]
    for i, tc in enumerate(message.get("tool_calls") or []):
        args = tc["function"]["arguments"]
        mid = max(1, len(args) // 2)
        merge_tool_call_delta(
            assistant,
            {"index": i, "id": tc.get("id", f"call_{i}"), "function": {"name": tc["function"]["name"], "arguments": ""}},
        )
        merge_tool_call_delta(assistant, {"index": i, "function": {"arguments": args[:mid]}})
        merge_tool_call_delta(assistant, {"index": i, "function": {"arguments": args[mid:]}})
    if not assistant["tool_calls"]:
        assistant.pop("tool_calls", None)
    return assistant
```


工程点：前端可用 SSE/WebSocket 推送文本；Agent 工具环通常等拼装完成再执行工具（并行 tool 见模块 11）。

---

## 4. 必掌握：错误与重试

常见：

| 情况 | 处理 |
|------|------|
| 401/403 | 别重试，修 Key/权限 |
| 400 | 别盲重试，修请求 |
| 429 | 退避重试，尊重 Retry-After |
| 5xx / 超时 | 有限次退避重试 |
| 上下文超限 | 截断/摘要后再试 |

回顾：异常章的 `retryable`、异步章的 `wait_for`、Semaphore 限流。

---

## 5. 建议掌握：多模型适配层

仓库统一契约（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）：`complete` 返回 **assistant 消息 dict**，不是裸 `str`。

```python
from typing import Any, Protocol


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict: ...  # {"role": "assistant", "content": ..., "tool_calls": ...?}


class OpenAICompatClient:
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict:
        ...


class FakeLLM:
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict:
        last = messages[-1].get("content") if messages else ""
        return {"role": "assistant", "content": f"ECHO: {last}"}


def text_of(message: dict) -> str:
    return message.get("content") or ""
```

业务只依赖 `LLMClient`。换供应商 = 换适配器。需要纯文本时用 `text_of(...)`。

---

## 6. 了解即可：本地推理

Ollama / vLLM / llama.cpp 等：私有化、要显存与运维。  
API 形态常做成 OpenAI 兼容，正好吃你的适配层。

---

## 7. 最小封装示例

```python
import os
import httpx


class ChatClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools is not None:
            payload["tools"] = tools
        if max_output_tokens is not None:
            # 字段名因厂商而异：max_tokens / max_completion_tokens …
            payload["max_tokens"] = max_output_tokens
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]  # assistant dict
```

（字段按你用的供应商调整。纯文本：`text_of(await client.complete(messages))`。）

---

## 8. 练习指引

[`exercises/09-ai-llm/02-llm-api.md`](../../exercises/09-ai-llm/02-llm-api.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能发 Chat 请求并取出 assistant message / content
- [ ] 能解析 SSE 并拼装完整 content（及可选 tool_calls）
- [ ] 知道哪些错误可重试
- [ ] 有 Protocol 级适配层意识（`complete` → dict）

### 下一章

[`03-prompt-engineering.md`](./03-prompt-engineering.md) —— 把话说清楚，让模型稳定做事。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[名词词典](./01-ai-landscape-glossary.md)
- 下一章：[Prompt Engineering](./03-prompt-engineering.md)
