# asyncio 基础

> 所属模块：`05-async-python` · Python 异步编程  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（有 JS `async/await` / `Promise` 经验可更快；事件循环让出与 `time.sleep` 卡循环建议亲手踩一遍）  
> 约定：Python ≥ 3.11（`TimeoutError` 与内置同名、注解用 `list[str]` / `str | None`）  
> 对应练习：[`exercises/05-async-python/01-asyncio-fundamentals.md`](../../exercises/05-async-python/01-asyncio-fundamentals.md)

## 本章定位

- **模块目标**：掌握 asyncio，跨过 Agent 开发分水岭。
- **本章角色**：把 `async/await`、事件循环、Task、`gather`、超时与取消练熟，能把多个 I/O 等待重叠起来。
- **前置**：模块 04 的并发模型（并发 vs 并行、GIL、为何 I/O 适合异步）。本章不再重讲选型地图，只把「异步这一条路」写透。
- **你的优势**：若熟悉 JS/TS 的 `async/await` 与 `Promise.all`，多数心智可对照迁移；重点盯住「`await` 让出」「别用 `time.sleep` 卡循环」「Coroutine vs Task」。
- **刻意不做**：限流（`Semaphore`）、异步 HTTP 客户端、`TaskGroup` 生产模式——留给下一章。

## 学习目标（学完应能做到）

1. 正确编写并运行 `async def` / `await` / `asyncio.run` 代码。
2. 说清协程、Task、事件循环的关系，以及「`await` 如何让出控制权」。
3. 用 `asyncio.create_task` 与 `asyncio.gather` 并发等待多个 I/O 任务，并用计时证明重叠收益。
4. 会做基础超时（`wait_for`）与取消（`task.cancel`），知道 `TimeoutError` / `CancelledError` 各自出现在哪一层。
5. 完成课后练习，并分清哪些是「必掌握」、哪些可以先跳过。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | `async`/`await`、事件循环心智模型、Coroutine vs Task、`gather` | 能写并发 I/O，能解释让出 |
| **建议掌握** | 超时与取消 | 能避免无限挂起，能安全清理 |
| **了解即可** | 事件循环实现细节（selector / proactor） | 建立地图，不深挖 |

---

## 1. 为什么要学（Agent 分水岭）

#### 为什么异步是 Agent 的分水岭？

Agent 一步里常常要同时等好几件「网络活」：

```text
search()    等 800ms
browse()    等 1200ms
embed()     等 500ms
```

串行等待（即使写成 `await`，也是一个完再等下一个）：

```text
await search   0.8s
await browse   1.2s
await embed    0.5s
合计 ≈ 2.5s
```

并发等待（先调度再一起等）：

```text
同时等 search + browse + embed
合计 ≈ 1.2s（约等于最慢那个）
```

工具并行、批量 embedding、多路检索，全靠这一能力。  
FastAPI 路由、许多 LLM SDK 也默认异步友好。不会重叠 I/O，后面 Agent 延迟很难做上去。

#### 怎么理解本章要解决的问题

模块 04 已经告诉你：asyncio 适合**大量网络 I/O**。本章回答的是更具体的四件事：

1. 代码怎么写（`async def` / `await` / `asyncio.run`）？
2. 运行时怎么调度（事件循环、`await` 让出）？
3. 怎样真正并发（Task / `gather`），而不是「看起来像异步、其实还是串行」？
4. 慢调用挂起时怎么超时、怎么取消？

可以先记一句：

> **异步的核心不是「把函数写成 `async`」，而是「在等待 I/O 时把控制权交回去，让别的任务推进」。**

#### 跑一下（同步串行的「慢」长什么样）

先不用 asyncio，感受串行加法：

```python
import time


def fake_io(name: str, sec: float) -> str:
    time.sleep(sec)  # 假装网络等待
    return name


def sequential() -> list[str]:
    return [fake_io("search", 0.2), fake_io("browse", 0.2)]


t0 = time.perf_counter()
print(sequential())
print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")
# 大约 0.4s：两个 0.2 相加
```

期望输出大致是：

```text
['search', 'browse']
elapsed ≈ 0.4 s
```

本章后面会用 `asyncio.sleep` + `gather` 把同样两个 0.2s 压到约 0.2s。  
现在只要记住：**串行 I/O 的时间是相加的；能重叠就接近取 max。**

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 以为「函数写成了 `async` 就会自动并发」 | 若只是依次 `await`，时间仍是加法 |
| 以为 `await` = 多线程 / 多核加速 | `await` 是协作式让出；默认仍在单线程事件循环里 |
| 一上来就抄 `gather`，不懂让出 | 中间夹了 `time.sleep` / 同步 `requests`，循环被卡死，并发失效 |

#### JS Promise / async-await 对照

前端里你已经见过同类问题：

```javascript
// 串行：约 400ms
await fetchA()
await fetchB()

// 并发：约 200ms
await Promise.all([fetchA(), fetchB()])
```

| JavaScript | Python（本章） |
|------------|----------------|
| `async function` | `async def` |
| `await promise` | `await awaitable` |
| `Promise.all([...])` | `asyncio.gather(...)` |
| 主线程事件循环 | asyncio 事件循环 |
| 同步死循环卡页面 | `time.sleep` / 同步 I/O 卡事件循环 |

差异要盯住：JS 里「忘记 `await`」常得到未 settled 的 Promise；Python 里「忘记 `await`」常得到**从未被调度的协程对象**，还会冒 RuntimeWarning。

---

## 2. 必掌握：async / await

这一节会刻意写细——后面所有 Task、`gather`、超时，都建立在「协程函数 + await」上。

### 2.1 最小例子：协程函数长什么样

#### 为什么需要 `async def`？

普通函数一旦开始跑，就会一路跑到 `return`（或抛错）。  
异步函数需要在「等 I/O」的地方**暂停自己、把控制权交出去**——语言用 `async def` 标记「这是可被挂起的函数」。

#### 怎么写

```python
import asyncio


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)  # 非阻塞等待
    return f"hello {name}"


async def main() -> None:
    result = await say("agent", 0.1)
    print(result)


asyncio.run(main())
```

三件套：

1. `async def`：定义**协程函数**
2. `await`：等待一个 awaitable（协程 / Task / Future 等）
3. `asyncio.run(...)`：脚本入口，负责创建事件循环、跑完入口协程、收尾

#### 跑一下

把上面代码存成脚本执行，期望输出：

```text
hello agent
```

计时版（看清「单次 await」本身并不神奇）：

```python
import asyncio
import time


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"hello {name}"


async def main() -> None:
    t0 = time.perf_counter()
    print(await say("agent", 0.2))
    print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")


asyncio.run(main())
# elapsed ≈ 0.2 s
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 以为调用 `say(...)` 就会立刻执行完 | 调用协程函数只得到协程对象，必须 `await` 或包成 Task |
| 在模块顶层直接 `await say(...)` | 语法错误（除非特殊 REPL / 顶层 await 环境） |
| 忘记用 `asyncio.run` 包入口 | 协程创建了但没有事件循环去跑 |

#### JS 对照

```javascript
async function say(name, delay) {
  await new Promise((r) => setTimeout(r, delay * 1000))
  return `hello ${name}`
}

async function main() {
  console.log(await say("agent", 0.1))
}

main()
```

| JavaScript | Python |
|------------|--------|
| `async function say()` | `async def say()` |
| 调用 `say()` → Promise | 调用 `say()` → 协程对象 |
| 用 `await` / `.then` 消费 | 用 `await` / Task / `gather` 消费 |
| 浏览器/Node 已有循环 | 脚本里常用 `asyncio.run` 显式启动 |

---

### 2.2 调用 `async def` 得到什么？

#### 为什么这一点必须钉死？

这是新手第一坑，也是「看起来写了异步、其实什么都没跑」的根源。

#### 怎么写（先看类型）

```python
import asyncio


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"hello {name}"


coro = say("a", 0.1)
print(type(coro))   # <class 'coroutine'>
print(coro)         # <coroutine object say at 0x...>
# 到这里：函数体几乎还没开始跑（至少你不能当它已经 return 了）
```

正确消费方式（任选其一，后面几节会展开）：

```python
# 1) 直接 await（在另一个协程里）
result = await say("a", 0.1)

# 2) 包成 Task，交给事件循环调度
task = asyncio.create_task(say("a", 0.1))
result = await task

# 3) 交给 gather 一起等
results = await asyncio.gather(say("a", 0.1), say("b", 0.1))
```

口诀：

> **`async def` 是「工厂」；调用它得到「协程对象」；只有被 await / 调度后才会真正推进。**

#### 跑一下（忘记 await 的警告）

```python
import asyncio
import warnings


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"hello {name}"


async def bad() -> None:
    say("x", 0.1)  # 只创建了协程，没调度
    print("done?")


asyncio.run(bad())
# 常见：RuntimeWarning: coroutine 'say' was never awaited
```

期望现象：打印了 `done?`，但 `say` 的业务逻辑没真正跑完；进程结束前常出现 never awaited 警告。

#### 易错点

| 错法 | 纠正 |
|------|------|
| `result = say("x", 0.1)` 然后当字符串用 | `result` 是协程对象，不是返回值 |
| 「警告可以忽略」 | 通常表示逻辑根本没执行 |
| 把协程对象存进列表却从不 await | 和「创建了 Promise 却从不 then/await」同类事故 |

#### JS 对照

```javascript
const p = say("x", 0.1)   // Promise，同样「还没等到结果」
// 必须 await p 或 p.then(...)
```

Python 比 JS 更「吵」一点：未 await 的协程常直接 RuntimeWarning，这是好事。

---

### 2.3 `await` 到底在等什么？

#### 为什么要单独讲 `await`？

很多人把 `await` 理解成「睡眠」或「开线程」。更准确的说法是：

> **在当前协程里暂停，直到这个 awaitable 完成；暂停期间事件循环可以去推进其它就绪任务。**

#### 怎么写

`await` 右边必须是 awaitable，常见三类：

| 类型 | 例子 | 说明 |
|------|------|------|
| 协程对象 | `say("a", 0.1)` | 最常见 |
| Task | `asyncio.create_task(...)` | 已被调度的并发单元 |
| 其它 Future/awaitable | 库返回的对象 | 先会用，细节可后补 |

```python
async def main() -> None:
    # await 协程
    a = await say("a", 0.1)

    # await Task（等价于等它完成并取结果）
    t = asyncio.create_task(say("b", 0.1))
    b = await t

    print(a, b)
```

#### 跑一下（串行两个 await）

```python
import asyncio
import time


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name


async def main() -> None:
    t0 = time.perf_counter()
    a = await say("a", 0.2)
    b = await say("b", 0.2)
    print(a, b)
    print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")
    # ≈ 0.4s：仍然是串行相加！


asyncio.run(main())
```

结论要早点建立：

> **`await` 本身不制造并发。**  
> 并发来自「多个 Task 已被调度，且在各自 await 时把控制权交回去」。

#### 易错点

| 错法 | 纠正 |
|------|------|
| 「我写了 await，所以一定比同步快」 | 单线程串行 await 并不更快 |
| 在普通 `def` 里写 `await` | 语法不允许 |
| `await` 一个普通返回值（如 `int`） | TypeError：object can't be awaited |

#### JS 对照

```javascript
// 一样：两个 await 串行，总时间相加
const a = await say("a", 0.2)
const b = await say("b", 0.2)
```

`await` 在两边都是「等完成」；并发要靠 `Promise.all` / `gather` / 先启动再一起等。

---

### 2.4 入口：`asyncio.run`

#### 为什么需要入口函数？

协程要跑起来，需要事件循环。现代脚本最省心的方式是：

```python
asyncio.run(main())
```

它大致负责：创建循环 → 跑入口协程直到完成 → 清理挂起任务 → 关闭循环。

#### 怎么写

推荐结构：

```python
import asyncio


async def main() -> None:
    print(await say("agent", 0.05))


if __name__ == "__main__":
    asyncio.run(main())
```

要点：

- 业务逻辑放进 `async def main`（或其它协程）
- 进程入口只调用一次 `asyncio.run`
- 已经在跑的循环里，**不要**再套一层 `asyncio.run`（常见于 Jupyter / 框架内部）

#### 跑一下

```python
import asyncio


async def main() -> None:
    print("inside main")


asyncio.run(main())
print("after run")
```

期望输出：

```text
inside main
after run
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 在协程内部再 `asyncio.run(...)` | 抛错：不能嵌套 |
| 同一线程反复 `asyncio.run` 开很多循环却不理解生命周期 | 脚本场景通常没事；长期服务应使用框架提供的循环 |
| 把 `asyncio.run(say(...))` 到处乱调 | 每次都新建/关闭循环，难组合；应在一个 `main` 里组织 |

#### JS 对照

浏览器/Node 里通常没有「手写 `asyncio.run`」这一步——宿主已经在跑事件循环。  
Python **脚本**更像「你要自己把循环点着」；FastAPI / 测试框架则常常替你管好循环。

---

### 2.5 千万别混用：语法与调度错误

#### 为什么单独列一节？

这些错误会反复出现；先建立「红灯清单」，后面调试更快。

#### 怎么写（错误 vs 正确）

```python
import asyncio


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"hello {name}"


# ❌ 错误 1：忘记 await
async def bad1() -> None:
    say("x", 0.1)  # 只创建协程


# ❌ 错误 2：在普通函数里直接 await（语法不允许）
# def bad2():
#     await say("x", 0.1)


# ❌ 错误 3：把协程当返回值直接打印「业务结果」
async def bad3() -> None:
    print(say("x", 0.1))  # 打印的是 coroutine 对象


# ✅ 正确
async def good() -> None:
    print(await say("x", 0.1))
```

#### 跑一下（对比 good）

```python
asyncio.run(good())
# hello x
```

#### 易错点

- 「程序没报错就等于异步生效了」——忘记 await 时经常**只警告**，业务静默没跑。  
- 从同步代码「临时」想调异步：不要假装能直接 `await`；脚本入口用 `asyncio.run`，库代码用框架生命周期或明确桥接（进阶话题）。

#### JS 对照

```javascript
// 忘记 await：拿到 Promise，不是结果
const x = say("x", 0.1)
console.log(x)  // Promise { <pending> }

// Python 同类：拿到 coroutine，不是结果
```

---

### 2.6 `asyncio.sleep` vs `time.sleep`（必踩坑）

#### 为什么这是本章最重要的对比之一？

异步代码里最危险的不是「不会写 gather」，而是：

> **在事件循环线程里调用了阻塞函数，把整个循环卡住。**

`time.sleep` 就是最经典的阻塞示范。

#### 怎么写

| | `asyncio.sleep` | `time.sleep` |
|--|-----------------|--------------|
| 效果 | 让出事件循环，其它任务可跑 | **阻塞整个线程**，卡住循环 |
| 异步代码里 | 正确的「假装 I/O 等待」 | 通常错误（除非丢到线程） |
| 类比 JS | `await sleep(ms)` / `setTimeout` | 同步死循环 / 同步 `execSync` 一类卡主线程 |

#### 跑一下（亲眼看并发被卡死）

```python
import asyncio
import time


async def worker(name: str, blocker: str) -> str:
    print(name, "start", blocker)
    if blocker == "asyncio":
        await asyncio.sleep(0.3)
    else:
        time.sleep(0.3)  # 卡住整个事件循环线程
    print(name, "end", blocker)
    return name


async def with_asyncio_sleep() -> None:
    t0 = time.perf_counter()
    await asyncio.gather(
        worker("A", "asyncio"),
        worker("B", "asyncio"),
    )
    print("asyncio.sleep elapsed ≈", round(time.perf_counter() - t0, 3), "s")


async def with_time_sleep() -> None:
    t0 = time.perf_counter()
    await asyncio.gather(
        worker("A", "time"),
        worker("B", "time"),
    )
    print("time.sleep elapsed ≈", round(time.perf_counter() - t0, 3), "s")


print("=== 正确：asyncio.sleep ===")
asyncio.run(with_asyncio_sleep())
print("=== 错误示范：time.sleep ===")
asyncio.run(with_time_sleep())
```

期望现象（大约）：

```text
=== 正确：asyncio.sleep ===
A start asyncio
B start asyncio
A end asyncio
B end asyncio
asyncio.sleep elapsed ≈ 0.3 s

=== 错误示范：time.sleep ===
A start time
A end time
B start time
B end time
time.sleep elapsed ≈ 0.6 s
```

解释：

- `asyncio.sleep`：两个 worker 都能启动，等待重叠，总时间 ≈ 0.3s  
- `time.sleep`：虽然用了 `gather`，但阻塞发生在循环线程上，另一个任务插不进去，总时间回到 ≈ 0.6s

同步 `requests.get`、重 CPU 纯 Python 循环，杀伤力同类。  
下一章会讲 `asyncio.to_thread` 逃生舱；本章先建立肌肉记忆：**异步路径里默认用 `await` 的非阻塞 API。**

#### 易错点

| 错法 | 纠正 |
|------|------|
| 「有 gather 就不会被 sleep 卡住」 | gather 救不了线程级阻塞 |
| 用 `time.sleep`「临时调试」留在代码里 | 调试假等待请用 `await asyncio.sleep` |
| 以为只有 sleep 会卡循环 | 任何长时间占着线程不 await 的代码都会 |

#### JS 对照

```javascript
// 类似：用同步死循环卡主线程，Promise.all 也救不了页面
function sleepSync(ms) {
  const end = Date.now() + ms
  while (Date.now() < end) {}
}
```

JS 里你会避免在主线程做重同步活；Python asyncio 里同理。

---

## 3. 必掌握：事件循环（心智模型）

这一节几乎没有新 API，但决定你会不会「写出 async、想的是多线程」。

### 3.1 把事件循环想成调度员

#### 为什么需要心智模型？

你很少手写 `loop = asyncio.get_event_loop()`（现代代码用 `asyncio.run`）。  
但如果不理解循环在干什么，就解释不清：

- 为什么 `await` 之后别的任务能跑？
- 为什么 CPU 密集代码会「饿死」其它协程？
- 为什么阻塞调用比慢 await 更可怕？

#### 怎么理解

```text
准备好的任务 → 跑到下一个 await
遇到 I/O 等待 → 登记「完成后再续跑」，去跑别的就绪任务
I/O 完成 → 任务重新就绪
```

更短的一句话：

> **事件循环在单线程里轮流推进所有就绪的协程/Task；谁 await 了，谁就让出。**

#### 跑一下（用打印看交错）

```python
import asyncio


async def work(name: str, steps: int) -> None:
    for i in range(steps):
        print(f"{name} step {i}")
        await asyncio.sleep(0)  # 主动让出；0 也表示「下一轮再继续」


async def main() -> None:
    await asyncio.gather(work("A", 3), work("B", 3))


asyncio.run(main())
```

期望输出大致交错（不必比特级相同）：

```text
A step 0
B step 0
A step 1
B step 1
A step 2
B step 2
```

若把 `await asyncio.sleep(0)` 删掉、改成纯计算死循环，另一个任务就很难插进来——这就是协作式调度。

#### 易错点

| 错法 | 纠正 |
|------|------|
| 把事件循环想成「自动时间片抢占」 | 主要在 `await`（或其它让出点）切换 |
| 手写很深的 loop API 才算懂异步 | 应用层先把心智模型用熟 |
| 以为理解了循环就能绕过 GIL 多核跑 Python | 默认仍是单线程协作 |

#### JS 对照

```text
JS：call stack 清空 → 取任务队列 / microtask → 再执行
Python asyncio：就绪 Task 往前跑 → 碰到 await 让出 → 循环调度下一个
```

不必强行一一对应每个队列名字；两边共同点是：**单线程 + 回调/续跑 + 别阻塞。**

---

### 3.2 `await` = 协作式让出

#### 为什么强调「协作式」？

因为这决定了性能与正确性边界：

```text
抢占式（OS 线程）：到点可能被强制切换
协作式（asyncio）：你写到 await（等让出点），才把控制权交还
```

所以：

- `await` 之间的代码，会一直占用当前线程
- 这段代码若又长又重，其它 Task 只能干等
- 它也**不会**因此变成多核并行

#### 怎么理解（时间线）

```text
Task A:  [跑]--await I/O--[挂起]........[继续跑]--done
Task B:           [跑]--await I/O--[挂起]..[继续]--done
Loop :  一直在：推进就绪者 / 等 I/O 完成信号
```

#### 跑一下（await 之间的重计算会占住循环）

```python
import asyncio
import time


async def hungry(name: str) -> None:
    print(name, "cpu start")
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < 0.2:
        _ = 123456789 * 987654321  # 假装重计算（无 await）
    print(name, "cpu end")


async def polite(name: str) -> None:
    print(name, "hi")


async def main() -> None:
    t0 = time.perf_counter()
    await asyncio.gather(hungry("A"), polite("B"))
    print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")


asyncio.run(main())
```

常见现象：`B hi` 可能很晚才出现（取决于调度时机），总时间也接近「重计算本身」的量级。  
结论：

> **asyncio 擅长重叠等待；不擅长在同一个循环线程里硬扛重 CPU。**  
> 重 CPU 请回到模块 04 的进程/离线方案，或下一章的线程逃生舱。

#### 易错点

| 错法 | 纠正 |
|------|------|
| 「都 async 了，CPU 也会自动并行」 | 不会 |
| 「偶尔算一下没关系」 | 短计算 fine；几十上百毫秒级纯 Python 循环会伤延迟 |
| 用更多 `gather` 解决 CPU 瓶颈 | 叠再多 Task 也共用一个循环线程 |

#### JS 对照

主线程里跑很重的 `for`，页面掉帧——和这里同一类问题。  
前端用 Worker；Python 常用多进程 / C 扩展 / 把活移出热路径。

---

### 3.3 和模块 04 的衔接（别混概念）

#### 为什么要回钩一枪？

避免学完本章又把词用乱：

| 概念 | 本章中的位置 |
|------|--------------|
| 并发 | asyncio 正在做的事：交替推进多个未完成 I/O |
| 并行 | 多核同时算；**不是** asyncio 默认能力 |
| GIL | 仍在；异步不靠「开很多 Python 线程」绕过它 |
| 阻塞 I/O | 异步路径上的头号敌人 |

#### 怎么记

```text
Agent 多工具等待  → 要并发（本章 gather/Task）
本地重计算清洗   → 要想并行或预处理（不是堆 async）
同步库短期难改   → 线程池包一层（下一章 to_thread）
```

#### 易错点

把「并发收益」和「多核加速」写成同一句注释——以后排障会误导自己。

#### JS 对照

`Promise.all` 让等待重叠 ≠ Worker 让计算并行。  
Python：`gather` ≠ `ProcessPoolExecutor`。

---

## 4. 必掌握：Coroutine 与 Task

这一节会刻意写细——「会不会并发」常常取决于你有没有把协程提升为 Task。

### 4.1 协程对象：还没开始跑的清单

#### 为什么先强调「对象」？

因为调试时你要对着 `print` / 类型看清楚：手里拿的是「菜谱」还是「已下单的厨房任务」。

#### 怎么写

```python
import asyncio


async def say(name: str, delay: float) -> str:
    print("running", name)
    await asyncio.sleep(delay)
    return name


async def main() -> None:
    coro = say("a", 0.1)      # 协程对象，尚未执行函数体中的 print
    print("created", coro)
    result = await coro       # 现在才真正推进
    print("result", result)


asyncio.run(main())
```

期望输出顺序大致是：

```text
created <coroutine object say at ...>
running a
result a
```

#### 易错点

| 错法 | 纠正 |
|------|------|
| 创建协程后既不 await 也不 create_task | 永不执行 + RuntimeWarning |
| 同一个协程对象 await 两次 | 不行；协程用过即废，需重新调用函数创建 |
| 把「协程函数」和「协程对象」当成同一个词 | 函数可反复调用；每次调用产生新对象 |

#### JS 对照

```javascript
const p = say("a", 0.1)  // 已经开始执行到第一个 await（Promise 语义）
await p
```

注意差异（重要）：

- JS：调用 `async function` 通常**立刻开始执行**到第一个 `await`/`return`
- Python：调用 `async def` 得到协程对象，**一般要等到被调度/await 才进入函数体**

这是前端同学最容易误判的点之一。

---

### 4.2 Task：被调度的并发单元

#### 为什么需要 Task？

只写：

```python
a = await say("a", 0.2)
b = await say("b", 0.2)
```

永远是串行。  
要想「两个都开始等」，需要把它们登记到事件循环里，成为可并发推进的单元——这就是 Task。

#### 怎么写

```python
import asyncio


async def say(name: str, delay: float) -> str:
    print("start", name)
    await asyncio.sleep(delay)
    print("end", name)
    return name


async def main() -> None:
    t1 = asyncio.create_task(say("a", 0.2))
    t2 = asyncio.create_task(say("b", 0.2))
    # create_task：已登记调度；
    # 通常要等当前协程 await 把控制权交回循环后，它们才真正往前跑
    r1 = await t1
    r2 = await t2
    print(r1, r2)


asyncio.run(main())
```

#### 跑一下（看 start 是否都能出现）

期望输出大致是：

```text
start a
start b
end a
end b
a b
```

计时版：

```python
import asyncio
import time


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name


async def sequential() -> list[str]:
    return [await say("a", 0.2), await say("b", 0.2)]


async def with_tasks() -> list[str]:
    t1 = asyncio.create_task(say("a", 0.2))
    t2 = asyncio.create_task(say("b", 0.2))
    return [await t1, await t2]


for label, fn in [("sequential", sequential), ("tasks", with_tasks)]:
    t0 = time.perf_counter()
    print(label, asyncio.run(fn()), "elapsed ≈", round(time.perf_counter() - t0, 3), "s")

# sequential ≈ 0.4s
# tasks      ≈ 0.2s
```

#### 易错点

| 错法 | 纠正 |
|------|------|
| `create_task` 后忘记 await/收集 | 任务可能还在跑，主协程就结束了；`asyncio.run` 收尾时可能警告/取消 |
| 以为 `create_task` 会立刻跑完 | 只是调度；要结果仍需 await |
| 在没有运行中的循环时 `create_task` | 需要已在异步上下文中（通常在协程里调用） |

#### JS 对照

```javascript
// 先启动两个 Promise，再一起等 —— 类似 create_task 后 await
const t1 = say("a", 0.2)  // 已开始
const t2 = say("b", 0.2)
const r1 = await t1
const r2 = await t2
```

| Python | JavaScript 粗对照 |
|--------|-------------------|
| 协程对象（未调度） | （不完全像）「还没调用的 async 函数」 |
| `create_task(coro)` | 先调用得到 Promise，并让它开始跑 |
| `await task` | `await promise` |

---

### 4.3 直觉对照：只 await 协程 vs create_task

#### 为什么需要这张对照表？

这是本章「会不会真并发」的分水岭。

#### 怎么理解

| 写法 | 行为 | 总耗时（两个 0.2s I/O） |
|------|------|-------------------------|
| `await c1` 然后 `await c2` | 基本顺序执行 | ≈ 0.4s |
| 先 `create_task` 两个，再分别 await | 可交错推进 | ≈ 0.2s |
| `await gather(c1, c2)` | 内部会调度它们并发 | ≈ 0.2s |

口诀：

> **裸 await 协程 ≈ 顺序套娃；Task / gather ≈ 先挂上号再一起等。**

#### 跑一下（三种写法并排）

```python
import asyncio
import time


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name


async def only_await() -> list[str]:
    return [await say("a", 0.2), await say("b", 0.2)]


async def tasks() -> list[str]:
    t1 = asyncio.create_task(say("a", 0.2))
    t2 = asyncio.create_task(say("b", 0.2))
    return [await t1, await t2]


async def gather_way() -> list[str]:
    return list(await asyncio.gather(say("a", 0.2), say("b", 0.2)))


async def main() -> None:
    for label, fn in [
        ("only_await", only_await),
        ("tasks", tasks),
        ("gather", gather_way),
    ]:
        t0 = time.perf_counter()
        result = await fn()
        print(label, result, "elapsed ≈", round(time.perf_counter() - t0, 3), "s")


asyncio.run(main())
```

期望：

```text
only_await ['a', 'b'] elapsed ≈ 0.4 s
tasks ['a', 'b'] elapsed ≈ 0.2 s
gather ['a', 'b'] elapsed ≈ 0.2 s
```

#### 易错点

- 把 `gather` 想成「语法糖魔法」——它本质上仍是「调度 + 一起等」。  
- 有依赖时硬并发：`b` 需要 `a` 的结果，就该串行（或先 await a 再启动 b）。

#### JS 对照

```javascript
// only await
await say("a", 0.2); await say("b", 0.2)

// 类似 tasks / gather
await Promise.all([say("a", 0.2), say("b", 0.2)])
```

---

### 4.4 Task 结果、异常与「火后忘记」

#### 为什么还要补这几句？

并发单元一旦启动，异常可能发生在「你还没 await 到它」的时候。

#### 怎么写

```python
import asyncio


async def boom() -> None:
    await asyncio.sleep(0.05)
    raise ValueError("boom")


async def main() -> None:
    t = asyncio.create_task(boom())
    await asyncio.sleep(0.1)  # 此时 t 可能已经失败
    try:
        await t
    except ValueError as e:
        print("caught from task:", e)


asyncio.run(main())
```

原则：

1. 创建的 Task，最终要被 await，或被明确收集/监督  
2. 不要「点火后永久忘记」——未检索异常可能在收尾时以警告形式冒出来  
3. 需要「一组同生共死」时，下一章的 `TaskGroup` 更合适（本章先用 gather/手动 await）

#### 易错点

| 错法 | 纠正 |
|------|------|
| `create_task` 后完全不 await | 结果/异常可能被忽略 |
| 假设异常会立刻打断其它无关 Task | 默认不会；要看你怎么汇合它们 |

#### JS 对照

未处理的 Promise rejection 会吵；Python 未检索的 Task exception 也会在回收时警告。都要养成「谁启动、谁负责收尾」的习惯。

---

## 5. 必掌握：`asyncio.gather`

### 5.1 基本用法：并发等一组，按传入顺序收结果

#### 为什么 `gather` 是 Agent 日常 API？

因为工具并行几乎总是「启动一组，等全部（或策略性）结束，按稳定顺序拿结果」。

#### 怎么写

```python
import asyncio


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name


async def main() -> None:
    results = await asyncio.gather(
        say("a", 0.2),
        say("b", 0.1),
        say("c", 0.3),
    )
    print(results)  # 按传入顺序，不是完成顺序


asyncio.run(main())
```

#### 跑一下（顺序 vs 耗时）

```python
import asyncio
import time


async def say(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name


async def main() -> None:
    t0 = time.perf_counter()
    results = await asyncio.gather(
        say("a", 0.2),
        say("b", 0.1),
        say("c", 0.3),
    )
    print(results)
    print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")
    # results == ['a', 'b', 'c']
    # elapsed ≈ 0.3s（最慢的那个），不是 0.6s


asyncio.run(main())
```

期望输出大致是：

```text
['a', 'b', 'c']
elapsed ≈ 0.3 s
```

注意：`b` 最先完成，但结果列表里仍在索引 1——**按传入顺序**。

#### 易错点

| 错法 | 纠正 |
|------|------|
| 假设 gather 按完成顺序返回 | 默认按传入顺序 |
| 传入已开始的 Task 和裸协程混用时乱了心智 | 都可以；关键是「它们被并发推进」 |
| 空 `gather()` | 合法，返回空列表；但业务上通常没意义 |

#### JS 对照

```javascript
const results = await Promise.all([say("a", 0.2), say("b", 0.1), say("c", 0.3)])
// 同样：按传入顺序，不是完成顺序
```

| Python | JavaScript |
|--------|------------|
| `asyncio.gather(a, b, c)` | `Promise.all([a, b, c])` |
| 按传入顺序 | 按传入顺序 |
| `return_exceptions=True` | 有点像自己 map 成 `settle`（见下） |

---

### 5.2 异常行为（务必分清）

#### 为什么 gather 的异常语义容易混？

因为「某一个失败」之后，其它任务怎么办——不同 API 答案不同。

#### 怎么写（默认）

```python
import asyncio


async def ok(name: str) -> str:
    await asyncio.sleep(0.05)
    return name


async def bad() -> str:
    await asyncio.sleep(0.02)
    raise ValueError("nope")


async def main() -> None:
    try:
        await asyncio.gather(ok("a"), bad(), ok("c"))
    except ValueError as e:
        print("gather raised:", e)
    # 默认：把「最先发生的异常」传播给 await gather 的一方
    # 其它任务**不会**因此被自动取消，仍可能继续跑完


asyncio.run(main())
```

#### 怎么写（`return_exceptions=True`）

```python
async def main() -> None:
    results = await asyncio.gather(
        ok("a"),
        bad(),
        ok("c"),
        return_exceptions=True,
    )
    for i, r in enumerate(results):
        print(i, type(r).__name__, r)
    # 异常作为结果项返回，不因单个失败而打断 gather 本身


asyncio.run(main())
```

期望输出大致是：

```text
0 str a
1 ValueError nope
2 str c
```

对照决策：

| 需求 | 做法 |
|------|------|
| 任一失败就让调用方立刻知道 | gather 默认（再决定如何处理其它 Task） |
| 想收齐所有成功/失败 | `return_exceptions=True` |
| 一组同生共死、失败取消兄弟任务 | 3.11+ `asyncio.TaskGroup`（下一章） |

#### 跑一下（别误以为默认会取消兄弟）

```python
import asyncio


async def slow(name: str) -> str:
    try:
        await asyncio.sleep(0.2)
        print(name, "finished")
        return name
    except asyncio.CancelledError:
        print(name, "cancelled")
        raise


async def bad() -> str:
    await asyncio.sleep(0.05)
    raise RuntimeError("fail")


async def main() -> None:
    try:
        await asyncio.gather(slow("keep-going"), bad())
    except RuntimeError as e:
        print("caught", e)
    await asyncio.sleep(0.25)  # 给兄弟任务一点时间暴露行为


asyncio.run(main())
# 常见：看到 keep-going finished，而不是 cancelled
```

#### 易错点

| 错法 | 纠正 |
|------|------|
| 把 gather 默认当成 TaskGroup | 默认**不**取消兄弟任务 |
| `return_exceptions=True` 后当全部成功 | 要自己辨认 `isinstance(x, Exception)` |
| 忽略「已失败但仍在跑的任务」的资源占用 | 生产路径要有监督/取消策略（下一章加深） |

#### JS 对照

```javascript
// Promise.all：一个失败就 reject；其它 Promise 仍可能继续跑完
await Promise.all([ok("a"), bad(), ok("c")])

// 想收齐：Promise.allSettled
await Promise.allSettled([ok("a"), bad(), ok("c")])
```

`return_exceptions=True` 的体感更接近 `allSettled`（但仍要自己拆结果）。

---

### 5.3 Agent 场景：并行假工具 / 检索+嵌入

#### 为什么这里要接到 Agent？

因为这就是你后面手写工具环时最常用的骨架。

#### 怎么写

```python
import asyncio


async def search(query: str) -> list[str]:
    await asyncio.sleep(0.2)
    return [f"doc:{query}"]


async def embed(query: str) -> list[float]:
    await asyncio.sleep(0.2)
    return [0.1, 0.2, 0.3]


async def agent_prepare(query: str) -> tuple[list[str], list[float]]:
    docs, emb = await asyncio.gather(
        search(query),
        embed(query),
    )
    return docs, emb


async def main() -> None:
    docs, emb = await agent_prepare("asyncio")
    print(docs, emb)


asyncio.run(main())
```

有依赖时不要硬 gather：

```python
docs = await search(query)
prompt = build_prompt(docs)      # 依赖 docs
answer = await llm(prompt)       # 依赖 prompt
```

#### 跑一下（串行 vs gather 计时）

```python
import asyncio
import time


async def tool(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name


async def sequential_tools() -> list[str]:
    return [
        await tool("search", 0.2),
        await tool("calc", 0.2),
        await tool("browse", 0.2),
    ]


async def parallel_tools() -> list[str]:
    return list(
        await asyncio.gather(
            tool("search", 0.2),
            tool("calc", 0.2),
            tool("browse", 0.2),
        )
    )


async def main() -> None:
    for label, fn in [("sequential", sequential_tools), ("parallel", parallel_tools)]:
        t0 = time.perf_counter()
        print(label, await fn(), "elapsed ≈", round(time.perf_counter() - t0, 3), "s")


asyncio.run(main())
# sequential ≈ 0.6s；parallel ≈ 0.2s
```

#### 易错点

- 把「检索 → 拼 prompt → 生成」整段塞进 gather——有依赖，重叠不动。  
- 并行了 300 个外部调用却不限流——下一章 Semaphore；本章先把正确并发写会。

#### JS 对照

```javascript
const [docs, emb] = await Promise.all([search(query), embed(query)])
```

和 Python 几乎一一对应。

---

## 6. 建议掌握：超时与取消

生产里 LLM / 工具调用必须有超时；用户取消、任务淘汰时要会取消。

### 6.1 超时：`asyncio.wait_for`

#### 为什么需要超时？

网络调用可能永远不回来。没有超时，一个挂起的 await 就能拖死整步 Agent。

#### 怎么写

```python
import asyncio


async def call_llm(prompt: str) -> str:
    await asyncio.sleep(2)  # 假装慢调用
    return f"ok:{prompt}"


async def main() -> None:
    try:
        result = await asyncio.wait_for(call_llm("hi"), timeout=0.5)
    except TimeoutError:  # 3.11+；与内置 TimeoutError 同名
        print("timed out")
    else:
        print(result)


asyncio.run(main())
```

语义（务必分清两层）：

```text
wait_for 超时
  → 取消内部 awaitable
  → 内层任务常收到 CancelledError
  → 外层 await wait_for(...) 看到的是 TimeoutError（3.11+）
```

清理逻辑放在内层的 `try/finally`（或异步上下文管理器）。

#### 跑一下

```python
import asyncio
import time


async def slow() -> str:
    try:
        await asyncio.sleep(1.0)
        return "done"
    finally:
        print("slow cleanup")


async def main() -> None:
    t0 = time.perf_counter()
    try:
        print(await asyncio.wait_for(slow(), timeout=0.2))
    except TimeoutError:
        print("timed out")
    print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")


asyncio.run(main())
```

期望输出大致是：

```text
slow cleanup
timed out
elapsed ≈ 0.2 s
```

#### 易错点

| 错法 | 纠正 |
|------|------|
| 捕获了 `TimeoutError` 却以为内层还在跑且「没关系」 | 超时路径会取消内层；要假设它在收尾 |
| 在内层吞掉 `CancelledError` 还不重新抛出 | 可能导致超时/取消机制失效（见下一小节） |
| 用很老的文档只写 `asyncio.TimeoutError` | 3.11+ 推荐直接 `TimeoutError`（二者相关，课程约定用内置名） |

#### JS 对照

```javascript
// 浏览器：AbortSignal.timeout / AbortController
await fetch(url, { signal: AbortSignal.timeout(500) })
```

Python 的 `wait_for` 更像「带超时的 await 包装器」；取消协作仍要求内层在 await 点响应。

---

### 6.2 取消：`task.cancel`

#### 为什么需要手动取消？

超时只是取消的一种触发器。还有：

- 用户点了停止
- 新请求让旧请求过期
- 竞赛模式：谁先到用谁，其它取消

#### 怎么写

```python
import asyncio


async def call_llm(prompt: str) -> str:
    try:
        await asyncio.sleep(2)
        return f"ok:{prompt}"
    finally:
        print("release resources")


async def main() -> None:
    task = asyncio.create_task(call_llm("hi"))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")
        raise  # 多数情况下继续向上传更安全


try:
    asyncio.run(main())
except asyncio.CancelledError:
    print("main cancelled bubbled")
```

更常见的「在 main 里消化」写法：

```python
async def main() -> None:
    task = asyncio.create_task(call_llm("hi"))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")
        # 若取消是你的预期控制流，这里可以不再 raise
        # 若你在库代码中间层，优先重新 raise，让上层决定


asyncio.run(main())
```

原则：

1. `cancel()` 不是立刻杀死 CPU 指令，而是**在下一个 await 点注入 `CancelledError`**
2. `try/finally` 仍会跑——用来释放资源
3. 不要宽吞 `CancelledError`（写成 `except Exception` 也很危险）

#### 跑一下

```python
import asyncio


async def work() -> None:
    try:
        print("work start")
        await asyncio.sleep(1)
        print("work end")  # 取消成功时通常看不到
    finally:
        print("work finally")


async def main() -> None:
    t = asyncio.create_task(work())
    await asyncio.sleep(0.05)
    t.cancel()
    try:
        await t
    except asyncio.CancelledError:
        print("await saw CancelledError")


asyncio.run(main())
```

期望输出大致是：

```text
work start
work finally
await saw CancelledError
```

#### 易错点

| 错法 | 纠正 |
|------|------|
| `except Exception:` 把 `CancelledError` 吃掉 | 取消失效、任务「僵尸」难查（3.8+ `CancelledError` 继承 `BaseException`，但其它宽捕获仍要小心） |
| 以为 `cancel()` 返回后任务必定已停 | 要 `await task`（或等价汇合）确认收尾 |
| 取消后不做清理 | 连接、临时文件、锁可能泄漏 |

关于继承关系（了解即可，避免教条）：在现代 Python 里 `CancelledError` 是 `BaseException` 的子类，不是普通 `Exception`；所以 `except Exception` **吞不到**它。更常见的事故是：为了「省事」写 `except BaseException`，或在 `finally` 里又启动了无法收尾的新任务。

#### JS 对照

```javascript
const ac = new AbortController()
const p = doWork({ signal: ac.signal })
ac.abort()
try {
  await p
} catch (e) {
  // AbortError
}
```

两边都是**协作式取消**：被取消方要在可中断点响应。

---

### 6.3 超时与取消怎么配合（心智图）

#### 为什么要画在一起？

避免把三种异常/错误混成一锅：

```text
你 await wait_for(inner, timeout=...)
        │
        ├─ 正常完成 → 得到结果
        ├─ inner 抛业务异常 → 传播该异常
        └─ 超时 → 取消 inner
                 ├─ inner 内：CancelledError（可用 finally 清理）
                 └─ 外层：TimeoutError（3.11+）
```

手动 `task.cancel()`：

```text
cancel → await task → 常见看到 CancelledError
```

#### 怎么写（给慢工具统一超时）

```python
import asyncio


async def tool(name: str, delay: float) -> dict:
    await asyncio.sleep(delay)
    return {"tool": name, "ok": True}


async def run_tool(name: str, delay: float, timeout: float = 0.5) -> dict | Exception:
    try:
        return await asyncio.wait_for(tool(name, delay), timeout=timeout)
    except TimeoutError:
        return TimeoutError(f"{name} timed out")


async def main() -> None:
    results = await asyncio.gather(
        run_tool("search", 0.1),
        run_tool("slow_browse", 2.0, timeout=0.2),
        return_exceptions=False,
    )
    print(results)


asyncio.run(main())
```

#### 易错点

把「业务 ValueError」和「超时 TimeoutError」用同一个模糊日志糊过去——排障时分不清是模型坏了还是网络挂了。

#### JS 对照

`AbortSignal.timeout` + `Promise.allSettled` 的组合，和「`wait_for` + gather/return_exceptions」解决的是同一类产品问题：慢调用有上限、一批工具可部分失败。

---

## 7. 了解即可：事件循环实现细节

#### 为什么只了解即可？

selector、proactor、不同 OS 的 I/O 多路复用——知道存在即可。  
应用层把「别阻塞循环」做好，收益远大于背具体后端名字。

#### 怎么建立地图

```text
Windows 常见：ProactorEventLoop（IOCP）
类 Unix 常见：SelectorEventLoop（select/epoll/kqueue 等）
```

你几乎不需要在业务代码里切换它们；`asyncio.run` 会选合理默认。  
真要踩到平台差异，多半是：

- 子进程 / stdin 一类边界行为
- 某些第三方库对 loop 类型敏感

处理策略：查库文档，而不是先重写循环。

#### 跑一下（看当前策略名字，供好奇）

```python
import asyncio


async def main() -> None:
    loop = asyncio.get_running_loop()
    print(type(loop).__name__)


asyncio.run(main())
```

#### 易错点

为了「优化」去手搓 loop 后端——课程与绝大多数 Agent 业务都不需要。

#### JS 对照

Node 有 libuv；浏览器有自己的事件循环阶段。日常业务同样很少直接操作底层轮询机制。

---

## 8. 综合小例子：并行假工具

把本章必掌握点串起来：协程 + gather + 计时 + Agent 一步。

```python
import asyncio
import time


async def tool(name: str, delay: float) -> dict:
    await asyncio.sleep(delay)
    return {"tool": name, "ok": True}


async def run_agent_step() -> list[dict]:
    t0 = time.perf_counter()
    results = await asyncio.gather(
        tool("search", 0.3),
        tool("calc", 0.2),
        tool("browse", 0.4),
    )
    ms = (time.perf_counter() - t0) * 1000
    print(f"elapsed≈{ms:.0f}ms")  # 约 400ms，不是 0.9s
    return list(results)


async def run_agent_step_sequential() -> list[dict]:
    t0 = time.perf_counter()
    results = [
        await tool("search", 0.3),
        await tool("calc", 0.2),
        await tool("browse", 0.4),
    ]
    ms = (time.perf_counter() - t0) * 1000
    print(f"sequential elapsed≈{ms:.0f}ms")  # 约 900ms
    return results


if __name__ == "__main__":
    print("parallel:", asyncio.run(run_agent_step()))
    print("sequential:", asyncio.run(run_agent_step_sequential()))
```

期望现象：

```text
elapsed≈400ms
parallel: [{'tool': 'search', 'ok': True}, ...]
sequential elapsed≈900ms
sequential: [...]
```

还可以加超时保护（建议掌握合练）：

```python
async def run_agent_step_safe() -> list[dict | BaseException]:
    return list(
        await asyncio.gather(
            asyncio.wait_for(tool("search", 0.3), timeout=1.0),
            asyncio.wait_for(tool("calc", 0.2), timeout=1.0),
            asyncio.wait_for(tool("browse", 0.4), timeout=1.0),
            return_exceptions=True,
        )
    )
```

若把任一 `asyncio.sleep` 换成 `time.sleep`，并行版耗时会恶化——请自己改一次，把坑踩实。

---

## 9. 常见坑

1. **在 async 函数里 `time.sleep` / 同步 `requests.get`**  
   卡住整个事件循环；`gather` 也救不了。

2. **创建协程却忘记 `await` / `create_task`**  
   业务没跑 + `RuntimeWarning: never awaited`。

3. **误以为「写了 `async/await` 就等于并发」**  
   依次 await 仍是加法；要 Task / gather。

4. **在已经运行的 loop 里再 `asyncio.run`**  
   嵌套报错；Jupyter/框架内要用它们提供的入口。

5. **假设 `gather` 按完成顺序返回**  
   实际按传入顺序；完成顺序请用其它 API（进阶再谈）。

6. **假设 `gather` 失败会取消兄弟任务**  
   默认不会；要同生共死看 `TaskGroup`（下一章）。

7. **忽略 / 乱吞 `CancelledError`**  
   取消与超时机制依赖它；清理放 `finally`，别当普通业务异常埋掉。

8. **`create_task` 点火后永远不汇合**  
   异常可能被延迟到回收时才爆；谁启动谁负责 await/监督。

9. **用 asyncio 硬扛纯 Python CPU**  
   重叠不了计算；回到进程池/预处理。

10. **JS 直觉误判「调用即开始」**  
    Python 调用 `async def` 只得协程对象；要调度才会进函数体。

---

## 10. 练习指引

按文档顺序做：[`exercises/05-async-python/01-asyncio-fundamentals.md`](../../exercises/05-async-python/01-asyncio-fundamentals.md)

建议本地目录：`playground/05-async-python/01-asyncio-fundamentals/`

做题时强制自己：

1. 每个并发题都打 `time.perf_counter()`  
2. 至少制造一次 `time.sleep` 卡循环，对照 `asyncio.sleep`  
3. 先自己写，再回看本章对应小节

---

## 11. 小结与下一站

### 自检

- [ ] 能手写 `asyncio.run` + `async def` + `await`
- [ ] 能说明「调用协程函数得到对象，不等于已经执行完」
- [ ] 能说明 `await` 让出与事件循环调度的关系
- [ ] 能说明 Task 与裸协程差异，并用计时证明
- [ ] 能用 `gather` 并行等待，且知道返回顺序与默认异常语义
- [ ] 会给慢调用加 `wait_for`，并在取消路径用 `finally` 清理
- [ ] 能解释为什么 `time.sleep` 会毁掉并发

### 关键句记住

> **`await` 让出控制权；Task/`gather` 制造并发；阻塞调用卡死循环；超时与取消要协作响应。**

### 下一章

[`02-asyncio-advanced.md`](./02-asyncio-advanced.md) —— 限流、并发模式、异步 HTTP、`TaskGroup`、`to_thread`、常见生产坑。

## 导航

- 返回模块：[README](./README.md)
- 上一模块：[并发模型](../04-systems-basics/03-concurrency-models.md)
- 下一章：[asyncio 进阶实践](./02-asyncio-advanced.md)
- 课程约定：[CONVENTIONS.md](../CONVENTIONS.md)
