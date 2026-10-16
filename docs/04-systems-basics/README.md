# 模块 04-systems-basics：计算机与服务端基础

> 状态：`四章正文与练习已全部完成` · 预计周期：1～2 周

## 模块目标

补齐前端背景下的系统直觉，避免一知半解。

## 为什么现在学

解释 Agent 超时、阻塞、网络失败、资源占用的「为什么」。后面学 asyncio、FastAPI、数据库时，会反复用到这些词。

## 章节目录

1. [操作系统基础](./01-os-basics.md) · [练习](../../exercises/04-systems-basics/01-os-basics.md)
2. [网络与 HTTP](./02-network-http.md) · [练习](../../exercises/04-systems-basics/02-network-http.md)
3. [并发模型](./03-concurrency-models.md) · [练习](../../exercises/04-systems-basics/03-concurrency-models.md)
4. [数据结构与算法精要](./04-dsa-essentials.md) · [练习](../../exercises/04-systems-basics/04-dsa-essentials.md)

## 建议学习方式

1. 本模块以**概念 + 小实验 + 选型题**为主，不必陷入内核/竞赛深水
2. 每章先吃「必掌握」，建议掌握用来回答“为什么选这个”
3. 结合你已写过的 Agent 小项目，对照超时、重试、去重、Top-K 等点

## 模块自检

- [ ] 能区分进程/线程，理解阻塞与句柄泄漏风险
- [ ] 能解读常见 HTTP 状态码并设计超时/重试边界
- [ ] 能在线程/进程/异步之间做合理选型，并理解 GIL
- [ ] 能用复杂度直觉选择 list/dict/set/堆
- [ ] 清楚本模块如何服务后续 asyncio 与后端

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Python 工程化](../03-engineering/README.md)
- 下一模块：[Python 异步编程](../05-async-python/README.md)
