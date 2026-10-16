# 练习：asyncio 基础

> 对应文档：[`docs/05-async-python/01-asyncio-fundamentals.md`](../../docs/05-async-python/01-asyncio-fundamentals.md)  
> 状态：`已完成出题` · 建议用时：60～90 分钟

目录：`playground/05-async-python/01-asyncio-fundamentals/`

---

## 基础题（必做）

### B1. 第一个协程

写 `async def hello(name)`，`await asyncio.sleep(0.05)` 后返回字符串；用 `asyncio.run` 打印。

### B2. 顺序 vs gather 计时

三个 `asyncio.sleep(0.2)`：

1. 依次 await —— 打印总耗时  
2. `gather` 并发 —— 打印总耗时  

断言并发版明显更接近 0.2s 量级而不是 0.6s。

### B3. create_task

用两个 `create_task` 启动假 I/O，再分别 await；打印完成。

### B4. wait_for 超时

故意 sleep 1 秒的协程，用 `timeout=0.2` 包住，捕获超时异常并打印 `"timed out"`。

---

## 进阶题（建议）

### A1. return_exceptions

`gather` 三个任务：两个成功、一个抛 `ValueError`，`return_exceptions=True`，打印结果列表类型分布。

### A2. 取消任务

启动长 sleep 任务，短暂等待后 `cancel`，捕获 `CancelledError`，在笔记写是否应继续 raise。

---

## 挑战题（可选）

### C1. 迷你并行工具步

实现文档综合例子 `run_agent_step`，并断言耗时 < 串行之和的 70%（阈值设宽松）。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
