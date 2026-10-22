# 练习：Iterator / Generator

> 对应文档：[`docs/02-advanced-python/03-iterator-generator.md`](../../docs/02-advanced-python/03-iterator-generator.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先分清 iterable / iterator / `yield`，再写管道与流式拼接。
4. 建议代码目录：

```text
playground/02-advanced-python/03-iterator-generator/
```

5. 先做题再看文末答案；注意生成器耗尽后不可二次遍历。

---

## 热身题（建议先做）

### W1. `iter` / `next` 手动走两步

**给定**：`nums = [10, 20, 30]`。

**要求**：`it = iter(nums)`，连续 `next` 两次，观察值。

**验收**：

```python
it = iter([10, 20, 30])
assert next(it) == 10
assert next(it) == 20
```

---

### W2. 最小生成器函数

**要求**：`def countdown(n):` 从 `n` 降到 `1` 依次 `yield`。

**验收**：`list(countdown(3)) == [3, 2, 1]`。

---

### W3. 生成器表达式

**要求**：用生成器表达式得到平方：`(x * x for x in range(4))`，再 `list(...)`。

**验收**：结果为 `[0, 1, 4, 9]`。

---

### W4. 耗尽后再 `list` 为空

**要求**：对同一生成器连续两次 `list(gen)`，用断言确认第二次是 `[]`。

**验收**：理解「生成器默认一次性」。

---

## 基础题（必做）

### B1. 手写迭代器类

实现 `RangeLike(start: int, end: int)`（不含 `end`）：

- 支持 `for x in RangeLike(1, 4)` 得到 `1, 2, 3`
- 支持 `list(RangeLike(1, 4))` 多次调用都得到完整结果  
  （提示：`__iter__` 每次返回新迭代器对象）

**验收**：`list(RangeLike(1, 4)) == [1, 2, 3]` 连续两次成立。

---

### B2. 生成器函数：`batched`

实现：

```python
def batched(items, size: int):
    """把可迭代对象按固定大小分组产出 list。"""
```

示例：`list(batched([1, 2, 3, 4, 5], 2))` → `[[1, 2], [3, 4], [5]]`

**要求**：`size <= 0` 时抛 `ValueError`。

**验收**：上例通过；空输入产出空；最后一组可短于 `size`。

---

### B3. 惰性过滤检索结果（贴近 RAG）

给定假数据源函数（请按生成器实现，不要一次 return 全 list）：

```python
def iter_hits(query: str):
    # yield 若干 {text, score}
    ...
```

再实现：

```python
def top_texts(query: str, *, min_score: float = 0.6, limit: int = 3):
    """惰性过滤 + 截断，最终返回 list[str]（只含 text）。"""
```

**要求**：

1. `iter_hits` 必须是生成器（函数里有 `yield`）
2. 分数过滤与 limit 截断在物化前完成
3. 自己构造至少 5 条数据，其中有低分与高分

**验收**：返回条数不超过 `limit`；不含低分文本。

---

### B4. 流式拼接

实现：

```python
def fake_tokens(text: str):
    """逐字 yield。"""

def join_stream(tokens) -> str:
    """消费可迭代 tokens，拼成完整字符串。"""
```

**验收**：`join_stream(fake_tokens("Agent")) == "Agent"`。

---

## 进阶题（建议至少做 1 题）

### A1. 生成器管道三件套

实现并串联：

```python
def clean(chunks): ...
def filter_score(chunks, min_score=0.6): ...
def take(chunks, n): ...
```

全部用 `yield`；最后 `list(take(filter_score(clean(raw())), 2))` 验证。

再写一版用 `yield from` 的 `merged()`：把两个 chunk 流拼成一个流。

**验收**：管道结果稳定；`merged` 含两路全部。

---

### A2. 一次性耗尽实验（认知题 + 代码）

```python
gen = (x for x in range(3))
```

1. 对 `gen` 连续两次 `list(gen)`，记录结果
2. 写一段注释解释为什么
3. 给出「需要多次使用」的两种修法（重新创建 / 物化）

**验收**：有代码输出 + 简明注释。

---

## 挑战题（可选）

### C1. 迷你 LLM 流式回放器

实现：

```python
def replay_tokens(text: str, chunk_size: int = 2):
    """按 chunk_size 个字符一组 yield（最后一组可更短）。"""

def run_ui(text: str) -> str:
    """
    消费 replay_tokens：
    - 每来一个 chunk 就追加到 buffer
    - 同时 print 当前已累计文本
    - 最终返回完整文本
    """
```

**验收**：最终文本等于输入；过程中能看到逐步变长的中间态。

---

### C2. 提前停止是否少干活？

写一个生成器，在每次 `yield` 前给计数器 +1。  
消费端只取前 3 个就 `break`。  
断言计数器 == 3（而不是全部）。

**验收**：证明惰性 + break 能减少实际产量。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成
- [ ] 能口述 iterable vs iterator，以及生成器为何常一次性
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。

### W1 参考答案

```python
it = iter([10, 20, 30])
assert next(it) == 10
assert next(it) == 20
```

### W2 参考答案

```python
def countdown(n: int):
    while n >= 1:
        yield n
        n -= 1


assert list(countdown(3)) == [3, 2, 1]
```

### W3 参考答案

```python
gen = (x * x for x in range(4))
assert list(gen) == [0, 1, 4, 9]
```

### W4 参考答案

```python
gen = (x for x in range(3))
assert list(gen) == [0, 1, 2]
assert list(gen) == []  # 已耗尽
```

### B1 思路 + 参考答案

**思路**

外层类只保存 start/end；`__iter__` 每次返回**新的**内部迭代器，迭代器实现 `__next__`。

**参考答案**

```python
class _RangeIterator:
    def __init__(self, start: int, end: int) -> None:
        self._current = start
        self._end = end

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self._current >= self._end:
            raise StopIteration
        value = self._current
        self._current += 1
        return value


class RangeLike:
    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end

    def __iter__(self):
        # 每次新迭代器 → list(...) 可重复
        return _RangeIterator(self.start, self.end)


assert list(RangeLike(1, 4)) == [1, 2, 3]
assert list(RangeLike(1, 4)) == [1, 2, 3]
assert [x for x in RangeLike(0, 3)] == [0, 1, 2]
```

### B2 思路 + 参考答案

**思路**

累加到 `size` 就 `yield batch` 并清空；循环结束后若 batch 非空再 yield 一次。

**参考答案**

```python
from collections.abc import Iterable, Iterator


def batched(items: Iterable, size: int) -> Iterator[list]:
    if size <= 0:
        raise ValueError("size must be > 0")
    batch: list = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


assert list(batched([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
assert list(batched([], 2)) == []
try:
    list(batched([1], 0))
    raise AssertionError("should have raised")
except ValueError:
    pass
```

### B3 思路 + 参考答案

**思路**

1. `iter_hits` 用 `yield` 模拟检索流。
2. `top_texts` 边读边过滤，凑够 `limit` 就 `break`，避免无谓物化。

**参考答案**

```python
def iter_hits(query: str):
    # 假数据：混入低分，模拟检索噪声
    data = [
        {"text": f"{query} 基础概念", "score": 0.9},
        {"text": "无关噪音", "score": 0.2},
        {"text": f"{query} 实战技巧", "score": 0.75},
        {"text": "低相关", "score": 0.4},
        {"text": f"{query} 进阶", "score": 0.68},
        {"text": f"{query} 评测", "score": 0.81},
    ]
    for item in data:
        yield item


def top_texts(
    query: str,
    *,
    min_score: float = 0.6,
    limit: int = 3,
) -> list[str]:
    selected: list[str] = []
    for hit in iter_hits(query):
        if hit["score"] < min_score:
            continue
        selected.append(hit["text"])
        if len(selected) >= limit:
            break
    return selected


texts = top_texts("RAG", min_score=0.6, limit=3)
assert len(texts) <= 3
assert all("噪音" not in t and "低相关" not in t for t in texts)
assert texts == ["RAG 基础概念", "RAG 实战技巧", "RAG 进阶"]
```

### B4 思路 + 参考答案

**思路**

`fake_tokens` 逐字 yield；`join_stream` 用 `"".join` 或累加字符串。

**参考答案**

```python
def fake_tokens(text: str):
    for ch in text:
        yield ch


def join_stream(tokens) -> str:
    return "".join(tokens)


assert join_stream(fake_tokens("Agent")) == "Agent"

# 边消费边观察长度
buf: list[str] = []
for t in fake_tokens("hi"):
    buf.append(t)
    print("len=", len(buf), "so_far=", "".join(buf))
```

### A1 思路 + 参考答案

**思路**

每个阶段都是生成器，组成惰性管道；`yield from` 可扁平合并两个流。

**参考答案**

```python
def raw():
    yield {"text": "  a  ", "score": 0.9}
    yield {"text": "", "score": 0.8}
    yield {"text": "b", "score": 0.4}
    yield {"text": "c", "score": 0.7}


def clean(chunks):
    for c in chunks:
        text = (c.get("text") or "").strip()
        if not text:
            continue
        yield {"text": text, "score": c["score"]}


def filter_score(chunks, min_score: float = 0.6):
    for c in chunks:
        if c["score"] >= min_score:
            yield c


def take(chunks, n: int):
    count = 0
    for c in chunks:
        if count >= n:
            break
        yield c
        count += 1


def merged(a, b):
    yield from a
    yield from b


result = list(take(filter_score(clean(raw())), 2))
assert result == [
    {"text": "a", "score": 0.9},
    {"text": "c", "score": 0.7},
]

m = list(
    merged(
        [{"text": "x", "score": 1.0}],
        [{"text": "y", "score": 1.0}],
    )
)
assert m == [{"text": "x", "score": 1.0}, {"text": "y", "score": 1.0}]
```

### A2 思路 + 参考答案

**思路**

生成器有内部指针；耗尽后继续迭代得到空。多次使用：重新创建生成器，或先 `list` 物化。

**参考答案**

```python
gen = (x for x in range(3))
first = list(gen)
second = list(gen)
print("first=", first, "second=", second)
assert first == [0, 1, 2]
assert second == []
# 原因：生成器迭代一次后内部状态耗尽，不能自动重头再来。

# 修法 1：需要时重新创建
def make_gen():
    return (x for x in range(3))


assert list(make_gen()) == [0, 1, 2]
assert list(make_gen()) == [0, 1, 2]

# 修法 2：物化成 list 复用
materialized = list(make_gen())
assert materialized == [0, 1, 2]
assert materialized == [0, 1, 2]
```

### C1 思路 + 参考答案

**思路**

按 `chunk_size` 切片 yield；UI 侧累加 buffer 并打印中间态（模拟打字机/流式输出）。

**参考答案**

```python
def replay_tokens(text: str, chunk_size: int = 2):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def run_ui(text: str) -> str:
    buffer: list[str] = []
    for chunk in replay_tokens(text, chunk_size=2):
        buffer.append(chunk)
        print("partial:", "".join(buffer))
    return "".join(buffer)


assert list(replay_tokens("Agent", 2)) == ["Ag", "en", "t"]
assert run_ui("Agent") == "Agent"
```

### C2 思路 + 参考答案

**思路**

生成器是协作式惰性：消费者 `break` 后，生产者不会继续跑完。

**参考答案**

```python
produced = {"n": 0}


def numbers(limit: int = 100):
    for i in range(limit):
        produced["n"] += 1  # yield 前计数 = 真正干活次数
        yield i


got: list[int] = []
for x in numbers(100):
    got.append(x)
    if len(got) == 3:
        break

assert got == [0, 1, 2]
assert produced["n"] == 3  # 不是 100
```
