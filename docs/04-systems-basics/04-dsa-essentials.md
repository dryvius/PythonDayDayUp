# 数据结构与算法精要

> 所属模块：`04-systems-basics` · 计算机与服务端基础  
> 状态：`已完成正文`  
> 建议学时：2～4 小时  
> 对应练习：[`exercises/04-systems-basics/04-dsa-essentials.md`](../../exercises/04-systems-basics/04-dsa-essentials.md)

## 本章定位

- **本章角色**：用「复杂度直觉 + 结构取舍」服务工程选型，而不是变成算法竞赛课。
- **和 Agent**：消息队列选型、检索 Top-K、去重、缓存、图状 Multi-Agent 路由，都依赖这些直觉。

## 学习目标

1. 看懂大 O 的工程含义（不是证明题）。
2. 对 list/dict/set/堆等结构做正确取舍。
3. 能把结构选择连到缓存、队列、检索等场景。
4. 知道刷题是加分项，不是本路线主线。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 复杂度直觉、常用结构取舍、工程选型关系 | 能解释为什么选 dict/堆 |
| **建议掌握** | 哈希/堆/图场景 | 能举例 |
| **了解即可** | 刷题路线 | 可选 |

---

## 1. 为什么要学（精要版）

Agent 里你会写：

```text
历史消息截断前先遍历过滤
工具名去重
按分数取 Top-K
LRU 缓存 prompt 结果
多 Agent 路由图
```

选错结构：

- n 大时突然变慢
- 去重失效
- Top-K 每次全排序浪费

---

## 2. 必掌握：复杂度直觉

常见：

| 写法 | 粗直觉 |
|------|--------|
| O(1) | 基本定数时间：dict 平均查找 |
| O(log n) | 每次砍半：堆操作、有序结构 |
| O(n) | 扫一遍 |
| O(n log n) | 排序 |
| O(n²) | 双层循环，n 上千要警惕 |

工程解读：

- n=20 的消息列表：怎么写都行
- n=10⁵ 文档片段：要认真
- 先测量再优化；但**明显的 O(n²) 热路径**要避免

```python
# 慢：每次 membership 都 O(n)
seen = []
for x in items:
    if x not in seen:
        seen.append(x)

# 快：平均 O(1) 查询
seen_set = set()
...
```

---

## 3. 必掌握：常用结构取舍

| 结构 | 擅长 | 不擅长 | Agent 例子 |
|------|------|--------|------------|
| `list` | 有序、尾部增删 | 中间插入、按值查找 | 消息历史 |
| `dict` | 键查、映射 | 无序依赖（3.7+ 有序但是语义上当映射用） | 工具注册表 |
| `set` | 去重、成员检测 | 要下标访问 | 已调用工具集合 |
| `deque` | 两头高效增删 | 中间随机访问 | 固定长度窗口 |
| `heapq` | 持续 Top-K / 优先队列 | 任意删除复杂 | 维护最高分 chunk |

### Top-K 直觉

```python
import heapq

scores = [0.2, 0.9, 0.4, 0.8, 0.7]
print(heapq.nlargest(3, scores))  # [0.9, 0.8, 0.7]
```

小 K、大 n：堆往往优于每次全排序（概念上记住即可）。

---

## 4. 必掌握：和工程选型的关系

| 工程组件 | 背后结构直觉 |
|----------|--------------|
| Redis 缓存 | 哈希表 + TTL |
| 消息队列 | 队列；优先级队列用堆思想 |
| 向量检索 | 近似最近邻索引（比暴力算相似度） |
| LRU 缓存 | 哈希 + 双向链表思想 |
| 路由/工作流 | 图（节点+边） |

你不一定手写这些，但要听懂文档在说什么。

---

## 5. 建议掌握：哈希 / 堆 / 图场景

### 哈希

- 平均 O(1) 查；最坏需了解可能退化（一般知道即可）
- 键必须可哈希：list 不行，tuple（元素可哈希）可以

### 堆

- 优先处理“最重要/最高分/最早到期”
- Agent：优先调度、Top-K 维护

### 图

- LangGraph 一类工作流就是图
- Multi-Agent：节点是 agent，边是移交关系
- 算法面：BFS/DFS 扫盲即可

---

## 6. 了解即可：刷题路线（非主线）

若以后面试或想加功力：

```text
数组/哈希 → 双指针 → 栈队列 → 二叉树 → BFS/DFS → 堆 → 基础 DP
```

本路线主线仍是：**工程 + Agent**。刷题当加餐，别停更。

---

## 7. 综合小例子：检索后处理选型

```python
import heapq
from collections import deque


def select_chunks(chunks: list[dict], k: int = 3, window: int = 20) -> list[dict]:
    # 去重：set
    best_by_text: dict[str, dict] = {}
    for c in chunks:
        text = c["text"].strip()
        if not text:
            continue
        prev = best_by_text.get(text)
        if prev is None or c["score"] > prev["score"]:
            best_by_text[text] = {**c, "text": text}

    # Top-K：堆
    top = heapq.nlargest(k, best_by_text.values(), key=lambda c: c["score"])

    # 可选：保留最近 window 的来源 id
    recent_sources = deque(maxlen=window)
    for c in top:
        recent_sources.append(c.get("source"))
    return top
```

---

## 8. 练习指引

[`exercises/04-systems-basics/04-dsa-essentials.md`](../../exercises/04-systems-basics/04-dsa-essentials.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能解释 dict/set 相对 list 的查找差异
- [ ] 知道 Top-K 可用堆思想
- [ ] 能把缓存/队列/图对应到工程组件

### 模块 04 收官

```text
OS → 网络HTTP → 并发模型 → DSA精要
```

下一模块：[`../05-async-python/README.md`](../05-async-python/README.md) —— asyncio 实战（Agent 分水岭）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[并发模型](./03-concurrency-models.md)
- 下一模块：[Python 异步编程](../05-async-python/README.md)
