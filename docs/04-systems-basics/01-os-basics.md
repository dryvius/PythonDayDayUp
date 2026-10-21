# 操作系统基础

> 所属模块：`04-systems-basics` · 计算机与服务端基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有浏览器/Node 经验可更快；进程/线程、阻塞与超时、fd 泄漏建议动手踩一遍）  
> 对应练习：[`exercises/04-systems-basics/01-os-basics.md`](../../exercises/04-systems-basics/01-os-basics.md)

## 本章定位

- **模块目标**：补齐前端背景下的系统直觉，避免一知半解。
- **本章角色**：建立进程/线程、内存与 I/O、文件描述符、调度与阻塞的心智模型，用来解释 Agent「卡住、超时、占内存、打不开太多连接」等现象。
- **你的优势**：浏览器多进程、JS 单线程事件循环、`fetch` 超时这些经验可以直接对照；重点盯住「阻塞在等什么」以及「打开的东西占名额」。
- **目标不是**：成为内核工程师；够用、能对话、能排障即可。

## 学习目标（学完应能做到）

1. 分清进程与线程，说清它们如何共享/隔离资源。
2. 用「CPU 密集 vs I/O 密集」解释为何 Agent 常在等网络，以及为何超时/异步有意义。
3. 对文件描述符 / 句柄有直觉（文件、socket 都占名额），能联系 `with` 与连接池。
4. 理解阻塞、睡眠、忙等与调度的基本含义；能解释「卡住」和「超时」在 OS 层发生了什么。
5. 完成课后练习，分清必掌握 / 建议掌握 / 了解即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | 进程/线程、内存与 I/O、文件描述符直觉 | 能讲清、能联系排障、能做小实验 |
| **建议掌握** | 调度与阻塞（含超时心智） | 能解释「为什么卡住 / 为什么要设超时」 |
| **了解即可** | 内核细节（系统调用、页表、中断等） | 建立地图，不深挖 |

---

## 1. 为什么要学（和 Agent 的关系）

#### 为什么需要操作系统直觉？

Agent 运行时典型画像：

```text
等 LLM HTTP 响应（网络 I/O）── 常常是秒级甚至更久
等数据库 / 向量库（网络 I/O）
本地解析 JSON、拼 prompt（少量 CPU）
写日志、读文件、加载语料（磁盘 I/O）
一次打开很多连接 / 文件（占 fd / 句柄）
```

大多数时间在 **等 I/O**，不是在算矩阵。  
所以你会听到：异步、超时、连接池、文件句柄耗尽、进程内存涨——这些词都建立在 OS 概念上。

#### 没有这些概念时，排障会长这样

```text
「Agent 卡住了」→ 不知道是在等网络、等磁盘，还是死锁/忙等
「内存好像很大」→ 不知道是 history 无限涨，还是一次加载了整库
「Too many open files」→ 不知道文件/socket 都占同一类名额
「设了 timeout 还是挂」→ 不知道超时作用在哪一层、阻塞在哪个线程
```

有了本章地图，你会先问：

```text
1. 现在卡在哪个进程/线程？在等什么资源？
2. 是 CPU 在忙，还是线程阻塞在 I/O？
3. 打开了多少文件/连接？有没有及时释放？
4. 有没有超时？超时之后谁负责取消/清理？
```

#### 本章要练的四种能力

1. **定位资源边界**：进程隔离什么、线程共享什么
2. **区分等待类型**：CPU 忙算 vs I/O 阻塞 vs 主动 sleep
3. **管好打开的东西**：文件、socket、客户端 → fd/句柄
4. **用超时保护 Agent**：不让一次 LLM/工具调用无限占住执行流

可以先记一句：

> OS 基础不是背名词，而是给「卡住、超时、占资源」找到可验证的解释。

#### 前端 / 浏览器对照（先建立地图）

| 你在前端熟悉的现象 | 本章对应概念 |
| --- | --- |
| 标签页崩了不影响别的站 | 进程隔离 |
| JS 主线程卡死，UI 不响 | 单执行流被同步长任务占住 |
| `await fetch` 在等网络 | 线程/协程在做 I/O 等待 |
| `AbortSignal` / 请求超时 | 不愿无限阻塞，主动设上限 |
| 打开太多 WebSocket / 文件句柄类错误 | fd / 句柄耗尽 |

下一章网络、再后面的并发与 asyncio，都会反复用到这些词。

---

## 2. 必掌握：进程与线程

这一节会刻意写细——后面内存、I/O、阻塞、并发选型都建立在「谁在执行、资源归谁」之上。

### 2.1 进程（Process）：资源容器

#### 为什么需要进程这个概念？

操作系统不能让所有程序共用一块乱糟糟的内存。它用**进程**做隔离单位：每个进程有自己的地址空间、打开的文件表、权限与生命周期。  
对你写 Python 来说：一次 `python script.py`，通常就是启动**一个进程**（里面再跑解释器）。

#### 怎么理解

把进程想成「带围墙的小房子」：

```text
进程 = 资源容器
├── 独立虚拟内存地址空间
├── 打开的文件 / socket 表（后面 §4）
├── 至少一个线程（执行流）
└── PID（进程 ID）等元数据
```

关键性质：

| 性质 | 含义 | 对 Agent 的启示 |
| --- | --- | --- |
| 内存默认隔离 | A 进程改不了 B 进程的变量 | 子进程挂了，主进程数据还在；反之也难「直接共享 dict」 |
| 通信要显式 | 管道、队列、共享内存、网络 | 多进程 Agent worker 要设计 IPC / Redis / HTTP |
| 崩溃边界 | 一进程崩，通常不直接拖垮另一进程 | 可把危险工具放进子进程（沙箱思路的简化版） |

#### 怎么验证

每次运行脚本，OS 都会分配一个 PID；进程结束，PID 可被复用，但「这一次运行」就是一个独立容器。

#### 跑一下

```python
import os
import sys
from pathlib import Path

print("pid =", os.getpid())
print("ppid =", os.getppid())  # 父进程，常见是终端 / IDE
print("cwd =", Path.cwd())
print("executable =", sys.executable)
```

连跑两次，观察：

- `pid` 几乎总会变 → 每次是新进程
- `cwd` / `executable` 往往不变 → 工作目录与解释器路径由启动方式决定

Windows 上同样有 PID；只是底层实现与 Unix 不同，心智模型「一次运行 = 一个进程容器」仍然成立。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为「开两个终端跑同一脚本」共享内存 | 不共享；两个独立进程、两份变量 |
| 以为 `import` 会跨进程自动同步状态 | 每个进程各自有一份模块全局状态 |
| 把「电脑上的 Python」当成一个永远存在的进程 | 每次启动脚本通常是新进程；IDE 调试器另算 |

#### 前端 / 浏览器对照

| 浏览器 | OS / Python |
| --- | --- |
| 浏览器进程 / 渲染进程隔离 | 进程地址空间隔离 |
| 一个标签出问题尽量不影响别的 | 子进程崩溃的边界 |
| 扩展、插件常跑在独立上下文 | 用进程换安全与隔离（代价是通信更重） |

---

### 2.2 线程（Thread）：进程里的执行流

#### 为什么需要线程？

一个进程若只有一条执行流，遇到「等网络 2 秒」就会整段卡住，什么都干不了。  
线程让**同一个进程**里可以有多条执行流：一条在等 HTTP，另一条仍可能跑别的逻辑（是否真能并行算，还受 GIL 等限制，见本模块并发章）。

#### 怎么理解

```text
进程（房子）
├── 线程 A：正在 call_llm，阻塞等响应
├── 线程 B：写日志 / 心跳
└── 共享：堆上的对象、模块全局变量、打开的 fd 表
```

| 维度 | 进程 | 线程 |
| --- | --- | --- |
| 是什么 | 资源容器 | 执行流 |
| 内存 | 默认隔离 | **同进程共享** |
| 创建代价 | 相对重 | 相对轻 |
| 崩坏影响 | 边界更清晰 | 一线程写坏共享数据，全家遭殃 |
| 通信 | 要 IPC | 直接读写共享对象（也更易竞态） |

一句话：

> 进程管「有哪些资源」；线程管「谁在这条时间线上往前跑」。

#### 怎么验证

Python 标准库 `threading` 可以在同一进程里再开执行流。先建立「同 pid、多 tid」的直觉即可（选型细节留给并发章）。

#### 跑一下

```python
import os
import threading
import time


def worker(name: str) -> None:
    print(f"{name}: pid={os.getpid()} tid={threading.get_ident()}")
    time.sleep(0.2)
    print(f"{name}: done")


print("main:", os.getpid(), threading.get_ident())
t = threading.Thread(target=worker, args=("worker-1",))
t.start()
t.join()
```

你会看到：

- `pid` 相同 → 仍在同一进程
- `tid`（`threading.get_ident()`）不同 → 多条执行流
- `sleep` 期间线程在**等待**，不占满 CPU 做有用计算（见 §5）

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把线程当成「自动并行算力」 | CPU 密集在 CPython 上常受 GIL 限制；I/O 等待才更受益 |
| 多线程随便改同一个 `list`/`dict` | 竞态：丢更新、偶现 bug |
| 以为「开了线程就不会卡住」 | 若所有线程都阻塞在同一个慢调用上，整体照样慢 |

#### 前端 / 浏览器对照

| 前端概念 | 可粗对照 |
| --- | --- |
| JS 主线程 + 事件循环 | 更像「一条执行流 + 异步 I/O 回调/微任务」 |
| Web Worker | 额外执行流；**不**随意共享内存（要用 postMessage） |
| `Atomics` / `SharedArrayBuffer` | 少见的真共享；默认隔离才是常态 |

注意：浏览器 Worker 的「默认不共享」和 OS 线程的「默认共享」正好相反——别把两套模型混成一句「线程就是 Worker」。

---

### 2.3 共享与隔离：排障时怎么想

#### 为什么要把这张表钉死？

Agent 里「多开一个 worker」「用线程跑工具」「子进程跑沙箱」都是资源边界决策。边界选错，轻则性能差，重则状态错乱。

#### 怎么理解（速查）

| 资源 | 同进程多线程 | 多进程 |
| --- | --- | --- |
| Python 对象 / 全局变量 | 共享（需同步） | 不共享（要序列化/IPC） |
| 文件描述符表 | 共享同一张表的视图（细节因 OS 而异，先记「都占名额」） | 各自一份 |
| 崩溃 | 可能拖垮整个进程 | 通常止于该进程 |
| 适合 | I/O 等待重叠、轻量后台任务 | CPU 并行、隔离危险代码 |

#### 和 Agent 的直接关系

```text
单进程同步 Agent：
  一次 LLM 调用阻塞 → 整条对话流水线停住

单进程 + 线程/异步：
  等待网络时切换去做别的（或重叠多个等待）

多进程 worker：
  隔离崩溃 / 绕开 GIL 做重计算；通信与部署更重
```

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 「隔离」和「性能」一把梭 | 隔离换安全，通信换成本；没有免费午餐 |
| 在线程里假设「赋值一定原子」 | 复合操作（读-改-写）不是原子的 |
| 把 GIL 当成「没有竞态」 | GIL 不保护你的业务不变量；仍要锁或队列 |

#### 预告：GIL

CPython 有 **GIL**（全局解释器锁）：同一时刻通常只有一个线程在执行 Python 字节码。  
这对 **CPU 密集**多线程帮助有限；对 **阻塞 I/O** 等待时，线程仍常能释放 GIL，让别的线程跑。  
细节见本模块 [`03-concurrency-models.md`](./03-concurrency-models.md)，本章先建立「线程 ≠ 自动多核加速」即可。

---

### 2.4 小实验：一次运行就是一个进程

#### 为什么要做这个实验？

很多人口头知道「进程」，但没把「每次 `python xxx.py`」和 PID、工作目录、解释器路径连起来。排障时「到底跑的是哪份 Python」全靠这个直觉。

#### 跑一下（对应练习 B1）

```python
# playground/04-systems-basics/01-os-basics/show_process.py
import os
import sys
from pathlib import Path

print("pid =", os.getpid())
print("cwd =", Path.cwd())
print("python =", sys.executable)
```

```bash
python show_process.py
python show_process.py
```

笔记里写：两次 `pid` 是否不同？若用 IDE 运行与终端运行，`cwd` / `executable` 是否可能不同？

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 在错误目录运行，相对路径全乱 | 进程有 `cwd`；文件路径相对它解析 |
| 系统 Python 与 venv Python 搞混 | 看 `sys.executable`，不要凭感觉 |

---

## 3. 必掌握：内存与 I/O

Agent 的「慢」和「胖」大多落在这两类资源上：内存装太多，或线程堵在 I/O 上。

### 3.1 内存：进程看到的是虚拟地址空间

#### 为什么需要「虚拟内存」这层说法？

你在 Python 里 `x = [0] * 10_000_000`，并不是「直接独占一整块物理 RAM 的裸操作」。进程拿到的是**虚拟地址空间**；OS 再映射到物理页。  
教学上够用的结论：

```text
你的变量 / 对象 → 落在进程的堆/栈等区域（虚拟地址）
物理页不够 → OS 可能换页、压缩、或让分配失败（表现因系统而异）
Python 对象还有解释器开销 → 同样「100 万个小对象」比「一大块 bytes」更吃内存
```

不必背页表结构；要有「进程内存账本由 OS 管，Python 对象有额外税」的直觉。

#### 怎么理解（Agent 常见压力源）

| 压力源 | 典型表现 | 缓解方向 |
| --- | --- | --- |
| 消息 history 无限追加 | RSS 缓慢爬升 | 截断、摘要、滑动窗口 |
| 一次 `read()` 整本语料 | 峰值内存尖刺 | 流式 / 分页 / 分块 |
| 向量或文档「全进内存」 | 机器换页、变慢 | 外置索引、按需加载 |
| 缓存只加不删 | 长时间运行后 OOM | TTL、上限、LRU |

实践口令：

```text
上下文截断、流式处理、分页读取、不要 list(巨大生成器)
```

#### 怎么验证（可选，对应挑战题 C1）

若环境能装 `psutil`：

```python
import psutil
import os

proc = psutil.Process(os.getpid())
print("before MB =", proc.memory_info().rss / 1024 / 1024)
data = [i for i in range(5_000_000)]
print("after MB =", proc.memory_info().rss / 1024 / 1024)
print(len(data))
```

装不了就跳过：用任务管理器 / `htop` 观察也可。重点是「大对象分配前后对比」，不是精确到字节的 profiling。

#### 跑一下（不依赖第三方）

```python
import sys

a = []
print("empty list", sys.getsizeof(a))

a.append(1)
print("one int ref", sys.getsizeof(a))

# getsizeof 只量「容器本身」，不含元素指向的对象——这是常见误解
s = "x" * 1_000_000
print("str approx", sys.getsizeof(s))
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用 `sys.getsizeof(list)` 当总占用 | 漏算元素对象；只是下限直觉 |
| `history.append` 永不裁剪 | 长会话 Agent 内存与 token 费用双涨 |
| `list(huge_generator)`「图方便」 | 瞬间物化，峰值爆炸 |

#### 前端对照

| 前端 | Python / Agent |
| --- | --- |
| 大 JSON 一次 `JSON.parse` 卡主线程 | 大文件一次读入内存 |
| 虚拟列表 / 分页 | 流式读、分块处理 |
| 闭包误持有大对象导致泄漏 | 全局缓存、未清的 history 引用 |

---

### 3.2 I/O：程序与外界交换数据

#### 为什么要把 I/O 单独拎出来？

CPU 再快，等磁盘、等网卡时线程也只能干等（除非用多线程/异步把等待重叠起来）。Agent 延迟的主因经常是 **I/O 等待**，不是 JSON 解析那几毫秒。

#### 怎么理解

| 类型 | 例子 | Agent 里 |
| --- | --- | --- |
| 网络 I/O | HTTP 调 LLM、查向量库 | **最常见瓶颈** |
| 磁盘 I/O | 读文档、写日志、会话落盘 | RAG 建库、审计日志 |
| 终端 I/O | `print`、交互输入 | 调试；生产应收敛到日志系统 |

心智图：

```text
你的代码 ──系统调用──▶ OS ──▶ 网卡/磁盘/终端
              ▲
              └── 在结果回来前，线程可能处于「阻塞」状态
```

#### 阻塞 I/O 是什么感觉？

**阻塞 I/O**：调用发出去后，这条执行流在结果回来之前，不能继续跑后面的 Python 语句（除非你用别的线程/异步任务去干别的事）。

```python
import time
import urllib.request

# 示意：同步 HTTP（教学用；生产多用 httpx/requests 并设超时）
# 在响应返回前，当前线程就卡在这一行
# resp = urllib.request.urlopen("https://example.com", timeout=5)

time.sleep(0.5)  # 同样是「当前线程等待」，只是等的是定时器
print("after wait")
```

`time.sleep` 不是网络，但训练的是同一种感觉：**当前执行流停在这里**。

#### 跑一下：串行等待的总耗时（对应练习 B2）

```python
import time


def sleep_n(seconds: float) -> None:
    time.sleep(seconds)


t0 = time.perf_counter()
sleep_n(0.3)
sleep_n(0.3)
elapsed = time.perf_counter() - t0
print(f"elapsed ≈ {elapsed:.2f}s")  # 大约 0.6s，不是 0.3s
```

笔记写一句：这两段时间里，CPU 多半在**等**，不是在狂算。  
若改成「能重叠等待」的并发模型（线程/异步，见后续章），总墙钟时间才可能接近 `max(各段等待)`。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把「电脑风扇响 / 卡」全怪 Python 语法慢 | 可能是同步串行在等网络 |
| 以为 `print` 很多等于 I/O 主瓶颈 | Agent 主路径通常是 HTTP；日志要节流但别误判主因 |
| 不计超时地同步 `urlopen` / `requests.get` | 对端挂起 → 你的 worker 永久阻塞 |

#### 前端对照

| 前端 | 后端 / Agent |
| --- | --- |
| `await fetch` | 同步 HTTP 阻塞线程；或 async await 挂起协程 |
| 主线程里同步 XHR（反模式） | 同步串行调 LLM（会拖垮吞吐） |
| 骨架屏 / loading | 超时、重试、降级文案 |

---

### 3.3 CPU 密集 vs I/O 密集

#### 为什么要分清楚？

并发手段选错，全靠这张分类表：

| 类型 | 特征 | 例子 | 常见策略方向 |
| --- | --- | --- | --- |
| **I/O 密集** | 大量时间在等外界 | LLM HTTP、DB、读大文件 | 异步 / 多线程重叠等待 |
| **CPU 密集** | 大量时间在算 | 大循环、重解析、图像特征 | 多进程 / 本地扩展 / 缩小计算量 |

Agent 主对话环：**偏 I/O 密集**。  
数据预处理、大批量本地解析：才更常碰到 CPU 密集。

#### 跑一下（对应练习 A1）

```python
import time


def cpu_bound(n: int = 5_000_000) -> int:
    s = 0
    for i in range(n):
        s += i
    return s


def io_wait(seconds: float = 0.5) -> None:
    time.sleep(seconds)


t0 = time.perf_counter()
cpu_bound()
print("cpu_bound", time.perf_counter() - t0)

t1 = time.perf_counter()
io_wait()
print("io_wait", time.perf_counter() - t1)
```

文字结论（写进笔记）：

- `cpu_bound`：线程在跑字节码，多线程在 CPython 上未必线性加速（GIL）
- `io_wait`：线程在阻塞等待，适合用并发把多段等待叠起来

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 凡慢就上多线程 | CPU 密集可能几乎不涨；还引入竞态 |
| 凡慢就上多进程 | I/O 场景杀鸡用牛刀，内存与通信成本高 |
| 把「JSON 解析」当成主瓶颈而不测 | 先看墙钟时间花在 await/HTTP 还是本地循环 |

---

## 4. 必掌握：文件描述符直觉

### 4.1 fd / 句柄：打开的东西占名额

#### 为什么需要这个概念？

在 Unix-like 上，打开的文件、管道、socket 都会对应一个非负整数 **fd（file descriptor，文件描述符）**。  
Windows 上是 **HANDLE（句柄）** 体系，思想类似：

> 凡是「打开」的东西，都在进程的一张表里占一个名额；用完要释放。

Agent 同时保持太多 HTTP 连接、忘记关文件、泄漏客户端会话，最终都可能撞上：

```text
OSError: [Errno 24] Too many open files
```

（具体文案因平台而异，含义都是「名额用尽」。）

#### 怎么理解

```text
进程
└── 打开文件表
    ├── 0 stdin
    ├── 1 stdout
    ├── 2 stderr
    ├── 3 某个 .txt
    ├── 4 到 api.openai.com 的 socket
    └── ...
```

常见占用者：

| 对象 | 是否占名额 | 备注 |
| --- | --- | --- |
| `open` / `Path.open` | 是 | 忘记 close → 泄漏 |
| TCP / TLS 连接、HTTP 客户端 | 是（底层 socket） | 连接池要有上限与释放 |
| 监听端口的 server socket | 是 | 服务进程长期持有 |
| 已 `close` / 离开 `with` | 归还 | 名额可复用 |

#### 怎么验证

在 Linux/macOS 上可用 `lsof -p <pid>` 或查看 `/proc/<pid>/fd`（教学了解即可）。  
Windows 可用句柄查看工具；Python 层更实用的是：**保证 `with` / 上下文关闭，并给客户端设限**。

#### 跑一下：`with` 归还句柄（对应练习 B3）

```python
from pathlib import Path

path = Path("demo_fd.txt")

with path.open("w", encoding="utf-8") as f:
    f.write("ok\n")
# 离开 with：关闭文件，归还 fd/句柄

with path.open("r", encoding="utf-8") as f:
    print(f.read().strip())  # ok
```

错误示范（注释版，对应练习「不必真制造泄漏」）：

```python
# 错误示范：中途异常可能跳过 close
# f = path.open("w", encoding="utf-8")
# f.write("x")
# raise RuntimeError("boom")  # close 没执行 → 依赖 GC/解释器退出才收
# f.close()

# 正确：用 with / finally，异常也会关
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 循环 `open` 一万次不关 | 很快触达上限（练习 A2 思想实验） |
| 每个请求 `httpx.Client()` 新建且不关 | 连接/fd 堆积 |
| 只关文件、忘了关 DB/HTTP 客户端 | 名额照样涨 |
| 在 `with` 外继续用已关闭句柄 | `ValueError: I/O operation on closed file` |

#### 前端对照

| 前端 | 系统侧 |
| --- | --- |
| 忘记 `URL.revokeObjectURL` | 资源释放习惯 |
| WebSocket 只连不关 | socket 占名额 |
| 浏览器「每主机连接数」限制 | 另一层配额；与 OS fd 上限不同但都是「别无限开」 |

和《上下文管理器》章的联系：`with open` / `async with client` 的核心价值，就是把「归还名额」绑到作用域结束。

---

### 4.2 连接池与「别为每个请求新开世界」

#### 为什么 Agent 特别容易踩？

伪代码反模式：

```text
for message in stream:
    client = 新建 HTTP 客户端()
    await client.post(llm_url, ...)
    # 忘记 aclose / close
```

每一次都新建连接，既慢又耗 fd。更好的方向：

```text
进程内复用一个客户端 / 连接池
设 max_connections、超时
应用退出或 with 结束时统一关闭
```

#### 怎么写（同步示意）

```python
# 示意：生产请按所用库的文档管理生命周期
import httpx

def call_llm(prompt: str) -> str:
    # 演示「每次新建」——能跑，但不适合高并发热路径
    with httpx.Client(timeout=30.0) as client:
        # resp = client.post(...)
        return f"echo:{prompt}"
```

更好的形状（进程级复用，需自行保证关闭时机）：

```python
# 模块级或 lifespan 里创建一次，结束时 close
# client = httpx.Client(timeout=30.0, limits=httpx.Limits(max_connections=100))
```

具体 API 放到网络章 / 异步章；本章只要建立：**连接是有寿命的 OS 资源**。

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 池开无限大 | 把压力转嫁给对端与本机 fd |
| 超时只设「连接」不设「读」 | 连上了但对端不发完，仍可能长期阻塞 |
| 异常路径不关闭 | 与不用 `with` 打开文件是同一类病 |

---

## 5. 建议掌握：调度与阻塞

这一节回答现场最高频的两句：「为什么卡住？」和「超时到底打断了什么？」

### 5.1 调度：看起来同时跑，常常是交错跑

#### 为什么需要调度直觉？

CPU 核有限，可运行的线程可能很多。OS **调度器**按时间片在线程间切换。你感觉「好几个任务同时在跑」，底层经常是：

```text
线程A 跑一小会 → 切换 → 线程B 跑一小会 → …
或
线程A 阻塞等 I/O → 调度器把 CPU 给别人
```

对写业务的人：不必会写调度器，但要知道——

> 「同时」常常是交错；阻塞时线程会让出 CPU，忙等则不会。

#### 怎么理解

| 状态（简化） | 含义 |
| --- | --- |
| 运行 | 正在 CPU 上执行 |
| 就绪 | 想跑，在等被调度 |
| 阻塞 | 等 I/O/锁/事件，暂时不占 CPU 做事 |

Agent worker 调 LLM 时，同步线程多半进入**阻塞**（等 socket 可读），而不是占满核做浮点。

#### 跑一下（感受「等待不占满算力」）

```python
import time

t0 = time.perf_counter()
time.sleep(1.0)
print("slept", time.perf_counter() - t0)
# 这一秒里，该线程基本不在做有用计算；机器还可以干别的
```

对比空转（下一小节）：同样「过了 1 秒」，CPU 占用完全不同。

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 看到多核就以为自己的 Python 线程在线性加速 | 还受 GIL、任务类型影响 |
| 把「调度切换」当成 bug | 正常现象；只有错误同步才会变成活锁/饿死 |

#### 前端对照

浏览器主线程也有「任务队列 + 渲染」；长任务会阻塞输入——类似「一条执行流被占满」。`requestIdleCallback` / 拆分任务 ≈ 主动让出，和「别忙等、别长时间占住」同一家族。

---

### 5.2 阻塞 vs 睡眠 vs 忙等

#### 为什么要三分清？

都叫「卡住」，机制不同，药方不同。

| 方式 | 含义 | CPU | Agent 场景 |
| --- | --- | --- | --- |
| **阻塞** | 等 I/O/锁，线程进入等待 | 低 | `requests.get` 等响应 |
| **睡眠** | 主动 `sleep` 一段时间 | 低 | 重试退避、限速 |
| **忙等** | `while not ready: pass` 空转 | **高** | 几乎总是反模式 |

#### 跑一下：忙等有多糟（短演示）

```python
import time

deadline = time.perf_counter() + 0.3
# 忙等：吃 CPU，还不比 sleep 更「有用」
while time.perf_counter() < deadline:
    pass
print("busy-wait done")

time.sleep(0.3)
print("sleep done")
```

用系统监视器看：前 0.3 秒 CPU 占用通常明显高于 `sleep`。  
生产代码里等条件，应阻塞在队列/`Event`/异步 wait 上，而不是空转。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用忙等「轮询文件是否写完」 | 风扇狂转、费电、抢调度 |
| 把 `sleep` 当取消手段 | `sleep` 只是拖延；不替你关闭连接 |
| 误以为阻塞 = 程序死了 | 阻塞可能是健康等待；要配超时与可观测性 |

---

### 5.3 Agent 超时：我不想无限阻塞在一次调用上

#### 为什么超时是 OS/运行时话题，而不只是「业务参数」？

同步调用 LLM 时：

```text
线程进入阻塞，等待 socket 数据
对端极慢或半开连接 → 你可能永远等下去
该 worker 不再处理别的用户/消息
连接与 fd 一直被占着
```

超时的本质：

> 给这次等待一个上限；到点就放弃（并尽量清理连接），把执行流解放出来。

#### 怎么理解分层

| 层 | 例子 | 作用 |
| --- | --- | --- |
| 连接超时 | connect timeout | 连不上尽快失败 |
| 读/写超时 | read timeout | 连上了但不返回也别傻等 |
| 总超时 | 整次调用 deadline | 含重试时要重新设计预算 |
| 应用层超时 | `asyncio.wait_for` / 任务编排超时 | 取消上层任务（需协作） |

伪代码心智（同步）：

```python
import httpx

def ask_model(prompt: str) -> str:
    # timeout=30：不愿无限阻塞
    with httpx.Client(timeout=30.0) as client:
        # resp = client.post("https://api.example.com/v1/chat", json={...})
        # return resp.json()["content"]
        return f"echo:{prompt}"
```

异步侧（印象即可，模块 05 再实战）：

```python
import asyncio

async def ask_with_budget(coro):
    try:
        return await asyncio.wait_for(coro, timeout=30)
    except TimeoutError:
        # 记日志、返回降级、触发重试策略等
        raise
```

注意：`wait_for` 超时后，被取消的任务能否真正停掉底层 I/O，取决于库是否响应取消——**设了超时 ≠ 资源一定立刻释放**，但「无限挂死」会少很多。

#### 怎么验证（本地不依赖外网）

```python
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout


def slow_job() -> str:
    time.sleep(2.0)
    return "done"


with ThreadPoolExecutor(max_workers=1) as pool:
    future = pool.submit(slow_job)
    try:
        print(future.result(timeout=0.3))
    except FuturesTimeout:
        print("timed out: 不愿再等这条阻塞调用")
        # 注意：底层线程可能仍在 sleep；超时是「调用方放弃等待」
        # 生产还要考虑取消/关闭连接，避免线程与 fd 泄漏
```

这个实验刻意展示一个残酷事实：

```text
调用方超时返回 ≠ 后台阻塞工作一定已停止
所以 Agent 设计要同时考虑：
1. 调用方 deadline（用户侧别挂死）
2. 尽量取消/关闭底层连接（资源侧别泄漏）
```

#### 和「卡住」现场的对照表

| 现象 | 更可能的原因 | 先查什么 |
| --- | --- | --- |
| 整进程 CPU 很低但无响应 | 线程阻塞在网络/锁 | 超时设置、对端延迟、死锁 |
| CPU 100% | 忙等或 CPU 密集死循环 | 代码热点、是否空转 |
| 刚开始正常，越跑越慢 | 内存涨、fd 泄漏、连接堆积 | history、打开文件数、池大小 |
| 偶发超时 | 尾延迟、限流、冷启动 | 重试是否幂等、超时是否过紧 |

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 只设客户端超时，编排层无限等 | 上层仍可能卡住 |
| 超时后立刻盲重试砸对端 | 雪崩；要退避与预算 |
| 以为 `future.result(timeout=…)` 会杀线程 | 默认只是不再等；线程可能还活着 |
| 把超时关了「图稳定」 | 稳定性以「可失败、可恢复」为准，不是「永远等」 |

#### 前端对照

| 前端 | Agent / 服务端 |
| --- | --- |
| `AbortController` + `signal` | 超时取消请求 |
| `fetch` 一直 pending | 同步线程阻塞在读 socket |
| 加载态转错误态 | 超时异常 → 降级回复 / 重试 |

---

### 5.4 把四块拼起来：一次 LLM 调用在 OS 眼里发生了什么

#### 为什么需要这张总图？

前面分开学了进程、内存、I/O、fd、阻塞。合成一条时间线，排障才快。

```text
用户消息进入
  → 某个进程里的某条线程/协程开始处理
  → 拼 prompt（CPU + 一点内存）
  → 打开或复用 HTTP 连接（占 fd / 句柄）
  → 发送请求后阻塞/挂起，等待响应（I/O）
  → 若超过 timeout → 调用方放弃，尽量关闭连接
  → 若成功 → 解析 JSON（CPU），追加 history（内存）
  → 写日志（磁盘 I/O）
  → 释放或归还连接到池
```

自问四句：

1. **谁在跑？** 哪个进程/线程？
2. **在等什么？** 网络、磁盘、锁，还是在狂算？
3. **占了什么？** 内存、fd、连接槽位？
4. **上限在哪？** 超时、池大小、history 长度？

---

## 6. 了解即可：内核细节

下面这些词知道「存在、为谁服务」即可，排障用到再查文档。

| 概念 | 一句话 | 何时会遇见 |
| --- | --- | --- |
| 系统调用（syscall） | 用户态程序请求 OS 做事的入口（读文件、recv 等） | 性能分析、strace 类工具 |
| 页表 / 缺页 | 虚拟地址如何落到物理页 | 内存尖刺、换页抖动 |
| 中断 | 设备/定时器通知 CPU「有事了」 | 理解 I/O 完成如何唤醒线程 |
| 调度器算法 | 谁先跑、跑多久 | 延迟尾部、实时性讨论 |
| 用户态 vs 内核态 | 权限与安全边界 | 驱动、安全沙箱进阶 |

本章目标再次强调：

> 你会用进程/线程/阻塞/fd/超时说话，比会背 CFS 调度细节更重要。

#### 前端对照（可选）

浏览器与 Node 也站在 syscall 之上：`fs.readFile`、TCP、定时器最终都要进 OS。前端工程师不需要写内核，但「事件循环底下仍是 I/O 与线程池」的地图，和本章一致。

---

## 7. 常见坑（全章对照表）

把前面易错点收成一张「出门前核对」表：

| # | 坑 | 正确习惯 |
| --- | --- | --- |
| 1 | 把「电脑卡」全怪 Python 慢 | 先分清：阻塞等网络 / CPU 忙 / 内存换页 |
| 2 | 同步串行等多次 LLM/工具 | I/O 可重叠时用线程或异步（见并发/异步章） |
| 3 | history / 缓存无限涨 | 截断、上限、摘要；监控 RSS |
| 4 | 打开文件/客户端不关 | `with` / lifespan；池有上限 |
| 5 | 高并发打满 fd / 连接数 | 复用连接、限流、及时释放 |
| 6 | CPU 密集任务死磕多线程 | 看 GIL；考虑进程或减计算 |
| 7 | 不设超时或超时后不清理 | 分层超时 + 尽量取消/关连接 |
| 8 | 用忙等轮询 | `sleep`/事件/队列/异步 wait |
| 9 | 把线程当浏览器 Worker（默认隔离） | OS 线程默认共享内存，注意竞态 |
| 10 | 调用方超时就以为后台已停 | 确认取消语义，避免僵尸请求与泄漏 |

---

## 8. 练习指引

请打开并完成：

[`exercises/04-systems-basics/01-os-basics.md`](../../exercises/04-systems-basics/01-os-basics.md)

建议代码位置：

```text
playground/04-systems-basics/01-os-basics/
```

建议动手顺序：

1. **B1** 打印 `pid` / `cwd` / `sys.executable`，跑两次写笔记（§2）  
2. **B2** 串行 `sleep` 测总耗时，写清「在等还是在算」（§3、§5）  
3. **B3** `with` 读写文件 + 错误示范注释（§4）  
4. **B4** Agent 内存风险清单三则（§3）  
5. 有余力：**A1** CPU vs I/O；**A2** 打开过多文件的思想实验；**C1** `psutil` 观察内存  

做题时始终对照四问：谁在跑、在等什么、占了什么、上限在哪。

---

## 9. 小结与下一站

### 心智模型

```text
进程 = 资源容器（内存隔离、fd 表、生命周期）
线程 = 容器里的执行流（同进程共享内存与坑）

Agent 主路径 ≈ 大量 I/O 等待 + 少量 CPU
打开文件/连接 ≈ 占用 fd/句柄 → 必须释放或复用
卡住 ≈ 多半在阻塞等待；要用超时与可观测性保护
调度 ≈ CPU 核上交错执行；阻塞让出，忙等不让
```

### 和前端经验的最终对照

| 你在前端熟悉的事 | 本章对应 |
| --- | --- |
| 多标签隔离 | 进程隔离 |
| 主线程卡死 | 单执行流被同步任务/忙占住 |
| `await fetch` + Abort | I/O 等待 + 超时取消 |
| 连接/资源要关 | fd / 句柄生命周期 |
| 虚拟列表、分页 | 控制内存峰值 |

### 自检清单

- [ ] 能区分进程与线程，并说出共享/隔离差异
- [ ] 能判断 Agent 主路径偏 I/O，并举例内存压力来源
- [ ] 知道文件与 socket 都占名额；会用 `with` 思维释放
- [ ] 能解释阻塞 / sleep / 忙等；能说明为何要给 LLM 调用设超时
- [ ] 知道内核细节「了解即可」，不在此章深挖
- [ ] 独立完成练习基础题 B1～B4

### 一句话带走

> Agent 的「卡住、超时、占内存、打不开连接」，先用进程/线程、I/O 阻塞、fd 与超时四块解释，再决定要不要上异步或加机器。

### 下一章

[`02-network-http.md`](./02-network-http.md) —— 网络与 HTTP：Agent 调 API 的世界（状态码、超时、重试边界）。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Python 工程化](../03-engineering/README.md)
- 下一章：[网络与 HTTP](./02-network-http.md)
