# 数据结构与算法精要

> 所属模块：`04-systems-basics` · 计算机与服务端基础  
> 状态：`已完成正文`  
> 建议学时：2～4 小时（有前端数组/Map/Set 经验可更快；复杂度与堆选型建议动手跑一遍小基准）  
> 对应练习：[`exercises/04-systems-basics/04-dsa-essentials.md`](../../exercises/04-systems-basics/04-dsa-essentials.md)

## 本章定位

- **模块目标**：补齐「计算机与服务端」直觉，让后面 asyncio、缓存、队列、检索不再只是 API 堆砌。
- **本章角色**：用「复杂度直觉 + 结构取舍」服务工程选型，而不是变成算法竞赛课。
- **和 Agent**：消息队列选型、检索 Top-K、去重、缓存、图状 Multi-Agent 路由，都依赖这些直觉。
- **你的优势**：JS/TS 里的 `Array` / `Map` / `Set` / 偶尔手写优先队列经验可以直接迁移；重点盯住 Python 的 `list` vs `deque`、`dict` 有序语义、以及 `heapq` 的用法边界。

## 学习目标（学完应能做到）

1. 看懂大 O 的工程含义（不是证明题）：能把「n 多大、热不热」说清楚。
2. 对 `list` / `dict` / `set` / `deque` / 堆等结构做正确取舍，并能一句话讲清理由。
3. 能把结构选择连到缓存、队列、检索、路由等工程场景。
4. 知道刷题是加分项，不是本路线主线；主线是**为工程选型服务**。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 复杂度直觉、常用结构取舍、工程选型关系 | 能解释为什么选 dict/堆，能对照场景选型 |
| **建议掌握** | 哈希 / 堆 / 图场景 | 能举例，能听懂文档里的「哈希表 / 优先队列 / 图」 |
| **了解即可** | 刷题路线 | 可选加餐，别停更主线 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要「数据结构直觉」？

Agent 里你会写：

```text
历史消息截断前先遍历过滤
工具名去重
按分数取 Top-K
LRU 缓存 prompt 结果
多 Agent 路由图
```

这些看起来是「业务代码」，底层却是：

| 业务动作 | 结构问题 |
|----------|----------|
| 过滤 / 截断消息 | 有序序列上扫一遍，还是反复 `in list`？ |
| 工具名去重 | `list` 查成员，还是 `set`？ |
| 取 Top-K chunk | 每次全排序，还是堆维护？ |
| 缓存命中 | 键查找要不要平均 O(1)？ |
| 多 Agent 移交 | 节点 + 边怎么表达？ |

选错结构：

- n 大时突然变慢（开发时 n=20，上线 n=10⁵）
- 去重失效或顺序语义搞错
- Top-K 每次全排序浪费 CPU / 延迟
- 听不懂 Redis / 队列 / LangGraph 文档在说什么

#### 本章要练的三种能力

1. **复杂度直觉**：先估「大概扫几遍、砍几次半」，再决定要不要改结构
2. **结构取舍**：同样是「存一堆东西」，list / dict / set / 堆擅长完全不同
3. **工程映射**：把「哈希 / 队列 / 堆 / 图」听成 Redis、MQ、Top-K、工作流，而不是刷题名词

可以先记一句：

> 本章目标不是证明算法，而是：**在工程热路径上少选错容器**。

#### 前端/JS 结构对照（先建立地图）

| 常见需求 | JavaScript | Python |
|----------|------------|--------|
| 有序列表 | `Array` | `list` |
| 键值映射 | `Map` / 普通对象 | `dict` |
| 去重 / 成员检测 | `Set` | `set` |
| 两头增删窗口 | 手写或第三方 | `collections.deque` |
| Top-K / 优先队列 | 手写堆或库 | `heapq` |

后面每节都会把「怎么选」和这张表对齐。

---

## 2. 必掌握：复杂度直觉

这一节会刻意写细——复杂度是后面所有「为什么选 dict / 堆」的共同尺子。  
目标是**工程读法**，不是渐近证明。

### 2.1 大 O 在工程里到底说什么？

#### 为什么需要大 O？

你不需要在白板上推导递推式。你需要的是：

> 当输入从 100 涨到 10 万时，这段代码大概会慢多少倍？热路径上能不能扛住？

大 O 回答的是「**规模变大时，时间/空间怎么涨**」，不是「这一次调用绝对要几毫秒」。

#### 怎么理解（粗直觉表）

| 写法 | 粗直觉 | 工程心智 |
|------|--------|----------|
| O(1) | 基本定数时间 | `dict` / `set` 平均查找；「跟 n 无关」 |
| O(log n) | 每次砍半 | 堆操作、有序查找；n 再大也涨得慢 |
| O(n) | 扫一遍 | 遍历消息、过滤 chunk；通常可接受 |
| O(n log n) | 排序量级 | `sorted`、多数比较排序；偶发 OK，热路径慎用 |
| O(n²) | 双层循环 | n 上千要警惕；嵌套「对每个 x 再扫一遍 list」最常见 |

一句话：

> O 描述的是**增长趋势**；常量、机器、语言实现会影响「实际毫秒」，但选错增长阶，优化常数救不回来。

#### 跑一下（体感：n 从百到万）

下面这段**刻意**对比「list 成员检测」和「set 成员检测」。不必追求精确计时库；感受数量级即可。

```python
import time


def uniq_with_list(items: list[str]) -> list[str]:
    seen: list[str] = []
    out: list[str] = []
    for x in items:
        if x not in seen:  # 每次可能扫整份 seen → 整体接近 O(n²)
            seen.append(x)
            out.append(x)
    return out


def uniq_with_set(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:  # 平均 O(1)
            seen.add(x)
            out.append(x)
    return out


def bench(n: int) -> None:
    items = [f"tool-{i % (n // 2 + 1)}" for i in range(n)]
    t0 = time.perf_counter()
    uniq_with_list(items)
    t_list = time.perf_counter() - t0

    t0 = time.perf_counter()
    uniq_with_set(items)
    t_set = time.perf_counter() - t0
    print(f"n={n:>6}  list≈{t_list*1000:7.2f}ms  set≈{t_set*1000:7.2f}ms")


for n in (200, 2000, 8000):
    bench(n)
```

你会看到：n 变大时，`list` 版涨得更猛；`set` 版慢涨得多。  
这就是「复杂度直觉」要服务的决策：**热路径上去重/成员检测，别用 list 当集合。**

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 把 O(1) 理解成「永远 1 纳秒」 | 忽略常量与哈希冲突；平均很快 ≠ 绝对定数 |
| 小 n 就过度优化 | 消息列表 n=20，怎么写都行；可读性优先 |
| 只记符号不连场景 | 背了 O(n²) 却仍写 `if x not in list` |
| 微基准当真理 | 一次计时有噪声；看趋势，别抠小数 |

#### 前端/JS 结构对照

| 操作 | JS | Python | 粗复杂度 |
|------|----|--------|----------|
| 数组末尾 push | `arr.push(x)` | `lst.append(x)` | 摊还 O(1) |
| 数组里找值 | `arr.includes(x)` | `x in lst` | O(n) |
| Set 成员 | `set.has(x)` | `x in s` | 平均 O(1) |
| Map 取值 | `map.get(k)` | `d[k]` / `d.get(k)` | 平均 O(1) |
| 排序 | `[...].sort()` | `sorted(lst)` | O(n log n) |

---

### 2.2 n 多大才要认真？

#### 为什么需要「规模感」？

同一段 O(n²) 代码：

- n=20：可能看不出问题
- n=10⁵：延迟和 CPU 会「突然」爆

Agent 开发里最常见的陷阱是：**本地 fixture 很小，生产检索/日志/工具调用历史很大。**

#### 怎么选（工程刻度）

| 规模直觉 | 例子 | 策略 |
|----------|------|------|
| n ≈ 10～50 | 一轮对话消息、少量工具 | 结构怎么写都行；先清晰 |
| n ≈ 10³ | 一批日志、中等 chunk 列表 | 避免明显的双重扫描热路径 |
| n ≈ 10⁵+ | 文档片段、全量用户事件 | 认真选 dict/set/堆/索引；先测量 |

经验法则：

1. **先测量再优化**——但**明显的 O(n²) 热路径**要避免（比如循环里 `x in list`）
2. 冷路径（启动一次、管理脚本）可读性可以压过微优化
3. 热路径（每条请求、每个 chunk）先保证增长阶合理

#### 跑一下（心智实验，不必真跑大数据）

```python
# 慢：每次 membership 都 O(n)
seen = []
for x in items:
    if x not in seen:
        seen.append(x)

# 快：平均 O(1) 查询
seen_set = set()
for x in items:
    if x not in seen_set:
        seen_set.add(x)
```

把 `items` 想成「本轮调用过的工具名」或「已见过的 chunk 文本」：  
n 从小变大时，左边会从「无所谓」变成「请求延迟抖动」。

#### 易错点

- 「我测了 100 条很快」≠「10 万条也很快」
- 把排序 `O(n log n)` 放在**每个 token / 每个请求**里，比放在离线批处理里危险得多
- 复杂度是**相对输入规模**；输入是「当前请求的 chunks」，不是「全库文档」时，别过度设计

#### 前端/JS 结构对照

前端同样：`array.includes` 在列表很长时会卡交互；`Set` / `Map` 是同一类选型。  
差别只是：Agent 后端的 n 往往来自检索与历史，而不是 DOM 节点。

---

### 2.3 常见操作的复杂度速查（服务选型）

#### 为什么需要一张速查表？

选型时你要的是「这个操作贵不贵」，不是背完整复杂度手册。

#### 怎么理解 / 怎么选

| 结构 | 常见便宜操作 | 常见贵操作 |
|------|--------------|------------|
| `list` | 尾部 `append` / `pop`；按下标访问 | `x in list`；中间 `insert`/`pop(0)` |
| `dict` | 按键读写、删键 | 按「值」找键（得扫） |
| `set` | 加/删/成员检测 | 按下标取第 i 个（没有下标语义） |
| `deque` | 两头 `append` / `popleft` | 中间随机访问（不如 list） |
| 堆 (`heapq`) | 推入、弹出当前最值 | 任意删除某个元素（别当通用有序集合） |

#### 跑一下

```python
from collections import deque

lst = [1, 2, 3]
lst.append(4)       # 便宜
# lst.insert(0, 0)  # 贵：后面元素要挪

d = {"search": fn}
d["search"]         # 便宜（平均）

s = {"a", "b"}
"a" in s            # 便宜（平均）

q = deque(maxlen=3)
q.append("t1")
q.append("t2")
q.append("t3")
q.append("t4")      # 最旧的自动丢掉
print(list(q))      # ['t2', 't3', 't4']
```

#### 易错点

- `list.pop(0)` 看起来只删一个，实际是 O(n)；固定窗口请用 `deque`
- `dict` 在 3.7+ **保留插入顺序**，但语义上仍当「映射」用，别当「靠顺序的队列」核心模型（队列请用 `deque` / 队列中间件）
- 「我用了 dict 所以一定 O(1)」——键不可哈希、或误用线性扫描找值时，并不成立

#### 前端/JS 结构对照

| Python | JS 近似 | 备注 |
|--------|---------|------|
| `list.pop(0)` 贵 | `arr.shift()` 也会挪元素 | 两边都别当高频队列 |
| `deque` | 无内建等价常用结构 | 后端窗口/队列优先 `deque` |
| `dict` 有序 | 现代 JS 对象/`Map` 也有序 | 有序 ≠ 应用语义就是「列表」 |

---

## 3. 必掌握：常用结构取舍

这一节是本章核心：**同一份数据，换容器就换成本模型。**

### 3.1 总览：先选对「擅长什么」

#### 为什么需要取舍表？

Agent 代码里最常见的错误不是「不会写算法」，而是：

> 所有东西都塞进 `list`，再用线性扫描硬扛。

#### 怎么选

| 结构 | 擅长 | 不擅长 | Agent 例子 |
|------|------|--------|------------|
| `list` | 有序、尾部增删、按下标 | 中间插入、按值查找 | 消息历史 |
| `dict` | 键查、映射、聚合 | 无「按值当主键」语义 | 工具注册表 |
| `set` | 去重、成员检测 | 要下标访问、要重复元素 | 已调用工具集合 |
| `deque` | 两头高效增删、定长窗口 | 中间随机访问 | 固定长度日志/工具窗口 |
| `heapq` | 持续 Top-K / 优先队列 | 任意删除、按键更新复杂 | 维护最高分 chunk |

口诀：

```text
要顺序浏览、按下标     → list
要按名字/id 找         → dict
要问「有没有出现过」   → set
要两头进、或只要最近 K → deque
要持续「当前最大/最小」→ heap（或 nlargest 一次算完）
```

#### 跑一下（同一需求，三种容器）

```python
tools = ["search", "browse", "search", "calc", "browse"]

# list：保序，但「是否出现过」贵
as_list = tools

# set：成员检测快，但丢失顺序与重复
as_set = set(tools)

# dict：去重且可保首次顺序（3.7+）
as_dict = dict.fromkeys(tools)

print(as_list)             # ['search', 'browse', 'search', 'calc', 'browse']
print(as_set)              # 无序集合语义（打印顺序勿依赖）
print(list(as_dict))       # ['search', 'browse', 'calc']  去重保序
```

#### 易错点

- 「去重」用 `set` 后若还要**首次出现顺序**，用 `dict.fromkeys` 或「set 辅助 + list 输出」
- 工具注册表用 `list[tuple]` 再线性找名字——能跑，但注册多了就痛；用 `dict[str, Callable]`
- 把 `heapq` 当「自动排序的 list」——堆只保证堆顶，不保证全体有序

#### 前端/JS 结构对照

| 场景 | JS | Python |
|------|----|--------|
| 消息数组 | `Message[]` | `list[dict]` |
| 工具注册 | `Map<string, Fn>` / 对象 | `dict[str, Callable]` |
| 已调用工具 | `Set<string>` | `set[str]` |
| 最近 N 条 | 手写 `push` + `shift` | `deque(maxlen=N)` |

---

### 3.2 `list`：有序序列的默认选择

#### 为什么需要 list？

对话历史、步骤轨迹、chunk 原始顺序——**顺序本身就是信息**。list 是默认容器。

#### 怎么理解 / 怎么选

适合：

- 追加消息、按时间顺序遍历
- 切片截断：`messages[-20:]`
- 偶尔全量排序（冷路径）

不适合作为主力：

- 高频 `x in messages`（按内容找）
- 高频从头部删除（用 `deque`）

#### 跑一下

```python
messages = [
    {"role": "system", "content": "你是助手"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！"},
]

# 截断：保留最近窗口（有序语义）
window = messages[-2:]
print(window[0]["role"])  # user

# 尾部追加：便宜
messages.append({"role": "user", "content": "继续"})
```

#### 易错点

- 截断前若要「按 id 去重」，别对 list 反复 `in`；先抽键到 `set`/`dict`
- `messages.remove(x)` 按值删且只删第一个，还是 O(n)；频繁按 id 删考虑 dict 索引

#### 前端/JS 结构对照

几乎等同 `Array`：`push` / 下标 / `slice` 心智一致。  
差别：Python `list` 是动态数组；没有「类型只能装 number」这种限制（注解另说）。

---

### 3.3 `dict`：键查找与聚合的主力

#### 为什么需要 dict？

Agent 里大量是「名字 → 东西」：

```text
工具名 → 函数
chunk 文本 → 当前最高分记录
session_id → 状态
```

这就是映射；用 list 扫等于放弃平均 O(1)。

#### 怎么理解 / 怎么选

- **注册表 / 路由表 / 配置表** → `dict`
- **按某字段聚合留最优** → `dict`（见 §7）
- 需要「既要键查，又要顺序遍历」→ `dict`（3.7+ 保插入序）通常够用

#### 跑一下

```python
from typing import Callable

ToolFn = Callable[..., str]

registry: dict[str, ToolFn] = {
    "search": lambda q: f"result:{q}",
    "calc": lambda expr: str(eval(expr)),  # 仅演示；生产勿对不可信输入 eval
}

name = "search"
if name in registry:
    print(registry[name]("python"))  # result:python
```

聚合留最高分：

```python
chunks = [
    {"text": "AAA", "score": 0.4},
    {"text": "BBB", "score": 0.9},
    {"text": "AAA", "score": 0.7},
]

best: dict[str, dict] = {}
for c in chunks:
    t = c["text"]
    if t not in best or c["score"] > best[t]["score"]:
        best[t] = c

print(best["AAA"]["score"])  # 0.7
```

#### 易错点

- 键必须可哈希：`list` 不能当键；`tuple`（元素也可哈希）可以
- `d[k]` 键不存在会 `KeyError`；不确定时用 `d.get(k)` 或 `if k in d`
- 不要用 `dict` 模拟「按分数排序的优先队列」——那是堆的活

#### 前端/JS 结构对照

| JS | Python | 注意 |
|----|--------|------|
| `obj[key]` / `Map` | `dict` | 普通对象键会被转成字符串；`Map` 更接近 `dict` |
| `key in obj` | `k in d` | 都是成员检测 |
| `Object.keys` 顺序 | `dict` 插入序 | 都别把「映射」误当成队列抽象 |

---

### 3.4 `set`：去重与成员检测

#### 为什么需要 set？

问题形态是「出现过没有 / 只要唯一集合」，而不是「第几个、什么顺序」。

Agent 例子：本轮已调用工具、已注入的文档 id、禁止重复的副作用工具。

#### 怎么理解 / 怎么选

```text
只关心成员 → set
还要保序输出 → dict.fromkeys 或 set 辅助 + list
还要计数 → collections.Counter（了解即可）
```

#### 跑一下

```python
called: set[str] = set()

def ensure_once(tool: str) -> bool:
    if tool in called:
        return False
    called.add(tool)
    return True


print(ensure_once("search"))  # True
print(ensure_once("search"))  # False
print(ensure_once("browse"))  # True
```

去重保序（练习 B2 同款）：

```python
def dedupe_keep_order(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


print(dedupe_keep_order(["a", "b", "a", "c", "b"]))  # ['a', 'b', 'c']
```

#### 易错点

- `set` 元素必须可哈希；嵌套 `list` 不行
- 集合运算很强（`&` `|` `-`），但别在没需求时炫技
- 「去重」后若下游还要分数/元数据，用 `dict` 聚合而不是裸 `set`

#### 前端/JS 结构对照

`Set` ↔ `set` 几乎一一对应：`add` / `has` / `delete`。  
JS `Set` 迭代顺序是插入序；Python `set` **不要依赖**遍历顺序当业务顺序——要保序用 `dict`。

---

### 3.5 `deque`：窗口与两头队列

#### 为什么需要 deque？

`list` 尾部强、头部弱。需要「最近 N 条」「队列进出」时，`collections.deque` 是标准答案。

#### 怎么理解 / 怎么选

| 需求 | 选 |
|------|----|
| 最近 50 条 tool 名 | `deque(maxlen=50)` |
| 生产者消费者内存队列（单机玩具） | `deque` 或 `queue.Queue` |
| 随机下标访问为主 | `list` |

#### 跑一下

```python
from collections import deque

recent_tools: deque[str] = deque(maxlen=5)
for name in ["a", "b", "c", "d", "e", "f"]:
    recent_tools.append(name)

print(list(recent_tools))  # ['b', 'c', 'd', 'e', 'f']  — a 被挤出
```

#### 易错点

- `maxlen` 满了会**静默丢掉最旧**——这是特性；若不能丢，别设 `maxlen`
- 需要线程安全队列时，看 `queue` 模块；`deque` 本身不是完整并发队列抽象
- 中间插入/删除仍可能贵；deque 优势在两端

#### 前端/JS 结构对照

JS 常用 `arr.push` + `arr.shift` 模拟窗口；数据大时 `shift` 贵。  
Python 侧直接 `deque(maxlen=...)`，意图更清晰。

---

### 3.6 堆（`heapq`）：Top-K 与优先队列

#### 为什么需要堆？

当问题是：

> 我不要全排序，我只要「当前最重要的 K 个」或「下一次该处理谁」

全量 `sorted` 是 O(n log n) 且产生完整顺序；堆更贴「优先」语义，K≪n 时更划算。

#### 怎么理解 / 怎么选

| 场景 | 更合适 |
|------|--------|
| 一次性取 Top-K | `heapq.nlargest` / `nsmallest`（或小 n 直接 `sorted`） |
| 流式不断进、持续维持前 K | 固定大小堆（思维：小根堆存当前 Top-K） |
| 要稳定全序输出 | `sorted` 更直观 |
| 要按键删改任意元素 | 堆不擅长；考虑其它结构 |

小 K、大 n：堆往往优于每次全排序（概念上记住即可）。

#### 跑一下

```python
import heapq

scores = [0.2, 0.9, 0.4, 0.8, 0.7]
print(heapq.nlargest(3, scores))  # [0.9, 0.8, 0.7]

chunks = [
    {"text": "a", "score": 0.2},
    {"text": "b", "score": 0.9},
    {"text": "c", "score": 0.4},
    {"text": "d", "score": 0.8},
]
top = heapq.nlargest(2, chunks, key=lambda c: c["score"])
print([c["text"] for c in top])  # ['b', 'd']
```

小基准直觉（n 较大、K 很小）：

```python
import random
import time
import heapq

n, k = 50_000, 5
data = [random.random() for _ in range(n)]

t0 = time.perf_counter()
sorted(data, reverse=True)[:k]
t_sort = time.perf_counter() - t0

t0 = time.perf_counter()
heapq.nlargest(k, data)
t_heap = time.perf_counter() - t0

print(f"sorted+slice≈{t_sort*1000:.2f}ms  nlargest≈{t_heap*1000:.2f}ms")
```

n 小或 K 接近 n 时，差距可能不明显——**先看场景，再看基准**。

#### 易错点

| 错法 | 说明 |
|------|------|
| 以为 `heapq` 里 list 始终全有序 | 只有堆性质；`list(heap)` 打印不是排序结果 |
| 默认堆是大根堆 | Python `heapq` 是**小根堆**；要最大用负数或 `nlargest` |
| 任意删除某个任务 | 堆删任意元素麻烦；别硬掰 |
| n=20 还上复杂堆结构 | 直接 `sorted(..., reverse=True)[:k]` 更清晰 |

#### 前端/JS 结构对照

JS 标准库没有官方堆；常 `sort` 后 `slice`，或引第三方。  
Python 内建 `heapq`——Agent 检索后处理里很常用，值得会用 `nlargest`。

---

## 4. 必掌握：和工程选型的关系

这一节把「结构名词」接到你会在文档/架构图里看到的组件。  
你不一定手写这些，但要听懂文档在说什么。

### 4.1 组件 ↔ 结构直觉

#### 为什么需要这张映射？

否则会出现：

- 听人说「用哈希做缓存」却不知道和 `dict` 同一类问题
- 听「优先队列调度」却以为必须自己写竞赛级堆
- 听「LangGraph」却不知道图就是节点+边

#### 怎么理解 / 怎么选

| 工程组件 | 背后结构直觉 | 你要抓住的点 |
|----------|--------------|--------------|
| Redis 缓存 | 哈希表 + TTL | 按 key 平均 O(1) 读写；过期是策略 |
| 消息队列 | 队列；优先级队列用堆思想 | 先进先出 vs 按优先级出 |
| 向量检索 | 近似最近邻索引（比暴力算相似度） | n 大时不能每次全库扫 |
| LRU 缓存 | 哈希 + 双向链表思想 | O(1) 查 + O(1) 更新「最近使用」 |
| 路由 / 工作流 | 图（节点+边） | 状态机 / Multi-Agent 移交 |

选型问题改写成结构问题：

```text
要按 key 找结果？     → 哈希思维（dict / Redis）
要削峰、异步解耦？   → 队列思维
只要 Top-K 相关？     → 堆 / 限幅排序思维
要表达流转关系？     → 图思维
```

#### 跑一下（LRU 思想的最小模拟）

下面**不是**生产 LRU，只演示「哈希 + 顺序」如何配合。生产用 `functools.lru_cache` 或 Redis。

```python
from collections import OrderedDict


class TinyLRU:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._data: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> str | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)  # 标记为最近使用
        return self._data[key]

    def put(self, key: str, value: str) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)  # 丢掉最久未使用


cache = TinyLRU(2)
cache.put("p1", "resp-1")
cache.put("p2", "resp-2")
cache.get("p1")
cache.put("p3", "resp-3")  # 挤掉 p2
print(cache.get("p2"))  # None
print(cache.get("p1"))  # resp-1
```

#### 易错点

- 把 Redis 只记成「远程 dict」——忽略 TTL、淘汰、并发与序列化成本
- 把「向量数据库」理解成普通 SQL——核心是近似检索索引，不是暴力 `for` 算余弦
- 手写 LRU / 堆调度用在玩具可以；上线优先成熟组件

#### 前端/JS 结构对照

| 后端组件 | 前端近似心智 |
|----------|--------------|
| Redis 哈希 | `Map` + 过期策略（前端少见完整 TTL 层） |
| MQ | 任务队列 / 请求队列 |
| LRU | 内存缓存、HTTP 缓存语义 |
| 工作流图 | 状态机、路由图、redux-like 流转（仅类比） |

---

### 4.2 Agent 场景选型清单

#### 为什么需要清单？

把 §3 的容器和 §4.1 的组件收成「看见场景就会选」。

#### 怎么选

| 场景 | 倾向 | 一句话理由 |
|------|------|------------|
| 工具注册表 | `dict[str, Callable]` | 按名 O(1) 分发 |
| 已调用工具名 | `set[str]` | 成员检测 |
| 最近 50 条日志 / tool | `deque(maxlen=50)` | 定长窗口 |
| 持续维护前 10 高分文档 | 堆 / `nlargest` | Top-K，不必反复全排序 |
| prompt 结果缓存 | LRU / Redis | 哈希键 + 淘汰 |
| Multi-Agent 移交 | 图 | 节点=agent，边=移交 |

#### 跑一下（把清单落成最小骨架）

```python
from collections import deque
import heapq

registry = {"search": lambda q: q, "browse": lambda u: u}
called: set[str] = set()
recent: deque[str] = deque(maxlen=50)

def dispatch(name: str, arg: str) -> str:
    if name not in registry:
        raise KeyError(name)
    called.add(name)
    recent.append(name)
    return registry[name](arg)


chunks = [{"id": i, "score": (i * 37) % 100 / 100} for i in range(30)]
top10 = heapq.nlargest(10, chunks, key=lambda c: c["score"])
print(len(top10), top10[0]["score"] >= top10[-1]["score"])
```

#### 易错点

- 场景是「注册表」却用 list 存 `(name, fn)` 再扫——能跑到一定规模就痛
- 场景是 Top-K 却每次对全量 `sorted` 后只取 3 个——K 固定且 n 大时浪费
- 场景是图却强行用深层 if/else 链——后期加边改路由会崩

#### 前端/JS 结构对照

前端路由表 ≈ `dict`；按钮防重复点击 ≈ `set`；聊天消息窗 ≈ `list`/`deque` 思维。  
Agent 后端只是把同一套选型用到「工具 / 检索 / 调度」上。

---

## 5. 建议掌握：哈希 / 堆 / 图场景

必掌握偏「选容器」；本节偏「听懂场景词、能举例」。

### 5.1 哈希场景

#### 为什么需要单独讲哈希？

`dict` / `set` / Redis / 很多缓存，底层都是哈希表思想：

> 用哈希函数把键打到桶里，平均一次跳转找到。

#### 怎么理解

- **平均 O(1) 查**；最坏可能退化（一般知道即可，正常键空间极少成为你的主矛盾）
- **键必须可哈希**：`list` 不行；`tuple`（元素可哈希）可以；`str` / `int` 常用
- 工程上：缓存 key、工具名、用户 id、规范化后的文本指纹，都是哈希键候选

#### 跑一下

```python
# 可哈希
key = ("user", 42)
cache = {key: "ok"}
print(cache[key])

# 不可哈希：list 当键
try:
    {[1, 2]: "no"}  # type: ignore[dict-item]
except TypeError as e:
    print(type(e).__name__)  # TypeError
```

文本当键前先规范化（去空白、大小写策略要想清楚）：

```python
def norm(text: str) -> str:
    return " ".join(text.split()).lower()


print(norm("  Hello   World "))  # hello world
```

#### 易错点

- 可变对象当键（list/dict）→ `TypeError`
- 用「未规范化文本」当去重键 → 看起来不同、语义相同的重复漏网
- 把「哈希冲突最坏 O(n)」天天挂嘴边却忽略测量——工程上先保证键设计合理

#### 前端/JS 结构对照

| JS | Python |
|----|--------|
| `Map` 可用对象当键（引用相等） | `dict` 键要可哈希；自定义对象需 `__hash__`/`__eq__`（了解即可） |
| `Set` | `set` |
| 对象键转字符串 | `dict` 不会把 `int` 键变成 `"1"` |

---

### 5.2 堆场景

#### 为什么需要堆场景？

不是为了手写堆化数组，而是识别：

> 这是「优先」问题，还是「全排序」问题？

#### 怎么理解 / 怎么选

Agent 里典型：

- 检索后取分数最高的 K 个 chunk
- 优先调度：先跑「快/重要/最早到期」的任务
- 限流窗口里保留「最贵」或「最新」若干项（结合业务）

#### 跑一下（优先调度直觉）

```python
import heapq
import time

# 小根堆：(priority, seq, job)；priority 越小越优先
pq: list[tuple[int, int, str]] = []
seq = 0


def push(priority: int, job: str) -> None:
    global seq
    heapq.heappush(pq, (priority, seq, job))
    seq += 1


push(5, "embed-batch")
push(1, "user-reply")
push(3, "log-flush")

while pq:
    priority, _, job = heapq.heappop(pq)
    print(priority, job)
# 1 user-reply → 3 log-flush → 5 embed-batch
```

`seq` 用于同优先级时 FIFO，避免直接比较任务对象。

#### 易错点

- 任务对象不可比较时，只压 `(priority, task)` 可能在 priority 相等时炸——加 `seq`
- 需要「提高某个已在堆里任务的优先级」→ 堆不擅长原地改；常用懒删除或换结构
- 与排序混淆：要完整名次用 `sorted`；只要下一批最优先用堆

#### 前端/JS 结构对照

前端偶发「优先级任务」常直接 `sort`；后端调度/检索 Top-K 更常碰到堆语义。  
会用 `heapq.nlargest` 通常就够本章。

---

### 5.3 图场景

#### 为什么需要图？

Multi-Agent、工作流、工具编排一旦出现「谁能转到谁」，线性 list 就不够表达关系。

#### 怎么理解

- **节点**：agent / 步骤 / 工具
- **边**：移交、依赖、允许的下一跳
- LangGraph 一类工作流就是图
- 算法面：BFS/DFS **扫盲即可**——会「顺着边走访」就行，不要求刷题深度

邻接表（dict）是最常见工程表达：

```text
researcher → {search_tool, writer}
search_tool → {researcher}
writer → {end}
```

#### 跑一下（邻接表 + BFS 扫盲）

```python
from collections import deque

graph: dict[str, list[str]] = {
    "researcher": ["search", "writer"],
    "search": ["researcher"],
    "writer": ["end"],
    "end": [],
}


def reachable(start: str) -> list[str]:
    seen: set[str] = set()
    order: list[str] = []
    q: deque[str] = deque([start])
    while q:
        node = q.popleft()
        if node in seen:
            continue
        seen.add(node)
        order.append(node)
        q.extend(graph.get(node, []))
    return order


print(reachable("researcher"))
# 例如：['researcher', 'search', 'writer', 'end']
```

DFS 直觉：用栈或递归「一条路走到底再回头」；BFS：用队列「一层层扩」。  
选型课里记住：**表达关系用图；遍历用 BFS/DFS 两种走法。**

#### 易错点

- 用巨型 if/else 模拟可扩展路由——加节点就要改一堆分支
- 忽略环：agent 互相移交可能成环，遍历要 `seen`
- 把「图算法竞赛题」当成主线——本章够用到邻接表 + 走访即可

#### 前端/JS 结构对照

| 概念 | JS 常见 | Python 常见 |
|------|---------|-------------|
| 邻接表 | `Map<string, string[]>` | `dict[str, list[str]]` |
| BFS 队列 | 数组 `shift`（注意性能） | `deque` |
| 工作流 | 状态机 / 路由配置 | LangGraph / 自研图执行器 |

---

## 6. 了解即可：刷题路线（非主线）

#### 为什么单独开一节「了解即可」？

避免两种极端：

1. 完全不碰算法 → 面试/难题时慌
2. 把本路线学成 LeetCode 营 → Agent / 工程主线停更

#### 怎么理解

若以后面试或想加功力，可按这条加餐：

```text
数组/哈希 → 双指针 → 栈队列 → 二叉树 → BFS/DFS → 堆 → 基础 DP
```

本路线主线仍是：**工程 + Agent**。刷题当加餐，别停更。

#### 跑一下（把刷题映射回工程，而不是反过来）

| 刷题主题 | 工程映射（主线更关心这个） |
|----------|----------------------------|
| 哈希表题 | 去重、注册表、缓存键 |
| 栈队列题 | 窗口、消息缓冲、BFS |
| 堆题 | Top-K、优先调度 |
| BFS/DFS | 工作流/权限图走访 |
| DP | 多数 Agent 业务不先学；了解即可 |

#### 易错点

- 为刷题而重写业务里本来清晰的 `sorted[:k]`——无收益
- 以为「没刷完题就不能做 Agent」——本路线明确反对

#### 前端/JS 结构对照

刷题语言可以是 JS 或 Python；**容器选型直觉两边通用**。  
本课用 Python 容器把工程场景跑通即可。

---

## 7. 综合小例子：检索后处理选型

这一节把前面所有「必掌握」串起来——也是练习 A1 的直接模板。  
强调：**为工程选型服务**，不是炫算法。

### 7.1 问题拆解

#### 为什么需要「后处理」？

向量检索 / 关键词检索回来的 chunks 常常：

- 重复文本或近重
- 分数字段要排序取 Top-K
- 还想留下「最近用过哪些 source」做调试或多样性

若全用 list 硬扫 + 反复全排序，n 一涨就痛。

#### 怎么选（结构分工）

| 步骤 | 结构 | 理由 |
|------|------|------|
| 规范化文本、跳过空 | 纯逻辑 | 键设计 |
| 同一文本留最高分 | `dict[str, dict]` | 按键聚合，平均 O(1) |
| 取 Top-K | `heapq.nlargest` | K 小、语义就是 Top-K |
| 最近 window 的 source | `deque(maxlen=...)` | 定长窗口 |

流水线：

```text
chunks(list)
  → 规范化 + dict 聚合去重
  → 堆取 Top-K
  →（可选）deque 记录 source 窗口
  → 返回 list[dict]
```

### 7.2 完整示例

#### 跑一下

```python
import heapq
from collections import deque


def select_chunks(
    chunks: list[dict],
    k: int = 3,
    window: int = 20,
) -> list[dict]:
    # 1) 去重 / 聚合：同一文本保留最高分 —— dict
    best_by_text: dict[str, dict] = {}
    for c in chunks:
        text = c["text"].strip()
        if not text:
            continue
        prev = best_by_text.get(text)
        if prev is None or c["score"] > prev["score"]:
            best_by_text[text] = {**c, "text": text}

    # 2) Top-K：堆
    top = heapq.nlargest(k, best_by_text.values(), key=lambda c: c["score"])

    # 3) 可选：保留最近 window 的来源 id —— deque
    recent_sources: deque[object] = deque(maxlen=window)
    for c in top:
        recent_sources.append(c.get("source"))

    # recent_sources 可用于日志/多样性；此处仍返回 top
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
print([(c["text"], c["score"]) for c in result])
# [('beta', 0.9), ('gamma', 0.8)]  — alpha 聚合为 0.7 后未进 Top-2
```

#### 易错点

| 错法 | 后果 |
|------|------|
| 用 `set(texts)` 去重 | 丢掉 score / source 元数据 |
| 聚合键用原始未 strip 文本 | `"alpha"` 与 `"  alpha  "` 变两条 |
| 每次 `sorted(chunks)[:k]` 且 n 极大、调用极频 | 延迟与 CPU 浪费（小 n 可接受） |
| Top-K 后还假设 list 全序可用下标当「第 2 名策略」乱改 | `nlargest` 返回从大到小；要稳妥可再明确排序需求 |
| 把近似「近重」（相似但不相同）当 `dict` 精确键 | 精确去重≠语义去重；后者要别的策略 |

#### 前端/JS 结构对照

| 步骤 | JS 近似 |
|------|---------|
| 按文本聚合 | `Map<string, Chunk>` |
| Top-K | ` [...arr].sort((a,b)=>b.score-a.score).slice(0,k)`（n 大再考虑堆库） |
| 最近 source | 数组窗口或第三方 deque |

心智相同：**Map 聚合 → 取前 K → 窗口记录**。

### 7.3 和工程主线的关系

```text
本函数解决的是「单次请求内的后处理选型」
真正全库检索 → 向量索引 / 搜索引擎（§4）
跨请求缓存   → LRU / Redis（§4）
多步 Agent    → 图路由（§5.3）
```

综合例的意义：让你在应用层**先选对 list/dict/set/堆**，再决定要不要上外部系统。

---

## 8. 练习指引

按文档粒度动手，比只看表有用：

[`exercises/04-systems-basics/04-dsa-essentials.md`](../../exercises/04-systems-basics/04-dsa-essentials.md)

建议顺序：

1. **B1** 复杂度对照——对齐 §2  
2. **B2** 去重保序——对齐 §3.4  
3. **B3** Top-K——对齐 §3.6  
4. **B4** 结构选型——对齐 §3～§4  
5. **A1** `select_chunks`——对齐 §7  
6. **A2** deque 窗口——对齐 §3.5  
7. **C1** 图直觉——对齐 §5.3  

目录：`playground/04-systems-basics/04-dsa-essentials/`

---

## 9. 小结与下一站

### 自检

- [ ] 能解释 dict/set 相对 list 的查找差异（平均 O(1) vs O(n)）
- [ ] 知道 Top-K 可用堆思想（`heapq.nlargest` / 固定大小堆）
- [ ] 能把缓存 / 队列 / 图对应到工程组件（Redis、MQ、工作流）
- [ ] 能对「注册表 / 去重 / 窗口 / Top-K」说出选用的结构与理由
- [ ] 清楚刷题是加餐，主线是工程选型

### 记住三句

1. **复杂度先看热路径与 n**，再谈微优化。  
2. **list 保序，dict 映射，set 成员，deque 窗口，堆优先。**  
3. **结构名词要听成组件能力**——为选型服务，不为刷题服务。

### 模块 04 收官

```text
OS → 网络HTTP → 并发模型 → DSA精要
```

下一模块：[`../05-async-python/README.md`](../05-async-python/README.md) —— asyncio 实战（Agent 分水岭）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[并发模型](./03-concurrency-models.md)
- 下一模块：[Python 异步编程](../05-async-python/README.md)
