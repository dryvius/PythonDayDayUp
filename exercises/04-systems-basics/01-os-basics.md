# 练习：操作系统基础

> 对应文档：[`docs/04-systems-basics/01-os-basics.md`](../../docs/04-systems-basics/01-os-basics.md)  
> 状态：`已完成出题`  
> 建议用时：40～70 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：进程、阻塞、文件句柄、`with`、内存直觉。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/04-systems-basics/01-os-basics/
```

4. Python ≥ 3.11；先做题再看文末答案。书面题给完整段落，不要只写关键词。

---

## 热身题（建议先做）

### W1. pid 是什么

**要求**：一句话解释进程 PID 对排障有什么用。

**验收**：能说到「标识正在跑的那个进程实例」。

---

### W2. 阻塞的体感词

**要求**：从「等 I/O」和「占着 CPU 算」里选出：`time.sleep(1)` 更接近哪一种。

**验收**：答「等 / 让出」，不是「疯狂占满 CPU 算」。

---

### W3. 进程 vs 线程（一句话）

**要求**：各用一句话说明：进程与线程在「内存是否默认共享」上的差别。

**验收**：进程默认隔离；同进程内线程共享地址空间。

---

### W4. 句柄名额

**要求**：文件与 TCP socket 是否都占「打开物」名额（fd / 句柄）？这对 Agent 同时打很多 HTTP 有什么提醒？

**验收**：都占；要关连接 / 用连接池 / 限流，否则可能 `Too many open files`。

---

## 基础题（必做）

### B1. 进程信息

写脚本打印：

- `pid`（`os.getpid()`）
- `cwd`（`os.getcwd()`）
- `python` 可执行路径（`sys.executable`）

运行两次，观察 pid 变化，写进 `b1_notes.md`。

**验收**：有两次运行记录；能说明「每次启动通常是新进程 → pid 常变」。

---

### B2. 阻塞直觉

写 `sleep_n(seconds: float) -> None`，主流程串行调用两次各 `0.3` 秒，打印总耗时（用 `time.perf_counter()`）。

再在笔记写一句：这两段时间里 CPU 大概在忙算还是在等。

**验收**：总耗时约 `0.6s` 量级；笔记结论正确。

---

### B3. 文件句柄与 `with`

1. 用 `with` 写文件再读回，断言内容一致。
2. 再写一段「错误示范注释版」：说明若中途异常且不用 `with`，可能发生什么（不必真制造泄漏）。

**验收**：读写断言通过；注释说清「未关闭句柄 / finally 易忘」。

---

### B4. Agent 内存风险清单（书面）

列出 **3 个**会导致 Agent 内存涨的做法，并各给一个缓解措施。写进 `b4_notes.md`。

**验收**：三条都有「风险 + 缓解」，完整句子。

---

## 进阶题（建议至少做 1 题）

### A1. 区分 CPU vs I/O

给两个函数：

- 空循环累加（CPU）
- `time.sleep`（I/O 等待）

各跑一会儿，用文字说明为何并发策略应不同（线程/进程/异步怎么选——点到为止）。

**验收**：`a1_notes.md` 有对比结论。

---

### A2. 打开过多文件的思想实验

写笔记：若循环打开 1 万个文件不关闭，可能看到什么错误？如何改。

**验收**：提到句柄耗尽 / `OSError` 一类；改法指向 `with` 或显式 close。

---

## 挑战题（可选）

### C1. 用 `psutil` 观察内存（若可安装）

加载一个大 `list` 前后打印进程内存；装不了就跳过并在笔记注明。

**验收**：有前后数字，或明确跳过原因。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W2
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

### W1 参考答案

PID 用来唯一标识操作系统里的一个进程实例；看日志、杀进程、对照监控时，靠它确认「就是这一次运行」。

### W2 参考答案

`time.sleep(1)` 是等待（阻塞当前线程一段时间），不是用满 CPU 做计算。

---

### B1 思路 + 参考答案

```python
# b1_procinfo.py
import os
import sys


def main() -> None:
    print("pid =", os.getpid())
    print("cwd =", os.getcwd())
    print("executable =", sys.executable)


if __name__ == "__main__":
    main()
```

```bash
python b1_procinfo.py
python b1_procinfo.py
```

**`b1_notes.md` 参考作答**

```markdown
# B1

第一次：pid=24120
第二次：pid=18844

cwd 与 executable 不变（同一项目、同一解释器），pid 变化。
结论：每次命令行启动脚本通常是新进程；pid 标识该次实例。
```

---

### B2 思路 + 参考答案

```python
# b2_sleep.py
import time


def sleep_n(seconds: float) -> None:
    time.sleep(seconds)


def main() -> None:
    t0 = time.perf_counter()
    sleep_n(0.3)
    sleep_n(0.3)
    elapsed = time.perf_counter() - t0
    print(f"elapsed ≈ {elapsed:.3f}s")
    assert 0.55 <= elapsed <= 1.0


if __name__ == "__main__":
    main()
```

笔记一句：这两段时间主要在**等待**，不是狂算；串行所以总时间近似相加。

---

### B3 思路 + 参考答案

```python
# b3_files.py
from pathlib import Path


def write_and_read(path: Path, text: str) -> str:
    with path.open("w", encoding="utf-8") as f:
        f.write(text)
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def main() -> None:
    path = Path("demo_os.txt")
    out = write_and_read(path, "hello-agent")
    assert out == "hello-agent"
    print("ok", out)

    # ---- 错误示范（注释版，不要当正确写法）----
    # f = open(path, "w", encoding="utf-8")
    # f.write("x")
    # raise RuntimeError("boom")   # 若此处异常且没有 finally/close
    # f.close()                    # 可能执行不到 → 句柄延迟释放/锁文件（视 OS）
    # 正确：始终用 with，或 try/finally 里 close。


if __name__ == "__main__":
    main()
```

---

### B4 思路 + 参考答案

**`b4_notes.md` 完整参考作答**

```markdown
# B4 Agent 内存风险清单

1. **无限追加 messages / 工具结果从不截断**  
   风险：多轮对话后列表与字符串占用持续上涨，最终 OOM 或变慢。  
   缓解：`truncate_messages`、只保留最近 N 轮、对工具结果做摘要/截断。

2. **把整库文档或超大检索结果一次性 `read()` 进内存**  
   风险：单次请求尖峰内存；并发几个请求就放大。  
   缓解：分页、Top-K、流式处理、限制 `max_bytes`。

3. **缓存字典只增不减（按用户/会话缓存 prompt 或 embedding）**  
   风险：进程长跑后缓存变成内存泄漏。  
   缓解：LRU / TTL、限制条目数、按会话结束清理；大对象外置到 Redis 等。
```

---

### A1 思路 + 参考答案

```python
# a1_cpu_io.py
import time


def cpu_bound(n: int = 3_000_000) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


def io_wait(sec: float = 0.3) -> None:
    time.sleep(sec)


if __name__ == "__main__":
    t0 = time.perf_counter()
    cpu_bound()
    print("cpu elapsed ≈", round(time.perf_counter() - t0, 3), "s")

    t0 = time.perf_counter()
    io_wait()
    print("io  elapsed ≈", round(time.perf_counter() - t0, 3), "s")
```

**`a1_notes.md` 参考作答**

```markdown
# A1

- CPU 累加：线程被算力占满；Python 多线程常受 GIL 限制，要加速更看多进程或换实现。
- sleep I/O 等待：等待时可重叠；多线程或 asyncio 往往有收益。

并发策略应先问「在等还是在算」，再选线程池 / 进程池 / asyncio。
```

---

### A2 思路 + 参考答案

**`a2_notes.md` 完整参考作答**

```markdown
# A2 打开过多文件

若循环 `open()` 一万次却不 `close()`/`with`，进程会占用大量文件描述符。
常见现象：抛出 `OSError: [Errno 24] Too many open files`（或 Windows 上类似的句柄耗尽错误）。

改法：
1. 始终用 `with open(...) as f:`，离开块自动关闭；
2. 必须手动时用 `try/finally: f.close()`；
3. 批量处理时控制并发打开数，而不是一次全打开。
```

---

### C1 思路 + 参考答案

```python
# c1_psutil_mem.py
# pip install psutil  （可选）
import os

try:
    import psutil
except ImportError:
    print("psutil not installed; skip C1")
    raise SystemExit(0)


def rss_mb() -> float:
    proc = psutil.Process(os.getpid())
    return proc.memory_info().rss / (1024 * 1024)


def main() -> None:
    before = rss_mb()
    data = [i for i in range(2_000_000)]
    after = rss_mb()
    print(f"rss before≈{before:.1f}MB after≈{after:.1f}MB delta≈{after - before:.1f}MB")
    assert after >= before
    del data


if __name__ == "__main__":
    main()
```

---

### W3 参考答案

- **进程**：各自独立虚拟地址空间，默认不共享 Python 变量。  
- **线程**：同属一进程，**共享**堆内存；因此多线程改同一 `counter` 可能竞态。

### W4 参考答案

文件描述符 / 句柄是进程级稀缺名额；打开文件、监听 socket、出站连接都可能占用。  
Agent 若对每个工具调用新建未关闭的 HTTP 客户端 / 文件句柄，高并发时会撞上限。缓解：`with` / `async with`、连接池、并发 Semaphore、及时 close。

---

### 常见坑（自检清单）

| 现象 | 先怀疑 |
|------|--------|
| Agent「卡住」很久 | 在等 LLM/工具网络，还是死循环 CPU？有无超时？ |
| 内存持续上涨 | messages 无限追加？缓存只增不减？一次读整文件？ |
| Too many open files | 循环 open/connect 未关闭；连接池未复用 |
| 设了 timeout 仍挂 | 超时是否作用在正确一层（connect/read/整体）？卡住的是别的线程？ |
| 多开终端跑脚本「共享了变量」 | 没有；那是两个进程 |

**补充练习（可选，不算通过线）**：写一个脚本用 `pathlib.Path.write_text` / `read_text` 完成 B3 的读写断言，体会「高层 API 内部仍会管好关闭」。

```python
from pathlib import Path

p = Path("demo_pathlib.txt")
p.write_text("agent-os", encoding="utf-8")
assert p.read_text(encoding="utf-8") == "agent-os"
```

**进程信息扩展断言示例**

```python
import os
import sys

assert isinstance(os.getpid(), int) and os.getpid() > 0
assert os.path.isabs(os.getcwd()) or os.getcwd()  # cwd 非空
assert "python" in sys.executable.lower() or sys.executable.endswith("python.exe")
```

**阻塞计时模板（可复用到并发章对照）**

```python
import time


def timed(fn) -> float:
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def two_sleeps() -> None:
    time.sleep(0.2)
    time.sleep(0.2)


elapsed = timed(two_sleeps)
print(f"two sleeps ≈ {elapsed:.3f}s")
assert elapsed >= 0.35
```

**口诀（可背）**

```text
卡住先问：在等还是在算？
打开的东西：用 with，记得关。
内存只增不减：截断 / LRU / 限大小。
超时不是装饰：每一层都要想清楚作用点。
```

---

### 本章速查

| 主题 | 记住 |
|------|------|
| 进程 | pid / cwd / executable；进程间内存默认隔离 |
| 线程 | 同进程共享内存；I/O 等待可重叠，CPU 受 GIL 影响 |
| 阻塞 | sleep / 等网络是「等」，不是狂算 |
| 文件 | 永远优先 `with`；文件与 socket 都占名额 |
| 内存 | 截断、限流、LRU，防只增不减 |
| 排障四问 | 谁在跑？在等什么？打开了多少？有没有超时？ |
