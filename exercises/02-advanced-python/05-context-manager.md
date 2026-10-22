# 练习：上下文管理器

> 对应文档：[`docs/02-advanced-python/05-context-manager.md`](../../docs/02-advanced-python/05-context-manager.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先写最小 `__enter__` / `__exit__` 与 `@contextmanager`，再上计时器与配置恢复。
4. 建议代码目录：

```text
playground/02-advanced-python/05-context-manager/
```

5. 验证「异常也会清理」时，可用 `try/except` 包住 `with` 观察副作用。先做题再看答案。

---

## 热身题（建议先做）

### W1. 文件 with 读写一行

**要求**：用 `with open(...)` 写入一行再读回（也可用 `pathlib.Path.write_text` / `read_text`，但至少体验一次 `with open`）。

**验收**：读回内容等于写入内容。

---

### W2. 最小类协议

**要求**：类 `Hello`：`with Hello() as x:` 时 `x == "hello"`。

**验收**：`assert x == "hello"`。

---

### W3. `@contextmanager` 骨架

**要求**：用 `@contextmanager` 写 `def opened_flag(box: dict):`，进入时 `box["open"]=True`，退出时改回 `False`。

**验收**：with 内外标志正确。

---

### W4. 异常也走 finally

**要求**：在 W3 的实现里确认：块内 `raise ValueError` 后标志仍被恢复，且异常能被外层捕获。

**验收**：恢复 + 异常继续传播。

---

## 基础题（必做）

### B1. 文件 with 实操

1. 用 `with` + `pathlib` 写入 `hello.txt`
2. 再用 `with` 读回并断言内容
3. 在写入过程中故意 `raise RuntimeError("boom")`（写在 with 块内），确认异常能被捕获，且你使用了 with 而不是裸 open 忘记 close

**验收**：正常读写通过；异常路径代码存在且仍使用 `with`。

---

### B2. `@contextmanager` 计时器

实现：

```python
@contextmanager
def timed(label: str):
    ...
```

**要求**：

1. 退出时打印 `label` 与毫秒耗时
2. 块内异常也必须打印耗时，然后异常继续抛出
3. 写两段 demo：正常结束 / 异常结束

**验收**：两段都能看到耗时日志；异常段外层能 catch 到原异常。

---

### B3. 临时改配置（贴近 LLM 参数）

实现 `temporary_set(mapping, key, value)`：

- 进入时设置新值
- 退出时恢复旧值；若原先没有该 key，则退出时删除该 key
- 异常退出也必须恢复

**验收**：

```python
cfg = {"temperature": 0.7}
with temporary_set(cfg, "temperature", 0):
    assert cfg["temperature"] == 0
assert cfg["temperature"] == 0.7

with temporary_set(cfg, "top_p", 0.9):
    assert cfg["top_p"] == 0.9
assert "top_p" not in cfg
```

再补一个「块内 raise 后仍恢复」的断言。

---

### B4. 协议默写（小问答 + 最小类）

1. 在 `b4_notes.md` 用自己的话写：`__enter__` / `__exit__` 何时调用
2. 手写类 `NullContext`，`with NullContext() as x:` 时 `x` 为 `"ok"`，退出无事发生

**验收**：笔记存在；`with NullContext() as x: assert x == "ok"` 通过。

---

## 进阶题（建议至少做 1 题）

### A1. 类版 Timer

把 B2 改成类 `Timer`：

- `__enter__` 返回 self
- 属性 `elapsed_ms` 在退出后可读取
- 不吞异常

**验收**：`with Timer("x") as t:` 结束后 `t.elapsed_ms > 0`。

---

### A2. 会话作用域 `agent_session`

实现风格接近文档综合例子的 `agent_session(name)`：

- yield 一个带 `log` 方法的 session 对象
- 成功 / 失败写不同事件
- finally 写结束事件（可含耗时）
- 异常必须重新抛出

**验收**：成功与失败两条路径的 `events` 列表符合预期。

---

## 挑战题（可选）

### C1. 简易「锁」（单线程模拟）

实现 `FakeLock` 上下文管理器：

- 进入时若已锁定则抛 `RuntimeError("locked")`
- 否则标记锁定，退出时解锁
- 用两个连续 `with` 证明可先后使用
- 再写一个嵌套/并发模拟：第二次 acquire 失败

**验收**：正常 with 两次成功；在已锁定状态下再次 enter 失败；异常退出后锁被释放。

---

### C2. 工具调用 span（贴近观测）

实现 `tool_span(tool_name: str)`：

- 进入：记录 start
- 退出：向全局 list append 一条记录 `{tool, ok, ms}`
- 块内异常 → `ok=False`，仍记录，再抛出

用它包两段假工具调用（成功/失败），最后打印 span 列表。

**验收**：两条记录都在；失败那条 `ok is False`。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成
- [ ] 能口述：为何 with 比手工 close 更安全；`@contextmanager` 的 yield/finally 结构
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。

### W1 参考答案

```python
from pathlib import Path

path = Path(__file__).resolve().parent / "w1.txt"
with path.open("w", encoding="utf-8") as f:
    f.write("hello")
with path.open("r", encoding="utf-8") as f:
    assert f.read() == "hello"
```

### W2 参考答案

```python
class Hello:
    def __enter__(self) -> str:
        return "hello"

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


with Hello() as x:
    assert x == "hello"
```

### W3 参考答案

```python
from contextlib import contextmanager


@contextmanager
def opened_flag(box: dict):
    box["open"] = True
    try:
        yield box
    finally:
        box["open"] = False


box: dict = {"open": False}
with opened_flag(box):
    assert box["open"] is True
assert box["open"] is False
```

### W4 参考答案

```python
from contextlib import contextmanager


@contextmanager
def opened_flag(box: dict):
    box["open"] = True
    try:
        yield box
    finally:
        box["open"] = False


box: dict = {"open": False}
try:
    with opened_flag(box):
        raise ValueError("boom")
except ValueError:
    pass
assert box["open"] is False
```

### B1 思路 + 参考答案

**思路**

正常路径读写断言；异常路径仍包在 `with` 里，证明「即便炸了也会走清理协议」。

**参考答案**

```python
from pathlib import Path

path = Path(__file__).resolve().parent / "hello.txt"

with path.open("w", encoding="utf-8") as f:
    f.write("hello agent")

with path.open("r", encoding="utf-8") as f:
    assert f.read() == "hello agent"

try:
    with path.open("w", encoding="utf-8") as f:
        f.write("partial")
        raise RuntimeError("boom")
except RuntimeError as exc:
    assert str(exc) == "boom"
# 使用 with：无需手工 f.close()
```

### B2 思路 + 参考答案

**思路**

`try: yield` + `finally: 打印耗时`；不要在 except 里吞掉异常。

**参考答案**

```python
import time
from contextlib import contextmanager


@contextmanager
def timed(label: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        ms = (time.perf_counter() - start) * 1000
        print(f"{label}: {ms:.2f} ms")


with timed("ok-path"):
    sum(range(10000))

try:
    with timed("err-path"):
        raise ValueError("x")
except ValueError as exc:
    assert str(exc) == "x"
```

### B3 思路 + 参考答案

**思路**

进入前记下 `missing` 与 `old`；`finally` 分支恢复或删除。LLM 调参临时改 temperature 很常见。

**参考答案**

```python
from contextlib import contextmanager
from typing import Any


@contextmanager
def temporary_set(mapping: dict, key: Any, value: Any):
    missing = key not in mapping
    old = mapping.get(key)
    mapping[key] = value
    try:
        yield mapping
    finally:
        if missing:
            mapping.pop(key, None)
        else:
            mapping[key] = old


cfg = {"temperature": 0.7}
with temporary_set(cfg, "temperature", 0):
    assert cfg["temperature"] == 0
assert cfg["temperature"] == 0.7

with temporary_set(cfg, "top_p", 0.9):
    assert cfg["top_p"] == 0.9
assert "top_p" not in cfg

try:
    with temporary_set(cfg, "temperature", 0):
        raise RuntimeError("boom")
except RuntimeError:
    pass
assert cfg["temperature"] == 0.7
```

### B4 思路 + 参考答案

**思路**

`__enter__` 在进入 with 时调用，返回值赋给 `as` 目标；`__exit__` 在离开时调用（含异常路径）。

**参考答案**

`b4_notes.md`：

```text
__enter__：进入 with 时调用，返回值给 as 变量。
__exit__：离开 with 时调用（正常结束或异常），可做清理。
若 __exit__ 返回 True 会吞异常；通常返回 False/None 让异常继续传播。
```

```python
class NullContext:
    def __enter__(self) -> str:
        return "ok"

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


with NullContext() as x:
    assert x == "ok"
```

### A1 思路 + 参考答案

**思路**

类版把开始时间放在实例上；退出后可读 `elapsed_ms`。

**参考答案**

```python
import time


class Timer:
    def __init__(self, label: str) -> None:
        self.label = label
        self._start = 0.0
        self.elapsed_ms = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        print(f"{self.label}: {self.elapsed_ms:.2f} ms")
        return None  # 不吞异常


with Timer("x") as t:
    sum(range(100000))
assert t.elapsed_ms > 0
```

### A2 思路 + 参考答案

**思路**

`try: yield session; log success` / `except: log error; raise` / `finally: log end`。用于 Agent 会话作用域事件。

**参考答案**

```python
import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Session:
    name: str
    events: list[str] = field(default_factory=list)

    def log(self, event: str) -> None:
        self.events.append(event)


@contextmanager
def agent_session(name: str):
    session = Session(name=name)
    start = time.perf_counter()
    session.log(f"start:{name}")
    try:
        yield session
        session.log("success")
    except Exception as exc:
        session.log(f"error:{type(exc).__name__}")
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        session.log(f"end:{ms:.1f}ms")


events_ok: list[str] = []
with agent_session("demo") as s:
    s.log("work")
    events_ok = list(s.events)
# finally 已追加 end
assert events_ok[0].startswith("start:")
# 注意：with 结束后 s.events 含 success 与 end
assert "success" in s.events
assert any(e.startswith("end:") for e in s.events)

try:
    with agent_session("boom") as s2:
        raise ValueError("x")
except ValueError:
    pass
assert "error:ValueError" in s2.events
assert any(e.startswith("end:") for e in s2.events)
```

### C1 思路 + 参考答案

**思路**

实例属性 `_locked`；`__enter__` 检查并设置；`__exit__` 清回 False。

**参考答案**

```python
class FakeLock:
    def __init__(self) -> None:
        self._locked = False

    def __enter__(self) -> "FakeLock":
        if self._locked:
            raise RuntimeError("locked")
        self._locked = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._locked = False
        return None


lock = FakeLock()
with lock:
    pass
with lock:
    pass  # 先后使用 OK

lock2 = FakeLock()
lock2.__enter__()
try:
    lock2.__enter__()  # 已锁定再 enter
    raise AssertionError("should have raised")
except RuntimeError as exc:
    assert str(exc) == "locked"
finally:
    lock2.__exit__(None, None, None)

# 异常退出后锁释放
try:
    with FakeLock() as lk:
        raise RuntimeError("boom")
except RuntimeError:
    pass
# 新 with 应可进入：用同一把锁验证
lk2 = FakeLock()
try:
    with lk2:
        raise ValueError("x")
except ValueError:
    pass
with lk2:
    assert lk2._locked is True
```

### C2 思路 + 参考答案

**思路**

与观测里的 span 类似：记录工具名、是否成功、耗时；异常也要落盘再抛出。

**参考答案**

```python
import time
from contextlib import contextmanager

SPANS: list[dict] = []


@contextmanager
def tool_span(tool_name: str):
    start = time.perf_counter()
    ok = True
    try:
        yield
    except Exception:
        ok = False
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        SPANS.append({"tool": tool_name, "ok": ok, "ms": ms})


SPANS.clear()
with tool_span("search"):
    hits = ["doc:1"]

try:
    with tool_span("browse"):
        raise ConnectionError("down")
except ConnectionError:
    pass

assert len(SPANS) == 2
assert SPANS[0]["ok"] is True and SPANS[0]["tool"] == "search"
assert SPANS[1]["ok"] is False and SPANS[1]["tool"] == "browse"
print(SPANS)
```
