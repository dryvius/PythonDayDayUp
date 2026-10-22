# 练习：asyncio 进阶实践

> 对应文档：[`docs/05-async-python/02-asyncio-advanced.md`](../../docs/05-async-python/02-asyncio-advanced.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握 / 建议掌握」：`Semaphore`、分批 `gather`、异步 HTTP、阻塞危害、`to_thread`、流式 `async for`。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/05-async-python/02-asyncio-advanced/
```

4. Python ≥ 3.11；异步 HTTP 可用 `httpx`（需安装）。网络不通时允许 mock，并注明。
5. 对齐 CONVENTIONS：教学假模型若出现，早期可用 `EchoLLM`；不要把同步教学客户端误叫 FakeLLM。
6. 先做题再看文末答案。

---

## 热身题（建议先做）

### W1. Semaphore 是干什么的

**要求**：一句话说明 `asyncio.Semaphore(n)` 在并发扇出时限制什么。

**验收**：限制**同时进入临界区 / 同时执行**的协程数量（峰值并发）。

---

### W2. 分批 gather 的峰值

**要求**：25 个任务、`batch_size=10`，批内 `gather`、批间串行——峰值并发大约多少？

**验收**：约 10。

---

### W3. 阻塞一句警语

**要求**：为什么在 `async def` 里写 `time.sleep(1)` 会毁掉并发？

**验收**：堵住事件循环线程，其它协程无法推进。

---

## 基础题（必做）

### B1. Semaphore

10 个任务，每个 `await asyncio.sleep(0.2)`，`Semaphore=2`。  
打印总耗时，说明为何大约是「5 个波次」而不是「10 串行」或「全并行」。

**验收**：耗时约 1.0s 量级（允许抖动）；笔记解释波次。

---

### B2. 分批 gather

实现 `map_batched(items, fn, batch_size)`，对 `range(25)` 做假处理，`batch_size=10`，验证结果长度 25。

**验收**：`assert len(out) == 25`；结果内容正确（如 `x * 2`）。

---

### B3. 异步 HTTP（可选联网）

用 `httpx.AsyncClient` GET `https://httpbin.org/get`（或任意可达 URL），打印 `status_code`。  
若网络不可用：用 mock / 本地假客户端代替，并注明。

**验收**：有 status 输出；真实或 mock 路径清晰。

---

### B4. 阻塞危害（认知实验）

在 async 函数里用 `time.sleep(0.5)` 跑两个并发任务，对比改成 `asyncio.sleep` 的耗时差异；写 3 行结论到 `b4_notes.md`。

**验收**：能用数字说明 `time.sleep` 让「假并发」接近串行相加。

---

## 进阶题（建议至少做 1 题）

### A1. 复用 `AsyncClient`

把 client 提到外层 `async with AsyncClient`，并发请求 3 个 URL（可重复同一 mock URL），对比「每请求新建 client」的代码结构差异（笔记即可）。

**验收**：`a1_notes.md` 说明连接复用/生命周期好处。

---

### A2. `async for` 流

实现 `token_stream`，`async for` 拼接完整字符串，断言等于原文。

**验收**：`assert await collect("agent") == "agent"`。

---

## 挑战题（可选）

### C1. 限流工具运行时

实现文档 `run_tools` + `ToolCall`，`limit=2`，4 个工具，打印结果与耗时。

**验收**：可跑；耗时明显小于四 delay 之和。

---

### C2. `to_thread` 包装同步函数

把一个同步 `time.sleep` 函数放到 `asyncio.to_thread`，在 `gather` 里并发跑 3 次，观察是否重叠等待。

**验收**：总耗时接近单次 sleep，而不是三倍（允许抖动）。

---

## 模块 05 通关自检

- [ ] 会 async/await/Task/gather
- [ ] 会超时取消
- [ ] 会 Semaphore 限流
- [ ] 会异步 HTTP 基本用法
- [ ] 清楚不能在事件循环里阻塞

完成后进入模块 06《Web 后端》。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W3
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1 参考答案

`Semaphore(n)` 限制**同时持有许可**的协程数，从而把峰值并发压到 n（例如同时最多 2 个工具 HTTP）。

### W2 参考答案

峰值并发约等于 **`batch_size`（10）**；批与批之间串行，所以不会 25 全开。

### W3 参考答案

`time.sleep` 阻塞的是跑事件循环的那条线程；循环无法调度其它协程，`gather` 也救不了。

---

### B1 思路 + 参考答案

**思路**

10 个任务、并发上限 2、每个 0.2s → 约 5 波 × 0.2s ≈ 1.0s。  
不是 10×0.2=2.0（那是完全串行），也不是 0.2（那是无限并发）。

```python
# b1_semaphore.py
import asyncio
import time


async def worker(sem: asyncio.Semaphore, i: int) -> int:
    async with sem:
        await asyncio.sleep(0.2)
        return i


async def main() -> None:
    sem = asyncio.Semaphore(2)
    t0 = time.perf_counter()
    results = await asyncio.gather(*(worker(sem, i) for i in range(10)))
    dt = time.perf_counter() - t0
    print("results", results)
    print(f"elapsed ≈ {dt:.3f}s")
    assert results == list(range(10))
    assert 0.85 <= dt <= 1.6  # 约 5 波；机器忙时放宽


if __name__ == "__main__":
    asyncio.run(main())
```

**笔记示例**

```markdown
Semaphore=2，10 个 0.2s 任务 → 同时最多 2 个在 sleep，需要 5 个波次，总时间≈1.0s。
```

---

### B2 思路 + 参考答案

```python
# b2_map_batched.py
import asyncio
from collections.abc import Awaitable, Callable, Sequence


async def map_batched[T, R](
    items: Sequence[T],
    fn: Callable[[T], Awaitable[R]],
    batch_size: int = 10,
) -> list[R]:
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    out: list[R] = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        part = await asyncio.gather(*(fn(x) for x in batch))
        out.extend(part)
    return out


async def work(x: int) -> int:
    await asyncio.sleep(0.01)
    return x * 2


async def main() -> None:
    items = list(range(25))
    out = await map_batched(items, work, batch_size=10)
    assert len(out) == 25
    assert out == [x * 2 for x in items]
    print("ok", out[:5], "...", out[-3:])


if __name__ == "__main__":
    asyncio.run(main())
```

若你的环境对 PEP 695 泛型函数不熟，可改成无类型参数版本：

```python
async def map_batched(items, fn, batch_size: int = 10):
    out = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        part = await asyncio.gather(*(fn(x) for x in batch))
        out.extend(part)
    return out
```

---

### B3 思路 + 参考答案

**联网版**

```python
# b3_httpx_get.py
import asyncio

import httpx


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get("https://httpbin.org/get")
        print("status_code =", r.status_code)
        assert r.status_code == 200


if __name__ == "__main__":
    asyncio.run(main())
```

**无网假客户端版**

```python
import asyncio


class FakeAsyncClient:
    async def get(self, url: str):
        class Resp:
            status_code = 200

        await asyncio.sleep(0)
        return Resp()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


async def main() -> None:
    async with FakeAsyncClient() as client:
        r = await client.get("https://httpbin.org/get")
        print("status_code =", r.status_code, "(fake client)")
        assert r.status_code == 200


if __name__ == "__main__":
    asyncio.run(main())
```

---

### B4 思路 + 参考答案

```python
# b4_blocking_hazard.py
import asyncio
import time


async def with_time_sleep() -> float:
    async def job() -> None:
        time.sleep(0.5)  # 反面教材：阻塞事件循环

    t0 = time.perf_counter()
    await asyncio.gather(job(), job())
    return time.perf_counter() - t0


async def with_asyncio_sleep() -> float:
    async def job() -> None:
        await asyncio.sleep(0.5)

    t0 = time.perf_counter()
    await asyncio.gather(job(), job())
    return time.perf_counter() - t0


async def main() -> None:
    blocked = await with_time_sleep()
    overlapped = await with_asyncio_sleep()
    print(f"time.sleep gather ≈ {blocked:.3f}s")
    print(f"asyncio.sleep gather ≈ {overlapped:.3f}s")
    assert blocked > 0.9
    assert overlapped < 0.8


if __name__ == "__main__":
    asyncio.run(main())
```

**`b4_notes.md` 完整参考作答**

```markdown
# B4 阻塞危害（3 行结论）

1. `time.sleep` + `gather` 两个 0.5s：总耗时≈1.0s，几乎串行相加。  
2. `asyncio.sleep` + `gather`：总耗时≈0.5s，等待重叠。  
3. 结论：异步并发依赖「await 让出循环」；任何阻塞调用都会让其它协程饿死。同步 SDK 请用 `asyncio.to_thread` / 线程池，并限流。
```

---

### A1 思路 + 参考答案

```python
# a1_reuse_client.py
import asyncio

import httpx


async def fetch_many_reused(urls: list[str]) -> list[int]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        async def one(url: str) -> int:
            r = await client.get(url)
            return r.status_code

        return list(await asyncio.gather(*(one(u) for u in urls)))


async def fetch_many_new_each(urls: list[str]) -> list[int]:
    async def one(url: str) -> int:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            return r.status_code

    return list(await asyncio.gather(*(one(u) for u in urls)))


# 无网时用 mock 思路：只对比代码结构，不必真跑外网
```

**`a1_notes.md` 完整参考作答**

```markdown
# A1 复用 AsyncClient

- **每请求新建 client**：代码简单，但握手/连接池建了就扔，高频调用浪费大，超时/代理配置也易重复。
- **外层 `async with AsyncClient`**：同一生命周期内复用连接池；并发 `gather` 共享一个 client 更自然；退出时统一关闭。

Agent 里对同一 Provider 的多次 LLM/embedding 调用，优先复用 client（或单例持有），并在应用关闭时 aclose。
```

---

### A2 思路 + 参考答案

```python
# a2_token_stream.py
import asyncio
from collections.abc import AsyncIterator


async def token_stream(text: str) -> AsyncIterator[str]:
    for ch in text:
        await asyncio.sleep(0)  # 让出循环；真实场景是等网络块
        yield ch


async def collect(text: str) -> str:
    parts: list[str] = []
    async for ch in token_stream(text):
        parts.append(ch)
    return "".join(parts)


async def main() -> None:
    assert await collect("agent") == "agent"
    assert await collect("") == ""
    print(await collect("hi"))


if __name__ == "__main__":
    asyncio.run(main())
```

---

### C1 思路 + 参考答案

```python
# c1_run_tools.py
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass(frozen=True)
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
    results = await run_tools(calls, limit=2)
    dt = time.perf_counter() - t0
    print(results)
    print(f"elapsed ≈ {dt:.2f}s")
    assert [r["name"] for r in results] == ["search", "browse", "calc", "embed"]
    assert dt < sum(c.delay for c in calls) * 0.8


if __name__ == "__main__":
    asyncio.run(main())
```

说明：`gather` 按传入顺序返回结果；总耗时接近「并发度 2 调度下的关键路径」，不是四个 delay 相加。

---

### C2 思路 + 参考答案

```python
# c2_to_thread.py
import asyncio
import time


def blocking_sleep(sec: float) -> str:
    time.sleep(sec)
    return "ok"


async def main() -> None:
    t0 = time.perf_counter()
    results = await asyncio.gather(
        asyncio.to_thread(blocking_sleep, 0.4),
        asyncio.to_thread(blocking_sleep, 0.4),
        asyncio.to_thread(blocking_sleep, 0.4),
    )
    dt = time.perf_counter() - t0
    print(results, f"elapsed≈{dt:.3f}s")
    assert results == ["ok", "ok", "ok"]
    assert dt < 0.9  # 重叠等待：接近 0.4 而不是 1.2


if __name__ == "__main__":
    asyncio.run(main())
```

笔记：`to_thread` 把阻塞移到线程池，事件循环仍可调度；但仍要 Semaphore 限流，避免打爆线程与下游。

---

### 本章速查

| 主题 | 记住 |
|------|------|
| Semaphore | 控峰值并发 |
| map_batched | 批内并发、批间串行 |
| AsyncClient | 复用，不要每次新建（高频时） |
| 阻塞 | `time.sleep` / 同步 HTTP 会卡 loop |
| to_thread | 同步 SDK 的逃生舱 |
| async for | 流式 token / chunk |

升级方向：单工具 `wait_for`、失败策略（`return_exceptions` vs `TaskGroup`）、与观测字段（`run_id` / `latency_ms`）结合——进入 Web / Agent 章后继续。
