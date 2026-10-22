# 练习：异常系统

> 对应文档：[`docs/02-advanced-python/06-exception-system.md`](../../docs/02-advanced-python/06-exception-system.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先摸清 `try/except/else/finally` 与 `raise ... from`，再上 Agent 异常层次。
4. 建议代码目录：

```text
playground/02-advanced-python/06-exception-system/
```

5. 验证异常链时，可打印 `exc.__cause__` 或看 traceback。先做题再看答案。

---

## 热身题（建议先做）

### W1. 捕获 `ZeroDivisionError`

**要求**：写 `safe_div(a, b)`，除零时返回 `None`，否则返回商。

**验收**：`safe_div(1, 0) is None`；`safe_div(6, 3) == 2`。

---

### W2. `else` 只在成功时走

**要求**：在 `try/except/else` 结构里，成功路径于 `else` 里 append `"ok"` 到列表。

**验收**：成功一次有 `"ok"`；失败一次没有。

---

### W3. `finally` 总会执行

**要求**：无论成功失败，`finally` 都往 `events` append `"done"`。

**验收**：两次调用后至少两个 `"done"`。

---

### W4. `raise ... from`

**要求**：捕获 `ValueError("bad")`，再 `raise RuntimeError("wrap") from exc`，断言 `__cause__` 是原异常。

**验收**：`exc.__cause__` 不为 `None`。

---

## 基础题（必做）

### B1. try/except/else/finally 行为观察

写函数 `divide(a, b)`：

- `b == 0` 时捕获 `ZeroDivisionError`，返回 `"div0"`
- 成功时走 `else`，返回商
- 无论成败，`finally` 里给全局列表 `events` append `"done"`

再分别调用 `divide(6, 3)` 与 `divide(1, 0)`。

**验收**：成功返回 `2`；失败返回 `"div0"`；两次调用后 `events` 至少含两个 `"done"`。

---

### B2. 自定义异常层次（Agent 向）

实现：

```python
class AgentError(Exception): ...
class ToolNotFoundError(AgentError): ...
class ToolExecutionError(AgentError):
    def __init__(self, tool_name: str, message: str, *, retryable: bool = False): ...
```

并写 `get_tool(registry, name)`：不存在则 `raise ToolNotFoundError(name)`。

**验收**：捕获 `ToolNotFoundError` 时能读到工具名；它同时也是 `AgentError` 的实例。

---

### B3. 异常链

实现 `parse_json_object(text: str) -> dict`：

- JSON 非法 → `raise ToolExecutionError("parser", "invalid json") from exc`
- 解析结果非 dict → `raise ToolExecutionError("parser", "must be object")`

**验收**：非法 JSON 时 `exc.__cause__` 不为 `None`；非对象 JSON（如 `[1]`）也能报错。

---

### B4. 捕获宽度对比（认知 + 代码）

写两段代码：

1. `except Exception:` 把 `ValueError` 和你故意埋的 `NameError`（或其它）一起吞掉（演示坏味道，打日志即可）
2. 改成只捕获 `ValueError`，让另一类错误冒泡

在 `b4_notes.md` 写 3～5 行：为什么边界层可以宽捕，业务核心通常要窄捕。

**验收**：有对比代码 + 笔记。

---

## 进阶题（建议至少做 1 题）

### A1. ToolRuntime.call

按文档综合例子实现精简版 `ToolRuntime`：

- `register` / `call(name, arguments_json)`
- 未知工具 → `ToolNotFoundError`
- JSON 坏 → `ToolExecutionError`（带 cause）
- `ConnectionError` → `ToolExecutionError(retryable=True)`
- 其它执行错误 → `retryable=False`

注册假 `search`，覆盖：成功、未知工具、坏 JSON、网络错误四条路径。

**验收**：四条路径行为正确；网络错误路径 `retryable is True`。

---

### A2. 重试只针对 retryable

写 `call_with_retry(runtime, name, arguments_json, max_attempts=3)`：

- 捕获 `ToolExecutionError`，仅当 `retryable` 才重试
- `ToolNotFoundError` 不重试
- 次数用尽后抛出最后一次异常（保持 cause）

**验收**：对 retryable 错误会尝试多次；对 not found 只尝试 1 次。

---

## 挑战题（可选）

### C1. 把错误回传给「模型」

实现 `agent_once(runtime, tool_name, arguments_json) -> dict`：

成功：`{"ok": True, "result": ...}`  
失败：`{"ok": False, "error_type": "...", "message": "...", "retryable": false}`

不要让异常直接打爆主流程（在该函数边界转成结构化结果）。  
同时在日志里打印原始 cause（若有）。

**验收**：成功/失败都返回 dict；失败信息不丢关键字段。

---

### C2. 异常层次图（书面）

画或列出你为「LLM 调用 + Tool 调用」设计的异常树（8～12 行即可），并标注每类错误的处理策略：重试 / 换工具 / 终止 / 回传模型。

**验收**：有 `c2_errors.md`；策略不是全写成「重试」。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成
- [ ] 能口述：else/finally 用途；为何需要自定义异常；`from` 链的价值
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。

### W1 参考答案

```python
def safe_div(a: float, b: float) -> float | None:
    try:
        return a / b
    except ZeroDivisionError:
        return None


assert safe_div(1, 0) is None
assert safe_div(6, 3) == 2
```

### W2 参考答案

```python
def run(ok: bool, box: list[str]) -> None:
    try:
        if not ok:
            raise ValueError("x")
    except ValueError:
        box.append("err")
    else:
        box.append("ok")


box: list[str] = []
run(True, box)
run(False, box)
assert box == ["ok", "err"]
```

### W3 参考答案

```python
events: list[str] = []


def work(fail: bool) -> None:
    try:
        if fail:
            raise RuntimeError("x")
    except RuntimeError:
        pass
    finally:
        events.append("done")


work(False)
work(True)
assert events.count("done") >= 2
```

### W4 参考答案

```python
try:
    raise ValueError("bad")
except ValueError as exc:
    try:
        raise RuntimeError("wrap") from exc
    except RuntimeError as wrapped:
        assert wrapped.__cause__ is exc
```

### B1 思路 + 参考答案

**思路**

`except` 处理失败；`else` 只在无异常时执行；`finally` 做收尾计数。

**参考答案**

```python
events: list[str] = []


def divide(a: float, b: float):
    try:
        result = a / b
    except ZeroDivisionError:
        return "div0"
    else:
        return result
    finally:
        events.append("done")


assert divide(6, 3) == 2
assert divide(1, 0) == "div0"
assert events.count("done") >= 2
```

### B2 思路 + 参考答案

**思路**

自定义层次便于 `except AgentError` 统一边界处理，同时保留细类信息（是否可重试等）。

**参考答案**

```python
class AgentError(Exception):
    """Agent 运行期错误基类。"""


class ToolNotFoundError(AgentError):
    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"tool not found: {tool_name}")


class ToolExecutionError(AgentError):
    def __init__(
        self,
        tool_name: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        self.tool_name = tool_name
        self.retryable = retryable
        super().__init__(f"{tool_name}: {message}")


def get_tool(registry: dict, name: str):
    if name not in registry:
        raise ToolNotFoundError(name)
    return registry[name]


registry = {"search": lambda **kw: ["ok"]}
assert get_tool(registry, "search") is registry["search"]
try:
    get_tool(registry, "browse")
    raise AssertionError("should have raised")
except ToolNotFoundError as exc:
    assert exc.tool_name == "browse"
    assert isinstance(exc, AgentError)
```

### B3 思路 + 参考答案

**思路**

`json.loads` 失败用 `from` 保留根因；类型不对单独报业务错误。

**参考答案**

```python
import json


class AgentError(Exception):
    pass


class ToolExecutionError(AgentError):
    def __init__(self, tool_name: str, message: str, *, retryable: bool = False) -> None:
        self.tool_name = tool_name
        self.retryable = retryable
        super().__init__(f"{tool_name}: {message}")


def parse_json_object(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolExecutionError("parser", "invalid json") from exc
    if not isinstance(data, dict):
        raise ToolExecutionError("parser", "must be object")
    return data


assert parse_json_object('{"a": 1}') == {"a": 1}

try:
    parse_json_object("{bad")
    raise AssertionError("should have raised")
except ToolExecutionError as exc:
    assert exc.__cause__ is not None

try:
    parse_json_object("[1]")
    raise AssertionError("should have raised")
except ToolExecutionError as exc:
    assert "must be object" in str(exc)
```

### B4 思路 + 参考答案

**思路**

宽捕会掩盖编程错误；边界（如 HTTP handler / agent_once）可以转成结构化错误，核心逻辑应窄捕。

**参考答案**

```python
def wide_catch(action: str) -> str:
    try:
        if action == "value":
            raise ValueError("v")
        if action == "name":
            raise NameError("n")  # 演示：不该被业务宽捕吞掉
        return "ok"
    except Exception as exc:
        print("swallowed:", type(exc).__name__, exc)
        return "swallowed"


def narrow_catch(action: str) -> str:
    try:
        if action == "value":
            raise ValueError("v")
        if action == "name":
            raise NameError("n")
        return "ok"
    except ValueError as exc:
        print("handled ValueError:", exc)
        return "handled"


assert wide_catch("value") == "swallowed"
assert wide_catch("name") == "swallowed"  # 坏味道：NameError 也被吞

assert narrow_catch("value") == "handled"
try:
    narrow_catch("name")
    raise AssertionError("NameError should bubble")
except NameError:
    pass
```

`b4_notes.md` 示例：

```text
边界层（例如把结果回传给模型 / HTTP）可以宽捕，转成结构化错误，避免进程崩溃。
业务核心应窄捕：只处理预期的 ValueError / 网络错误等。
宽捕会把 NameError、Bug 一起吞掉，排障困难。
```

### A1 思路 + 参考答案

**思路**

先解析 JSON，再查工具，再调用；分层转换异常，不要把 `ToolNotFoundError` 包成 ExecutionError。

**参考答案**

```python
import json
from collections.abc import Callable
from typing import Any


class AgentError(Exception):
    pass


class ToolNotFoundError(AgentError):
    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(tool_name)


class ToolExecutionError(AgentError):
    def __init__(
        self,
        tool_name: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        self.tool_name = tool_name
        self.retryable = retryable
        super().__init__(message)


class ToolRuntime:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self._tools[name] = fn

    def call(self, name: str, arguments_json: str) -> Any:
        if name not in self._tools:
            raise ToolNotFoundError(name)
        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError as exc:
            raise ToolExecutionError(name, "invalid json") from exc
        if not isinstance(args, dict):
            raise ToolExecutionError(name, "arguments must be object")
        try:
            return self._tools[name](**args)
        except ConnectionError as exc:
            raise ToolExecutionError(name, str(exc), retryable=True) from exc
        except Exception as exc:
            raise ToolExecutionError(name, str(exc), retryable=False) from exc


def search(query: str, top_k: int = 3) -> list[str]:
    if query == "net":
        raise ConnectionError("timeout")
    return [f"doc:{query}:{i}" for i in range(top_k)]


rt = ToolRuntime()
rt.register("search", search)

assert rt.call("search", '{"query": "RAG", "top_k": 2}') == ["doc:RAG:0", "doc:RAG:1"]

try:
    rt.call("browse", "{}")
    raise AssertionError("should have raised")
except ToolNotFoundError:
    pass

try:
    rt.call("search", "{bad")
    raise AssertionError("should have raised")
except ToolExecutionError as exc:
    assert exc.__cause__ is not None

try:
    rt.call("search", '{"query": "net"}')
    raise AssertionError("should have raised")
except ToolExecutionError as exc:
    assert exc.retryable is True
```

### A2 思路 + 参考答案

**思路**

仅对 `retryable=True` 重试；`ToolNotFoundError` 立即抛出。

**参考答案**

```python
# 依赖 A1 的 ToolRuntime / 异常类


def call_with_retry(runtime, name: str, arguments_json: str, max_attempts: int = 3):
    last: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return runtime.call(name, arguments_json)
        except ToolNotFoundError:
            raise
        except ToolExecutionError as exc:
            last = exc
            if not exc.retryable or attempt == max_attempts - 1:
                raise
    raise RuntimeError("unreachable") from last


# 网络错误会重试多次（配合会失败的假工具）
attempts = {"n": 0}


def flaky_search(query: str) -> list[str]:
    attempts["n"] += 1
    if attempts["n"] < 3:
        raise ConnectionError("tmp")
    return [f"doc:{query}"]


rt2 = ToolRuntime()
rt2.register("search", flaky_search)
assert call_with_retry(rt2, "search", '{"query": "x"}') == ["doc:x"]
assert attempts["n"] == 3

try:
    call_with_retry(rt2, "nope", "{}")
    raise AssertionError("should have raised")
except ToolNotFoundError:
    assert True  # 不重试，直接失败
```

### C1 思路 + 参考答案

**思路**

在 Agent 边界把 `AgentError` 转成结构化 dict，便于回传模型或上层编排；日志打印 `__cause__`。

**参考答案**

```python
def agent_once(runtime, tool_name: str, arguments_json: str) -> dict:
    try:
        result = runtime.call(tool_name, arguments_json)
        return {"ok": True, "result": result}
    except AgentError as exc:
        cause = getattr(exc, "__cause__", None)
        if cause is not None:
            print("cause:", type(cause).__name__, cause)
        retryable = bool(getattr(exc, "retryable", False))
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "retryable": retryable,
        }


rt3 = ToolRuntime()
rt3.register("search", search)
assert agent_once(rt3, "search", '{"query": "RAG"}')["ok"] is True
bad = agent_once(rt3, "browse", "{}")
assert bad["ok"] is False
assert bad["error_type"] == "ToolNotFoundError"
```

### C2 思路 + 参考答案

`c2_errors.md` 示例：

```text
AgentError
├── LLMError
│   ├── LLMTimeoutError      → 重试 / 降级模型
│   ├── LLMRateLimitError    → 退避重试
│   └── LLMBadResponseError  → 回传/终止（通常不盲重试）
└── ToolError
    ├── ToolNotFoundError    → 换工具或回传模型（不重试同名）
    ├── ToolAuthError        → 终止并告警
    ├── ToolExecutionError
    │   ├── retryable=True   → 有限次重试
    │   └── retryable=False  → 回传模型或换策略
    └── ToolValidationError  → 修正参数后重试一次 / 回传

原则：不是所有错误都重试；编程错误与鉴权失败应终止。
```
