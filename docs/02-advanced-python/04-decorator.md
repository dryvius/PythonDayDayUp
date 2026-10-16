# 装饰器

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/02-advanced-python/04-decorator.md`](../../exercises/02-advanced-python/04-decorator.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：学会用「不改函数核心逻辑」的方式，给函数加上重试、计时、日志、鉴权等横切能力。
- **前置**：闭包、`*args/**kwargs`、高阶函数（函数章）——装饰器本质就是它们的语法糖。

## 学习目标（学完应能做到）

1. 手写函数装饰器，并说清 `@decorator` 等价于什么。
2. 写出带参数的装饰器工厂（三层结构）。
3. 用 `functools.wraps` 保留原函数元信息。
4. 能实现重试 / 计时等实用装饰器；知道类装饰器与叠多个装饰器时的顺序。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 函数装饰器、带参数装饰器、保留元信息 | 能写、能读框架代码 |
| **建议掌握** | 类装饰器、重试/计时/鉴权场景 | 会落地常用模式 |
| **了解即可** | 装饰器栈顺序细节 | 知道规则，少炫技叠太多层 |

---

## 1. 为什么要学（和 Agent 有什么关系）

Agent / 后端里大量逻辑是「业务本身」+「外围策略」：

```text
调用 LLM
  + 失败重试
  + 记录耗时与 token
  + 校验 API Key / 权限
  + 统一把异常转成结构化错误
```

如果每个工具函数都手写一遍重试，代码会重复且难改。装饰器让你写成：

```python
@retry(max_attempts=3)
@timed
def call_llm(prompt: str) -> str:
    ...
```

许多框架的 `@app.get`、测试里的 `@pytest.fixture` 本身就是装饰器；FastAPI 的 `Depends` 是**依赖注入**（不是装饰器），但和装饰器一样常用于横切/组装横切能力。

---

## 2. 必掌握：函数装饰器

### 2.1 本质：函数进，函数出

```python
def logged(fn):
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)

    return wrapper


def add(a, b):
    return a + b


add = logged(add)   # 手工装饰
print(add(1, 2))
```

`@` 只是语法糖：

```python
@logged
def add(a, b):
    return a + b

# 完全等价于：
# def add(a, b): ...
# add = logged(add)
```

### 2.2 最小完整模板（请背下结构）

```python
from functools import wraps


def logged(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print(f"→ {fn.__name__}")
        result = fn(*args, **kwargs)
        print(f"← {fn.__name__}")
        return result

    return wrapper
```

结构永远是：

```text
decorator(fn):
    def wrapper(...):
        # 前处理
        result = fn(...)
        # 后处理
        return result
    return wrapper
```

### 2.3 和 JS 的对照（有前端经验时）

TS/JS 也有装饰器提案/框架装饰器；Python 的关键差异是：

- 运行时就是普通函数替换：`f = deco(f)`
- 先把「高阶函数」学扎实，`@` 就不神秘了

---

## 3. 必掌握：带参数的装饰器

当你想写 `@retry(max_attempts=3)` 时，需要多一层「工厂」：

```python
from functools import wraps
import time


def retry(max_attempts: int = 3, delay: float = 0.0):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:  # 演示用；真实项目应收窄异常类型
                    last_error = exc
                    if delay:
                        time.sleep(delay)
            raise RuntimeError(
                f"{fn.__name__} failed after {max_attempts} attempts"
            ) from last_error

        return wrapper

    return decorator


@retry(max_attempts=2)
def flaky():
    raise ValueError("boom")
```

三层分别是：

| 层 | 作用 | 例子 |
|----|------|------|
| 外层 | 接收装饰器参数 | `retry(max_attempts=2)` |
| 中层 | 接收被装饰函数 | `decorator(fn)` |
| 内层 | 实际被调用的包装器 | `wrapper(*args, **kwargs)` |

记忆口诀：

> **先配参数，再接函数，再接调用。**

无参装饰器可以看成「工厂已经关掉」的简化版；有参装饰器多一层。

---

## 4. 必掌握：保留元信息（`functools.wraps`）

没有 `@wraps` 时：

```python
def deco(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper


@deco
def create_message(role: str, content: str) -> dict:
    """创建一个消息。"""
    return {"role": role, "content": content}


print(create_message.__name__)  # wrapper  ← 丢了
print(create_message.__doc__)   # None     ← 丢了
```

加上 `@wraps(fn)` 后，`__name__` / `__doc__` / 注解等信息会尽量保留。  
对调试、日志、OpenAPI 文档、测试报错信息都很重要——**写装饰器默认带 wraps**。

---

## 5. 建议掌握：实际场景

### 5.1 计时

```python
from functools import wraps
import time


def timed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            cost_ms = (time.perf_counter() - start) * 1000
            print(f"{fn.__name__} took {cost_ms:.1f} ms")

    return wrapper


@timed
def work():
    time.sleep(0.01)
    return "ok"
```

Agent 里常用来观察「LLM 调用 / 工具执行」耗时。

### 5.2 鉴权（简化版）

```python
from functools import wraps


class AuthError(PermissionError):
    pass


def require_api_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        api_key = kwargs.get("api_key")
        if not api_key:
            raise AuthError("missing api_key")
        return fn(*args, **kwargs)

    return wrapper


@require_api_key
def call_provider(prompt: str, api_key: str | None = None) -> str:
    return f"ok:{prompt}"
```

真实系统会从 context / header / 依赖注入取身份；这里先体会「调用前拦截」。

### 5.3 组合使用

```python
@timed
@retry(max_attempts=3)
def call_llm(prompt: str) -> str:
    ...
```

等价于：

```python
call_llm = timed(retry(max_attempts=3)(call_llm))
```

---

## 6. 建议掌握：类装饰器

装饰器也可以是「可调用的类实例」：

```python
from functools import wraps


class Counter:
    def __init__(self, fn):
        wraps(fn)(self)  # 把元信息拷到实例上（常见写法之一）
        self.fn = fn
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.fn(*args, **kwargs)


@Counter
def ping():
    return "pong"


print(ping())
print(ping.calls)  # 1
```

何时用类装饰器：

- 需要在装饰器上保存较明显的状态（计数、缓存句柄）
- 或一套相关行为想组织成对象

多数场景函数装饰器足够；能读懂类装饰器即可。

> 另一种「类装饰器」是装饰**类本身**（`@dataclass` 就是）；那是「接收 class，返回 class」。先分清：本章主线是装饰函数。

---

## 7. 了解即可：装饰器栈顺序

多个装饰器时，**靠近函数的先应用**（更内层）：

```python
@a
@b
def f():
    ...

# 等价：f = a(b(f))
```

调用时则从外到内进入、再从内到外返回（像洋葱）：

```text
a 前处理
  b 前处理
    f 本体
  b 后处理
a 后处理
```

实践建议：

- 少叠层，优先可读
- 重试通常更靠近业务函数（内层），日志/计时可在外层包住「含重试的总耗时」或内层包「单次尝试」——**先想清楚你要量的是哪一段**

---

## 8. 常见坑

1. **忘记返回 `wrapper`**  
   装饰器函数必须返回可调用对象，否则 `@deco` 后原函数变成 `None`。

2. **忘记调用原函数或丢掉返回值**  
   `wrapper` 里要 `return fn(...)`。

3. **不写 `*args, **kwargs`**  
   包装后原参数签名容易挂。

4. **有参/无参混用写错层数**  
   `@retry` vs `@retry()`：若设计为有参工厂，通常应 `@retry()` 或 `@retry(3)`；不要两者语义混乱。

5. **在装饰器里吞掉所有异常还不记录**  
   重试可以 catch，但最终要抛出或转成明确错误。

6. **可变默认值/共享状态**  
   装饰器若把 list/dict 挂在闭包外层当缓存，注意线程与串扰（进阶话题）。

---

## 9. 综合小例子：Agent 工具上的计时 + 重试

```python
from functools import wraps
import time


def timed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            ms = (time.perf_counter() - start) * 1000
            print(f"[timed] {fn.__name__}: {ms:.1f}ms")

    return wrapper


def retry(max_attempts: int = 3):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last = None
            for i in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last = exc
                    print(f"[retry] {fn.__name__} attempt {i + 1} failed: {exc}")
            raise RuntimeError("exhausted") from last

        return wrapper

    return decorator


_calls = {"search": 0}


@timed
@retry(max_attempts=3)
def search(query: str) -> list[str]:
    _calls["search"] += 1
    if _calls["search"] < 3:
        raise ConnectionError("temporary network error")
    return [f"doc:{query}"]


print(search("RAG"))
print("name:", search.__name__)
```

观察：

- 前两次失败重试，第三次成功
- `[timed]` 量到的是「含重试」的总时间（因为 `timed` 在外层）
- `__name__` 仍是 `search`

---

## 10. 练习指引

请打开并完成：

[`exercises/02-advanced-python/04-decorator.md`](../../exercises/02-advanced-python/04-decorator.md)

建议代码位置：

```text
playground/02-advanced-python/04-decorator/
```

---

## 11. 小结与下一站

### 心智模型

```text
@deco
def f(...):
    ...

⇔

def f(...):
    ...
f = deco(f)
```

带参：

```text
@deco(x=1)  ⇔  f = deco(x=1)(f)
```

### 自检清单

- [ ] 能手写无参装饰器，并解释 `@` 等价替换
- [ ] 能手写三层带参装饰器（如 retry）
- [ ] 默认使用 `@wraps`
- [ ] 能说清多个装饰器时 `a(b(f))` 的含义
- [ ] 独立完成练习基础题

### 下一章

[`05-context-manager.md`](./05-context-manager.md) —— 上下文管理器：`with` 协议、资源管理，和装饰器一样都是「把前后置逻辑从业务里拆出去」。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[Iterator / Generator](./03-iterator-generator.md)
- 下一章：[上下文管理器](./05-context-manager.md)
