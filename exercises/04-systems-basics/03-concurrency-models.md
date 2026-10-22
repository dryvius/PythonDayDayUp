# 练习：并发模型

> 对应文档：[`docs/04-systems-basics/03-concurrency-models.md`](../../docs/04-systems-basics/03-concurrency-models.md)  
> 状态：`已完成出题`  
> 建议用时：50～80 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：并发 vs 并行、线程/进程/异步地图、GIL 直觉。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/04-systems-basics/03-concurrency-models/
```

4. 本章**不要求**写完整 asyncio 业务（留给模块 05）；但选型题可以选 asyncio。
5. Python ≥ 3.11；先做题再看答案。

---

## 热身题（建议先做）

### W1. 一句话区分

**要求**：并发 vs 并行，各用一句话。

**验收**：并发强调交替推进；并行强调同一时刻多核真一起干。

---

### W2. 串行 I/O 时间

**要求**：两个各 `sleep(0.2)` 的串行调用，总耗时更接近 0.2 还是 0.4？

**验收**：约 0.4（相加）。

---

### W3. 三种模型各擅长什么

**要求**：用一句话各点：多线程 / 多进程 / 异步（asyncio）最擅长的一类负载。

**验收**：线程→阻塞 I/O；进程→CPU 密集；异步→大量网络等待（调用链可异步化）。

---

### W4. `as_completed` 顺序

**要求**：`as_completed` 返回的顺序等于提交顺序吗？

**验收**：不等于；是完成顺序。要保序请按 Future 列表依次 `.result()`。

---

## 基础题（必做）

### B1. 并发 vs 并行（书面）

各举：

- 1 个生活例子
- 1 个 Agent 例子

写进 `b1_notes.md`。

**验收**：四格都有完整句子。

---

### B2. 串行 vs 线程池计时

按文档实现 `fake_io` + `sequential` + `threaded`，打印两种总耗时，确认线程版更快。

**验收**：串行 ≈ 0.4s 量级，线程版 ≈ 0.2s 量级（允许机器抖动）；可用 assert 放宽阈值。

---

### B3. GIL 选择题（书面）

判断并简述理由：

1. 纯 Python 计算斐波那契加速，多线程通常？  
2. 多个 `time.sleep` / 网络等待，多线程通常？

**验收**：`b3_notes.md` 两问都有判断 + 理由。

---

### B4. 选型题

为下列场景选：`asyncio` / `线程池` / `多进程` / `保持串行`，并一句理由：

1. 同时调 10 个 LLM embedding HTTP  
2. 同步 SDK 且短期不想改  
3. 对 200MB 文本做 CPU 正则重处理  
4. 三步严格依赖：检索→拼 prompt→生成

**验收**：四个选择 + 理由写在 `b4_notes.md`。

---

## 进阶题（建议至少做 1 题）

### A1. `ThreadPoolExecutor.map`

用线程池并行跑 5 个不同 delay 的 `fake_io`，收集结果。

**验收**：结果长度 5；总耗时明显小于 delay 之和。

---

### A2. 竞态演示（小心）

两个线程对同一 `counter += 1` 循环很多次，观察是否总等于期望；写笔记说明风险。（次数可调小以免过慢）

**验收**：有实验记录；能说明「共享可变状态需要同步」。

---

## 挑战题（可选）

### C1. 同步工具 + 异步编排草图

说明哪里用 asyncio，哪里用 `to_thread` / 线程池。画在 `c1_notes.md`。

**验收**：有 ASCII 图或分层说明，完整可读。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W2
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

### W1 参考答案

- **并发**：多个任务交替推进（看起来同时发生）。  
- **并行**：同一时刻多个核心真正同时执行。

### W2 参考答案

约 **0.4s**（串行相加）。

---

### B1 思路 + 参考答案

**`b1_notes.md` 完整参考作答**

```markdown
# B1

## 并发

- 生活：一个人烧水时同时洗菜——双手交替推进多件事，不一定两件事在同一毫秒「真并行」。
- Agent：同时等待 search / browse 两个 HTTP 返回——事件循环或线程在重叠等待。

## 并行

- 生活：两名厨师同时炒两道菜（两份劳动力同时干活）。
- Agent：用多进程对大文本做 CPU 密集分片处理，多个进程占多核同时算。
```

---

### B2 思路 + 参考答案

```python
# b2_thread_vs_seq.py
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
        # as_completed：按完成顺序；断言时用集合
        return [f.result() for f in as_completed(futs)]


def threaded_in_order() -> list[str]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fake_io, n, 0.2) for n in ("a", "b")]
        return [f.result() for f in futs]


if __name__ == "__main__":
    t0 = time.perf_counter()
    seq = sequential()
    seq_dt = time.perf_counter() - t0

    t0 = time.perf_counter()
    th = threaded_in_order()
    th_dt = time.perf_counter() - t0

    print("sequential", seq, f"elapsed≈{seq_dt:.3f}s")
    print("threaded  ", th, f"elapsed≈{th_dt:.3f}s")

    assert set(seq) == {"a", "b"}
    assert th == ["a", "b"]
    assert seq_dt >= 0.35
    assert th_dt <= 0.35
```

---

### B3 思路 + 参考答案

**`b3_notes.md` 完整参考作答**

```markdown
# B3 GIL

1. **纯 Python 计算斐波那契 + 多线程：通常几乎不加速（甚至更慢）**  
   理由：CPU 密集字节码执行受 GIL 约束，多线程难真正并行算 Python 代码，还多调度开销。

2. **多个 sleep / 网络等待 + 多线程：通常能明显缩短总等待墙钟时间**  
   理由：等待 I/O 时往往释放 GIL，其它线程可推进；等待可以重叠。
```

---

### B4 思路 + 参考答案

**`b4_notes.md` 完整参考作答**

```markdown
# B4 选型

1. 同时调 10 个 embedding HTTP → **asyncio**（或线程池）  
   理由：典型高并发网络 I/O；asyncio 适合大量等待（模块 05 细练）。短期也可用线程池。

2. 同步 SDK 且短期不想改 → **线程池**  
   理由：用 `ThreadPoolExecutor` / 以后 `asyncio.to_thread` 包一层，避免一次性重写全链路。

3. 200MB 文本 CPU 正则重处理 → **多进程**  
   理由：要多核真并行；多线程对纯 Python CPU 帮助有限。

4. 检索→拼 prompt→生成（严格依赖）→ **保持串行**  
   理由：后一步依赖前一步输出，硬并发没有重叠收益，只增加复杂度。
```

---

### A1 思路 + 参考答案

```python
# a1_map.py
import time
from concurrent.futures import ThreadPoolExecutor


def fake_io(item: tuple[str, float]) -> str:
    name, sec = item
    time.sleep(sec)
    return name


if __name__ == "__main__":
    jobs = [("a", 0.30), ("b", 0.10), ("c", 0.20), ("d", 0.15), ("e", 0.25)]
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(fake_io, jobs))
    dt = time.perf_counter() - t0
    print(results, f"elapsed≈{dt:.3f}s")
    assert results == ["a", "b", "c", "d", "e"]  # map 保序
    assert dt < sum(s for _, s in jobs) * 0.7
```

---

### A2 思路 + 参考答案

```python
# a2_race.py
import threading

COUNTER = 0
N = 100_000


def worker() -> None:
    global COUNTER
    for _ in range(N):
        COUNTER += 1  # 非原子：读改写可能交错


if __name__ == "__main__":
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    expected = 2 * N
    print("counter=", COUNTER, "expected=", expected)
    # 在很多 CPython 版本/负载下可能不相等；即使偶然相等，也不能当正确写法
```

**笔记参考**

```markdown
# A2

观察到 counter 常常 < expected（也可能偶发相等）。
风险：多线程共享可变状态的读改写不是原子操作，需要 Lock 或改用队列/不可变消息传递。
结论：I/O 并发可以；共享计数/缓存要同步或避免共享。
```

---

### C1 思路 + 参考答案

**`c1_notes.md` 完整参考作答**

```markdown
# C1 同步工具 + 异步编排

```text
                asyncio 事件循环（编排）
                          |
          +---------------+---------------+
          |               |               |
     await llm_http   await retriever  await gather(tools...)
     (原生 async)      (原生 async)          |
                                          |
                              同步 SDK 工具（阻塞）
                                          |
                              asyncio.to_thread / 线程池
                              （把阻塞移出事件循环线程）
```

原则：
1. 编排、超时、取消、并发扇出：用 asyncio。
2. 不得不调用的同步客户端：`to_thread` / `ThreadPoolExecutor`，并限流。
3. 不要在 async 函数里直接 `time.sleep` / 同步 `requests.get`。
```

---

### W3 参考答案

| 模型 | 擅长 |
|------|------|
| 多线程 | 阻塞 I/O 等待重叠（同步 SDK 短期方案） |
| 多进程 | CPU 密集真并行（绕开 GIL 算力墙） |
| asyncio | 大量网络 I/O、高扇出等待（调用链异步化后） |

### W4 参考答案

`as_completed` 按**谁先完成谁先出来**；不要 `assert results == ["a", "b"]`。  
保序写法：保留 `futs` 列表，再 `[f.result() for f in futs]`。

---

### 常见坑（自检清单）

| 错法 | 后果 |
|------|------|
| 有串行依赖还硬并发 | 无收益 + 复杂度上升 |
| 用多线程加速纯 Python CPU | 通常几乎不加速 |
| 假设 `as_completed` 保序 | 断言偶发失败 |
| 多线程无锁改共享计数 | 竞态，结果不稳定 |
| 「三种模型叠满一定更快」 | 边界不清时调试成本爆炸 |
| 在未来的 asyncio 里直接 `time.sleep` | 卡死事件循环（模块 05 重点） |

**补充：保序线程池最小示例**

```python
from concurrent.futures import ThreadPoolExecutor
import time


def fake_io(name: str, sec: float) -> str:
    time.sleep(sec)
    return name


with ThreadPoolExecutor(max_workers=3) as pool:
    futs = [
        pool.submit(fake_io, "a", 0.3),
        pool.submit(fake_io, "b", 0.1),
        pool.submit(fake_io, "c", 0.2),
    ]
    ordered = [f.result() for f in futs]
assert ordered == ["a", "b", "c"]
```

**补充：选型决策树（抄进笔记亦可）**

```text
任务有严格数据依赖？ → 串行
主要是等 HTTP / LLM？
  ├─ 能异步化 → asyncio
  └─ 只有同步 SDK → 线程池
主要是吃 CPU？ → 多进程（或换本地扩展/服务）
```

**补充：墙钟时间对照表（本练习经验值）**

| 场景 | 期望墙钟时间（约） |
|------|-------------------|
| 2×`sleep(0.2)` 串行 | 0.4s |
| 2×`sleep(0.2)` 线程池(2) | 0.2s |
| 4×`sleep(0.2)` 线程池(4) | 0.2s |
| 纯 Python 累加 ×4 线程 | ≈ 单线程（别指望线性加速） |

自己跑数字时允许抖动；看的是「方向对不对」，不是小数点后三位。

**和模块 05 的衔接（先建立地图）**

```text
本章：为什么要并发、线程池能重叠 sleep、GIL 限制什么
模块 05：async/await、gather、Semaphore、不要 time.sleep
```

不必现在写完整 asyncio Agent；把 B2 的计时直觉带走即可。

验收口诀：先分清「在等还是在算」，再选模型；有依赖就串行。

测耗时请用 `time.perf_counter()`，短间隔比 `time.time()` 更合适。

---

### 本章速查

| 主题 | 记住 |
|------|------|
| 并发/并行 | 交替 vs 真同时 |
| I/O | 线程/异步可重叠等待 |
| CPU | 多进程更靠谱 |
| GIL | 限 CPU 线程加速，不限 I/O 重叠 |
| 依赖链 | 该串行就串行 |
| 顺序 | `as_completed` 不保序；要保序按 Future 列表取 |
