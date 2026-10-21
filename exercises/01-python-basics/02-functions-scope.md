# 练习：函数与作用域

> 对应文档：`[docs/01-python-basics/02-functions-scope.md](../../docs/01-python-basics/02-functions-scope.md)`  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：每题很小，用来把 `return`、默认参数、`*args`、闭包、可变默认参数踩一遍；做完再上基础题会顺很多。
4. 建议代码目录：

```text
playground/01-python-basics/02-functions-scope/
```

5. 先自己做完，再看文末「提示与参考答案」。计算型函数请 `return`，不要只靠 `print` 交差。

---

## 热身题（建议先做）

> 每题控制在几分钟内。不必写成大项目；在 playground 里逐题跑通即可。

### W1. 最简单的 `return`：`add`

**给定**：两个数字 `a`、`b`。

**要求**：实现 `add(a, b)`，用 `return` 返回二者之和（不要只 `print`）。

**期望输出 / 验收**：

```python
assert add(2, 3) == 5
assert add(-1, 1) == 0
```

---

### W2. 默认参数：打招呼

**给定**：名字与可选称呼后缀。

**要求**：实现 `greet(name, suffix="!")`，返回形如 `"Hello, Alice!"` 的字符串；不传 `suffix` 时用默认的 `"!"`。

**期望输出 / 验收**：

```python
assert greet("Alice") == "Hello, Alice!"
assert greet("Bob", suffix="~") == "Hello, Bob~"
```

---

### W3. 无 `return` 时拿到 `None`

**给定**：下面这个「看起来在做事」的函数：

```python
def shout(text):
    print(text.upper())
    # 故意不写 return
```

**要求**：

1. 调用 `result = shout("hi")`，观察打印与 `result` 的值。
2. 用一句话写下结论：没有 `return`（或只写了 `return` 没带值）时，调用方拿到什么？

**验收**：能确认 `result is None`，并口头说清「打印 ≠ 返回值」。

---

### W4. `*args`：收集几个字符串

**给定**：不定数量的字符串参数。

**要求**：实现 `join_words(*words)`，用空格把传入的所有字符串拼成一句；一个都不传时返回空字符串 `""`。

**期望输出 / 验收**：

```python
assert join_words("RAG", "is", "cool") == "RAG is cool"
assert join_words("hi") == "hi"
assert join_words() == ""
```

---

### W5. 闭包：`make_greeter(name)`

**给定**：一个固定的名字。

**要求**：实现 `make_greeter(name)`，返回一个**无参**函数；调用返回的函数时，得到 `"Hi, <name>"`。

**期望输出 / 验收**：

```python
hi_alice = make_greeter("Alice")
hi_bob = make_greeter("Bob")
assert hi_alice() == "Hi, Alice"
assert hi_bob() == "Hi, Bob"
```

---

### W6. 可变默认参数：先踩坑再修复

**给定**（错误示范，请先原样试跑）：

```python
def append_item(item, bucket=[]):
    bucket.append(item)
    return bucket
```

**要求**：

1. **踩坑**：连续调用两次不传 `bucket`（例如先 `"a"` 再 `"b"`），观察两次返回值是否「串味」。
2. **修复**：改成默认「空列表」且多次调用互不污染（提示：`None` 哨兵）。

**验收**：

```python
# 修复后应满足：
assert append_item("a") == ["a"]
assert append_item("b") == ["b"]  # 不能是 ["a", "b"]
```

---

## 基础题（必做）

### B1. 函数定义与返回值：消息工厂

实现：

```python
def create_message(
    role: str,
    content: str,
    *,
    name: str | None = None,
) -> dict:
    ...
```

要求：

1. 返回字典，至少包含 `"role"`、`"content"`
2. 仅当 `name is not None` 时加入 `"name"` 字段
3. `content` 先 `.strip()`；若 strip 后为空，抛出 `ValueError("content empty")`
4. `role` 只允许：`"system"` / `"user"` / `"assistant"` / `"tool"`，否则抛出 `ValueError`

自行写几组调用做验证（正常 + 异常）。

**验收**：非法 role / 空 content 会报错；合法调用返回结构正确，且 `name` 缺省时键不存在（不是 `"name": None`）。

---

### B2. `*args` / `**kwargs`：工具调用构建与转发

实现两个函数：

```python
def build_tool_call(name: str, **arguments) -> dict:
    """返回 {"name": name, "arguments": arguments}"""


def run_tool(tool_call: dict, registry: dict) -> dict:
    """
    registry 形如：{"search": search_fn, "calc": calc_fn}
    从 tool_call 取出 name / arguments，调用对应函数。
    返回 {"name": name, "result": ..., "ok": True/False}
    """
```

约定：

1. `build_tool_call("search", query="RAG", top_k=3)` 得到标准结构
2. `run_tool` 若 name 不在 registry：`ok=False`，`result` 为错误说明字符串
3. 若调用函数过程抛异常：捕获后 `ok=False`，`result` 为异常字符串
4. 成功则 `ok=True`，`result` 为函数返回值

可先在 registry 里放两个假工具：

```python
def search(query: str, top_k: int = 5) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


def calc(expression: str) -> float:
    # 练习里允许用安全的极简实现，例如只处理 "1+2" 这类；
    # 或直接写死几个 case。不要用 eval 处理任意字符串（习惯上不安全）。
    ...
```

**验收**：成功 / 未知工具 / 工具抛错 三条路径都能跑通。

---

### B3. 作用域与闭包：计数器与限流器

1. 实现 `make_counter(start: int = 0)`，返回一个无参函数；每调用一次返回递增后的值。
2. 实现 `make_rate_limiter(max_calls: int)`，返回函数 `allow() -> bool`：
  - 前 `max_calls` 次调用返回 `True`
  - 之后返回 `False`
  - 内部用闭包计数（需要 `nonlocal`）

**验收**：

```python
c = make_counter(10)
assert c() == 11 and c() == 12

limit = make_rate_limiter(2)
assert limit() is True and limit() is True and limit() is False
```

---

### B4. lambda 与排序

给定：

```python
tool_results = [
    {"name": "browse", "ok": False, "latency_ms": 800},
    {"name": "search", "ok": True, "latency_ms": 120},
    {"name": "calc", "ok": True, "latency_ms": 30},
    {"name": "search", "ok": True, "latency_ms": 90},
]
```

要求（可用 `sorted` + `lambda`，也可先 `def` 再当 key）：

1. 得到 `ok_first`：先按 `ok` 降序（True 在前），再按 `latency_ms` 升序
2. 得到 `names`：所有 `ok is True` 的工具名列表（推导式或 filter 均可）

**验收**：`ok_first[0]["name"] == "calc"`；`names` 含 `search`/`calc`，不含失败的 `browse`。

---

## 进阶题（建议至少做 1 题）

### A1. 修复可变默认参数 + 不可变更新

下面函数有 bug，请改成正确版本，并补充测试证明多次调用互不影响：

```python
def add_message(history, message):
    # 错误示范思路：用 history=[] 当默认值
    history.append(message)
    return history
```

正确要求：

1. `history` 默认应为「空历史」，多次调用互不污染
2. **不要修改**传入的原 list；返回新 list
  （即：调用方传入的 list 内容保持不变）

---

### A2. partial 配置聊天函数

```python
def chat(model: str, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> dict:
    return {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
```

用 `functools.partial` 生成：

- `ask_strict`：`model="gpt-4.1-mini"`, `temperature=0`, `max_tokens=256`
- 再调用 `ask_strict(prompt="一句话解释闭包")` 并打印结果

**验收**：返回 dict 中预填字段正确，且只需传 `prompt`。

---

## 挑战题（可选）

### C1. 迷你 Tool Runtime

综合本章，实现一个极简运行时：

```python
class_or_functions_whatever_you_like = ...

# 期望能力：
# 1) register(name, fn) 注册工具
# 2) call(name, **kwargs) 调用工具，返回 {ok, result, name}
# 3) 提供 calls() -> int 统计成功调用次数（闭包或对象属性均可）
# 4) 提供 with_logging(fn) 高阶函数：包装后先打印 "calling <name>" 再执行
```

约束：

- 注册时若 name 重复，直接覆盖或拒绝均可，但要在注释里说明
- `call` 内部应使用 `**kwargs` 转发给工具
- 写一段 demo：注册 `search`/`calc`，成功调用 + 一次失败调用

**验收**：别人只看你的 demo，能看懂如何注册与调用。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W6 先做完，建立手感
- [ ] **通过线**：B1～B4 全部完成，关键路径有断言或清晰打印
- [ ] 能口述：可变默认参数为什么危险；闭包里何时需要 `nonlocal`
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。答案不是唯一写法，能通过验收、意图清晰即可。

W1 参考答案

```python
def add(a, b):
    return a + b
```

W2 参考答案

```python
def greet(name, suffix="!"):
    return f"Hello, {name}{suffix}"
```

W3 参考答案

```python
def shout(text):
    print(text.upper())
    # 无 return → 调用方得到 None


result = shout("hi")  # 会打印 HI
assert result is None
# 结论：print 只负责显示；没有 return 时返回值是 None
```

W4 参考答案

```python
def join_words(*words):
    return " ".join(words)
```

W5 参考答案

```python
def make_greeter(name):
    def greet():
        return f"Hi, {name}"

    return greet
```

W6 参考答案

```python
# 踩坑：默认 list 只创建一次，两次调用会共享同一个 bucket
# 修复：用 None 作哨兵，函数体内再 new 列表

def append_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket


assert append_item("a") == ["a"]
assert append_item("b") == ["b"]
```

B1 思路 + 参考答案

**思路**

1. 先校验再组装：非法输入尽早 `raise`，避免半成品 dict。
2. `content` 先 `strip` 再判空；写入字典的也是 strip 后的值。
3. `name` 在 `*` 之后 → 只能关键字传入；`None` 时**不要**写入键。
4. 允许的 `role` 用集合 `in` 判断更直观。

**参考答案**

```python
ALLOWED_ROLES = {"system", "user", "assistant", "tool"}


def create_message(
    role: str,
    content: str,
    *,
    name: str | None = None,
) -> dict:
    """构造一条聊天消息字典；非法 role / 空 content 抛 ValueError。"""
    # 1) 校验 role：不在白名单直接失败
    if role not in ALLOWED_ROLES:
        raise ValueError(f"invalid role: {role!r}")

    # 2) 清洗 content：去掉首尾空白后再判空
    cleaned = content.strip()
    if not cleaned:
        # 题目约定错误文案为 "content empty"
        raise ValueError("content empty")

    # 3) 先放必填字段
    message: dict = {
        "role": role,
        "content": cleaned,
    }

    # 4) 仅当调用方显式传入 name 时才写入键
    #    注意：缺省是「键不存在」，不是 "name": None
    if name is not None:
        message["name"] = name

    return message


# ---- 验证：正常路径 ----
assert create_message("user", "  hi  ") == {"role": "user", "content": "hi"}
assert "name" not in create_message("assistant", "ok")
assert create_message("tool", "done", name="search")["name"] == "search"

# ---- 验证：异常路径 ----
try:
    create_message("worker", "hi")
    raise AssertionError("should have raised")
except ValueError:
    pass

try:
    create_message("user", "   ")
    raise AssertionError("should have raised")
except ValueError as exc:
    assert str(exc) == "content empty"
```

B2 思路 + 参考答案

**思路**

1. `build_tool_call`：`**arguments` 直接收成 dict，原样塞进返回结构。
2. `run_tool` 三条路径：未知工具 / 调用异常 / 成功。
3. 转发参数用 `fn(**arguments)`，这是 `**kwargs` 最典型的用法。
4. `calc` 练习里用查表即可，不要 `eval` 任意字符串。

**参考答案**

```python
def build_tool_call(name: str, **arguments) -> dict:
    """把工具名与关键字参数打包成标准 tool_call 结构。"""
    return {
        "name": name,
        # arguments 本身就是一个 dict，例如 {"query": "RAG", "top_k": 3}
        "arguments": arguments,
    }


def run_tool(tool_call: dict, registry: dict) -> dict:
    """
    按 registry 查找并调用工具。
    成功：{"name", "result", "ok": True}
    失败：{"name", "result": 错误说明, "ok": False}
    """
    name = tool_call["name"]
    arguments = tool_call.get("arguments", {})

    # 路径 1：工具未注册
    fn = registry.get(name)
    if fn is None:
        return {
            "name": name,
            "ok": False,
            "result": f"unknown tool: {name}",
        }

    # 路径 2 / 3：调用；异常要吞掉并标记 ok=False
    try:
        result = fn(**arguments)
        return {"name": name, "ok": True, "result": result}
    except Exception as exc:
        return {"name": name, "ok": False, "result": str(exc)}


# ---- 假工具 ----
def search(query: str, top_k: int = 5) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


def calc(expression: str) -> float:
    # 极简安全实现：只认白名单表达式，避免 eval
    table = {"1+2": 3.0, "10/2": 5.0, "3*4": 12.0}
    if expression not in table:
        raise ValueError(f"unsupported expression: {expression!r}")
    return table[expression]


registry = {"search": search, "calc": calc}

# 成功
call1 = build_tool_call("search", query="RAG", top_k=3)
assert run_tool(call1, registry)["ok"] is True
assert run_tool(call1, registry)["result"] == ["doc:RAG:0", "doc:RAG:1", "doc:RAG:2"]

# 未知工具
call2 = build_tool_call("browse", url="https://x")
assert run_tool(call2, registry)["ok"] is False

# 工具抛错
call3 = build_tool_call("calc", expression="1/0")
assert run_tool(call3, registry)["ok"] is False
```

B3 思路 + 参考答案

**思路**

1. 外层函数创建局部变量 `count`，内层函数读取/修改它 → 闭包。
2. 内层若要对 `count` **赋值**，必须写 `nonlocal count`，否则会当成内层新局部变量。
3. `make_counter`：每次 `+1` 后返回新值。
4. `make_rate_limiter`：前 `max_calls` 次放行，之后一律 `False`。

**参考答案**

```python
def make_counter(start: int = 0):
    """返回一个无参计数器：每次调用返回「递增后」的值。"""
    count = start  # 闭包捕获的状态

    def inc() -> int:
        # 没有 nonlocal 时，下一行的 count = ... 会让 Python
        # 把 count 当成 inc 的局部变量，进而读未绑定就报错
        nonlocal count
        count += 1
        return count

    return inc


def make_rate_limiter(max_calls: int):
    """返回 allow()：前 max_calls 次 True，之后 False。"""
    count = 0

    def allow() -> bool:
        nonlocal count
        if count < max_calls:
            count += 1
            return True
        return False

    return allow


# ---- 验收 ----
c = make_counter(10)
assert c() == 11 and c() == 12

limit = make_rate_limiter(2)
assert limit() is True and limit() is True and limit() is False

# 两个 limiter 状态互不影响
limit2 = make_rate_limiter(1)
assert limit2() is True and limit2() is False
```

B4 思路 + 参考答案

**思路**

1. `sorted` 的 `key` 返回元组时，按元组元素从左到右比较。
2. 想让 `ok=True` 排前面：用 `not r["ok"]`（False 排在 True 前），或用 `(-int(r["ok"]), ...)`。
3. 第二关键字直接用 `latency_ms` 升序。
4. `names`：过滤 `ok is True` 再取 `name`。

**参考答案**

```python
tool_results = [
    {"name": "browse", "ok": False, "latency_ms": 800},
    {"name": "search", "ok": True, "latency_ms": 120},
    {"name": "calc", "ok": True, "latency_ms": 30},
    {"name": "search", "ok": True, "latency_ms": 90},
]

# key 元组：(是否失败, 延迟)
# not ok → False(成功) < True(失败)，因此成功整体在前
# 成功组内再按 latency_ms 升序 → calc(30) 会成为第一名
ok_first = sorted(
    tool_results,
    key=lambda r: (not r["ok"], r["latency_ms"]),
)

# 只要成功工具的名字；顺序跟随原列表出现顺序即可
names = [r["name"] for r in tool_results if r["ok"] is True]
# 等价写法：list(filter(...)) 或 [r["name"] for r in tool_results if r["ok"]]

assert ok_first[0]["name"] == "calc"
assert "browse" not in names
assert set(names) == {"search", "calc"}
# 更细一点：成功三条按延迟应是 calc → search(90) → search(120)
assert [r["name"] for r in ok_first if r["ok"]] == ["calc", "search", "search"]
```

A1 思路 + 参考答案

**思路**

1. **可变默认参数陷阱**：`def f(history=[])` 会让所有调用共享同一个 list。
2. 正确默认值写法：`history: list | None = None`，函数体内再创建新 list。
3. 题目还要求**不修改传入的原 list**：先浅拷贝再 append，返回新对象。

**参考答案**

```python
def add_message(
    history: list | None = None,
    message: object = None,
) -> list:
    """
    追加一条消息，返回新历史。
    - 默认空历史：多次调用互不污染
    - 不修改调用方传入的原 list
    """
    # None → 新空列表；否则浅拷贝，切断与原 list 的别名关系
    base = [] if history is None else list(history)
    base.append(message)
    return base


# ---- 证明：默认参数不共享 ----
h1 = add_message(message={"role": "user", "content": "a"})
h2 = add_message(message={"role": "user", "content": "b"})
assert h1 == [{"role": "user", "content": "a"}]
assert h2 == [{"role": "user", "content": "b"}]
assert h1 is not h2

# ---- 证明：不修改传入的原 list ----
original = [{"role": "system", "content": "hi"}]
updated = add_message(original, {"role": "user", "content": "q"})
assert original == [{"role": "system", "content": "hi"}]  # 原列表未变
assert len(updated) == 2
assert updated[1]["content"] == "q"
```

错误对照（不要这样写）：

```python
def add_message_bad(history=[], message=None):  # 危险：默认 list 只创建一次
    history.append(message)
    return history
```

A2 思路 + 参考答案

**思路**

1. `functools.partial` 预填一部分参数，得到「参数更少」的新可调用对象。
2. 预填 `model` / `temperature` / `max_tokens` 后，调用时只需传 `prompt`。
3. `partial` 适合「同一配置反复调用」；和装饰器不同，它不改变原函数。

**参考答案**

```python
from functools import partial


def chat(
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> dict:
    return {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


# 预填严格配置：低温 + 较短输出
ask_strict = partial(
    chat,
    model="gpt-4.1-mini",
    temperature=0,
    max_tokens=256,
)

result = ask_strict(prompt="一句话解释闭包")
print(result)

assert result["model"] == "gpt-4.1-mini"
assert result["temperature"] == 0
assert result["max_tokens"] == 256
assert result["prompt"] == "一句话解释闭包"
```

C1 思路 + 参考答案

**思路**

1. 用类或闭包都行；下面用类更直观：`register` / `call` / `calls` 都挂在同一对象上。
2. `call` 内部 `fn(**kwargs)` 转发；统计**成功**次数。
3. `with_logging` 是高阶函数：吃进一个函数，返回包装后的函数。
4. 注册重名策略这里选择**覆盖**，并在注释说明。

**参考答案**

```python
from collections.abc import Callable
from typing import Any


class ToolRuntime:
    """极简工具运行时：注册、调用、成功计数、日志包装。"""

    def __init__(self) -> None:
        self._registry: dict[str, Callable[..., Any]] = {}
        self._success_count = 0

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        # 策略：同名直接覆盖（也可改成 raise ValueError 拒绝重复）
        self._registry[name] = fn

    def call(self, name: str, **kwargs: Any) -> dict:
        fn = self._registry.get(name)
        if fn is None:
            return {
                "name": name,
                "ok": False,
                "result": f"unknown tool: {name}",
            }
        try:
            result = fn(**kwargs)  # **kwargs 原样转发给工具
            self._success_count += 1
            return {"name": name, "ok": True, "result": result}
        except Exception as exc:
            return {"name": name, "ok": False, "result": str(exc)}

    def calls(self) -> int:
        """仅统计成功调用次数。"""
        return self._success_count

    def with_logging(self, name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
        """高阶函数：包装后先打印 calling <name>，再执行原函数。"""

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"calling {name}")
            return fn(*args, **kwargs)

        return wrapper


# ---- demo ----
def search(query: str, top_k: int = 5) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


def calc(expression: str) -> float:
    table = {"1+2": 3.0, "10/2": 5.0}
    if expression not in table:
        raise ValueError(f"unsupported: {expression!r}")
    return table[expression]


rt = ToolRuntime()
# 注册时包一层日志，便于观察调用
rt.register("search", rt.with_logging("search", search))
rt.register("calc", calc)

print(rt.call("search", query="RAG", top_k=2))
# → 先打印 calling search，再返回 ok=True

print(rt.call("calc", expression="1+2"))  # 成功
print(rt.call("calc", expression="boom"))  # 失败：ok=False
print(rt.call("browse", url="x"))  # 未知工具

assert rt.calls() == 2  # 仅两次成功计入
```

若更偏好闭包风格，也可把 `registry` / `success_count` 放在外层函数里，返回一个含 `register/call/calls/with_logging` 的小对象或 dict of functions；验收标准相同。