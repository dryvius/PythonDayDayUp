# 练习：并发模型

> 对应文档：[`docs/04-systems-basics/03-concurrency-models.md`](../../docs/04-systems-basics/03-concurrency-models.md)  
> 状态：`已完成出题` · 建议用时：50～80 分钟

目录：`playground/04-systems-basics/03-concurrency-models/`

---

## 基础题（必做）

### B1. 并发 vs 并行（书面）

各举 1 个生活例子 + 1 个 Agent 例子。

### B2. 串行 vs 线程池计时

按文档实现 `fake_io` + `sequential` + `threaded`，打印两种总耗时，确认线程版更快。

### B3. GIL 选择题（书面）

判断并简述理由：

1. 纯 Python 计算斐波那契加速，多线程通常？  
2. 多个 `time.sleep` / 网络等待，多线程通常？

### B4. 选型题

为下列场景选：asyncio / 线程池 / 多进程 / 保持串行，并一句理由：

1. 同时调 10 个 LLM embedding HTTP  
2. 同步 SDK 且短期不想改  
3. 对 200MB 文本做 CPU 正则重处理  
4. 三步严格依赖：检索→拼prompt→生成

---

## 进阶题（建议）

### A1. ThreadPoolExecutor map

用线程池并行跑 5 个不同 delay 的 fake_io，收集结果。

### A2. 竞态演示（小心）

两个线程对同一 `counter += 1` 循环很多次，观察是否总等于期望；写笔记说明风险。（次数可调小以免过慢）

---

## 挑战题（可选）

### C1. 给「同步工具 + 异步编排」画架构草图

说明哪里用 asyncio，哪里用 `to_thread`/线程池。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
