# 上下文管理器

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：2～4 小时（有 JS `try/finally` 经验可更快；`__exit__` 吞异常与 `@contextmanager` 建议动手踩一遍）  
> 对应练习：[`exercises/02-advanced-python/05-context-manager.md`](../../exercises/02-advanced-python/05-context-manager.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：学会用 `with` 把「获取资源 → 使用 → 必定清理」写成可靠结构；和装饰器一样，都是把前后置逻辑从业务里拆出去。
- **你早已用过**：`with open(...) as f:` 就是上下文管理器。
- **你的优势**：JS/TS 里的 `try { ... } finally { ... }` 经验可以直接迁移；Python 用 `with` 把这段模式固化成协议。

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

#### 为什么需要上下文管理器？

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

#### 本章要练的三种能力

1. **边界清晰**：哪一段代码「占用」了资源，离开就释放
2. **异常安全**：业务抛错时，清理逻辑仍然执行
3. **可读性**：把 setup / teardown 从业务中间抽出去（和装饰器互补）

可以先记一句：

> 上下文管理器的核心价值：**把清理逻辑绑定到作用域结束**。

#### JS 对照（先建立地图）

| JavaScript | Python |
| --- | --- |
| `try { use(res) } finally { cleanup() }` | `with mgr as res: use(res)` |
| 手写 `finally` 保证关闭 | `__exit__` / `yield` 后的 `finally` 自动保证 |
| 没有官方统一的「资源协议」 | `__enter__` / `__exit__` 是语言级协议 |

装饰器适合「包装函数调用」；上下文管理器适合「包装一段代码块」。两者常一起出现。

---

## 2. 必掌握：`with` 协议

这一节会刻意写细——`with` 协议是后面 `@contextmanager`、自定义类、异步版的共同底座。

### 2.1 基本写法

#### 为什么需要这套语法？

你已经会 `try/finally`。但「获取 → 使用 → 清理」出现太频繁时，每次手写 `try/finally` 又长又容易漏。`with` 把这段模式收成固定语法：进入时准备，离开时清理。

#### 怎么写

```python
with EXPR as VAR:
    BODY
```

三件事：

1. `EXPR`：产生一个「上下文管理器」对象（实现了协议）
2. `as VAR`：可选；把 `__enter__` 的返回值绑到名字上
3. `BODY`：真正使用资源的代码块；块结束（任何方式）都会触发清理

#### 跑一下

```python
from pathlib import Path

path = Path("notes.txt")
with path.open("w", encoding="utf-8") as f:
    f.write("hello\n")

with path.open("r", encoding="utf-8") as f:
    content = f.read()

print(content)  # hello
# 到这里两个文件句柄都已关闭
```

心智图：

```text
with EXPR as VAR:
    BODY

≈

mgr = EXPR
VAR = mgr.__enter__()
try:
    BODY
finally:
    mgr.__exit__(exc_type, exc, tb)   # 正常离开时三者都是 None
```

上面是**简化理解**（**不是**与 `try/else` 逐行等价）。你不需要背 CPython 实现，但要记住三条：

1. 进入 `with` → 调 `__enter__`
2. 离开 `with`（正常、异常、`return`/`break`/`continue`）→ 都会调 `__exit__`
3. `__exit__` 负责清理；它的返回值决定要不要吞异常（见后文）

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为只有「跑完 BODY」才清理 | `return` / `break` / 异常离开也会调 `__exit__` |
| 把协议想成 `try/else` | BODY 里 `return` 时 `else` 不执行，但真实 `with` 仍会清理 |
| 忘记 `as` 时以为拿不到资源 | 可以不写 `as`；需要句柄/对象时再写 |

#### JS 对照

```javascript
// JS：靠 try/finally 自己保证
const f = openFile("notes.txt")
try {
  f.write("hello\n")
} finally {
  f.close()
}
```

```python
# Python：协议替你保证
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("hello\n")
```

---

### 2.2 协议展开：`__enter__` / `__exit__` 何时调用

#### 为什么要把「何时调用」钉死？

读框架源码、写自定义管理器时，你必须知道：异常路径会不会清理？`as` 拿到的是什么？否则容易写出「看起来关了、其实没关」的代码。

#### 怎么写（协议签名）

```python
class Manager:
    def __enter__(self):
        # 获取资源 / 改状态
        return resource_or_self

    def __exit__(self, exc_type, exc, tb):
        # 释放资源 / 恢复状态
        # 返回 True 会吞掉异常；False/None 继续抛出
        return None
```

调用顺序（正常路径）：

```text
1. 求值 EXPR → 得到 mgr
2. mgr.__enter__() → 返回值赋给 as 后面的变量
3. 执行 BODY
4. mgr.__exit__(None, None, None)
```

调用顺序（异常路径）：

```text
1～2 同上
3. BODY 抛出异常 e
4. mgr.__exit__(type(e), e, traceback)
5. 若 __exit__ 返回 True → 异常被吞掉，继续往下执行
   若返回 False/None → 异常继续向外抛
```

#### 跑一下

用一个「会打印日志」的迷你管理器看清顺序：

```python
class Trace:
    def __enter__(self):
        print("enter")
        return "resource"

    def __exit__(self, exc_type, exc, tb):
        print("exit", exc_type)
        return False  # 不吞异常


print("--- 正常 ---")
with Trace() as x:
    print("body", x)

print("--- 异常 ---")
try:
    with Trace() as x:
        print("body", x)
        raise ValueError("boom")
except ValueError as e:
    print("caught", e)
```

期望输出大致是：

```text
--- 正常 ---
enter
body resource
exit None
--- 异常 ---
enter
body resource
exit <class 'ValueError'>
caught boom
```

注意：即使 `BODY` 里 `raise`，`exit` 那一行**仍然出现**——这就是 `with` 比裸 `close()` 更安全的原因。

#### 易错点

- `__enter__` 的返回值才是 `as` 后面的变量；默认不是「管理器自己」，除非你 `return self`
- `__exit__` **总会被调用**（只要 `__enter__` 成功返回了）；别在 `__exit__` 里假设「一定成功跑完了 BODY」
- 若 `__enter__` 自己就抛错，**不会**调用 `__exit__`（资源根本没获取成功）

#### JS 对照

| 概念 | JavaScript | Python |
| --- | --- | --- |
| 进入 | `try` 之前的准备代码 | `__enter__` |
| 使用 | `try` 块 | `with` 的 BODY |
| 离开 | `finally` | `__exit__` |
| 是否吞异常 | `catch` 里决定 | `__exit__` 返回 `True`/`False` |

---

### 2.3 文件：最经典例子

#### 为什么文件是入门第一例？

文件句柄是 OS 资源：不关会泄漏；异常时更容易忘关。`open` / `Path.open` 自带上下文协议，是练「看到 `with` 就安心」的最佳起点。

#### 怎么写 / 跑一下

```python
from pathlib import Path

path = Path("notes.txt")

# 写
with path.open("w", encoding="utf-8") as f:
    f.write("hello\n")
    f.write("world\n")

# 读
with path.open("r", encoding="utf-8") as f:
    print(f.read())
```

Agent 场景里常见写法：

```python
def load_system_prompt(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read().strip()
```

即使后面解析 JSON 失败，文件也已经关掉——因为 `return` 离开 `with` 时会先走 `__exit__`。

#### 易错点

| 错法 | 正确做法 |
| --- | --- |
| `f = open(...); ...; f.close()` 中间可能抛错 | 一律 `with open(...) as f:` |
| 忘记 `encoding="utf-8"` | 文本模式显式写 encoding（跨平台更稳） |
| 在 `with` 外继续用 `f` | 句柄已关；需要内容就先读进变量再离开块 |

#### JS 对照

Node 里常见 `fs.promises` + `try/finally`，或 `using`（较新的显式资源管理提案）。Python 的 `with open` 是更早、更统一的语言级答案。

---

### 2.4 多个上下文

#### 为什么需要「一次管多个」？

读写两个文件、同时拿锁又开连接——你会想把多个边界叠在一起。Python 允许在一个 `with` 里并列多个管理器。

#### 怎么写 / 跑一下

```python
with open("a.txt", encoding="utf-8") as fa, open("b.txt", encoding="utf-8") as fb:
    text_a = fa.read()
    text_b = fb.read()
print(len(text_a), len(text_b))
```

也可以嵌套（语义等价，有时更清晰）：

```python
with open("a.txt", encoding="utf-8") as fa:
    with open("b.txt", encoding="utf-8") as fb:
        ...
```

Python 3.10+ 也常见用括号把多行 `with` 写清楚：

```python
with (
    open("a.txt", encoding="utf-8") as fa,
    open("b.txt", encoding="utf-8") as fb,
):
    ...
```

退出顺序：**后进先出**（先打开的后关闭）——和嵌套 `with` 一致。

#### 易错点

- 并列写法里，如果第二个 `__enter__` 失败，第一个已经成功进入的管理器仍会正确 `__exit__`
- 不要为了「好看」把无关资源硬塞进同一个 `with`；相关边界才并列

#### JS 对照

JS 没有并列 `with` 语法；通常是嵌套 `try/finally`，或把清理函数推进一个栈里统一弹出——这正是后面 `ExitStack` 的思路。

---

## 3. 必掌握：资源管理思维

### 3.1 把「资源」理解宽一点

#### 为什么不能只想到文件？

文件句柄只是最直观的一种。Agent 代码里真正要「进得去、出得来」的，往往是连接、锁、临时配置、观测 span——它们都适用同一套思维。

#### 怎么写（分类表）

| 类型 | 例子 | 进入时 | 退出时 |
|------|------|--------|--------|
| OS 资源 | 文件、socket | 打开 | 关闭 |
| 连接 | DB、HTTP client | connect | close/aclose |
| 并发 | Lock | acquire | release |
| 状态 | 临时改 `cwd` / env / dict | 修改 | 恢复 |
| 观测 | timer / span | start | stop & log |

原则口诀：

> **谁获取，谁负责释放；用 `with` 把释放钉死在作用域上。**

#### 跑一下（锁的直觉）

```python
from threading import Lock

lock = Lock()

with lock:
    # 临界区：同一时刻只有一个线程能进来
    print("critical section")
# 离开 with 自动 release；异常也会 release
```

#### 易错点

1. **作用域资源 vs 应用级单例**  
   请求里打开的临时文件 → 适合 `with`。  
   全局复用的连接池 / 客户端 → 不一定每次请求都 create+close；生命周期跟应用绑定。

2. **和装饰器职责混淆**  
   - 装饰器：增强**函数**（每次调用前后）  
   - 上下文：增强**代码块 / 作用域**（一段代码的进出）

#### JS 对照

| 场景 | JS 常见写法 | Python |
| --- | --- | --- |
| 关文件/流 | `try/finally` 或 `stream.destroy()` | `with open` |
| 互斥 | 库提供的 mutex + `try/finally` | `with lock` |
| 临时改配置 | 自己存旧值，`finally` 还原 | `@contextmanager` / 自定义类 |

---

### 3.2 异常安全：为什么 `with` 比手工 `close` 更稳

#### 为什么这一点特别重要？

Agent 工具调用经常失败：网络超时、JSON 解析失败、权限错误。失败路径比成功路径更容易漏掉清理。

#### 怎么写 / 跑一下

对比两种写法：

```python
# ❌ 危险：write 抛错时 close 可能跑不到
def bad_write(path: str, text: str) -> None:
    f = open(path, "w", encoding="utf-8")
    f.write(text)
    f.close()


# ✅ 安全：任何离开方式都会关
def good_write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
```

用「故意抛错」验证清理仍发生（自定义管理器更直观）：

```python
class Flag:
    def __init__(self) -> None:
        self.cleaned = False

    def __enter__(self) -> "Flag":
        return self

    def __exit__(self, *_) -> None:
        self.cleaned = True


flag = Flag()
try:
    with flag:
        raise RuntimeError("boom")
except RuntimeError:
    pass

print(flag.cleaned)  # True
```

#### 易错点

- 「我在函数末尾写了 `close`」≠ 异常安全；中间 `return` / `raise` 都会跳过
- 不要用裸 `except:` 把清理和业务错误搅在一起；清理交给协议，业务异常继续抛

#### JS 对照

```javascript
let cleaned = false
try {
  throw new Error("boom")
} finally {
  cleaned = true  // 一定执行
}
```

Python 的 `with` 就是把这段 `finally` **标准化**进对象协议。

---

## 4. 必掌握：`contextlib` 快速写法

大多数时候，用生成器写上下文管理器比手写类更短。这一节是「必掌握」里写代码最多的部分。

### 4.1 `@contextmanager`

#### 为什么需要生成器写法？

手写类要定义 `__enter__` / `__exit__` 两套方法，状态还要挂在 `self` 上。很多场景其实只是：

```text
setup
把资源交给 with 块
cleanup
```

生成器的 `yield` 天然把函数劈成「前半 / 后半」——正好对应进入 / 退出。

#### 怎么写

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
```

结构口诀（请背下）：

```text
setup
try:
    yield 资源或 None
finally:
    cleanup
```

- `yield` 之前：相当于 `__enter__`
- `yield` 出去的值：成为 `as` 后面的变量
- `yield` 之后（通常放在 `finally`）：相当于 `__exit__`

#### 跑一下

```python
with timed("llm_call"):
    time.sleep(0.01)
    # 业务代码

# 异常路径：耗时仍会打印，异常继续抛出
try:
    with timed("broken"):
        time.sleep(0.01)
        raise ValueError("oops")
except ValueError as e:
    print("caught:", e)
```

`yield` 带返回值：

```python
@contextmanager
def open_text(path: str, mode: str = "r"):
    f = open(path, mode, encoding="utf-8")
    try:
        yield f
    finally:
        f.close()


with open_text("notes.txt", "w") as f:
    f.write("via generator\n")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `yield` 后忘记包在 `try/finally` | 异常离开时清理可能被跳过 |
| `yield` 两次 | `@contextmanager` 要求恰好 yield 一次 |
| 在 `yield` 前就做完「使用资源」 | 业务应写在 `with` 块里，不要写在生成器后半段当业务 |
| 在 `finally` 里 `return True` 想吞异常 | 生成器版吞异常要用别的机制；别在 cleanup 里乱 return |

再强调一句：

> `@contextmanager` 忘记 `try/finally`，是本章最高频的坑。

#### JS 对照

没有直接等价的 `@contextmanager`。最接近的心智是「把准备和清理写成一对函数，再用高阶函数包住一段回调」：

```javascript
function withTimed(label, fn) {
  const start = performance.now()
  try {
    return fn()
  } finally {
    console.log(`${label}: ${(performance.now() - start).toFixed(1)}ms`)
  }
}

withTimed("llm_call", () => {
  // 业务
})
```

Python 的 `with timed(...):` 让业务代码不用塞进回调，可读性更好。

---

### 4.2 `closing` / `suppress`（认得即可）

#### 为什么库里还要这些小工具？

有些对象只有 `close()`，却没实现上下文协议；有些异常你**明确想忽略**（例如「文件本来就不存在」）。`contextlib` 给了两个常用补丁。

#### 怎么写 / 跑一下

```python
from contextlib import closing, suppress
from pathlib import Path
from urllib.request import urlopen

# closing：给只有 close()、没有上下文协议的对象临时补上
# with closing(urlopen("https://example.com")) as page:
#     data = page.read()

# suppress：有选择地忽略某些异常（慎用）
with suppress(FileNotFoundError):
    Path("maybe.txt").unlink()

print("ok even if file missing")
```

#### 易错点

- `suppress` **不要**拿来当「万能吞异常」；只用于真正可忽略的情况
- 调试阶段乱用 `suppress(Exception)` 会让问题「消失」
- `closing` 只调用 `.close()`；若对象清理方法叫 `aclose` / `shutdown`，就不适用

#### JS 对照

| Python | JS 近似 |
| --- | --- |
| `suppress(FileNotFoundError)` | `try { ... } catch (e) { if (!(e.code === 'ENOENT')) throw e }` |
| `closing(obj)` | `try { use(obj) } finally { obj.close() }` |

---

### 4.3 `ExitStack`（了解有这个工具）

#### 为什么需要动态栈？

`with a, b, c` 适合**编译期就知道数量**的情况。若要在循环里打开 N 个文件、或按条件决定要不要进入某个上下文，就需要一个「可运行时 push 的清理栈」。

#### 怎么写（认形状即可）

```python
from contextlib import ExitStack
from pathlib import Path


def read_all(paths: list[str]) -> list[str]:
    contents: list[str] = []
    with ExitStack() as stack:
        files = [stack.enter_context(Path(p).open(encoding="utf-8")) for p in paths]
        for f in files:
            contents.append(f.read())
    # 离开 with 时，栈里所有上下文按 LIFO 清理
    return contents
```

本阶段先知道名字与用途；真遇到「动态多个 with」再查文档深挖。

#### 易错点

- 不要用 `ExitStack` 炫技替代普通 `with`；静态两个资源用并列 `with` 更清晰
- `enter_context` 失败时，已成功进入的仍会被栈清理——这正是它存在的理由

#### JS 对照

近似于「把 dispose 函数推进数组，在 `finally` 里倒序执行」——很多手动资源管理代码都在重复发明 `ExitStack`。

---

## 5. 建议掌握：自定义类上下文管理器

当逻辑更复杂、需要面向对象状态、或要在退出后继续读属性时，手写类往往更清晰。

### 5.1 最小完整模板：`Timer`

#### 为什么有了 `@contextmanager` 还要写类？

1. 退出后还要读 `elapsed_ms` 等状态 → 类实例更自然  
2. 需要继承 / 多态 / 多个方法协作 → 类更合适  
3. 读框架源码时，大量管理器就是类

#### 怎么写

```python
import time


class Timer:
    def __init__(self, label: str) -> None:
        self.label = label
        self.elapsed_ms = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self  # as 拿到的是 Timer 自己

    def __exit__(self, exc_type, exc, tb) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        print(f"{self.label}: {self.elapsed_ms:.1f}ms")
        # 返回 None/False：不吞异常
        # 返回 True：吞掉异常（通常不建议）
        return None
```

#### 跑一下

```python
with Timer("work") as t:
    time.sleep(0.01)

print("recorded:", t.elapsed_ms)  # with 结束后仍可读取
```

异常路径：

```python
try:
    with Timer("broken") as t:
        time.sleep(0.01)
        raise RuntimeError("fail")
except RuntimeError:
    print("still recorded:", t.elapsed_ms)  # 仍然有值
```

#### 易错点

- 忘记 `return self`（或返回资源）→ `as` 得到 `None`
- 在 `__exit__` 里默认 `return True` → 异常被静默吞掉，极难查
- `__enter__` 里获取失败却留下半初始化状态 → 清理逻辑要能容忍「没获取成功」

#### JS 对照

```javascript
class Timer {
  constructor(label) {
    this.label = label
    this.elapsedMs = 0
  }
  run(fn) {
    const start = performance.now()
    try {
      return fn(this)
    } finally {
      this.elapsedMs = performance.now() - start
      console.log(`${this.label}: ${this.elapsedMs.toFixed(1)}ms`)
    }
  }
}

const t = new Timer("work")
t.run(() => { /* 业务 */ })
console.log(t.elapsedMs)
```

Python 用协议把 `run(fn)` 变成语法级的 `with Timer() as t:`。

---

### 5.2 `__exit__` 的三个参数与返回值

#### 为什么必须搞懂这三个参数？

清理时你常常想知道：「是正常结束，还是炸了？」例如会话要记 `success` / `error`；数据库要决定 commit 还是 rollback。

#### 怎么写

```python
def __exit__(self, exc_type, exc, tb):
    ...
```

| 情况 | `exc_type` | `exc` | `tb` |
|------|------------|-------|------|
| 块内正常结束 | `None` | `None` | `None` |
| 块内异常 | 异常类型 | 异常实例 | traceback |

返回值语义：

| 返回值 | 含义 |
|--------|------|
| `False` / `None` | 异常继续向外抛（**默认、推荐**） |
| `True` | 「我已处理」，异常被吞掉 |

#### 跑一下

```python
class SwallowValueError:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is ValueError:
            print("swallowed:", exc)
            return True  # 只吞 ValueError
        return False


with SwallowValueError():
    raise ValueError("soft fail")

print("continues")  # 会执行到这里

try:
    with SwallowValueError():
        raise TypeError("hard fail")
except TypeError as e:
    print("re-raised:", e)
```

#### 易错点 / 口诀

> 学习阶段：**默认不吞异常**；清理放「一定会跑」的逻辑里完成即可。

- 乱返回 `True`：调试时问题会「消失」
- `__exit__` 里再抛新异常：可能掩盖原异常（Python 3 有异常链，但仍要小心日志与排查）
- 需要区分成功/失败时，看 `exc_type is None`，而不是靠猜

#### JS 对照

```javascript
try {
  // BODY
} catch (e) {
  if (e instanceof ValueErrorLike) {
    // 相当于 return True：处理掉
    return
  }
  throw e  // 相当于 return False
} finally {
  // 清理：无论是否 catch 都可做
}
```

Python 把「清理 + 是否吞异常」收进同一个 `__exit__`。

---

### 5.3 半初始化与清理容忍度

#### 为什么 `__enter__` 失败很危险？

若你在 `__enter__` 里打开了 A，再打开 B 时失败——A 可能已经占用。协议保证：**只有 `__enter__` 成功返回后**，才会在离开时调 `__exit__`。所以复杂获取要自己处理好回滚。

#### 怎么写 / 跑一下（思路）

```python
class TwoFiles:
    def __init__(self, a: str, b: str) -> None:
        self.a_path, self.b_path = a, b
        self.fa = None
        self.fb = None

    def __enter__(self) -> "TwoFiles":
        self.fa = open(self.a_path, encoding="utf-8")
        try:
            self.fb = open(self.b_path, encoding="utf-8")
        except Exception:
            self.fa.close()
            self.fa = None
            raise
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.fb is not None:
            self.fb.close()
        if self.fa is not None:
            self.fa.close()
        return None
```

实际项目里更常直接用并列 `with` 或 `ExitStack`，避免自己编排回滚；但「清理要容忍半初始化」这个意识必须有。

#### 易错点

- 在 `__exit__` 里对可能为 `None` 的句柄直接 `.close()` → 二次异常掩盖原异常
- 获取失败仍假设「已经打开」→ 资源泄漏

#### JS 对照

和手动 `try { openA; openB } catch { closeA }` 同一类问题；Python 协议帮你管「成功进入之后」的离开，**进入过程中的回滚仍要自己写对**。

---

## 6. 综合小例子：会话作用域 + 临时状态

把前面协议、`@contextmanager`、异常路径揉进 Agent 常见模式。

### 6.1 Agent 会话计时与收尾

#### 为什么需要「会话作用域」？

一次 Agent 运行通常有明确边界：开始 → 调工具 / 调 LLM → 成功或失败结束。你希望：

- 进会话时创建状态对象
- 块内随时 `log`
- 离开时无论成败都记耗时、flush 事件

这正是上下文管理器的主场。

#### 怎么写

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
```

#### 跑一下

```python
with agent_session("demo") as s:
    s.log("tool:search")
    s.log("llm:complete")
# 打印类似：['start', 'tool:search', 'llm:complete', 'success', 'end:0.xms']
```

失败路径：

```python
try:
    with agent_session("demo-fail") as s:
        s.log("tool:search")
        raise RuntimeError("llm timeout")
except RuntimeError:
    pass
# events 里应有 start / tool:search / error / end:... ，且没有 success
```

#### 易错点

- `except` 里忘了 `raise` → 错误被吞，调用方以为成功
- 把「业务成功日志」写在 `finally` → 失败也会被标成 success；成功标记应放在 `yield` 之后、`except` 之外
- 在 `finally` 里再抛错 → 可能掩盖会话内原始异常

#### JS 对照

```javascript
async function withAgentSession(name, fn) {
  const events = ["start"]
  const start = performance.now()
  try {
    const session = { name, log: (e) => events.push(e) }
    await fn(session)
    events.push("success")
  } catch (e) {
    events.push("error")
    throw e
  } finally {
    events.push(`end:${(performance.now() - start).toFixed(1)}ms`)
    console.log(events)
  }
}
```

Python 用 `yield session` 避免把整段业务塞进回调。

---

### 6.2 临时改字典配置（用完恢复）

#### 为什么测试和 Agent 都爱这个模式？

你想临时把 `temperature` 调成 `0` 跑一次确定性输出，或临时注入 `debug=True`，但**绝不能污染**全局/外层配置。上下文管理器保证「改得进去、回得来」。

#### 怎么写

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
```

#### 跑一下

```python
config = {"model": "small", "temperature": 0.7}

with temporary_set(config, "temperature", 0):
    print("inside:", config["temperature"])  # 0
print("outside:", config["temperature"])     # 0.7

with temporary_set(config, "top_p", 0.9):
    print("inside top_p:", config["top_p"])  # 0.9
print("has top_p?", "top_p" in config)       # False
```

异常也必须恢复：

```python
config = {"temperature": 0.7}
try:
    with temporary_set(config, "temperature", 0):
        raise RuntimeError("boom")
except RuntimeError:
    pass
print(config["temperature"])  # 0.7
```

#### 易错点

| 错法 | 后果 |
| --- | --- |
| 退出时无脑 `mapping[key] = old` | 原先没有的 key 会留下一个 `None` |
| 不用 `finally` | 异常路径污染配置，后续测试全绿/全红都很怪 |
| 改的是可变对象内部字段却只恢复引用 | 深拷贝/浅恢复要分清；本例只覆盖「顶层 key」 |

这种模式在测试里特别常见；生产里改 `os.environ`、临时切工作目录，也是同一套路。

#### JS 对照

```javascript
function withTemporarySet(mapping, key, value, fn) {
  const missing = !(key in mapping)
  const old = mapping[key]
  mapping[key] = value
  try {
    return fn()
  } finally {
    if (missing) delete mapping[key]
    else mapping[key] = old
  }
}
```

---

### 6.3 再补一个：临时改当前工作目录（认模式）

#### 为什么还要这个例子？

和「临时改 dict」同类：改的是进程级状态，用完必须恢复，否则后续相对路径全乱。

#### 怎么写 / 跑一下

```python
from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def temporary_cwd(path: str | Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield Path.cwd()
    finally:
        os.chdir(prev)


# with temporary_cwd("/tmp"):
#     ...
```

#### 易错点

- 多线程程序里改进程级 `cwd` 本身就不安全；这类管理器适合单线程脚本/测试
- 恢复失败（目录被删）会在 `finally` 再抛错——注意日志

#### JS 对照

Node 同样不推荐在并发里乱改 `process.chdir`；模式仍是「存旧值 → `try` → `finally` 还原」。

---

## 7. 了解即可：异步上下文管理器

异步世界里，获取/释放常常是 `await` 的（连接池、HTTP 客户端、异步 DB）。同步的 `__enter__` / `__exit__` 不够用，于是有异步协议。

### 7.1 `async with` 长什么样

#### 为什么需要异步版？

```python
# 同步
with open(path) as f:
    ...

# 异步：进入/退出本身可能要 await
async with http_client as client:
    resp = await client.get(url)
```

若只用同步 `with` 去管异步客户端，容易在事件循环里阻塞，或漏掉 `aclose()`。

#### 怎么写（认形状）

对应协议：

```text
__aenter__ / __aexit__
```

类写法示意：

```python
class AsyncTimer:
    async def __aenter__(self):
        # 可能 await 某些初始化
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # 可能 await 关闭
        return None


# async with AsyncTimer() as t:
#     ...
```

生成器快捷写法：

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def agent_span(name: str):
    print("start", name)
    try:
        yield {"name": name}
    finally:
        print("end", name)


# async with agent_span("llm"):
#     await call_llm(...)
```

#### 跑一下（现在可以不跑）

本阶段**建立印象即可**：看到 `async with` 就知道是「异步版 with」。HTTPX、数据库异步驱动、很多 LLM SDK 都会用到。等模块 05（异步）再实战。

#### 易错点（先记两条）

- 异步管理器要用 `async with`，不要写成普通 `with`（除非对象同时提供同步协议）
- `@asynccontextmanager` 里同样要 `try/finally`，口诀与同步版相同

#### JS 对照

```javascript
// JS 里常见：await 获取，finally 里 await 释放
const client = await createClient()
try {
  await client.get(url)
} finally {
  await client.close()
}
```

Python 把这对操作收成 `async with`。

---

## 8. 常见坑（全章对照表）

把前面易错点收成一张「出门前核对」表：

| # | 坑 | 正确习惯 |
|---|----|----------|
| 1 | 在 `__enter__` 失败时仍假设资源已获取 | 获取失败就回滚；清理容忍半初始化 |
| 2 | `__exit__` 里再抛新异常，掩盖原异常 | 清理失败先打日志；慎抛 |
| 3 | 乱返回 `True` 吞异常 | 默认 `False`/`None`；吞异常要有充分理由 |
| 4 | `@contextmanager` 忘记 `try/finally` | `yield` 必须落在 `try`，清理进 `finally` |
| 5 | 把应用级单例每次都 `with` 掉 | 分清「作用域资源」与「进程级生命周期」 |
| 6 | 和装饰器职责混淆 | 装饰器增强函数；上下文增强代码块 |
| 7 | `with` 外继续用已关闭句柄 | 需要的数据先读出再离开块 |
| 8 | `suppress` 当万能 `catch` | 只忽略明确可忽略的异常类型 |

---

## 9. 练习指引

请打开并完成：

[`exercises/02-advanced-python/05-context-manager.md`](../../exercises/02-advanced-python/05-context-manager.md)

建议代码位置：

```text
playground/02-advanced-python/05-context-manager/
```

建议动手顺序：

1. 文件 `with` + 故意抛错，确认清理发生  
2. `@contextmanager` 计时器（含异常路径）  
3. `temporary_set`  
4. 手写最小类 / 类版 `Timer`  
5. 有余力再碰 `ExitStack` 或异步认形状

---

## 10. 小结与下一站

### 心智模型

```text
with 资源 as x:
    使用 x

进入 → __enter__（或 generator yield 前）
离开 → __exit__（或 yield 后 finally）
异常也会离开 → 所以清理更可靠

装饰器：包装「调用」
上下文：包装「作用域」
```

### 和 JS `try/finally` 的最终对照

| 你在 JS 里做的事 | Python 对应 |
| --- | --- |
| `try { ... } finally { close() }` | `with` 协议 |
| 把 close 写成重复样板 | `@contextmanager` / 自定义类复用 |
| 回调式 `withResource(fn)` | `with mgr:` 块（不必塞回调） |
| `await acquire` + `await release` | `async with` / `__aenter__` / `__aexit__` |

### 自检清单

- [ ] 能解释为何 `with open` 比手工 `close` 更安全
- [ ] 能用 `@contextmanager` 写计时或临时改配置
- [ ] 知道 `__exit__` 三参数与「别随便吞异常」
- [ ] 能手写基于类的 `__enter__` / `__exit__`
- [ ] 看到 `async with` 知道是异步版协议
- [ ] 独立完成练习基础题

### 下一章

[`06-exception-system.md`](./06-exception-system.md) —— 异常系统：如何设计错误、传播错误、在 Agent 工具调用里优雅失败。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[装饰器](./04-decorator.md)
- 下一章：[异常系统](./06-exception-system.md)
