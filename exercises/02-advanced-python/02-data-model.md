# 练习：Python 数据模型

> 对应文档：[`docs/02-advanced-python/02-data-model.md`](../../docs/02-advanced-python/02-data-model.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先练 `__len__` / `__str__` / `__call__`，再写容器与 Registry。
4. 建议代码目录：

```text
playground/02-advanced-python/02-data-model/
```

5. 每题写少量断言或清晰打印；先做题再看文末答案。

---

## 热身题（建议先做）

### W1. `__len__` 与 `len()`

**要求**：类 `Bag` 内部有 `_items: list`，实现 `__len__`。

**验收**：`len(Bag([1, 2])) == 2`。

---

### W2. `__str__` vs `__repr__`

**要求**：类 `Tag` 令 `str(tag) == "hi"`，`repr(tag)` 含类名（例如 `"Tag('hi')"`）。

**验收**：`str(tag) != repr(tag)`。

---

### W3. `__call__` 让对象可调用

**要求**：类 `Adder(n)`，`Adder(3)(4) == 7`。

**验收**：`callable(Adder(3)) is True`。

---

### W4. `__contains__` 与 `in`

**要求**：类 `RoleSet`，支持 `"user" in RoleSet(["user", "assistant"])`。

**验收**：`"tool" in RoleSet(["user"])` 为 False。

---

## 基础题（必做）

### B1. 协议对照表（书面 + 代码）

1. 在 `b1_notes.md` 中列出至少 6 组对照：`写法 → dunder`
2. 写一个最小类 `Demo`，实现 `__str__` 与 `__repr__`，并打印证明二者不同

**验收**：笔记存在；`str(demo) != repr(demo)`（内容不同即可）。

---

### B2. MessageList 容器协议

实现 `MessageList`，内部存 `dict` 或简单对象均可，需支持：

```python
messages.add("user", "hi")
len(messages)
"user" in messages          # 按 role 判断
messages[0]                 # 取第 0 条
for m in messages: ...      # 可迭代
bool(messages)              # 空为 False
```

额外要求：

- 索引越界抛 `IndexError`
- `messages[0]` **推荐返回拷贝**（改返回值不影响内部）

**验收**：上述操作均可运行；空列表 `if messages:` 为假。

---

### B3. 可调用 Tool

实现：

```python
@dataclass
class Tool:
    name: str
    handler: Callable[..., object]

    def __call__(self, **kwargs): ...
    def __str__(self) -> str: ...
```

再用它包装假 `calc`，调用 `tool(expression="1+2")`。

**验收**：`callable(tool) is True`；`print(tool)` 友好；调用返回正确结果。

---

### B4. `__eq__` 与业务去重

实现 `ToolCall(name: str, arguments: dict)`：

1. 同 name + 同 arguments → 相等
2. 写函数 `unique_calls(calls) -> list[ToolCall]` 去重且保序

注意：`dict` 不能直接放进 `set`；可用 `(name, json.dumps(arguments, sort_keys=True))` 作签名。

**验收**：输入 4 条含重复，输出去重后数量正确且顺序保留首次出现。

---

## 进阶题（建议至少做 1 题）

### A1. 完整 ToolRegistry

实现：

- `register` / `__len__` / `__contains__` / `__getitem__` / `__iter__` / `__repr__`
- 通过 `registry["search"](query="x")` 直接调用

未知工具名时 `__getitem__` 抛 `KeyError`。

**验收**：注册 2 个工具后，遍历名称集合与 `repr(registry)` 合理。

---

### A2. 可调用重试器

实现 `Retry(max_attempts: int)`：

- `__call__(self, fn, *args, **kwargs)` 按次数重试
- 属性 `attempts` 记录总共尝试次数（跨多次调用可累计，或每次调用重置——在注释说明）
- 最终失败抛 `RuntimeError`，并用 `from` 链接最后一次异常

写一个「前两次失败、第三次成功」的假函数验证。

**验收**：成功路径返回值正确；一直失败时异常类型正确。

---

## 挑战题（可选）

### C1. 描述符：NonEmptyName（选做）

实现 `NonEmpty` 描述符，用于：

```python
class ToolSpec:
    name = NonEmpty("name")
```

空字符串或空白赋值时报错；正常赋值自动 strip。

**验收**：非法赋值抛 `ValueError`；合法赋值后读回无首尾空格。

---

### C2. TokenBudget 小对象（贴近 Agent）

实现 `TokenBudget(limit: int)`：

- `consume(n: int)` 扣减
- `remaining` property
- `__bool__`：还有剩余额度则为 True
- `__lt__`：可与另一 budget 比 remaining（自行定义并写清）

模拟：多轮 tool calling 每轮消耗若干 token，额度用尽停止。

**验收**：循环在额度用尽时停止；打印剩余额度。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成
- [ ] 能不看资料说出至少 5 个「语法 → dunder」
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。

### W1 参考答案

```python
class Bag:
    def __init__(self, items: list) -> None:
        self._items = list(items)

    def __len__(self) -> int:
        return len(self._items)


assert len(Bag([1, 2])) == 2
```

### W2 参考答案

```python
class Tag:
    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Tag({self.value!r})"


tag = Tag("hi")
assert str(tag) == "hi"
assert repr(tag) == "Tag('hi')"
assert str(tag) != repr(tag)
```

### W3 参考答案

```python
class Adder:
    def __init__(self, n: int) -> None:
        self.n = n

    def __call__(self, x: int) -> int:
        return self.n + x


assert callable(Adder(3))
assert Adder(3)(4) == 7
```

### W4 参考答案

```python
class RoleSet:
    def __init__(self, roles: list[str]) -> None:
        self._roles = set(roles)

    def __contains__(self, role: object) -> bool:
        return role in self._roles


assert "user" in RoleSet(["user", "assistant"])
assert "tool" not in RoleSet(["user"])
```

### B1 思路 + 参考答案

**思路**

至少覆盖：`len` → `__len__`；`in` → `__contains__`；下标 → `__getitem__`；`str` / `repr`；调用 `obj()` → `__call__`；`for` → `__iter__`。

**参考答案**

`b1_notes.md` 示例：

```text
len(x)      → x.__len__()
x in y      → y.__contains__(x)
x[i]        → x.__getitem__(i)
str(x)      → x.__str__()
repr(x)     → x.__repr__()
x()         → x.__call__()
for i in x  → x.__iter__()
```

```python
class Demo:
    def __str__(self) -> str:
        return "friendly"

    def __repr__(self) -> str:
        return "Demo(debug=True)"


demo = Demo()
print(str(demo), repr(demo))
assert str(demo) != repr(demo)
```

### B2 思路 + 参考答案

**思路**

1. `__contains__` 比较 role；`__bool__` 可显式写，或只写 `__len__`。
2. 迭代 `return iter(self._items)`；下标返回拷贝。

**参考答案**

```python
class MessageList:
    def __init__(self) -> None:
        self._items: list[dict] = []

    def add(self, role: str, content: str) -> None:
        self._items.append({"role": role, "content": content})

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return len(self._items) > 0

    def __contains__(self, role: object) -> bool:
        return any(m["role"] == role for m in self._items)

    def __getitem__(self, index: int) -> dict:
        return dict(self._items[index])  # 拷贝

    def __iter__(self):
        return iter(self._items)


messages = MessageList()
assert not messages
messages.add("user", "hi")
messages.add("assistant", "ok")
assert len(messages) == 2
assert "user" in messages
assert messages[0]["content"] == "hi"
messages[0]["content"] = "hacked"
assert messages[0]["content"] == "hi"  # 内部未变
roles = [m["role"] for m in messages]
assert roles == ["user", "assistant"]
```

### B3 思路 + 参考答案

**思路**

`__call__` 内转发 `self.handler(**kwargs)`；`__str__` 给人看，`__repr__` 可更偏调试。

**参考答案**

```python
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    handler: Callable[..., object]

    def __call__(self, **kwargs: object) -> object:
        return self.handler(**kwargs)

    def __str__(self) -> str:
        return f"Tool<{self.name}>"


def calc(expression: str) -> float:
    table = {"1+2": 3.0, "10/2": 5.0}
    if expression not in table:
        raise ValueError(expression)
    return table[expression]


tool = Tool("calc", calc)
assert callable(tool) is True
assert tool(expression="1+2") == 3.0
assert str(tool) == "Tool<calc>"
print(tool)
```

### B4 思路 + 参考答案

**思路**

1. `__eq__` 比较 name 与 arguments。
2. 去重用签名集合保序：首次出现才加入结果。

**参考答案**

```python
import json
from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    arguments: dict

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ToolCall):
            return NotImplemented
        return self.name == other.name and self.arguments == other.arguments

    def signature(self) -> tuple[str, str]:
        return (
            self.name,
            json.dumps(self.arguments, sort_keys=True, ensure_ascii=False),
        )


def unique_calls(calls: list[ToolCall]) -> list[ToolCall]:
    seen: set[tuple[str, str]] = set()
    out: list[ToolCall] = []
    for c in calls:
        sig = c.signature()
        if sig in seen:
            continue
        seen.add(sig)
        out.append(c)
    return out


calls = [
    ToolCall("search", {"q": "RAG"}),
    ToolCall("calc", {"expression": "1+2"}),
    ToolCall("search", {"q": "RAG"}),  # 重复
    ToolCall("search", {"q": "Agent"}),
]
uniq = unique_calls(calls)
assert len(uniq) == 3
assert uniq[0].name == "search" and uniq[0].arguments["q"] == "RAG"
assert uniq[1].name == "calc"
assert uniq[2].arguments["q"] == "Agent"
assert ToolCall("a", {"x": 1}) == ToolCall("a", {"x": 1})
```

### A1 思路 + 参考答案

**思路**

Registry 同时是映射与可调用集合：取出的工具本身可 `__call__`。

**参考答案**

```python
from collections.abc import Callable, Iterator
from typing import Any


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self._tools[name] = fn

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __getitem__(self, name: str) -> Callable[..., Any]:
        if name not in self._tools:
            raise KeyError(name)
        return self._tools[name]

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self._tools))

    def __repr__(self) -> str:
        return f"ToolRegistry({list(self)!r})"


def search(query: str) -> list[str]:
    return [f"doc:{query}"]


def calc(expression: str) -> float:
    return 3.0 if expression == "1+2" else 0.0


registry = ToolRegistry()
registry.register("search", search)
registry.register("calc", calc)
assert len(registry) == 2
assert "search" in registry
assert registry["search"](query="x") == ["doc:x"]
assert list(registry) == ["calc", "search"]
print(repr(registry))
try:
    registry["browse"]
    raise AssertionError("should have raised")
except KeyError:
    pass
```

### A2 思路 + 参考答案

**思路**

循环尝试；捕获异常保存 `last`；次数用尽 `raise RuntimeError(...) from last`。本题选择：**每次 `__call__` 重置 attempts 计数**（也可累计，注释说明即可）。

**参考答案**

```python
class Retry:
    def __init__(self, max_attempts: int) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.max_attempts = max_attempts
        self.attempts = 0  # 最近一次 __call__ 的尝试次数

    def __call__(self, fn, *args, **kwargs):
        # 策略：每次调用重置 attempts（只反映这一次重试过程）
        self.attempts = 0
        last: Exception | None = None
        for _ in range(self.max_attempts):
            self.attempts += 1
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                last = exc
        raise RuntimeError(
            f"failed after {self.max_attempts} attempts"
        ) from last


state = {"n": 0}


def flaky() -> str:
    state["n"] += 1
    if state["n"] < 3:
        raise ConnectionError("tmp")
    return "ok"


retry = Retry(max_attempts=3)
assert retry(flaky) == "ok"
assert retry.attempts == 3

always_fail = Retry(2)
try:
    always_fail(lambda: (_ for _ in ()).throw(ValueError("no")))
    raise AssertionError("should have raised")
except RuntimeError as exc:
    assert isinstance(exc.__cause__, ValueError)
```

### C1 思路 + 参考答案

**思路**

描述符挂在类上；`__set__` 校验后写入私有属性；`__get__` 读回。

**参考答案**

```python
class NonEmpty:
    def __init__(self, name: str) -> None:
        self.public_name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name)

    def __set__(self, obj, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{self.public_name} must be non-empty")
        setattr(obj, self.private_name, value.strip())


class ToolSpec:
    name = NonEmpty("name")

    def __init__(self, name: str) -> None:
        self.name = name


t = ToolSpec("  search  ")
assert t.name == "search"
try:
    t.name = "   "
    raise AssertionError("should have raised")
except ValueError:
    pass
```

### C2 思路 + 参考答案

**思路**

`remaining` 驱动 `__bool__`；循环 `while budget: consume(...)` 模拟多轮工具调用耗 token。

**参考答案**

```python
class TokenBudget:
    def __init__(self, limit: int) -> None:
        if limit < 0:
            raise ValueError("limit must be >= 0")
        self.limit = limit
        self._used = 0

    def consume(self, n: int) -> None:
        if n < 0:
            raise ValueError("n must be >= 0")
        if n > self.remaining:
            raise RuntimeError("budget exceeded")
        self._used += n

    @property
    def remaining(self) -> int:
        return self.limit - self._used

    def __bool__(self) -> bool:
        return self.remaining > 0

    def __lt__(self, other: "TokenBudget") -> bool:
        # 按 remaining 比较
        return self.remaining < other.remaining


budget = TokenBudget(100)
costs = [30, 40, 25, 20]  # 第四轮会不够
rounds = 0
for cost in costs:
    if not budget or budget.remaining < cost:
        break
    budget.consume(cost)
    rounds += 1

assert rounds == 3
assert budget.remaining == 5
print("remaining:", budget.remaining)
assert TokenBudget(1) < TokenBudget(10)
```
