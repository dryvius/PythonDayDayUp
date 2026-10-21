# Structured Output

> 所属模块：`09-ai-llm` · AI / LLM 基础与认知地图  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（建议先动手写 `strip → loads → validate` 管线，再对照厂商能力）  
> 对应练习：[`exercises/09-ai-llm/04-structured-output.md`](../../exercises/09-ai-llm/04-structured-output.md)  
> 运行环境：Python ≥ 3.11 · Pydantic v2

## 本章定位

- **模块目标**：对现阶段 AI 发展与常用名词建立较深入认知，并能调用 LLM。
- **本章角色**：让 LLM 输出 JSON / Schema 可校验结构，并与 Pydantic 结合；这是 Tool Calling 与 Agent 编排的前置能力。
- **目标一句话**：程序能稳定 `parse`，而不是用正则从散文里「抠」。
- **你已具备**：上一章会写 system / few-shot / 约束；上一章 API 能拿到 `content`（或假客户端）。本章把「输出契约」做成可测试的数据管线。
- **下一座桥**：[`../11-agent-core/01-tool-calling.md`](../11-agent-core/01-tool-calling.md) 里的工具参数，本质就是本章的结构化输出换了个入口。

## 学习目标（学完应能做到）

1. 用提示或厂商能力约束 JSON 输出，并说清「软约束 → 硬约束」各层分别防什么。
2. 写出 `strip → json.loads → Pydantic validate` 管线；校验失败时有有界修复 / 重试策略。
3. 用同一套 Pydantic 模型承接「API 入参」与「LLM 出参」，减少类型漂移。
4. 理解工具参数本质也是结构化输出，并能接到 Tool Calling 的服务端校验。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | JSON / Schema 约束、校验与修复、Pydantic v2 | 能落地解析管线，敢在业务里用 |
| **建议掌握** | 工具参数结构化 | 能接到 Tool Calling，知道服务端仍要校验 |
| **了解即可** | 厂商能力差异 | 建立地图，适配层统一抽象 |

---

## 1. 为什么要结构化

这一节会刻意写细——后面所有「约束、校验、修复、工具参数」都建立在同一个动机上：

> **把模型输出变成程序能稳定消费的数据，而不是需要人眼读懂的散文。**

### 1.1 为什么 Agent 系统离不开结构化？

Agent / 编排层几乎每天都在要这些东西：

```text
分类结果、抽取字段、路由决策、工具参数、评测标签、是否继续循环
```

它们有共同特征：

1. **要被下一行代码用**（`if intent == "billing"`、`db.insert(**row)`）
2. **要能测**（fixture 固定输入 → 断言字段）
3. **要能观测**（日志里打 `intent` / `confidence`，而不是整段散文）

散文输出 → 难组合、难测试、难观测。

### 1.2 散文 vs 结构：同一任务两种形态

用户问：「为什么这个月扣了两次费？」

**散文形态**（对人友好，对程序不友好）：

```text
用户似乎在咨询账单问题，置信度大概比较高，建议转人工或查订单……
```

**结构形态**（对程序友好）：

```json
{"intent": "billing", "confidence": 0.91}
```

下游立刻可以写：

```python
if result.intent == "billing":
    route_to("billing_agent")
```

不必再写一堆脆弱的 `if "账单" in text`。

### 1.3 对照图：数据流差在哪里

```text
【散文路径】
LLM → 一大段中文
    → 正则 / 人工规则抠字段   ← 脆、难测、易漏
    → 业务

【结构路径】
LLM → JSON 字符串
    → strip 围栏
    → json.loads
    → Pydantic validate       ← 契约明确、失败可重试
    → 业务 / 工具执行
```

本章后面每一节，都在把「结构路径」写硬、写稳。

### 1.4 和 Prompt 章的关系（对照）

| Prompt Engineering（上一章） | Structured Output（本章） |
| --- | --- |
| 告诉模型「要什么格式」 | 保证程序「真的吃得到这个格式」 |
| 约束写在自然语言里 | 约束落到 Schema + 校验器 |
| few-shot 示范输出样貌 | 失败时 repair / 重试 |
| 偏「怎么说」 | 偏「怎么 parse 与恢复」 |

可以记一句：

> 提示负责**约定**；结构化输出负责**兑现约定**。

### 1.5 易错点（动机层）

| 错法 | 会发生什么 |
| --- | --- |
| 觉得「模型很聪明，直接正则抠就行」 | 换模型 / 换温度就碎；测试难写 |
| 把结构化当成「只要 JSON」 | 合法 JSON 仍可能缺字段、类型错、枚举越界 |
| 只在 happy path 测 | 生产第一次遇到围栏 / 尾随逗号就炸 |
| 把结构化输出和 Tool Calling 当成两件事 | 工具参数就是结构化输出；后面会重复踩坑 |

---

## 2. 必掌握：约束输出

这一节会刻意写细——约束是「从软到硬」的梯子，不是单一技巧。

### 2.1 为什么需要多层约束？

只靠一句「请输出 JSON」时，模型仍可能：

- 加前言：「好的，结果如下：」
- 包 Markdown 围栏：\`\`\`json ... \`\`\`
- 多吐解释字段、少吐必填字段
- 输出近似 JSON（单引号、尾随逗号、`True`/`None`）

所以工程上把约束分成层次（从软到硬）：

1. **提示约束**：只输出 JSON，给 schema / 示例  
2. **响应预处理**：剥掉 \`\`\`json 围栏、去掉前后废话  
3. **JSON Schema / 厂商 structured output / tool calls**  
4. **校验器（Pydantic）失败则重试或修复**

越往下，越不依赖「模型听话」，越依赖「协议与代码」。

### 2.2 怎么写：提示约束（最软、但必须会）

#### 为什么还要写提示？

即使厂商提供硬 schema，提示仍负责：

- 字段语义（`intent` 什么叫 `billing`）
- 边界（材料不足时返回什么）
- 禁止项（不要 Markdown、不要解释）

#### 怎么写

```text
只输出 JSON，不要 Markdown，不要解释。
Schema：
{
  "intent": "billing" | "tech" | "other",
  "confidence": 0到1之间的数字
}
```

更好一点：给**合法示例**（few-shot 格式，见上一章）：

```text
示例输出：
{"intent":"billing","confidence":0.9}

现在处理：
{question}
```

#### 跑一下（假客户端也能练）

```python
SYSTEM = """你是意图分类器。只输出 JSON，不要 Markdown。
Schema: {"intent":"billing|tech|other","confidence":0-1}
"""

def build_messages(question: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]

# FakeLLM：固定返回，方便本地练管线
def fake_llm(messages: list[dict[str, str]]) -> str:
    q = messages[-1]["content"]
    if "扣费" in q or "账单" in q:
        return '{"intent":"billing","confidence":0.91}'
    return '{"intent":"other","confidence":0.55}'

raw = fake_llm(build_messages("为什么扣费两次？"))
print(raw)  # {"intent":"billing","confidence":0.91}
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 约束写「尽量 JSON」 | 模型仍夹带解释 |
| schema 只写在注释里，提示里不出现 | 模型看不到契约 |
| 示例与 schema 不一致 | few-shot「教坏」模型 |
| 把用户原文直接拼进 system | 缓存差、难维护（上一章已强调） |

### 2.3 怎么写：响应预处理（剥围栏）

#### 为什么需要预处理？

即使提示写了「不要 Markdown」，模型仍常包：

````text
```json
{"intent":"tech","confidence":0.8}
```
````

若不剥围栏，`json.loads` 直接失败。

#### 怎么写

```python
def strip_fences(text: str) -> str:
    """去掉首尾 Markdown 代码围栏；无围栏则原样（去首尾空白）。"""
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    # 首行可能是 ``` 或 ```json
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
```

#### 跑一下

```python
raw1 = '{"intent":"tech","confidence":0.8}'
raw2 = """```json
{"intent":"tech","confidence":0.8}
```"""

assert strip_fences(raw1) == '{"intent":"tech","confidence":0.8}'
assert strip_fences(raw2) == '{"intent":"tech","confidence":0.8}'
print("strip_fences ok")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只替换字符串 \`\`\`json | 结尾 \`\`\` 或语言标签变体漏掉 |
| 用贪婪正则抠「第一个 `{` 到最后一个 `}`」 | 字符串字段里有 `}` 时可能截错；嵌套对象更危险 |
| 把预处理当成校验 | 剥干净仍可能是非法 JSON 或错 schema |
| 在业务各处复制粘贴 strip | 行为不一致；应集中在 parse 入口 |

> 实用策略：先 `strip_fences`，再 `json.loads`；若仍失败，再考虑「找第一个 `{` / `[`」的宽松提取——并记日志，因为那说明提示约束偏软。

### 2.4 怎么写：JSON Schema 与厂商硬约束

#### 为什么要硬约束？

提示 + 预处理仍是「希望模型配合」。硬约束让服务端在**协议层**拒绝不合规输出（或让解码本身受 schema 约束）。

常见形态（名字因厂商而异，这里建立地图即可）：

| 形态 | 直觉 |
| --- | --- |
| `response_format: { "type": "json_object" }` | 强制 JSON 对象，未必校验字段 |
| `response_format: json_schema` / Structured Outputs | 按 schema 约束字段与类型 |
| Tool / Function Calling | 用「伪工具」拿参数 JSON（见 §5、§6） |

#### 怎么写（概念示例，字段名按你用的 SDK 改）

```python
# 概念示意：真正字段名以厂商 SDK 为准
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "intent_result",
        "strict": True,  # 若厂商支持
        "schema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["billing", "tech", "other"],
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
            },
            "required": ["intent", "confidence"],
            "additionalProperties": False,
        },
    },
}
```

#### 对照：软 vs 硬

| 层 | 防什么 | 防不住什么 |
| --- | --- | --- |
| 提示 | 大多数格式漂移 | 偶发围栏 / 胡编字段 |
| 预处理 | 围栏与空白 | 非法 JSON、错类型 |
| 厂商 schema | 结构与类型（视支持度） | 语义错误（intent 标错） |
| Pydantic | 类型、范围、枚举、未知字段策略 | 业务语义是否「该」 |

### 2.5 本节对照小结

```text
提示约束     → 约定「长什么样」
预处理       → 清掉常见包装
厂商 schema  → 协议层加压（有则用）
Pydantic     → 应用层最终契约（始终要有）
```

口诀：

> **软约束减概率，硬约束减事故；Pydantic 是最后一道闸。**

---

## 3. 必掌握：校验与修复

这一节会刻意写细——生产里「偶发坏 JSON」是常态，要有有界策略，而不是撞大运。

### 3.1 为什么「能 loads」还不够？

```python
import json

data = json.loads('{"intent":"billing","confidence":"高"}')
# loads 成功了，但 confidence 是 str，业务要用 float
```

`json.loads` 只保证「是合法 JSON」，不保证「符合你的业务契约」。  
契约层用 **Pydantic v2**（或同类校验器）。

### 3.2 怎么写：Pydantic 模型 + parse

```python
import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class IntentResult(BaseModel):
    intent: Literal["billing", "tech", "other"]
    confidence: float = Field(ge=0, le=1)


def parse_intent(text: str) -> IntentResult:
    data = json.loads(strip_fences(text))
    return IntentResult.model_validate(data)
```

要点（Pydantic v2）：

- 用 `model_validate` 吃 `dict`；用 `model_validate_json` 可直接吃 JSON 字符串（仍建议先 `strip_fences`）
- `Field(ge=0, le=1)` 把「约定 0～1」写成可执行约束
- `Literal[...]` 把枚举收死，避免 `"Billing"` / `"账单"` 这类漂移

### 3.3 跑一下：合法 / 非法

```python
ok = parse_intent('{"intent":"tech","confidence":0.7}')
print(ok.intent, ok.confidence)  # tech 0.7

try:
    parse_intent('{"intent":"billing","confidence":1.5}')
except ValidationError as e:
    print("range fail:", e.error_count())

try:
    parse_intent("这不是 JSON")
except json.JSONDecodeError:
    print("json fail")

try:
    parse_intent('{"intent":"billing"}')  # 缺 confidence
except ValidationError:
    print("missing field")
```

建议你在本地把上面几条都跑通，再写进练习 B1～B3。

### 3.4 失败分两类（先分类，再谈修复）

| 失败类型 | 典型信号 | 常见原因 |
| --- | --- | --- |
| **语法失败** | `JSONDecodeError` | 围栏、尾随逗号、单引号、截断 |
| **语义 / 契约失败** | `ValidationError` | 缺字段、类型错、枚举越界、多余字段（若 forbid） |

修复策略可以不同：

- 语法失败 → 强调「合法 JSON、无 Markdown」
- 契约失败 → 把 `e.errors()` 摘要回灌，指出缺哪、错哪

### 3.5 怎么写：有界修复 / 重试

#### 为什么要「有界」？

无界重试 = 烧钱 + 可能死循环。  
固定上限 `N`（常见 1～3），超限返回**领域错误**，让上层决定降级 / 转人工 / 告警。

#### 怎么写

```python
from collections.abc import Callable


class ParseFailedError(Exception):
    """结构化解析在有界重试后仍失败。"""


def parse_with_repair(
    call_llm: Callable[[list[dict[str, str]]], str],
    messages: list[dict[str, str]],
    *,
    max_attempts: int = 3,
) -> IntentResult:
    """call_llm(messages) -> 模型原始文本；失败则追加修复说明再调。"""
    last_err: Exception | None = None
    history = list(messages)

    for attempt in range(1, max_attempts + 1):
        raw = call_llm(history)
        try:
            return parse_intent(raw)
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = e
            history = [
                *history,
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        "你的上一条输出无法通过校验。"
                        f"错误：{type(e).__name__}: {e}\n"
                        "请严格按 schema 重输，只输出 JSON，不要 Markdown。"
                    ),
                },
            ]
            # 也可在此打日志：attempt / raw 截断 / error

    raise ParseFailedError(f"parse failed after {max_attempts} attempts") from last_err
```

失败策略（记这三条就够用）：

```text
1) 再请求一次：「你的输出不是合法 JSON / 未通过 schema，请严格按 schema 重输」
2) 有限次后失败，返回领域错误（ParseFailedError / 业务 Result.err）
3) 不要无限循环烧钱
```

### 3.6 跑一下：FakeLLM 先坏后好

```python
class FlakyLLM:
    def __init__(self) -> None:
        self.n = 0

    def __call__(self, messages: list[dict[str, str]]) -> str:
        self.n += 1
        if self.n == 1:
            return "好的，结果是：\n```json\n{bad}\n```"  # 故意坏
        return '{"intent":"other","confidence":0.6}'


llm = FlakyLLM()
# 第一次会失败；若你的 strip+loads 仍炸，repair 后第二次应成功
# 下面用「第二次直接成功」演示管线形状：
msgs = build_messages("随便问问天气")
# 手动演示第二次：
print(parse_intent(llm(msgs)))  # 若第一次坏，换更可控的 stub
```

更干净的单测写法（推荐练习 A2）：

```python
def fake_ok(_: list[dict[str, str]]) -> str:
    return '```json\n{"intent":"billing","confidence":0.88}\n```'

result = parse_with_repair(fake_ok, build_messages("为何扣费两次？"), max_attempts=2)
assert result.intent == "billing"
```

### 3.7 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 捕获所有 `Exception` 然后重试 | 把编程错误（`NameError`）也重试掉，难排查 |
| 重试时丢掉原始 `raw` | 模型不知道自己错在哪；日志也无法回放 |
| `max_attempts` 很大 | 成本失控；应告警而不是硬扛 |
| 修复提示写太长、加新要求 | 模型更混乱；修复提示应短、只强调契约 |
| 校验失败就 `pass` 用默认值糊弄 | 静默脏数据进入业务，比抛错更可怕 |
| 把 `ValidationError` 原文整页塞回模型 | token 浪费；摘要 `e.error_count()` + 前几条即可 |

### 3.8 对照：校验 vs 修复 vs 降级

| 动作 | 何时用 | 结果 |
| --- | --- | --- |
| 校验 | 每次拿到模型输出 | 通过 → 业务；失败 → 进入策略 |
| 修复重试 | 偶发格式问题、值得再花一次调用 | 有界成功或失败 |
| 降级 | 超限 / 高风险字段 | 默认路由、人工、或安全拒绝 |
| 人工确认 | 涉及钱 / 删改 / 外发 | 结构对了也不自动执行 |

---

## 4. 必掌握：与 Pydantic 结合

这一节会刻意写细——Pydantic 不是「多写一层类型」，而是**全链路同一契约**。

### 4.1 为什么要「同一套模型」？

没有统一模型时，常见漂移：

```text
提示里写 confidence 0～1
下游 int(confidence * 100)
另一个服务又当 0～100
工具参数里 top_k 有时 str 有时 int
```

用同一套 Pydantic 模型：

- **请求进模型**：HTTP / CLI / 内部 API 入参  
- **LLM 出模型**：结构化结果  
- **工具参数模型**：即将交给 Tool Calling 的 arguments  

→ **同一套类型，减少漂移。**

### 4.2 怎么写：从「出参模型」到「工具参数模型」

```python
from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    intent: Literal["billing", "tech", "other"]
    confidence: float = Field(ge=0, le=1)


class ToolArgs(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


def build_tool_call(name: str, args: ToolArgs) -> dict:
    return {"name": name, "arguments": args.model_dump()}
```

`model_dump()`（v2）把模型变成普通 `dict`，便于：

- 塞进日志
- 当作 tool arguments
- 再 `json.dumps` 发给下游

需要 JSON 字符串时用 `model_dump_json()`。

### 4.3 跑一下：合法构造与越界拒绝

```python
args = ToolArgs(query="RAG", top_k=3)
print(build_tool_call("search", args))
# {'name': 'search', 'arguments': {'query': 'RAG', 'top_k': 3}}

try:
    ToolArgs(query="RAG", top_k=99)
except ValidationError as e:
    print("top_k rejected")
```

### 4.4 怎么写：LLM JSON → 模型（两种入口）

```python
# 入口 A：先 loads 再 validate（便于先 strip）
data = json.loads(strip_fences(raw))
result = IntentResult.model_validate(data)

# 入口 B：Pydantic 直接吃 JSON 字符串（仍建议先 strip）
result = IntentResult.model_validate_json(strip_fences(raw))
```

Agent 场景更常见 A：预处理与 JSON 语法错误要分开处理、分开打点。

### 4.5 多余字段：丢弃还是失败？

LLM 偶尔多吐字段：

```json
{"intent":"tech","confidence":0.8,"note":"可能与网络有关"}
```

两种策略：

```python
class LooseIntent(BaseModel):
    model_config = {"extra": "ignore"}  # 默认倾向：忽略未知字段
    intent: Literal["billing", "tech", "other"]
    confidence: float = Field(ge=0, le=1)


class StrictIntent(BaseModel):
    model_config = {"extra": "forbid"}
    intent: Literal["billing", "tech", "other"]
    confidence: float = Field(ge=0, le=1)
```

对照：

| 策略 | 优点 | 缺点 |
| --- | --- | --- |
| `extra="ignore"`（宽松） | 对模型多嘴更稳健 | 可能吞掉「模型想表达的重要信号」 |
| `extra="forbid"`（严格） | 契约干净、易测 | 多一个字段就失败，修复率上升 |

练习 C1 会让你写权衡。经验法则：

- **对内编排 / 评测标签**：可偏严格  
- **对模型自由生成、schema 未声明扩展点**：可先 ignore，但日志里记录 unknown keys  
- **工具参数（副作用）**：偏严格 + 服务端再校验（见 §5）

### 4.6 易错点（Pydantic v2）

| 错法 | 会发生什么 |
| --- | --- |
| 还在用 v1 的 `.parse_obj` / `.dict()` | API 已变；用 `model_validate` / `model_dump` |
| 用 `dict` 注解却期望自动变模型 | 嵌套模型要声明嵌套 `BaseModel` 类型 |
| `confidence: float` 不写范围 | `"1.5"` 或 `2` 可能滑进业务 |
| 把模型当可变全局缓存乱改字段 | 应用 `model_copy(update=...)`；保持数据清晰 |
| schema 只写在 OpenAPI，LLM 提示另一套 | 两套契约必然漂移——尽量从同一模型生成 |

### 4.7 对照：Pydantic 在链路中的位置

```text
用户 / API
   ↓  IntentRequest.model_validate   （入）
业务拼 prompt
   ↓
LLM 原始文本
   ↓  strip + loads + IntentResult.model_validate  （出）
路由 / 工具
   ↓  ToolArgs.model_validate + model_dump         （工具参数）
执行器
```

一句话：

> **Pydantic 是结构化输出的类型系统；提示是说明书，模型是编译器，校验器是类型检查。**

---

## 5. 建议掌握：工具参数结构化

这一节对接 [`../11-agent-core/01-tool-calling.md`](../11-agent-core/01-tool-calling.md)——先把「同一件事」认出来。

### 5.1 为什么说「工具参数 = 结构化输出」？

Function / Tool Calling = 模型选择**工具名** + 给出**参数 JSON**。

```text
结构化输出（本章）：
  content ≈ '{"intent":"billing","confidence":0.9}'

Tool Calling（模块 11）：
  tool_calls[].function.arguments ≈ '{"query":"RAG","top_k":3}'
```

差别主要在**运输层**（字段挂在 `content` 还是 `tool_calls`），不在**数据层**（都是要校验的 JSON）。

所以本章练熟的管线，到 Tool Calling 几乎原样复用：

```text
arguments 字符串
  → json.loads（注意截断，见 API 章流式拼装）
  → ToolArgs.model_validate
  → 执行 REGISTRY[name](**args)
```

### 5.2 怎么写：从 Pydantic 生成「给模型看的参数 schema」

概念上（真正挂到 `tools=` 的形状见 Tool Calling 章）：

```python
def tool_parameters_schema(model: type[BaseModel]) -> dict:
    """从 Pydantic v2 模型导出 JSON Schema，供 tools 定义复用。"""
    return model.model_json_schema()


print(tool_parameters_schema(ToolArgs))
```

好处：

- 提示 / 工具定义 / 校验**同源**
- 改 `Field(le=10)` 时，文档与校验一起变

### 5.3 怎么写：服务端仍要校验（即使厂商「保证 schema」）

厂商保证不同程度的 schema 跟随；你仍应：

- **服务端再校验**（Pydantic）
- **默认值 / 范围检查**（`top_k` 上限）
- **拒绝未知字段**（视严格度；副作用工具建议 forbid 或显式 allowlist）
- **授权与副作用门闩**（模块 12；这里先记住「结构对 ≠ 允许执行」）

```python
def parse_tool_args(raw_arguments: str) -> ToolArgs:
    # 流式场景：确认 arguments 已拼完整，再 loads
    data = json.loads(raw_arguments)
    return ToolArgs.model_validate(data)


def run_search(raw_arguments: str) -> list[str]:
    args = parse_tool_args(raw_arguments)
    # 真正的 search 实现；此处示意
    return [f"doc:{args.query}:{i}" for i in range(args.top_k)]
```

### 5.4 跑一下：坏参数必须停在校验层

```python
bad = '{"query":"RAG","top_k":999}'
try:
    parse_tool_args(bad)
except ValidationError:
    print("blocked before side effect")
```

这比「工具内部才发现 top_k 太大」安全：校验失败可以结构化回传模型（模块 11 / 异常章会展开），而不是半执行。

### 5.5 对照：本章 → Tool Calling 桥

| 本章概念 | Tool Calling 中的对应 |
| --- | --- |
| `IntentResult` | 某步「决策结构」或最终结构化答案 |
| `ToolArgs` | `function.arguments` 的模型 |
| `strip_fences` + `loads` | 对 `arguments` 字符串 `loads`（通常无围栏，但截断更常见） |
| `parse_with_repair` | 参数校验失败 → 把错误写回 `tool` / `user` 消息再让模型改 |
| 厂商 structured output | `strict` tool args / structured outputs（见 §6） |

这与下一模块 RAG、再下一模块 Tool Calling 直接衔接：RAG 常要结构化「引用片段 id 列表」；Tool Calling 要结构化「调用哪、参数是什么」。

### 5.6 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 信任模型参数，直接 `**json.loads(...)` 进函数 | 多字段、错类型、路径穿越类参数风险 |
| 只校验顶层，不校验嵌套 | 嵌套 `filters` 里脏数据漏网 |
| 把工具执行错误和参数校验错误混成一种 | 模型不知道该「改参数」还是「换策略」 |
| 流式 `arguments` 未拼完就 loads | `JSONDecodeError`；见 [`02-llm-api.md`](./02-llm-api.md) 的 merge |

---

## 6. 了解即可：厂商差异

先建立地图，细节以你选用的 SDK 文档为准；适配层比背厂商字段名更重要。

### 6.1 为什么会有差异？

结构化是「产品能力」，不是 Python 语法。各家在下列维度上不一致：

- 是否支持 `response_format: json_schema`
- 是否支持 strict / structured tool arguments
- 不合规时是**拒答、截断修复、还是尽力生成**
- 流式下 structured / tool_calls 的增量形状

### 6.2 常见三条路（对照）

| 路线 | 做法 | 你仍要做的 |
| --- | --- | --- |
| A. 提示 + 自管 parse | 只靠 prompt / few-shot | strip + loads + Pydantic + repair（本章主线） |
| B. 厂商 JSON / json_schema | `response_format` 等 | 仍建议 Pydantic 再校验一层 |
| C. 借 Tool Calling 拿结构 | 定义一个内部工具如 `emit_intent` | 按工具参数管线校验（§5） |

有的支持 `response_format: json_schema`；有的强依赖 tool calling；有的只靠提示。  
**适配层**把「结构化获取」抽象成统一接口，例如：

```python
from typing import Protocol, TypeVar

T = TypeVar("T", bound=BaseModel)


class StructuredClient(Protocol):
    def complete_structured(
        self,
        messages: list[dict[str, str]],
        model: type[T],
    ) -> T: ...
```

底层可以是：真 schema / tool 伪调用 / 提示 + repair。业务只依赖 `complete_structured`。

### 6.3 易错点（地图层）

| 错法 | 会发生什么 |
| --- | --- |
| 业务代码直接依赖某厂商字段名 | 换模型厂商时大面积改 |
| 以为「开了 json_schema 就永不 ValidationError」 | 语义错误、截断、SDK bug 仍可能发生 |
| 忽略流式与非流式差异 | 本地非流式测过，生产流式拼装炸 |

了解即可：遇到具体厂商再查表；本章目标是**你的管线在最软路线（A）也能稳**。

---

## 7. 端到端小流程

把前面各节收成一条可落地的主链。

### 7.1 总览图

```text
user question
  → prompt(+schema)          # §2 提示约束
  → LLM
  → strip + json.loads       # §2 预处理 + §3
  → Pydantic validate        # §3 / §4
  → 成功：进入业务 / 路由 / 准备 tool args
  → 失败：repair prompt 重试 ≤ N
  → 仍失败：领域错误 / 降级
```

Tool Calling 只是在「成功」之后多一步：

```text
… → ToolArgs.validate → 执行工具 → 结果回写 messages → 再调 LLM
```

### 7.2 怎么写：最小可运行骨架（FakeLLM）

```python
import json
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class IntentResult(BaseModel):
    intent: Literal["billing", "tech", "other"]
    confidence: float = Field(ge=0, le=1)


def strip_fences(text: str) -> str:
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_intent(text: str) -> IntentResult:
    return IntentResult.model_validate(json.loads(strip_fences(text)))


SYSTEM = """只输出 JSON，不要 Markdown。
Schema: {"intent":"billing|tech|other","confidence":0-1}
"""


def build_messages(question: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]


class ParseFailedError(Exception):
    pass


def parse_with_repair(
    call_llm: Callable[[list[dict[str, str]]], str],
    messages: list[dict[str, str]],
    *,
    max_attempts: int = 3,
) -> IntentResult:
    history = list(messages)
    last_err: Exception | None = None
    for _ in range(max_attempts):
        raw = call_llm(history)
        try:
            return parse_intent(raw)
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = e
            history = [
                *history,
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        f"输出未通过校验（{type(e).__name__}）。"
                        "请严格按 schema 重输，只输出 JSON。"
                    ),
                },
            ]
    raise ParseFailedError("exhausted retries") from last_err


def fake_llm(messages: list[dict[str, str]]) -> str:
    q = messages[-1]["content"]
    if "扣费" in q:
        return '```json\n{"intent":"billing","confidence":0.9}\n```'
    return '{"intent":"other","confidence":0.5}'


if __name__ == "__main__":
    result = parse_with_repair(fake_llm, build_messages("为什么扣费两次？"))
    print(result.model_dump())  # {'intent': 'billing', 'confidence': 0.9}
```

### 7.3 跑一下时建议打的点

| 打点 | 为什么 |
| --- | --- |
| `attempt` | 看修复是否真的在救场 |
| `raw` 截断（如前 500 字） | 回放坏输出 |
| `error_type` | 区分 JSON vs Validation |
| `latency_ms` / token（有真 API 时） | 成本和超时 |

可观测性细节见模块 12；本章先养成「失败可回放」的习惯即可。

### 7.4 易错点（端到端）

| 错法 | 会发生什么 |
| --- | --- |
| 业务直接 `json.loads(llm(...))` 散落各处 | 行为不一致，修一处漏三处 |
| 成功路径有模型，失败路径返回裸 `dict` | 类型同盟破裂 |
| 修复时不断追加整段历史却不截断 | 上下文膨胀、费用上升 |
| 把端到端测试做成「必须打真模型」 | CI 不稳；用 FakeLLM 测管线，真模型测评测集 |

### 7.5 对照：本章交付物清单

学完你手里应有：

1. `strip_fences`  
2. `parse_*`（loads + `model_validate`）  
3. `parse_with_repair`（有界）  
4. 至少两个模型：`IntentResult` + `ToolArgs`  
5. 一句能讲清的话：工具参数是结构化输出的桥  

---

## 8. 练习指引

按文档顺序做更顺：

1. 先完成 B1～B3：模型、剥围栏、parse 管线  
2. 再做 B4：有界修复伪代码 / 实现  
3. 建议 A1：`SearchArgs` + 越界  
4. 建议 A2：FakeLLM 端到端  
5. 可选 C1：`extra='forbid'` 权衡  

练习题：[`exercises/09-ai-llm/04-structured-output.md`](../../exercises/09-ai-llm/04-structured-output.md)

本地建议目录（示例）：

```text
playground/09-ai-llm/04-structured-output/
  test_parse.py
```

---

## 9. 小结与下一站

### 记住这几句

1. **结构化的目标**：程序稳定 `parse`，不是散文抠字段。  
2. **约束是梯子**：提示 → 预处理 → 厂商 schema / tool → Pydantic。  
3. **失败要有界**：分类错误、短修复、上限 N、领域错误 / 降级。  
4. **Pydantic 同一契约**：入参、出参、工具参数尽量同源。  
5. **Tool Calling 桥**：`arguments` 就是结构化输出；服务端必须再校验。

### 自检

- [ ] 能定义 schema 并用 Pydantic v2 校验  
- [ ] 有失败重试 / 修复策略，且知道为何不能无限重试  
- [ ] 理解 Tool Calling 与结构化输出的关系  
- [ ] 能说清软约束与硬约束各自防什么、防不住什么  

### 模块 09 收官

下一模块：[`../10-rag/README.md`](../10-rag/README.md) —— Embedding 与 RAG。  
结构化能力会在 RAG 的「引用 id / 是否足够回答」以及模块 11 的 Tool Calling 里反复出现。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Prompt Engineering](./03-prompt-engineering.md)
- 下一模块：[Embedding 与 RAG](../10-rag/README.md)
- 前瞻桥接：[Tool Calling](../11-agent-core/01-tool-calling.md)
