# 练习：asyncio 基础

> 对应文档：[`docs/05-async-python/01-asyncio-fundamentals.md`](../../docs/05-async-python/01-asyncio-fundamentals.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：`async def` / `await` / `asyncio.run`、Task、`gather`、超时与取消入门。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/05-async-python/01-asyncio-fundamentals/
```

4. Python ≥ 3.11（`asyncio.TimeoutError` 为 `TimeoutError` 别名等约定见 CONVENTIONS）。
5. **禁止**在 async 路径里用 `time.sleep` 冒充并发（B4/认知题除外的反面教材）。
6. 先做题再看文末答案。

---

## 热身题（建议先做）

### W1. 调用 `async def` 得到什么？

**给定**：

```python
async def hello() -> str:
    return "hi"
```

**要求**：不 `await`、不 `asyncio.run`，只写 `x = hello()`，用一句话说明 `x` 是什么；并说明为什么还没真正执行函数体（或只创建了协程对象）。

**验收**：能说出「协程对象 / 未调度」。

---

### W2. 入口只能有一个 `asyncio.run`？

**要求**：一句话说明：通常如何启动顶层协程。

**验收**：`asyncio.run(main())`（或框架提供的 loop）；不要在已运行的 loop 里再 `run`。

---

### W3. 假睡眠该用谁

**要求**：在协程里等待 0.1 秒，应写 `await asyncio.sleep(0.1)` 还是 `time.sleep(0.1)`？

**验收**：前者。

---

## 基础题（必做）

### B1. 第一个协程

写 `async def hello(name: str) -> str`：`await asyncio.sleep(0.05)` 后返回字符串（如 `f"hello, {name}"`）；用 `asyncio.run` 打印。

**验收**：能跑通；返回值可 assert。

---

### B2. 顺序 vs `gather` 计时

三个 `asyncio.sleep(0.2)`：

1. 依次 `await` —— 打印总耗时  
2. `asyncio.gather` 并发 —— 打印总耗时  

断言并发版明显更接近 0.2s 量级而不是 0.6s。

**验收**：有打印 + assert（阈值可放宽，如并发 `< 0.45`，串行 `> 0.55`）。

---

### B3. `create_task`

用两个 `create_task` 启动假 I/O，再分别 `await`；打印完成。

**验收**：两个任务都跑完；理解「先启动再等待」与「立刻 await 第一个」的差别（笔记一句即可）。

---

### B4. `wait_for` 超时

故意 `sleep(1)` 的协程，用 `timeout=0.2` 包住，捕获超时异常并打印 `"timed out"`。

**验收**：打印 `timed out`；不让进程以未捕获异常崩溃（演示路径里要接住）。

---

## 进阶题（建议至少做 1 题）

### A1. `return_exceptions`

`gather` 三个任务：两个成功、一个抛 `ValueError`，`return_exceptions=True`，打印结果列表类型分布。

**验收**：列表长度 3；含 `str`（或你的成功类型）与 `ValueError` 实例。

---

### A2. 取消任务

启动长 sleep 任务，短暂等待后 `cancel`，捕获 `CancelledError`，在笔记写是否应继续 raise。

**验收**：`a2_notes.md` 有完整结论（不是一句话关键词）。

---

## 挑战题（可选）

### C1. 迷你并行工具步

实现文档综合例子 `run_agent_step`（`gather` 三个假工具），并断言耗时 < 串行之和的 70%（阈值设宽松）。

**验收**：并行明显快于串行；有 assert。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W3
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

### W1 参考答案

```python
import asyncio


async def hello() -> str:
    return "hi"


x = hello()
print(type(x))  # <class 'coroutine'>
# 协程对象已被创建，但函数体通常尚未推进；需要 await / 被调度
x.close()  # 避免 RuntimeWarning: never awaited（演示用）
```

结论：调用 `async def` 得到**协程对象**，不是返回值字符串。

### W2 参考答案

脚本入口用 `asyncio.run(main())` 创建 loop、跑完并清理；已在运行的 loop（如 Jupyter、部分框架）里不要再套一层 `asyncio.run`。

### W3 参考答案

应使用 **`await asyncio.sleep(0.1)`**。`time.sleep` 会阻塞整个事件循环线程，其它协程也无法推进。

---

### B1 思路 + 参考答案

```python
# b1_hello.py
import asyncio


async def hello(name: str) -> str:
    await asyncio.sleep(0.05)
    return f"hello, {name}"


async def main() -> None:
    msg = await hello("agent")
    print(msg)
    assert msg == "hello, agent"


if __name__ == "__main__":
    asyncio.run(main())
```

---

### B2 思路 + 参考答案

**思路**

依次 await 是加法；`gather` 把等待重叠，总时间接近 max。

```python
# b2_gather.py
import asyncio
import time


async def nap(sec: float) -> str:
    await asyncio.sleep(sec)
    return "ok"


async def sequential() -> float:
    t0 = time.perf_counter()
    await nap(0.2)
    await nap(0.2)
    await nap(0.2)
    return time.perf_counter() - t0


async def parallel() -> float:
    t0 = time.perf_counter()
    await asyncio.gather(nap(0.2), nap(0.2), nap(0.2))
    return time.perf_counter() - t0


async def main() -> None:
    seq = await sequential()
    par = await parallel()
    print(f"sequential ≈ {seq:.3f}s")
    print(f"parallel   ≈ {par:.3f}s")
    assert seq > 0.55
    assert par < 0.45


if __name__ == "__main__":
    asyncio.run(main())
```

---

### B3 思路 + 参考答案

```python
# b3_tasks.py
import asyncio


async def fake_io(name: str, sec: float) -> str:
    await asyncio.sleep(sec)
    return name


async def main() -> None:
    t1 = asyncio.create_task(fake_io("search", 0.2))
    t2 = asyncio.create_task(fake_io("calc", 0.1))
    # 两个任务已开始调度；再分别 await
    r1 = await t1
    r2 = await t2
    print("done", r1, r2)
    assert {r1, r2} == {"search", "calc"}


if __name__ == "__main__":
    asyncio.run(main())
```

笔记：若写成 `await fake_io(...); await fake_io(...)` 则仍串行；`create_task` 先挂上调度器才能重叠。

---

### B4 思路 + 参考答案

```python
# b4_timeout.py
import asyncio


async def slow() -> str:
    await asyncio.sleep(1.0)
    return "done"


async def main() -> None:
    try:
        await asyncio.wait_for(slow(), timeout=0.2)
    except TimeoutError:
        # Python 3.11+：asyncio.TimeoutError 是 TimeoutError 的别名
        print("timed out")
    else:
        raise AssertionError("should have timed out")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### A1 思路 + 参考答案

```python
# a1_return_exceptions.py
import asyncio


async def ok(name: str) -> str:
    await asyncio.sleep(0.05)
    return name


async def bad() -> str:
    await asyncio.sleep(0.05)
    raise ValueError("boom")


async def main() -> None:
    results = await asyncio.gather(
        ok("a"),
        bad(),
        ok("c"),
        return_exceptions=True,
    )
    print(results)
    types = [type(x).__name__ for x in results]
    print("types:", types)
    assert len(results) == 3
    assert results[0] == "a"
    assert isinstance(results[1], ValueError)
    assert results[2] == "c"


if __name__ == "__main__":
    asyncio.run(main())
```

---

### A2 思路 + 参考答案

```python
# a2_cancel.py
import asyncio


async def long_job() -> str:
    try:
        await asyncio.sleep(10)
        return "finished"
    except asyncio.CancelledError:
        # 清理资源后，通常应继续向上传播取消
        print("long_job cancelled, cleanup then re-raise")
        raise


async def main() -> None:
    task = asyncio.create_task(long_job())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("caller saw CancelledError")


if __name__ == "__main__":
    asyncio.run(main())
```

**`a2_notes.md` 完整参考作答**

```markdown
# A2 取消与 CancelledError

1. `task.cancel()` 会在任务下一个 await 点注入取消。
2. 任务内部常会冒出 `CancelledError`；若你在 `except` 里做清理，**清理完后一般应 `raise` 继续传播**，让调用方与 `gather`/`TaskGroup` 知道任务被取消。
3. 若吞掉 `CancelledError` 当成功返回，取消语义被破坏，上层超时/关闭流程会表现怪异。
4. 教学结论：取消是协作式的；清理可以做，但不要把取消偷偷变成「假装成功」。
```

---

### C1 思路 + 参考答案

```python
# c1_agent_step.py
import asyncio
import time


async def tool(name: str, sec: float) -> dict:
    await asyncio.sleep(sec)
    return {"tool": name, "ok": True}


async def run_agent_step() -> list[dict]:
    t0 = time.perf_counter()
    results = await asyncio.gather(
        tool("search", 0.3),
        tool("calc", 0.2),
        tool("browse", 0.4),
    )
    ms = (time.perf_counter() - t0) * 1000
    print(f"parallel elapsed≈{ms:.0f}ms")
    return list(results)


async def run_agent_step_sequential() -> list[dict]:
    t0 = time.perf_counter()
    results = [
        await tool("search", 0.3),
        await tool("calc", 0.2),
        await tool("browse", 0.4),
    ]
    ms = (time.perf_counter() - t0) * 1000
    print(f"sequential elapsed≈{ms:.0f}ms")
    return results


async def main() -> None:
    t0 = time.perf_counter()
    parallel = await run_agent_step()
    par_dt = time.perf_counter() - t0

    t0 = time.perf_counter()
    sequential = await run_agent_step_sequential()
    seq_dt = time.perf_counter() - t0

    assert len(parallel) == 3
    assert len(sequential) == 3
    assert par_dt < seq_dt * 0.7
    print("ok")


if __name__ == "__main__":
    asyncio.run(main())
```

可选加固（建议掌握合练）：

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

---

### 常见坑（自检清单）

| 错法 | 后果 |
|------|------|
| 创建协程却忘记 `await` / `create_task` | 业务没跑 + `RuntimeWarning` |
| 依次 `await` 却以为已经并发 | 时间仍是加法 |
| `async` 里 `time.sleep` / 同步 `requests` | 卡死整个循环 |
| 已有 loop 再 `asyncio.run` | 嵌套报错 |
| 假设 `gather` 按完成顺序返回 | 实际按传入顺序 |
| 假设 `gather` 失败会取消兄弟任务 | 默认不会（`TaskGroup` 另说） |
| 吞掉 `CancelledError` 当成功 | 取消语义损坏 |

**补充：协程未 await 的警示演示（看警告即可）**

```python
import asyncio
import warnings


async def work() -> str:
    return "x"


async def main() -> None:
    work()  # 错误示范：忘记 await
    await asyncio.sleep(0)


if __name__ == "__main__":
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            asyncio.run(main())
        finally:
            pass
    # 某些版本会在 GC 时报警；正确写法永远是 await work()
```

**补充：`gather` 保序断言**

```python
import asyncio


async def tag(name: str, sec: float) -> str:
    await asyncio.sleep(sec)
    return name


async def main() -> None:
    # b 更快完成，但 gather 仍按传入顺序返回
    out = await asyncio.gather(tag("a", 0.2), tag("b", 0.05))
    assert out == ["a", "b"]


asyncio.run(main())
```

---

### 本章速查

| API | 作用 |
|-----|------|
| `async def` / `await` | 定义与挂起协程 |
| `asyncio.run` | 脚本入口 |
| `create_task` | 尽快调度 |
| `gather` | 并发等待多个（按传入顺序返回） |
| `wait_for` | 超时 |
| `CancelledError` | 取消协作 |

常见坑：协程未 await；`time.sleep` 堵 loop；误以为写了 async 就自动并发。
