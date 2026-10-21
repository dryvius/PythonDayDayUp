# asyncio 进阶实践

> 所属模块：`05-async-python` · Python 异步编程  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（Semaphore / httpx / 阻塞坑建议动手踩一遍；TaskGroup 有 JS `Promise.all` 经验可更快）  
> 对应练习：[`exercises/05-async-python/02-asyncio-advanced.md`](../../exercises/05-async-python/02-asyncio-advanced.md)  
> 约定：Python ≥ 3.11（`TaskGroup` / `ExceptionGroup` / `except*` / `TimeoutError` 别名）

## 本章定位

- **模块目标**：掌握 asyncio，跨过 Agent 开发分水岭。
- **本章角色**：把基础并发变成「可控的生产级模式」——限流、异步 HTTP、资源生命周期、避坑。
- **前置**：上一章的 `async/await`、事件循环、Task、`gather`、超时与取消。
- **和 Agent**：并行工具时要限流；调 LLM 要用 `AsyncClient`；长任务要能取消与收尾。
- **你的优势**：JS/TS 里的 `Promise`、`p-limit`、`fetch`、`for await` 经验可以直接迁移；Python 侧对应 Semaphore / httpx / `async for`。

## 学习目标（学完应能做到）

1. 用 `Semaphore` 控制最大并发，说清「为什么不能无脑 gather 三百个」。
2. 掌握常见并发控制模式（分批 gather、worker 池、`TaskGroup`），能按场景选型。
3. 会用异步 HTTP 客户端（以 httpx 为例）发请求：复用 client、设 timeout、处理状态码。
4. 了解异步上下文 / 异步生成器，并能避开阻塞事件循环、死锁、未释放信号量等坑。
5. 会用 `asyncio.to_thread` 把不可避免的同步阻塞挪出事件循环线程。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | Semaphore、并发控制模式、异步 HTTP（httpx） | 能写限流并发调用，能复用 AsyncClient |
| **建议掌握** | TaskGroup / ExceptionGroup、异步上下文/生成器、常见坑与 `to_thread` | 能排障与选型，能解释「卡住」从哪来 |
| **了解即可** | trio / anyio | 扫盲，知道依赖树里可能见到 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么基础章还不够？

上一章你已经会「并发等一组 I/O」。但 Agent / 后端一旦上规模，问题立刻变成：

```text
无脑 gather 三百个请求
  → 打爆对方 429
  → 打爆本地连接数 / 文件描述符
  → 内存里堆满 Task
  → 一个慢工具拖死整批（或异常路径没收尾）
```

基础并发解决的是「能不能重叠等待」；进阶解决的是「**又快又稳**」。

#### 本章要练的四种能力

1. **限流**：同一下游最多 N 路同时飞（Semaphore）
2. **模式选型**：一批任务 vs 持续任务流 vs「同生共死」一组工作
3. **异步 HTTP**：用对客户端，超时与连接复用不能省
4. **避坑**：阻塞循环、死锁、未 await、取消后状态不一致

可以先记一句：

> 进阶 asyncio 的核心价值：**把并发从「能跑」变成「可控、可回收、可排障」**。

#### JS 对照（先建立地图）

| JavaScript / Node | Python（本章） |
| --- | --- |
| `p-limit` / 自管并发槽 | `asyncio.Semaphore` |
| `Promise.all` 一批结果 | `asyncio.gather` / 分批 gather |
| 队列 + worker 池 | `asyncio.Queue` + worker |
| `AbortController` + 组取消思路 | `asyncio.TaskGroup`（3.11+） |
| `fetch` / axios（注意连接复用） | `httpx.AsyncClient` |
| `for await (... of asyncIterable)` | `async for` |
| `worker_threads` / 丢到线程池 | `asyncio.to_thread` |

---

## 2. 必掌握：Semaphore 限流

这一节会刻意写细——Semaphore 是后面所有「限流并行」模式的底座。

### 2.1 基本写法：最多 N 个同时进入

#### 为什么需要 Semaphore？

`gather` 会**立刻**把所有任务都丢进循环。任务一多：

- 下游 API 限流（429 / 配额耗尽）
- 本机 socket / 连接池打满
- 峰值内存与调度开销飙升

信号量（Semaphore）提供一个「并发槽」：同一时刻最多 N 个协程持有许可；其余在 `async with` 处等待。

#### 怎么写

```python
import asyncio

sem = asyncio.Semaphore(3)  # 最多 3 个同时进入


async def call_one(i: int) -> int:
    async with sem:  # 获取许可；离开 with 时自动释放
        await asyncio.sleep(0.2)  # 假装 HTTP / LLM
        return i
```

要点：

1. `Semaphore(n)`：初始许可数为 `n`
2. **必须**用 `async with sem:`（或显式 `acquire` / `release`）包住「真正占并发」的那段
3. 信号量对象通常**共享**给一批任务（同一下游共用一个）

#### 跑一下

```python
import asyncio
import time


sem = asyncio.Semaphore(3)


async def call_one(i: int) -> int:
    async with sem:
        print("enter", i)
        await asyncio.sleep(0.2)
        print("leave", i)
        return i


async def main() -> None:
    t0 = time.perf_counter()
    results = await asyncio.gather(*(call_one(i) for i in range(10)))
    print(results)
    print(f"elapsed ≈ {time.perf_counter() - t0:.2f}s")
    # 10 个任务 × 0.2s，限流 3 → 大约 ceil(10/3)*0.2 ≈ 0.8s（略有调度误差）


asyncio.run(main())
```

心智图：

```text
Semaphore(3)  ≈  三个停车位

任务到达 → 有空位就进 → await I/O
         → 没空位就在门口等（不占事件循环 CPU）
离开 with → 让出一个车位给下一个等待者
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `sem = Semaphore(3)` 却放在每个任务里新建 | 每个任务自己一把锁，等于没限流 |
| 只 `acquire` 不 `release` / 不用 `async with` | 许可耗尽，后续任务永久等待 |
| 把限流包在「创建 Task」外层而不是「真正 I/O」外层 | 槽位含义错位，统计不准 |
| 以为 Semaphore 能并行跑 CPU | 不能；它只管「同时有多少协程进入临界区」 |

#### JS 对照

```javascript
// JS 常见：p-limit 或自管计数
import pLimit from "p-limit"
const limit = pLimit(3)

const results = await Promise.all(
  Array.from({ length: 10 }, (_, i) =>
    limit(async () => {
      await sleep(200)
      return i
    }),
  ),
)
```

```python
# Python：Semaphore + gather
sem = asyncio.Semaphore(3)
results = await asyncio.gather(*(call_one(i) for i in range(10)))
```

---

### 2.2 按「下游」分别限流

#### 为什么不能全局只有一个 Semaphore？

Agent 往往同时打多个下游：LLM、搜索、网页抓取、向量库。它们的配额与成本完全不同——用同一把信号量要么过松、要么过严。

#### 怎么写 / 跑一下

```python
import asyncio


llm_sem = asyncio.Semaphore(5)       # LLM：稍宽
search_sem = asyncio.Semaphore(2)    # 搜索：更严
browse_sem = asyncio.Semaphore(1)    # 抓取：最严


async def call_llm(prompt: str) -> str:
    async with llm_sem:
        await asyncio.sleep(0.1)
        return f"echo:{prompt}"


async def search(q: str) -> list[str]:
    async with search_sem:
        await asyncio.sleep(0.15)
        return [q]


async def main() -> None:
    a, b = await asyncio.gather(
        call_llm("hi"),
        search("python asyncio"),
    )
    print(a, b)


asyncio.run(main())
```

Agent 建议：

- 对同一 LLM 供应商设最大并发（如 5）
- 对网页抓取 / 搜索工具设更严的限流
- 信号量可按「下游」分别创建，不要一张全局表打天下

#### 易错点

- 限流数字写死在业务深处 → 难调；至少抽成常量 / 配置
- 忘记：HTTP 客户端自身的 `limits` / 连接池也是一层限流，要和 Semaphore **对齐理解**（见第 4 节）

#### JS 对照

和 Node 里「每个 API host 一个 `p-limit` 实例」是同一思路。

---

### 2.3 `acquire` / `release` 与 `async with` 的关系

#### 为什么还要知道显式 API？

读库代码或写更细的超时包装时，会看到 `acquire()`。日常优先 `async with`；但要懂等价关系，排障才快。

#### 怎么写

```python
# 推荐
async with sem:
    await do_work()

# 等价展开（异常路径必须释放）
await sem.acquire()
try:
    await do_work()
finally:
    sem.release()
```

#### 跑一下（观察「忘了 release」）

```python
import asyncio


async def leak_demo() -> None:
    sem = asyncio.Semaphore(1)
    await sem.acquire()
    # 故意不 release → 第二个 acquire 会一直等
    # await sem.acquire()  # 解开这行会挂住


asyncio.run(leak_demo())
```

#### 易错点

- 在 `acquire` 与 `release` 之间 `return` / 抛异常却没 `finally` → 许可泄漏
- `release` 次数多于 `acquire` → 许可数被抬高（行为符合文档，但多半是 bug）

#### JS 对照

显式 `acquire/release` 类似手写 `try { n++; ... } finally { n-- }`；`async with` 则是把这段固化成协议。

---

## 3. 必掌握：并发控制模式

Semaphore 解决「同时最多几个」；本节解决「任务怎么组织」。三种模式都常见，选型看**任务是否一次性**、**是否持续进流**、**失败要不要取消兄弟**。

### 3.1 分批 gather

#### 为什么需要分批？

有时你不想「全部 Task 立刻创建」（内存 / 调度压力），又想实现简单：按批切，每批 `gather`，批与批串行推进。

#### 怎么写

```python
async def map_batched(items, fn, batch_size: int = 10):
    out = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        part = await asyncio.gather(*(fn(x) for x in batch))
        out.extend(part)
    return out
```

特点：

- 简单、好懂
- 适合**总数可控**的一次性任务列表
- 批内并发、批间串行（峰值并发 ≈ `batch_size`）

#### 跑一下

```python
import asyncio
import time


async def work(x: int) -> int:
    await asyncio.sleep(0.1)
    return x * 2


async def map_batched(items: list[int], batch_size: int = 3) -> list[int]:
    out: list[int] = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        part = await asyncio.gather(*(work(x) for x in batch))
        out.extend(part)
    return out


async def main() -> None:
    t0 = time.perf_counter()
    print(await map_batched(list(range(9)), batch_size=3))
    print(f"elapsed ≈ {time.perf_counter() - t0:.2f}s")
    # 9 个 × 0.1s，每批 3 → 约 0.3s


asyncio.run(main())
```

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 批内又不加 Semaphore，批大小开到 200 | 分批只是换了一种打爆方式 |
| 以为分批能「失败取消整批外的后续」 | 默认不会；批失败策略要自己写 |
| 与 Semaphore 叠用时搞不清峰值 | 峰值 ≈ `min(batch_size, sem_value)` 量级，先画清楚再调 |

#### JS 对照

```javascript
async function mapBatched(items, fn, batchSize = 10) {
  const out = []
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize)
    out.push(...(await Promise.all(batch.map(fn))))
  }
  return out
}
```

---

### 3.2 Worker 池（队列）

#### 为什么需要 worker 池？

分批 gather 适合「手里已经有完整列表」。服务端 / Agent 运行时更常见的是：**任务持续进来**——用户一问，工具调用不断追加。这时用「固定数量的 worker + 队列」更自然。

#### 怎么写

```python
import asyncio


async def worker(name: str, queue: asyncio.Queue) -> None:
    while True:
        item = await queue.get()
        try:
            if item is None:  # 哨兵：结束
                return
            await asyncio.sleep(0.1)
            print(name, "did", item)
        finally:
            queue.task_done()


async def main() -> None:
    queue: asyncio.Queue = asyncio.Queue()
    workers = [asyncio.create_task(worker(f"w{i}", queue)) for i in range(3)]
    for x in range(10):
        await queue.put(x)
    await queue.join()  # 等队列任务都 task_done
    for _ in workers:
        await queue.put(None)  # 毒丸，让 worker 退出
    await asyncio.gather(*workers)


asyncio.run(main())
```

模式拆解：

```text
生产者 put → Queue → N 个 worker 并发 get/处理
join 等待「已投递的任务都完成」
再用哨兵（None）优雅停机
```

#### 跑一下（感受固定并发）

上面例子里 worker 数 = 3，相当于「最多 3 路同时处理」。把 `range(10)` 改大、把 `sleep` 调明显，用打印顺序观察交错。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `get` 后忘记 `task_done` | `queue.join()` 永久等待 |
| 哨兵数量 ≠ worker 数量 | 有的 worker 退不出，或多余哨兵被当成业务数据 |
| 业务异常没包 `try/finally` | `task_done` 漏掉 → join 卡死 |
| fire-and-forget 丢进队列却从不 `join` | 主协程先结束，任务被取消 / 未跑完 |

#### JS 对照

Node 里「固定 N 个消费者读同一个 async queue / channel」是同一骨架；Python 的 `asyncio.Queue` + `task_done`/`join` 把「完成计数」内建了。

---

### 3.3 `TaskGroup`（3.11+，建议掌握）

#### 为什么需要 TaskGroup？

`gather` 默认：**一个失败，其它兄弟不会被取消**，仍可能继续跑完。很多场景你要的是结构化并发：

> 一组任务同生共死；**任一子任务失败 → 取消组内其它任务**；多个错误常以 `ExceptionGroup` 出现。

#### 怎么写（对照表）

| | `asyncio.gather` | `asyncio.TaskGroup` |
|--|------------------|---------------------|
| 失败时取消兄弟？ | **默认否** | **是** |
| 结果收集 | 按传入顺序返回结果列表 | 需自己保存 Task / 回调收集 |
| 多异常 | 默认只抛「先发生的」那个（除非 `return_exceptions`） | 常以 `ExceptionGroup` 汇总 |
| 典型用途 | 收集一组结果 | 要强清理 / 同生共死的一组工作 |

```python
import asyncio


async def boom(n: int) -> int:
    await asyncio.sleep(0.05)
    if n == 1:
        raise RuntimeError("fail")
    return n


async def main() -> None:
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(boom(0))
            tg.create_task(boom(1))  # 失败 → 取消兄弟
            tg.create_task(boom(2))
    except* RuntimeError as eg:  # 3.11+：按类型拆 ExceptionGroup
        print("caught", eg.exceptions)


asyncio.run(main())
```

选型口诀：

- 能用 `gather` 且**不需要**「失败即取消兄弟」→ 继续用 `gather`
- 新代码若要结构化取消 / 强清理 → 优先 `TaskGroup`

#### 跑一下（看取消是否发生）

```python
import asyncio


async def slow(n: int) -> int:
    try:
        await asyncio.sleep(1.0)
        print("finished", n)
        return n
    except asyncio.CancelledError:
        print("cancelled", n)
        raise


async def main() -> None:
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(slow(0))
            tg.create_task(boom_like())
    except* RuntimeError:
        print("group failed")


async def boom_like() -> None:
    await asyncio.sleep(0.05)
    raise RuntimeError("boom")


asyncio.run(main())
# 预期：看到 cancelled 0，而不是 finished 0
```

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 用 `except Exception` 想接住组错误 | 多异常时是 `ExceptionGroup`；应用 `except*` 或显式处理 group |
| 假设 `TaskGroup` 像 `gather` 那样返回结果列表 | 不会；要自己在 task 里写回、或保存 `tg.create_task(...)` 的返回值再 `.result()` |
| 在 `async with TaskGroup` 块外还想 `create_task` 进同一组 | 离开上下文后组已关闭 |
| 子任务里吞掉 `CancelledError` 还不重新抛出 | 破坏取消传播，组无法干净收尾 |

#### JS 对照

```javascript
// Promise.all：一个 reject，all 立刻 reject，
// 但其它 promise 默认仍会继续跑完（除非你自己 AbortSignal）
await Promise.all([a(), b(), c()])
```

```python
# TaskGroup：失败会主动 cancel 兄弟（更接近「结构化并发」）
async with asyncio.TaskGroup() as tg:
    tg.create_task(a())
    tg.create_task(b())
```

JS 没有与 `TaskGroup` 一一对应的语言内建；常见是 `AbortController` + 约定取消，或第三方结构化并发库。Python 3.11 把这套收进标准库。

---

### 3.4 模式怎么选（一张表）

| 场景 | 更合适的模式 |
| --- | --- |
| 一次性列表、要结果顺序、失败可继续收集 | `gather`（可加 Semaphore） |
| 一次性列表、控制峰值创建量 | 分批 gather |
| 持续进任务、固定并发工人 | Queue + worker 池 |
| 一组工作必须同生共死、失败即清理 | `TaskGroup` |
| 同一下游防打爆 | **任何模式都叠加 Semaphore** |

---

## 4. 必掌握：异步 HTTP 客户端（httpx）

### 4.1 安装与最小请求

#### 为什么要用异步 HTTP 客户端？

在 `async` 函数里用同步 `requests` / `urllib`，等于在事件循环线程里阻塞——其它协程全部排队干等。Agent 的 LLM、工具、检索几乎全是 HTTP，这里用错，前面学的并发全白费。

#### 怎么写

```bash
pip install httpx
# 或 uv add httpx
```

```python
import asyncio
import httpx


async def fetch_text(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.text
```

#### 跑一下（限流 + 复用 client）

```python
import asyncio
import httpx


async def fetch_many(urls: list[str]) -> list[str]:
    sem = asyncio.Semaphore(5)
    async with httpx.AsyncClient(timeout=10.0) as client:

        async def one(url: str) -> str:
            async with sem:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.text

        return await asyncio.gather(*(one(u) for u in urls))


# 练习可用 https://httpbin.org/get 或本地 mock，避免依赖真实 Key
# asyncio.run(fetch_many(["https://httpbin.org/get"] * 3))
```

#### 易错点（先记四条）

1. 用 **`AsyncClient`**，不要在 async 里用同步 `requests`
2. **timeout 必设**（连接超时 + 读超时；`timeout=10.0` 是起步）
3. 客户端复用：热路径上**共享一个 client**，不要每个请求 `AsyncClient()` 新建又销毁
4. `raise_for_status()` 处理 4xx/5xx；否则「拿到了 Response」不等于「业务成功」

#### JS 对照

```javascript
// 浏览器 / Node 18+：fetch
const resp = await fetch(url, { signal: AbortSignal.timeout(10_000) })
if (!resp.ok) throw new Error(String(resp.status))
const text = await resp.text()
```

```python
async with httpx.AsyncClient(timeout=10.0) as client:
    resp = await client.get(url)
    resp.raise_for_status()
    text = resp.text
```

---

### 4.2 为什么必须复用 `AsyncClient`

#### 为什么？

每次新建 client 通常意味着：

- 重新建连接池 / SSL 上下文
- 无法复用 keep-alive
- 更多握手延迟与文件描述符抖动

生产热路径：**一个生命周期内共享 client**（应用启动时建、关闭时 `aclose`；或用 `async with` 包住一整批请求）。

#### 怎么写（两种常见寿命）

```python
# A. 一批请求共用（脚本 / 单次 Agent step）
async with httpx.AsyncClient(timeout=10.0) as client:
    await asyncio.gather(fetch_text(client, u1), fetch_text(client, u2))

# B. 长寿命（服务进程）：在 startup 创建，shutdown 关闭
# app.state.http = httpx.AsyncClient(timeout=10.0)
# ...
# await app.state.http.aclose()
```

#### 易错点

- 在循环里 `async with AsyncClient() as client: await client.get(...)` → 每个请求新建，几乎抵消异步收益
- 长寿命 client 忘记在进程退出时关闭 → 资源警告 / 连接泄漏
- 把「Semaphore 限流」和「client 连接池上限」当成一回事 → 两层都要理解，数字建议对齐

#### JS 对照

Node 里复用 `undici`/`axios` 实例、或依赖全局 `fetch` 的连接复用，是同一类优化；Python 教学里把「共享 AsyncClient」写死成纪律即可。

---

### 4.3 假 LLM 调用形态

#### 为什么要单独记这个形状？

后面 Agent / LLM 章会反复出现：`POST` JSON、带 `Authorization`、解析 `resp.json()`。先把异步外壳练熟，真 Key 只是换 URL 与字段。

#### 怎么写 / 跑一下（结构示意）

```python
import httpx


async def chat(client: httpx.AsyncClient, prompt: str) -> dict:
    resp = await client.post(
        "https://api.example.com/v1/chat/completions",
        json={
            "model": "gpt-x",
            "messages": [{"role": "user", "content": prompt}],
        },
        headers={"Authorization": "Bearer sk-xxx"},
    )
    resp.raise_for_status()
    return resp.json()
```

练习建议：用 httpbin 或本地 mock，**避免依赖真实 Key**（与仓库 FakeLLM 约定一致：CI / 单测必须可无 Key 绿）。

#### 易错点

- 把 API Key 写进仓库 → 用环境变量；教学示例里的 `sk-xxx` 仅示意
- 忽略超时：LLM 慢是常态，`timeout` 与上层 `wait_for` 可叠用，但要清楚谁负责取消
- 同步 SDK 塞进 `async def` 却不 `to_thread` → 见第 6 节

#### JS 对照

和前端 `await fetch('/v1/chat/completions', { method:'POST', body: JSON.stringify(...) })` 同形；差别在 Python 侧更强调 **AsyncClient 生命周期**。

---

## 5. 建议掌握：异步上下文与异步生成器

### 5.1 `async with`：异步上下文管理器

#### 为什么需要异步版 `with`？

获取 / 释放本身常常要 `await`（连接池借还、HTTP client 关闭、异步 DB）。同步 `__enter__` / `__exit__` 不够用。

协议对应：

```text
__aenter__ / __aexit__
```

#### 怎么写

```python
import asyncio


class FakeConn:
    async def __aenter__(self):
        await asyncio.sleep(0)  # 假装异步握手
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await asyncio.sleep(0)  # 假装异步关闭
        return None


async def main() -> None:
    async with FakeConn() as conn:
        print("using", conn)


asyncio.run(main())
```

快捷写法：

```python
from contextlib import asynccontextmanager
import asyncio


@asynccontextmanager
async def agent_span(name: str):
    print("start", name)
    try:
        yield {"name": name}
    finally:
        print("end", name)


async def main() -> None:
    async with agent_span("llm") as span:
        await asyncio.sleep(0.01)
        print("span", span)


asyncio.run(main())
```

`httpx.AsyncClient`、异步 DB 连接都靠 `async with`（或显式 `aclose`）保证关闭。

#### 跑一下

上面两段可直接跑；观察 `start` / `end` 是否在异常路径也会打印（在 `yield` 后故意 `raise` 验证 `finally`）。

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 对异步管理器用普通 `with` | 类型/运行期都不对；要用 `async with` |
| `@asynccontextmanager` 里没有 `try/finally` | 异常时收尾逻辑被跳过（与同步 `@contextmanager` 同一坑） |
| 在 `__aexit__` 里再开无限等待且无超时 | 退出阶段卡住，资源更难回收 |

#### JS 对照

```javascript
const client = await createClient()
try {
  await client.get(url)
} finally {
  await client.close()
}
```

Python 用协议把这段收成 `async with`；模块 02 的上下文管理器章已铺过地图，这里是异步实战。

---

### 5.2 异步生成器与 `async for`

#### 为什么需要异步生成器？

流式 LLM 输出、SSE、分块下载：生产者「有一块就 yield 一块」，消费者用 `async for` 边收边处理，而不必等全部结束。

#### 怎么写

```python
import asyncio


async def token_stream(text: str):
    for ch in text:
        await asyncio.sleep(0)  # 让出循环；真实场景是等网络块
        yield ch


async def main() -> None:
    async for ch in token_stream("hi"):
        print(ch, end="")
    print()


asyncio.run(main())
```

#### 跑一下（拼回完整字符串）

```python
async def collect(text: str) -> str:
    parts: list[str] = []
    async for ch in token_stream(text):
        parts.append(ch)
    return "".join(parts)


async def main() -> None:
    print(await collect("agent"))  # agent


asyncio.run(main())
```

#### 易错点

- 在异步生成器里用 `time.sleep` → 一样卡循环
- 把 `async for` 写成普通 `for` → 得不到异步迭代协议
- 生成器没被迭代完就丢弃 → 看场景是否需要 `aclose()` / 上下文包一层，避免半开连接

#### JS 对照

```javascript
async function* tokenStream(text) {
  for (const ch of text) {
    await sleep(0)
    yield ch
  }
}

for await (const ch of tokenStream("hi")) {
  process.stdout.write(ch)
}
```

---

## 6. 建议掌握：常见死锁与坑

排障口诀先记：

> **先找阻塞点，再找锁与未 await，再看超时。**

### 6.1 死锁：持锁时 await 另一个也要同锁的任务

#### 为什么会死锁？

协程是协作式的：你在持有锁时 `await`，其它协程可以运行——但如果它们也要同一把锁，而你又不释放，两边就互相等。

#### 怎么写（错误形态 vs 正确思路）

```python
import asyncio

lock = asyncio.Lock()


async def bad() -> None:
    async with lock:
        # 危险示意：持锁期间又去等「也需要同一把 lock」的路径
        await also_needs_same_lock()


async def also_needs_same_lock() -> None:
    async with lock:  # 若由 bad 持锁同步等待到这里 → 死锁
        return


# 正确思路（选一）：
# 1. 缩小持锁范围：只锁「读改写共享状态」那几行，I/O 放到锁外
# 2. 拆锁 / 规定锁顺序，避免 AB-BA
# 3. 把需要同锁的逻辑合并到同一临界区，避免「持锁 await 别人再抢锁」
```

#### 跑一下（最小死锁演示）

```python
import asyncio

lock = asyncio.Lock()


async def child() -> None:
    async with lock:
        print("child got lock")


async def parent() -> None:
    async with lock:
        print("parent holding lock")
        await child()  # child 也要 lock → 死锁


# asyncio.run(parent())  # 会挂住；演示时用 wait_for 包一层看超时
async def main() -> None:
    try:
        await asyncio.wait_for(parent(), timeout=0.5)
    except TimeoutError:
        print("deadlock suspected: timed out")


asyncio.run(main())
```

#### 易错点

- 以为「协程没有线程死锁」→ 有，形态换成「锁 + await」
- 持锁做 HTTP / LLM → 临界区过长，吞吐塌掉（即使侥幸不死锁）

#### JS 对照

单线程 JS 里用 `async` mutex 也会出现同一类问题：持锁 `await` 后再请求同锁。原则相同——**缩小临界区，I/O 不要握着锁做**。

---

### 6.2 阻塞事件循环：异步里调用同步阻塞 I/O

#### 为什么整站会「卡住」？

事件循环跑在**一个线程**里。`time.sleep`、同步 `requests.get`、重 CPU 循环、同步磁盘大读写，都会占住这根线程——其它协程即使 `await` 好了也得不到调度。

#### 怎么写 / 跑一下（对比）

```python
import asyncio
import time


async def blocked() -> None:
    time.sleep(1)  # 错误：卡住整个循环
    print("blocked done")


async def peer() -> None:
    await asyncio.sleep(0.1)
    print("peer done")


async def main() -> None:
    await asyncio.gather(blocked(), peer())
    # peer 往往要等 blocked 的 time.sleep 结束才有机会打印


asyncio.run(main())
```

正确方向（下一小节）：把阻塞调用丢进线程。

#### 易错点

| 阻塞源 | 典型例子 |
| --- | --- |
| 同步 sleep | `time.sleep` |
| 同步 HTTP | `requests`、部分同步 SDK |
| 重 CPU | 大 JSON 解析死循环、纯 Python 算特征 |
| 同步磁盘 | 巨大文件同步读（视调用而定） |

#### JS 对照

Node 里在请求回调里跑重同步 CPU，一样会饿死事件循环；差别是 Python 教学里更常误用 `requests` / `time.sleep`。

---

### 6.3 `asyncio.to_thread`：阻塞调用的逃生舱

#### 为什么需要 `to_thread`？

有些库只有同步 API（或短期内改不掉）。`asyncio.to_thread(fn, *args)` 把调用丢到线程池，当前协程 `await` 等待结果，**事件循环线程得以继续调度其它任务**。

约定：Python 3.9+ 提供；本路线按 ≥ 3.11。

#### 怎么写

```python
import asyncio
import time


def blocking_sleep(seconds: float) -> str:
    time.sleep(seconds)  # 同步阻塞，但会在线程里跑
    return "ok"


async def main() -> None:
    results = await asyncio.gather(
        asyncio.to_thread(blocking_sleep, 0.3),
        asyncio.to_thread(blocking_sleep, 0.3),
        asyncio.to_thread(blocking_sleep, 0.3),
    )
    print(results)  # 三者重叠等待，总耗时约 0.3s 量级，而非 0.9s


asyncio.run(main())
```

#### 跑一下（用 `perf_counter` 亲眼看）

```python
import asyncio
import time


def blocking_sleep(seconds: float) -> str:
    time.sleep(seconds)
    return "ok"


async def main() -> None:
    t0 = time.perf_counter()
    await asyncio.gather(
        *(asyncio.to_thread(blocking_sleep, 0.3) for _ in range(3))
    )
    print(f"elapsed ≈ {time.perf_counter() - t0:.2f}s")


asyncio.run(main())
```

#### 易错点

- `to_thread` **不是**多核银弹：受 GIL 影响，CPU 密集仍可能挤在一起；它擅长救 **阻塞 I/O / 同步 SDK**
- 线程里的代码仍要自己保证线程安全
- 能异步的库（httpx、异步驱动）优先原生 async，而不是全部 `to_thread`
- 无限把重任务丢线程池 → 池耗尽，一样会堆请求

#### JS 对照

类似把重活丢给 `worker_threads` / 池化执行；Python 的 `to_thread` 更轻量，适合「偶尔同步阻塞」而不是替代真正的异步库。

---

### 6.4 其它高频坑（清单）

#### 为什么要集中扫一遍？

这些坑在代码审查里反复出现；每个都不长，但线上症状都是「偶发卡住 / 异常消失 / 资源泄漏」。

#### 怎么写（对照正确姿势）

1. **Fire-and-forget Task 不保存引用** → 可能被回收、异常丢失  
   - 保存 task 引用，或显式管理生命周期（列表 / TaskGroup）
2. **Semaphore 忘记 `async with` 释放** → 许可耗尽，后续全挂  
3. **在 running loop 中调用 `asyncio.run`** → 报错；嵌套要用当前 loop 策略，而不是再 `run` 一层  
4. **取消后仍假设共享状态一致** → 在 `finally` 里清理；对共享结构做「取消安全」设计  
5. **`gather` 与 `TaskGroup` 取消语义搞混** → 见第 3.3 节对照表

#### 跑一下（未 await 的协程警告）

```python
import asyncio


async def work() -> str:
    return "done"


async def main() -> None:
    work()  # 忘记 await：通常会 RuntimeWarning，且工作没执行
    await asyncio.sleep(0)


asyncio.run(main())
```

#### 易错点口诀（再背一次）

> 先找阻塞点，再找锁与未 await，再看超时。

#### JS 对照

| 坑 | JS 近似 |
| --- | --- |
| 未 await | floating Promise，无 `await` / `.catch` |
| 未保存 Task | 丢失的 Promise 引用 + 未处理 rejection |
| 嵌套 `asyncio.run` | 「已经在异步上下文又去乱开新运行时」类问题 |

---

## 7. 了解即可：trio / anyio

#### 为什么会出现在依赖树里？

生态里不只有 asyncio 一种风格：

- **Trio**：另一套结构化并发思想（nursery 等），影响了后来的 API 设计讨论
- **AnyIO**：兼容层，很多库用它做「后端无关」异步（asyncio / trio 可切换）

#### 怎么写（认名字即可）

你会在依赖树里见到 `anyio`、偶见 `trio`。本路线主线仍是：

```text
asyncio + httpx + FastAPI
```

会用本章的 Semaphore / TaskGroup / AsyncClient，就已经能覆盖绝大多数 Agent 后端场景。

#### 易错点

- 同一进程混用多套事件循环后端 → 除非库明确支持，否则别自己拼
- 看到 `anyio.Sleep` / `anyio.create_task_group` 不必慌：概念上可映射到本章的 sleep / TaskGroup

#### JS 对照

类似「主流是原生 Promise / async，但生态里还有专用并发库」——知道地图即可，不必一开始双修。

---

## 8. 综合小例子：限流并行工具调用

把 Semaphore、假工具、结果收集收成一个可跑最小件——形态接近 Agent「一步并行打多个 tool」。

#### 为什么要综合练？

单点知识会背，不等于能拼：真正写 Agent step 时，限流、超时、结果列表、错误策略会挤在一起。先用假 `sleep` 把骨架跑通。

#### 怎么写 / 跑一下

```python
import asyncio
import time
from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    delay: float


async def run_tool(call: ToolCall, sem: asyncio.Semaphore) -> dict:
    async with sem:
        await asyncio.sleep(call.delay)
        return {"name": call.name, "ok": True}


async def run_tools(calls: list[ToolCall], limit: int = 2) -> list[dict]:
    sem = asyncio.Semaphore(limit)
    return list(await asyncio.gather(*(run_tool(c, sem) for c in calls)))


async def main() -> None:
    calls = [
        ToolCall("search", 0.3),
        ToolCall("browse", 0.4),
        ToolCall("calc", 0.1),
        ToolCall("embed", 0.2),
    ]
    t0 = time.perf_counter()
    print(await run_tools(calls, limit=2))
    print(f"elapsed ≈ {time.perf_counter() - t0:.2f}s")
    # limit=2 时，总耗时接近「按并发 2 调度后的关键路径」，而非四个 delay 相加


if __name__ == "__main__":
    asyncio.run(main())
```

升级方向（练习里可继续做）：

- 换成 `httpx.AsyncClient` 打 httpbin
- 失败策略：`return_exceptions=True` vs `TaskGroup`
- 给单工具加 `asyncio.wait_for(..., timeout=...)`
- 不可避免的同步工具：`asyncio.to_thread`

#### 易错点

- `limit` 与工具数量、单工具耗时没一起看 → 用 `perf_counter` 校准预期
- 结果顺序依赖 `gather` 的「按传入顺序返回」——若改成 Queue/worker，顺序要自己编码

#### JS 对照

```javascript
const limit = pLimit(2)
const results = await Promise.all(
  calls.map((c) => limit(() => runTool(c))),
)
```

与本节 Python 版同构：`Semaphore(limit)` ≈ `pLimit(limit)`。

---

## 9. 练习指引

按练习文档做，优先亲手踩这些点：

1. Semaphore 限流是否真的把耗时从「串行总和」改成「按并发度分段」
2. 分批 gather 与 worker 池各写一小版，感受适用场景
3. httpx（或 mock）复用 `AsyncClient` + timeout
4. 故意写一次 `time.sleep`，再改成 `to_thread`，对比 peer 任务是否还能推进

练习入口：[`exercises/05-async-python/02-asyncio-advanced.md`](../../exercises/05-async-python/02-asyncio-advanced.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能用 Semaphore 限制并发，并按下游分别限流
- [ ] 能写出分批 gather 或简单 worker，并说清何时用 `TaskGroup`
- [ ] 能用 `httpx.AsyncClient` 发异步请求（或 mock），知道复用与 timeout
- [ ] 知道 `async with` / `async for` 的基本用途
- [ ] 知道阻塞调用会毁掉事件循环，会用 `to_thread` 做逃生舱
- [ ] 能解释死锁（持锁 await 再抢同锁）与取消后的清理责任

### 一张图收回去

```text
并发能跑
  → Semaphore：别打爆下游
  → 模式：分批 / worker / TaskGroup
  → httpx.AsyncClient：真 I/O 要用异步客户端
  → async with / async for：资源与流式
  → 避坑：阻塞、死锁、未释放、未 await
  → to_thread：同步库的临时桥
```

### 模块 05 收官

下一模块：[`../06-web-backend/README.md`](../06-web-backend/README.md) —— Web 后端（ASGI / FastAPI / Pydantic / 认证），异步能力会直接用上。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[asyncio 基础](./01-asyncio-fundamentals.md)
- 下一模块：[Web 后端](../06-web-backend/README.md)
