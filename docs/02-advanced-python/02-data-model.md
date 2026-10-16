# Python 数据模型

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/02-advanced-python/02-data-model.md`](../../exercises/02-advanced-python/02-data-model.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：弄清「为什么 `len(x)`、`x in y`、`obj()` 能工作」——答案几乎都是：**对象实现了某些协议（dunder 方法）**。
- **和上一章关系**：OOP 教你如何组织类；数据模型教你如何让类**像 Python 内置对象一样被使用**。

## 学习目标（学完应能做到）

1. 用「协议」视角解释常用语法糖背后调用了什么。
2. 为自定义类实现一组常用 dunder 方法（展示、比较、容器、可调用）。
3. 写出可调用对象（`__call__`），理解它和普通函数的相似处。
4. 完成练习；描述符与 CPython 细节先建立地图即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 对象协议直觉、常用 dunder、可调用对象 | 能写、能读框架代码 |
| **建议掌握** | 描述符入门 | 能认出 `@property` 背后的机制 |
| **了解即可** | 与 CPython 实现的关系 | 知道「别神化」，够用就停 |

---

## 1. 为什么要学（和 Agent 有什么关系）

读 Agent / 后端库时，你会不断遇到「看起来像内置类型」的自定义对象：

```python
len(messages)
tool in registry
agent("你好")          # 有的设计把 agent 做成可调用对象
async with client:     # 后面上下文管理器章
for chunk in stream:   # 下一章迭代器
```

它们不是魔法，而是实现了约定方法：

```text
len(x)     →  x.__len__()
x in y     →  y.__contains__(x) 或迭代比较
f(...)     →  f.__call__(...)
str(x)     →  x.__str__()
```

学会数据模型后，你能：

1. **读源码更快**（看到 `__getitem__` 就知道能 `obj[key]`）
2. **把自研 Tool/Registry/MessageList 写得更 Pythonic**
3. **少写** `registry.get_length()` 这种别扭 API

---

## 2. 必掌握：对象协议直觉

### 2.1 一句话定义

> **Python 数据模型** = 一套「对象如何与语言语法/内置函数协作」的约定。  
> 你实现约定方法，解释器就给你对应的语法能力。

这些方法名通常形如 `__xxx__`，叫 **dunder methods**（double underscore），也常被叫魔法方法。

### 2.2 语法糖 → 方法 对照（先背最常用）

| 你写的代码 | 大致调用 |
|------------|----------|
| `str(x)` / `print(x)` | `x.__str__()` |
| `repr(x)` | `x.__repr__()` |
| `len(x)` | `x.__len__()` |
| `x in y` | `y.__contains__(x)` |
| `y[key]` | `y.__getitem__(key)` |
| `y[key] = v` | `y.__setitem__(key, v)` |
| `del y[key]` | `y.__delitem__(key)` |
| `f(a, b)` | `f.__call__(a, b)` |
| `bool(x)` | `x.__bool__()` → 若无则 `__len__()` → 若都无则恒为 `True` |
| `a == b` | `a.__eq__(b)` |
| `iter(x)` | `x.__iter__()`（下一章展开） |

不必一次背完；用的时候回来查这张表。

### 2.3 设计原则：只实现你需要的协议

不要为了「显得高级」实现一堆 dunder。  
**需要容器行为就实现容器协议；需要漂亮打印就实现 `__str__`。**

---

## 3. 必掌握：常用 dunder 方法

### 3.1 展示：`__repr__` 与 `__str__`

```python
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str

    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"

    # dataclass 已生成不错的 __repr__；也可自定义


m = Message("user", "你好")
print(str(m))    # [user] 你好   ← 面向用户/日志友好
print(repr(m))   # Message(role='user', content='你好')  ← 面向调试
```

经验：

- `__str__`：可读
- `__repr__`：尽量无歧义，最好能看出如何构造

### 3.2 真假值：`__bool__` / `__len__`

```python
class Buffer:
    def __init__(self, items: list | None = None) -> None:
        # 用 is not None，避免传入空列表 [] 被 or 丢掉
        self.items = items if items is not None else []

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return len(self.items) > 0


buf = Buffer()
if not buf:
    print("empty")
```

规则：有 `__bool__` 用它；否则看 `__len__`（0 为假）；**两者都没有则对象恒为真**。

### 3.3 相等比较：`__eq__`

```python
@dataclass
class ToolCall:
    name: str
    arguments: dict


print(ToolCall("search", {"q": "a"}) == ToolCall("search", {"q": "a"}))  # True
```

`dataclass` 默认按字段比较。自己写 class 时：

```python
class ToolCall:
    def __init__(self, name: str, arguments: dict) -> None:
        self.name = name
        self.arguments = arguments

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ToolCall):
            return NotImplemented
        return self.name == other.name and self.arguments == other.arguments
```

返回 `NotImplemented` 是礼貌做法，让 Python 再尝试另一边的比较逻辑。

### 3.4 容器协议：`__len__` / `__contains__` / `__getitem__` ...

上一章的 `ToolRegistry` 就是典型。再完整一点：

```python
from typing import Iterator


class MessageList:
    def __init__(self) -> None:
        self._items: list[Message] = []

    def add(self, message: Message) -> None:
        self._items.append(message)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, role: object) -> bool:
        # 支持："user" in messages
        return any(m.role == role for m in self._items)

    def __getitem__(self, index: int) -> Message:
        return self._items[index]

    def __iter__(self) -> Iterator[Message]:
        return iter(self._items)


messages = MessageList()
messages.add(Message("system", "You are helpful."))
messages.add(Message("user", "hi"))

print(len(messages))
print("user" in messages)
print(messages[0])
for m in messages:
    print(m)
```

有了这些，你的类型用起来就像内置 list 的「受限版本」。

### 3.5 运算符（了解常用即可）

```python
class Score:
    def __init__(self, value: float) -> None:
        self.value = value

    def __add__(self, other: "Score") -> "Score":
        return Score(self.value + other.value)

    def __lt__(self, other: "Score") -> bool:
        return self.value < other.value


print((Score(0.2) + Score(0.5)).value)  # 0.7
print(Score(0.2) < Score(0.5))          # True
```

Agent 业务里不如容器协议、可调用对象常见；能读懂即可。

---

## 4. 必掌握：可调用对象（`__call__`）

### 4.1 函数只是可调用对象的一种

任何实现 `__call__` 的对象，都可以像函数一样调用：

```python
class Greeter:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def __call__(self, name: str) -> str:
        return f"{self.prefix}, {name}"


hello = Greeter("hello")
print(hello("Alice"))  # hello, Alice
print(callable(hello)) # True
```

这和「带配置的闭包」很像，但状态挂在对象上，更易扩展方法。

### 4.2 Agent / Tool 场景

```python
class Retry:
    def __init__(self, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts
        self.calls = 0

    def __call__(self, fn, *args, **kwargs):
        last_error = None
        for _ in range(self.max_attempts):
            self.calls += 1
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # 演示用，真实项目应收窄异常
                last_error = exc
        raise RuntimeError(f"failed after {self.max_attempts}") from last_error


def flaky():
    raise ValueError("boom")


# retry = Retry(2)
# retry(flaky)  # 会失败，但 calls == 2
```

也可以把「一次 Agent 运行」设计成可调用：

```python
class Agent:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, query: str) -> str:
        return f"{self.name} answers: {query}"


run = Agent("demo")
print(run("what is RAG"))
```

是否采用这种风格是设计选择；关键是：**看到 `obj()` 先找 `__call__`**。

### 4.3 和普通函数怎么选？

| 更适合函数 | 更适合可调用对象 |
|------------|------------------|
| 无状态变换 | 需要保存配置/计数/连接 |
| 简单短小 | 还要附带其它方法 |
| 到处传递回调 | 生命周期更长的组件 |

---

## 5. 建议掌握：描述符入门

### 5.1 你已经用过描述符

`@property` 就是描述符协议的应用：

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius
```

访问 `obj.celsius` 时，并不是简单取属性，而是触发了 property 对象的 `__get__`。

### 5.2 最小描述符长什么样

```python
class NonEmpty:
    def __init__(self, name: str = "value") -> None:
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name)

    def __set__(self, obj, value: str) -> None:
        if not value.strip():
            raise ValueError(f"{self.name} must be non-empty")
        setattr(obj, self.private_name, value.strip())


class ToolSpec:
    name = NonEmpty("name")

    def __init__(self, name: str) -> None:
        self.name = name


t = ToolSpec("search")
print(t.name)
# t.name = "   "  → ValueError
```

### 5.3 学习建议

- 会用 `@property` / `dataclass` 解决 90% 需求
- 读 ORM、校验库源码时，遇到 `__get__`/`__set__`/`__set_name__` 知道是描述符
- **本阶段不必手写复杂描述符**

---

## 6. 了解即可：和 CPython 的关系

CPython 是最常用的 Python 解释器实现。很多内置类型的高效行为在 C 层，不完全等价于你用纯 Python 写的同名 dunder。

对你意味着：

1. 协议是语言层面的契约，值得学
2. 性能细节、内存布局先别追
3. 业务代码优先正确与可读，而不是模仿 C 层优化

---

## 7. 常见坑

1. **`__repr__` 里访问可能未初始化的属性**  
   对象创建失败时调试会更惨，保持简洁。

2. **只实现 `__eq__` 不思考哈希**  
   若对象要进 `set`/做 `dict` key，需要匹配的 `__hash__`；可变对象通常设 `__hash__ = None`（dataclass 可变默认也如此）。Message 当 key 并不常见，先知道有这回事。

3. **`__getitem__` 支持切片时要处理 `slice`**  
   `obj[1:3]` 传入的是 slice 对象；初期可只支持 int 索引。

4. **可调用对象被误当成无状态函数多次复用**  
   注意实例内计数器/缓存是否跨调用残留。

5. **为了炫技实现运算符重载**  
   业务含义不清时，宁可写 `add_score()`。

---

## 8. 综合小例子：Pythonic 的 ToolRegistry

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


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __getitem__(self, name: str) -> Tool:
        return self._tools[name]

    def __iter__(self):
        return iter(self._tools.values())

    def __repr__(self) -> str:
        names = ", ".join(sorted(self._tools))
        return f"ToolRegistry([{names}])"


def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


registry = ToolRegistry()
registry.register(Tool("search", search, "keyword search"))

print(registry)
print(len(registry))
print("search" in registry)
print(registry["search"](query="RAG", top_k=2))
for tool in registry:
    print(str(tool), tool.description)
```

这里把「工具既是数据，也可调用」表达得很自然。

---

## 9. 练习指引

请打开并完成：

[`exercises/02-advanced-python/02-data-model.md`](../../exercises/02-advanced-python/02-data-model.md)

建议代码位置：

```text
playground/02-advanced-python/02-data-model/
```

---

## 10. 小结与下一站

### 心智模型

```text
语法/内置函数
    ↓
查找对象上的协议方法（dunder）
    ↓
执行你的实现
```

### 自检清单

- [ ] 能把 `len` / `in` / 下标 / `print` 对应到 dunder
- [ ] 能为自定义集合类实现一组容器协议
- [ ] 能写 `__call__` 并说明何时优于普通函数
- [ ] 知道 property 与描述符有关，但不强求手写描述符
- [ ] 独立完成练习基础题

### 下一章

[`03-iterator-generator.md`](./03-iterator-generator.md) —— Iterator / Generator：流式输出、惰性处理大数据、理解 `for` 背后的协议。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[面向对象编程](./01-oop.md)
- 下一章：[Iterator / Generator](./03-iterator-generator.md)
