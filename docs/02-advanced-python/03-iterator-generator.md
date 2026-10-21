# Iterator / Generator

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：4～7 小时（迭代协议与 `yield` 建议动手踩一遍；管道与 `yield from` 可边写边串）  
> 对应练习：[`exercises/02-advanced-python/03-iterator-generator.md`](../../exercises/02-advanced-python/03-iterator-generator.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：弄清 `for` 循环背后的协议，并用生成器做**惰性处理**——流式输出、大文件、检索结果管道都会用到。
- **和上一章关系**：数据模型里的 `__iter__` 在这里展开成完整的迭代故事。
- **你的优势**：JS 里的 `for...of`、`Symbol.iterator`、generator function（`function*`）经验可以直接迁移；重点盯住 Python 的「可迭代 vs 迭代器」、生成器一次性、以及惰性管道组装。

## 学习目标（学完应能做到）

1. 说清可迭代对象（iterable）与迭代器（iterator）的区别，并解释 `for` 背后调用了什么。
2. 用手写类实现最小迭代协议，并用 `yield` 写出生成器函数；会写生成器表达式。
3. 解释惰性求值的好处，能写出「过滤 → 转换 → 截断」的生成器管道。
4. 完成练习；`yield from` 会用，异步生成器先建立印象即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 迭代协议、手写迭代器、生成器与 `yield`、生成器表达式、惰性求值 | 能写、能讲、能做题 |
| **建议掌握** | 生成器管道、`yield from` | 会组装、会委托 |
| **了解即可** | 异步生成器预告、`itertools` 常用件 | 知道地图在哪，后面按需查 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要迭代器 / 生成器？

Agent / LLM 场景里，数据经常是「边产生边消费」的：

```text
LLM 流式 token
    → 逐块打印 / 推送给前端
检索到的大量 chunk
    → 过滤分数 → 截断 Top-K → 再送进 prompt
读超大日志 / 语料文件
    → 不能一次性 read() 进内存
```

如果你只会「先做成完整 list 再处理」，在数据变大或要流式体验时就会卡：内存飙高、首字延迟变长、提前 `break` 也白算了后面的结果。

#### 学完能写出什么

生成器让你写：

```python
for token in stream_tokens(response):
    print(token, end="", flush=True)
```

以及「小阶段串联」的管道：

```python
pipeline = take(filter_score(clean(raw_chunks())), 2)
for chunk in pipeline:
    ...
```

#### 本章要练的三种能力

1. **协议直觉**：`for` / `iter` / `next` 背后在调什么
2. **惰性写法**：用 `yield` 和生成器表达式「需要时才算下一个」
3. **管道组装**：过滤 / 转换 / 截断拆成可单测的小生成器

可以先记一句：

> list 负责「已经全部备好的一批数据」；生成器负责「按需产出的一条流水线」。

---

## 2. 必掌握：迭代协议

这一节会刻意写细——迭代协议是后面生成器、管道、`async for` 的共同底座。  
上一章数据模型只点了 `iter(x) → x.__iter__()`；这里把它讲透。

### 2.1 两个角色：iterable 与 iterator

#### 为什么要拆成两个角色？

很多人会把「能 `for` 的东西」都叫迭代器。Python 里其实有两层：

| 角色 | 含义 | 关键方法 |
|------|------|----------|
| **Iterable（可迭代）** | 能提供迭代器的对象 | `__iter__` → 返回 iterator |
| **Iterator（迭代器）** | 能产出下一个值的对象 | `__next__`；通常也实现 `__iter__` 返回自己 |

比喻：

```text
可迭代对象 ≈ 一本书（可以反复打开读）
迭代器     ≈ 一个书签（记住读到哪了；翻完就到头了）
```

`list` 是可迭代对象：每次 `for` 都会拿到**新的**迭代器（新书签）。  
迭代器本身通常是**一次性**的：走完再 `next` 就没了。

#### 怎么写（先认协议）

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

心智图：

```text
for x in obj
    │
    ├─ iter(obj)  → 拿到 iterator
    │
    └─ 反复 next(iterator)
           │
           ├─ 有值 → 交给循环体
           └─ StopIteration → 结束循环
```

#### 跑一下：用内置函数看见协议

```python
nums = [10, 20, 30]
it = iter(nums)          # list.__iter__() → list_iterator
print(next(it))          # 10
print(next(it))          # 20
print(next(it))          # 30
# print(next(it))        # StopIteration
```

也可以自己模拟 `for`：

```python
it = iter(["a", "b"])
while True:
    try:
        x = next(it)
    except StopIteration:
        break
    print(x)
# a
# b
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把「能 for」的都叫 iterator | 说不清为何 `list` 可多次 `for`，而生成器不行 |
| 忘记 `StopIteration` 是正常结束信号 | 以为是「出错了」；其实 `for` 就是靠它收尾 |
| 对同一个 iterator 期望「自动重置」 | 走完就空；要重新开始就再 `iter(容器)` |

检查技巧（调试时够用）：

```python
from collections.abc import Iterable, Iterator

print(isinstance([1, 2], Iterable))   # True
print(isinstance([1, 2], Iterator))   # False
print(isinstance(iter([1, 2]), Iterator))  # True
```

经验规则：

> **Iterator 一定是 Iterable**（因为它的 `__iter__` 通常返回自己）；  
> **Iterable 不一定是 Iterator**（list / dict / 文件都是 iterable，但 list 本身不是 iterator）。

#### JS 对照

| Python | JavaScript |
| --- | --- |
| `iter(obj)` | `obj[Symbol.iterator]()` |
| `next(it)` | `it.next()`（返回 `{value, done}`） |
| `StopIteration` | `{ done: true }` |
| `for x in obj` | `for (const x of obj)` |

```javascript
const arr = [10, 20, 30]
const it = arr[Symbol.iterator]()
console.log(it.next())  // { value: 10, done: false }
console.log(it.next())  // { value: 20, done: false }
console.log(it.next())  // { value: 30, done: false }
console.log(it.next())  // { value: undefined, done: true }
```

差异：JS 用 `{value, done}` 打包结果；Python 用「返回值 + 抛 `StopIteration`」两套信号。

---

### 2.2 你每天都在用

#### 为什么先看「日常用法」？

协议听起来抽象，但你早就在用了。先建立「到处都是可迭代」的直觉，再去手写实现。

#### 怎么写 / 跑一下

```python
for x in [1, 2, 3]:
    print(x)

for key in {"a": 1, "b": 2}:
    print(key)

for line in open("notes.txt", encoding="utf-8"):
    print(line.strip())
```

| 对象 | 迭代时拿到什么 |
| --- | --- |
| `list` / `tuple` / `str` | 元素 / 字符 |
| `dict` | **键**（要键值对用 `.items()`） |
| 文件对象 | 一行行文本（惰性读文件的经典例子） |
| `range(...)` | 整数序列（本身也是惰性的） |

`for` 自动帮你取迭代器；你很少需要手写 `iter`/`next`，但**读源码和排错时必须懂**。

#### 易错点

- `for k in some_dict` 迭代的是键，不是 `(k, v)`  
- 文件对象既是可迭代也常被当作迭代器使用；用完记得关（优先 `with open(...)`）
- 空可迭代不是错误：`for x in []: ...` 循环体一次都不进

#### JS 对照

```javascript
for (const x of [1, 2, 3]) console.log(x)
for (const key of Object.keys({ a: 1 })) console.log(key)
```

Python 的 `dict` 默认可 `for` 键；JS 普通对象不能直接 `for...of`，通常要 `Object.keys` / `Object.entries`。

---

### 2.3 手写一个最小迭代器

#### 为什么要手写一遍？

生成器（下一节）会帮你省掉样板代码，但手写一次能把协议钉死：

1. `__iter__` 返回谁？
2. `__next__` 何时抛 `StopIteration`？
3. 为什么「迭代器一次性」，而「容器可多次 for」？

练习 B1 的 `RangeLike` 就是这个能力。

#### 怎么写：迭代器 = 自己既是 iterable 又是 iterator

```python
class CountDown:
    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self):
        return self  # 迭代器的 __iter__ 返回自己

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value
```

要点拆开：

1. `__iter__` 返回 `self` → 它本身就是 iterator  
2. `__next__` 负责「下一个值」；结束时**必须** `raise StopIteration`  
3. 状态（`self.current`）存在实例上 → 走完就耗尽

#### 跑一下

```python
for n in CountDown(3):
    print(n)
# 3
# 2
# 1

it = CountDown(2)
print(list(it))  # [2, 1]
print(list(it))  # []   ← 再取就空了
```

第二次 `list(it)` 为空，不是 bug：书签已经翻到末尾了。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 结束时 `return` 而不抛 `StopIteration` | `for` 可能卡住或行为怪异（协议要求抛） |
| 耗尽后有时抛、有时又吐出值 | 破坏迭代器契约；应持续抛 `StopIteration` |
| 把「可多次遍历」的期望放在同一 iterator 上 | 应改成「工厂 / 容器」模式（下一小节） |
| `__iter__` 返回了别的无关对象 | `for` 拿到的不是你想要的迭代过程 |

#### JS 对照

```javascript
function createCountDown(start) {
  let current = start
  return {
    [Symbol.iterator]() { return this },
    next() {
      if (current <= 0) return { done: true }
      return { value: current--, done: false }
    },
  }
}

for (const n of createCountDown(3)) {
  console.log(n)  // 3, 2, 1
}
```

心智模型接近：都是「对象自己记住进度，并提供取下一个的方法」。

---

### 2.4 可多次遍历：容器每次返回新迭代器

#### 为什么需要「工厂」模式？

`CountDown` 自己就是迭代器 → 用一次就空。  
若希望每次 `for` / 每次 `list(...)` 都重新开始，应把「数据源」和「书签」拆开：

```text
容器（Iterable）──__iter__──► 新的迭代器（Iterator）
```

#### 怎么写

```python
class CountDownIterator:
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


class CountDownFactory:
    """可多次遍历的可迭代对象：每次 __iter__ 都新建迭代器。"""

    def __init__(self, start: int) -> None:
        self.start = start

    def __iter__(self):
        return CountDownIterator(self.start)
```

#### 跑一下

```python
factory = CountDownFactory(2)
print(list(factory))  # [2, 1]
print(list(factory))  # [2, 1]  ← 每次都完整
```

这正是 `list` / `range` 的工作方式：容器记得「从哪开始」，迭代器记得「读到哪了」。

#### 易错点

- 只实现 `__next__` 却指望 `for` 工作：还需要 `__iter__`（迭代器上通常 `return self`）
- 「可多次遍历」≠「迭代器自动重置」：重置靠**新迭代器**，不是改旧对象偷偷归零（当然你也可以设计可重置 API，但那不是默认协议）
- 练习里若要求 `list(RangeLike(...))` 两次都完整，检查点就是：`__iter__` 是否每次 `return` 新对象

#### JS 对照

```javascript
function countDownFactory(start) {
  return {
    *[Symbol.iterator]() {
      for (let i = start; i > 0; i--) yield i
    },
  }
}

const f = countDownFactory(2)
console.log([...f])  // [2, 1]
console.log([...f])  // [2, 1]
```

JS 里用 generator method 当 `[Symbol.iterator]`，每次 `for...of` 都会启动新的生成器——和「每次返回新迭代器」同构。

---

### 2.5 `iter()` / `next()` 的实用细节

#### 为什么还要会这两个内置函数？

`for` 够用，但调试、手写消费逻辑、对接「回调式 API」时，`iter`/`next` 更直接。

#### 怎么写 / 跑一下

```python
it = iter(["a", "b"])
print(next(it))           # a
print(next(it))           # b
print(next(it, "end"))    # end（给默认值，避免 StopIteration）
```

`next(iterator, default)` 是高频写法：耗尽时返回 default，而不是抛异常。

还有两参数形式的 `iter(callable, sentinel)`（了解即可）：

```python
# 伪意：反复调用 func()，直到返回 sentinel 为止
# it = iter(func, sentinel)
```

日常 Agent 代码较少手写这种；见到时知道「这是在造迭代器」即可。

#### 易错点

- `next(it)` 在耗尽时抛 `StopIteration`；在 `for` 外层裸调记得处理或给 default  
- `iter(x)` 要求 `x` 可迭代；对 `int` 会 `TypeError: 'int' object is not iterable`

#### JS 对照

| Python | JavaScript |
| --- | --- |
| `next(it)` | `it.next().value`（并看 `done`） |
| `next(it, default)` | 自己判断 `done` 后返回 default |

---

## 3. 必掌握：生成器与 `yield`

手写 `__iter__` / `__next__` 很啰嗦。生成器函数用 `yield` 自动变成迭代器——**状态机由解释器帮你保存**。

### 3.1 最小生成器函数

#### 为什么需要 `yield`？

同样的倒计时，用类要写一堆样板；用生成器函数：

```python
def count_down(start: int):
    while start > 0:
        yield start
        start -= 1
```

几行就表达「产出一串值」的意图。Agent 里的假 token 流、假检索流、按行读大文件，几乎都是这种形状。

#### 怎么写

规则：

1. 函数体里出现 `yield` → 调用它**不会立刻跑完**，而是返回 generator 对象  
2. 每次 `next(...)` / `for` 前进 → 执行到下一个 `yield`，把值产出，并**暂停**  
3. 函数结束（或 `return`）→ 自动等价于 `StopIteration`

#### 跑一下

```python
for n in count_down(3):
    print(n)
# 3
# 2
# 1

gen = count_down(2)
print(gen)            # <generator object count_down at ...>
print(next(gen))      # 2
print(next(gen))      # 1
# print(next(gen))    # StopIteration
```

发生了什么（逐步）：

```text
调用 count_down(2)
    → 返回 generator（函数体几乎还没跑）

next(gen)
    → 跑到 yield 2，暂停，交出 2

next(gen)
    → 从暂停处继续，yield 1，暂停，交出 1

再 next(gen)
    → while 结束，函数返回 → StopIteration
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为 `count_down(3)` 返回 list | 实际返回 generator；`type` 一看便知 |
| 对同一 `gen` 期望第二次 `for` 还有数据 | 生成器一次性；要重新调用 `count_down(3)` |
| 写成 `return` 一串值却还想惰性 | `return [1,2,3]` 不是生成器；要惰性就 `yield` |
| 在生成器里只 `print` 不 `yield` | 调用方 `for` 不到任何值 |

#### JS 对照

```javascript
function* countDown(start) {
  while (start > 0) {
    yield start
    start -= 1
  }
}

for (const n of countDown(3)) {
  console.log(n)
}
```

| Python | JavaScript |
| --- | --- |
| `def f(): yield ...` | `function* f() { yield ... }` |
| 调用 `f()` 得 generator | 调用 `f()` 得 generator |
| `next(gen)` | `gen.next().value` |

---

### 3.2 生成器表达式

#### 为什么还要「表达式」形态？

列表推导式你已经会了：

```python
squares_list = [x * x for x in range(5)]  # 立刻算完 → list
```

只要把 `[]` 换成 `()`，就变成**惰性**的生成器表达式：

```python
squares_gen = (x * x for x in range(5))   # 还没算 → generator
```

适合「只遍历一次、中间结果很大、不想多写一个 `def`」的场景。

#### 怎么写 / 跑一下

```python
squares_list = [x * x for x in range(5)]
squares_gen = (x * x for x in range(5))

print(squares_list)       # [0, 1, 4, 9, 16]
print(squares_gen)        # <generator object ...>

print(sum(squares_gen))   # 30
print(sum(squares_gen))   # 0  ← 已耗尽
```

带过滤：

```python
high = (c["text"] for c in chunks if c["score"] >= 0.6)
```

函数参数里只有一个推导时，外层圆括号可省（常见写法）：

```python
total = sum(x * x for x in range(5))  # 不必再套一层 ()
```

#### 易错点

| 场景 | 更合适 |
| --- | --- |
| 需要多次遍历 / 下标 / `len` | `list` / 列表推导 |
| 只消费一次、数据可能很大 | 生成器表达式或生成器函数 |
| 逻辑超过两三行、要起名字 | 生成器函数（更可读、可测） |

注意：生成器表达式**同样只能用一次**。

#### JS 对照

JS 没有和「生成器表达式」一一对应的语法糖；更接近的是：

```javascript
// 急切
const squaresList = [...Array(5).keys()].map((x) => x * x)

// 惰性：手写 generator，或用库
function* squares() {
  for (let x = 0; x < 5; x++) yield x * x
}
```

Python 的 `(... for ... in ...)` 是独特且高频的短惰性写法。

---

### 3.3 Agent 味例子：流式假 token

#### 为什么单独举这个例子？

真实 LLM SDK 常提供「可迭代 / 异步可迭代的事件流」。你的消费端就是 `for event in stream`。用假 token 先把同步生成器手感练熟。

#### 怎么写

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
```

#### 跑一下

```python
print(print_stream("你好，Agent"))
# 你好，Agent
```

把 `delay` 调成 `0.05`，你会看到「一个字一个字出来」的体感——这就是惰性 + 流式的意义：不必等全部生成完再显示。

#### 易错点

- 若先 `tokens = list(fake_token_stream(...))` 再打印，就失去了流式首字延迟优势  
- 真实 SDK 还可能是异步流（见 §7）；同步 `for` 与 `async for` 不要混用

#### JS 对照

```javascript
async function* fakeTokenStream(text, delay = 50) {
  for (const ch of text) {
    await new Promise((r) => setTimeout(r, delay))
    yield ch
  }
}

// for await (const ch of fakeTokenStream("hi")) { ... }
```

前端常见 `ReadableStream` / async generator；Python 侧先掌握同步 `yield`，异步章再接 `async for`。

---

### 3.4 生成器里的 `return`（知道即可）

#### 为什么提一句？

生成器里可以 `return`，但它**不会**变成 `for` 循环拿到的值：

```python
def g():
    yield 1
    return "done"  # 进入 StopIteration.value；普通 for 拿不到


print(list(g()))  # [1]
```

高级用法里（`yield from` 的返回值）会碰到；本阶段记住：

> 给消费方的数据用 `yield`；`return` 只表示「结束（可附带结束值）」。

---

## 4. 必掌握：惰性求值

### 4.1 是什么

#### 为什么「惰性」值得单独成章？

**惰性** = 真正需要下一个值时才计算下一个值，而不是提前把全部结果造出来。

生成器、生成器表达式、`range`、文件按行迭代，核心收益都是这个。

#### 怎么写 / 跑一下

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
# 0
# 1
# 2
```

因为惰性，**无限序列**也可以安全表达：只要消费方负责截断（`break` / `islice` / 自己的 `take`）。

#### 易错点

- `list(infinite_gen)` / 无界 `for` 不 `break` → 内存或 CPU 被吃光  
- 误以为「定义了生成器就立刻算完」→ 恰恰相反，定义几乎不算

#### JS 对照

```javascript
function* infiniteNumbers() {
  let n = 0
  while (true) yield n++
}

for (const n of infiniteNumbers()) {
  if (n >= 3) break
  console.log(n)
}
```

两边都靠「生成器 + 消费方截断」表达无限流。

---

### 4.2 为什么重要（和急切对比）

#### 为什么要会选 eager / lazy？

| 急切（eager） | 惰性（lazy） |
|---------------|--------------|
| `[process(x) for x in huge]` | `(process(x) for x in huge)` |
| 内存峰值高 | 内存更稳 |
| 必须等全部完成 | 可边算边用、可提前 break |
| 可下标、可多次遍历、可知 `len` | 默认一次性；无 `len`/下标 |

Agent 场景口诀：

> **检索 / 流式 / 大文件**：优先惰性；  
> **要排序、要随机访问、要反复用**：某阶段再 `list(...)` 物化。

#### 怎么写（取舍示意）

```python
# 急切：全进内存再排序截断
chunks = load_all_chunks()
top = sorted(chunks, key=lambda c: c["score"], reverse=True)[:5]


# 惰性：边读边过滤（不必先装下全部）
def iter_good_chunks():
    for chunk in load_chunks_lazily():
        if chunk["score"] >= 0.6:
            yield chunk
```

#### 跑一下：感受「提前停止」

```python
def ticks():
    for i in range(1000):
        print(f"produce {i}")
        yield i


for x in ticks():
    if x >= 2:
        break
# 通常只会看到 produce 0/1/2 —— 后面 997 次根本不会跑
```

这就是惰性对性能的真实意义：不只是省内存，还能**少做无用功**。

#### 易错点

- 管道很长却在第一层就 `list(...)` → 后面的惰性全废  
- 需要 `len` 时强行对生成器 `len(gen)` → `TypeError`；应物化或改设计

#### JS 对照

| 思路 | Python | JavaScript |
| --- | --- | --- |
| 急切 map | `[f(x) for x in xs]` | `xs.map(f)` |
| 惰性 | `(f(x) for x in xs)` / `yield` | `function*` / 部分引擎的 iterator helpers |
| 截断 | `break` / `islice` | `break` / 自己写 take |

---

### 4.3 和 list 的取舍

#### 为什么不是「永远生成器」？

生成器省内存，但丢了 list 的随机访问与多次遍历。工程上常常是：

```text
惰性拉取 / 过滤 / 截断  →  某节点 list(...) 物化  →  再排序或多次使用
```

#### 怎么写 / 跑一下

```python
def iter_chunks():
    for chunk in (
        {"text": "a", "score": 0.9},
        {"text": "b", "score": 0.4},
        {"text": "c", "score": 0.8},
    ):
        if chunk["score"] >= 0.6:
            yield chunk


# 只遍历一次：保持惰性
for c in iter_chunks():
    print(c["text"])

# 需要多次用：物化
materialized = list(iter_chunks())
print(len(materialized))
print(materialized[0])
```

#### 易错点

- 物化后再抱怨「怎么还是生成器」——`list(gen)` 得到的是 list  
- 物化前生成器已耗尽 → `list` 得到 `[]`；注意变量不要复用已耗尽的 gen

---

## 5. 建议掌握：生成器管道

把多个小生成器串起来，每个阶段只做一件事——很像前端流式 transform，或 Unix pipe。

### 5.1 为什么需要管道？

一个巨型 `for` 里同时清洗、过滤、截断，难读也难测：

```python
# 难维护的「一锅炖」
result = []
for c in data:
    text = c["text"].strip()
    if not text:
        continue
    if c["score"] < 0.6:
        continue
    result.append({**c, "text": text})
    if len(result) >= 2:
        break
```

拆成管道后：

```text
raw_chunks → clean → filter_score → take(n) → 消费
```

每段可单测；中间默认不造大 list。

### 5.2 怎么写

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
```

组装：

```python
pipeline = take(filter_score(clean(raw_chunks())), 2)
```

类型注解里的 `Iterable` / `Iterator` 来自 `collections.abc`：输入侧用 `Iterable`（更宽），输出侧用 `Iterator`（更准）。

### 5.3 跑一下

```python
print(list(pipeline))
# [{'text': 'Agent 能调用工具', 'score': 0.88},
#  {'text': '向量库存 embedding', 'score': 0.77}]
```

注意：空字符串那条被 `clean` 丢掉；低分 `0.42` 被 `filter_score` 丢掉；`take(2)` 只留两条。

调试技巧：中间临时物化看一眼：

```python
stage = list(clean(raw_chunks()))
print(stage)  # 确认清洗结果
# 确认后再改回惰性串联
```

### 5.4 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 每一段结尾都 `return list(...)` | 失去惰性；内存与提前停止优势消失 |
| 管道写太深却从不分层命名 | 难调试；优先具名小函数 |
| 复用同一个已耗尽的 `pipeline` 变量 | 第二次 `list(pipeline)` 得到 `[]` |
| 在上游用 `list` 强行拉爆无限源 | 卡死；截断应放在消费侧或用 `take`/`islice` |

### 5.5 JS 对照

```javascript
// 概念接近：可迭代协议上的惰性变换（示意）
function* clean(chunks) {
  for (const c of chunks) {
    const text = c.text.trim()
    if (text) yield { ...c, text }
  }
}
```

前端若用 RxJS / 流式 pipeline，思想一致：**小变换串联 + 晚订阅/惰性拉**。Python 生成器管道是同步、拉取式（pull）的版本。

---

## 6. 建议掌握：`yield from`

### 6.1 为什么需要 `yield from`？

当你要把「另一个可迭代对象的产出」整段委托出去时，可以写：

```python
for x in tools():
    yield x
```

`yield from` 就是这个模式的专用语法，更短，也更利于子生成器的高级委托（发送值/异常——本阶段了解存在即可）。

### 6.2 怎么写 / 跑一下

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
def more_tools():
    for x in tools():
        yield x
    yield "browse"
```

在管道里拼接、在递归结构里展平子迭代器时很方便：

```python
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


print(list(flatten([1, [2, 3], [4, [5]]])))  # [1, 2, 3, 4, 5]
```

`raw_chunks` 里的 `yield from data` 也是同一用法：把 list 的元素逐个委托产出。

### 6.3 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `yield from` 后面写单个非可迭代值（如 `yield from 3`） | `TypeError` |
| 以为 `yield from xs` 会一次 yield 整个 list | 实际是逐元素委托 |
| 把 `yield from` 和 `return` 子生成器返回值搅在一起 | 高级用法；本阶段先会「委托迭代」即可 |

子生成器 `return` 的值可以被 `yield from` 接住（了解即可）：

```python
def sub():
    yield 1
    return "done"


def main():
    value = yield from sub()
    print("sub returned:", value)


print(list(main()))
# sub returned: done
# [1]
```

### 6.4 JS 对照

```javascript
function* tools() {
  yield "search"
  yield "calc"
}

function* moreTools() {
  yield* tools()  // 注意是 yield*
  yield "browse"
}

console.log([...moreTools()])  // ['search', 'calc', 'browse']
```

| Python | JavaScript |
| --- | --- |
| `yield from xs` | `yield* xs` |

---

## 7. 了解即可：异步生成器预告

### 7.1 为什么现在只「预告」？

后面学 `asyncio`（模块 05）时会遇到：网络流、官方 LLM SDK 的流式接口经常是**异步可迭代**。现在先建立名字与语法印象，避免看到 `async for` 就慌。

### 7.2 怎么写（先认形状）

```python
async def token_stream():
    for ch in "hi":
        yield ch


async def main():
    async for ch in token_stream():
        print(ch)
```

对照：

```text
同步：for x in gen
异步：async for x in async_gen
```

异步生成器函数：`async def` + 体里 `yield`。  
它不能用普通 `for` 消费，只能 `async for`（或异步迭代协议）。

### 7.3 跑一下？

本阶段不必强行跑通事件循环；记住这张地图即可：

```text
def f(): yield x          → 同步生成器 → for
async def f(): yield x    → 异步生成器 → async for
```

等模块 05 再实战 `asyncio.run(main())` 与真实 SDK 流。

### 7.4 易错点（提前避雷）

- 在同步函数里 `async for` → 语法/语义都不对  
- 把异步生成器当成普通 generator 丢进 `list(...)` → 不行  
- 以为「有 `yield` 就是同步生成器」→ 看有没有 `async def`

### 7.5 JS 对照

```javascript
async function* tokenStream() {
  for (const ch of "hi") yield ch
}

// for await (const ch of tokenStream()) { ... }
```

| Python | JavaScript |
| --- | --- |
| `async def` + `yield` | `async function*` |
| `async for` | `for await...of` |

---

## 8. 常用工具（够用即可）

自己写 `take` / `filter` 很好；熟了以后知道标准库里有现成零件。

#### 为什么要知道 `itertools`？

很多「惰性管道积木」已经写好了：切片、拼接、无限计数等。不必从零造轮子，但**先会手写再去用库**，排错更稳。

#### 怎么写 / 跑一下

```python
from itertools import islice, chain, count


print(list(islice(count(), 5)))           # [0, 1, 2, 3, 4]
print(list(chain([1, 2], [3, 4])))        # [1, 2, 3, 4]
```

| 工具 | 作用 | 和本章关系 |
| --- | --- | --- |
| `islice(iterable, n)` | 惰性取前 n 个 | 类似手写 `take` |
| `chain(a, b, ...)` | 拼接多个可迭代 | 类似多次 `yield from` |
| `count()` | 无限计数器 | 惰性无限源示例 |

#### 易错点

- `islice` 返回的仍是迭代器：需要 list 时再 `list(...)`  
- `count()` 不要直接 `list(count())`

#### JS 对照

JS 标准库较分散；常见是手写 `take`，或使用 lodash / iterator helpers。概念上 `islice` ≈ 「惰性版 `slice`」。

---

## 9. 常见坑

1. **生成器只能用一次**  
   需要多次遍历就 `list(gen)` 或重新调用生成器函数 / 重新 `iter(容器)`。

2. **在生成器里返回值**  
   `return xxx` 会变成 `StopIteration.value`，普通 `for` 拿不到；一般只 `yield`。

3. **把生成器当 list 用**  
   `gen[0]`、`len(gen)` 通常不行（除非你物化）。

4. **管道写太深导致难调试**  
   中间可临时 `list(stage)` 查看；确认后改回惰性。

5. **迭代过程中修改底层 list**  
   可能漏项或报错；边迭代边改要非常小心（先拷贝、或迭代索引副本）。

6. **文件迭代忘记关闭**  
   用 `with open(...) as f:`，在 with 块内迭代。

7. **iterable / iterator 概念混淆**  
   「能 for」≠「是迭代器」；需要多次完整遍历时，确认 `__iter__` 是否每次返回新迭代器。

8. **过早物化**  
   第一层就 `list(huge_stream)`，后面的 `take`/`break` 都救不了已经付出的成本。

---

## 10. 综合小例子：惰性处理「假检索流」

把协议 + 生成器 + 提前停止串起来，做成 Agent 里极常见的「检索 → 过滤 → Top-K」：

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
# - LangGraph intro
# - LangGraph deep dive
```

注意：这里用普通 `for` + `break` 就享受了惰性好处——若 `retrieve` 背后是网络流，提前 break 可少拉数据（真实客户端还要看是否支持取消）。

也可以改成管道风格（与 §5 同一套路）：

```python
def filter_score(chunks, min_score: float = 0.5):
    for c in chunks:
        if c["score"] >= min_score:
            yield c


def take(chunks, n: int):
    count = 0
    for c in chunks:
        if count >= n:
            return
        yield c
        count += 1


texts = [c["text"] for c in take(filter_score(retrieve("LangGraph")), 2)]
print(texts)
```

最后一层列表推导会物化——这是有意的：交给 prompt 前通常需要稳定的 `list[str]`。

---

## 11. 练习指引

请打开并完成：

[`exercises/02-advanced-python/03-iterator-generator.md`](../../exercises/02-advanced-python/03-iterator-generator.md)

建议代码位置：

```text
playground/02-advanced-python/03-iterator-generator/
```

做题顺序建议：

1. **B1 手写迭代器** —— 钉死「每次 `__iter__` 返回新对象」  
2. **B2 `batched`** —— 用 `yield` 表达分组状态机  
3. **B3 惰性过滤** —— `yield` 数据源 + 过滤截断，避免过早 `list`  
4. 进阶题再练管道 / `yield from`

---

## 12. 小结与下一站

### 心智模型

```text
for x in obj
   → iter(obj) 得到 iterator
   → 反复 next(iterator) 直到 StopIteration

可迭代（Iterable）= 能提供迭代器的对象（可多次打开）
迭代器（Iterator）= 带着进度往前走的对象（通常一次性）

生成器 = 用 yield 自动实现的 iterator
生成器表达式 = 短惰性变换
惰性 = 需要时才算下一个（可提前 break 省功）
管道 = 小生成器串联，阶段清晰
yield from / yield* = 委托另一个可迭代的产出
async for = 异步世界的 for（模块 05 再实战）
```

### 自检清单

- [ ] 能区分 iterable / iterator，并解释为何迭代器常一次性
- [ ] 能手写最小迭代器类，并写出「可多次遍历」的工厂版
- [ ] 能用 `yield` 写生成器，并说明与返回 list 的差异
- [ ] 会写生成器表达式，并知道何时改回 list
- [ ] 能解释惰性求值，并能写过滤 + 截断的惰性管道
- [ ] 知道 `yield from` 用于委托；见过异步生成器 / `async for` 的形状
- [ ] 独立完成练习基础题

### 下一章

[`04-decorator.md`](./04-decorator.md) —— 装饰器：重试、计时、鉴权、缓存等横切逻辑的标准写法。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[Python 数据模型](./02-data-model.md)
- 下一章：[装饰器](./04-decorator.md)
