# 练习：数据结构与算法精要

> 对应文档：[`docs/04-systems-basics/04-dsa-essentials.md`](../../docs/04-systems-basics/04-dsa-essentials.md)  
> 状态：`已完成出题` · 建议用时：50～80 分钟

目录：`playground/04-systems-basics/04-dsa-essentials/`

---

## 基础题（必做）

### B1. 复杂度对照（书面）

对以下操作给出粗复杂度：`list.append`、`x in list`、`x in set`、`dict[key]`、`sorted(list)`。

### B2. 去重保序

输入字符串列表（含重复），返回去重且保留首次出现顺序的新列表。  
（提示：`dict.fromkeys` 或 `set` 辅助）

### B3. Top-K

给定 chunk 字典列表（含 `score`），返回分数最高的 K 条（可用 `heapq.nlargest` 或 `sorted`）。  
用断言验证顺序。

### B4. 结构选型题

为场景选结构并一句理由：工具注册表、已调用工具名集合、最近 50 条日志、持续维护前 10 高分文档。

---

## 进阶题（建议）

### A1. 实现 `select_chunks`

按文档综合例子完成：strip → 按文本留最高分 → Top-K。写 2～3 个测试用例（手工 assert 即可）。

### A2. deque 窗口

用 `collections.deque(maxlen=5)` 模拟「只保留最近 5 个 tool 名」，演示超出后自动丢掉最旧。

---

## 挑战题（可选）

### C1. 图直觉（书面）

把一个「研究员 Agent → 搜索工具 → 写作 Agent」画成 3～5 个节点的图，标明边含义。

---

## 模块 04 通关自检

- [ ] 能用 OS 术语解释阻塞/句柄
- [ ] 见到 HTTP 状态码知道第一反应
- [ ] 能为 I/O 场景选并发模型
- [ ] 能做基础结构取舍（dict/set/堆）

完成后进入模块 05《Python 异步编程》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
