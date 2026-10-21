# 面向对象编程

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：4～7 小时（有 JS/TS class 经验可更快；dataclass / ABC / 组合优先建议动手踩一遍）  
> 对应练习：[`exercises/02-advanced-python/01-oop.md`](../../exercises/02-advanced-python/01-oop.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：学会用 class 表达「有状态的能力单元」——LLM 客户端、Tool、Agent、Memory 在框架里几乎都是对象。
- **你的优势**：TS 的 `class` / `interface` / 构造注入经验很值钱；重点补 Python 的 `dataclass`、`@property`、ABC，以及「组合优于继承」在 Agent 里的落地。

## 学习目标（学完应能做到）

1. 定义 class，正确使用 `__init__`、实例属性与方法。
2. 分清继承与组合，知道 Agent 场景里为何更常选组合。
3. 用 ABC（抽象基类）定义「必须实现的接口」，并写出可替换实现。
4. 用 `dataclass` 快速描述数据对象，用 `@property` 控制只读/派生属性。
5. 完成课后练习，分清必掌握 / 建议掌握 / 了解即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | class / 继承 / 组合、ABC、dataclass、property | 能写、能讲、能做题 |
| **建议掌握** | 常用魔法方法子集、依赖注入直觉 | 会读、会用简单模式 |
| **了解即可** | 元类扫盲 | 只建地图，不深挖 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要面向对象？

函数很适合「无长期状态的变换」：清洗消息、截断上下文、解析 JSON——输入进、结果出。  
但 Agent 系统里大量东西是**带状态、可替换、可配置**的：

```text
LLM Client（不同厂商可替换）
Tool（search / calc / browse）
Memory（短期 / 长期）
Agent（持有 llm + tools + memory，循环调用）
```

没有 class 时，你会很快写成这样：

```text
一堆 dict + 全局变量 + 散落函数
  ├── llm_config = {...}
  ├── tools = [...]
  ├── history = []
  └── run_agent() 里到处 if/else 判断「当前是哪种 llm」
```

有了对象，同一件事通常长这样：

```text
EchoLLM / OpenAIClient  ──┐
SearchTool / CalcTool   ──┼──▶ Agent(llm, tools, memory)
MemoryStore             ──┘
```

框架源码里你会反复看到：

```python
class BaseTool(ABC):
    @abstractmethod
    def run(self, **kwargs): ...

@dataclass
class Message:
    role: str
    content: str
```

#### 本章要练的四种能力

1. **封装状态**：把「数据 + 行为」收成对象（Tool、LLM、Agent）
2. **定契约**：用 ABC 说清「必须实现什么」
3. **拼装系统**：用组合 + 依赖注入组装可替换部件
4. **少踩坑**：分清类属性/实例属性、可变默认值、继承深度

可以先记一句：

> 本章不是要你背 OO 教条，而是让你能读懂框架抽象、自己写出可扩展的小结构，并避免一上来就堆很深的继承树。

---

## 2. 必掌握：class 基础

这一节会刻意写细——class 是后面 ABC、dataclass、Agent 拼装的共同底座。

### 2.1 最小 class

#### 为什么需要 class？

上一模块你会写函数。但「计数器」「聊天客户端」「带历史的 Agent」这类东西：

- 需要**长期记住状态**（当前值、消息列表、已注册工具）
- 需要一组**围绕该状态的操作**（增加、重置、调用）

把它们散成全局变量 + 函数，很快会乱。class 就是给「状态 + 操作」起一个类型名字。

#### 怎么写

```python
class Counter:
    def __init__(self, start: int = 0) -> None:
        self.value = start

    def inc(self, step: int = 1) -> int:
        self.value += step
        return self.value
```

拆开看：

1. `class Counter:` 定义类型；名字用 `PascalCase`
2. `__init__` 在创建实例时调用，负责初始化
3. `self` 是「当前这个实例」；方法里通过 `self.xxx` 读写它的状态
4. `inc` 是实例方法：第一个参数必须是 `self`

#### 跑一下

```python
c = Counter(10)
print(c.inc())    # 11
print(c.value)    # 11
print(c.inc(5))   # 16
```

心智图：

```text
Counter(10)
    ↓
创建实例 c，调用 __init__，挂上 c.value = 10
    ↓
c.inc()  →  self 就是 c  →  value 变成 11
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 方法忘写 `self` | `TypeError: takes 0 positional arguments but 1 was given` |
| 在方法里写 `value = ...` 却没用 `self.value` | 只是局部变量，实例上看不到 |
| 以为要写 `new Counter(10)` | Python 一般直接 `Counter(10)`，没有 `new` |
| 把 `__init__` 当成「必须 return 实例」 | `__init__` 应返回 `None`；实例由解释器创建 |

#### JS/TS 对照

| TypeScript | Python |
| --- | --- |
| `constructor(private value = 0) {}` | `__init__(self, start=0): self.value = start` |
| `this.value` | `self.value` |
| `new Counter(10)` | `Counter(10)`（一般不写 `new`） |
| 方法里 `this` 可隐式存在 | **必须显式**把 `self` 写成第一个参数 |

---

### 2.2 方法、属性、为什么要对象

#### 为什么需要「数据 + 行为」绑在一起？

Agent 里一条消息常常同时需要：字段本身、转成 dict、做预览、校验 role……  
如果只有裸 dict，相关逻辑会散落在各处；对象可以把「属于它的操作」收拢。

#### 怎么写

```python
class ChatMessage:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def as_dict(self) -> dict:
        return {"role": self.role, "content": self.content}

    def preview(self, n: int = 20) -> str:
        text = self.content.strip()
        return text if len(text) <= n else text[: n - 3] + "..."
```

#### 跑一下

```python
m = ChatMessage("user", "你好，请介绍一下 RAG")
print(m.as_dict())
# {'role': 'user', 'content': '你好，请介绍一下 RAG'}

print(m.preview(10))
# 你好，请介...
```

#### 易错点

- 不是所有东西都该变成 class：临时 JSON、一次性中间结果，用 `dict` 往往更干净
- 对象适合「长期存在、有明确行为边界」的概念；不要为了 OO 而 OO
- 方法里需要实例状态 → 写成实例方法；不需要 → 考虑模块级函数或 `@staticmethod`（后面用到再学）

#### 何时用对象 vs 松散函数？

| 更适合对象 | 更适合函数 / dict |
| --- | --- |
| 有状态要跨多次调用保留 | 无状态变换（清洗、解析） |
| 多个操作围绕同一批数据 | 一次算完就结束 |
| 需要可替换实现（见 ABC） | 临时数据结构 |

---

### 2.3 类属性 vs 实例属性

#### 为什么要分清这两种？

初学者常把「共享默认值」和「每个对象自己的状态」混在一起，尤其是可变对象（list/dict）当类属性时，会出现「改了一个实例，别的实例也被污染」。

#### 怎么写

```python
class LLMClient:
    default_timeout = 30.0  # 类属性：定义在 class 体里，大家共享查找

    def __init__(self, model: str) -> None:
        self.model = model          # 实例属性：每个对象各自一份
        self.timeout = self.default_timeout
```

查找规则（简化版）：

```text
读 obj.xxx
  → 先看实例自己有没有 xxx
  → 没有再去类上找
```

#### 跑一下

```python
a = LLMClient("gpt-mini")
b = LLMClient("local-llm")
print(a.default_timeout, b.default_timeout)  # 30.0 30.0

LLMClient.default_timeout = 60.0
print(a.default_timeout, b.default_timeout)  # 60.0 60.0

a.timeout = 5.0  # 改的是实例自己的 timeout，不影响类属性
print(a.timeout, b.timeout)  # 5.0 60.0
```

再看可变类属性的坑：

```python
class BadRegistry:
    tools: list[str] = []  # 危险：类上共享同一个 list

    def add(self, name: str) -> None:
        self.tools.append(name)


r1 = BadRegistry()
r2 = BadRegistry()
r1.add("search")
print(r2.tools)  # ['search']  ← 被污染了！
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `class A: items = []` 再 `self.items.append(...)` | 多个实例共享同一 list |
| 把业务状态挂在类属性上 | 并发/多实例时互相踩踏 |
| 以为 `self.timeout = ...` 会改类属性 | 通常只是在实例上新建同名属性 |

新手阶段经验法则：

> **状态优先放实例属性**；类属性只放真正共享的常量/默认配置。

#### JS/TS 对照

| TypeScript | Python |
| --- | --- |
| `static defaultTimeout = 30` | `default_timeout = 30.0`（类体里） |
| 实例字段 `this.model = model` | `self.model = model` |
| 静态可变数组同样会共享 | 类属性 list/dict 同样会共享 |

---

## 3. 必掌握：继承 vs 组合

Agent 代码里「该继承还是该组合」比语法本身更重要。这一节建立选型直觉。

### 3.1 继承：is-a（是一种）

#### 为什么需要继承？

多种 Tool 都有 `name`，都要能 `run(...)`，差异只在具体实现。  
继承表达：**子类是一种父类**，可以复用骨架、统一接口。

#### 怎么写

```python
class Tool:
    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, **kwargs):
        raise NotImplementedError("subclass must implement run()")


class SearchTool(Tool):
    def run(self, query: str, top_k: int = 3) -> list[str]:
        return [f"{query}#{i}" for i in range(top_k)]


class CalcTool(Tool):
    def run(self, expression: str) -> float:
        mapping = {"1+2": 3.0, "10/2": 5.0}
        if expression not in mapping:
            raise ValueError(f"unsupported: {expression}")
        return mapping[expression]
```

#### 跑一下

```python
search = SearchTool("search")
print(search.name)                       # search
print(search.run(query="RAG", top_k=2))  # ['RAG#0', 'RAG#1']
print(isinstance(search, Tool))          # True
```

#### 易错点

- 父类里 `raise NotImplementedError` 只是**运行时约定**；忘了实现要等到调用才爆（更强约束见 ABC）
- 继承树一深（3 层以上），调用链会很难跟
- 「为了复用两行代码就继承」通常是坏味道——复用优先函数/组合

#### JS/TS 对照

```typescript
class Tool {
  constructor(public name: string) {}
  run(_kwargs: Record<string, unknown>): unknown {
    throw new Error("not implemented");
  }
}

class SearchTool extends Tool {
  run(kwargs: { query: string; top_k?: number }): string[] {
    const topK = kwargs.top_k ?? 3;
    return Array.from({ length: topK }, (_, i) => `${kwargs.query}#${i}`);
  }
}
```

Python 的 `class SearchTool(Tool)` ≈ TS 的 `extends Tool`。

---

### 3.2 组合：has-a（拥有）

#### 为什么需要组合？

`Agent` **不是一种** `LLMClient`，也不是一种 `Tool`。  
它是**拥有** llm、tools、memory，并把它们编排起来——这是 has-a，不是 is-a。

#### 怎么写

```python
class Agent:
    def __init__(self, llm: "LLMClient", tools: list[Tool]) -> None:
        self.llm = llm          # 拥有一个 llm
        self.tools = tools      # 拥有一组 tools

    def available_tool_names(self) -> list[str]:
        return [t.name for t in self.tools]

    def call_tool(self, name: str, **kwargs):
        for t in self.tools:
            if t.name == name:
                return t.run(**kwargs)
        raise KeyError(f"unknown tool: {name}")
```

#### 跑一下

```python
class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


agent = Agent(llm=EchoLLM(), tools=[SearchTool("search"), CalcTool("calc")])
print(agent.available_tool_names())
# ['search', 'calc']

print(agent.call_tool("calc", expression="1+2"))
# 3.0
```

#### 易错点

- 组合不是「永远不继承」——Tool 族仍可用继承/ABC
- 别把 Agent 做成「继承 OpenAIClient 再挂 tools」这种怪异结构
- 依赖放在 `__init__` 里传入，而不是在方法里临时 `OpenAIClient()`（见 §8 依赖注入）

#### 心智图

```text
继承：SearchTool ──是一种──▶ Tool
组合：Agent ──拥有──▶ llm / tools / memory
```

---

### 3.3 Agent 场景怎么选？

#### 为什么需要一张选型表？

很多 Agent demo 后期翻车，就是因为「一切皆继承」：`BaseAgent` → `ChatAgent` → `RAGAgent` → `MySpecialAgent`，改一处牵全身。

#### 对照表

| 更适合继承 | 更适合组合 |
| --- | --- |
| 多种 Tool 共享同一接口骨架 | Agent 组装 llm / tools / memory |
| 少量层级（1～2 层） | 可替换依赖、可测试 |
| 「是一种」关系非常稳定 | 「拥有并协作」关系 |
| 需要 `isinstance` / 统一调度 | 需要灵活插拔部件 |

经验法则：

> **默认组合；继承只用于稳定的接口族。**  
> 继承树一深，框架代码就会变得难读难测。

#### 反例纠错

```python
# ❌ 反例：为了「复用」硬继承
class OpenAIAgent(OpenAIClient):
    def __init__(self):
        super().__init__()
        self.tools = []

# ✅ 正例：组合
class Agent:
    def __init__(self, llm: LLMClient, tools: list[BaseTool]) -> None:
        self.llm = llm
        self.tools = tools
```

---

### 3.4 `super()`

#### 为什么需要 `super()`？

子类想扩展父类行为（多挂一个 `description`），又不想复制父类 `__init__` 的赋值逻辑——用 `super()` 调用父类实现。

#### 怎么写

```python
class NamedTool(Tool):
    def __init__(self, name: str, description: str) -> None:
        super().__init__(name)
        self.description = description
```

#### 跑一下

```python
t = NamedTool("search", "网页检索")
print(t.name, t.description)  # search 网页检索
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 子类 `__init__` 里既不调 `super()` 又不自己赋 `self.name` | 父类约定的属性缺失 |
| 多继承时乱调父类 | MRO（方法解析顺序）变复杂——本章先避开多继承 |
| 以为 `super()` 只能用在 `__init__` | 任何需要复用父类方法的地方都能用 |

#### JS/TS 对照

```typescript
class NamedTool extends Tool {
  constructor(name: string, public description: string) {
    super(name);
  }
}
```

Python 的 `super().__init__(name)` ≈ TS 的 `super(name)`。

---

## 4. 必掌握：抽象基类（ABC）

### 4.1 为什么需要 ABC？

#### 问题：只靠约定会忘

上一节父类里 `raise NotImplementedError` 有个弱点：  
你忘了实现 `run`，**实例化时不会报错**，要等到真正调用才爆——排错更晚、更痛。

ABC 可以在**实例化时就拦住**「抽象方法还没实现」的类。

#### 怎么写

```python
from abc import ABC, abstractmethod


class BaseTool(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self, **kwargs) -> object:
        """执行工具并返回结果。"""


class CalcTool(BaseTool):
    def run(self, expression: str) -> float:
        mapping = {"1+2": 3.0, "10/2": 5.0}
        if expression not in mapping:
            raise ValueError(f"unsupported: {expression}")
        return mapping[expression]
```

#### 跑一下

```python
# BaseTool("x")
# TypeError: Can't instantiate abstract class BaseTool without an implementation for abstract method 'run'

tool = CalcTool("calc")
print(tool.run(expression="1+2"))  # 3.0
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 子类方法名写错（`runs` / `execute`） | 仍被视为抽象类，实例化失败 |
| 签名完全对不上业务约定 | ABC 不替你检查参数名；契约要靠文档/类型注解/测试 |
| 在 ABC 里塞满具体业务 | 变成上帝类；ABC 先保证契约清晰 |

#### JS/TS 对照

| TypeScript | Python |
| --- | --- |
| `abstract class BaseTool { abstract run(...): ... }` | `class BaseTool(ABC):` + `@abstractmethod` |
| `interface Tool { run(...): ... }` | ABC 或后续 `Protocol`（类型系统章） |
| 编译期拦住未实现 | **运行时**实例化时拦住 |

这和 TS 的 `abstract class` / `interface` 很像：先定契约，再写实现。

---

### 4.2 多实现可替换（多态）

#### 为什么需要多态？

Agent 主流程不应该写死「只能调 OpenAI」。  
它应该依赖「能 `complete(prompt)` 的东西」——具体是 Echo、Upper 还是真客户端，由外部决定。

#### 怎么写

```python
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...


class EchoLLM(LLMClient):
    """教学玩具签名。仓库 FakeLLM 以 CONVENTIONS 为准（messages → assistant dict）。"""

    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


class UpperLLM(LLMClient):
    def complete(self, prompt: str) -> str:
        return prompt.upper()


def ask(llm: LLMClient, prompt: str) -> str:
    return llm.complete(prompt)
```

#### 跑一下

```python
print(ask(EchoLLM(), "hi"))   # ECHO: hi
print(ask(UpperLLM(), "hi"))  # HI
```

`ask` 不关心具体是哪个 LLM——这就是后续做「多模型适配层」的雏形。

#### 易错点

- 注解写成 `llm: LLMClient` 是文档 + 类型检查器用；**运行时默认不强制**
- 教学玩具用 `complete(prompt: str)`；真实项目可能是 `messages: list[dict]`——以你们仓库 CONVENTIONS / FakeLLM 为准
- 更现代、更轻的接口方式是 `Protocol`（鸭子类型 + 静态检查），类型系统章会讲；现在先把 ABC 用熟

#### 多态心智图

```text
ask(llm, prompt)
        │
        ▼
   llm.complete(...)
        │
   ┌────┴────┐
EchoLLM   UpperLLM   （以后还可接 OpenAIClient ...）
```

---

## 5. 必掌握：dataclass

### 5.1 用数据类干掉样板代码

#### 为什么需要 dataclass？

手写 Message 时，你会重复写 `__init__`、`__repr__`，字段一多就烦：

```python
# 手写样板（能跑，但啰嗦）
class Message:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def __repr__(self) -> str:
        return f"Message(role={self.role!r}, content={self.content!r})"
```

`dataclass` 自动生成这些样板，特别适合「主要是数据」的对象。

#### 怎么写

```python
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str
    metadata: dict = field(default_factory=dict)
```

#### 跑一下

```python
m = Message(role="user", content="你好")
print(m)
# Message(role='user', content='你好', metadata={})

print(m.metadata)
# {}

m2 = Message("assistant", "嗨", metadata={"model": "echo"})
print(m2.metadata["model"])  # echo
```

适合场景：

- Message / ToolCall / DocumentChunk
- 配置对象
- 函数间传递的结构化数据（DTO）

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 无默认值字段写在有默认值字段后面 | `TypeError`（字段顺序不合法） |
| 忘记 `@dataclass` 装饰器 | 不会自动生成 `__init__` |
| 把复杂生命周期对象也强行 dataclass | 初始化/校验逻辑会别扭——改用普通 class |

#### JS/TS 对照

| TypeScript | Python |
| --- | --- |
| `type Message = { role: string; content: string }` | `@dataclass class Message: ...` |
| `interface` + 手写 class | dataclass 一次搞定数据壳 |
| 通常没有自动 `__repr__` | dataclass 自带友好打印 |

---

### 5.2 可变默认值要用 `field(default_factory=...)`

#### 为什么这一点特别重要？

和函数可变默认参数是同一类坑：默认值如果在「定义时」共享同一个 list/dict，多个实例会踩同一块内存。

#### 怎么写 / 跑一下

```python
from dataclasses import dataclass, field


@dataclass
class AgentState:
    messages: list[dict] = field(default_factory=list)
    step: int = 0


s1 = AgentState()
s2 = AgentState()
s1.messages.append({"role": "user", "content": "hi"})
print(s1.messages)  # [{'role': 'user', 'content': 'hi'}]
print(s2.messages)  # []  ← 互不影响，正确
```

#### 反例纠错

```python
# ❌ 不要这样写（即便有时解释器/类型检查会警告）
@dataclass
class BadState:
    messages: list = []  # 可变默认值陷阱

# ✅ 永远用 default_factory
@dataclass
class GoodState:
    messages: list = field(default_factory=list)
```

#### 易错点

> 不要写 `messages: list = []`，原因与函数可变默认参数相同。  
> `field(default_factory=list)` 的意思是：**每个实例新建自己的 list**。

---

### 5.3 `frozen=True`：只读数据

#### 为什么需要 frozen？

有些对象表示「已经发生的事件」：某次 ToolCall、某条审计日志。  
创建后不应再改字段，避免历史被悄悄篡改。

#### 怎么写 / 跑一下

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


call = ToolCall("search", {"query": "RAG"})
print(call)
# ToolCall(name='search', arguments={'query': 'RAG'})

# call.name = "calc"  →  dataclasses.FrozenInstanceError
```

#### 易错点（浅不可变）

```python
call.arguments["query"] = "改掉了"  # frozen 拦不住！
print(call.arguments)  # {'query': '改掉了'}
```

> `frozen` 防的是**改字段绑定**（不能 `call.name = ...`）；  
> 若字段值本身是 dict/list，仍可能被原地修改。真正不可变需要更谨慎设计（了解即可）。

#### 适用直觉

| 用 `frozen=True` | 保持可变 |
| --- | --- |
| ToolCall、事件、值对象 | AgentState、运行中缓存 |
| 作为 dict key（需可哈希且字段也可哈希） | 频繁更新的累加器 |

---

### 5.4 何时用 dataclass，何时用普通 class？

#### 为什么需要选型？

dataclass 很香，但不是银弹。选错会让代码别扭：要么样板太多，要么行为对象被数据壳绑死。

#### 对照表

| 用 dataclass | 用普通 class |
| --- | --- |
| 主要是数据 + 少量方法 | 有复杂行为 / 生命周期 |
| Message、DTO、配置 | Agent 运行时、连接池封装 |
| 想快速比较 / 打印 | 需要精细控制初始化 |
| 字段列表稳定、偏声明式 | 有较多分支校验、资源管理 |

经验法则：

> **数据壳用 dataclass；行为引擎用普通 class（或 ABC 子类）。**  
> 综合小例子里：`Message` 是 dataclass，`Agent` 也可以是 dataclass（字段简单时），但带连接/线程的客户端通常用普通 class。

---

## 6. 必掌握：`@property`

### 6.1 把方法变成属性访问

#### 为什么需要 `@property`？

有些值是**算出来的**，不是存出来的：预览文本、是否相关、工具名列表……  
你希望调用方写 `chunk.preview`，而不是 `chunk.get_preview()`——读起来像字段，实现仍是方法。

#### 怎么写

```python
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    text: str
    score: float

    @property
    def preview(self) -> str:
        text = self.text.strip()
        return text if len(text) <= 20 else text[:17] + "..."

    @property
    def is_relevant(self) -> bool:
        return self.score >= 0.6
```

#### 跑一下

```python
c = DocumentChunk("LangGraph 适合有状态 Agent 工作流", 0.88)
print(c.preview)
# LangGraph 适合有状态 A...

print(c.is_relevant)
# True

print(c.score)
# 0.88
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 写成 `c.preview()` | `TypeError`：property 不是手写调用的函数 |
| 在 property 里做很重的 I/O | 属性访问看起来很「便宜」，实际很贵——别误导调用方 |
| 既当字段又同名 property 搞混 | 读写路径不清晰；命名要稳定 |

#### JS/TS 对照

```typescript
class DocumentChunk {
  constructor(public text: string, public score: number) {}

  get preview(): string {
    const t = this.text.trim();
    return t.length <= 20 ? t : t.slice(0, 17) + "...";
  }

  get isRelevant(): boolean {
    return this.score >= 0.6;
  }
}
```

Python 的 `@property` ≈ TS/JS 的 `get xxx()`。

---

### 6.2 带 setter：受控写入

#### 为什么需要 setter？

有时外部可以改值，但你想在赋值时做校验（温度不能低于绝对零度、score 必须在 0～1）。

#### 怎么写 / 跑一下

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._celsius = value


t = Temperature(25)
print(t.celsius)  # 25
t.celsius = 36.5
print(t.celsius)  # 36.5
# t.celsius = -300  →  ValueError
```

#### 易错点

- `_celsius` 下划线表示**内部属性**（约定，不是语法强制）；外部优先走 property
- 只读属性：只写 `@property`，不写 setter
- 新手阶段：派生只读视图用 property 即可；setter 会用就行，不必到处上

---

## 7. 建议掌握：常用魔法方法子集

完整数据模型下一章展开；这里先掌握读框架时最常碰的几个。

### 7.1 为什么需要魔法方法？

你希望自己的对象支持：

```python
print(msg)          # 友好展示
len(registry)       # 有多少工具
"search" in registry
tool = registry["search"]
```

这些语法背后，是 Python 去调对象上的特殊方法（dunder methods）。

### 7.2 怎么写 / 跑一下

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


class BaseTool(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self, **kwargs) -> object:
        ...


@dataclass
class Message:
    role: str
    content: str

    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def __getitem__(self, name: str) -> BaseTool:
        return self._tools[name]


class PingTool(BaseTool):
    def run(self, **kwargs) -> str:
        return "pong"


reg = ToolRegistry()
reg.register(PingTool("ping"))
print(len(reg))           # 1
print("ping" in reg)      # True
print(reg["ping"].run())  # pong
print(Message("user", "hi"))  # [user] hi
```

### 7.3 速查表

| 方法 | 触发方式 | 用途 |
| --- | --- | --- |
| `__str__` | `print(obj)` / `str(obj)` | 友好展示 |
| `__repr__` | 调试展示 / 容器里默认展示 | dataclass 通常已生成 |
| `__len__` | `len(obj)` | 容器感 |
| `__contains__` | `x in obj` | 成员检测 |
| `__getitem__` | `obj[key]` | 下标访问 |

### 7.4 易错点

- `__str__` 给人看，`__repr__` 给调试看；两者职责别混
- 不要为了「炫技」实现一堆 dunder；用到再加
- 下一章会系统讲 Python 数据模型；本章够你读很多框架代码了

#### JS 对照直觉

| JavaScript | Python |
| --- | --- |
| `toString()` | `__str__` |
| 没有统一的 `len(obj)` | `__len__` → `len(obj)` |
| `obj[key]` 普通属性/Map | `__getitem__` 可自定义 |

---

## 8. 建议掌握：依赖注入（DI）直觉

依赖注入听起来玄，本质就一句：

> **不要在对象内部 `new` 死依赖；从外面传进来。**

### 8.1 硬编码依赖（难测、难替换）

#### 为什么这是问题？

```python
class Agent:
    def __init__(self) -> None:
        self.llm = OpenAIClient()  # 写死了
```

后果：

- 单测必须联网或 mock 模块内部
- 换模型厂商要改 Agent 源码
- Agent 和具体实现耦合

### 8.2 注入依赖（推荐）

#### 怎么写

```python
class Agent:
    def __init__(self, llm: LLMClient, tools: list[BaseTool]) -> None:
        self.llm = llm
        self.tools = tools
```

#### 跑一下（测试友好）

```python
agent = Agent(llm=EchoLLM(), tools=[CalcTool("calc")])
# 生产环境再换成真实客户端：
# agent = Agent(llm=OpenAIClient(...), tools=[...])
print(type(agent.llm).__name__)  # EchoLLM
```

#### 好处

- 测试时可注入 `EchoLLM`（后期 FakeLLM 见 CONVENTIONS）
- 生产可注入真实客户端
- Agent 本身不关心模型厂商

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 在 `ask()` 里临时 `OpenAIClient()` | 每次调用新建连接/难测 |
| 用全局单例偷偷拿 llm | 隐藏依赖，测试互相污染 |
| 为了 DI 上很重的框架 | 小项目里「构造函数传参」就够 |

#### 前端对照

| 前端常见做法 | Python 对应直觉 |
| --- | --- |
| 组件 props 传入 service | `__init__(self, llm=...)` |
| `provide` / `inject` | 上层组装好再往下传 |
| 构造器注入 | 最常见、也最清晰的 DI |

---

## 9. 了解即可：元类扫盲

#### 为什么只需要扫盲？

元类（metaclass）= 「创建类的类」。  
库作者有时用它做自动注册、ORM 映射、声明式 API 等。

你现在只需要建立地图，不必会写。

#### 心智定位

```text
普通开发：用 class / ABC / dataclass 就够
读源码时看到 metaclass=...：先当「高级钩子」，别卡主线
几乎很少需要自己写元类
现代替代：装饰器、ABC、`__init_subclass__`、dataclass 等往往更直观
```

#### 见到时怎么读？

1. 先看这个类**对外提供什么 API**
2. 再问：元类是不是在做「注册到全局表 / 改类属性」
3. 不要一上来追进元类实现细节

本路线后续不把元类当必选项。

---

## 10. 常见坑（建议收藏）

### 10.1 忘记 `self`

```python
class Bad:
    def inc(step=1):  # 少了 self
        ...
```

实例方法第一个参数必须是 `self`（名字理论上可改，但**别改**）。  
报错长这样：`TypeError: Bad.inc() takes 0 positional arguments but 1 was given`——那个多出来的 1 就是实例自己。

### 10.2 可变类属性当共享状态

```python
class A:
    items = []

    def add(self, x):
        self.items.append(x)
```

`self.items.append(...)` 可能污染所有实例。  
修复：在 `__init__` 里 `self.items = []`，或 dataclass 的 `field(default_factory=list)`。

### 10.3 继承过深

超过两层就要警惕；优先组合。  
问自己：我是在表达稳定的 is-a，还是只是想少写两行代码？

### 10.4 在抽象类里写太多具体逻辑

ABC 先保证契约清晰；公共默认实现可以有，但不要变成上帝类。  
「所有 Agent 行为都塞进 BaseAgent」是常见翻车点。

### 10.5 dataclass 字段顺序

无默认值字段必须在有默认值字段之前：

```python
@dataclass
class Ok:
    role: str
    content: str = ""

# @dataclass
# class Bad:
#     content: str = ""
#     role: str        # TypeError
```

### 10.6 把所有 dict 都改成 class

边界校验、长期演化的领域概念值得 class；  
临时 JSON 传递、第三方 API 原始响应，保持 dict 往往更好。

自检三问：

1. 这个概念会跨多个模块长期存在吗？→ 倾向 class / dataclass  
2. 只是管道里的一次性数据吗？→ 倾向 dict  
3. 需要可替换实现吗？→ 上 ABC（或后续 Protocol）

---

## 11. 综合小例子：可替换 LLM 的小 Agent

把本章知识点串起来——很像最小可用的 Agent 骨架。

### 11.1 完整代码

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str

    def as_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...


class EchoLLM(LLMClient):
    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


class BaseTool(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self, **kwargs) -> object:
        ...


class SearchTool(BaseTool):
    def run(self, query: str, top_k: int = 2) -> list[str]:
        return [f"doc:{query}:{i}" for i in range(top_k)]


@dataclass
class Agent:
    llm: LLMClient
    tools: list[BaseTool] = field(default_factory=list)
    history: list[Message] = field(default_factory=list)

    @property
    def tool_names(self) -> list[str]:
        return [t.name for t in self.tools]

    def ask(self, content: str) -> str:
        self.history.append(Message("user", content))
        # 假装先检索再回答
        search = next(t for t in self.tools if t.name == "search")
        docs = search.run(query=content)
        prompt = f"q={content}; docs={docs}"
        answer = self.llm.complete(prompt)
        self.history.append(Message("assistant", answer))
        return answer


agent = Agent(llm=EchoLLM(), tools=[SearchTool("search")])
print(agent.tool_names)
print(agent.ask("what is RAG"))
print(agent.history)
```

### 11.2 跑一下（预期输出）

```text
['search']
ECHO: q=what is RAG; docs=['doc:what is RAG:0', 'doc:what is RAG:1']
[Message(role='user', content='what is RAG'), Message(role='assistant', content="ECHO: q=what is RAG; docs=['doc:what is RAG:0', 'doc:what is RAG:1']")]
```

### 11.3 这里用到了什么？

```text
dataclass Message / Agent
  → ABC：LLMClient、BaseTool
  → 继承：SearchTool(BaseTool)、EchoLLM(LLMClient)
  → 组合：Agent 拥有 llm + tools + history
  → property：tool_names
  → 依赖注入：构造时传入 EchoLLM / SearchTool
  → field(default_factory=...)：避免可变默认值坑
```

### 11.4 你可以怎么改着玩？

1. 再写一个 `UpperLLM`，只改构造注入，不改 `Agent.ask`
2. 给 `Message` 加 `@property preview`
3. 抽一个 `ToolRegistry`，用 `__getitem__` / `__contains__` 管理工具

---

## 12. 练习指引

请打开并完成：

[`exercises/02-advanced-python/01-oop.md`](../../exercises/02-advanced-python/01-oop.md)

建议代码位置：

```text
playground/02-advanced-python/01-oop/
```

建议路径：

1. 先把 class / `self` / 实例属性写顺
2. 再做 ABC + 可替换 LLM/Tool
3. 用 dataclass + property 表达 Message / Chunk
4. 有余力：组合一个小 Agent，练习依赖注入

先按自己的理解写出来即可；尤其是「继承 vs 组合」和「可变默认值」，写错一次往往比只看文档记得更牢。

---

## 13. 小结与下一站

### 你现在应该掌握的心智模型

```text
数据用 dataclass（或 dict）
契约用 ABC（或后续 Protocol）
行为对象用 class
系统拼装用组合 + 依赖注入
继承只服务「稳定的 is-a」
```

### 自检清单

- [ ] 能写出带 `__init__` / 方法的 class，并说清 `self`
- [ ] 能举例说明继承与组合在 Agent 中的取舍
- [ ] 能用 ABC + 子类实现可替换 LLM/Tool
- [ ] 能用 dataclass 与 property 表达 Message/Chunk，并避开可变默认值坑
- [ ] 知道常用 dunder（`__str__` / `__len__` / `__getitem__`）在读代码时的含义
- [ ] 独立完成练习基础题

### 下一章

[`02-data-model.md`](./02-data-model.md) —— Python 数据模型：对象协议与更多 dunder 方法，帮你读懂「为什么 `in` / `len` / 可调用对象能工作」。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 下一章：[Python 数据模型](./02-data-model.md)
