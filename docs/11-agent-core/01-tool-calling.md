# Tool Calling

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/11-agent-core/01-tool-calling.md`](../../exercises/11-agent-core/01-tool-calling.md)

## 本章定位

- **模块目标**：理解 Agent 本质，能手写并使用框架构建 Agent。
- **本章角色**：掌握工具定义 → 模型选择 → 执行回传 → 循环终止；这是 Agent 行动能力的核心协议。
- **前置**：结构化输出、HTTP/异步、异常分类。

## 学习目标

1. 用 JSON Schema / 函数描述定义工具。
2. 理解模型如何返回 tool_calls。
3. 在服务端执行工具并把结果写回 messages。
4. 设计安全的循环终止条件。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 工具定义、选择、执行回传、终止条件 | 能实现单轮/多轮工具环 |
| **建议掌握** | 工具设计原则、并行 tool_calls 与失败语义、结果截断 | 能落地稳妥执行器 |
| **了解即可** | 厂商 strict / structured tool args 差异 | 地图 |

---

## 1. Agent 与 Tool Calling

没有工具的 Chat：只能说。  
有工具的模型：可以**做事**（搜、查库、算、调 API）。

```text
用户 → 模型
       ↓ 决定调用 search(query=...)
     执行工具
       ↓ result
     模型基于结果继续 / 给出最终答案
```

---

## 2. 必掌握：工具定义

向模型暴露的是**名称 + 描述 + 参数 schema**：

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "在知识库中搜索相关文档片段",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
            },
        },
    }
]
```

服务端注册真正的实现：

```python
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]

REGISTRY = {"search": search}
```

---

## 3. 必掌握：模型选择工具

请求里带 `tools=`（字段名因厂商而异）。  
响应可能包含 `tool_calls`：

```json
{
  "role": "assistant",
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

要点：

- `arguments` 常是 **JSON 字符串**，要 `json.loads`
- 必须用 Pydantic/校验再执行
- 未知工具名 → 返回结构化错误给模型或中止

---

## 4. 必掌握：执行与回传

```python
import json


def run_tool_call(tool_call: dict, registry: dict) -> dict:
    name = tool_call["function"]["name"]
    raw = tool_call["function"]["arguments"]
    args = json.loads(raw) if isinstance(raw, str) else raw
    if name not in registry:
        return {"role": "tool", "tool_call_id": tool_call["id"], "content": f"unknown tool: {name}"}
    try:
        result = registry[name](**args)
        content = json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        content = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    return {"role": "tool", "tool_call_id": tool_call["id"], "content": content}
```

把 assistant（含 tool_calls）与 tool 消息依次 append 进历史，再请求模型。

---

## 5. 必掌握：循环终止条件

```text
for step in range(max_steps):
  调模型
  若无 tool_calls → 取 content 作为最终回答，break
  否则执行工具并回传
否则 → 强制结束（超时步数）
```

边角（实现时要处理）：

- `content` 与 `tool_calls` **可同时存在**：先执行工具，勿过早当最终答
- `arguments` 非法/截断 JSON → 校验失败信息回传或中止，勿裸 `**args`
- 看厂商 `finish_reason`（length / content_filter 等）决定重试还是失败
- 用户取消、总超时、重复相同 tool_call 熔断
- 危险工具人工确认（模块 12）

---

## 6. 建议掌握：工具设计原则

1. **单一职责**：一个工具一件事  
2. **描述写清边界**：何时用/何时不用  
3. **参数少而硬**：枚举、范围、默认值  
4. **返回结构化**：便于模型继续推理  
5. **失败可解释**：错误信息对模型友好  
6. **无副作用或可幂等**：防重试双执行  

---

## 7. 建议掌握：并行 tool_calls 与失败语义

一次响应可含多个 `tool_calls`。无数据依赖时可并行：

```python
import asyncio


async def run_many(tool_calls: list[dict], registry: dict, sem: asyncio.Semaphore) -> list[dict]:
    async def one(call: dict) -> dict:
        async with sem:
            return await asyncio.to_thread(run_tool_call, call, registry)

    # 按原顺序收集结果，便于与 tool_call_id 对齐
    return await asyncio.gather(*(one(c) for c in tool_calls))
```

规则：

| 点 | 做法 |
|----|------|
| 依赖顺序 | `search` 的结果要喂给下一步时，**不要**与依赖它的工具并行；串行或拆两轮 |
| 部分失败 | 单个工具错误 → 仍回传该条 tool 错误 JSON；让模型决定改参/换工具，勿整组静默丢弃 |
| 限流 | `Semaphore`（进程内）+ 供应商 RPM；与模块 05/07 限流区分 |
| 幂等 | 重试同一 `tool_call_id` / 业务幂等键，防双执行 |
| ACL | 每个 call 都要 `authorize(role, name, args)`（模块 12） |

### 结果截断（防撑爆 context）

```python
MAX_TOOL_CHARS = 4000


def clip_tool_content(content: str) -> str:
    if len(content) <= MAX_TOOL_CHARS:
        return content
    return content[: MAX_TOOL_CHARS - 20] + "\n...[truncated]"
```

大结果可先摘要再回传；原始落盘用 `run_id` 关联，勿整份塞进 messages。

---

## 8. 了解即可：厂商能力差异

部分 API 支持严格 JSON Schema / structured tool args；仍应在服务端二次校验。  
流式 `tool_calls` 拼装见模块 09 §3。

---

## 9. 练习指引

[`exercises/11-agent-core/01-tool-calling.md`](../../exercises/11-agent-core/01-tool-calling.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能实现校验 + 错误 JSON 回传的 `run_tool_call`
- [ ] 知道并行时何时必须串行、部分失败如何回传
- [ ] 会对过大工具结果做截断

### 下一章

[`02-handwritten-agent.md`](./02-handwritten-agent.md) —— 把工具环收成完整 Agent。

## 导航

- 返回模块：[README](./README.md)
- 下一章：[手写一个 Agent](./02-handwritten-agent.md)
