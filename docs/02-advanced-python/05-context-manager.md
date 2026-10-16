# 上下文管理器

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：2～4 小时  
> 对应练习：[`exercises/02-advanced-python/05-context-manager.md`](../../exercises/02-advanced-python/05-context-manager.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：学会用 `with` 把「获取资源 → 使用 → 必定清理」写成可靠结构；和装饰器一样，都是把前后置逻辑从业务里拆出去。
- **你早已用过**：`with open(...) as f:` 就是上下文管理器。

## 学习目标（学完应能做到）

1. 说清 `with` 背后调用了 `__enter__` / `__exit__`，以及异常时为何仍会清理。
2. 用 `contextlib.contextmanager` 快速写出上下文管理器。
3. 用 `with` 管理文件、锁、计时、临时状态等资源/边界。
4. 能手写基于类的上下文管理器；异步版本先建立印象即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | `with` 协议、`contextlib`、资源管理思维 | 能写、敢用、懂为何安全 |
| **建议掌握** | 自定义类上下文管理器 | 会实现 `__enter__`/`__exit__` |
| **了解即可** | 异步上下文管理器 | 知道 `async with`，后面异步章再用 |

---

## 1. 为什么要学（和 Agent 有什么关系）

Agent / 后端经常要保证「进得去、出得来」：

```text
打开文件 / DB 连接 / HTTP 客户端
临时切换工作目录或环境变量
给一段 LLM 调用计时、打 span（可观测性）
获取锁，避免并发写同一份 memory
会话开始 → 结束时 flush 日志
```

没有 `with` 时，人很容易写成：

```python
f = open("a.txt", "w", encoding="utf-8")
f.write("hi")
# 中间一旦异常，close 可能被跳过
f.close()
```

有 `with` 时：

```python
with open("a.txt", "w", encoding="utf-8") as f:
    f.write("hi")
# 不论成功还是异常，都会关闭
```

这就是上下文管理器的核心价值：**把清理逻辑绑定到作用域结束**。

---

## 2. 必掌握：`with` 协议

### 2.1 基本写法

```python
with EXPR as VAR:
    BODY
```

简化理解（**不是**与 `try/else` 逐行等价）：

```text
mgr = EXPR
VAR = mgr.__enter__()
try:
    BODY
except BaseException as e:
    若 mgr.__exit__(type(e), e, traceback) 返回 True：吞掉异常
    否则：继续抛出
# 正常离开 with（含 BODY 里 return/break/continue）也会调 __exit__(None, None, None)
# 注意：若把上面写成 try/else，BODY 里 return 时 else 不会执行——但真实 with 仍会清理
```

你不需要背实现细节，但要记住：

1. 进入 `with` → 调 `__enter__`
2. 离开 `with`（正常、异常、`return`/`break`）→ 都会调 `__exit__`
3. `__exit__` 负责清理

### 2.2 文件：最经典例子

```python
from pathlib import Path

path = Path("notes.txt")
with path.open("w", encoding="utf-8") as f:
    f.write("hello\n")

with path.open("r", encoding="utf-8") as f:
    print(f.read())
```

### 2.3 多个上下文

```python
with open("a.txt", encoding="utf-8") as fa, open("b.txt", encoding="utf-8") as fb:
    fa.read()
    fb.read()
```

或用括号多行写（Python 3.10+ 更常见的风格也可用嵌套 `with`）。

---

## 3. 必掌握：资源管理思维

把「资源」理解宽一点——不只是文件句柄：

| 类型 | 例子 | 进入时 | 退出时 |
|------|------|--------|--------|
| OS 资源 | 文件、socket | 打开 | 关闭 |
| 连接 | DB、HTTP client | connect | close/aclose |
| 并发 | Lock | acquire | release |
| 状态 | 临时改 `cwd` / env | 修改 | 恢复 |
| 观测 | timer / span | start | stop & log |

原则：

> **谁获取，谁负责释放；用 `with` 把释放钉死在作用域上。**

装饰器适合「包装函数调用」；上下文管理器适合「包装一段代码块」。两者常一起出现。

---

## 4. 必掌握：`contextlib` 快速写法

大多数时候，用生成器写上下文管理器比手写类更短。

### 4.1 `@contextmanager`

```python
from contextlib import contextmanager
import time


@contextmanager
def timed(label: str):
    start = time.perf_counter()
    try:
        yield  # yield 之前=进入；之后=退出
    finally:
        ms = (time.perf_counter() - start) * 1000
        print(f"{label}: {ms:.1f}ms")


with timed("llm_call"):
    time.sleep(0.01)
    # 业务代码
```

结构口诀：

```text
setup
try:
    yield 资源或 None
finally:
    cleanup
```

`yield` 出去的值，会成为 `as` 后面的变量：

```python
@contextmanager
def open_text(path: str, mode: str = "r"):
    f = open(path, mode, encoding="utf-8")
    try:
        yield f
    finally:
        f.close()
```

### 4.2 `closing` / `suppress`（认得即可）

```python
from contextlib import closing, suppress
from pathlib import Path
from urllib.request import urlopen

# closing：给只有 close()、没有上下文协议的对象临时补上
# suppress：有选择地忽略某些异常（慎用）

with suppress(FileNotFoundError):
    Path("maybe.txt").unlink()
```

`suppress` 不要拿来当「万能吞异常」；只用于真正可忽略的情况。

### 4.3 `ExitStack`（了解有这个工具）

需要动态数量的上下文（循环里打开很多文件）时可用 `ExitStack`。  
本阶段先知道名字；真遇到再查文档。

---

## 5. 建议掌握：自定义类上下文管理器

当逻辑更复杂、需要面向对象状态时，手写类：

```python
import time


class Timer:
    def __init__(self, label: str) -> None:
        self.label = label
        self.elapsed_ms = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        print(f"{self.label}: {self.elapsed_ms:.1f}ms")
        # 返回 None/False：不吞异常
        # 返回 True：吞掉异常（通常不建议）
        return None


with Timer("work") as t:
    time.sleep(0.01)

print("recorded:", t.elapsed_ms)
```

### `__exit__` 的三个参数

```python
def __exit__(self, exc_type, exc, tb):
    ...
```

| 情况 | 参数 |
|------|------|
| 块内正常结束 | 全是 `None` |
| 块内异常 | 异常类型、实例、traceback |

返回值：

- `False` / `None`：异常继续向外抛（默认）
- `True`：表示「我已处理」，异常被吞掉

学习阶段：**默认不吞异常**；清理放 `finally` 语义里完成即可。

---

## 6. 综合小例子：会话作用域 + 临时状态

### 6.1 Agent 会话计时与收尾

```python
from contextlib import contextmanager
from dataclasses import dataclass, field
import time


@dataclass
class Session:
    name: str
    events: list[str] = field(default_factory=list)

    def log(self, event: str) -> None:
        self.events.append(event)


@contextmanager
def agent_session(name: str):
    session = Session(name)
    session.log("start")
    start = time.perf_counter()
    try:
        yield session
        session.log("success")
    except Exception:
        session.log("error")
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        session.log(f"end:{ms:.1f}ms")
        print(session.events)


with agent_session("demo") as s:
    s.log("tool:search")
    s.log("llm:complete")
```

### 6.2 临时改字典配置（用完恢复）

```python
from contextlib import contextmanager


@contextmanager
def temporary_set(mapping: dict, key, value):
    missing = key not in mapping
    old = mapping.get(key)
    mapping[key] = value
    try:
        yield
    finally:
        if missing:
            mapping.pop(key, None)
        else:
            mapping[key] = old


config = {"model": "small", "temperature": 0.7}
with temporary_set(config, "temperature", 0):
    print("inside:", config["temperature"])  # 0
print("outside:", config["temperature"])     # 0.7
```

这种模式在测试里特别常见。

---

## 7. 了解即可：异步上下文管理器

异步世界用：

```python
async with http_client as client:
    ...
```

对应协议是：

```text
__aenter__ / __aexit__
```

以及：

```python
from contextlib import asynccontextmanager
```

HTTPX、数据库异步驱动、很多 LLM SDK 都会用到。  
等模块 05（异步）再实战；现在看到 `async with` 知道是「异步版 with」即可。

---

## 8. 常见坑

1. **在 `__enter__` 失败时仍假设资源已获取**  
   获取失败就不要进入「已打开」状态；清理逻辑要能容忍半初始化。

2. **`__exit__` 里再抛新异常，掩盖原异常**  
   清理失败时注意日志；Python 3 有异常链，但仍要小心。

3. **乱返回 `True` 吞异常**  
   调试时问题会「消失」，非常坑。

4. **`@contextmanager` 忘记 `try/finally`**  
   yield 之后若无 finally，异常路径可能跳过清理。

5. **把该用 `with` 的长生命周期对象每次都 with 掉**  
   例如全局复用的连接池，不一定每次请求都 create+close；要分清「作用域资源」和「应用级单例」。

6. **和装饰器职责混淆**  
   - 装饰器：增强**函数**
   - 上下文：增强**代码块 / 作用域**

---

## 9. 练习指引

请打开并完成：

[`exercises/02-advanced-python/05-context-manager.md`](../../exercises/02-advanced-python/05-context-manager.md)

建议代码位置：

```text
playground/02-advanced-python/05-context-manager/
```

---

## 10. 小结与下一站

### 心智模型

```text
with 资源 as x:
    使用 x

进入 → __enter__（或 generator yield 前）
离开 → __exit__（或 yield 后 finally）
异常也会离开 → 所以清理更可靠
```

### 自检清单

- [ ] 能解释为何 `with open` 比手工 `close` 更安全
- [ ] 能用 `@contextmanager` 写计时或临时改配置
- [ ] 知道 `__exit__` 三参数与「别随便吞异常」
- [ ] 独立完成练习基础题

### 下一章

[`06-exception-system.md`](./06-exception-system.md) —— 异常系统：如何设计错误、传播错误、在 Agent 工具调用里优雅失败。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[装饰器](./04-decorator.md)
- 下一章：[异常系统](./06-exception-system.md)
