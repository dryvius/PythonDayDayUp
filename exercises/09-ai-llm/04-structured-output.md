# 练习：Structured Output

> 对应文档：[`docs/09-ai-llm/04-structured-output.md`](../../docs/09-ai-llm/04-structured-output.md)  
> 状态：`已完成出题`  
> 建议用时：60～100 分钟（含热身）  
> Python：`≥ 3.11`（Pydantic v2）

## 练习说明

1. 先读完文档「必掌握」：约束输出、校验与修复、与 Pydantic 结合。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **FakeLLM 契约**与 [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md) 一致：`async complete(...) -> dict`（assistant 消息），**禁止返回 `str`**。结构化管线从 `message["content"]` 取文本再 `strip` / `loads` / 校验。
4. 建议目录：

```text
playground/09-ai-llm/04-structured-output/
  parse.py
  models.py
  test_structured.py
```

可选自测：

```bash
python playground/09-ai-llm/04-structured-output/test_structured.py
```

5. 先自己做完，再看文末「提示与参考答案」。依赖：`pydantic>=2`。

---

## 热身题（建议先做）

### W1. 为什么「能 loads」还不够？

**给定**：

```python
import json
data = json.loads('{"intent":"billing","confidence":"高"}')
```

**要求**：用 2～3 句说明：这对业务意味着什么？下一层应该用什么拦？

**验收**：点出类型/范围未校验；应上 Pydantic（或同类）做契约。

---

### W2. 认出围栏噪声

**给定**：模型常返回 Markdown 代码围栏包着的 JSON。

**要求**：写出剥围栏前/后各一行示例字符串（可手写）。

**验收**：能说明若不剥，`json.loads` 会失败。

---

### W3. FakeLLM 返回什么？

**给定**：CONVENTIONS。

**要求**：写出 `complete` 的返回值类型与最小字段；说明结构化解析应从哪里取原始文本。

**验收**：返回 **dict**（`role`/`content`）；从 `content` 取文本，而不是让 `complete` 直接返回 JSON 字符串类型。

---

## 基础题（必做）

### B1. `strip_fences` + `json.loads`

**给定**：有围栏 / 无围栏两种模型输出。

**要求**：实现：

```python
def strip_fences(text: str) -> str:
    """去掉首尾 Markdown 代码围栏；无围栏则 strip 后原样返回。"""
    ...


def loads_json_content(text: str) -> dict:
    """strip_fences 后 json.loads；要求结果为 dict，否则 TypeError。"""
    ...
```

**验收**：

```python
import json

raw1 = '{"intent":"tech","confidence":0.8}'
raw2 = """```json
{"intent":"tech","confidence":0.8}
```"""

assert strip_fences(raw1) == '{"intent":"tech","confidence":0.8}'
assert strip_fences(raw2) == '{"intent":"tech","confidence":0.8}'
assert loads_json_content(raw2) == {"intent": "tech", "confidence": 0.8}

try:
    loads_json_content("这不是 JSON")
    raise AssertionError("should fail")
except json.JSONDecodeError:
    pass
```

---

### B2. Pydantic 校验：`IntentResult`

**给定**：意图三分类 + 置信度。

**要求**：

```python
from typing import Literal
from pydantic import BaseModel, Field, ValidationError


class IntentResult(BaseModel):
    intent: Literal["billing", "tech", "other"]
    confidence: float = Field(ge=0, le=1)


def parse_intent(text: str) -> IntentResult:
    """strip → loads → model_validate。"""
    ...
```

对合法 / 非法 dict（或文本）做校验测试。

**验收**：

```python
ok = parse_intent('{"intent":"tech","confidence":0.7}')
assert ok.intent == "tech" and ok.confidence == 0.7

try:
    parse_intent('{"intent":"billing","confidence":1.5}')
    raise AssertionError("range should fail")
except ValidationError:
    pass

try:
    parse_intent('{"intent":"billing"}')
    raise AssertionError("missing field should fail")
except ValidationError:
    pass

# 围栏也可过
ok2 = parse_intent('```json\n{"intent":"other","confidence":0.5}\n```')
assert ok2.intent == "other"
```

---

### B3. 解析管线说明（可与 B2 合并实现）

**给定**：业务入口只想调用一个函数。

**要求**：在注释或 docstring 写明管线  
`raw -> strip_fences -> json.loads -> IntentResult.model_validate`；  
非法 JSON → `JSONDecodeError`；契约失败 → `ValidationError`。  
`parse_intent` 即算完成本题（可与 B2 同一函数）。

**验收**：B2 断言全部通过即可；可选加日志区分 syntax / schema 失败。

---

### B4. `parse_with_repair`：有界修复重试骨架

**给定**：偶发坏 JSON 是常态；禁止无限重试。

**要求**：实现骨架（同步或异步均可，但若内部调 FakeLLM，须遵守 dict 契约）：

```python
from collections.abc import Awaitable, Callable


class ParseFailedError(Exception):
    """有界重试后仍失败。"""


async def parse_with_repair(
    complete: Callable[..., Awaitable[dict]],
    messages: list[dict],
    *,
    max_attempts: int = 3,
) -> IntentResult:
    """
    调用 complete(messages) -> assistant dict；
    取 content 解析；失败则把 raw 与错误摘要追加进 messages 再试。
    """
    ...
```

约定：

1. 只捕获 `json.JSONDecodeError` 与 `ValidationError` 进入修复；其它异常直接抛出。  
2. `max_attempts` 用尽后抛 `ParseFailedError`。  
3. 修复 user 提示要短：强调「只输出 JSON、不要 Markdown、按 schema」。

**验收**：用「先坏后好」的 stub（`complete` 必须返回 dict）：第一次 `content` 非法，第二次合法 JSON；断言 `result.intent == "other"` 且只调用 2 次。完整 stub 见文末 B4 参考答案。

---

## 进阶题（建议）

### A1. Tool arguments 结构化：`SearchArgs`

**给定**：工具 `search(query, top_k)`。

**要求**：

```python
from pydantic import BaseModel, Field, ValidationError


class SearchArgs(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


def build_tool_call(name: str, args: SearchArgs) -> dict:
    """返回 {"name": name, "arguments": args.model_dump()}"""
    ...
```

故意构造越界 `top_k`，验证失败；合法路径 `model_dump` 成功。

**验收**：

```python
args = SearchArgs(query="RAG", top_k=3)
assert build_tool_call("search", args) == {
    "name": "search",
    "arguments": {"query": "RAG", "top_k": 3},
}
try:
    SearchArgs(query="RAG", top_k=99)
    raise AssertionError("should reject")
except ValidationError:
    pass
```

---

### A2. FakeLLM 先坏后好：端到端

**给定**：业务函数 `async def classify_intent(client, question) -> IntentResult`。

**要求**：

1. `FakeLLM` / `FlakyFakeLLM`：`async complete -> dict`。  
2. 第一次 `content` 故意坏（围栏 + 非法 JSON 或越界 confidence）；第二次给合法 JSON。  
3. 业务侧走 `parse_with_repair`（或等价），端到端断言字段。  
4. **禁止** `complete` 返回 `str`。

**验收**：

```python
# FlakyFakeLLM / classify_intent 完整实现见文末 A2
result = await classify_intent(FlakyFakeLLM(), "为何扣费两次？")
assert result.intent == "billing" and abs(result.confidence - 0.88) < 1e-6
```

- [ ] `complete` 返回 dict（两次调用）  
- [ ] 经 repair 后得到合法 `IntentResult`  

---

## 挑战题（可选）

### C1. `complete_structured` Protocol

**给定**：希望业务直接拿到已校验模型，而不是满地 `parse_intent`。

**要求**：

1. 定义 Protocol（名称可微调，语义一致即可）：

```python
from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredLLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict: ...

    async def complete_structured(
        self,
        messages: list[dict],
        model_type: type[T],
        *,
        max_attempts: int = 3,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> T: ...
```

2. 实现一个适配器类（例如 `StructuredFacade`）：内部持有任意 `complete->dict` 客户端，`complete_structured` 内做 strip/loads/validate + 有界修复。  
3. 演示：对 `IntentResult` 调用成功；对故意永远坏的客户端最终抛 `ParseFailedError`。

**验收**：

```python
import asyncio


class AlwaysBad:
    async def complete(self, messages, tools=None, **kwargs) -> dict:
        return {"role": "assistant", "content": "NOT_JSON"}


async def _check() -> None:
    ok_client = FlakyFakeLLM()  # 复用 A2
    facade = StructuredFacade(ok_client)
    result = await facade.complete_structured(
        [
            {"role": "system", "content": "只输出 JSON"},
            {"role": "user", "content": "扣费问题"},
        ],
        IntentResult,
        max_attempts=3,
    )
    assert isinstance(result, IntentResult)

    bad = StructuredFacade(AlwaysBad())
    try:
        await bad.complete_structured(
            [{"role": "user", "content": "x"}],
            IntentResult,
            max_attempts=2,
        )
        raise AssertionError("should fail")
    except ParseFailedError:
        pass

asyncio.run(_check())
```

- [ ] `complete` 仍返回 dict  
- [ ] `complete_structured` 返回 Pydantic 模型实例  
- [ ] 失败路径有界且可捕获  

（可选书面）用 5 行讨论 `extra="ignore"` vs `extra="forbid"`：对 LLM 多余字段你选丢弃还是失败？——可写在同文件注释，不算通过线硬性条件。

---

## 验收标准（本章通过线）

- [ ] （建议）热身 W1～W3
- [ ] **通过线**：B1～B4；解析管线 + 有界 repair 可跑
- [ ] Fake / Flaky 的 `complete` **返回 dict**，无裸 `str`
- [ ] （建议）A1 与 A2
- [ ] （可选）C1 `complete_structured` Protocol / Facade

### 模块 09 通关自检

- [ ] 术语地图清楚（Token / Context / RAG / Agent…）
- [ ] 能封装 Chat 调用（真或假，`complete -> dict`）
- [ ] 会写可维护提示模板（含弱缓解分隔意识）
- [ ] 会结构化解析 + Pydantic 校验 + 有界修复

完成后进入模块 10《Embedding 与 RAG》。

---

## 提示与参考答案（先做题再看）

> 下列实现按 Pydantic v2；`complete` 一律返回 assistant dict。

W1 参考答案

`json.loads` 只保证语法合法。`confidence` 变成字符串 `"高"` 时业务算分会炸或静默算错。应用 Pydantic 做类型、范围与枚举校验。

---

W2 参考答案

```text
前：```json\n{"intent":"tech","confidence":0.8}\n```
后：{"intent":"tech","confidence":0.8}
```

不剥围栏时 `json.loads` 直接 `JSONDecodeError`。

---

W3 参考答案

```text
async def complete(messages, tools=None, **kwargs) -> dict
# 最小：{"role": "assistant", "content": "..."}
# 解析：content = message["content"] 再进 strip/loads
```

---

B1 思路 + 参考答案

**思路**：只处理首尾围栏；不要用贪婪正则硬抠第一个 `{` 到最后一个 `}` 当默认方案。

**参考答案**

```python
import json
from typing import Any


def strip_fences(text: str) -> str:
    """去掉首尾 Markdown 代码围栏；无围栏则原样（去首尾空白）。"""
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def loads_json_content(text: str) -> dict[str, Any]:
    data = json.loads(strip_fences(text))
    if not isinstance(data, dict):
        raise TypeError(f"expected json object, got {type(data).__name__}")
    return data


raw1 = '{"intent":"tech","confidence":0.8}'
raw2 = """```json
{"intent":"tech","confidence":0.8}
```"""
assert strip_fences(raw1) == raw1
assert loads_json_content(raw2)["intent"] == "tech"
```

---

B2 / B3 思路 + 参考答案

**思路**：`Literal` + `Field(ge=0, le=1)`；`parse_intent` 即管线终点（B3）。

**参考答案**

```python
import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


class IntentResult(BaseModel):
    intent: Literal["billing", "tech", "other"]
    confidence: float = Field(ge=0, le=1)


def parse_intent(text: str) -> IntentResult:
    """管线：strip_fences -> json.loads -> model_validate（strip 复用 B1）。"""
    data: dict[str, Any] = json.loads(strip_fences(text))
    return IntentResult.model_validate(data)


assert parse_intent('{"intent":"tech","confidence":0.7}').intent == "tech"
assert parse_intent('```json\n{"intent":"other","confidence":0.5}\n```').intent == "other"
try:
    parse_intent('{"intent":"billing","confidence":1.5}')
    raise AssertionError
except ValidationError:
    pass
```

---

B4 思路 + 参考答案

**思路**：有界；回灌 raw + 错误类型；`complete` 必须返回 dict。

**参考答案**

```python
import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError


class ParseFailedError(Exception):
    """有界重试后仍失败。"""


async def parse_with_repair(
    complete: Callable[..., Awaitable[dict]],
    messages: list[dict],
    *,
    max_attempts: int = 3,
) -> IntentResult:
    last_err: Exception | None = None
    history: list[dict] = list(messages)
    for _ in range(1, max_attempts + 1):
        msg = await complete(history)
        if not isinstance(msg, dict):
            raise TypeError("complete must return assistant dict, not str")
        raw = msg.get("content") or ""
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
                        f"校验失败：{type(e).__name__}: {e}\n"
                        "请严格按 schema 只输出 JSON，不要 Markdown。"
                    ),
                },
            ]
    raise ParseFailedError(f"parse failed after {max_attempts}") from last_err


class SequenceLLM:
    def __init__(self, contents: list[str]) -> None:
        self.contents = contents
        self.n = 0

    async def complete(self, messages: list[dict], tools=None, **kwargs: Any) -> dict:
        text = self.contents[min(self.n, len(self.contents) - 1)]
        self.n += 1
        return {"role": "assistant", "content": text}


async def _b4() -> None:
    llm = SequenceLLM(["```json\n{bad}\n```", '{"intent":"other","confidence":0.6}'])
    result = await parse_with_repair(
        llm.complete,
        [{"role": "user", "content": "hi"}],
        max_attempts=3,
    )
    assert result.intent == "other" and llm.n == 2


asyncio.run(_b4())
```

---

A1 思路 + 参考答案

**思路**：工具参数与出参共用 Pydantic；越界在校验层拦截。

**参考答案**

```python
from pydantic import BaseModel, Field, ValidationError


class SearchArgs(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


def build_tool_call(name: str, args: SearchArgs) -> dict:
    return {"name": name, "arguments": args.model_dump()}


assert build_tool_call("search", SearchArgs(query="RAG", top_k=3)) == {
    "name": "search",
    "arguments": {"query": "RAG", "top_k": 3},
}
try:
    SearchArgs(query="RAG", top_k=99)
    raise AssertionError
except ValidationError:
    pass


def parse_search_args(raw: str) -> SearchArgs:
    return SearchArgs.model_validate(loads_json_content(raw))
```

---

A2 思路 + 参考答案

**思路**：`FlakyFakeLLM.complete -> dict`；业务只调 `parse_with_repair`。

**参考答案**

```python
import asyncio


class FlakyFakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, messages: list[dict], tools=None, **kwargs) -> dict:
        self.calls += 1
        if self.calls == 1:
            return {"role": "assistant", "content": "结果：\n```json\n{not json}\n```"}
        return {"role": "assistant", "content": '{"intent":"billing","confidence":0.88}'}


async def classify_intent(client: FlakyFakeLLM, question: str) -> IntentResult:
    messages = [
        {"role": "system", "content": '只输出 JSON：{"intent":"...","confidence":0-1}'},
        {"role": "user", "content": question},
    ]
    return await parse_with_repair(client.complete, messages, max_attempts=3)


async def _e2e() -> None:
    client = FlakyFakeLLM()
    result = await classify_intent(client, "为何扣费两次？")
    assert result.intent == "billing" and client.calls == 2


asyncio.run(_e2e())
```

---

C1 思路 + 参考答案

**思路**：Protocol 描述 `complete` + `complete_structured`；Facade 包装任意 dict 客户端。题目中的 Protocol 签名可直接采用；下面给 Facade 完整实现。

**参考答案**

```python
from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredFacade:
    """任意 complete->dict 客户端 → complete_structured。"""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    async def complete(self, messages: list[dict], tools=None, **kwargs: Any) -> dict:
        msg = await self._inner.complete(messages, tools=tools, **kwargs)
        if not isinstance(msg, dict):
            raise TypeError("inner.complete must return dict")
        return msg

    async def complete_structured(
        self,
        messages: list[dict],
        model_type: type[T],
        *,
        max_attempts: int = 3,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> T:
        last_err: Exception | None = None
        history = list(messages)
        for _ in range(1, max_attempts + 1):
            msg = await self.complete(history, tools=tools, **kwargs)
            raw = msg.get("content") or ""
            try:
                return model_type.model_validate(json.loads(strip_fences(raw)))
            except (json.JSONDecodeError, ValidationError) as e:
                last_err = e
                history = [
                    *history,
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": f"未通过 {model_type.__name__}：{type(e).__name__}。只输出 JSON。",
                    },
                ]
        raise ParseFailedError(f"failed after {max_attempts}") from last_err


class AlwaysBad:
    async def complete(self, messages, tools=None, **kwargs) -> dict:
        return {"role": "assistant", "content": "NOT_JSON"}


async def _c1() -> None:
    ok = await StructuredFacade(FlakyFakeLLM()).complete_structured(
        [{"role": "user", "content": "扣费"}],
        IntentResult,
    )
    assert ok.intent == "billing"
    try:
        await StructuredFacade(AlwaysBad()).complete_structured(
            [{"role": "user", "content": "x"}],
            IntentResult,
            max_attempts=2,
        )
        raise AssertionError
    except ParseFailedError:
        pass


# asyncio.run(_c1())
```

**多余字段权衡（可选）**：`ignore` 更稳、`forbid` 更严；工具副作用偏严格；自由生成可 ignore 但记日志；执行前仍要再校验。

