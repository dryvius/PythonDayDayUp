# 练习：数据结构与算法精要

> 对应文档：[`docs/04-systems-basics/04-dsa-essentials.md`](../../docs/04-systems-basics/04-dsa-essentials.md)  
> 状态：`已完成出题`  
> 建议用时：50～80 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：list/dict/set/deque/堆的选型与复杂度直觉。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/04-systems-basics/04-dsa-essentials/
```

4. Python ≥ 3.11；代码题给可跑实现 + assert。先做题再看答案。

---

## 热身题（建议先做）

### W1. `in` 的直觉

**要求**：`x in list` 与 `x in set`，哪个通常更快？为什么（一句话）？

**验收**：set 平均 O(1)；list 要扫描。

---

### W2. dict 保序

**要求**：现代 Python（3.7+）里普通 `dict` 迭代顺序默认怎样？

**验收**：按插入顺序。

---

### W3. 堆是不是全排序 list？

**要求**：`heapq` 维护的 list 打印出来是否一定全局有序？Top-K 一次性场景更常用哪个辅助函数？

**验收**：不是全有序（只保证堆性质）；一次性 Top-K 常用 `nlargest` / `nsmallest`。

---

### W4. 何时不该用 list 做成员判断

**要求**：若每步都要判断「这个 tool 名是否已经调用过」，且调用名集合可能到成千上万，用 `list` 还是 `set`？为什么？

**验收**：用 `set`；`in list` 是 O(n)，热路径会慢。

---

## 基础题（必做）

### B1. 复杂度对照（书面）

对以下操作给出粗复杂度：`list.append`、`x in list`、`x in set`、`dict[key]`、`sorted(list)`。

**验收**：`b1_notes.md` 五条齐全。

---

### B2. 去重保序

输入字符串列表（含重复），返回去重且保留首次出现顺序的新列表。  
（提示：`dict.fromkeys` 或 set 辅助）

**验收**：有 assert；例如 `["a","b","a"] → ["a","b"]`。

---

### B3. Top-K

给定 chunk 字典列表（含 `score`），返回分数最高的 K 条（可用 `heapq.nlargest` 或 `sorted`）。  
用断言验证顺序（从高到低）。

**验收**：assert 通过。

---

### B4. 结构选型题

为场景选结构并一句理由：

1. 工具注册表  
2. 已调用工具名集合  
3. 最近 50 条日志  
4. 持续维护前 10 高分文档  

**验收**：写在 `b4_notes.md`。

---

## 进阶题（建议至少做 1 题）

### A1. 实现 `select_chunks`

按文档综合例子完成：strip → 按文本留最高分 → Top-K。写 2～3 个手工 assert。

**验收**：与文档 demo 预期一致：`beta/gamma` 进 Top-2，空白文本丢弃，`alpha` 聚合后为 0.7。

---

### A2. deque 窗口

用 `collections.deque(maxlen=5)` 模拟「只保留最近 5 个 tool 名」，演示超出后自动丢掉最旧。

**验收**：打印或 assert 能看出窗口滑动。

---

## 挑战题（可选）

### C1. 图直觉（书面）

把「研究员 Agent → 搜索工具 → 写作 Agent」画成 3～5 个节点的图，标明边含义。

**验收**：`c1_notes.md` 有图 + 边解释。

---

## 模块 04 通关自检

- [ ] 能用 OS 术语解释阻塞/句柄
- [ ] 见到 HTTP 状态码知道第一反应
- [ ] 能为 I/O 场景选并发模型
- [ ] 能做基础结构取舍（dict/set/堆）

完成后进入模块 05《Python 异步编程》。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W2
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

### W1 参考答案

通常 **`x in set` 更快**：哈希平均 O(1)；`x in list` 要线性扫描 O(n)。

### W2 参考答案

按**插入顺序**迭代（CPython 3.7+ 语言保证）。

---

### B1 思路 + 参考答案

**`b1_notes.md` 完整参考作答**

```markdown
# B1 粗复杂度（教学量级）

| 操作 | 粗复杂度 | 备注 |
|------|----------|------|
| list.append | 摊销 O(1) | 偶尔扩容 |
| x in list | O(n) | 最坏扫全表 |
| x in set | 平均 O(1) | 哈希 |
| dict[key] | 平均 O(1) | 哈希取值 |
| sorted(list) | O(n log n) | 比较排序 |
```

---

### B2 思路 + 参考答案

```python
# b2_dedupe.py
def dedupe_keep_order(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


assert dedupe_keep_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
assert dedupe_keep_order([]) == []
assert dedupe_keep_order(["x", "x", "x"]) == ["x"]
print("ok")
```

另一种写法（显式）：

```python
def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out
```

---

### B3 思路 + 参考答案

```python
# b3_topk.py
import heapq


def top_k_chunks(chunks: list[dict], k: int) -> list[dict]:
    return heapq.nlargest(k, chunks, key=lambda c: c["score"])


demo = [
    {"text": "a", "score": 0.2},
    {"text": "b", "score": 0.9},
    {"text": "c", "score": 0.5},
    {"text": "d", "score": 0.8},
]

top2 = top_k_chunks(demo, 2)
assert [c["text"] for c in top2] == ["b", "d"]
assert top2[0]["score"] >= top2[1]["score"]
print("ok")
```

---

### B4 思路 + 参考答案

**`b4_notes.md` 完整参考作答**

```markdown
# B4 结构选型

1. 工具注册表 → **dict[str, Callable]**  
   理由：按名字 O(1) 查找并调用；天然适合 registry。

2. 已调用工具名集合 → **set[str]**  
   理由：只需判存在/去重，不需顺序与分数。

3. 最近 50 条日志 → **deque(maxlen=50)**  
   理由：固定窗口、两端操作便宜，自动丢最旧。

4. 持续维护前 10 高分文档 → **heapq（固定大小堆）或定期 nlargest**  
   理由：要的是动态 Top-K，而不是全量排序后切片（n 很大时更疼）。
```

---

### A1 思路 + 参考答案

```python
# a1_select_chunks.py
import heapq
from collections import deque


def select_chunks(
    chunks: list[dict],
    k: int = 3,
    window: int = 20,
) -> list[dict]:
    best_by_text: dict[str, dict] = {}
    for c in chunks:
        text = c["text"].strip()
        if not text:
            continue
        prev = best_by_text.get(text)
        if prev is None or c["score"] > prev["score"]:
            best_by_text[text] = {**c, "text": text}

    top = heapq.nlargest(k, best_by_text.values(), key=lambda c: c["score"])

    recent_sources: deque[object] = deque(maxlen=window)
    for c in top:
        recent_sources.append(c.get("source"))
    _ = recent_sources
    return top


demo = [
    {"text": "  alpha  ", "score": 0.4, "source": "doc-1"},
    {"text": "beta", "score": 0.9, "source": "doc-2"},
    {"text": "alpha", "score": 0.7, "source": "doc-3"},
    {"text": "gamma", "score": 0.8, "source": "doc-4"},
    {"text": "  ", "score": 0.99, "source": "doc-5"},
]

result = select_chunks(demo, k=2)
pairs = [(c["text"], c["score"]) for c in result]
assert pairs == [("beta", 0.9), ("gamma", 0.8)]

# 额外用例：k 大于去重后数量
assert len(select_chunks(demo, k=10)) == 3  # alpha/beta/gamma

# 全空白
assert select_chunks([{"text": "  ", "score": 1.0}], k=1) == []
print("ok")
```

---

### A2 思路 + 参考答案

```python
# a2_deque_window.py
from collections import deque


def main() -> None:
    window: deque[str] = deque(maxlen=5)
    tools = ["search", "calc", "browse", "embed", "rerank", "search", "summarize"]
    for name in tools:
        window.append(name)
        print(list(window))

    assert list(window) == ["browse", "embed", "rerank", "search", "summarize"]
    # 最早的 search/calc 已被挤出


if __name__ == "__main__":
    main()
```

---

### C1 思路 + 参考答案

**`c1_notes.md` 完整参考作答**

```markdown
# C1 图直觉

```text
[User Question]
       |  (query)
       v
[Researcher Agent] ----tool_call(search)----> [Search Tool]
       |                                              |
       | <--------- documents / snippets -------------
       |  (write_request + evidence)
       v
[Writer Agent] ----> [Final Answer]
```

边含义：
1. User → Researcher：用户问题进入研究编排。
2. Researcher → Search Tool：发出检索工具调用（参数含 query）。
3. Search Tool → Researcher：返回文档片段。
4. Researcher → Writer：把证据与写作指令交给写作 Agent。
5. Writer → Final Answer：产出最终答复。

这就是「多节点 Agent + 工具」的最小图；边可以带状态（messages、scores）。
```

---

### W3 参考答案

`heapq` 只保证堆顶关系，**打印整个 list 不一定升序/降序**。  
一次性取 Top-K：优先 `heapq.nlargest(k, iterable, key=...)`（或数据很小直接 `sorted(...)[:k]`）。

### W4 参考答案

用 **`set`**（或 dict 键）。热路径上反复 `name in already_called_list` 会变成平方级成本；`set` 平均 O(1)。

---

### 常见坑（自检清单）

| 错法 | 后果 |
|------|------|
| 用 `set(texts)` 去重 chunk | 丢掉 score/source 元数据 |
| 聚合键未 `strip` | `"alpha"` 与 `"  alpha  "` 变两条 |
| 把 heap 当全排序数组下标乱取 | 逻辑错 |
| 小 n 却过早微优化堆结构 | 可读性下降，收益为零 |
| 用 list 做大规模成员判断 | 延迟毛刺 |
| 窗口日志用普通 list 手动 `pop(0)` | 频繁 O(n)；应用 `deque` |

**补充：registry + 已调用集合的最小可跑示例**

```python
from collections.abc import Callable

registry: dict[str, Callable[..., object]] = {
    "search": lambda q: [f"doc:{q}"],
    "calc": lambda expr: 42,
}
called: set[str] = set()


def call(name: str, *args: object) -> object:
    if name not in registry:
        raise KeyError(name)
    called.add(name)
    return registry[name](*args)


assert call("search", "RAG") == ["doc:RAG"]
assert "search" in called
assert "calc" not in called
```

**补充：Top-K 与 sorted 等价性（小数据）**

```python
import heapq

chunks = [
    {"text": "a", "score": 0.2},
    {"text": "b", "score": 0.9},
    {"text": "c", "score": 0.5},
]
by_heap = heapq.nlargest(2, chunks, key=lambda c: c["score"])
by_sorted = sorted(chunks, key=lambda c: c["score"], reverse=True)[:2]
assert by_heap == by_sorted
```

**补充：deque 窗口与 list 切片对照**

```python
from collections import deque

# deque：自动丢最旧
w: deque[str] = deque(maxlen=3)
for x in ["a", "b", "c", "d"]:
    w.append(x)
assert list(w) == ["b", "c", "d"]

# list 切片：每次新建，也能做窗口，但语义靠你自己维护
hist = ["a", "b", "c", "d"]
assert hist[-3:] == ["b", "c", "d"]
```

**一句话选型口诀**

```text
按名查找 → dict
是否出现过 → set
最近 N 条 → deque(maxlen=N)
最高/最低 K 条 → heapq.nlargest / nsmallest
只要有序遍历小列表 → list 也够用
```

---

### 本章速查

| 结构 | 典型用途 |
|------|----------|
| dict | 注册表、按文本聚合、保序去重（`dict.fromkeys`） |
| set | 去重、成员判断 |
| deque | 固定窗口日志/工具名 |
| heapq.nlargest | Top-K |
| list | 有序序列、小数据扫描可接受 |
