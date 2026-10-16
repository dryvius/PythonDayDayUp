# asyncio 进阶实践

> 所属模块：`05-async-python` · Python 异步编程  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/05-async-python/02-asyncio-advanced.md`](../../exercises/05-async-python/02-asyncio-advanced.md)

## 本章定位

- **本章角色**：把基础并发变成「可控的生产级模式」——限流、异步 HTTP、资源生命周期、避坑。
- **和 Agent**：并行工具时要限流；调 LLM 要用 AsyncClient；长任务要能取消与收尾。

## 学习目标

1. 用 `Semaphore` 控制最大并发。
2. 掌握常见并发控制模式（worker 池、分批 gather）。
3. 会用异步 HTTP 客户端（以 httpx 为例）发请求。
4. 了解异步上下文/生成器，并能避开阻塞事件循环等坑。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | Semaphore、并发控制模式、异步 HTTP | 能写限流并发调用 |
| **建议掌握** | TaskGroup / ExceptionGroup、异步上下文/生成器、常见坑 | 能排障与选型 |
| **了解即可** | trio/anyio | 扫盲 |

---

## 1. 为什么要学

无脑 `gather` 三百个请求：

```text
打爆对方 429
打爆本地连接数
内存里堆满 Task
```

进阶目标：**又快又稳**。

---

## 2. 必掌握：Semaphore 限流

```python
import asyncio


sem = asyncio.Semaphore(3)  # 最多 3 个同时进入


async def call_one(i: int) -> int:
    async with sem:
        await asyncio.sleep(0.2)  # 假装 HTTP
        return i


async def main() -> None:
    results = await asyncio.gather(*(call_one(i) for i in range(10)))
    print(results)


asyncio.run(main())
```

Agent 建议：

- 对同一 LLM 供应商设最大并发（如 5）
- 对网页抓取/搜索工具设更严的限流
- 信号量可按「下游」分别创建

---

## 3. 必掌握：并发控制模式

### 3.1 分批 gather

```python
async def map_batched(items, fn, batch_size: int = 10):
    out = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        part = await asyncio.gather(*(fn(x) for x in batch))
        out.extend(part)
    return out
```

简单、好懂；适合总数可控的任务。

### 3.2 Worker 池（队列）

```python
async def worker(name: str, queue: asyncio.Queue) -> None:
    while True:
        item = await queue.get()
        try:
            if item is None:
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
    await queue.join()
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


asyncio.run(main())
```

适合持续进来的任务流（更接近服务端）。

### 3.3 `TaskGroup`（3.11+，建议掌握）

结构化并发：一组任务同生共死；**任一子任务失败会取消组内其它任务**；多个错误常以 `ExceptionGroup` 形式出现（可用 `except*`）。

| | `asyncio.gather` | `asyncio.TaskGroup` |
|--|------------------|---------------------|
| 失败时取消兄弟？ | **默认否** | **是** |
| 典型用途 | 收集一组结果 | 要强清理/同生共死的一组工作 |

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
    except* RuntimeError as eg:
        print("caught", eg.exceptions)


asyncio.run(main())
```

能用 `gather` 且不需要「失败即取消兄弟」时，继续用 `gather` 即可；新代码若要结构化取消，优先用 `TaskGroup`。

---

## 4. 必掌握：异步 HTTP 客户端（httpx）

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


async def fetch_many(urls: list[str]) -> list[str]:
    sem = asyncio.Semaphore(5)
    async with httpx.AsyncClient(timeout=10.0) as client:

        async def one(url: str) -> str:
            async with sem:
                return await fetch_text(client, url)

        return await asyncio.gather(*(one(u) for u in urls))
```

要点：

1. 用 **`AsyncClient`**，不要在 async 里用同步 `requests`
2. **timeout** 必设
3. 客户端复用：热路径上**共享一个 client**（如上），不要每个请求 `AsyncClient()` 新建又销毁
4. `raise_for_status()` 处理 4xx/5xx

假 LLM 调用形态：

```python
async def chat(client: httpx.AsyncClient, prompt: str) -> dict:
    resp = await client.post(
        "https://api.example.com/v1/chat/completions",
        json={"model": "gpt-x", "messages": [{"role": "user", "content": prompt}]},
        headers={"Authorization": "Bearer sk-xxx"},
    )
    resp.raise_for_status()
    return resp.json()
```

（练习可用 httpbin 或本地 mock，避免依赖真实 Key。）

---

## 5. 建议掌握：异步上下文与异步生成器

### 5.1 `async with`

```python
class FakeConn:
    async def __aenter__(self):
        await asyncio.sleep(0)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await asyncio.sleep(0)


async def main():
    async with FakeConn() as conn:
        ...
```

`httpx.AsyncClient`、异步 DB 连接都靠它保证关闭。

也可用：

```python
from contextlib import asynccontextmanager
```

### 5.2 异步生成器 / `async for`

```python
async def token_stream(text: str):
    for ch in text:
        await asyncio.sleep(0)
        yield ch


async def main():
    async for ch in token_stream("hi"):
        print(ch, end="")
```

LLM 流式输出常用这种消费方式。

---

## 6. 建议掌握：常见死锁与坑

1. **在持有锁时 await 另一个也要同锁的任务** → 死锁  
2. **异步函数里调用阻塞 I/O** → 整个服务卡住  
   - 临时：`asyncio.to_thread(blocking_fn, ...)`  
3. **Fire-and-forget Task 不保存引用** → 可能被回收、异常丢失  
   - 保存 task 引用或显式管理生命周期  
4. **Semaphore 忘记 async with 释放**  
5. **在 running loop 中调用 `asyncio.run`**  
6. **取消后仍假设共享状态一致** → finally 里清理

排障口诀：

> 先找阻塞点，再找锁与未 await，再看超时。

---

## 7. 了解即可：trio / anyio

- **Trio**：另一套结构化并发思想
- **AnyIO**：兼容层，很多库用它做后端无关异步

你会在依赖树里见到；本路线主线仍是 **asyncio + httpx + FastAPI**。

---

## 8. 综合小例子：限流并行工具调用

```python
import asyncio
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
    return list(
        await asyncio.gather(*(run_tool(c, sem) for c in calls))
    )


async def main() -> None:
    calls = [
        ToolCall("search", 0.3),
        ToolCall("browse", 0.4),
        ToolCall("calc", 0.1),
        ToolCall("embed", 0.2),
    ]
    print(await run_tools(calls, limit=2))


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 9. 练习指引

[`exercises/05-async-python/02-asyncio-advanced.md`](../../exercises/05-async-python/02-asyncio-advanced.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能用 Semaphore 限制并发
- [ ] 能写出分批 gather 或简单 worker
- [ ] 能用 httpx.AsyncClient 发异步请求（或 mock）
- [ ] 知道阻塞调用会毁掉事件循环

### 模块 05 收官

下一模块：[`../06-web-backend/README.md`](../06-web-backend/README.md) —— Web 后端（ASGI/FastAPI/Pydantic/认证），异步能力会直接用上。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[asyncio 基础](./01-asyncio-fundamentals.md)
- 下一模块：[Web 后端](../06-web-backend/README.md)
