# 模块 05-async-python：Python 异步编程

> 状态：`两章正文与练习已全部完成` · 预计周期：1～2 周

## 模块目标

掌握 asyncio，跨过 Agent 开发分水岭。

## 为什么现在学

LLM / Tool / DB / HTTP 全是 I/O，异步几乎是标配。不会异步，就很难把 Agent 延迟和吞吐做上去，也难看懂 FastAPI / 现代 SDK。

## 章节目录

1. [asyncio 基础](./01-asyncio-fundamentals.md) · [练习](../../exercises/05-async-python/01-asyncio-fundamentals.md)
2. [asyncio 进阶实践](./02-asyncio-advanced.md) · [练习](../../exercises/05-async-python/02-asyncio-advanced.md)

## 建议学习方式

1. 先把基础章的 `gather` / Task / 超时跑通，再进限流与 HTTP（每章保留知识地图骨架；知识点按「为什么 → 怎么写 → 跑一下 → 易错点」推进）
2. 每一题都用 `time.perf_counter()` 亲眼看并发收益
3. 刻意制造一次 `time.sleep` 卡循环，建立肌肉记忆；先自己写再对照文档

## 模块自检

- [ ] 能解释事件循环与 await 让出的含义
- [ ] 能用 gather/Task 并行多个 I/O
- [ ] 能用 Semaphore 做限流
- [ ] 能用 AsyncClient（或等价物）发异步请求
- [ ] 知道阻塞调用的危害与 `to_thread` 逃生舱

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[计算机与服务端基础](../04-systems-basics/README.md)
- 下一模块：[Web 后端](../06-web-backend/README.md)
