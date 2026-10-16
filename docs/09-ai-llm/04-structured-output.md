# Structured Output

> 所属模块：`09-ai-llm` · AI / LLM 基础与认知地图  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/09-ai-llm/04-structured-output.md`](../../exercises/09-ai-llm/04-structured-output.md)

## 本章定位

- **本章角色**：让 LLM 输出 JSON/Schema 可校验结构，并与 Pydantic 结合；这是 Tool Calling 与 Agent 编排的前置能力。
- **目标**：程序能稳定 `parse`，而不是用正则从散文里「抠」。

## 学习目标

1. 用提示或厂商能力约束 JSON 输出。
2. 校验失败时有修复/重试策略。
3. 与 Pydantic 模型双向配合。
4. 理解工具参数本质也是结构化输出。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | JSON/Schema 约束、校验与修复、Pydantic | 能落地解析管线 |
| **建议掌握** | 工具参数结构化 | 能接到 Tool Calling |
| **了解即可** | 厂商能力差异 | 地图 |

---

## 1. 为什么要结构化

Agent 系统需要：

```text
分类结果、抽取字段、路由决策、工具参数、评测标签
```

散文输出 → 难组合、难测试、难观测。

---

## 2. 必掌握：约束输出

层次（从软到硬）：

1. **提示约束**：只输出 JSON，给 schema 示例  
2. **响应预处理**：剥掉 ```json 围栏  
3. **JSON Schema / 厂商 structured output / tool calls**  
4. **校验器（Pydantic）失败则重试或修复**

提示示例：

```text
只输出 JSON，不要 Markdown。Schema：
{"intent":"billing|tech|other","confidence":0-1}
```

---

## 3. 必掌握：校验与修复

```python
import json
from typing import Literal

from pydantic import BaseModel, ValidationError


class IntentResult(BaseModel):
    intent: Literal["billing", "tech", "other"]
    confidence: float  # 约定 0～1；可用 Field(ge=0, le=1) 再收紧


def parse_intent(text: str) -> IntentResult:
    data = json.loads(strip_fences(text))
    return IntentResult.model_validate(data)


def strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        # 去掉首尾围栏
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t
```

失败策略：

```text
1) 再请求一次：「你的输出不是合法 JSON，请严格按 schema 重输」
2) 有限次后失败，返回领域错误
3) 不要无限循环烧钱
```

---

## 4. 必掌握：与 Pydantic 结合

- **请求进模型**：API 入参  
- **LLM 出模型**：结构化结果  
- **同一套类型**：减少漂移  

```python
class ToolArgs(BaseModel):
    query: str
    top_k: int = 3


def build_tool_call(name: str, args: ToolArgs) -> dict:
    return {"name": name, "arguments": args.model_dump()}
```

---

## 5. 建议掌握：工具参数结构化

Function / Tool Calling = 模型选择工具名 + 给出参数 JSON。  
厂商保证不同程度的 schema 跟随；你仍应：

- 服务端再校验
- 默认值/范围检查
- 拒绝未知字段（视严格度）

这与下一模块 RAG、再下一模块 Tool Calling 直接衔接。

---

## 6. 了解即可：厂商差异

有的支持 `response_format: json_schema`；有的强依赖 tool calling；有的只靠提示。  
适配层把「结构化获取」抽象成统一接口。

---

## 7. 端到端小流程

```text
user question
  → prompt(+schema)
  → LLM
  → strip + json.loads
  → Pydantic validate
  → 成功：进入业务
  → 失败：repair prompt 重试 ≤ N
```

---

## 8. 练习指引

[`exercises/09-ai-llm/04-structured-output.md`](../../exercises/09-ai-llm/04-structured-output.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能定义 schema 并用 Pydantic 校验
- [ ] 有失败重试/修复策略
- [ ] 理解 Tool Calling 与结构化输出的关系

### 模块 09 收官

下一模块：[`../10-rag/README.md`](../10-rag/README.md) —— Embedding 与 RAG。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Prompt Engineering](./03-prompt-engineering.md)
- 下一模块：[Embedding 与 RAG](../10-rag/README.md)
