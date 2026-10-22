# 练习：类型系统

> 对应文档：[`docs/02-advanced-python/07-typing-system.md`](../../docs/02-advanced-python/07-typing-system.md)  
> 状态：`已完成出题`  
> 建议用时：80～110 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先写 `list[str]` / `str | None` / 简单别名，再上 Literal / TypedDict / Protocol。
4. 建议代码目录：

```text
playground/02-advanced-python/07-typing-system/
```

5. 若环境有 Pylance/Pyright/mypy，请用它检查你的标注；没有也能先完成代码与注解书写。Python ≥ 3.11；默认用 `list[str]`、`str | None`（勿再以 `List`/`Optional` 为唯一写法）。先做题再看答案。

---

## 热身题（建议先做）

### W1. 基础注解

**要求**：给函数补注解：

```python
def greet(name: str, times: int = 1) -> str:
    ...
```

返回 `name` 重复 `times` 次并用空格连接（`times=1` 时即原名）。

**验收**：`greet("A", 2) == "A A"`。

---

### W2. `str | None`

**要求**：实现 `label(value: str | None) -> str`：`None` 时返回 `"<empty>"`，否则返回原字符串。

**验收**：`label(None) == "<empty>"`；`label("x") == "x"`。

---

### W3. `list[str]` 过滤

**要求**：`def non_empty(items: list[str]) -> list[str]:` 去掉空串与纯空白。

**验收**：`non_empty(["a", " ", "", "b"]) == ["a", "b"]`。

---

### W4. 类型别名

**要求**：定义 `Messages = list[dict[str, str]]`，写一个接受 `Messages` 并返回长度的函数。

**验收**：注解齐全；运行返回正确长度。

---

## 基础题（必做）

### B1. 给函数补全注解

把下面函数补上参数与返回类型（可按你的理解微调实现）：

```python
def clip(text, max_len=20):
    ...

def safe_get(mapping, key, default=None):
    ...

def average(nums):
    # 空列表返回 None
    ...
```

**验收**：注解完整；`average([]) is None`；`average([1, 2, 3]) == 2`。

---

### B2. `Literal` + 收窄

```python
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]

def create_message(role: Role, content: str) -> dict[str, str]:
    ...
```

再写 `assert_role(role: str) -> Role`：若 role 合法则返回（类型上视为 Role），否则抛 `ValueError`。

**验收**：合法 role 通过；非法 role 抛错。可用注释标出故意写错的调用（可选）。

---

### B3. TypedDict 消息列表

定义 `Message` TypedDict（字段至少 `role`、`content`），实现：

```python
def append_message(messages: list[Message], role: Role, content: str) -> list[Message]:
    """返回新列表，不修改入参。"""

def contents(messages: list[Message]) -> list[str]:
    ...
```

**验收**：原列表不被修改；`contents` 正确。

---

### B4. Protocol：可替换 LLM

定义 `LLMClient(Protocol)`，实现 `EchoLLM` 与 `UpperLLM`，再写：

```python
def ask(llm: LLMClient, prompt: str) -> str: ...
```

**验收**：两个实现都能传入 `ask`；不要用继承 ABC 完成（本题刻意练 Protocol）。教学用 Echo，**不要**命名为 FakeLLM。

---

## 进阶题（建议至少做 1 题）

### A1. Generic ToolResult

实现：

```python
class ToolResult(Generic[T]):
    def __init__(self, name: str, value: T) -> None: ...

def unwrap(result: ToolResult[T]) -> T: ...
```

构造 `ToolResult[list[str]]` 与 `ToolResult[float]` 并 unwrap。

**验收**：类型标注齐全；运行结果正确。

---

### A2. 类型检查实践笔记

1. 故意写 2～3 个类型错误（错误 role、把 `None` 当 `str` 用、Protocol 缺方法）
2. 用编辑器或 mypy/pyright 跑一下
3. 在 `a2_notes.md` 记录报错要点与你的修法

若暂时装不了检查器：至少写出「你认为检查器会骂哪一行」并在笔记标明。

**验收**：有笔记；错误与修复成对出现。

---

## 挑战题（可选）

### C1. 迷你 Agent 类型化

综合实现并标注：

- `Message` TypedDict + `Role` Literal
- `LLMClient` Protocol
- `Tool[T]` Generic（或非泛型但注解清晰）
- `run(llm, tools, user_input) -> str`

要求：公共函数都有注解；用 EchoLLM 跑通。

**验收**：可运行；文件顶部可加 `from __future__ import annotations`。

---

### C2. TypedDict vs dataclass（书面）

写 `c2_notes.md`（10 行内）：在「LLM API 响应 JSON」和「Agent 运行时状态」两个场景，你分别选 TypedDict 还是 dataclass，为什么。

**验收**：有明确选择，不是两边都说「都可以」糊弄过去。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成
- [ ] 能口述：注解不运行时强制；Protocol 与 ABC 差异；TypedDict 适用场景
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 模块 02 通关自检（本章做完后）

- [ ] OOP：组合优先、ABC/dataclass/property 会用
- [ ] 数据模型：常用 dunder / `__call__` 会读会写
- [ ] 迭代生成：惰性管道会写
- [ ] 装饰器：retry/timed + wraps
- [ ] 上下文：with / contextmanager
- [ ] 异常：自定义层次 + 异常链
- [ ] 类型：Protocol / TypedDict / Generic 基础

全部勾上后，进入模块 03《Python 工程化》。

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。注解帮助读代码与静态检查，**不会**在运行时自动强制类型。

### W1 参考答案

```python
def greet(name: str, times: int = 1) -> str:
    return " ".join([name] * times)


assert greet("A", 2) == "A A"
assert greet("Agent") == "Agent"
```

### W2 参考答案

```python
def label(value: str | None) -> str:
    return "<empty>" if value is None else value


assert label(None) == "<empty>"
assert label("x") == "x"
```

### W3 参考答案

```python
def non_empty(items: list[str]) -> list[str]:
    return [x for x in items if x.strip()]


assert non_empty(["a", " ", "", "b"]) == ["a", "b"]
```

### W4 参考答案

```python
Messages = list[dict[str, str]]


def count_messages(messages: Messages) -> int:
    return len(messages)


assert count_messages([{"role": "user", "content": "hi"}]) == 1
```

### B1 思路 + 参考答案

**思路**

1. `clip`：`str` in / `str` out；`max_len: int`。
2. `safe_get` 可用 `TypeVar` 或简化为 `dict[str, object]`。
3. `average` 空列表返回 `None` → 返回类型 `float | None`。

**参考答案**

```python
from typing import TypeVar

T = TypeVar("T")


def clip(text: str, max_len: int = 20) -> str:
    if max_len < 3:
        raise ValueError("max_len must be >= 3")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def safe_get(mapping: dict[str, T], key: str, default: T | None = None) -> T | None:
    return mapping[key] if key in mapping else default


def average(nums: list[float]) -> float | None:
    if not nums:
        return None
    return sum(nums) / len(nums)


assert clip("abcdefghij", 8) == "abcde..."
assert safe_get({"a": 1}, "a") == 1
assert safe_get({"a": 1}, "b") is None
assert average([]) is None
assert average([1, 2, 3]) == 2
```

### B2 思路 + 参考答案

**思路**

`Literal` 收窄合法 role；运行时仍要用集合校验。需要时用 `typing.cast` 帮助检查器。

**参考答案**

```python
from typing import Literal, cast

Role = Literal["system", "user", "assistant", "tool"]
ALLOWED: set[str] = {"system", "user", "assistant", "tool"}


def assert_role(role: str) -> Role:
    if role not in ALLOWED:
        raise ValueError(f"invalid role: {role!r}")
    return cast(Role, role)


def create_message(role: Role, content: str) -> dict[str, str]:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("content empty")
    return {"role": role, "content": cleaned}


assert create_message("user", "hi")["role"] == "user"
assert assert_role("assistant") == "assistant"
try:
    assert_role("worker")
    raise AssertionError("should have raised")
except ValueError:
    pass

# 期望类型检查报警（可选）：
# create_message("worker", "x")
```

### B3 思路 + 参考答案

**思路**

TypedDict 描述「长得像 dict 的结构化数据」，很适合消息列表；`append_message` 返回新 list。

**参考答案**

```python
from typing import Literal, TypedDict

Role = Literal["system", "user", "assistant", "tool"]


class Message(TypedDict):
    role: Role
    content: str


def append_message(
    messages: list[Message],
    role: Role,
    content: str,
) -> list[Message]:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("content empty")
    new_item: Message = {"role": role, "content": cleaned}
    return [*messages, new_item]


def contents(messages: list[Message]) -> list[str]:
    return [m["content"] for m in messages]


original: list[Message] = [{"role": "system", "content": "sys"}]
updated = append_message(original, "user", "  hi  ")
assert original == [{"role": "system", "content": "sys"}]  # 未修改
assert contents(updated) == ["sys", "hi"]
```

### B4 思路 + 参考答案

**思路**

Protocol 是结构化子类型：只要有兼容方法即可，不必继承。适合「可替换 LLM」。

**参考答案**

```python
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class EchoLLM:
    def complete(self, prompt: str) -> str:
        return "ECHO: " + prompt


class UpperLLM:
    def complete(self, prompt: str) -> str:
        return prompt.upper()


def ask(llm: LLMClient, prompt: str) -> str:
    return llm.complete(prompt)


assert ask(EchoLLM(), "hi") == "ECHO: hi"
assert ask(UpperLLM(), "hi") == "HI"
```

### A1 思路 + 参考答案

**思路**

`TypeVar` + `Generic[T]` 让 `ToolResult` 携带结果类型；`unwrap` 原样取出。

**参考答案**

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class ToolResult(Generic[T]):
    def __init__(self, name: str, value: T) -> None:
        self.name = name
        self.value = value


def unwrap(result: ToolResult[T]) -> T:
    return result.value


docs = ToolResult[list[str]]("search", ["a", "b"])
num = ToolResult[float]("calc", 3.0)
assert unwrap(docs) == ["a", "b"]
assert unwrap(num) == 3.0
```

### A2 思路 + 参考答案

**思路**

故意制造检查器错误，再对照修复；重点建立「注解会被工具检查」的直觉。

**参考答案**（示例笔记内容）

`a2_notes.md`：

```text
1) create_message("worker", "x")
   报错：Literal 不允许 "worker"
   修法：先 assert_role，或改正字符串

2) def f(x: str) -> int: return len(x)
   f(None)
   报错：None 不能当 str
   修法：参数改为 str | None 并分支处理

3) class Bad: pass
   ask(Bad(), "hi")
   报错：缺少 complete 方法，不满足 Protocol
   修法：补上 complete
```

示意代码（勿提交为「正确答案」而不改）：

```python
# 错误示范（给检查器用）
# ask(object(), "hi")  # Protocol 不满足
```

### C1 思路 + 参考答案

**思路**

把消息、LLM、工具都标清楚；`run` 只依赖 Protocol / 注解，便于后续换实现。

**参考答案**

```python
from __future__ import annotations

from typing import Generic, Literal, Protocol, TypedDict, TypeVar

Role = Literal["system", "user", "assistant", "tool"]
T = TypeVar("T")


class Message(TypedDict):
    role: Role
    content: str


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class EchoLLM:
    def complete(self, prompt: str) -> str:
        return "ECHO: " + prompt


class Tool(Generic[T]):
    def __init__(self, name: str, handler: type[object] | object = None) -> None:
        # 简化：直接存可调用
        self.name = name
        self._handler = handler

    def run(self, **kwargs: object) -> T:
        return self._handler(**kwargs)  # type: ignore[operator]


def search_handler(query: str, top_k: int = 2) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


def run(llm: LLMClient, tools: dict[str, Tool[object]], user_input: str) -> str:
    search = tools["search"]
    docs = search.run(query=user_input, top_k=2)
    prompt = f"user={user_input}; docs={docs}"
    return llm.complete(prompt)


tools: dict[str, Tool[object]] = {
    "search": Tool("search", search_handler),
}
answer = run(EchoLLM(), tools, "RAG")
assert answer.startswith("ECHO:")
assert "doc:RAG:0" in answer
```

更干净的写法（推荐，避免上面 `type: ignore`）：

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Generic, Literal, Protocol, TypedDict, TypeVar

Role = Literal["system", "user", "assistant", "tool"]
T = TypeVar("T")


class Message(TypedDict):
    role: Role
    content: str


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class EchoLLM:
    def complete(self, prompt: str) -> str:
        return "ECHO: " + prompt


class Tool(Generic[T]):
    def __init__(self, name: str, handler: Callable[..., T]) -> None:
        self.name = name
        self.handler = handler

    def run(self, **kwargs: object) -> T:
        return self.handler(**kwargs)


def run(
    llm: LLMClient,
    tools: dict[str, Tool[object]],
    user_input: str,
) -> str:
    docs = tools["search"].run(query=user_input, top_k=2)
    return llm.complete(f"user={user_input}; docs={docs}")


tools = {
    "search": Tool[object](
        "search",
        lambda query, top_k=2: [f"doc:{query}:{i}" for i in range(top_k)],
    )
}
assert run(EchoLLM(), tools, "RAG").startswith("ECHO:")
```

### C2 思路 + 参考答案

`c2_notes.md` 示例：

```text
1) LLM API 响应 JSON → 优先 TypedDict
   原因：边界数据本质是 dict/JSON，字段可选多，序列化友好，不必强行 class。

2) Agent 运行时状态（会话、会话计数、内部缓冲）→ 优先 dataclass
   原因：有行为/不变量、需要方法与默认工厂，实例身份更清晰。

一句话：外边界用 TypedDict 描述形状；内核心用 dataclass（或普通类）承载行为。
```
