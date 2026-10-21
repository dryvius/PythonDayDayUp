# 装饰器

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/02-advanced-python/04-decorator.md`](../../exercises/02-advanced-python/04-decorator.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：学会用「不改函数核心逻辑」的方式，给函数加上重试、计时、日志、鉴权等横切能力。
- **前置**：闭包、`*args/**kwargs`、高阶函数（函数章）——装饰器本质就是它们的语法糖。
- **你的优势**：若写过 Express/Koa 中间件、或见过 NestJS/TS 装饰器，心智模型很近；Python 这边更直白——运行时就是普通函数替换。

## 学习目标（学完应能做到）

1. 手写函数装饰器，并说清 `@decorator` 等价于什么。
2. 写出带参数的装饰器工厂（三层结构）。
3. 用 `functools.wraps` 保留原函数元信息。
4. 能实现重试 / 计时 / 鉴权等实用装饰器；知道类装饰器与叠多个装饰器时的顺序。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 函数装饰器、带参数装饰器、保留元信息 | 能写、能读框架代码 |
| **建议掌握** | 类装饰器、重试/计时/鉴权场景 | 会落地常用模式 |
| **了解即可** | 装饰器栈顺序细节 | 知道规则，少炫技叠太多层 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要装饰器？

Agent / 后端里大量逻辑是「业务本身」+「外围策略」：

```text
调用 LLM
  + 失败重试
  + 记录耗时与 token
  + 校验 API Key / 权限
  + 统一把异常转成结构化错误
```

如果每个工具函数都手写一遍重试，代码会重复且难改：

```python
def call_llm(prompt: str) -> str:
    for attempt in range(3):
        try:
            # 真正业务只有下面两行，其余全是外围
            ...
            return result
        except ConnectionError:
            time.sleep(0.5)
    raise RuntimeError("exhausted")
```

装饰器让你把「外围」抽出去，业务函数只剩业务：

```python
@retry(max_attempts=3)
@timed
def call_llm(prompt: str) -> str:
    ...
```

#### 和 Agent / 框架的关系

许多框架的 `@app.get`、测试里的 `@pytest.fixture` 本身就是装饰器；FastAPI 的 `Depends` 是**依赖注入**（不是装饰器），但和装饰器一样常用于横切/组装横切能力。

可以先记一句：

> 装饰器 = 在不改动函数「内部逻辑」的前提下，用一层包装换掉原函数名指向的对象。

---

## 2. 必掌握：函数装饰器

这一节会刻意写细——装饰器是后面重试、计时、鉴权、框架路由装饰的共同底座。

### 2.1 本质：函数进，函数出

#### 为什么要先抓住这句话？

装饰器看起来像「魔法语法」，其实只是一个接受函数、返回函数的高阶函数。  
先把「函数进、函数出」跑通，`@` 就不神秘了。

#### 怎么写

```python
def logged(fn):
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)

    return wrapper


def add(a, b):
    return a + b


add = logged(add)   # 手工装饰：把 add 换成「带日志的 add」
```

拆开看发生了什么：

```text
1. logged 收到原函数 add（函数进）
2. 内部定义 wrapper：调用前后加逻辑，再调用原 add
3. logged 返回 wrapper（函数出）
4. add = logged(add) → 名字 add 现在指向 wrapper
```

心智图：

```text
调用方写：add(1, 2)
           │
           ▼
      wrapper(1, 2)      ← 名字还叫 add，实际是包装器
           │
           ├─ print("calling add")
           ├─ 原 add(1, 2) → 3
           └─ return 3
```

#### 跑一下

```python
print(add(1, 2))
# calling add
# 3
```

再确认「名字指向变了」：

```python
def add(a, b):
    return a + b

print(add)          # <function add at 0x...>
add = logged(add)
print(add)          # <function logged.<locals>.wrapper at 0x...>
print(add.__name__) # wrapper   ← 元信息丢了，§4 用 wraps 修
```

#### `@` 只是语法糖

```python
@logged
def add(a, b):
    return a + b

# 完全等价于：
# def add(a, b): ...
# add = logged(add)
```

定义结束后立刻执行一次替换——不是「每次调用才装饰」。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| `logged` 里忘了 `return wrapper` | `@logged` 后原函数变成 `None`，一调用就 TypeError |
| `wrapper` 里写了 `fn(...)` 但没 `return` | 原函数有返回值时，调用方拿到 `None` |
| 以为 `@logged` 每次调用都重新包装 | 只在定义时包装一次；之后每次调用的是同一个 `wrapper` |
| 手写 `add = logged(add)` 时写成 `logged(add())` | 传进去的是返回值，不是函数 |

#### JS 对照

| 概念 | Python | JavaScript（近似） |
|------|--------|-------------------|
| 高阶包装 | `f = deco(f)` | `const f = deco(f)` |
| 语法糖 | `@deco` | TC39 装饰器 / 框架装饰器（语法不同） |
| 中间件感 | `wrapper` 前后插逻辑 | Express/Koa 的 `(req,res,next)` 链 |

```javascript
// JS 里「手工装饰」的直觉版
function logged(fn) {
  return function wrapper(...args) {
    console.log(`calling ${fn.name}`)
    return fn(...args)
  }
}

let add = (a, b) => a + b
add = logged(add)
console.log(add(1, 2))  // calling add → 3
```

Python 的关键差异：运行时就是普通函数替换，没有单独的「装饰器运行时协议」要背。

---

### 2.2 最小完整模板（请背下结构）

#### 为什么需要「完整模板」？

演示版经常省略 `wraps`、`*args/**kwargs`、返回值。  
真实装饰器缺任何一项都会在下一周踩坑——所以直接背生产级最小模板。

#### 怎么写

```python
from functools import wraps


def logged(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 前处理
        print(f"→ {fn.__name__}")
        result = fn(*args, **kwargs)
        # 后处理
        print(f"← {fn.__name__}")
        return result

    return wrapper
```

结构永远是：

```text
decorator(fn):                 # ① 接收被装饰函数
    @wraps(fn)                 # ② 保留元信息（默认带上）
    def wrapper(*args, **kwargs):
        # 前处理
        result = fn(*args, **kwargs)   # ③ 调用原函数
        # 后处理
        return result                  # ④ 把返回值交回去
    return wrapper             # ⑤ 把包装器交出去
```

口诀：

> **接函数 → 包一层 → 前后插逻辑 → 原样转发参数与返回值 → 返回包装器。**

#### 跑一下

```python
@logged
def greet(name: str) -> str:
    """打个招呼。"""
    return f"hi, {name}"


print(greet("Alice"))
print(greet.__name__)  # greet（因为有 wraps）
print(greet.__doc__)   # 打个招呼。
```

预期输出大致是：

```text
→ greet
← greet
hi, Alice
greet
打个招呼。
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 只写 `fn(*args, **kwargs)` 不接 `result` | 后处理拿不到返回值，也容易忘 `return` |
| 参数写成固定 `(a, b)` | 只能装饰特定签名；换个函数就挂 |
| 异常路径不做 `try/finally` | 计时/日志在抛错时丢「后处理」（见 §5.1） |
| 在模板里写业务细节 | 模板应保持通用；业务进具体装饰器 |

#### JS 对照

```javascript
function logged(fn) {
  function wrapper(...args) {
    console.log(`→ ${fn.name}`)
    const result = fn(...args)
    console.log(`← ${fn.name}`)
    return result
  }
  // JS 没有 functools.wraps 标配；常手写拷贝 name/length
  Object.defineProperty(wrapper, "name", { value: fn.name })
  return wrapper
}
```

Python 用 `@wraps(fn)` 一行搞定；§4 细讲为什么必须带。

---

### 2.3 和 JS 的对照（有前端经验时）

TS/JS 也有装饰器提案/框架装饰器；Python 的关键差异是：

- 运行时就是普通函数替换：`f = deco(f)`
- 先把「高阶函数」学扎实，`@` 就不神秘了
- 叠多个装饰器时，Python 规则极清晰：靠近函数的先应用（§7）

先不必纠结 TS 实验性装饰器的阶段差异；把 Python 这边的替换模型吃透即可。

---

## 3. 必掌握：带参数的装饰器

### 3.1 为什么多一层？

无参装饰器是 `@logged`，Python 做的是 `add = logged(add)`。  
有参装饰器是 `@retry(max_attempts=3)`，括号先要「吃掉参数」，所以必须多一层工厂：

```text
@retry(max_attempts=3)
def flaky(): ...

⇔

def flaky(): ...
flaky = retry(max_attempts=3)(flaky)
#          └─ 返回 decorator ─┘ └─ 再装饰函数
```

若只有两层，`retry(max_attempts=3)` 的返回值就必须是「还能再接收 `fn` 的装饰器」。

### 3.2 三层完整写法

#### 怎么写

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
```

三层分别是：

| 层 | 作用 | 例子 | 调用时机 |
|----|------|------|----------|
| 外层 | 接收装饰器参数 | `retry(max_attempts=2)` | 写 `@retry(...)` 时立刻执行 |
| 中层 | 接收被装饰函数 | `decorator(fn)` | 外层返回后立刻执行 |
| 内层 | 实际被调用的包装器 | `wrapper(*args, **kwargs)` | 每次调用业务函数时 |

记忆口诀：

> **先配参数，再接函数，再接调用。**

展开成时间线：

```text
定义阶段：
  retry(max_attempts=2)  → 得到 decorator（闭包里记住了 2）
  decorator(flaky)       → 得到 wrapper
  名字 flaky 指向 wrapper

调用阶段：
  flaky()  → 实际跑 wrapper() → 内部按次数调用原 flaky
```

#### 跑一下

```python
@retry(max_attempts=2)
def flaky():
    raise ValueError("boom")


try:
    flaky()
except RuntimeError as e:
    print(type(e).__name__, "→", e)
    print("cause:", repr(e.__cause__))
```

预期：最终抛 `RuntimeError`，`__cause__` 仍是原来的 `ValueError("boom")`（`raise ... from last_error`）。

再看「成功路径」：

```python
_state = {"n": 0}


@retry(max_attempts=3)
def sometimes_ok() -> str:
    _state["n"] += 1
    if _state["n"] < 3:
        raise ConnectionError("temp")
    return "ok"


print(sometimes_ok())  # ok（前两次失败，第三次成功）
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 写成两层却用 `@retry(3)` | `retry(3)` 返回的是 `wrapper` 或类型对不上，装饰结果错乱 |
| 设计为工厂却写 `@retry`（没括号） | 传入的「fn」其实是默认参数值/整型，不是函数 |
| 中层忘了 `return wrapper` | 装饰后得到 `None` |
| `except Exception` 太宽 | 把 `KeyboardInterrupt` 以外的逻辑错误也重试掉（练习里会要求收窄） |
| 重试成功后还 `raise` | 控制流写错；成功应 `return fn(...)` 立刻结束 |

#### 无参 vs 有参：怎么统一心智

无参装饰器可以看成「工厂已经关掉」的简化版；有参装饰器多一层。

```text
无参：  decorator(fn) → wrapper
有参：  factory(*opt) → decorator(fn) → wrapper
```

若希望 `@retry` 和 `@retry()` 都能用，需要额外判断「第一个参数是不是 callable」——本章不强制；**宁可明确只支持 `@retry()` / `@retry(...)`**，语义更干净。

#### JS 对照

```javascript
function retry({ maxAttempts = 3, delay = 0 } = {}) {
  return function decorator(fn) {
    return async function wrapper(...args) {
      let last
      for (let i = 0; i < maxAttempts; i++) {
        try {
          return await fn(...args)
        } catch (e) {
          last = e
          if (delay) await new Promise(r => setTimeout(r, delay))
        }
      }
      throw last
    }
  }
}

// 用法直觉：retry({ maxAttempts: 2 })(flaky)
```

Python 的 `@retry(max_attempts=2)` 就是把上面两次调用折叠成语法糖。

---

## 4. 必掌握：保留元信息（`functools.wraps`）

### 4.1 为什么必须保留？

装饰之后，对外暴露的是 `wrapper`。若不处理：

- `__name__` 变成 `"wrapper"` → 日志、监控、pytest 失败信息全变难看
- `__doc__` 丢失 → 帮助文档/OpenAPI 描述可能空掉
- `__annotations__` 丢失 → 类型工具、文档生成读不到签名

Agent / FastAPI / 测试栈都依赖这些元信息——**写装饰器默认带 wraps**。

### 4.2 怎么写 / 跑一下

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

加上 `@wraps(fn)`：

```python
from functools import wraps


def deco(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper


@deco
def create_message(role: str, content: str) -> dict:
    """创建一个消息。"""
    return {"role": role, "content": content}


print(create_message.__name__)  # create_message
print(create_message.__doc__)   # 创建一个消息。
```

`wraps` 本质是把原函数的若干属性拷到 `wrapper` 上，并设置 `__wrapped__` 指向原函数（便于调试时「拆开洋葱」）。

### 4.3 易错点

| 错法 | 会发生什么 |
|------|------------|
| 写成 `@wraps` 却忘了传 `fn` | TypeError / 装饰行为异常 |
| 只手动改 `__name__` | 漏掉 `__doc__`、注解、`__module__` 等 |
| 类装饰器里忘了处理元信息 | 实例可调用，但名字仍不对（见 §6） |
| 以为 wraps 会复制闭包状态 | 不会；它只管元信息，不管你的计数器/缓存 |

### 4.4 JS 对照

| 需求 | Python | JavaScript |
|------|--------|------------|
| 保留函数名 | `@wraps(fn)` | 常手写 `Object.defineProperty(wrapper, "name", …)` |
| 指向原函数 | `fn.__wrapped__`（wraps 会设） | 无统一标准，框架各自约定 |

结论：Python 把这件事标准化了——**默认带上，别省**。

---

## 5. 建议掌握：实际场景

横切能力里最高频的三件套：**计时、鉴权、重试**（重试工厂已在 §3，这里补场景细节与组合）。

### 5.1 计时

#### 为什么需要？

Agent 里常要观察「LLM 调用 / 工具执行」耗时，才能判断慢在模型还是慢在工具。

#### 怎么写

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
```

要点：用 `try/finally`，这样**成功或抛错都会打印耗时**；`time.perf_counter()` 适合测间隔。

#### 跑一下

```python
@timed
def work():
    time.sleep(0.01)
    return "ok"


print(work())
# work took 10.x ms
# ok
```

抛错时也会有耗时日志：

```python
@timed
def boom():
    time.sleep(0.005)
    raise ValueError("x")


try:
    boom()
except ValueError:
    print("caught")
# boom took 5.x ms
# caught
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 只用 `time.time()` | 一般能用，但测短间隔更推荐 `perf_counter` |
| 把 `print` 放在 `return` 前且无 `finally` | 异常路径没有耗时 |
| 计时装饰器叠在重试内层/外层不先想清 | 量到的是「单次」还是「含重试总时间」（见 §7） |

#### JS 对照

```javascript
function timed(fn) {
  return function wrapper(...args) {
    const start = performance.now()
    try {
      return fn(...args)
    } finally {
      console.log(`${fn.name} took ${(performance.now() - start).toFixed(1)} ms`)
    }
  }
}
```

---

### 5.2 鉴权（简化版）

#### 为什么需要？

工具函数被调用前，常常要拦截「没带身份」的请求。装饰器非常适合做这种「调用前闸门」。

#### 怎么写

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

#### 跑一下

```python
print(call_provider("hi", api_key="secret"))  # ok:hi

try:
    call_provider("hi")
except AuthError as e:
    print(e)  # missing api_key
```

注意：示例从 `kwargs` 取 `api_key`。若调用方写位置参数传入，演示版可能取不到——生产里通常统一「从 context 读」，而不是扫 `*args`。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 鉴权失败还继续调用 `fn` | 等于没鉴权 |
| 用裸 `Exception` 表示未授权 | 调用方不好区分；用专用异常更清晰 |
| 教学用 `!=` 比较密钥就当生产方案 | 生产还应考虑恒定时间比较等（见课程约定） |

#### JS 对照

更接近 Express 中间件「先鉴权再 `next()`」：

```javascript
function requireApiKey(fn) {
  return function wrapper(opts) {
    if (!opts?.apiKey) throw new Error("missing api_key")
    return fn(opts)
  }
}
```

---

### 5.3 重试（场景补强）

§3 已给出三层工厂；这里强调落地时的三点：

1. **收窄异常**：只重试 `ConnectionError` / `TimeoutError` 等瞬时错误，不要无脑 `except Exception`
2. **保留因果**：最终失败用 `raise ... from last_error`，方便排查
3. **和计时组合时想清楚量的是哪一段**（§7）

最小「收窄版」骨架：

```python
from functools import wraps
import time


def retry(max_attempts: int = 3, delay: float = 0.0, errors: tuple = (ConnectionError,)):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except errors as exc:
                    last_error = exc
                    if delay:
                        time.sleep(delay)
            raise RuntimeError(
                f"{fn.__name__} failed after {max_attempts} attempts"
            ) from last_error

        return wrapper

    return decorator
```

#### 跑一下（收窄后「逻辑错误不重试」）

```python
@retry(max_attempts=3, errors=(ConnectionError,))
def bad_logic():
    raise ValueError("bug")  # 不在 errors 里 → 立刻抛出，不会重试


try:
    bad_logic()
except ValueError as e:
    print("no retry:", e)
```

---

### 5.4 组合使用

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

读法：先套 `retry`，再套 `timed`——因此 `timed` 看到的是「已经带重试的函数」。细节见 §7。

---

## 6. 建议掌握：类装饰器

### 6.1 为什么还要用类？

函数装饰器靠闭包存状态（如计数）完全可行。  
当状态更明显、或一组相关行为想组织成对象时，用「可调用的类实例」当装饰器更清晰。

### 6.2 怎么写：装饰函数的类

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
```

发生了什么：

```text
@Counter
def ping(): ...

⇔

def ping(): ...
ping = Counter(ping)   # ping 现在是 Counter 实例
```

调用 `ping()` 时走的是 `Counter.__call__`。

#### 跑一下

```python
print(ping())       # pong
print(ping())       # pong
print(ping.calls)   # 2
print(ping.__name__)  # ping（若 wraps 生效）
```

### 6.3 何时用类装饰器

- 需要在装饰器上保存较明显的状态（计数、缓存句柄）
- 或一套相关行为想组织成对象

多数场景函数装饰器足够；能读懂类装饰器即可。

### 6.4 另一种「类装饰器」：装饰类本身

> 另一种「类装饰器」是装饰**类本身**（`@dataclass` 就是）；那是「接收 class，返回 class」。先分清：本章主线是装饰函数。

```python
def add_hello(cls):
    cls.hello = lambda self: "hello"
    return cls


@add_hello
class User:
    pass


print(User().hello())  # hello
```

这和 `@Counter` 装饰函数不是同一条主线，但阅读框架代码时会遇到——知道「进什么出什么」即可。

### 6.5 易错点

| 错法 | 会发生什么 |
|------|------------|
| 类里只写 `__init__` 不写 `__call__` | 装饰后不可调用 |
| 忘记 `wraps(fn)(self)`（或等价处理） | `__name__` 等元信息不对 |
| 把「装饰函数的类」和「装饰类的函数」混谈 | 阅读 `@dataclass` 时会懵 |
| 实例状态当全局缓存且多线程共享 | 可能串扰（进阶话题） |

### 6.6 JS 对照

类装饰器在 TS/框架里更常见；Python 这边记住：

```text
装饰函数的类：  class → 实例，实例可调用（__call__）
装饰类的函数：  接收 type，返回 type
```

---

## 7. 了解即可：装饰器栈顺序

### 7.1 为什么顺序值得单独记？

多个装饰器时，**写反了不会语法报错**，但日志、耗时、重试次数的语义会悄悄变错——排障时非常坑。

### 7.2 规则：靠近函数的先应用

多个装饰器时，**靠近函数的先应用**（更内层）：

```python
@a
@b
def f():
    ...

# 等价：f = a(b(f))
```

定义时自下而上包装；调用时则从外到内进入、再从内到外返回（像洋葱）：

```text
a 前处理
  b 前处理
    f 本体
  b 后处理
a 后处理
```

#### 跑一下（用打印钉死顺序）

```python
def a(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print("a →")
        result = fn(*args, **kwargs)
        print("a ←")
        return result
    return wrapper


def b(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print("b →")
        result = fn(*args, **kwargs)
        print("b ←")
        return result
    return wrapper


@a
@b
def f():
    print("f")
    return 1


f()
```

输出：

```text
a →
b →
f
b ←
a ←
```

与 `f = a(b(f))` 完全一致。

### 7.3 和计时 / 重试组合时怎么选？

```python
@timed
@retry(max_attempts=3)
def call_llm(prompt: str) -> str:
    ...
```

- `timed` 在外：量到的是**含重试的总耗时**（更常见：用户感知延迟）
- 若写成 `@retry` 在外、`@timed` 在内：每次尝试各自计时，总耗时要自己加

实践建议：

- 少叠层，优先可读
- 重试通常更靠近业务函数（内层），日志/计时可在外层包住「含重试的总耗时」或内层包「单次尝试」——**先想清楚你要量的是哪一段**

### 7.4 易错点

| 错法 | 会发生什么 |
|------|------------|
| 凭「从上到下」猜调用顺序 | 容易反了；请用 `a(b(f))` 推 |
| 叠很多层做炫技 | 可读性崩；排障成本高 |
| 鉴权放在重试最内层且鉴权失败也重试 | 浪费次数；鉴权失败通常不应重试 |

### 7.5 JS 对照

和中间件洋葱模型同构：先入外层，再入内层，返回时反向。  
Python 装饰器栈用 `a(b(f))` 一次就能推干净。

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

7. **不用 `wraps`**  
   日志和测试里全是 `wrapper`，排查成本立刻上升。

8. **栈顺序凭感觉**  
   永远还原成 `f = a(b(f))` 再谈语义。

---

## 9. 综合小例子：Agent 工具上的计时 + 重试

把本章主线串起来：三层 `retry`、`timed`、`wraps`、栈顺序。

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

建议你改成 `@retry` 在外、`@timed` 在内再跑一遍，对比打印次数与耗时含义——这是把 §7 内化最快的方式。

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

三层口诀：

```text
先配参数 → 再接函数 → 再接调用
```

完整模板骨架：

```text
decorator(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 前
        result = fn(*args, **kwargs)
        # 后
        return result
    return wrapper
```

栈顺序：

```text
@a
@b
def f(): ...
⇔ f = a(b(f))
```

### 自检清单

- [ ] 能手写无参装饰器，并解释 `@` 等价替换
- [ ] 能手写三层带参装饰器（如 retry）
- [ ] 默认使用 `@wraps`
- [ ] 能说清多个装饰器时 `a(b(f))` 的含义
- [ ] 能解释计时在重试外层/内层分别量到什么
- [ ] 独立完成练习基础题

### 下一章

[`05-context-manager.md`](./05-context-manager.md) —— 上下文管理器：`with` 协议、资源管理，和装饰器一样都是「把前后置逻辑从业务里拆出去」。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[Iterator / Generator](./03-iterator-generator.md)
- 下一章：[上下文管理器](./05-context-manager.md)
