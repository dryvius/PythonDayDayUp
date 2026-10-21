# Python 数据模型

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有 JS/TS class 经验可更快；描述符建议动手踩一遍）  
> 对应练习：[`exercises/02-advanced-python/02-data-model.md`](../../exercises/02-advanced-python/02-data-model.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：弄清「为什么 `len(x)`、`x in y`、`obj()` 能工作」——答案几乎都是：**对象实现了某些协议（dunder 方法）**。
- **和上一章关系**：OOP 教你如何组织类；数据模型教你如何让类**像 Python 内置对象一样被使用**。
- **你的优势**：JS/TS 里「对象有方法就能被调用 / 可迭代」的直觉能迁移；重点盯住 Python 把这些能力**集中约定成 `__xxx__` 协议**。

## 学习目标（学完应能做到）

1. 用「协议」视角解释常用语法糖背后调用了什么。
2. 为自定义类实现一组常用 dunder 方法（展示、比较、容器、可调用）。
3. 写出可调用对象（`__call__`），理解它和普通函数的相似处与适用场景。
4. 完成练习；描述符与 CPython 细节先建立地图即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 对象协议直觉、常用 dunder、可调用对象 | 能写、能读框架代码 |
| **建议掌握** | 描述符入门 | 能认出 `@property` 背后的机制 |
| **了解即可** | 与 CPython 实现的关系 | 知道「别神化」，够用就停 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要「数据模型」？

上一章你会写 `class Tool`、`class Agent`。但读框架时你会发现：好代码不只是「有属性和方法」，还能**像内置类型一样用**：

```python
len(messages)
tool in registry
agent("你好")          # 有的设计把 agent 做成可调用对象
async with client:     # 后面上下文管理器章
for chunk in stream:   # 下一章迭代器
```

如果不会数据模型，你会写出别扭 API：

```python
registry.get_length()
registry.has_tool("search")
registry.get_tool("search").run(...)
```

会了协议，可以写成：

```python
len(registry)
"search" in registry
registry["search"](...)
```

#### 它们不是魔法

解释器遇到语法/内置函数时，会去找对象上的约定方法：

```text
len(x)     →  x.__len__()
x in y     →  y.__contains__(x) 或迭代比较
f(...)     →  f.__call__(...)
str(x)     →  x.__str__()
repr(x)    →  x.__repr__()
```

这些方法名形如 `__xxx__`，叫 **dunder methods**（double underscore），也常被叫魔法方法。

#### 学会后你能做什么

1. **读源码更快**（看到 `__getitem__` 就知道能 `obj[key]`）
2. **把自研 Tool / Registry / MessageList 写得更 Pythonic**
3. **少写** `get_xxx()` / `has_xxx()` 这种绕弯 API

可以先记一句：

> 数据模型不是「背魔法方法」，而是：**你实现约定，解释器给你语法能力**。

---

## 2. 必掌握：对象协议直觉

这一节会刻意写细——尤其是 dunder 对照表，因为它是后面每一节的查询入口。

### 2.1 一句话定义

#### 为什么需要「协议」这个词？

在 Python 里，「能不能 `len(x)`」不取决于你声明了某个 interface 关键字，而取决于对象**有没有实现约定行为**。这种「靠方法约定协作」的约定，就叫**协议（protocol）**。

> **Python 数据模型** = 一套「对象如何与语言语法/内置函数协作」的约定。  
> 你实现约定方法，解释器就给你对应的语法能力。

#### 怎么理解（心智图）

```text
你写的代码：  len(messages) / "search" in registry / tool(query="x")
                    ↓
解释器查找：  对象上有没有对应的 dunder
                    ↓
执行你的实现： messages.__len__() / registry.__contains__(...) / tool.__call__(...)
```

这和「鸭子类型」是同一条路：

> 看起来像鸭子、叫起来像鸭子——就可以当鸭子用。  
> 有 `__len__`、行为合理——就可以被 `len()` 使用。

### 2.2 语法糖 → 方法 对照（先背最常用）

#### 为什么要先有一张总表？

后面每一节都会展开某个 dunder。先有一张「查表」，你就不会在细节里迷路：

> 看到奇怪写法 → 先查「它对应哪个 dunder」→ 再决定要不要实现。

#### 常用对照表（建议收藏）

| 你写的代码 | 大致调用 | 典型用途 |
|------------|----------|----------|
| `str(x)` / `f"{x}"` / 多数 `print(x)` | `x.__str__()` | 给人看的展示 |
| `repr(x)` / 交互式回显 / 容器里嵌套打印 | `x.__repr__()` | 调试、无歧义展示 |
| `len(x)` | `x.__len__()` | 长度 / 数量 |
| `bool(x)` / `if x:` | `x.__bool__()`；若无则 `x.__len__()`；都无则恒为 `True` | 真假值 |
| `x in y` | 优先 `y.__contains__(x)`；否则可能迭代比较 | 成员判断 |
| `y[key]` | `y.__getitem__(key)` | 下标 / 映射读取 |
| `y[key] = v` | `y.__setitem__(key, v)` | 下标写入 |
| `del y[key]` | `y.__delitem__(key)` | 下标删除 |
| `f(a, b)` | `f.__call__(a, b)` | 把对象当函数用 |
| `a == b` | `a.__eq__(b)`（可回退到 `b.__eq__(a)`） | 相等 |
| `a < b` 等 | `__lt__` / `__le__` / `__gt__` / `__ge__` | 排序比较 |
| `a + b` | `a.__add__(b)`（可回退到 `b.__radd__(a)`） | 运算符 |
| `iter(x)` / `for x in ...` | `x.__iter__()`（下一章展开） | 迭代 |
| `next(it)` | `it.__next__()`（下一章展开） | 取下一个 |
| `with x:` | `x.__enter__` / `x.__exit__`（上下文管理器章） | 资源管理 |

#### 跑一下：亲眼看见「语法 → 方法」

```python
class Probe:
    def __len__(self) -> int:
        print("→ 调用了 __len__")
        return 3

    def __contains__(self, item: object) -> bool:
        print(f"→ 调用了 __contains__({item!r})")
        return item == "ok"

    def __getitem__(self, key: object) -> str:
        print(f"→ 调用了 __getitem__({key!r})")
        return f"value-of-{key}"

    def __call__(self, *args, **kwargs):
        print(f"→ 调用了 __call__ args={args} kwargs={kwargs}")
        return "called"


p = Probe()
print(len(p))          # → 调用了 __len__ / 3
print("ok" in p)       # → 调用了 __contains__('ok') / True
print(p["name"])       # → 调用了 __getitem__('name')
print(p(1, x=2))       # → 调用了 __call__ ...
```

跑完后记住：

> **语法糖不是另一套系统，只是 dunder 的快捷写法。**

#### 易错点

1. **表是「大致调用」，不是 1:1 字节码复刻**  
   内置类型可能走更快的 C 路径；自定义类按协议理解即可。

2. **`x in y` 不一定总有 `__contains__`**  
   没有时，Python 可能用迭代 + `==` 兜底（慢，且语义取决于你怎么迭代）。

3. **`print(x)` 优先 `__str__`，没有则退回 `__repr__`**  
   所以只实现 `__repr__` 时，`print` 也能看到内容——但两者职责仍应分开想。

4. **不必一次背完**  
   用的时候回来查这张表；本章后面会对重点行逐个拆开。

#### 和 JavaScript 对照（协议直觉）

| 想法 | Python | JavaScript（近似） |
|------|--------|-------------------|
| 长度 | `len(x)` → `__len__` | `x.length` 或自定义 getter |
| 成员 | `x in y` → `__contains__` | `y.includes?.(x)` / `x in y`（对象键） |
| 下标 | `y[key]` → `__getitem__` | `y[key]`（但无统一协议钩子） |
| 当函数调用 | `f()` → `__call__` | 函数本身可调用；普通对象默认不行 |
| 字符串化 | `str` / `repr` | `toString()` / `console` 展示习惯不同 |

JS 没有一套像 Python 这样集中、统一的「语言级协议表」。  
Python 的优势是：**你实现几个 dunder，整套语法立刻可用**。

### 2.3 设计原则：只实现你需要的协议

#### 为什么不要「实现一堆 dunder」？

因为每个 dunder 都是**公开 API 承诺**：

- 实现了 `__len__`，用户就会写 `len(obj)` 并假定它便宜、正确
- 实现了 `__getitem__`，用户就会写 `obj[i]` 并假定越界行为合理
- 实现了 `__eq__`，用户就会拿去比较、去重，并可能牵涉哈希

#### 怎么选

**需要容器行为就实现容器协议；需要漂亮打印就实现 `__str__` / `__repr__`。**  
不要为了「显得高级」把运算符、切片、描述符一次堆上。

#### 跑一下：最小有用集合

对 Agent 里的集合类，常常这组就够用：

```text
__repr__ / __str__
__len__ / __bool__
__contains__ / __getitem__ / __iter__
（可选）__call__
```

#### 易错点

- **「能实现」≠「应该实现」**：`Message + Message` 若业务含义不清，宁可不写 `__add__`。
- **协议要自洽**：有 `__eq__` 就要想哈希；有 `__getitem__` 就要想越界异常类型。

---

## 3. 必掌握：常用 dunder 方法

### 3.1 展示：`__repr__` 与 `__str__`

#### 为什么需要两套展示？

调试和给用户看，需求不同：

| 场景 | 需要什么 |
|------|----------|
| 日志给人类扫一眼 | 短、可读：`[user] 你好` |
| REPL / 异常栈 / 容器里嵌套打印 | 无歧义：最好能看出类型和字段 |

Python 为此拆成：

- `__str__`：面向可读展示
- `__repr__`：面向调试 / 无歧义

#### 怎么写

```python
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str

    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"

    # dataclass 已生成不错的 __repr__；需要时可覆盖
    # def __repr__(self) -> str:
    #     return f"Message(role={self.role!r}, content={self.content!r})"
```

经验口诀：

- `__str__`：可读
- `__repr__`：尽量无歧义，最好能看出如何构造（理想情况下 `eval(repr(x))` 能还原，现实中常做不到，但方向对）

`!r` 的意思是「用 `repr` 格式嵌入」，调试字符串时特别有用。

#### 跑一下

```python
m = Message("user", "你好")

print(str(m))     # [user] 你好
print(m)          # 同上：print 走 __str__
print(repr(m))    # Message(role='user', content='你好')  ← dataclass 默认

# 容器会优先用元素的 __repr__
print([m])        # [Message(role='user', content='你好')]
```

再看「只实现一个」时的回退：

```python
class OnlyRepr:
    def __repr__(self) -> str:
        return "OnlyRepr()"


class OnlyStr:
    def __str__(self) -> str:
        return "human-friendly"


print(OnlyRepr())      # OnlyRepr()  ← 无 __str__ 时用 __repr__
print(repr(OnlyStr())) # <__main__.OnlyStr object at 0x...>  ← 默认 repr
print(OnlyStr())       # human-friendly
```

#### 易错点

1. **在 `__repr__` / `__str__` 里做复杂 I/O 或可能失败的逻辑**  
   对象半初始化时一 `print` 又炸一次，调试更惨。保持简洁、只读已有字段。

2. **`__repr__` 输出太长**  
   大 `content` 可以截断：`content[:40]!r` + `"..."`，避免日志被一条消息刷爆。

3. **误以为 `dataclass` 的 `__repr__` 不能关**  
   `@dataclass(repr=False)` 可关掉，再自己写。

4. **f-string 默认更接近 `str`**  
   调试时记得 `{obj!r}`。

#### 和 JavaScript 对照

| Python | JavaScript（近似） |
|--------|-------------------|
| `__str__` | `toString()` |
| `__repr__` | 没有同等标准；更像调试用的自定义 inspect |
| `console.log(obj)` | 常看对象结构，不保证走 `toString` |
| `String(obj)` | 更接近 `toString` |

```python
print(str(m))
print(repr(m))
```

```javascript
class Message {
  constructor(role, content) {
    this.role = role
    this.content = content
  }
  toString() {
    return `[${this.role}] ${this.content}`
  }
}
const m = new Message("user", "你好")
console.log(String(m))  // [user] 你好
console.log(m)          // 对象结构（不一定等于 toString）
```

---

### 3.2 真假值：`__bool__` / `__len__`

#### 为什么需要自定义真假值？

Agent 代码里很常见：

```python
if not messages:
    ...
if buffer:
    flush(buffer)
if budget:
    continue_loop()
```

如果自定义集合/缓冲/额度对象不能直接用于 `if`，你就得到处写 `if len(x) == 0`，既啰嗦又容易漏。

#### 规则（先记清）

`bool(x)` / `if x:` 的查找顺序：

```text
1) 有 __bool__  → 用它（必须返回 True/False）
2) 否则有 __len__ → len == 0 为假，否则为真
3) 两者都没有 → 对象恒为 True
```

第三点特别容易踩坑：空的「看起来像容器」的自定义对象，若两者都没实现，`if obj:` 仍为真。

#### 怎么写

```python
class Buffer:
    def __init__(self, items: list | None = None) -> None:
        # 用 is not None，避免传入空列表 [] 被 or 丢掉
        self.items = items if items is not None else []

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return len(self.items) > 0
```

很多时候**只实现 `__len__` 就够**：`bool` 会自动根据长度判断。  
显式写 `__bool__` 的价值在于：真假值**不是**「长度非零」时（例如「额度对象：remaining > 0 才为真，但 `__len__` 另有含义」）。

#### 跑一下

```python
buf = Buffer()
print(len(buf))     # 0
print(bool(buf))    # False
if not buf:
    print("empty")  # empty

buf.items.append("x")
print(bool(buf))    # True


class AlwaysTruthy:
    pass


print(bool(AlwaysTruthy()))  # True  ← 没有 __bool__/__len__


class LenOnly:
    def __len__(self) -> int:
        return 0


print(bool(LenOnly()))  # False  ← 回退到 __len__
```

#### 易错点

1. **可变默认参数式写法**：`items: list | None = None` 后用 `items or []`  
   传入合法的空列表 `[]` 会被当成假，悄悄换成新列表。用 `is not None`。

2. **`__bool__` 返回非 bool**  
   应返回真正的 `True`/`False`，不要返回 `0`/`1` 以外的奇怪对象。

3. **昂贵的 `__bool__`**  
   `if obj:` 可能很频繁；别在里面做网络请求或全表扫描。

4. **和「空字符串 / 空列表」内置行为对齐**  
   用户对容器的直觉是「空为假」；你的 MessageList 最好遵守同一习惯。

#### 和 JavaScript 对照

| Python | JavaScript |
|--------|------------|
| `if obj:` 看 `__bool__` / `__len__` | 看 truthy/falsy 规则（`0`/`""`/`null`/`undefined`/`NaN`/`false`） |
| 自定义类默认恒真（无协议时） | 普通对象几乎总是 truthy：`if ({})` 为真 |
| `len(obj) == 0` 可驱动假值 | 数组空不会自动让 `if (arr)` 为假——`[]` 仍是 truthy |

```python
print(bool([]))       # False
print(bool(Buffer())) # False（实现了协议后）
```

```javascript
console.log(Boolean([]))  // true  ← 和 Python 空列表不同！
console.log([].length)    // 0
```

前端同学特别容易在这里踩跨语言差异：**JS 空数组是 truthy，Python 空 list 是 falsy。**

---

### 3.3 相等比较：`__eq__`

#### 为什么需要 `__eq__`？

业务去重、测试断言、缓存键比对，都会写 `a == b`。  
默认的 `==` 对自定义实例往往是**比身份**（是不是同一个对象），不是比「业务内容是否相同」。

```python
class ToolCall:
    def __init__(self, name: str, arguments: dict) -> None:
        self.name = name
        self.arguments = arguments


a = ToolCall("search", {"q": "a"})
b = ToolCall("search", {"q": "a"})
print(a == b)  # False  ← 默认比的是 identity
print(a is b)  # False
```

Agent 里「两次工具调用参数一样」通常应视为相等——这就要自定义 `__eq__`。

#### 怎么写

**方式 A：`dataclass`（最省事，字段相等即相等）**

```python
from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    arguments: dict


print(ToolCall("search", {"q": "a"}) == ToolCall("search", {"q": "a"}))  # True
```

**方式 B：手写 class**

```python
class ToolCall:
    def __init__(self, name: str, arguments: dict) -> None:
        self.name = name
        self.arguments = arguments

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ToolCall):
            return NotImplemented
        return self.name == other.name and self.arguments == other.arguments

    def __repr__(self) -> str:
        return f"ToolCall({self.name!r}, {self.arguments!r})"
```

返回 `NotImplemented`（注意不是 `NotImplementedError`）是礼貌做法：  
告诉 Python「我不知道怎么和这种类型比」，让解释器再尝试另一边的逻辑，而不是武断返回 `False`。

#### 跑一下

```python
a = ToolCall("search", {"q": "RAG"})
b = ToolCall("search", {"q": "RAG"})
c = ToolCall("calc", {"expr": "1+1"})

print(a == b)      # True
print(a == c)      # False
print(a == "search")  # False（通常会落到 NotImplemented 后的最终结果）


# 去重保序（dict 不能直接丢进 set，用签名）
import json


def unique_calls(calls: list[ToolCall]) -> list[ToolCall]:
    seen: set[str] = set()
    result: list[ToolCall] = []
    for call in calls:
        key = json.dumps(
            {"name": call.name, "arguments": call.arguments},
            sort_keys=True,
            ensure_ascii=False,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(call)
    return result


calls = [a, b, c, ToolCall("search", {"q": "RAG"})]
print(unique_calls(calls))  # 两条：search + calc
```

#### 易错点

1. **只实现 `__eq__` 却把对象放进 `set` / 当 `dict` key**  
   定义了 `__eq__` 后，若未定义 `__hash__`，实例通常会变成不可哈希（这是保护）。  
   可变对象（字段还会变）常见做法：`__hash__ = None`。  
   Message / ToolCall 当 key 并不常见，先知道有这回事。

2. **`__eq__` 里直接 `return False` 对未知类型**  
   更稳妥是 `return NotImplemented`。

3. **比较时修改对象**  
   `__eq__` 应无副作用。

4. **浮点、大 dict、深层嵌套的相等成本**  
   测试可以比全字段；热路径去重更常用「签名字符串 / id」。

#### 和 JavaScript 对照

| Python | JavaScript |
|--------|------------|
| 可自定义 `__eq__` | 没有给 `==` 真正重载的标准机制 |
| `dataclass` 按字段比 | 通常手写比较或用结构化比较库 |
| `NotImplemented` 双分派 | 无对等物 |
| 默认实例 `==` 近似 `is` | 对象 `===` 比引用 |

```javascript
// JS 里两个「长得一样」的对象默认不相等
const a = { name: "search", arguments: { q: "a" } }
const b = { name: "search", arguments: { q: "a" } }
console.log(a === b)  // false
```

---

### 3.4 容器协议：`__len__` / `__contains__` / `__getitem__` ...

#### 为什么需要容器协议？

Agent 里到处都是「集合型对象」：

- 消息历史 `MessageList`
- 工具注册表 `ToolRegistry`
- 检索结果列表、待执行 tool call 队列

用户（包括未来的你）天然想写：

```python
len(messages)
"user" in messages
messages[0]
for m in messages:
    ...
```

而不是：

```python
messages.size()
messages.has_role("user")
messages.get(0)
messages.each(...)
```

容器协议就是把这些语法能力接到你的类上。

#### 怎么写（最小可用 MessageList）

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass
class Message:
    role: str
    content: str

    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"


class MessageList:
    def __init__(self) -> None:
        self._items: list[Message] = []

    def add(self, message: Message) -> None:
        self._items.append(message)

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return len(self._items) > 0

    def __contains__(self, role: object) -> bool:
        # 支持："user" in messages  （按 role 判断，教学向 API）
        return any(m.role == role for m in self._items)

    def __getitem__(self, index: int) -> Message:
        # 初期只支持 int；切片见易错点
        return self._items[index]

    def __iter__(self) -> Iterator[Message]:
        return iter(self._items)

    def __repr__(self) -> str:
        return f"MessageList({self._items!r})"
```

上一章的 `ToolRegistry` 是同一思路：内部用 `dict`/`list` 存数据，对外暴露协议。

#### 跑一下

```python
messages = MessageList()
print(bool(messages))  # False

messages.add(Message("system", "You are helpful."))
messages.add(Message("user", "hi"))

print(len(messages))       # 2
print("user" in messages)  # True
print("assistant" in messages)  # False
print(messages[0])         # Message(...)；str 则是 [system] ...
print(messages[-1])        # 最后一条（list 索引语义被透传）

for m in messages:
    print(str(m))
```

输出大致是：

```text
False
2
True
False
Message(role='system', content='You are helpful.')
Message(role='user', content='hi')
[system] You are helpful.
[user] hi
```

#### 再补一组：读写删（`__setitem__` / `__delitem__`）

不是每个集合都要可写。需要时：

```python
class MutableMessageList(MessageList):
    def __setitem__(self, index: int, value: Message) -> None:
        self._items[index] = value

    def __delitem__(self, index: int) -> None:
        del self._items[index]


ms = MutableMessageList()
ms.add(Message("user", "a"))
ms.add(Message("user", "b"))
ms[0] = Message("user", "A")
del ms[1]
print(list(ms))
```

设计建议：

- **注册表**：常提供 `__getitem__`，不一定提供 `__setitem__`（改用 `register`）
- **消息列表**：是否允许 `messages[i] = ...` 取决于你是否想暴露可变性

#### 易错点

1. **`__getitem__` 收到切片 `slice`**  
   `obj[1:3]` 传入的是 `slice` 对象，不是两个 int。  
   初期可明确只支持 `int`，其它类型抛 `TypeError`：

   ```python
   def __getitem__(self, index: int | slice) -> Message | list[Message]:
       if isinstance(index, slice):
           return self._items[index]
       if isinstance(index, int):
           return self._items[index]
       raise TypeError("index must be int or slice")
   ```

2. **`__contains__` 语义要写清**  
   `"user" in messages` 是「存在该 role」还是「存在该 Message 对象」？  
   两种都行，但必须在文档/注释里说死，并保持一致。

3. **返回内部可变对象的引用**  
   `messages[0]` 若直接返回内部 dict/对象，调用方改了字段等于捅破封装。  
   练习里推荐返回拷贝，或明确注释「返回内部引用」。

4. **只有 `__getitem__` 也能被 `for` 迭代（旧协议）**  
   现代代码请显式写 `__iter__`，意图更清晰。

5. **异常类型要像内置**  
   索引越界 → `IndexError`；缺 key → `KeyError`。别统一抛 `ValueError`。

#### 和 JavaScript 对照

| Python 协议 | 用法 | JavaScript 近似 |
|-------------|------|-----------------|
| `__len__` | `len(x)` | `x.length` / `x.size` |
| `__contains__` | `e in x` | `x.includes(e)` / `x.has(e)` |
| `__getitem__` | `x[i]` | `x[i]` / `x.get(i)` |
| `__iter__` | `for e in x` | `for (const e of x)`（需 iterable） |
| `__setitem__` | `x[i] = v` | `x[i] = v` |

```python
for m in messages:
    print(m)
```

```javascript
for (const m of messages) {
  console.log(m)
}
```

JS 要让对象可 `for...of`，需实现 `Symbol.iterator`；  
Python 则是实现 `__iter__`（或下一章的迭代器协议）。**想法同类，钩子名字不同。**

---

### 3.5 运算符（了解常用即可）

#### 为什么本章只「了解」？

运算符重载很酷，但 Agent 业务里远不如容器协议、`__call__`、展示方法常见。  
你会在评分、向量、金额等类型上遇到；多数业务代码用普通方法更清晰。

#### 怎么写（最小例子）

```python
class Score:
    def __init__(self, value: float) -> None:
        self.value = value

    def __add__(self, other: "Score") -> "Score":
        if not isinstance(other, Score):
            return NotImplemented
        return Score(self.value + other.value)

    def __lt__(self, other: "Score") -> bool:
        if not isinstance(other, Score):
            return NotImplemented
        return self.value < other.value

    def __repr__(self) -> str:
        return f"Score({self.value!r})"
```

#### 跑一下

```python
print(Score(0.2) + Score(0.5))  # Score(0.7)
print(Score(0.2) < Score(0.5))  # True

scores = [Score(0.9), Score(0.2), Score(0.5)]
print(sorted(scores))  # 有 __lt__ 才能这样排
```

常用对照（不必背全）：

| 写法 | 方法 |
|------|------|
| `a + b` | `__add__` |
| `a < b` | `__lt__` |
| `a <= b` | `__le__` |
| `a > b` | `__gt__` |
| `a >= b` | `__ge__` |

#### 易错点

- **业务含义不清时不要重载**：`Message + Message` 是拼接 content？合并对话？看不懂就写 `merge()`。
- **类型不同要返回 `NotImplemented`**，别默默返回错误结果。
- **比较运算最好形成全序**，否则 `sorted` 行为会让人困惑。

#### 和 JavaScript 对照

JS 基本不能重载 `+` / `<`（除了 `valueOf`/`toPrimitive` 等有限钩子）。  
看到 Python 的 `__add__`，把它理解成「显式的操作符钩子」即可。

---

## 4. 必掌握：可调用对象（`__call__`）

### 4.1 函数只是可调用对象的一种

#### 为什么需要 `__call__`？

有时你想要「像函数一样调用」，但又要：

- 保存配置（重试次数、超时、模型名）
- 保存计数 / 缓存
- 附带其它方法（`reset()`、`stats()`）

闭包能做一部分；对象 + `__call__` 往往更清晰、更好扩展。

#### 怎么写

```python
class Greeter:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def __call__(self, name: str) -> str:
        return f"{self.prefix}, {name}"
```

任何实现 `__call__` 的对象，都可以像函数一样调用；`callable(obj)` 为 `True`。

#### 跑一下

```python
hello = Greeter("hello")
print(hello("Alice"))   # hello, Alice
print(callable(hello))  # True
print(hello.__call__("Bob"))  # 等价，但没人这么写日常代码
```

心智模型：

```text
普通函数：  代码挂在函数对象上，状态较少
可调用对象：代码在 __call__，状态挂在 self 上
```

#### 易错点

- **把「创建实例」和「调用实例」搞混**：`Greeter("hello")` 是构造；`hello("Alice")` 才是 `__call__`。
- **`callable(cls)` 也对**：类本身可调用（用来构造）；实例是否可调用取决于有没有 `__call__`。

### 4.2 Agent / Tool 场景

#### 为什么 Tool 适合做成可调用对象？

工具同时具备：

1. **数据**：`name` / `description` / schema  
2. **行为**：执行 handler

写成「数据 + `__call__`」，用起来非常自然：

```python
registry["search"](query="RAG", top_k=2)
```

#### 怎么写：可调用 Tool

```python
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    handler: Callable[..., Any]
    description: str = ""

    def __call__(self, **kwargs: Any) -> Any:
        return self.handler(**kwargs)

    def __str__(self) -> str:
        return f"Tool({self.name})"
```

#### 怎么写：可调用重试器（带状态）

```python
class Retry:
    def __init__(self, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts
        self.calls = 0

    def __call__(self, fn, *args, **kwargs):
        last_error: Exception | None = None
        for _ in range(self.max_attempts):
            self.calls += 1
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # 演示用，真实项目应收窄异常
                last_error = exc
        assert last_error is not None
        raise RuntimeError(
            f"failed after {self.max_attempts} attempts"
        ) from last_error
```

#### 怎么写：可调用 Agent（设计选择）

```python
class Agent:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, query: str) -> str:
        return f"{self.name} answers: {query}"
```

是否采用 `agent("question")` 这种风格是设计选择；有人更喜欢 `agent.run(...)`。  
关键能力是：**看到 `obj()` 先找 `__call__`**。

#### 跑一下

```python
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


tool = Tool("search", search, "keyword search")
print(callable(tool))
print(str(tool))
print(tool(query="RAG", top_k=2))


retry = Retry(2)

def flaky():
    raise ValueError("boom")

try:
    retry(flaky)
except RuntimeError as e:
    print(type(e).__name__, "← 最终失败")
    print("calls =", retry.calls)  # 2


run = Agent("demo")
print(run("what is RAG"))
```

#### 易错点

1. **可调用对象被当成无状态函数到处复用**  
   `Retry` 的 `calls` 会跨调用累积（或你选择每次重置——必须在注释说清）。

2. **`__call__` 签名过于随意**  
   Tool 建议明确 `**kwargs` 或与 schema 对齐，避免 `*args` 滥用导致排查困难。

3. **在 `__call__` 里吞掉所有异常**  
   演示可以；生产要收窄、记录、再抛出。

4. **和装饰器章的关系**  
   很多装饰器返回的就是「可调用对象」；先把 `__call__` 本身吃透。

### 4.3 和普通函数怎么选？

| 更适合函数 | 更适合可调用对象 |
|------------|------------------|
| 无状态变换 | 需要保存配置/计数/连接 |
| 简单短小 | 还要附带其它方法 |
| 到处传递回调 | 生命周期更长的组件 |
| `lambda` / 小钩子 | Tool / Agent / Retry / Client 门面 |

#### 和 JavaScript 对照

| Python | JavaScript |
|--------|------------|
| 实例实现 `__call__` 后可 `obj()` | 普通对象不能当函数调用 |
| `callable(obj)` | `typeof obj === "function"` |
| 类可调用 → 造实例 | `new Cls()`；无 `new` 时行为因函数而异 |
| 带状态可调用对象 | 「函数上挂属性」或 class 里再包一层方法 |

```python
tool(query="RAG")
```

```javascript
// JS 更常见：保存函数引用，或显式 .run()
tool.run({ query: "RAG" })
// 或者直接传 handler 函数
handler({ query: "RAG" })
```

---

## 5. 建议掌握：描述符入门

### 5.1 你已经用过描述符

#### 为什么要提描述符？

因为你写过：

```python
@property
def celsius(self) -> float:
    ...
```

也在框架里见过「字段校验」「ORM 列」「typed attribute」。  
它们底层常常是**描述符协议**：类属性对象实现了 `__get__` / `__set__` / `__delete__`。

本阶段目标不是手写复杂描述符框架，而是：

> 再看到 `__get__` / `__set__` / `__set_name__`，能说：「哦，这是描述符。」

#### 怎么理解 `@property`

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius


t = Temperature(36.5)
print(t.celsius)  # 看起来像属性访问，实际触发 property.__get__
```

访问 `obj.celsius` 时，并不是简单从 `__dict__` 取值，而是触发了 property 对象的 `__get__`。

### 5.2 最小描述符长什么样

#### 为什么要有「非空字段」这种东西？

Tool 名、Agent 名、配置 key——经常要求「非空、去首尾空格」。  
可以在每个 `__init__` 里手写校验，也可以把规则做成可复用描述符。

#### 怎么写

```python
class NonEmpty:
    def __init__(self, name: str = "value") -> None:
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            # 通过类访问：ToolSpec.name → 返回描述符自己
            return self
        return getattr(obj, self.private_name)

    def __set__(self, obj, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{self.name} must be non-empty")
        setattr(obj, self.private_name, value.strip())


class ToolSpec:
    name = NonEmpty("name")  # 注意：挂在类上，不是写在 __init__ 里临时创建

    def __init__(self, name: str) -> None:
        self.name = name  # 触发 NonEmpty.__set__
```

更现代的写法会用 `__set_name__` 自动拿属性名（了解即可）：

```python
class NonEmpty2:
    def __set_name__(self, owner, name: str) -> None:
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name)

    def __set__(self, obj, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{self.name} must be non-empty")
        setattr(obj, self.private_name, value.strip())


class ToolSpec2:
    name = NonEmpty2()
```

#### 跑一下

```python
t = ToolSpec("search")
print(t.name)  # search

t.name = "  calc  "
print(t.name)  # calc  ← 自动 strip

try:
    t.name = "   "
except ValueError as e:
    print(e)  # name must be non-empty

print(ToolSpec.name)  # <...NonEmpty object...> 或描述符实例
```

#### 易错点

1. **描述符必须挂在类上**  
   写在 `__init__` 里的 `self.name = NonEmpty()` 不会按描述符协议工作。

2. **和实例 `__dict__` 同名覆盖**  
   存储要用私有名（`_name`）或 `private_name`，避免与描述符自身抢名字。

3. **`__get__` 忘记处理 `obj is None`**  
   通过类访问时 `obj` 为 `None`，通常应返回描述符自己。

4. **本阶段不要过度使用**  
   校验库、ORM 可以看；业务代码 90% 场景用 `@property` / `dataclass` / 显式校验函数就够。

### 5.3 学习建议

- 会用 `@property` / `dataclass` 解决 90% 需求
- 读 ORM、校验库源码时，遇到 `__get__`/`__set__`/`__set_name__` 知道是描述符
- **本阶段不必手写复杂描述符**；练习挑战题够用即可

#### 和 JavaScript 对照

| Python | JavaScript |
|--------|------------|
| 描述符 `__get__`/`__set__` | `Object.defineProperty` / getter/setter |
| `@property` | `get field() { ... }` |
| 类级复用字段行为 | 装饰器或基类 getter，但无完全等同的描述符生态 |

```javascript
class Temperature {
  constructor(celsius) {
    this._celsius = celsius
  }
  get celsius() {
    return this._celsius
  }
}
```

---

## 6. 了解即可：和 CPython 的关系

#### 为什么只需了解？

CPython 是最常用的 Python 解释器实现。很多内置类型（`list`/`dict`）的高效行为在 C 层，不完全等价于你用纯 Python 写的同名 dunder。

#### 对你意味着什么

1. **协议是语言层面的契约，值得学**——自定义类靠它与语法协作  
2. **性能细节、内存布局先别追**——不是本阶段瓶颈  
3. **业务代码优先正确与可读**，而不是模仿 C 层优化  

#### 跑一下（建立「别神化」直觉）

```python
class FakeList:
    def __len__(self) -> int:
        return 3


print(len(FakeList()))  # 3 —— 协议生效
print(len([1, 2, 3]))   # 3 —— 内置 list 可能走更快路径，但对你用法一样
```

够用就停：你会用协议，就达到本章目标了。

---

## 7. 常见坑

1. **`__repr__` / `__str__` 里访问可能未初始化的属性**  
   对象创建失败时调试会更惨，保持简洁、防御缺失字段。

2. **只实现 `__eq__` 不思考哈希**  
   若对象要进 `set`/做 `dict` key，需要匹配的 `__hash__`；可变对象通常设 `__hash__ = None`（dataclass 可变默认也如此）。Message 当 key 并不常见，先知道有这回事。

3. **`__getitem__` 支持切片时要处理 `slice`**  
   `obj[1:3]` 传入的是 slice 对象；初期可只支持 int 索引，并抛清晰的 `TypeError`。

4. **可调用对象被误当成无状态函数多次复用**  
   注意实例内计数器/缓存是否跨调用残留；在注释写清生命周期。

5. **为了炫技实现运算符重载**  
   业务含义不清时，宁可写 `add_score()` / `merge_messages()`。

6. **自定义容器两者都不写：无 `__bool__` 也无 `__len__`**  
   结果是「空对象在 `if obj:` 里仍为真」，和用户对 list 的直觉相反。

7. **`__contains__` / `__eq__` 语义漂移**  
   今天按 role 判断 `in`，明天又按对象身份——API 会变得不可信。写清、测住。

8. **描述符实例化位置错误**  
   描述符要作为**类属性**定义；放进 `__init__` 不会获得描述符协议。

---

## 8. 综合小例子：Pythonic 的 ToolRegistry

把本章几条主线收束到一个可运行例子：

- Tool：`__call__` + `__str__`
- Registry：容器协议 + `__repr__`
- 用起来像内置映射/集合

```python
from dataclasses import dataclass
from typing import Any, Callable, Iterator


@dataclass
class Tool:
    name: str
    handler: Callable[..., Any]
    description: str = ""

    def __call__(self, **kwargs: Any) -> Any:
        return self.handler(**kwargs)

    def __str__(self) -> str:
        return f"Tool({self.name})"

    def __repr__(self) -> str:
        return f"Tool(name={self.name!r}, description={self.description!r})"


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def __len__(self) -> int:
        return len(self._tools)

    def __bool__(self) -> bool:
        return len(self._tools) > 0

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __getitem__(self, name: str) -> Tool:
        return self._tools[name]  # 缺省 KeyError，和 dict 一致

    def __iter__(self) -> Iterator[Tool]:
        return iter(self._tools.values())

    def __repr__(self) -> str:
        names = ", ".join(sorted(self._tools))
        return f"ToolRegistry([{names}])"


def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


def calc(expression: str) -> float:
    # 演示用：真实项目请用安全表达式方案，不要直接 eval 不可信输入
    allowed = {"__builtins__": {}}
    return float(eval(expression, allowed, {}))


registry = ToolRegistry()
print(bool(registry))  # False

registry.register(Tool("search", search, "keyword search"))
registry.register(Tool("calc", calc, "simple calculator"))

print(registry)                 # ToolRegistry([calc, search])
print(len(registry))            # 2
print("search" in registry)     # True
print(registry["search"](query="RAG", top_k=2))
print(registry["calc"](expression="1+2"))

for tool in registry:
    print(str(tool), "-", tool.description)
```

这里把「工具既是数据，也可调用；注册表像映射」表达得很自然——这就是数据模型的回报。

---

## 9. 练习指引

请打开并完成：

[`exercises/02-advanced-python/02-data-model.md`](../../exercises/02-advanced-python/02-data-model.md)

建议代码位置：

```text
playground/02-advanced-python/02-data-model/
```

做题顺序建议：

1. **B1** 对照表 + `__str__`/`__repr__`（先把协议眼睛练出来）
2. **B2** MessageList 容器协议（本章核心肌肉记忆）
3. **B3** 可调用 Tool
4. **B4** `__eq__` 与去重
5. 有余力再做 **A1 Registry / A2 Retry**；描述符挑战题对应 §5

---

## 10. 小结与下一站

### 心智模型

```text
语法 / 内置函数
    ↓
查找对象上的协议方法（dunder）
    ↓
执行你的实现
```

再压缩成一句：

> **你实现约定，Python 给你语法。**

### 自检清单

- [ ] 能把 `len` / `in` / 下标 / `print` / 调用 对应到 dunder
- [ ] 说清 `__str__` 与 `__repr__` 的分工，并能写出不同实现
- [ ] 说清 `bool(x)` 的三级回退：`__bool__` → `__len__` → 恒真
- [ ] 能为自定义集合类实现一组容器协议，并处理好越界/缺 key
- [ ] 能写 `__eq__`，知道 `NotImplemented` 与哈希坑
- [ ] 能写 `__call__` 并说明何时优于普通函数（Tool / Retry）
- [ ] 知道 property 与描述符有关，但不强求手写复杂描述符
- [ ] 独立完成练习基础题

### 下一章

[`03-iterator-generator.md`](./03-iterator-generator.md) —— Iterator / Generator：流式输出、惰性处理大数据、理解 `for` 背后的协议。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[面向对象编程](./01-oop.md)
- 下一章：[Iterator / Generator](./03-iterator-generator.md)
