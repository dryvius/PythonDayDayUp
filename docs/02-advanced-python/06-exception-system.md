# 异常系统

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/02-advanced-python/06-exception-system.md`](../../exercises/02-advanced-python/06-exception-system.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：学会「如何失败」——在 Agent 工具调用、LLM API、后端接口里，错误要可区分、可追踪、可恢复。
- **和前后章关系**：上下文管理器保证清理；异常系统决定错误如何表达与传播；下一章类型系统帮你在静态层面减少错误。

## 学习目标（学完应能做到）

1. 熟练使用 `try / except / else / finally`，知道各自职责。
2. 自定义异常层次，按业务语义分类错误。
3. 使用 `raise ... from ...` 保留异常链，方便排障。
4. 掌握几条错误设计原则；了解 `ExceptionGroup` 即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | try/except/else/finally、自定义异常、异常链 | 能写、能分型、能追踪 |
| **建议掌握** | 错误设计原则 | 能在 Agent/API 里落地 |
| **了解即可** | ExceptionGroup | 建立地图，遇到再查 |

---

## 1. 为什么要学（和 Agent 有什么关系）

Agent 运行时几乎天天失败：

```text
LLM 超时 / 限流
工具参数不合法
检索空结果
下游 HTTP 5xx
模型返回了无法解析的 JSON
```

如果只会：

```python
except Exception:
    print("出错了")
```

你会失去：

- **可恢复性**（哪些该重试，哪些不该）
- **可观测性**（日志里看不出根因）
- **可调试性**（原始异常被吞掉）

目标能力：

```text
可预期的业务错误 → 自定义异常（带上下文）
可重试的瞬时错误 → 捕获后 retry
编程错误 / 未知错误 → 尽早暴露，不要假装成功
```

---

## 2. 必掌握：`try / except / else / finally`

### 2.1 完整结构

```python
try:
    result = do_work()
except ValueError as exc:
    print("bad input:", exc)
except (TimeoutError, ConnectionError) as exc:  # 3.11+：asyncio.TimeoutError 即内置 TimeoutError
    print("transient:", exc)
else:
    print("success:", result)   # 没有异常才走这里
finally:
    print("cleanup")            # 无论如何都走
```

| 子句 | 何时执行 | 典型用途 |
|------|----------|----------|
| `try` | 可能失败的代码 | 业务主路径 |
| `except` | 匹配到异常 | 恢复 / 转译 / 记录 |
| `else` | try 成功且无 return/break 等提前离开时 | 「成功后」逻辑，避免误捕 |
| `finally` | 离开 try 复合语句前几乎总会执行 | 清理资源（也可用 `with`） |

### 2.2 捕获要尽可能具体

```python
# 不推荐：太宽，容易吞掉 Bug
except Exception:
    pass

# 推荐：只抓你知道如何处理的
except json.JSONDecodeError:
    ...
```

宽捕获仅适合：最外层边界（如请求入口）做统一日志并返回错误响应——而且通常要记录后再次区分处理。

### 2.3 `else` 为什么有用

```python
try:
    data = json.loads(text)
except json.JSONDecodeError:
    return {"ok": False, "error": "invalid_json"}
else:
    return {"ok": True, "data": data}
```

把「成功路径」放 `else`，避免成功逻辑里的异常被同一个 `except` 误伤（当 except 写得较宽时尤其重要）。

### 2.4 `finally` 与 return

```python
def f():
    try:
        return 1
    finally:
        print("finally still runs")


print(f())
```

即使 `try` 里 `return`，`finally` 仍会执行。  
清理优先考虑 `with`；`finally` 作为补充。

---

## 3. 必掌握：自定义异常

### 3.1 为什么要自定义？

内置的 `ValueError` / `RuntimeError` 太泛。Agent 里更希望：

```python
raise ToolNotFoundError("browse")
raise ToolExecutionError("search", cause=...)
raise LLMRateLimitError(retry_after=30)
```

这样上层可以：

```python
except LLMRateLimitError:
    sleep / retry
except ToolNotFoundError:
    告诉模型换工具
except ToolExecutionError:
    把错误信息回传给模型，让它改参数
```

### 3.2 最小层次设计

```python
class AgentError(Exception):
    """Agent 领域错误基类。"""


class ToolError(AgentError):
    def __init__(self, tool_name: str, message: str = "") -> None:
        self.tool_name = tool_name
        super().__init__(message or tool_name)


class ToolNotFoundError(ToolError):
    pass


class ToolExecutionError(ToolError):
    def __init__(self, tool_name: str, message: str, *, retryable: bool = False) -> None:
        self.retryable = retryable
        super().__init__(tool_name, message)


class LLMError(AgentError):
    pass


class LLMRateLimitError(LLMError):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(f"rate limited, retry after {retry_after}s")
```

建议：

- 有一个领域基类（`AgentError`）
- 子类表达**不同处理策略**，而不是无限细碎同义名
- 需要的上下文做成属性（`tool_name`、`retryable`）

### 3.3 抛出与捕获

```python
def run_tool(name: str, registry: dict, **kwargs):
    if name not in registry:
        raise ToolNotFoundError(name)
    try:
        return registry[name](**kwargs)
    except ToolError:
        raise
    except Exception as exc:
        raise ToolExecutionError(name, str(exc), retryable=False) from exc
```

---

## 4. 必掌握：异常链（`raise ... from ...`）

### 4.1 问题：丢失根因

```python
try:
    raw = "{\"bad\"}"
    json.loads(raw)
except Exception:
    raise RuntimeError("parse failed")  # 根因可能看不清
```

### 4.2 显式链接

```python
import json


def parse_tool_args(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolExecutionError("parser", "invalid json args") from exc
    if not isinstance(data, dict):
        raise ToolExecutionError("parser", "args must be object")
    return data
```

打印 traceback 时会出现 `The above exception was the direct cause of the following exception`，排障友好得多。

### 4.3 `from None`：有意隐藏内部异常

```python
raise ToolNotFoundError(name) from None
```

用于：内部细节不想暴露给上层（偶尔用于 API 边界）。  
默认学习阶段优先 `from exc` 保留链。

---

## 5. 建议掌握：错误设计原则

### 5.1 几条实用原则

1. **失败要响亮**：不要返回 `"error"` 字符串假装成功；该抛就抛，或返回明确的 Result 结构并统一约定。
2. **按处理方式分类**：可重试 / 不可重试 / 用户可修正 / 系统故障。
3. **边界转译**：底层 `httpx.HTTPError` 到领域层变成 `LLMError`，避免上层依赖底层库异常类型。
4. **信息足够但安全**：日志可详细；返回给模型/用户的信息避免泄露密钥与内部路径。
5. **工具错误可回传模型**：Tool Calling 里，把结构化错误交给模型，常比直接中断整轮更有用。

### 5.2 Result 风格（可选补充）

有时不想用异常做控制流：

```python
def run_tool(...) -> dict:
    try:
        return {"ok": True, "result": ...}
    except ToolError as exc:
        return {"ok": False, "error": str(exc), "tool": exc.tool_name}
```

异常适合「罕见/需要中断」；Result 适合「预期内失败且要继续编排」。Agent runtime 两种都会见到。

### 5.3 和重试装饰器配合

```text
只对 retryable / 瞬时网络类异常重试
对参数错误、鉴权失败不要盲着重试
```

这正是自定义异常带 `retryable` 属性的价值。

---

## 6. 了解即可：`ExceptionGroup`（Python 3.11+）

并发场景可能「一次抛出多个异常」：

```python
# 概念示意
ExceptionGroup("worker errors", [exc1, exc2])
```

配合 `except*` 可以按类型拆开处理。  
在 `asyncio.TaskGroup` 等场景会遇到。本阶段：

- 知道有「异常组」这回事
- 见到再查官方文档即可

---

## 7. 常见坑

1. **裸 `except:`**  
   会捕获 `BaseException`（含 `KeyboardInterrupt` / `SystemExit`），等于连中断退出都吞掉。至少写 `except Exception:`，并慎重。

2. **捕获后空 `pass`**  
   问题被静默，后期极难查。

3. **用异常做普通分支（过度）**  
   高频可预期路径用 if/Result；异常用于错误路径。

4. **抛出字符串 / 抛出非 Exception**  
   始终 `raise SomeError(...)`。

5. **在 `finally` 里 raise，掩盖原异常**  
   清理失败要额外小心。

6. **日志只打印 `str(e)`，不带 traceback**  
   关键路径用 `logging.exception(...)` 或 `repr` + traceback。

---

## 8. 综合小例子：迷你 Tool Runtime 错误处理

```python
import json
from typing import Any, Callable


class AgentError(Exception):
    pass


class ToolNotFoundError(AgentError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name)


class ToolExecutionError(AgentError):
    def __init__(self, name: str, message: str, *, retryable: bool = False) -> None:
        self.name = name
        self.retryable = retryable
        super().__init__(message)


ToolFn = Callable[..., Any]


class ToolRuntime:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFn] = {}

    def register(self, name: str, fn: ToolFn) -> None:
        self._tools[name] = fn

    def call(self, name: str, arguments_json: str) -> dict:
        if name not in self._tools:
            raise ToolNotFoundError(name)

        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError as exc:
            raise ToolExecutionError(name, "invalid json") from exc

        if not isinstance(args, dict):
            raise ToolExecutionError(name, "arguments must be object")

        try:
            result = self._tools[name](**args)
        except TypeError as exc:
            # 通常是参数不匹配，不建议盲重试
            raise ToolExecutionError(name, f"bad arguments: {exc}") from exc
        except ConnectionError as exc:
            raise ToolExecutionError(name, str(exc), retryable=True) from exc
        except Exception as exc:
            raise ToolExecutionError(name, str(exc), retryable=False) from exc

        return {"ok": True, "name": name, "result": result}


def search(query: str, top_k: int = 3) -> list[str]:
    if query == "network":
        raise ConnectionError("dns timeout")
    return [f"doc:{query}:{i}" for i in range(top_k)]


rt = ToolRuntime()
rt.register("search", search)

print(rt.call("search", '{"query": "RAG", "top_k": 2}'))

try:
    rt.call("browse", "{}")
except ToolNotFoundError as exc:
    print("missing tool:", exc.name)

try:
    rt.call("search", '{"query": "network"}')
except ToolExecutionError as exc:
    print("failed:", exc.name, "retryable=", exc.retryable)
    print("cause:", exc.__cause__)
```

这已经接近真实 Tool Calling 层的错误处理骨架。

---

## 9. 练习指引

请打开并完成：

[`exercises/02-advanced-python/06-exception-system.md`](../../exercises/02-advanced-python/06-exception-system.md)

建议代码位置：

```text
playground/02-advanced-python/06-exception-system/
```

---

## 10. 小结与下一站

### 心智模型

```text
发生问题
  → 抛出「带语义」的异常（必要时 from 根因）
  → 在对的层级捕获
  → 重试 / 转译 / 返回给模型 / 失败终止
  → finally/with 负责清理
```

### 自检清单

- [ ] 能正确使用 try/except/else/finally
- [ ] 能设计小型异常层次（基类 + 2～3 个子类）
- [ ] 会用 `raise ... from ...` 保留因果
- [ ] 能说明哪些错误可重试、哪些不该
- [ ] 独立完成练习基础题

### 下一章

[`07-typing-system.md`](./07-typing-system.md) —— 类型系统：用注解与 Protocol/Generic 把「约定」写清楚，减少一整类运行时错误。  
（这也是模块 02 的收官章。）

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[上下文管理器](./05-context-manager.md)
- 下一章：[类型系统](./07-typing-system.md)
