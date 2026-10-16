# 练习：asyncio 进阶实践

> 对应文档：[`docs/05-async-python/02-asyncio-advanced.md`](../../docs/05-async-python/02-asyncio-advanced.md)  
> 状态：`已完成出题` · 建议用时：70～100 分钟

目录：`playground/05-async-python/02-asyncio-advanced/`

---

## 基础题（必做）

### B1. Semaphore

10 个任务，每个 sleep 0.2s，Semaphore=2。  
打印总耗时，说明为何大约是「5 个波次」而不是「10 串行」或「全并行」。

### B2. 分批 gather

实现 `map_batched(items, fn, batch_size)`，对 `range(25)` 做假处理，`batch_size=10`，验证结果长度 25。

### B3. 异步 HTTP（可选联网）

用 `httpx.AsyncClient` GET `https://httpbin.org/get`（或任意可达 URL），打印 status_code。  
若网络不可用：用 `respx`/`unittest.mock` 或本地假客户端代替，并注明。

### B4. 阻塞危害（认知实验）

在 async 函数里用 `time.sleep(0.5)` 跑两个并发任务，对比改成 `asyncio.sleep` 的耗时差异；写 3 行结论。

---

## 进阶题（建议）

### A1. 复用 AsyncClient

把 client 提到外层 `async with AsyncClient`，并发请求 3 个 URL（可重复同一 mock URL），对比「每请求新建 client」的代码结构差异（笔记即可）。

### A2. async for 流

实现 `token_stream`，`async for` 拼接完整字符串，断言等于原文。

---

## 挑战题（可选）

### C1. 限流工具运行时

实现文档 `run_tools` + `ToolCall`，`limit=2`，4 个工具，打印结果与耗时。

### C2. `to_thread` 包装同步函数

把一个同步 `time.sleep` 函数放到 `asyncio.to_thread`，在 gather 里并发跑 3 次，观察是否重叠等待。

---

## 模块 05 通关自检

- [ ] 会 async/await/Task/gather
- [ ] 会超时取消
- [ ] 会 Semaphore 限流
- [ ] 会异步 HTTP 基本用法
- [ ] 清楚不能在事件循环里阻塞

完成后进入模块 06《Web 后端》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
