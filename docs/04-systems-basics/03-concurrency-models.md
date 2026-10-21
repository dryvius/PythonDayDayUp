# 并发模型

> 所属模块：`04-systems-basics` · 计算机与服务端基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有前端事件循环 / Worker 经验可更快；GIL 与选型清单建议动手测一遍）  
> 对应练习：[`exercises/04-systems-basics/03-concurrency-models.md`](../../exercises/04-systems-basics/03-concurrency-models.md)

## 本章定位

- **模块目标**：补齐前端背景下的系统直觉，避免一知半解。
- **本章角色**：在写 asyncio 专章前，先建立「并发选项地图」，避免盲选线程/进程/异步。
- **和 Agent**：要同时等多个工具、多个嵌入请求、多个 LLM 调用——必须懂并发。
- **刻意不做**：本章只铺「为什么需要 asyncio、它和线程/进程差在哪」；`async/await`、事件循环、`gather` 细节留给模块 05。

## 学习目标（学完应能做到）

1. 分清并行与并发，并用生活例子 / Agent 例子讲清楚。
2. 对比多线程 / 多进程 / 异步的适用场景与代价。
3. 建立 Python GIL 直觉（知道它限制什么、不限制什么）。
4. 能对具体任务（尤其是 Agent I/O）选出合理模型。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 并行 vs 并发、三种模型对比、GIL 直觉 | 能选型、能解释 |
| **建议掌握** | 何时选哪种（Agent 清单） | 能讲清理由 |
| **了解即可** | 无锁结构 | 扫盲，知道应用层优先消息传递 |

---

## 1. 为什么要学

#### 为什么并发是 Agent 的硬技能？

同步写法（一个完再等下一个）：

```text
search()   等 800ms
browse()   等 1200ms
embed()    等 500ms
总计 ≈ 2.5s
```

并发写法（I/O 等待重叠）：

```text
search + browse + embed 同时等
总计 ≈ 1.2s（约等于最慢那个）
```

Agent 延迟体验往往取决于你会不会重叠 I/O。  
同一段「等网络」的时间，串行是加法，能重叠就接近取 max。

#### 怎么理解本章要解决的问题

你后面会听到很多词：线程、进程、asyncio、线程池、GIL……  
本章先画一张**选型地图**，回答三件事：

1. 我是在「交替推进多个任务」，还是在「多核真的一起算」？
2. 这个任务主要是**等 I/O**，还是**吃 CPU**？
3. Python 里选线程 / 进程 / 异步，各自换到了什么、付出了什么？

可以先记一句：

> 先分清「并发结构」和「并行算力」，再谈用哪套 API。

#### 跑一下（同步串行的「慢」长什么样）

不用任何并发库，先感受串行：

```python
import time


def fake_io(name: str, sec: float) -> str:
    time.sleep(sec)  # 假装网络等待
    return name


def sequential() -> list[str]:
    return [fake_io("a", 0.2), fake_io("b", 0.2)]


t0 = time.perf_counter()
print(sequential())
print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")
# 大约 0.4s：两个 0.2 相加
```

后面第 7 节会用线程池做对照；模块 05 再用 asyncio 做第三种对照。  
现在只要记住：**串行 I/O 的时间是相加的。**

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 以为「用了并发库就一定更快」 | 任务有串行依赖时，重叠不了；还多了调度开销 |
| 把「并发」和「多核加速」当成一回事 | 异步/多线程常是重叠等待，不等于 CPU 并行 |
| 一上来就学 asyncio API | 不知道自己要解决的是 I/O 重叠还是 CPU 并行，容易选错 |

#### JS 单线程 / Worker 对照

前端里你已经见过类似问题：

```text
主线程里同步 for 循环算很久 → 页面卡死
fetch / setTimeout → 主线程可以先去做别的事（事件循环）
Web Worker → 另开执行流，适合重计算，但不共享随意内存
```

| 前端直觉 | 本章对应 |
|----------|----------|
| 事件循环重叠多个网络请求 | 并发（尤其是异步模型） |
| `Promise.all` 一起等 | I/O 等待重叠 |
| Web Worker 扛重计算 | 更像「另开执行单元」（Python 里常是多进程） |
| 主线程被同步死循环卡住 | 异步里误调阻塞函数（后面反复警告） |

---

## 2. 必掌握：并行 vs 并发

这一节会刻意写细——后面所有选型都建立在这对概念上。

### 2.1 一句话定义

#### 为什么要先分清这两个词？

中文口语里「并行」「并发」经常混用。混了之后你会把：

- 「单线程事件循环同时等 100 个 HTTP」  
和  
- 「8 核同时算 8 段正则」  

当成同一件事，然后奇怪：为什么 asyncio 没有把 CPU 打满？

#### 怎么理解

| 概念 | 含义 | 典型画面 |
|------|------|----------|
| **并发 concurrency** | 同一**时段**交替推进多个任务 | 单核上边等网络边切换任务；一人同时炖汤+洗碗（交替） |
| **并行 parallelism** | 同一**时刻**真正一起执行 | 多核同时算；两人同时切菜 |

一句话：

> **并发是结构问题**（怎么组织多个未完成任务）；**并行是硬件同时执行问题**（多个执行单元真的一起跑）。

关系可以记成：

```text
并行 ⊂ 一种实现并发的手段（但并发不必并行）

可以：
  - 并发但不并行：单核时间片切换 / 单线程事件循环
  - 又并发又并行：多进程压榨多核 CPU
```

异步编程首先解决的是**高并发 I/O**，不一定等于多核并行算力。

#### 跑一下（用「厨师」类比钉死）

不必写复杂代码，先用时间线理解：

```text
【并发但不并行】一个厨师：
  开火炖汤 → 等汤沸腾时去切菜 → 汤好了回来搅
  同一时刻只做一件事，但多个任务都在推进

【并行】两个厨师：
  A 炖汤的同时 B 在切菜
  同一时刻两件事都在发生
```

Agent 版：

```text
【并发】一个事件循环同时「挂起等待」10 个 embedding HTTP
【并行】8 个进程同时对本地大文件做 CPU 正则清洗
```

#### 易错点

| 错法 | 纠正 |
|------|------|
| 「asyncio = 多核加速」 | asyncio 默认单线程协作；擅长重叠 I/O，不擅长纯 Python CPU |
| 「多线程一定并行」 | 在 CPython 里，CPU 字节码常受 GIL 限制；I/O 等待时才更像「有用的并发」 |
| 「只要任务多就会更快」 | 有依赖链（A→B→C）时，B 必须等 A，重叠空间有限 |

#### JS 单线程 / Worker 对照

```javascript
// 并发（主线程事件循环）：多个 fetch 同时飞着
await Promise.all([fetch(url1), fetch(url2), fetch(url3)])

// 并行感更强（Worker）：重计算挪出主线程
// new Worker('heavy.js')  — 不共享主线程的随意内存
```

| JavaScript | Python 心智 |
|------------|-------------|
| 主线程单线程 + 事件循环 | 很像「单线程异步并发」 |
| `Promise.all` 重叠等待 | 下一模块的 `asyncio.gather` 同类问题 |
| Web Worker | 更接近「另开执行单元」；Python 重 CPU 常用多进程 |

---

### 2.2 Agent 场景里怎么用这对概念

#### 为什么 Agent 几乎天天碰「并发」？

典型一步：

```text
用户问题
  → 同时：检索 / 读文件 / 调工具
  → 拼 prompt
  → 调 LLM
  → 可能再并发调多个工具
```

检索、工具、embedding **彼此常无依赖**，天然适合并发等待。  
而「拼 prompt → 调 LLM」常常有顺序，不能假装并行。

#### 怎么理解（先问两个问题）

1. **这些等待能不能重叠？**（有没有数据依赖）  
2. **瓶颈是网络等待，还是本地 CPU？**

| 场景 | 更像 | 直觉选型 |
|------|------|----------|
| 10 路 HTTP embedding | 并发 I/O | 异步（或线程池包同步客户端） |
| 本地解析 200MB 文本 | 想要并行 CPU | 多进程 / 离线预处理 |
| 检索→拼 prompt→生成 | 串行依赖 | 保持串行（局部步骤内部仍可并发） |

#### 跑一下（依赖让「并发」失效）

```python
import time


def step_a() -> str:
    time.sleep(0.1)
    return "ctx"


def step_b(ctx: str) -> str:
    time.sleep(0.1)
    return ctx + "|prompt"


def step_c(prompt: str) -> str:
    time.sleep(0.1)
    return prompt + "|answer"


def pipeline() -> str:
    # 有依赖：没法合理重叠成「只花 0.1s」
    return step_c(step_b(step_a()))


t0 = time.perf_counter()
print(pipeline())
print("elapsed ≈", round(time.perf_counter() - t0, 3), "s")  # ≈ 0.3s
```

结论：

> 并发只能重叠**彼此独立**的等待；依赖链还是加法。

#### 易错点

- 把「三步流水线」强行丢进线程池，结果还是得按顺序 `result()`，白白增加复杂度。  
- 局部可并发、整体串行：例如「先并发检索 3 个源，再串行生成」——要拆开看。

#### JS 对照

```javascript
// 可重叠
await Promise.all([toolA(), toolB()])

// 有依赖：仍然得顺序
const ctx = await retrieve()
const prompt = build(ctx)
const answer = await llm(prompt)
```

---

## 3. 必掌握：三种模型对比

Python 里最常见的三条路：

```text
多线程 threading / concurrent.futures.ThreadPoolExecutor
多进程 multiprocessing / ProcessPoolExecutor
异步   asyncio（下一模块细学）
```

先建立地图，再逐个加深。

### 3.1 总览对照

#### 为什么要三选一，而不是「永远用最快的」？

因为它们优化的东西不同，代价也不同：

| 模型 | 共享什么 | 擅长 | 主要代价 |
|------|----------|------|----------|
| 多线程 | 同进程内存 | 阻塞 I/O 等待 | 竞态、加锁、GIL 限制 CPU 并行 |
| 多进程 | 基本不共享（要 IPC） | CPU 密集真并行 | 内存更大、序列化/通信更重 |
| 异步 | 单线程协作 | 大量网络 I/O | 调用链要异步化；阻塞会卡死循环 |

#### 怎么理解（一张决策草图）

```text
主要是等 HTTP / LLM / DB？
  ├─ 调用链能异步化 → asyncio（模块 05）
  └─ 库只有同步 API → 线程池包一层

主要是吃 CPU（纯 Python 重计算）？
  └─ 多进程 / 本地扩展 / 干脆离线预处理

任务很少、脚本偶发并发？
  └─ concurrent.futures 往往够用
```

#### 跑一下（三种模型「听起来」长什么样）

先看 API 轮廓（**能读懂即可**；asyncio 细节下章再写）：

```python
# 1) 线程池：把「阻塞函数」丢到别的线程跑
from concurrent.futures import ThreadPoolExecutor

def blocking_io() -> str:
    import time
    time.sleep(0.1)
    return "ok"

with ThreadPoolExecutor(max_workers=4) as pool:
    future = pool.submit(blocking_io)
    print(future.result())

# 2) 进程池：把「CPU 函数」丢到别的进程跑（示意）
# from concurrent.futures import ProcessPoolExecutor
# with ProcessPoolExecutor() as pool:
#     print(pool.submit(cpu_heavy, data).result())

# 3) 异步：在事件循环里 await 多个 I/O（下章展开）
# await asyncio.gather(fetch_a(), fetch_b())
```

#### 易错点

| 错法 | 说明 |
|------|------|
| 「线程 = 一定比进程快」 | I/O 场景线程轻；CPU 场景进程才可能真快 |
| 「异步 = 自动多核」 | 默认不是 |
| 「三种一起上一定更强」 | 混合模型要有边界（见选型清单）；乱叠复杂度爆炸 |

#### JS 对照

| Python | 前端粗对照 |
|--------|------------|
| 线程池跑阻塞 I/O | 有点像把同步工作丢给别的执行上下文（但不等于 Promise） |
| 多进程 | 更像 Worker / 多进程工具链 |
| asyncio | 最像主线程事件循环 + `async/await` |

---

### 3.2 多线程（threading）

#### 为什么还需要线程？

现实里大量库是**同步阻塞**的：`requests`、某些 SDK、老数据库驱动。  
你短期改不成全异步，但又想同时等好几个调用——线程池是务实逃生舱。

#### 怎么理解

- 同进程共享内存（传对象方便，也容易踩竞态）
- 适合：**阻塞 I/O** 等待（在等的时候常释放 GIL，其它线程可跑）
- 风险：多线程改同一 `list`/`dict`/计数器，可能数据错乱
- CPU 密集：受 GIL 限制，加速有限（见第 4 节）

常用高层 API：`concurrent.futures.ThreadPoolExecutor`（比手搓 `threading.Thread` 更省心）。

#### 跑一下（同步串行 vs 线程池）

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def fake_io(name: str, sec: float) -> str:
    time.sleep(sec)
    return name


def sequential() -> list[str]:
    return [fake_io("a", 0.2), fake_io("b", 0.2)]


def threaded() -> list[str]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fake_io, n, 0.2) for n in ("a", "b")]
        # as_completed：按完成顺序；不要假设 == ["a", "b"]
        return [f.result() for f in as_completed(futs)]


def threaded_in_order() -> list[str]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fake_io, n, 0.2) for n in ("a", "b")]
        return [f.result() for f in futs]  # 按提交顺序取结果


for label, fn in [("sequential", sequential), ("threaded", threaded)]:
    t0 = time.perf_counter()
    result = fn()
    print(label, result, "elapsed ≈", round(time.perf_counter() - t0, 3), "s")

# sequential ≈ 0.4s；threaded ≈ 0.2s（都在 sleep，线程版应明显更快）
# 断言结果时用集合相等，或改用 threaded_in_order()
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 假设 `as_completed` 顺序 == 提交顺序 | 完成快的先出来 |
| 多线程无锁改同一计数器 | 结果可能对不上（练习 A2） |
| 用多线程硬扛纯 Python CPU | 往往几乎不加速，还更难调试 |

#### JS 对照

JS 主线程**没有**「随便开共享内存线程」这种日常写法；重活更多走 Worker。  
Python 多线程在 I/O 场景很常见，但共享内存带来的竞态，是前端同学要补的课。

```text
JS：默认隔离（Worker 用 postMessage）
Python 线程：默认共享 → 方便 + 危险
```

---

### 3.3 多进程（multiprocessing）

#### 为什么需要多进程？

当你的瓶颈是**纯 Python CPU**（大文本清洗、重正则、复杂特征计算），线程往往帮不上忙（GIL）。  
多进程 = 多个解释器进程，**可绕过 GIL** 做 CPU 并行。

#### 怎么理解

- 每个进程有自己的内存空间（更隔离，也更贵）
- 进程间通信（队列、管道、共享内存）要序列化/拷贝，有成本
- 适合：解析大量文本、CPU 重计算  
- Agent **主路径**较少见（主路径多是 HTTP）；**数据预处理 / 建库 / 离线批处理**更常见

高层 API：`concurrent.futures.ProcessPoolExecutor`。

#### 跑一下（只建立直觉：CPU 任务才值得）

```python
# 示意：CPU 密集时才考虑进程池
# Windows 下进程入口常需 if __name__ == "__main__": 保护

from concurrent.futures import ProcessPoolExecutor


def cpu_bound(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


if __name__ == "__main__":
    nums = [2_000_000, 2_000_000, 2_000_000, 2_000_000]
    with ProcessPoolExecutor(max_workers=4) as pool:
        print(list(pool.map(cpu_bound, nums)))
```

对照心智（不必在本章纠结微基准）：

```text
纯 Python 累加百万次：
  多线程 ≈ 常常不更快（GIL）
  多进程 ≈ 才可能接近按核数加速（仍有启动/序列化开销）
```

#### 易错点

| 错法 | 说明 |
|------|------|
| 为了「看起来专业」无脑上多进程 | 调试、部署、内存都更痛；I/O 场景往往不值 |
| 在进程间来回传超大对象 | 序列化成本可能吃掉并行收益 |
| 忘记 `if __name__ == "__main__":`（Windows） | 可能无限重生进程 |

#### JS 对照

```text
Web Worker / Node worker_threads：
  - 不共享随意内存
  - 用消息传递
≈ Python 多进程的「隔离 + 通信」哲学（比多线程更像）
```

---

### 3.4 异步（asyncio）——地图级，不展开细节

#### 为什么异步会成为 Agent 默认选项？

Agent 热路径几乎全是：

```text
HTTP → LLM
HTTP → Tool
HTTP → 向量库 / DB
```

这是**大量网络 I/O**。  
异步模型用单线程事件循环 + 协作式多任务，用很少的线程数撑起很高的并发等待。

#### 怎么理解（本章只要这张地图）

- 通常：**单线程** + 事件循环 + `async/await` 协作让出
- 适合：大量网络 I/O、高并发连接
- 要求：调用链基本异步化（同步阻塞会卡住循环）
- Agent / FastAPI / `httpx.AsyncClient` 是主战场

本章**不**展开：

- `async def` / `await` 语法细节  
- Task / `gather` / 取消 / Semaphore  

这些是模块 05 的正文。你现在只要能说：

> 「同时等很多 HTTP → 优先考虑 asyncio；下一模块学怎么写。」

#### 跑一下（用「同步对比」感受问题，而不是学 API）

下面这段**故意不用 asyncio**，只对比「串行等」和「线程重叠等」——先建立收益直觉：

```python
import time
from concurrent.futures import ThreadPoolExecutor


def fake_http(sec: float) -> str:
    time.sleep(sec)
    return "ok"


def many_sequential(n: int = 5) -> None:
    for _ in range(n):
        fake_http(0.1)


def many_threaded(n: int = 5) -> None:
    with ThreadPoolExecutor(max_workers=n) as pool:
        list(pool.map(fake_http, [0.1] * n))


for label, fn in [("sequential", many_sequential), ("threaded", many_threaded)]:
    t0 = time.perf_counter()
    fn()
    print(label, "elapsed ≈", round(time.perf_counter() - t0, 3), "s")
```

模块 05 里，你会看到 asyncio 版在 I/O 场景也能把时间压到「约等于最慢那个」，且通常更适合「成千上万路等待」。

#### 易错点（提前打预防针）

| 错法 | 后果 |
|------|------|
| 在异步函数里直接 `time.sleep` / 同步 `requests` | 事件循环卡住，其它协程也不动 |
| 以为写了 `async def` 就自动并发 | 若仍一个一个 `await`，还是串行 |
| 全项目一半同步一半异步却无边界 | 到处 `run_until_complete` / 嵌套循环，极难维护 |

#### JS 对照

```javascript
// 前端最像 asyncio 的日常模型
async function main() {
  const [a, b] = await Promise.all([fetch(u1), fetch(u2)])
}
```

| JS | Python（下章） |
|----|----------------|
| `async function` | `async def` |
| `await` | `await` |
| `Promise.all` | `asyncio.gather`（近似同类问题） |
| 主线程被同步死循环卡住 | 事件循环被阻塞调用卡住 |

---

### 3.5 对照表（选型速查）

| 需求 | 更优选项 |
|------|----------|
| 同时等很多 HTTP | asyncio（模块 05） |
| 调用阻塞库又不想改 | 线程池 |
| 压榨多核 CPU | 多进程 / 本地扩展 |
| 简单脚本偶发并发 | `concurrent.futures` |
| 三步强依赖流水线 | 保持串行（步骤内可再并发） |

---

## 4. 必掌握：GIL 直觉

### 4.1 GIL 是什么、限制什么

#### 为什么前端背景特别容易误判 GIL？

在 JS 里，「单线程」是默认故事；你很少指望「开几个线程把 for 循环算得更快」。  
到了 Python，看到 `threading` 关键字，很容易以为：「多线程 = 多核加速」。  
**CPython 的 GIL 会打破这个直觉。**

#### 怎么理解

CPython 有 **Global Interpreter Lock（全局解释器锁）**：

> 同一时刻，通常只有一个线程在执行 Python 字节码。

含义拆开记：

1. **CPU 密集多线程 ≠ 线性加速**（多个线程抢同一把 GIL）  
2. **I/O 等待时**线程常释放 GIL，其它线程可以跑 → 多线程对阻塞 I/O 仍有用  
3. 想要 CPU 真并行：多进程 / 其它运行时 / native 扩展（C/Rust 等在扩展内可释放 GIL）

不要把 GIL 理解成「Python 不能并发」——  
它限制的是**并行执行 Python 字节码**，不是禁止多任务推进。

了解即可：CPython 3.13+ 有实验性 free-threaded（无 GIL）构建，生态与默认安装仍在演进；**本教程默认仍按「有 GIL」心智**选型。

#### 跑一下（I/O vs CPU 的对比实验）

```python
import time
from concurrent.futures import ThreadPoolExecutor


def io_task(_: int) -> int:
    time.sleep(0.2)  # 等待时往往释放 GIL
    return 1


def cpu_task(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


def run_pool(fn, args, workers: int) -> float:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(fn, args))
    return time.perf_counter() - t0


print("io  1 worker :", round(run_pool(io_task, range(4), 1), 3), "s")
print("io  4 workers:", round(run_pool(io_task, range(4), 4), 3), "s")
# I/O：4 workers 通常明显接近 0.2s，而不是 0.8s

N = 1_500_000
print("cpu 1 worker :", round(run_pool(cpu_task, [N] * 4, 1), 3), "s")
print("cpu 4 workers:", round(run_pool(cpu_task, [N] * 4, 4), 3), "s")
# CPU：4 workers 常常几乎不更快（GIL）；不同机器略有波动
```

读结果时抓住方向即可：

```text
I/O 等待 + 多线程 → 常有收益
纯 Python CPU + 多线程 → 别指望线性加速
```

#### 易错点

| 错法 | 纠正 |
|------|------|
| 「有 GIL 所以别用线程」 | I/O 场景线程仍然非常常用 |
| 「有 GIL 所以 Python 不能并发」 | 并发（多任务推进）可以；字节码并行受限 |
| 「numpy/某些 C 扩展也很慢」 | 扩展内部可能释放 GIL；纯 Python 循环才是典型受害者 |
| 「3.13 无 GIL 了，不用学这些」 | 默认构建与生态仍在演进；选型心智先按有 GIL |

#### JS 单线程 / Worker 对照

```text
JS 主线程：
  本来就单线程执行 JS；用事件循环重叠 I/O
  重 CPU → Worker

CPython 多线程：
  看起来像「多线程」，但字节码层仍常串行（GIL）
  重 CPU → 多进程 / 扩展，而不是堆线程
```

口诀：

> **GIL 让「线程加速 CPU」在 CPython 里经常失效；但「线程重叠 I/O」仍然成立。**

---

### 4.2 GIL 与三种模型的关系（串起来）

```text
多线程：
  I/O ✅ 常常值得
  纯 Python CPU ❌ 别指望

多进程：
  绕过 GIL，CPU ✅（付进程开销）

异步：
  不是用来绕 GIL 的
  用来高效地并发等待 I/O
```

---

## 5. 建议掌握：如何选型（Agent 清单）

### 5.1 决策清单

#### 为什么要有清单，而不是「感觉选」？

Agent 代码里最常见的失败模式不是「不会写 gather」，而是：

- 该重叠的 I/O 写成了串行  
- 不该并行的依赖链硬并行  
- 同步 SDK 堵死事件循环  
- 用多进程「优化」其实是网络等待  

清单把选择变成可重复的问答。

#### 怎么理解（按顺序问）

```text
1) 主要是等 LLM / HTTP / DB？
     → 优先 asyncio（下一模块细学）

2) 某库只有同步客户端，短期不想改？
     → 线程池包一层（或 to_thread），或找异步替代

3) 大量 CPU 预处理（本地重计算）？
     → 多进程；或预处理离线做完，别放在请求热路径

4) 需要共享复杂可变状态？
     → 先避免；改用队列传消息，少共享内存 + 少裸锁

5) 步骤之间有严格数据依赖？
     → 保持串行；只在「无依赖的兄弟任务」上并发
```

经验法则：

> **默认异步 I/O；CPU 重活单独拿出去；少在热路径上裸加锁共享状态。**

#### 跑一下（把练习 B4 变成「对照表」）

| 场景 | 选项 | 理由 |
|------|------|------|
| 同时调 10 个 LLM embedding HTTP | asyncio | 典型可重叠网络 I/O |
| 同步 SDK 且短期不想改 | 线程池 | 用线程释放等待，避免重写整条链 |
| 对 200MB 文本做 CPU 正则重处理 | 多进程（或离线） | 纯 CPU，要绕 GIL |
| 检索→拼 prompt→生成 | 保持串行 | 强依赖；可在「检索多源」子步内并发 |

#### 易错点

| 错法 | 更好做法 |
|------|----------|
| 全链路默认多进程 | 先确认是不是 CPU 瓶颈 |
| 异步项目里随手调用同步 HTTP | `to_thread` / 线程池隔离，或换 AsyncClient |
| 为了共享状态上很多锁 | 优先消息传递、不可变快照、单写者 |

#### JS 对照（选型语感）

| 你在前端会怎么做 | Python Agent 类比 |
|------------------|-------------------|
| 多个 `fetch` 一起等 | asyncio / 并发 I/O |
| 同步 SDK 堵主线程 | 线程池逃生（或换异步库） |
| 重计算丢 Worker | 多进程 / 离线任务 |
| 严格的 `await a; await b` 依赖 | 保持串行 |

---

### 5.2 混合架构草图（挑战题 C1 的地图）

真实 Agent 常常是混合，而不是纯一种：

```text
asyncio 事件循环（编排）
  ├─ await 多个异步 HTTP（LLM / 工具）
  ├─ 遇到同步 SDK → await asyncio.to_thread(sync_call, ...)
  └─ 偶尔 CPU 重活 → 丢进程池 / 独立 worker 服务
```

本章只要能画出边界；`to_thread` / Task 细节见模块 05。

---

## 6. 了解即可：无锁结构

#### 为什么会听到「无锁」？

高并发中间件（队列、缓存、调度器）常讨论：

- 无锁队列  
- 原子操作  
- CAS 等算法  

目标是：少用互斥锁，降低线程互相等待。

#### 怎么理解（应用层先记住什么）

对写 Agent / 业务服务的你：

1. **优先避免共享可变状态**（最有效）  
2. 需要协作时：用**队列 + 消息**（谁拥有数据谁改）  
3. 真要共享：用标准库里已经设计好的结构 / 锁，不要自己发明无锁算法  

应用层口诀：

> **队列与不可变消息传递，优先于手写无锁。**

「了解即可」的边界：

```text
知道有这些词，知道它们为高并发基础组件服务
≠ 本章要你实现 lock-free 队列
```

#### 跑一下（用「有锁共享」反衬「消息传递」）

反例（共享可变状态，需要保护）：

```python
import threading

counter = 0
lock = threading.Lock()


def bump(n: int) -> None:
    global counter
    for _ in range(n):
        with lock:  # 没有锁时，多线程下 counter 可能错
            counter += 1


threads = [threading.Thread(target=bump, args=(50_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)  # 有锁时应为 200_000
```

更稳的应用层方向（示意）：

```text
worker A 只通过 queue.put(msg)
worker B 只 queue.get() 后处理
各自本地状态，不直接改对方的 dict
```

#### 易错点

- 以为「用了无锁结构 = 业务自动正确」：算法正确性极难，业务层别炫技。  
- 在 Agent 热路径用复杂共享内存：排障成本通常高于收益。

#### JS 对照

```text
JS Worker：postMessage / structured clone
→ 天然偏向「消息传递，而不是共享可变对象」

这正是 Python 应用层更值得模仿的方向
（尤其是多进程 / 多服务时）
```

---

## 7. 最小代码直觉（同步对比）

这一节把前面的「能跑的最小对照」收束到一处，方便直接对着练习 B2 / A1。

#### 为什么要自己测耗时？

只看理论，你会以为「并发 = 更快」。  
自己用 `time.perf_counter()` 跑一遍，身体才会记住：

- 独立 I/O：可接近 max  
- 有依赖：仍接近 sum  
- CPU + 线程：可能几乎没变化  

#### 怎么理解（两套读结果方式）

```text
threaded()           → as_completed：完成顺序，别写死 == ["a", "b"]
threaded_in_order()  → 按提交 Future 的顺序取 result
断言时：set(result) == {"a", "b"} 或直接用 in_order 版
```

#### 跑一下

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def fake_io(name: str, sec: float) -> str:
    time.sleep(sec)  # 假装网络
    return name


def sequential() -> list[str]:
    return [fake_io("a", 0.2), fake_io("b", 0.2)]


def threaded() -> list[str]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fake_io, n, 0.2) for n in ("a", "b")]
        # as_completed：按完成顺序；不要假设 == ["a", "b"]
        return [f.result() for f in as_completed(futs)]


def threaded_in_order() -> list[str]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fake_io, n, 0.2) for n in ("a", "b")]
        return [f.result() for f in futs]  # 按提交顺序等结果


if __name__ == "__main__":
    for label, fn in [
        ("sequential", sequential),
        ("threaded", threaded),
        ("threaded_in_order", threaded_in_order),
    ]:
        t0 = time.perf_counter()
        result = fn()
        dt = time.perf_counter() - t0
        print(f"{label:18} result={result}  elapsed≈{dt:.3f}s")
```

自己测耗时：线程版应明显更快（都在 `sleep`）。  
进阶：把 `fake_io` 换成「纯 Python 累加」，再看线程版是否还更快——这就是 GIL 直觉。

#### 易错点

| 错法 | 说明 |
|------|------|
| 只打印结果不看耗时 | 看不见并发收益 |
| 用 `time.time()` 也行，但教学统一 `perf_counter` | 更适合测短间隔 |
| 在 notebook 里多次运行进程池却不看平台差异 | Windows / 交互环境对进程入口更敏感 |

#### JS 对照

```javascript
console.time("all")
await Promise.all([sleep(200), sleep(200)])
console.timeEnd("all")  // 约 200ms，不是 400ms
```

和本章 `threaded` 版同一类现象：**独立等待可重叠**。

---

## 8. 常见坑

把全章易错点收成排障清单（写代码前扫一眼）：

1. **在异步里调用长时间阻塞函数** → 卡住事件循环（模块 05 会反复练）  
2. **多线程改同一 list/dict 不加保护** → 竞态、偶发错乱  
3. **为了“快”无脑上多进程** → 调试/内存/序列化成本爆炸  
4. **把并行当银弹** → 任务本身串行依赖就重叠不了  
5. **用多线程优纯 Python CPU** → 常被 GIL 挡住，误判「并发没用」  
6. **混淆 as_completed 顺序与提交顺序** → 测试断言偶发失败  
7. **共享复杂可变状态靠一堆锁硬撑** → 优先队列与消息传递  

---

## 9. 练习指引

[`exercises/04-systems-basics/03-concurrency-models.md`](../../exercises/04-systems-basics/03-concurrency-models.md)

建议路径：

1. **B1** 先写并发 vs 并行的例子（生活 + Agent）  
2. **B2** 跑通第 7 节串行 vs 线程池计时  
3. **B3** 结合第 4 节 GIL 实验做判断  
4. **B4** 对照第 5 节清单选型  
5. （建议）**A1 / A2**：`map` 与竞态  
6. （可选）**C1**：同步工具 + 异步编排草图  

playground 目录：`playground/04-systems-basics/03-concurrency-models/`

---

## 10. 小结与下一站

### 自检

- [ ] 能区分并发 / 并行，并各举 Agent 例子  
- [ ] 能说明线程 / 进程 / 异步各自擅长什么  
- [ ] 能说明 GIL 对「线程 + CPU」与「线程 + I/O」的不同影响  
- [ ] 能给 Agent I/O 场景选出异步 / 线程池 / 多进程 / 串行  
- [ ] 知道应用层优先消息传递，而不是先上无锁  

### 把地图带去下一模块

```text
本章：选哪条路、为什么
模块 05：asyncio 这条路具体怎么走
  - async / await
  - 事件循环、Task、gather
  - 超时、取消、限流
  - 阻塞调用的危害与 to_thread
```

### 下一章

[`04-dsa-essentials.md`](./04-dsa-essentials.md) —— 数据结构与算法精要（工程选型向，不走刷题主线）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[网络与 HTTP](./02-network-http.md)
- 下一章：[数据结构与算法精要](./04-dsa-essentials.md)
- 下一模块预告：[asyncio 基础](../05-async-python/01-asyncio-fundamentals.md)
