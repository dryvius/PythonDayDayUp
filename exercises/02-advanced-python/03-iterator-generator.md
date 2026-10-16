# 练习：Iterator / Generator

> 对应文档：[`docs/02-advanced-python/03-iterator-generator.md`](../../docs/02-advanced-python/03-iterator-generator.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/02-advanced-python/03-iterator-generator/
```

4. 先做题再看文末提示；注意生成器耗尽后不可二次遍历。

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

示例：

```python
list(batched([1, 2, 3, 4, 5], 2))
# [[1, 2], [3, 4], [5]]
```

要求：`size <= 0` 时抛 `ValueError`。

**验收**：上例通过；空输入产出空；最后一组可短于 `size`。

---

### B3. 惰性过滤检索结果

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

要求：

1. `iter_hits` 必须是生成器（函数里有 `yield`）
2. 分数过滤与 limit 截断在物化前完成（用 `for` + `break` 或生成器管道）
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

再用断言证明：`join_stream(fake_tokens("Agent")) == "Agent"`。

**验收**：通过断言；额外打印「边消费边观察」也可以（例如每来一个 token 打印长度）。

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

**验收**：管道结果稳定；`merged` 含两路全部（或按你定义的顺序）。

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
    - 同时 yield/print 当前已累计文本（二选一）
    - 最终返回完整文本
    """
```

目标是模拟前端「打字机效果」的数据源侧。不必真 sleep（可加可选 delay）。

**验收**：最终文本等于输入；过程中能看到逐步变长的中间态（打印即可）。

---

### C2. 提前停止是否少干活？

写一个生成器，在每次 `yield` 前给计数器 +1。  
消费端只取前 3 个就 `break`。  
断言计数器 == 3（而不是全部）。

**验收**：证明惰性 + break 能减少实际产量（在纯 Python 生成器场景）。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成
- [ ] 能口述 iterable vs iterator，以及生成器为何常一次性
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

外层类只保存 start/end；`__iter__` 返回内部迭代器实例，迭代器里实现 `__next__`。

</details>

<details>
<summary>B2 提示</summary>

累加到 `size` 就 `yield batch` 并清空；循环结束后若 batch 非空再 yield 一次。

</details>

<details>
<summary>B3 提示</summary>

```python
for hit in iter_hits(query):
    if hit["score"] < min_score:
        continue
    ...
    if len(selected) >= limit:
        break
```

</details>

<details>
<summary>B4 提示</summary>

`return "".join(tokens)` 即可；`fake_tokens` 用 `for ch in text: yield ch`。

</details>

<details>
<summary>A1 思路</summary>

参考文档第 5 节。`yield from a; yield from b` 即可合并。

</details>

<details>
<summary>C1 思路</summary>

切片 `text[i:i+chunk_size]`，`i` 步进；或复用 B2 的 `batched` 思路作用于字符序列。

</details>
