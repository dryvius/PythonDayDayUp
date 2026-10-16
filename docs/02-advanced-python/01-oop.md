# 面向对象编程

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：4～7 小时（有 JS/TS class 经验可更快）  
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
|------|------|----------|
| **必掌握** | class / 继承 / 组合、ABC、dataclass、property | 能写、能讲、能做题 |
| **建议掌握** | 常用魔法方法子集、依赖注入直觉 | 会读、会用简单模式 |
| **了解即可** | 元类扫盲 | 只建地图，不深挖 |

---

## 1. 为什么要学（和 Agent 有什么关系）

函数很适合「无长期状态的变换」；但 Agent 系统里大量东西是**带状态、可替换、可配置**的：

```text
LLM Client（不同厂商可替换）
Tool（search / calc / browse）
Memory（短期 / 长期）
Agent（持有 llm + tools + memory，循环调用）
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

本章不是要你背 OO 教条，而是让你能：

1. **读懂**这类抽象
2. **自己写出**可扩展的小结构
3. **避免**一上来就堆很深的继承树

---

## 2. 必掌握：class 基础

### 2.1 最小 class

```python
class Counter:
    def __init__(self, start: int = 0) -> None:
        self.value = start

    def inc(self, step: int = 1) -> int:
        self.value += step
        return self.value


c = Counter(10)
print(c.inc())   # 11
print(c.value)   # 11
```

要点：

- `__init__` 是构造时的初始化方法（不是 JS constructor 关键字，但角色类似）
- `self` 是实例自己（类似 TS/JS 的 `this`，但 Python **必须显式写在方法第一个参数**）
- 实例属性通常在 `__init__` 里挂到 `self.xxx`

和 TS 对照：

| TypeScript | Python |
|------------|--------|
| `constructor(private value = 0) {}` | `__init__(self, start=0): self.value = start` |
| `this.value` | `self.value` |
| `new Counter(10)` | `Counter(10)`（一般不写 new） |

### 2.2 方法、属性、为什么要对象

```python
class ChatMessage:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def as_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


m = ChatMessage("user", "你好")
print(m.as_dict())
```

当数据和行为经常一起出现时，用对象比「一堆松散 dict + 外部函数」更稳。  
但也不要硬对象化：简单数据传递用 `dict` / `dataclass` 往往更干净。

### 2.3 类属性 vs 实例属性

```python
class LLMClient:
    default_timeout = 30.0  # 类属性：大家共享默认值

    def __init__(self, model: str) -> None:
        self.model = model  # 实例属性：每个对象各自一份
```

修改 `LLMClient.default_timeout` 会影响还没覆盖该属性的实例的查找结果；新手阶段：**状态优先放实例属性**。

---

## 3. 必掌握：继承 vs 组合

### 3.1 继承：is-a（是一种）

```python
class Tool:
    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, **kwargs):
        raise NotImplementedError


class SearchTool(Tool):
    def run(self, query: str, top_k: int = 3) -> list[str]:
        return [f"{query}#{i}" for i in range(top_k)]
```

`SearchTool` **是一种** `Tool`。适合：共享少量基础行为，子类差异明确。

### 3.2 组合：has-a（拥有）

```python
class Agent:
    def __init__(self, llm: "LLMClient", tools: list[Tool]) -> None:
        self.llm = llm          # 拥有一个 llm
        self.tools = tools      # 拥有一组 tools

    def available_tool_names(self) -> list[str]:
        return [t.name for t in self.tools]
```

`Agent` **拥有** LLM 和 Tools，而不是去继承某个巨大的 `BaseEverything`。

### 3.3 Agent 场景怎么选？

| 更适合继承 | 更适合组合 |
|------------|------------|
| 多种 Tool 共享同一接口骨架 | Agent 组装 llm/tools/memory |
| 少量层级（1～2 层） | 可替换依赖、可测试 |
| 「是一种」关系非常稳定 | 「拥有并协作」关系 |

经验法则：

> **默认组合；继承只用于稳定的接口族。**  
> 继承树一深，框架代码就会变得难读难测——这正是很多 Agent demo 后期翻车的原因。

### 3.4 `super()`

子类要复用父类初始化时：

```python
class NamedTool(Tool):
    def __init__(self, name: str, description: str) -> None:
        super().__init__(name)
        self.description = description
```

---

## 4. 必掌握：抽象基类（ABC）

### 4.1 为什么需要 ABC？

只靠约定「子类请实现 `run`」很容易忘。ABC 可以**在实例化时就拦住**：

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


# BaseTool("x")  →  TypeError: Can't instantiate abstract class...
tool = CalcTool("calc")
print(tool.run(expression="1+2"))
```

这和 TS 的 `abstract class` / `interface` 很像：先定契约，再写实现。

### 4.2 多实现可替换（多态）

```python
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


print(ask(EchoLLM(), "hi"))
print(ask(UpperLLM(), "hi"))
```

`ask` 不关心具体是哪个 LLM——这就是后续做「多模型适配层」的雏形。  
（更现代、更轻的接口方式是 `Protocol`，类型系统章会讲；现在先把 ABC 用熟。）

---

## 5. 必掌握：dataclass

### 5.1 用数据类干掉样板代码

```python
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str
    metadata: dict = field(default_factory=dict)


m = Message(role="user", content="你好")
print(m)
print(m.metadata)
```

`dataclass` 会自动生成 `__init__` / `__repr__` 等，特别适合：

- Message / ToolCall / DocumentChunk
- 配置对象
- 作为函数间传递的结构化数据

### 5.2 可变默认值要用 `field(default_factory=...)`

```python
@dataclass
class AgentState:
    messages: list[dict] = field(default_factory=list)
    step: int = 0
```

不要写 `messages: list = []`，原因与函数可变默认参数相同。

### 5.3 `frozen=True`：只读数据

```python
@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict
```

创建后不能改字段，适合表示「已经发生的事件」。  
注意：`frozen` 防的是改字段绑定；若 `arguments` 本身是 dict，仍可能被原地修改内部键值。真正不可变需要更谨慎的设计（了解即可）。

### 5.4 何时用 dataclass，何时用普通 class？

| 用 dataclass | 用普通 class |
|--------------|--------------|
| 主要是数据 + 少量方法 | 有复杂行为 / 生命周期 |
| Message、DTO、配置 | Agent 运行时、连接池封装 |
| 想快速比较/打印 | 需要精细控制初始化 |

---

## 6. 必掌握：`@property`

把「方法」变成「属性访问」，适合派生值或只读视图：

```python
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


c = DocumentChunk("LangGraph 适合有状态 Agent 工作流", 0.88)
print(c.preview)
print(c.is_relevant)
```

带 setter 的例子（了解用法即可）：

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
```

约定：`_celsius` 下划线表示内部属性，外部优先走 property。

---

## 7. 建议掌握：常用魔法方法子集

完整数据模型下一章展开；这里先掌握最常碰的几个。

```python
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
```

| 方法 | 触发方式 | 用途 |
|------|----------|------|
| `__str__` | `print(obj)` / `str(obj)` | 友好展示 |
| `__repr__` | 调试展示 | dataclass 通常已生成 |
| `__len__` | `len(obj)` | 容器感 |
| `__contains__` | `x in obj` | 成员检测 |
| `__getitem__` | `obj[key]` | 下标访问 |

下一章会系统讲 Python 数据模型；本章够你读很多框架代码了。

---

## 8. 建议掌握：依赖注入（DI）直觉

依赖注入听起来玄，本质就一句：

> **不要在对象内部 `new` 死依赖；从外面传进来。**

### 8.1 硬编码依赖（难测、难替换）

```python
class Agent:
    def __init__(self) -> None:
        self.llm = OpenAIClient()  # 写死了
```

### 8.2 注入依赖（推荐）

```python
class Agent:
    def __init__(self, llm: LLMClient, tools: list[BaseTool]) -> None:
        self.llm = llm
        self.tools = tools
```

好处：

- 测试时可注入 `EchoLLM`（后期 FakeLLM 见 CONVENTIONS）
- 生产可注入真实客户端
- Agent 本身不关心模型厂商

前端里你见过的 props / provide-inject / 构造器注入，就是同一思想。

---

## 9. 了解即可：元类扫盲

元类（metaclass）= 「创建类的类」。  
库作者有时用它做自动注册、ORM 映射等。

你现在只需要知道：

```text
普通开发：用 class / ABC / dataclass 就够
读源码时看到 metaclass=...：先当「高级钩子」，别卡主线
几乎很少需要自己写元类
```

本路线后续不把元类当必选项。

---

## 10. 常见坑

1. **忘记 `self`**  
   实例方法第一个参数必须是 `self`（名字可改但别改）。

2. **可变类属性当共享状态**  
   `class A: items = []` 然后 `self.items.append(...)` 可能污染所有实例。

3. **继承过深**  
   超过两层就要警惕；优先组合。

4. **在抽象类里写太多具体逻辑**  
   ABC 先保证契约清晰；公共默认实现可以有，但不要变成上帝类。

5. **dataclass 字段顺序**  
   无默认值字段必须在有默认值字段之前。

6. **把所有 dict 都改成 class**  
   边界校验、长期演化的领域概念值得 class；临时 JSON 传递保持 dict 往往更好。

---

## 11. 综合小例子：可替换 LLM 的小 Agent

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

这里覆盖了：ABC、继承、组合、dataclass、property、依赖注入。

---

## 12. 练习指引

请打开并完成：

[`exercises/02-advanced-python/01-oop.md`](../../exercises/02-advanced-python/01-oop.md)

建议代码位置：

```text
playground/02-advanced-python/01-oop/
```

---

## 13. 小结与下一站

### 心智模型

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
- [ ] 能用 dataclass 与 property 表达 Message/Chunk
- [ ] 独立完成练习基础题

### 下一章

[`02-data-model.md`](./02-data-model.md) —— Python 数据模型：对象协议与更多 dunder 方法，帮你读懂「为什么 `in` / `len` / 可调用对象能工作」。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 下一章：[Python 数据模型](./02-data-model.md)
