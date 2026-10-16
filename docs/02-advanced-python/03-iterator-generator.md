# Iterator / Generator

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/02-advanced-python/03-iterator-generator.md`](../../exercises/02-advanced-python/03-iterator-generator.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：弄清 `for` 循环背后的协议，并用生成器做**惰性处理**——流式输出、大文件、检索结果管道都会用到。
- **和上一章关系**：数据模型里的 `__iter__` 在这里展开成完整的迭代故事。

## 学习目标（学完应能做到）

1. 说清可迭代对象（iterable）与迭代器（iterator）的区别。
2. 用手写类实现最小迭代协议，并用 `yield` 写出生成器函数。
3. 解释惰性求值的好处，能写出「过滤 → 转换 → 截断」的生成器管道。
4. 完成练习；`yield from` 会用，异步生成器先建立印象即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 迭代协议、生成器与 `yield`、惰性求值 | 能写、能讲、能做题 |
| **建议掌握** | 生成器管道、`yield from` | 会组装、会委托 |
| **了解即可** | 异步生成器预告 | 知道 `async for` 存在，后面异步章再用 |

---

## 1. 为什么要学（和 Agent 有什么关系）

Agent / LLM 场景里，数据经常是「边产生边消费」的：

```text
LLM 流式 token
    → 逐块打印 / 推送给前端
检索到的大量 chunk
    → 过滤分数 → 截断 Top-K → 再送进 prompt
读超大日志 / 语料文件
    → 不能一次性 read() 进内存
```

如果你只会「先做成完整 list 再处理」，在数据变大或要流式体验时就会卡。  
生成器让你写：

```python
for token in stream_tokens(response):
    print(token, end="", flush=True)
```

这一章就是为这种写法打底。

---

## 2. 必掌握：迭代协议

### 2.1 两个角色

| 角色 | 含义 | 关键方法 |
|------|------|----------|
| **Iterable（可迭代）** | 能提供迭代器的对象 | `__iter__` → 返回 iterator |
| **Iterator（迭代器）** | 能产出下一个值的对象 | `__next__`；通常也实现 `__iter__` 返回自己 |

`for` 循环大致做了这些事：

```text
it = iter(obj)          # 调 obj.__iter__()
while True:
    try:
        x = next(it)    # 调 it.__next__()
    except StopIteration:
        break
    # 循环体使用 x
```

### 2.2 你每天都在用

```python
for x in [1, 2, 3]:
    print(x)

for key in {"a": 1}:
    print(key)

for line in open("notes.txt", encoding="utf-8"):
    print(line.strip())
```

list / dict / 文件对象都是可迭代的；`for` 自动帮你取迭代器。

### 2.3 手写一个最小迭代器

```python
class CountDown:
    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


for n in CountDown(3):
    print(n)
# 3
# 2
# 1
```

要点：

- 耗尽后继续 `next(...)` 应持续抛 `StopIteration`
- 迭代器通常是**一次性**的：走完就空了

```python
it = CountDown(2)
print(list(it))  # [2, 1]
print(list(it))  # []   ← 再取就空了
```

若希望每次 `for` 都重新开始，让容器的 `__iter__` **每次返回新迭代器**：

```python
class CountDownFactory:
    def __init__(self, start: int) -> None:
        self.start = start

    def __iter__(self):
        return CountDown(self.start)
```

### 2.4 `iter()` / `next()`

```python
it = iter(["a", "b"])
print(next(it))           # a
print(next(it))           # b
print(next(it, "end"))    # end（给默认值，避免 StopIteration）
```

---

## 3. 必掌握：生成器与 `yield`

手写 `__iter__`/`__next__` 很啰嗦。生成器函数用 `yield` 自动变成迭代器。

### 3.1 最小生成器

```python
def count_down(start: int):
    while start > 0:
        yield start
        start -= 1


for n in count_down(3):
    print(n)
```

发生了什么：

1. 调用 `count_down(3)` **不会立刻执行完函数**，而是返回一个 generator 对象
2. 每次 `next(...)` / `for` 前进，执行到下一个 `yield`，把值产出
3. 函数结束 → 自动 `StopIteration`

```python
gen = count_down(2)
print(gen)            # <generator object ...>
print(next(gen))      # 2
print(next(gen))      # 1
```

### 3.2 生成器表达式

和列表推导式很像，但是**惰性**的：

```python
squares_list = [x * x for x in range(5)]   # 立刻算完，得到 list
squares_gen = (x * x for x in range(5))    # 还没算，得到 generator

print(sum(squares_gen))  # 30
print(sum(squares_gen))  # 0  ← 已耗尽
```

规则：

- 需要多次使用 / 要下标访问 → 用 list
- 只遍历一次、数据可能很大 → 用生成器表达式或生成器函数

### 3.3 Agent 味例子：流式假 token

```python
import time


def fake_token_stream(text: str, delay: float = 0.05):
    for ch in text:
        time.sleep(delay)  # 模拟网络到达
        yield ch


def print_stream(text: str) -> str:
    parts: list[str] = []
    for token in fake_token_stream(text, delay=0):
        parts.append(token)
        # 真实场景这里可 sys.stdout.write(token); flush
    return "".join(parts)


print(print_stream("你好，Agent"))
```

真实项目里，SDK 往往提供「可迭代的事件流」；你的消费端就是 `for event in stream`.

---

## 4. 必掌握：惰性求值

### 4.1 是什么

**惰性** = 真正需要下一个值时才计算下一个值，而不是提前把全部结果造出来。

```python
def infinite_numbers():
    n = 0
    while True:
        yield n
        n += 1


# 千万别 list(infinite_numbers()) —— 会无限跑
for n in infinite_numbers():
    if n >= 3:
        break
    print(n)
```

### 4.2 为什么重要

| 急切（eager） | 惰性（lazy） |
|---------------|--------------|
| `[process(x) for x in huge]` | `(process(x) for x in huge)` |
| 内存峰值高 | 内存更稳 |
| 必须等全部完成 | 可边算边用、可提前 break |

### 4.3 和 list 的取舍

```python
chunks = load_all_chunks()                 # 急切：全进内存
top = sorted(chunks, key=...)[:5]

def iter_chunks():
    for chunk in load_chunks_lazily():     # 惰性
        if chunk["score"] >= 0.6:
            yield chunk
```

若后续还要 `len`、多次遍历、随机下标 → 某阶段再 `list(...)` 物化。

---

## 5. 建议掌握：生成器管道

把多个小生成器串起来，每个阶段只做一件事——很像前端流式 transform，或 Unix pipe。

```python
from collections.abc import Iterable, Iterator


def raw_chunks() -> Iterator[dict]:
    data = [
        {"text": "  Agent 能调用工具  ", "score": 0.88},
        {"text": "", "score": 0.95},
        {"text": "RAG 先检索再生成", "score": 0.42},
        {"text": "向量库存 embedding", "score": 0.77},
    ]
    yield from data


def clean(chunks: Iterable[dict]) -> Iterator[dict]:
    for c in chunks:
        text = c["text"].strip()
        if text:
            yield {**c, "text": text}


def filter_score(chunks: Iterable[dict], min_score: float = 0.6) -> Iterator[dict]:
    for c in chunks:
        if c["score"] >= min_score:
            yield c


def take(chunks: Iterable[dict], n: int) -> Iterator[dict]:
    count = 0
    for c in chunks:
        if count >= n:
            return
        yield c
        count += 1


pipeline = take(filter_score(clean(raw_chunks())), 2)
print(list(pipeline))
```

好处：

- 每段可单测
- 中间不造大 list（直到你最终 `list` / 消费）
- 可读性通常好于一个巨型 for

---

## 6. 建议掌握：`yield from`

用于把「另一个可迭代对象的产出」委托出去：

```python
def tools():
    yield "search"
    yield "calc"


def more_tools():
    yield from tools()
    yield "browse"


print(list(more_tools()))  # ['search', 'calc', 'browse']
```

等价于：

```python
for x in tools():
    yield x
```

在管道里拼接、在递归结构里展平子迭代器时很方便。  
（它还有向子生成器发送值/异常的高级用法；本阶段会用「委托迭代」即可。）

---

## 7. 了解即可：异步生成器预告

后面学 `asyncio` 时会遇到：

```python
async def token_stream():
    for ch in "hi":
        yield ch


async def main():
    async for ch in token_stream():
        print(ch)
```

现在只需记住：

```text
同步：for x in gen
异步：async for x in async_gen
```

LLM 官方 SDK 的流式接口经常是异步可迭代。等模块 05 再实战。

---

## 8. 常用工具（够用即可）

```python
from itertools import islice, chain, count


print(list(islice(count(), 5)))           # 0..4，惰性无限计数的切片
print(list(chain([1, 2], [3, 4])))        # 拼接多个可迭代
```

自己写 `take` 很好；熟了以后知道 `islice` 在标准库里。

---

## 9. 常见坑

1. **生成器只能用一次**  
   需要多次遍历就 `list(gen)` 或重新调用生成器函数。

2. **在生成器里返回值**  
   `return xxx` 会变成 `StopIteration.value`，普通 `for` 拿不到；一般只 `yield`。

3. **把生成器当 list 用**  
   `gen[0]`、`len(gen)` 通常不行（除非你物化）。

4. **管道写太深导致难调试**  
   中间可临时 `list(stage)` 查看；确认后改回惰性。

5. **迭代过程中修改底层 list**  
   可能漏项或报错；边迭代边改要非常小心。

6. **文件迭代忘记关闭**  
   用 `with open(...) as f:`，在 with 块内迭代。

---

## 10. 综合小例子：惰性处理「假检索流」

```python
from collections.abc import Iterator


def retrieve(query: str) -> Iterator[dict]:
    # 假装检索服务一条条返回
    yield {"text": f"{query} intro", "score": 0.91}
    yield {"text": f"{query} deep dive", "score": 0.73}
    yield {"text": "irrelevant", "score": 0.20}
    yield {"text": f"{query} faq", "score": 0.66}


def build_context(query: str, top_k: int = 2) -> str:
    selected = []
    for chunk in retrieve(query):
        if chunk["score"] < 0.5:
            continue
        selected.append(chunk["text"])
        if len(selected) >= top_k:
            break  # 提前停止，后面的结果不必再处理
    return "\n".join(f"- {t}" for t in selected)


print(build_context("LangGraph"))
```

注意：这里用普通 `for` + `break` 就享受了惰性好处——若 `retrieve` 背后是网络流，提前 break 可少拉数据（真实客户端还要看是否支持取消）。

---

## 11. 练习指引

请打开并完成：

[`exercises/02-advanced-python/03-iterator-generator.md`](../../exercises/02-advanced-python/03-iterator-generator.md)

建议代码位置：

```text
playground/02-advanced-python/03-iterator-generator/
```

---

## 12. 小结与下一站

### 心智模型

```text
for x in obj
   → iter(obj) 得到 iterator
   → 反复 next(iterator) 直到 StopIteration

生成器 = 用 yield 自动实现的 iterator
惰性 = 需要时才算下一个
管道 = 小生成器串联，阶段清晰
```

### 自检清单

- [ ] 能区分 iterable / iterator，并解释为何迭代器常一次性
- [ ] 能用 `yield` 写生成器，并说明与返回 list 的差异
- [ ] 能写过滤 + 截断的惰性管道
- [ ] 知道 `yield from` 用于委托
- [ ] 独立完成练习基础题

### 下一章

[`04-decorator.md`](./04-decorator.md) —— 装饰器：重试、计时、鉴权、缓存等横切逻辑的标准写法。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[Python 数据模型](./02-data-model.md)
- 下一章：[装饰器](./04-decorator.md)
