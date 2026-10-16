# asyncio 基础

> 所属模块：`05-async-python` · Python 异步编程  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/05-async-python/01-asyncio-fundamentals.md`](../../exercises/05-async-python/01-asyncio-fundamentals.md)

## 本章定位

- **模块目标**：掌握 asyncio，跨过 Agent 开发分水岭。
- **本章角色**：把 `async/await`、事件循环、Task、`gather` 练熟，能把多个 I/O 等待重叠起来。
- **前置**：模块 04 的并发模型（并发 vs 并行、GIL、为何 I/O 适合异步）。

## 学习目标

1. 正确编写并运行 `async def` / `await` 代码。
2. 说清协程、Task、事件循环的关系。
3. 用 `asyncio.gather` 并发等待多个 I/O 任务。
4. 会做基础超时与取消（建议掌握）。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | async/await、事件循环、Coroutine/Task、gather | 能写并发 I/O |
| **建议掌握** | 超时与取消 | 能避免无限挂起 |
| **了解即可** | 事件循环实现细节 | 不深挖 |

---

## 1. 为什么要学（Agent 分水岭）

串行等待（即使写成 `await`，也是一个完再等下一个）：

```text
await llm_a   2.0s
await llm_b   2.0s
合计 4.0s
```

并发等待（先调度再一起等）：

```text
同时等 llm_a + llm_b
合计 ≈ 2.0s
```

工具并行、批量 embedding、多路检索，全靠这一能力。  
FastAPI 路由、许多 LLM SDK 也默认异步友好。

---

## 2. 必掌握：async / await

### 2.1 最小例子

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

要点：

- `async def` 定义**协程函数**；调用它返回协程对象，不会立刻跑完
- `await` 等待一个 awaitable（协程/Task/Future 等）
- 入口常用 `asyncio.run(...)`（脚本顶层）

### 2.2 千万别混用

```python
# 错误：忘记 await
async def bad():
    say("x", 0.1)  # 只创建了协程，没调度执行

# 错误：在普通函数里直接 await（语法不允许）
def bad2():
    await say("x", 0.1)
```

### 2.3 `asyncio.sleep` vs `time.sleep`

| | `asyncio.sleep` | `time.sleep` |
|--|-----------------|--------------|
| 效果 | 让出事件循环，其它任务可跑 | **阻塞整个线程**，卡住循环 |
| 异步代码里 | 正确 | 通常错误（除非放到线程） |

---

## 3. 必掌握：事件循环（心智模型）

把事件循环想成「调度员」：

```text
准备好的任务 → 跑到下一个 await
遇到 I/O 等待 → 登记回调，去跑别的任务
I/O 完成 → 任务重新就绪
```

你很少手写 loop（现代代码用 `asyncio.run`），但要理解：

> **`await` 是协作式让出：把控制权交还事件循环，好去推进其它就绪任务。**  
> 它不是 OS 抢占式「时间片」；`await` 之间的 CPU 密集代码仍会占满当前线程，也**不会**因此绕过 GIL 做多核并行。

---

## 4. 必掌握：Coroutine 与 Task

### 4.1 协程对象

```python
coro = say("a", 0.1)  # 协程对象，尚未执行
# 必须 await coro 或包装成 Task
```

### 4.2 Task：被调度的并发单元

```python
async def main() -> None:
    t1 = asyncio.create_task(say("a", 0.2))
    t2 = asyncio.create_task(say("b", 0.2))
    # create_task：已登记调度；通常要等当前协程 await 把控制权交回循环后才真正跑
    r1 = await t1
    r2 = await t2
    print(r1, r2)


asyncio.run(main())
```

区别直觉：

- **只 await 协程**：基本顺序执行（一个完再下一个，除非内部自己并发）
- **create_task**：把任务丢进循环，后续可与其它任务交错推进

---

## 5. 必掌握：`asyncio.gather`

并发等一组任务，收集结果：

```python
async def main() -> None:
    results = await asyncio.gather(
        say("a", 0.2),
        say("b", 0.2),
        say("c", 0.2),
    )
    print(results)  # 按传入顺序返回


asyncio.run(main())
```

异常行为（易混，务必分清）：

```python
# gather 默认：把「最先发生的异常」传播给 await gather 的一方；
# 其它任务**不会**因此被取消，仍可能继续跑完。
# return_exceptions=True：异常作为结果项返回，不因单个失败而打断 gather 本身。
results = await asyncio.gather(t1, t2, return_exceptions=True)

# 若要「一组同生共死、失败取消兄弟任务」→ 用 3.11+ 的 asyncio.TaskGroup（下一章）
```

Agent 场景：

```python
docs, emb = await asyncio.gather(
    search(query),
    embed(query),
)
```

---

## 6. 建议掌握：超时与取消

### 6.1 超时

```python
async def call_llm(prompt: str) -> str:
    await asyncio.sleep(2)  # 假装慢调用
    return "ok"


async def main() -> None:
    try:
        result = await asyncio.wait_for(call_llm("hi"), timeout=0.5)
    except TimeoutError:  # 3.11+；更早是 asyncio.TimeoutError
        print("timed out")
    else:
        print(result)
```

生产中：LLM / 工具调用必须有超时。

`wait_for` 超时后会 **cancel** 内部 awaitable：内层任务常收到 `CancelledError`，外层 `await wait_for(...)` 看到的是 `TimeoutError`（3.11+ 与内置同名）。清理逻辑放在内层的 `try/finally`。

### 6.2 取消

```python
async def main() -> None:
    task = asyncio.create_task(call_llm("hi"))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")
        raise  # 多数情况下继续向上传更安全
```

在 `try/finally` 里做清理；被取消时也要释放资源。

---

## 7. 了解即可：事件循环实现细节

selector、proactor、不同 OS 的 I/O 多路复用——知道存在即可。  
应用层把「别阻塞循环」做好更重要。

---

## 8. 综合小例子：并行假工具

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


if __name__ == "__main__":
    print(asyncio.run(run_agent_step()))
```

---

## 9. 常见坑

1. 在 async 函数里 `time.sleep` / 同步 `requests.get`
2. 创建协程却忘记 await / create_task
3. 在已经运行的 loop 里再 `asyncio.run`（嵌套问题）
4. 假设 gather 会“按完成顺序”返回（实际按传入顺序）
5. 忽略 CancelledError 乱吞

---

## 10. 练习指引

[`exercises/05-async-python/01-asyncio-fundamentals.md`](../../exercises/05-async-python/01-asyncio-fundamentals.md)

---

## 11. 小结与下一站

### 自检

- [ ] 能手写 `asyncio.run` + `async def` + `await`
- [ ] 能说明 Task 与裸协程差异
- [ ] 能用 gather 并行等待
- [ ] 会给慢调用加 `wait_for`

### 下一章

[`02-asyncio-advanced.md`](./02-asyncio-advanced.md) —— 限流、并发模式、异步 HTTP、常见坑。

## 导航

- 返回模块：[README](./README.md)
- 上一模块：[并发模型](../04-systems-basics/03-concurrency-models.md)
- 下一章：[asyncio 进阶实践](./02-asyncio-advanced.md)
