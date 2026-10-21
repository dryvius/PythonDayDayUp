# 异常系统

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有 JS/TS 的 `try/catch` 经验可更快；异常链与 `ExceptionGroup` 建议动手跑一遍）  
> 对应练习：[`exercises/02-advanced-python/06-exception-system.md`](../../exercises/02-advanced-python/06-exception-system.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：学会「如何失败」——在 Agent 工具调用、LLM API、后端接口里，错误要可区分、可追踪、可恢复。
- **和前后章关系**：上下文管理器保证清理；异常系统决定错误如何表达与传播；下一章类型系统帮你在静态层面减少错误。
- **你的优势**：JS/TS 里的 `try/catch/finally`、自定义 `Error` 子类经验可以直接迁移；重点盯住 Python 独有的 `else`、`raise ... from ...`、以及 3.11+ 的 `ExceptionGroup` / `except*`。

## 学习目标（学完应能做到）

1. 熟练使用 `try / except / else / finally`，知道各自职责，能讲清执行顺序。
2. 自定义异常层次，按业务语义分类错误，并带上可观测上下文。
3. 使用 `raise ... from ...` 保留异常链，知道何时用 `from None`。
4. 掌握几条错误设计原则；能把底层库异常转译成领域异常。
5. 了解 `ExceptionGroup` / `except*` 的地图；独立完成课后练习。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | try/except/else/finally、自定义异常、异常链 | 能写、能分型、能追踪 |
| **建议掌握** | 错误设计原则、边界转译、Result 风格 | 能在 Agent/API 里落地 |
| **了解即可** | ExceptionGroup / except* | 建立地图，遇到再查 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要「认真设计失败」？

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

#### 本章要练的三种能力

1. **表达**：用「带语义的异常类型 + 上下文属性」描述失败
2. **传播**：在对的层级捕获；用异常链保留根因
3. **决策**：重试 / 转译 / 回传模型 / 失败终止——按类型分支

目标能力可以先记成一张图：

```text
可预期的业务错误 → 自定义异常（带上下文）
可重试的瞬时错误 → 捕获后 retry
编程错误 / 未知错误 → 尽早暴露，不要假装成功
```

可以先记一句：

> 异常不是「程序崩了就算了」，而是给失败起一个可分类、可追踪、可决策的名字。

---

## 2. 必掌握：`try / except / else / finally`

这一节会刻意写细——异常控制流是后面自定义异常、异常链、Tool Runtime 的共同底座。

### 2.1 完整结构：四块各干什么

#### 为什么需要四块，而不是只有 try/except？

JS 里常见 `try/catch/finally`。Python 多了一个 `else`：专门放「try 成功之后」的逻辑，避免成功路径里的异常被同一个 `except` 误伤。

#### 怎么写

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
| --- | --- | --- |
| `try` | 可能失败的代码 | 业务主路径 |
| `except` | 匹配到异常 | 恢复 / 转译 / 记录 |
| `else` | try 成功且无 return/break/continue 等提前离开时 | 「成功后」逻辑，避免误捕 |
| `finally` | 离开 try 复合语句前几乎总会执行 | 清理资源（也可用 `with`） |

#### 跑一下

把上面收成可直接运行的最小版：

```python
def do_work(x: int) -> int:
    if x < 0:
        raise ValueError("x must be >= 0")
    return x * 2


def demo(x: int) -> None:
    try:
        result = do_work(x)
    except ValueError as exc:
        print("bad input:", exc)
    else:
        print("success:", result)
    finally:
        print("cleanup")


demo(3)
print("---")
demo(-1)
```

输出大致是：

```text
success: 6
cleanup
---
bad input: x must be >= 0
cleanup
```

心智图：

```text
进入 try
  ├─ 抛异常 → 匹配 except →（跳过 else）→ finally
  └─ 无异常 → else → finally
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为 `else` 和 `if/else` 一样「二选一」 | 这里的 `else` 绑定的是 **try 是否成功**，不是某个条件表达式 |
| 在 `except` 里写成功逻辑 | 成功逻辑一旦出错，会被别的宽 `except` 误伤时更难查 |
| 把清理只写在 `try` 末尾 | 一旦中途抛异常，清理不会跑；用 `finally` 或 `with` |

#### JS 对照

| JavaScript | Python |
| --- | --- |
| `try { ... } catch (e) { ... }` | `try: ... except SomeError as e: ...` |
| `finally { ... }` | `finally: ...` |
| 没有直接对应的 `else` | `else:` = try 成功才执行 |
| `catch (e)` 常接类型判断 | `except` 可按类型分流，可一次写多个类型 |

```javascript
try {
  const result = doWork(x);
  console.log("success:", result); // 成功逻辑常直接写在 try 里
} catch (e) {
  console.log("failed:", e);
} finally {
  console.log("cleanup");
}
```

Python 更鼓励：可能失败的放 `try`，成功后的放 `else`，清理放 `finally`。

---

### 2.2 捕获要尽可能具体

#### 为什么不能一上来 `except Exception`？

宽捕获像一张大网：参数错误、断网、你自己的 Bug，全被同一只手接住。结果是：

- 该重试的没重试
- 不该重试的盲着重试
- 编程错误被静默，排障极痛苦

#### 怎么写

```python
import json

# 不推荐：太宽，容易吞掉 Bug
# except Exception:
#     pass

# 推荐：只抓你知道如何处理的
try:
    data = json.loads(text)
except json.JSONDecodeError as exc:
    print("invalid json:", exc)
```

一次捕获多种「同类瞬时错误」时，用元组：

```python
except (TimeoutError, ConnectionError) as exc:
    print("transient:", type(exc).__name__, exc)
```

#### 跑一下

```python
import json


def parse(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        print("caught JSONDecodeError:", exc)
        return None


print(parse('{"ok": true}'))
print(parse("{bad}"))
```

#### 易错点

- 宽捕获仅适合：**最外层边界**（如请求入口、Agent 一轮循环最外层）做统一日志并返回错误响应——而且通常要记录后再次区分处理。
- `except Exception` 不会吃掉 `KeyboardInterrupt` / `SystemExit`（它们挂在 `BaseException` 下）；但裸 `except:` 会——见 §7。
- 「只 print 一下就当处理完了」往往等于没处理；至少要：记录、转译、或向上抛。

#### JS 对照

JS 的 `catch` 默认拿到任意 thrown 值，类型分流靠 `instanceof`：

```javascript
try {
  data = JSON.parse(text);
} catch (e) {
  if (e instanceof SyntaxError) {
    console.log("invalid json");
  } else {
    throw e; // 不认识的继续抛
  }
}
```

Python 把「按类型分流」写进语法：`except SomeError`。

---

### 2.3 `else`：为什么有用

#### 为什么要把成功路径挪出 try？

看这个反例：

```python
try:
    data = json.loads(text)
    # 下面这行如果炸了（比如 KeyError），也可能被下面的 except 吃掉
    return {"ok": True, "name": data["name"]}
except Exception:
    return {"ok": False, "error": "invalid_json"}
```

`data["name"]` 的 `KeyError` 会被误报成 `invalid_json`。根因被谎言掩盖。

#### 怎么写

```python
import json


def parse_name(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json"}
    else:
        # 只有 loads 成功才走这里；这里再炸，不会被上面的 except 误伤
        return {"ok": True, "name": data["name"]}
```

更稳妥时，成功路径里再对业务错误单独处理；但至少 **JSON 解析失败** 和 **字段缺失** 已经分开了。

#### 跑一下

```python
import json


def parse_payload(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json"}
    else:
        return {"ok": True, "data": data}


print(parse_payload('{"a": 1}'))
print(parse_payload("{bad}"))
```

#### 易错点

- `else` 在 try 里若 `return` / `break` / `continue` 提前离开，**不会**执行。
- `else` 不是必须的；逻辑很短时写在 try 里也可以——但 except 一旦写宽，就优先拆到 `else`。
- `else` 里抛出的异常，**不会**被同一个 try 的 `except` 捕获（这正是它的价值）。

#### JS 对照

JS 没有 try-else。常见写法是成功逻辑继续写在 try 里，或用提前 return：

```javascript
try {
  const data = JSON.parse(text);
  return { ok: true, data };
} catch (e) {
  if (e instanceof SyntaxError) {
    return { ok: false, error: "invalid_json" };
  }
  throw e;
}
```

Python 的 `else` 把「成功后」从「可能失败」里物理隔离，读代码时意图更清楚。

---

### 2.4 `finally` 与 return

#### 为什么 finally 几乎总会跑？

清理（关文件、释放锁、记一条结束日志）不能依赖「刚好没抛异常」。`finally` 保证：无论成功、失败、甚至 try/except 里 `return`，离开这块语句前都会尽量执行清理。

#### 怎么写 / 跑一下

```python
def f() -> int:
    try:
        return 1
    finally:
        print("finally still runs")


print("got:", f())
```

输出：

```text
finally still runs
got: 1
```

即使 `try` 里 `return`，`finally` 仍会执行，然后才把返回值交给调用方。

再看「finally 里也 return」会怎样（了解即可，生产少用）：

```python
def g() -> int:
    try:
        return 1
    finally:
        return 2  # 会覆盖 try 的 return


print(g())  # 2
```

#### 易错点

- 清理优先考虑 `with`（上一章上下文管理器）；`finally` 作为补充。
- `finally` 里再 `raise`，可能掩盖 try 里的原异常——见 §7。
- `finally` 里尽量别写复杂业务；只做清理与必达的收尾。

#### JS 对照

```javascript
function f() {
  try {
    return 1;
  } finally {
    console.log("finally still runs");
  }
}
console.log(f());
```

行为高度类似：`finally` 在 return 真正完成前执行。

---

### 2.5 多个 except 的匹配顺序

#### 为什么顺序重要？

Python **从上到下**找第一个匹配的 `except`。子类要写在父类前面，否则永远走不到子类分支。

#### 怎么写 / 跑一下

```python
class AgentError(Exception):
    pass


class ToolError(AgentError):
    pass


def classify(exc: Exception) -> str:
    try:
        raise exc
    except ToolError:
        return "tool"
    except AgentError:
        return "agent"
    except Exception:
        return "other"


print(classify(ToolError("x")))   # tool
print(classify(AgentError("x")))  # agent
print(classify(ValueError("x")))  # other
```

如果把 `except AgentError` 写在 `except ToolError` 前面，`ToolError` 分支会变成死代码。

#### 易错点

- 先具体、后宽泛。
- 同一个异常只会进入**一个** except 块。
- 元组形式 `except (A, B)` 表示「A 或 B」，不是顺序优先级问题——优先级仍是「哪个 except 子句先匹配」。

---

## 3. 必掌握：自定义异常

### 3.1 为什么要自定义？

#### 为什么内置异常不够用？

内置的 `ValueError` / `RuntimeError` 太泛。上层看到它们，无法直接决定「重试还是换工具」。Agent 里更希望：

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

#### 怎么写（先看意图）

自定义异常的本质是：**用类型表达处理策略差异**，而不是换一个同义英文名。

#### 易错点（先立规矩）

- 不要为每个细碎文案都建一个类；按「调用方怎么处理」分叉。
- 需要的上下文做成属性（`tool_name`、`retryable`），别只塞进字符串再让上层正则拆。

#### JS 对照

```javascript
class ToolNotFoundError extends Error {
  constructor(name) {
    super(name);
    this.name = "ToolNotFoundError";
    this.toolName = name;
  }
}
```

心智模型接近：都是继承错误基类，挂上业务字段。

---

### 3.2 最小层次设计

#### 为什么需要「一层基类 + 少量子类」？

有了领域基类 `AgentError`，最外层可以：

```python
except AgentError as exc:
    # 所有可预期业务失败的统一出口
    ...
```

同时又保留细分子类给重试/回传模型等策略。

#### 怎么写

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

层次示意：

```text
Exception
  └── AgentError
        ├── ToolError
        │     ├── ToolNotFoundError
        │     └── ToolExecutionError   (+ retryable)
        └── LLMError
              └── LLMRateLimitError    (+ retry_after)
```

建议：

- 有一个领域基类（`AgentError`）
- 子类表达**不同处理策略**，而不是无限细碎同义名
- 需要的上下文做成属性（`tool_name`、`retryable`）
- `__init__` 里记得 `super().__init__(...)`，否则 `str(exc)` / traceback 信息会空

#### 跑一下

```python
class AgentError(Exception):
    pass


class ToolError(AgentError):
    def __init__(self, tool_name: str, message: str = "") -> None:
        self.tool_name = tool_name
        super().__init__(message or tool_name)


class ToolExecutionError(ToolError):
    def __init__(self, tool_name: str, message: str, *, retryable: bool = False) -> None:
        self.retryable = retryable
        super().__init__(tool_name, message)


err = ToolExecutionError("search", "dns timeout", retryable=True)
print(err)                 # dns timeout
print(err.tool_name)       # search
print(err.retryable)       # True
print(isinstance(err, AgentError))  # True
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 忘了调用 `super().__init__` | `str(exc)` 为空，日志难看 |
| 子类无限膨胀（`SearchEmptyError`、`SearchTypoError`…） | 调用方 `except` 写爆；应按策略合并 |
| 把所有东西都挂在 `RuntimeError` | 失去类型分流能力 |

---

### 3.3 抛出与捕获

#### 为什么要「自己的异常放行，其它包装」？

工具层内部可能已经抛出 `ToolError`；外层再包一层会丢失语义。模式是：

1. 领域异常 → 原样再抛（`raise`）
2. 未知异常 → 包装成领域异常，并用 `from` 保留根因（下一节）

#### 怎么写

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

#### 跑一下

```python
class AgentError(Exception):
    pass


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


def boom() -> None:
    raise ValueError("bad")


def run_tool(name: str, registry: dict, **kwargs):
    if name not in registry:
        raise ToolNotFoundError(name)
    try:
        return registry[name](**kwargs)
    except ToolError:
        raise
    except Exception as exc:
        raise ToolExecutionError(name, str(exc), retryable=False) from exc


registry = {"boom": boom}

try:
    run_tool("missing", registry)
except ToolNotFoundError as exc:
    print("missing:", exc.tool_name)

try:
    run_tool("boom", registry)
except ToolExecutionError as exc:
    print("exec:", exc.tool_name, exc)
    print("cause:", repr(exc.__cause__))
```

#### 易错点

- `except ToolError: raise` 是「捕获后再原样抛出」，用来避免被后面的宽 `except Exception` 重新包装。
- `raise` 单独写（不带异常对象）会继续传播**当前正在处理的异常**；不要写成 `raise exc` 除非你清楚要截断/重抛的轨迹差异（入门阶段优先 `raise` 或 `raise NewError(...) from exc`）。
- 包装时务必 `from exc`，否则根因链条断掉——见下一节。

#### JS 对照

```javascript
try {
  return registry[name](...);
} catch (e) {
  if (e instanceof ToolError) throw e;
  throw new ToolExecutionError(name, String(e), { cause: e });
}
```

现代 JS 的 `{ cause: e }` 和 Python 的 `raise ... from ...` 是同一类想法。

---

## 4. 必掌握：异常链（`raise ... from ...`）

### 4.1 问题：丢失根因

#### 为什么「重新 raise 一个新异常」会伤排障？

```python
try:
    raw = '{"bad"}'
    json.loads(raw)
except Exception:
    raise RuntimeError("parse failed")  # 根因可能看不清
```

上层只看到 `RuntimeError: parse failed`，原始的 `JSONDecodeError` 细节可能被冲淡或弄丢（是否保留隐式链还取决于具体写法与版本习惯）。教学上请养成：**显式链接**。

#### 跑一下（反例体感）

```python
import json


def bad_parse(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        raise RuntimeError("parse failed")


try:
    bad_parse("{bad}")
except RuntimeError as exc:
    print("exc:", exc)
    print("__cause__:", exc.__cause__)
```

你真正需要的是：既能看到业务语义（parse failed），又能点进根因（哪一行 JSON 坏了）。

---

### 4.2 显式链接：`raise ... from ...`

#### 为什么需要 `from`？

`from exc` 把「直接原因」挂到新异常的 `__cause__` 上。打印 traceback 时会出现：

```text
The above exception was the direct cause of the following exception
```

排障友好得多：先读业务层语义，再顺着链看底层细节。

#### 怎么写

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

#### 跑一下

```python
import json


class ToolExecutionError(Exception):
    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(message)


def parse_tool_args(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolExecutionError("parser", "invalid json args") from exc
    if not isinstance(data, dict):
        raise ToolExecutionError("parser", "args must be object")
    return data


try:
    parse_tool_args("{bad}")
except ToolExecutionError as exc:
    print("business:", exc)
    print("cause type:", type(exc.__cause__).__name__)
    print("cause:", exc.__cause__)
```

#### 易错点

- `exc.__cause__` 是显式链（`from`）；另外还有 `__context__`（在 except 块里 raise 另一个异常时的隐式上下文）。入门优先把 `from` 写明白。
- 业务校验失败（如「必须是 object」）若没有底层异常，就直接 `raise ToolExecutionError(...)`，不必硬凑 `from`。
- 日志时：业务异常 + `repr(__cause__)` 或 `logging.exception` 一起看。

#### JS 对照

```javascript
try {
  data = JSON.parse(text);
} catch (e) {
  throw new ToolExecutionError("parser", "invalid json args", { cause: e });
}
```

| Python | JavaScript |
| --- | --- |
| `raise NewError(...) from exc` | `throw new NewError(..., { cause: exc })` |
| `exc.__cause__` | `error.cause` |

---

### 4.3 `from None`：有意隐藏内部异常

#### 为什么有时要断开链条？

API 边界不想把内部实现细节（文件路径、SQL、第三方库栈）直接暴露给调用方时，可以用 `from None` 抑制上下文。

#### 怎么写

```python
raise ToolNotFoundError(name) from None
```

#### 跑一下

```python
class ToolNotFoundError(Exception):
    pass


def public_api(name: str) -> None:
    try:
        raise KeyError(name)  # 内部细节
    except KeyError:
        raise ToolNotFoundError(name) from None


try:
    public_api("browse")
except ToolNotFoundError as exc:
    print(exc)
    print("__cause__:", exc.__cause__)  # None
```

#### 易错点

- 默认学习阶段优先 `from exc` 保留链。
- `from None` 是**有意**隐藏，不是偷懒；对内日志仍应记录原始异常。
- 对外返回给模型/用户的文案，与对内 traceback，本来就该两套详细度——见 §5。

---

## 5. 建议掌握：错误设计原则

### 5.1 几条实用原则

#### 为什么需要原则，而不是「能跑就行」？

Agent / API 里错误会穿过多层：HTTP 客户端 → 领域服务 → Tool Runtime → 模型对话。没有约定时，每一层都在用字符串和宽捕获「即兴创作」，最后谁都没法决策。

#### 怎么写（原则清单）

1. **失败要响亮**：不要返回 `"error"` 字符串假装成功；该抛就抛，或返回明确的 Result 结构并统一约定。
2. **按处理方式分类**：可重试 / 不可重试 / 用户可修正 / 系统故障。
3. **边界转译**：底层 `httpx.HTTPError` 到领域层变成 `LLMError`，避免上层依赖底层库异常类型。
4. **信息足够但安全**：日志可详细；返回给模型/用户的信息避免泄露密钥与内部路径。
5. **工具错误可回传模型**：Tool Calling 里，把结构化错误交给模型，常比直接中断整轮更有用。

#### 跑一下（边界转译示意）

```python
class LLMError(Exception):
    pass


class LLMRateLimitError(LLMError):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(f"rate limited, retry after {retry_after}s")


class FakeHTTPStatusError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"status={status_code}")


def call_llm() -> str:
    # 假装底层库抛了 HTTP 错误
    raise FakeHTTPStatusError(429)


def complete() -> str:
    try:
        return call_llm()
    except FakeHTTPStatusError as exc:
        if exc.status_code == 429:
            raise LLMRateLimitError(retry_after=30) from exc
        raise LLMError(str(exc)) from exc


try:
    complete()
except LLMRateLimitError as exc:
    print("retry after", exc.retry_after, "s")
    print("root:", type(exc.__cause__).__name__)
```

上层只依赖 `LLMRateLimitError`，不依赖 `FakeHTTPStatusError` / 真实 `httpx` 类型。

#### 易错点

- 「转译」不是「吞掉」：要用 `from exc` 留根因。
- 不要把密钥、完整 prompt、本地绝对路径塞进给模型看的 `str(exc)`。
- 分类维度优先「怎么处理」，不是「哪个函数抛的」。

#### JS 对照

原则通用。Express/Nest 等也常见「底层错误 → HttpException / DomainError」的边界转译；Agent 工具层同理。

---

### 5.2 Result 风格（可选补充）

#### 为什么有时不用异常做控制流？

异常适合「罕见 / 需要中断当前路径」。若失败是编排中的常态分支（工具偶发失败、检索为空），用 Result 字典/对象可能更清晰——调用方用 `if not result["ok"]` 继续跑，而不是层层 try。

#### 怎么写 / 跑一下

```python
def run_tool(name: str, fn, **kwargs) -> dict:
    try:
        return {"ok": True, "result": fn(**kwargs)}
    except ToolError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "tool": getattr(exc, "tool_name", name),
        }


class ToolError(Exception):
    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(message)


def flaky() -> str:
    raise ToolError("search", "empty index")


print(run_tool("search", flaky))
```

#### 易错点

- 团队内要统一：到底用异常还是 Result，避免混用到「有的层抛、有的层返回 ok:false、有的层返回 None」。
- Result 里仍建议带**机器可读**字段（`error_code` / `retryable`），别只有一句自然语言。
- 异常适合「罕见/需要中断」；Result 适合「预期内失败且要继续编排」。Agent runtime 两种都会见到。

#### JS 对照

类似 TypeScript 社区的 `Result` / `{ ok: true } | { ok: false }` 模式；或 `neverthrow` 一类库。Python 没有强制标准，约定比库更重要。

---

### 5.3 和重试装饰器配合

#### 为什么自定义异常要带 `retryable`？

重试是有成本的（延迟、费用、放大故障）。原则：

```text
只对 retryable / 瞬时网络类异常重试
对参数错误、鉴权失败不要盲着重试
```

这正是自定义异常带 `retryable` 属性的价值。

#### 怎么写 / 跑一下

```python
import time


class ToolExecutionError(Exception):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        self.retryable = retryable
        super().__init__(message)


def with_retry(fn, *, retries: int = 2, delay: float = 0.01):
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except ToolExecutionError as exc:
            last = exc
            if not exc.retryable or attempt == retries:
                raise
            time.sleep(delay)
    assert last is not None
    raise last


n = {"i": 0}


def sometimes() -> str:
    n["i"] += 1
    if n["i"] < 3:
        raise ToolExecutionError("timeout", retryable=True)
    return "ok"


print(with_retry(sometimes))  # ok
```

#### 易错点

- 限流（429）该退避；参数错误（400）重试一万次也没用。
- 重试要有上限与抖动（jitter）；教学示例可简化，生产别写死死循环。

---

## 6. 了解即可：`ExceptionGroup`（Python 3.11+）

### 6.1 为什么会有「一次多个异常」？

并发场景（如 `asyncio.TaskGroup`）里，多个子任务可能同时失败。传统「只能抛一个异常」装不下全貌，于是有了：

```python
ExceptionGroup("worker errors", [exc1, exc2])
```

#### 怎么写（概念示意）

```python
eg = ExceptionGroup(
    "worker errors",
    [
        ValueError("bad a"),
        ConnectionError("dns"),
    ],
)
print(eg)
print(eg.exceptions)
```

#### 跑一下：`except*` 按类型拆开

```python
def run() -> None:
    raise ExceptionGroup(
        "worker errors",
        [ValueError("bad a"), ConnectionError("dns")],
    )


try:
    run()
except* ValueError as eg:
    print("value errors:", eg.exceptions)
except* ConnectionError as eg:
    print("conn errors:", eg.exceptions)
```

注意是 `except*`（带星），不是普通 `except`。

#### 易错点

- 本阶段目标：知道有「异常组」这回事；见到 `TaskGroup` 报错里的 `ExceptionGroup` 不慌。
- 不要在同步单线程业务里强行发明 ExceptionGroup——它主要为并发聚合服务。
- 普通 `except Exception` **不会**按你想的那样把组内异常逐个当同级处理；要按类型拆开请用 `except*`。

#### JS 对照

JS 没有语言级 ExceptionGroup。`Promise.all` 失败时通常只看到**第一个** rejection；若要聚合，需自行设计（如 `Promise.allSettled` 再汇总）。Python 3.11+ 把「多错误一起抛」做成了语法与类型。

本阶段：

- 知道有「异常组」这回事
- 见到再查官方文档即可（关键词：`ExceptionGroup`、`except*`、`asyncio.TaskGroup`）

---

## 7. 常见坑

1. **裸 `except:`**  
   会捕获 `BaseException`（含 `KeyboardInterrupt` / `SystemExit`），等于连中断退出都吞掉。至少写 `except Exception:`，并慎重。

2. **捕获后空 `pass`**  
   问题被静默，后期极难查。

3. **用异常做普通分支（过度）**  
   高频可预期路径用 if/Result；异常用于错误路径。  
   反例：用 `try: d[k] except KeyError` 代替随手可得的 `if k in d` / `d.get`——偶尔可以，但不要当成默认风格。

4. **抛出字符串 / 抛出非 Exception**  
   始终 `raise SomeError(...)`。  
   （历史上曾允许 `raise "msg"`，现代 Python 已不允许。）

5. **在 `finally` 里 raise，掩盖原异常**  
   清理失败要额外小心；必要时先记日志，或把清理异常挂到链上。

6. **日志只打印 `str(e)`，不带 traceback**  
   关键路径用 `logging.exception(...)` 或 `logger.error(..., exc_info=True)`。

7. **except 顺序父类在前**  
   子类分支变死代码，策略永远走不到。

8. **包装异常却不写 `from`**  
   业务语义有了，根因断了——排障时只剩一句「failed」。

---

## 8. 综合小例子：迷你 Tool Runtime 错误处理

把本章必掌握点串起来：自定义层次、`try/except`、`raise from`、`retryable`、给调用方可读的结果。

#### 为什么要写这一整段？

真实 Tool Calling 层几乎都在做同一件事：

```text
解析参数 → 找工具 → 执行 → 成功返回 / 失败转译
```

错误必须区分：**工具不存在**、**参数坏了**、**瞬时网络**、**未知故障**。

#### 怎么写

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
        else:
            return {"ok": True, "name": name, "result": result}
```

#### 跑一下

```python
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

try:
    rt.call("search", "{bad json")
except ToolExecutionError as exc:
    print("parse failed:", exc, "| cause:", type(exc.__cause__).__name__)
```

预期直觉：

| 调用 | 异常 / 结果 | 上层策略 |
| --- | --- | --- |
| 正常 JSON | `{"ok": True, ...}` | 把 result 回传模型 |
| 未知工具名 | `ToolNotFoundError` | 提示模型换工具 |
| `query=network` | `ToolExecutionError(retryable=True)` | 可退避重试 |
| 坏 JSON | `ToolExecutionError` + `__cause__` 为 `JSONDecodeError` | 让模型改参数，不重试执行 |

这已经接近真实 Tool Calling 层的错误处理骨架。

#### 易错点（综合例）

- `TypeError`（缺参/多参）与 `ConnectionError` 必须分开：一个不可盲重试，一个可以。
- 成功返回放在 `else`，避免「构造返回值时」的异常被误包成 `ToolExecutionError`（本例返回很简单，但习惯值得保留）。
- 给模型看的错误文案用短语义（`invalid json`）；根因留在 `__cause__` / 日志里。

#### JS 对照（同一骨架）

```javascript
class ToolExecutionError extends Error {
  constructor(name, message, { retryable = false, cause } = {}) {
    super(message, { cause });
    this.toolName = name;
    this.retryable = retryable;
  }
}

// try { JSON.parse(...); runTool(...) }
// catch (e) { throw new ToolExecutionError(name, "...", { cause: e, retryable }) }
```

语义对齐即可，不必逐行翻译。

---

## 9. 练习指引

请打开并完成：

[`exercises/02-advanced-python/06-exception-system.md`](../../exercises/02-advanced-python/06-exception-system.md)

建议代码位置：

```text
playground/02-advanced-python/06-exception-system/
```

练习时优先自检：

1. except 是否够具体？
2. 自定义异常是否带了决策字段（如 `retryable`）？
3. 包装时有没有 `from`？
4. 最外层有没有把可预期业务错误和未知错误分开？

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

四句口诀：

```text
捕获要具体
类型表策略
from 留根因
边界做转译
```

### 自检清单

- [ ] 能正确使用 try/except/else/finally，并讲清执行顺序
- [ ] 能设计小型异常层次（基类 + 2～3 个子类）
- [ ] 会用 `raise ... from ...` 保留因果，知道 `from None` 的用途
- [ ] 能说明哪些错误可重试、哪些不该
- [ ] 见过 `ExceptionGroup` / `except*`，知道它和并发的关系
- [ ] 独立完成练习基础题

### 下一章

[`07-typing-system.md`](./07-typing-system.md) —— 类型系统：用注解与 Protocol/Generic 把「约定」写清楚，减少一整类运行时错误。  
（这也是模块 02 的收官章。）

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[上下文管理器](./05-context-manager.md)
- 下一章：[类型系统](./07-typing-system.md)
