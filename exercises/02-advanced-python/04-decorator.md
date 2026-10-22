# 练习：装饰器

> 对应文档：[`docs/02-advanced-python/04-decorator.md`](../../docs/02-advanced-python/04-decorator.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先写「手动替换函数」与无参装饰器，再上 `retry` / 带参装饰器。
4. 建议代码目录：

```text
playground/02-advanced-python/04-decorator/
```

5. 除题目明确要求外，装饰器请使用 `@functools.wraps`。先做题再看答案。

---

## 热身题（建议先做）

### W1. 手动替换：理解 `@`

**要求**：写 `def deco(fn):` 返回一个 wrapper，打印 `"before"` 再调用原函数。不要用 `@` 语法，手写 `f = deco(f)`。

**验收**：调用后能看到 `before`，且原返回值正确。

---

### W2. 语法糖 `@deco`

**要求**：把 W1 改成 `@deco` 写在函数上方。

**验收**：行为与 W1 相同。

---

### W3. `wraps` 保名

**要求**：无 wraps 与有 wraps 各装饰一个函数，对比 `__name__`。

**验收**：能指出无 wraps 时名字常变成 `wrapper`。

---

### W4. 带参装饰器骨架

**要求**：实现 `@twice`（固定调用 2 次，返回最后一次结果）。可先写死次数，不必通用 `n`。

**验收**：被装饰函数副作用执行 2 次。

---

## 基础题（必做）

### B1. 无参装饰器：`logged`

实现 `@logged`：

- 调用前打印：`CALL <name> args=... kwargs=...`
- 调用后打印：`RET  <name> -> <result>`
- 正确返回原函数结果

用它装饰一个 `add(a, b)` 并调用验证。

**验收**：有前后日志；`add(2, 3) == 5`；`add.__name__ == "add"`。

---

### B2. 带参装饰器：`repeat`

实现：

```python
@repeat(n=3)
def ping():
    print("pong")
    return "ok"
```

**要求**：

1. 本体函数被调用 `n` 次
2. 返回**最后一次**的返回值
3. `n <= 0` 时抛 `ValueError`

**验收**：`ping()` 打印 3 次 `pong`，返回 `"ok"`。

---

### B3. `wraps` 对比实验

写两个装饰器：`plain`（不用 wraps）与 `nice`（用 wraps），都装饰同一函数：

```python
def create_message(role: str, content: str) -> dict:
    """创建消息。"""
    return {"role": role, "content": content}
```

打印对比 `__name__` / `__doc__`。

**验收**：能用输出说明 wraps 保留了什么；注释写一句结论。

---

### B4. `retry`（收窄异常，贴近工具调用）

实现：

```python
@retry(max_attempts=3, exceptions=(ValueError, ConnectionError))
def fetch():
    ...
```

**要求**：

1. 只重试指定异常类型；其它异常立刻抛出
2. 超过次数后抛 `RuntimeError`，并用 `from` 链接最后一次异常
3. 用「前两次 ValueError、第三次成功」验证
4. 另测：抛 `TypeError` 时不重试

**验收**：成功路径返回正确；类型不匹配时立即失败。

---

## 进阶题（建议至少做 1 题）

### A1. `timed` + 装饰器顺序

实现 `@timed`，打印毫秒耗时。  
然后对同一函数分别尝试：

```python
@timed
@retry(max_attempts=3, exceptions=(ConnectionError,))
def call_llm():
    ...

@retry(max_attempts=3, exceptions=(ConnectionError,))
@timed
def call_llm2():
    ...
```

让函数前两次失败、第三次成功。观察两次计时差异，并在 `notes_a1.md` 写 3～5 行：  
**外层 timed 与内层 timed 分别量的是什么。**

**验收**：有笔记；两种顺序都能最终成功。

---

### A2. 简易 `require_fields`

写带参装饰器，确保 kwargs 中包含必需字段：

```python
@require_fields("query", "top_k")
def search(**kwargs):
    return kwargs
```

缺字段时抛 `ValueError`，信息里带上缺失字段名。

**验收**：缺 `top_k` 时报错；字段齐全时正常返回。

---

## 挑战题（可选）

### C1. 类装饰器计数器

用类实现 `@count_calls`：

```python
@count_calls
def work():
    return "done"

work(); work()
print(work.calls)  # 2
```

**验收**：`calls` 可读取；`work.__name__` 尽量仍为 `work`。

---

### C2. Agent 工具装饰器套装

为假工具函数加上：

1. `@require_fields(...)`
2. `@retry(...)`
3. `@timed`

模拟 `search(query: str, top_k: int = 3)`：偶发 `ConnectionError`，最终返回 list。  
写一段 demo 跑通，并打印工具的 `__name__`。

**验收**：缺参失败清晰；网络抖动可恢复；有耗时日志。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成
- [ ] 能口述：`@deco` 等价替换；有参装饰器三层结构；为何需要 wraps
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。

### W1 参考答案

```python
def deco(fn):
    def wrapper(*args, **kwargs):
        print("before")
        return fn(*args, **kwargs)

    return wrapper


def add(a, b):
    return a + b


add = deco(add)
assert add(1, 2) == 3
```

### W2 参考答案

```python
def deco(fn):
    def wrapper(*args, **kwargs):
        print("before")
        return fn(*args, **kwargs)

    return wrapper


@deco
def add(a, b):
    return a + b


assert add(1, 2) == 3
```

### W3 参考答案

```python
import functools


def plain(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def nice(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


@plain
def f1():
    """doc"""


@nice
def f2():
    """doc"""


print(f1.__name__, f2.__name__)  # wrapper vs f2
assert f2.__name__ == "f2"
```

### W4 参考答案

```python
import functools


def twice(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = None
        for _ in range(2):
            result = fn(*args, **kwargs)
        return result

    return wrapper


@twice
def bump(box: list):
    box.append(1)
    return len(box)


box: list[int] = []
assert bump(box) == 2
assert box == [1, 1]
```

### B1 思路 + 参考答案

**思路**

wrapper 里先 log，再调用，再 log，再 return；用 `wraps` 保留名字。

**参考答案**

```python
import functools


def logged(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        print(f"CALL {fn.__name__} args={args} kwargs={kwargs}")
        result = fn(*args, **kwargs)
        print(f"RET  {fn.__name__} -> {result}")
        return result

    return wrapper


@logged
def add(a: int, b: int) -> int:
    return a + b


assert add(2, 3) == 5
assert add.__name__ == "add"
```

### B2 思路 + 参考答案

**思路**

三层：`repeat(n)` → `decorator(fn)` → `wrapper`；循环 `n` 次保存最后结果。

**参考答案**

```python
import functools


def repeat(n: int):
    if n <= 0:
        raise ValueError("n must be > 0")

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = None
            for _ in range(n):
                result = fn(*args, **kwargs)
            return result

        return wrapper

    return decorator


@repeat(n=3)
def ping():
    print("pong")
    return "ok"


assert ping() == "ok"
```

### B3 思路 + 参考答案

**思路**

分别装饰两个副本，对比属性。结论：`wraps` 把 `__name__` / `__doc__` 等元数据拷回 wrapper。

**参考答案**

```python
import functools


def plain(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def nice(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def create_message(role: str, content: str) -> dict:
    """创建消息。"""
    return {"role": role, "content": content}


plain_cm = plain(create_message)
nice_cm = nice(create_message)
print("plain:", plain_cm.__name__, plain_cm.__doc__)
print("nice :", nice_cm.__name__, nice_cm.__doc__)
# 结论：不用 wraps 时 __name__ 常变成 wrapper，文档字符串也会丢。
assert nice_cm.__name__ == "create_message"
assert nice_cm.__doc__ == "创建消息。"
```

### B4 思路 + 参考答案

**思路**

`except exceptions as exc`（tuple）；其它异常不要 catch；次数用尽 `raise RuntimeError from last`。

**参考答案**

```python
import functools


def retry(*, max_attempts: int = 3, exceptions: tuple[type[BaseException], ...] = (Exception,)):
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last = exc
                    if attempt == max_attempts:
                        raise RuntimeError(
                            f"{fn.__name__} failed after {max_attempts} attempts"
                        ) from last
            raise RuntimeError("unreachable")  # 类型检查友好

        return wrapper

    return decorator


state = {"n": 0}


@retry(max_attempts=3, exceptions=(ValueError, ConnectionError))
def fetch() -> str:
    state["n"] += 1
    if state["n"] < 3:
        raise ValueError("tmp")
    return "data"


assert fetch() == "data"


@retry(max_attempts=3, exceptions=(ValueError,))
def boom():
    raise TypeError("no retry")


try:
    boom()
    raise AssertionError("should have raised")
except TypeError:
    pass
```

### A1 思路 + 参考答案

**思路**

`f = timed(retry(f))` 时进入顺序是 timed → retry → f，外层计时包含全部重试。  
`f = retry(timed(f))` 时每次尝试单独计时。

**参考答案**

```python
import functools
import time


def timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            ms = (time.perf_counter() - start) * 1000
            print(f"TIMED {fn.__name__}: {ms:.2f} ms")

    return wrapper


# 复用 B4 的 retry ...
# 然后分别定义 call_llm / call_llm2，前两次 raise ConnectionError

# notes_a1.md 示例：
# 外层 timed：一次调用的总墙钟时间，含所有重试间隔与失败尝试。
# 内层 timed：每一次尝试各自一条耗时，更能看清单次 LLM 调用快慢。
```

完整可跑版：

```python
import functools
import time


def retry(*, max_attempts: int = 3, exceptions: tuple[type[BaseException], ...] = (Exception,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last = exc
                    if attempt == max_attempts:
                        raise RuntimeError("failed") from last
            raise RuntimeError("unreachable")

        return wrapper

    return decorator


def timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            ms = (time.perf_counter() - start) * 1000
            print(f"TIMED {fn.__name__}: {ms:.2f} ms")

    return wrapper


counters = {"a": 0, "b": 0}


@timed
@retry(max_attempts=3, exceptions=(ConnectionError,))
def call_llm() -> str:
    counters["a"] += 1
    if counters["a"] < 3:
        raise ConnectionError("tmp")
    return "ok"


@retry(max_attempts=3, exceptions=(ConnectionError,))
@timed
def call_llm2() -> str:
    counters["b"] += 1
    if counters["b"] < 3:
        raise ConnectionError("tmp")
    return "ok"


assert call_llm() == "ok"
assert call_llm2() == "ok"
```

### A2 思路 + 参考答案

**思路**

装饰器工厂接收字段名；wrapper 检查 `kwargs` 缺哪些。

**参考答案**

```python
import functools


def require_fields(*fields: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            missing = [f for f in fields if f not in kwargs]
            if missing:
                raise ValueError(f"missing fields: {missing}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@require_fields("query", "top_k")
def search(**kwargs):
    return kwargs


assert search(query="RAG", top_k=3)["query"] == "RAG"
try:
    search(query="RAG")
    raise AssertionError("should have raised")
except ValueError as exc:
    assert "top_k" in str(exc)
```

### C1 思路 + 参考答案

**思路**

类的 `__init__` 存函数；`__call__` 计数并调用；手动同步 `__name__` 或配合 `update_wrapper`。

**参考答案**

```python
import functools


class count_calls:
    def __init__(self, fn):
        functools.update_wrapper(self, fn)
        self.fn = fn
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.fn(*args, **kwargs)


@count_calls
def work():
    return "done"


assert work() == "done"
assert work() == "done"
assert work.calls == 2
assert work.__name__ == "work"
```

### C2 思路 + 参考答案

**思路**

装饰器从下到上靠近函数：先 `require_fields`，再 `retry`，最外 `timed`（或按你想观测的顺序调整）。

**参考答案**

```python
import functools
import time

# 假设已实现 require_fields / retry / timed（见上文）


def require_fields(*fields: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            missing = [f for f in fields if f not in kwargs]
            if missing:
                raise ValueError(f"missing fields: {missing}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def retry(*, max_attempts: int = 3, exceptions: tuple[type[BaseException], ...] = (Exception,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last = exc
                    if attempt == max_attempts:
                        raise RuntimeError("failed") from last
            raise RuntimeError("unreachable")

        return wrapper

    return decorator


def timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f"TIMED {fn.__name__}: {(time.perf_counter() - start) * 1000:.2f} ms")

    return wrapper


state = {"n": 0}


@timed
@retry(max_attempts=3, exceptions=(ConnectionError,))
@require_fields("query", "top_k")
def search(**kwargs):
    state["n"] += 1
    if state["n"] < 2:
        raise ConnectionError("jitter")
    top_k = int(kwargs["top_k"])
    query = str(kwargs["query"])
    return [f"doc:{query}:{i}" for i in range(top_k)]


print(search.__name__)
assert search(query="Agent", top_k=2) == ["doc:Agent:0", "doc:Agent:1"]
try:
    search(query="Agent")
    raise AssertionError("should have raised")
except ValueError:
    pass
```
