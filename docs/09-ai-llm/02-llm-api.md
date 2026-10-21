# LLM API 实战

> 所属模块：`09-ai-llm` · AI / LLM 基础与认知地图  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（无 Key 用 Fake/Echo 也能跑通主线；有 Key 再打真调用）  
> 对应练习：[`exercises/09-ai-llm/02-llm-api.md`](../../exercises/09-ai-llm/02-llm-api.md)

## 本章定位

- **模块目标**：对现阶段 AI 发展与常用名词建立较深入认知，并能调用 LLM。
- **本章角色**：学会 Chat Completions（或等价 Chat API）的请求结构、关键参数、流式与错误重试；并设计多模型适配层。
- **实践约定**：有 Key 就打真 API；没有就写 `FakeLLM`（或早期教学用 `EchoLLM`），**接口保持与 [`CONVENTIONS.md`](../CONVENTIONS.md) 一致**。
- **目标不是**：背全厂商文档或成为 SDK 专家；能封装、能排障、能换供应商即可。

## 学习目标（学完应能做到）

1. 构造标准 `messages` 请求，并解析出完整 **assistant 消息 dict**（不是裸 `str`）。
2. 理解 `temperature`、输出上限等关键参数的工程影响，并能在适配层统一命名。
3. 实现流式 SSE 解析，并能拼装文本与流式 `tool_calls`。
4. 对 `429` / `5xx` / 超时做有纪律的重试；对 `401` / `400` 知道别盲重试。
5. 用 `Protocol` 级适配层隔离厂商差异；无 Key 时用 Fake 跑通主线与测试。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | Chat API 骨架、关键参数、流式拼装、错误与重试 | 能封装客户端，能写 Fake 测拼装 |
| **建议掌握** | 多模型适配层 | 能替换供应商而不改业务 |
| **了解即可** | 本地推理部署 | 扫盲：知道能接进同一适配层 |

## 仓库约定（先钉死，后面反复用）

见 [`CONVENTIONS.md`](../CONVENTIONS.md)：

```text
async def complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    **kwargs,
) -> dict  # assistant_message：至少含 role；常有 content / tool_calls
```

| 名字 | 何时用 | 返回 |
| --- | --- | --- |
| **`FakeLLM`** | 模块 09 起、工具环、评测、CI | `dict`（assistant 消息） |
| **`EchoLLM`** | 早期语言章「回声」教学 | 可 `str`；**勿命名为 FakeLLM** |

无 Key 时：用 Fake/Echo 跑通主线；单测与 CI **必须**可在 Fake 下绿；真模型是可选升级。

---

## 1. Chat API 请求骨架

这一节会刻意写细——后面所有参数、流式、重试、适配层，都建立在「一次 Chat 请求长什么样」之上。

### 1.1 一次请求在干什么

#### 为什么需要先钉骨架？

厂商 SDK 名称、字段、路径略有差异，但思想高度一致：你把 **消息列表 + 模型名 + 若干旋钮** 发给服务；服务返回 **一条（或若干）assistant 消息**，外加可选的 `usage`。若骨架不清，后面会把「SDK 细节」和「业务逻辑」缠在一起，换供应商时整片重写。

#### 怎么理解

```text
你的进程
  → 构造 messages（system / user / assistant / tool …）
  → 选 model + temperature 等参数
  → HTTP POST …/chat/completions（或厂商等价路径）
  → 解析 choices[0].message → assistant dict
  →（可选）把 assistant 写回历史，继续下一轮
```

标准请求体直觉（OpenAI 兼容形态）：

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
choices[0].message   → 完整 assistant 消息 dict（role / content / tool_calls?）
choices[0].message.content  → 文本回复（可能为 null，若走了 tool_calls）
usage                → token 统计（若有；计费与预算的准绳）
```

#### 怎么写（messages 构造）

```python
def build_chat(system: str, user: str) -> list[dict]:
    """最小可用：system + user。后续可追加 assistant / tool 轮次。"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
```

角色直觉（先够用，细节在 Tool Calling 章加深）：

| role | 谁在说话 | 常见用途 |
| --- | --- | --- |
| `system` | 你（开发者） | 人设、硬约束、输出格式 |
| `user` | 终端用户 / 调用方 | 本轮问题 |
| `assistant` | 模型 | 历史回复；含 `tool_calls` 时也是 assistant |
| `tool` | 工具执行结果 | 把工具输出塞回上下文（模块 11） |

#### 跑一下（无 Key：Echo / Fake）

早期「回声」教学（返回 `str`，**勿叫 FakeLLM**）：

```python
class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


echo = EchoLLM()
print(echo.complete("用一句话解释 RAG"))
# ECHO: 用一句话解释 RAG
```

模块 09 起的契约（返回 assistant dict）：

```python
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


import asyncio


async def main() -> None:
    client = FakeLLM()
    messages = build_chat("简洁回答", "用一句话解释 RAG")
    msg = await client.complete(messages)
    print(msg)
    # {'role': 'assistant', 'content': 'ECHO: 用一句话解释 RAG'}


asyncio.run(main())
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `complete` 直接返回 `str` | 与仓库契约冲突；后续拼 `tool_calls`、写历史会处处特判 |
| 把整段 SDK 响应当「消息」 | 业务要的是 `choices[0].message`，不是外层 envelope |
| system 与 user 揉进一条字符串 | 失去角色边界；多轮与工具环难扩展 |
| 日志打印完整 `Authorization` | Key 泄漏 |

#### 对照：EchoLLM vs FakeLLM vs 真 API

| | EchoLLM | FakeLLM | 真 Chat API |
| --- | --- | --- | --- |
| 阶段 | 早期语言/OOP 教学 | 模块 09+、Agent、评测 | 有 Key 的联调/上线 |
| 入参 | 常是 `prompt: str` | `messages`（+ 可选 `tools`） | 同 Fake 契约（经适配层） |
| 出参 | `str` | `dict`（assistant） | `dict`（assistant） |
| 能否测流式拼装 | 弱 | 能（见 §3.4） | 能，但烧钱、要网 |

Python 可用官方 SDK 或 `httpx` 直调。**建议自己包一层**，避免业务代码散落 SDK 细节（完整非流式封装见 §7）。

---

## 2. 必掌握：关键参数

### 2.1 旋钮地图

#### 为什么参数值得单独一节？

同一条 prompt，改 `temperature` 或输出上限，得到的是「稳抽取」还是「花活文案」、是「完整 JSON」还是「半截被截断」。Agent 里工具参数抽取、路由决策要**稳**；创意文案才需要高随机。评测时若一次拧多个旋钮，你分不清是 prompt 变好了还是采样变了。

#### 怎么理解

| 参数 | 直觉 | Agent 建议 |
| --- | --- | --- |
| `temperature` | 高更随机，低更稳 | 工具参数/抽取用低（如 `0`～`0.3`）；创意可高 |
| 输出上限 | 限制回复长度 | 适配层统一成 `max_output_tokens`；厂商字段可能是 `max_tokens` 或 `max_completion_tokens`（以文档为准；推理模型预算常含隐性 reasoning） |
| `top_p` | 另一种采样控制（核采样） | 优先固定一个主旋钮；评测时一次只改一个采样参数 |
| `stop` | 遇到序列就停 | 特殊格式/分隔符时用 |
| `seed`（若支持） | 增强可复现 | 评测时有用，**不保证**绝对一致 |

心智口诀：

```text
稳任务 → 低温 + 够用的输出上限 + 固定其它采样旋钮
评测对比 → 一次只改一个变量（prompt 或 temperature，不要一起拧）
字段名差异 → 在适配层翻译，业务只认 max_output_tokens
```

#### 怎么写（适配层统一命名）

```python
def apply_sampling(
    payload: dict,
    *,
    temperature: float = 0.2,
    max_output_tokens: int | None = None,
    top_p: float | None = None,
    stop: list[str] | None = None,
    seed: int | None = None,
    max_tokens_field: str = "max_tokens",
) -> dict:
    """把「统一旋钮」写进厂商 payload。max_tokens_field 按供应商切换。"""
    payload = {**payload, "temperature": temperature}
    if max_output_tokens is not None:
        payload[max_tokens_field] = max_output_tokens
    if top_p is not None:
        payload["top_p"] = top_p
    if stop is not None:
        payload["stop"] = stop
    if seed is not None:
        payload["seed"] = seed
    return payload
```

#### 跑一下（无网：对比「稳 vs 飘」的假想实验）

有 API 时：对「从文本提取订单号」跑 `temperature=0` 与 `0.9` 各 3 次，看结果是否一致。  
无 API 时：用书面对照建立直觉即可——

```text
任务：从「订单 ORD-2024-001 已发货」提取订单号

temperature ≈ 0
  → 三次都更可能是：ORD-2024-001（或稳定 JSON）

temperature ≈ 0.9
  → 可能夹杂解释、换说法、偶发格式漂移
```

代码侧先把「旋钮写入」跑通（不发网）：

```python
base = {"model": "gpt-x", "messages": [{"role": "user", "content": "hi"}]}
print(apply_sampling(base, temperature=0.0, max_output_tokens=64))
print(apply_sampling(base, temperature=0.9, max_tokens_field="max_completion_tokens"))
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 业务里直接写死 `max_tokens` | 换推理模型/厂商时字段名不对，静默忽略或 400 |
| `temperature` 与 `top_p` 一起猛拧 | 评测不可解释；行为难复现 |
| 输出上限太小 | JSON / `arguments` 被截断 → 校验失败（流式里更阴险） |
| 以为 `seed` = 完全可复现 | 多数厂商只是「尽量」；别当单元测试的唯一断言 |

#### 对照：业务旋钮 vs 厂商字段

| 适配层（业务） | 常见厂商字段 | 备注 |
| --- | --- | --- |
| `max_output_tokens` | `max_tokens` / `max_completion_tokens` | 以当前模型文档为准 |
| `temperature` | `temperature` | 较通用 |
| `tools` | `tools` / 旧式 `functions` | 模块 11 再展开 |

---

## 3. 必掌握：流式输出

流式：边生成边返回 delta，适合打字机体验与降低首字延迟。  
OpenAI 兼容接口常见形态是 **SSE**：每行 `data: {...}`，结束为 `data: [DONE]`。  
（下列示例假定使用 `httpx`；完整非流式封装见 §7。）

### 3.1 解析 SSE 行

#### 为什么要自己会解析？

SDK 会帮你藏细节，但排障、自建网关、写 Fake 流式、对接前端 SSE 时，你必须认得出「一行 data 是什么」。网络章已扫过 SSE 地图；这里落到 **Chat delta** 拼装。

#### 怎么写

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

#### 跑一下

```python
samples = [
    ": ping",
    "",
    'data: {"choices":[{"delta":{"content":"你"}}]}',
    "data: [DONE]",
    "event: ignore_me",
]
for line in samples:
    print(repr(line), "→", parse_sse_data_line(line))
```

期望直觉：注释/空行 → `None`；JSON → dict；`[DONE]` → `{"done": True}`；非 `data:` → `None`。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 忘了 strip `[DONE]` 两侧空白 | 结束帧识别失败，流挂起直到超时 |
| 把注释行当 JSON `loads` | 抛异常，整条流中断 |
| 假设一行一个完整 HTTP 响应 | SSE 是**长连接上的多行事件** |

#### 对照：前端 EventSource vs Python 行迭代

| 前端 | Python（httpx） |
| --- | --- |
| `EventSource` / `fetch` + `ReadableStream` | `client.stream` + `aiter_lines()` |
| `onmessage` 拿到 `event.data` | 自己剥 `data:` 前缀 |
| 连接断开重连策略 | 超时、重试策略由你封装（见 §4） |

---

### 3.2 拼装文本 delta → 完整 assistant

#### 为什么不能「只 print 不拼」？

打字机体验可以边收边推前端；但 Agent 要把回复写入 `messages` 历史、做评测、跑工具环时，最终仍需要**完整** assistant 消息。拼装逻辑必须可测、可 Fake。

#### 怎么写

```python
async def iter_chat_deltas(
    client: Any,  # httpx.AsyncClient
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


async def stream_text(client: Any, url: str, headers: dict[str, str], payload: dict[str, Any]) -> str:
    parts: list[str] = []
    async for event in iter_chat_deltas(client, url, headers, payload):
        delta = event["choices"][0].get("delta") or {}
        piece = delta.get("content") or ""
        if piece:
            parts.append(piece)
            # 这里也可以把 piece 推给前端 SSE
    return "".join(parts)
```

#### 跑一下（Fake 文本流，不烧钱）

```python
async def fake_stream_text(text: str, chunk: int = 4) -> AsyncIterator[str]:
    for i in range(0, len(text), chunk):
        yield text[i : i + chunk]


async def collect_fake_text(text: str) -> str:
    parts: list[str] = []
    async for piece in fake_stream_text(text):
        parts.append(piece)
    return "".join(parts)


async def demo_text() -> None:
    out = await collect_fake_text("你好，世界")
    assert out == "你好，世界"
    print("ok:", out)


asyncio.run(demo_text())
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只推前端、不拼完整 message | 历史断层；下一轮模型「忘了自己说过什么」 |
| 假设每帧都有 `content` | 前几帧可能只有 `role`；工具帧可能 `content` 为 null |
| 读超时按「非流式」设太短 | 长回答生成中被掐断 |

#### 对照：非流式 vs 流式

| | 非流式 | 流式 |
| --- | --- | --- |
| 首字延迟 | 等整段生成完 | 通常更低 |
| 解析 | 一次 `response.json()` | SSE 行 + 拼装 |
| 写入历史 | 直接取 `message` | **拼完**再取完整 dict |
| 失败面 | HTTP 级错误为主 | 还多「半截流」问题 |

---

### 3.3 流式 `tool_calls`：按 index 增量拼装

#### 为什么这一点特别容易错？

流式里工具调用常被拆成多片：先出 `id` / `name`，再持续追加 `arguments` 字符串碎片。  
必须按 `delta.tool_calls[].index` 归并，最后再 `json.loads`。若按「数组下标 = 出现顺序」想当然合并，多工具并行时会拼乱。

#### 怎么写

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


async def stream_assistant_message(
    client: Any,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
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

要点表：

| 点 | 说明 |
| --- | --- |
| 写入历史 | 流式结束后仍要得到**完整** assistant dict，再 append 到 messages |
| `finish_reason=length` | arguments 可能被截断 → 校验失败，结构化错误回传或重试 |
| Fake 流式 | 把完整 message 拆成若干 delta yield，方便测拼装逻辑、不依赖真网 |
| 超时 | `httpx` timeout 覆盖建连与读超时；长流式可适当加大 read timeout |

#### 跑一下（测 merge，不依赖真网）

```python
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
            {
                "index": i,
                "id": tc.get("id", f"call_{i}"),
                "function": {"name": tc["function"]["name"], "arguments": ""},
            },
        )
        merge_tool_call_delta(assistant, {"index": i, "function": {"arguments": args[:mid]}})
        merge_tool_call_delta(assistant, {"index": i, "function": {"arguments": args[mid:]}})
    if not assistant["tool_calls"]:
        assistant.pop("tool_calls", None)
    return assistant


complete = {
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "search",
                "arguments": '{"q":"RAG","k":3}',
            },
        }
    ],
}
got = assemble_from_complete_message(complete)
assert got["tool_calls"][0]["function"]["arguments"] == '{"q":"RAG","k":3}'
assert json.loads(got["tool_calls"][0]["function"]["arguments"])["q"] == "RAG"
print("tool_calls merge ok")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用「列表 append 顺序」代替 `index` | 多工具交错 delta 时拼错槽位 |
| 每帧 `json.loads(arguments)` | 半截 JSON 必然失败；应**拼完再 loads** |
| `finish_reason=length` 仍当成功 | 静默坏参数，工具执行怪错 |
| 拼完仍留空的 `tool_calls: []` | 有的下游讨厌空数组；可按需 `pop` |

#### 对照：文本 delta vs tool_calls delta

```text
文本：    delta.content  → 字符串追加
工具：    delta.tool_calls[i].function.arguments → 字符串追加（按 index）
共同点：  都是「碎片 → 完整」；完整后才能进历史 / 执行工具
```

工程点：前端可用 SSE/WebSocket 推送文本；Agent 工具环通常等拼装完成再执行工具（并行 tool 见模块 11）。

---

### 3.4 Fake 流式（测拼装、不烧钱）

#### 为什么 Fake 流式值得单独做？

真流式依赖网与 Key，CI 不稳定且贵。把「完整 message → 若干 delta」的逆过程写出来，就能单测 `merge_tool_call_delta` 与文本拼接，而不碰外网。

#### 怎么写 / 跑一下

上一小节的 `fake_stream_text` 与 `assemble_from_complete_message` 就是 Fake 流式的最小形态。再补一个「产出伪 SSE 事件」的异步生成器，方便练习题 A1：

```python
async def fake_sse_events(text: str, chunk: int = 2) -> AsyncIterator[dict[str, Any]]:
    for i in range(0, len(text), chunk):
        piece = text[i : i + chunk]
        yield {"choices": [{"delta": {"content": piece}}]}
    # 调用方在看到 done 时 break；这里用哨兵模拟
    yield {"done": True}


async def consume_fake_sse(text: str) -> str:
    parts: list[str] = []
    async for event in fake_sse_events(text):
        if event.get("done"):
            break
        parts.append(event["choices"][0]["delta"]["content"])
    return "".join(parts)


assert asyncio.run(consume_fake_sse("SSE")) == "SSE"
```

#### 易错点

- Fake 要覆盖：纯文本、`tool_calls` 分片、空 content、最后一帧 `finish_reason`
- Fake **不必**比特级模仿厂商；要模仿的是**你拼装代码依赖的形状**

#### 对照：测什么用 Fake，验什么用真 API

| 目标 | 推荐 |
| --- | --- |
| merge / SSE 行解析 / 重试决策 | Fake（CI 必绿） |
| 延迟、usage、模型质量 | 真 API（可选、脱敏日志） |

---

## 4. 必掌握：错误与重试

网络章（[`02-network-http.md`](../04-systems-basics/02-network-http.md)）已讲超时、幂等与退避；这里落到 **LLM Chat 调用** 的决策表与可跑函数。回顾：异常章的 `retryable`、异步章的 `wait_for`、Semaphore 限流。

### 4.1 失败谱与决策

#### 为什么重试必须「有纪律」？

LLM 调用贵、有配额，且 POST 语义下重试可能重复扣 token。完全不重试 → 偶发 503 就挂；无脑重试 → 429 风暴、双倍烧钱。

#### 怎么理解

| 情况 | 处理 |
| --- | --- |
| 401 / 403 | **别重试**，修 Key / 权限 |
| 400 | **别盲重试**，修请求（字段、上下文超限形态等） |
| 429 | 退避重试，**尊重 Retry-After** |
| 5xx / 超时 | 有限次退避重试 |
| 上下文超限 | 截断 / 摘要后再试（换策略，不是同一请求死撞） |

#### 怎么写：`should_retry` + 退避

```python
import random
from typing import Any


def should_retry(status_code: int | None, exc_type: str | None = None) -> bool:
    """教学用决策，与练习 B4 对齐。

    - 401/403/400：不重试
    - 429/502/503/504/5xx：可重试
    - 超时（exc_type 含 timeout）：可重试
    """
    if status_code in {400, 401, 403, 404}:
        return False
    if status_code == 429 or (status_code is not None and status_code >= 500):
        return True
    if exc_type and "timeout" in exc_type.lower():
        return True
    return False


def backoff_seconds(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    """指数退避；attempt 从 0 起。"""
    return min(cap, base * (2**attempt))


def backoff_with_jitter(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    delay = backoff_seconds(attempt, base=base, cap=cap)
    return delay * (0.5 + random.random())


def retry_after_seconds(headers: dict[str, Any] | None, attempt: int) -> float:
    """优先 Retry-After；否则走本地退避。"""
    if headers:
        raw = headers.get("Retry-After") or headers.get("retry-after")
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                pass
    return backoff_with_jitter(attempt)
```

带重试的调用壳（示意；生产还要日志、指标、取消）：

```python
import asyncio
from collections.abc import Awaitable, Callable


async def with_retries(
    op: Callable[[], Awaitable[dict]],
    *,
    max_attempts: int = 3,
    classify: Callable[[BaseException], tuple[int | None, str | None]] | None = None,
) -> dict:
    last: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            return await op()
        except BaseException as exc:  # 教学示意：实际应收窄异常类型
            last = exc
            status, et = (None, type(exc).__name__) if classify is None else classify(exc)
            if attempt >= max_attempts - 1 or not should_retry(status, et):
                raise
            await asyncio.sleep(backoff_with_jitter(attempt))
    assert last is not None
    raise last
```

#### 跑一下

```python
cases: list[tuple[int | None, str | None]] = [
    (401, None),
    (429, None),
    (503, None),
    (400, None),
    (None, "TimeoutError"),
]
for code, et in cases:
    print(code, et, "→", should_retry(code, et))

for i in range(4):
    print("attempt", i, "wait≈", round(backoff_seconds(i), 2), "s")
```

期望直觉：`401/400 → False`；`429/503/Timeout → True`；退避时间随 attempt 指数上升（有上限）。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 401 仍重试 | 无效消耗，掩盖配置错误 |
| 429 固定 sleep(0.1) 狂撞 | 配额更惨，可能连坐其它租户 |
| 无限重试 | 故障放大；拖垮自己的 worker |
| 上下文超限当 5xx 重试 | 同一超长 messages 会稳定失败 |
| 工具已执行成功后的「整轮重试」 | 重复副作用（幂等键 / 先查后做，见网络章） |

#### 对照：HTTP 状态 vs 你的动作

| 状态/异常 | 先查什么 | 再做什么 |
| --- | --- | --- |
| 401 / 403 | Key、权限、组织额度 | 修配置，不重试 |
| 400 | 字段名、消息格式、空 messages | 修请求 |
| 429 | `Retry-After`、RPM/TPM | 退避；考虑限流器 |
| 5xx | 上游公告 / 区域 | 有限次退避 |
| 超时 | 读超时是否过短、是否该流式 | 有限次；必要时加大 read timeout |

---

## 5. 建议掌握：多模型适配层

### 5.1 统一契约

#### 为什么要适配层？

今天 OpenAI 兼容，明天换 Azure / 国产网关 / 本地 Ollama——**业务代码不应出现三套字段名与三套 SDK**。适配层把差异关在边界内：业务只依赖 `LLMClient.complete(...) -> dict`。

仓库统一契约（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）：`complete` 返回 **assistant 消息 dict**，不是裸 `str`。

#### 怎么写

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
    """真调用骨架：内部再调 §7 的 ChatClient 或官方 SDK。"""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict:
        return await self._inner.complete(messages, tools=tools, **kwargs)


class FakeLLM:
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict:
        last = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last = m.get("content") or ""
                break
        return {"role": "assistant", "content": f"ECHO: {last}"}


def text_of(message: dict) -> str:
    return message.get("content") or ""
```

业务只依赖 `LLMClient`。换供应商 = 换适配器。需要纯文本时用 `text_of(...)`。

#### 跑一下（业务函数不感知真假）

```python
async def answer_one_liner(client: LLMClient, question: str) -> str:
    messages = build_chat("用一句话回答", question)
    msg = await client.complete(messages, temperature=0.2)
    return text_of(msg)


async def demo_swap() -> None:
    print(await answer_one_liner(FakeLLM(), "什么是 Token？"))
    # 有 Key 时：print(await answer_one_liner(OpenAICompatClient(ChatClient(...)), "..."))


asyncio.run(demo_swap())
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 业务直接 `import openai` 散落调用 | 换模型要改十处；测试难注入 Fake |
| Fake 命名成「返回 str 的 FakeLLM」 | 与 CONVENTIONS 冲突；后续章节接口分裂 |
| 把 `usage`、原始响应塞进业务返回值 | 边界泄漏；需要时另做 `complete_with_meta` |
| 同步/异步混用无适配 | 项目线偏好 `async`；手写 Agent 教学可用同步，但别两个都叫同一套业务 API 却不标明 |

#### 对照：适配层职责边界

| 放在适配层 | 放在业务层 |
| --- | --- |
| URL、鉴权头、字段名翻译 | prompt 内容、对话策略 |
| 流式拼装 → 完整 message | 是否展示打字机 UI |
| 重试 / 超时默认值 | 领域错误如何提示用户 |
| Fake / 真客户端切换 | 评测用例与验收断言 |

---

## 6. 了解即可：本地推理

### 6.1 地图：Ollama / vLLM / llama.cpp

#### 为什么要知道本地推理？

私有化、内网、数据不出域、控成本时，你会碰到本地或自建推理。本章不要求你会运维 GPU 集群，但要知道：**API 形态常做成 OpenAI 兼容，正好吃你的适配层**。

#### 怎么理解

| 方案 | 直觉 | 你何时碰 |
| --- | --- | --- |
| Ollama | 本机拉模型、常用 OpenAI 兼容端口 | 笔记本原型、内网 demo |
| vLLM | 高吞吐 serving | 团队自建推理服务 |
| llama.cpp | 轻量/CPU 也可跑 | 资源紧、边缘实验 |

共同运维现实：要显存（或量化）、要版本与模型文件管理、要监控延迟与显存碎片——细节留给运维/专题，这里只建地图。

#### 怎么写（接到同一契约）

```python
# 概念：base_url 指到本地，Key 可随便占位（视实现而定）
local = ChatClient(
    base_url="http://127.0.0.1:11434/v1",  # Ollama 兼容示例，以你环境为准
    api_key="ollama",
    model="llama3.2",
)
# 业务仍：await local.complete(messages) -> dict
```

无本地服务时，继续用 `FakeLLM` 跑主线即可——**不要**把「没装 Ollama」变成学习阻塞。

#### 跑一下（可选）

若本机已有 Ollama 且启用了兼容端点：用 §7 的 `ChatClient` 打一条非流式请求，打印 `text_of(message)`。  
否则跳过，用 Fake 断言契约即可。

#### 易错点

- 以为「本地 = 不用适配层」→ 字段与流式差异仍在，边界更值得统一
- 本地模型上下文更短 / 工具能力更弱 → 同一套 prompt 可能直接翻车，需单独评测
- 把教学用 Fake 行为当成「本地模型一定这样回」→ Fake 只保证接口，不保证智能

#### 对照：云 API vs 本地兼容端点

| | 云 API | 本地 OpenAI 兼容 |
| --- | --- | --- |
| 鉴权 | 真 Key、组织权限 | 常弱化或占位 |
| 计费 | token / 请求 | 电费与显卡 |
| 适配层 | `OpenAICompatClient` | **同一个**，换 `base_url` + `model` |
| CI | Fake | Fake（勿强依赖本机 GPU） |

---

## 7. 最小封装示例

### 7.1 非流式 `ChatClient`

#### 为什么要最小封装，而不是业务里直接 `httpx.post`？

三处以上调用就会开始复制：URL 拼接、Bearer、超时、取 `choices[0].message`、`max_tokens` 字段名。最小封装是适配层的「真客户端」内核；Fake 是同一 `complete` 签名的测试替身。

#### 怎么写

```python
import os
from typing import Any

import httpx


class ChatClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        max_tokens_field: str = "max_tokens",
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens_field = max_tokens_field
        self.timeout = timeout

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
        **kwargs: Any,
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
            payload[self.max_tokens_field] = max_output_tokens
        # 允许透传 stop / seed / top_p 等（由调用方显式传入）
        for key in ("stop", "seed", "top_p"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]  # assistant dict
```

工厂：有 Key 用真客户端，否则 Fake——主线永不堵死：

```python
def make_client() -> LLMClient:
    key = os.getenv("LLM_API_KEY", "").strip()
    if not key:
        return FakeLLM()
    return ChatClient(
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=key,
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )
```

#### 跑一下

```python
async def demo_client() -> None:
    client = make_client()
    msg = await client.complete(build_chat("简洁", "ping"))
    print(type(client).__name__, msg)


asyncio.run(demo_client())
```

无 Key 时期望类似：`FakeLLM {'role': 'assistant', 'content': 'ECHO: ping'}`。  
有 Key 时：打印真模型回复；**日志脱敏**，不要打印 Bearer。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 每次 `complete` 新建策略却忘了统一 timeout | 偶发卡死（回顾网络章） |
| `raise_for_status` 后不区分 429 | 上层无法 `should_retry` |
| 返回整个 `data` 而非 `message` | 与 Fake 形状不一致，业务分叉 |
| 把 Key 写进仓库 | 泄露；用环境变量 |

#### 对照：封装层次

```text
业务：answer_one_liner(client, q)
         ↓ 依赖 Protocol
适配：OpenAICompatClient / FakeLLM /（未来）OtherVendorClient
         ↓
传输：ChatClient（httpx） / 官方 SDK
         ↓
线路：HTTPS / 本地 v1 兼容端点
```

（字段按你用的供应商调整。纯文本：`text_of(await client.complete(messages))`。）

### 7.2 与流式、重试的拼装关系

```text
非流式主路径：ChatClient.complete → assistant dict
流式路径：    iter_chat_deltas → stream_assistant_message → 同一形状的 dict
重试：        包在 complete / stream 外层（只对瞬时错误）
Fake：        同签名返回 dict；流式用 §3.4 测拼装
```

你可以在练习里先完成非流式 + Fake，再加 SSE 拼装与 `should_retry`。

---

## 8. 练习指引

按 [`exercises/09-ai-llm/02-llm-api.md`](../../exercises/09-ai-llm/02-llm-api.md) 做：

| 题 | 对应本节 | 提示 |
| --- | --- | --- |
| B1 `build_chat` | §1 | 测 role/content 结构 |
| B2 `complete` + `text_of` | §1 / §5 / §7 | Fake 返回 ECHO dict |
| B3 temperature / 上限 | §2 | 无 Key 可书面对比 |
| B4 `should_retry` | §4 | 401/429/503/timeout |
| A1 SSE 文本拼装 | §3.1～3.2 / §3.4 | Fake 事件即可 |
| A2 流式 tool_calls | §3.3 | 按 index merge |
| A3 Protocol 适配 | §5 | 业务只依赖 Protocol |
| C1 真 httpx | §7 | 脱敏；可选再打 stream |

playground 可自建目录实验；保持 `complete -> dict` 契约即可。

---

## 9. 小结与下一站

### 知识地图（收回来）

```text
Chat 骨架（messages + model）
  → 关键参数（低温稳、上限防截断、字段名进适配层）
  → 流式（SSE 行 → 文本 / tool_calls 按 index 拼完整 dict）
  → 错误与重试（401/400 不重试；429/5xx/超时有限退避）
  → 适配层（LLMClient Protocol；FakeLLM 保 CI）
  → 本地推理（OpenAI 兼容端点，换 base_url）
  → 最小封装（ChatClient + make_client 无 Key 回落 Fake）
```

### 自检

- [ ] 能发 Chat 请求并取出 assistant message / content
- [ ] 能解析 SSE 并拼装完整 content（及可选 tool_calls）
- [ ] 知道哪些错误可重试，并能写出 `should_retry`
- [ ] 有 Protocol 级适配层意识（`complete` → dict）
- [ ] 无 Key 时能用 FakeLLM（或早期 EchoLLM）跑通主线，且不把 Echo 误叫作 FakeLLM

### 下一章

[`03-prompt-engineering.md`](./03-prompt-engineering.md) —— 把话说清楚，让模型稳定做事。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[名词词典](./01-ai-landscape-glossary.md)
- 下一章：[Prompt Engineering](./03-prompt-engineering.md)
- 约定：[CONVENTIONS.md](../CONVENTIONS.md)
- 相关：[`04-systems-basics/02-network-http.md`](../04-systems-basics/02-network-http.md)（超时 / 重试 / SSE 地图）
