# 练习：面向对象编程

> 对应文档：[`docs/02-advanced-python/01-oop.md`](../../docs/02-advanced-python/01-oop.md)  
> 状态：`已完成出题`  
> 建议用时：80～110 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先摸清 `self`、实例属性、简单继承，再上 Agent 相关类设计。
4. 建议代码目录：

```text
playground/02-advanced-python/01-oop/
```

5. 优先把类写在模块文件里，再用 `*_main.py` 演示；先做题再看文末答案。

---

## 热身题（建议先做）

### W1. 最小 class：`Point`

**要求**：实现 `Point`，`__init__(self, x: int, y: int)`，提供方法 `as_tuple(self) -> tuple[int, int]`。

**验收**：

```python
p = Point(3, 4)
assert p.as_tuple() == (3, 4)
```

---

### W2. 实例方法改状态

**要求**：实现 `Counter`，`inc()` 使内部计数 +1，`value` 属性（或方法）可读当前值。

**验收**：

```python
c = Counter()
c.inc(); c.inc()
assert c.value == 2  # 若用方法则 assert c.value() == 2
```

---

### W3. 继承覆盖方法

**要求**：基类 `Greeter.hello()` 返回 `"hi"`；子类 `LoudGreeter.hello()` 返回 `"HI"`。

**验收**：`LoudGreeter().hello() == "HI"` 且仍是 `Greeter` 的实例（`isinstance`）。

---

### W4. dataclass 一分钟

**要求**：用 `@dataclass` 定义 `Msg(role: str, content: str)`，构造一条 user 消息。

**验收**：`Msg("user", "hi").content == "hi"`。

---

## 基础题（必做）

### B1. class 基础：会话历史

实现 `ChatHistory`：

```python
class ChatHistory:
    def __init__(self) -> None: ...
    def add(self, role: str, content: str) -> None: ...
    def last(self, n: int = 1) -> list[dict]: ...
    def as_list(self) -> list[dict]: ...
    def __len__(self) -> int: ...
```

**要求**：

1. 内部用 list 存 `{"role", "content"}`
2. `add` 时对 `content` 做 `strip`；空内容拒绝（`ValueError`）
3. `last(n)` 返回最后 n 条的**拷贝**（改返回值不应影响内部）
4. `as_list()` 同样返回拷贝

**验收**：连续 add 3 条后 `len(history) == 3`；改 `history.last(1)[0]["content"]` 不影响内部。

---

### B2. 继承 + 组合：Tool 与 Agent

1. 写基类 `Tool`（普通类即可），含 `name` 与 `run(**kwargs)`（基类可 `raise NotImplementedError`）
2. 实现两个子类：
   - `SearchTool`：`run(query: str, top_k: int = 3) -> list[str]`
   - `CalcTool`：`run(expression: str) -> float`（可用小字典模拟）
3. 写 `SimpleAgent`（组合）：
   - `__init__(self, tools: list[Tool])`
   - `get_tool(self, name: str) -> Tool`（找不到报错）
   - `call(self, name: str, **kwargs) -> object`

**验收**：能调用 search/calc；调用未知工具抛清晰异常。

---

### B3. ABC：可替换 LLM

```python
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str: ...
```

实现：

1. `EchoLLM`：返回 `"ECHO: " + prompt`（教学用 Echo，**不要**命名为 FakeLLM）
2. `ReverseLLM`：返回反转后的 prompt
3. 函数 `run_prompt(llm: LLMClient, prompt: str) -> str` 只依赖抽象类型
4. 尝试直接 `LLMClient()`，确认会失败（把报错类型/关键信息写在注释里）

**验收**：同一 `run_prompt` 换两种 LLM 都能工作；抽象类不可实例化。

---

### B4. dataclass + property

```python
from dataclasses import dataclass, field

@dataclass
class DocumentChunk:
    text: str
    score: float
    source: str = "unknown"
    tags: list[str] = field(default_factory=list)

    @property
    def preview(self) -> str: ...

    @property
    def is_relevant(self) -> bool: ...
```

**要求**：

1. `preview`：strip 后长度 > 30 则截断到 27 字符 + `...`
2. `is_relevant`：`score >= 0.6`
3. 再写 `@dataclass` 的 `RagResult(chunks: list[DocumentChunk])`，提供 property `relevant_chunks`

**验收**：自己构造 3 个 chunk，打印 preview / relevant_chunks 符合预期；`tags` 默认值互不污染。

---

## 进阶题（建议至少做 1 题）

### A1. 组合优于继承：重构坏味道

下面是一个「坏设计」草稿（可抄到文件再改）：

```python
class OpenAISearchAgent:
    def ask(self, q: str) -> str:
        # 内部写死 OpenAI + Search，无法替换
        return f"openai+search:{q}"
```

请重构为：

- `LLMClient` 抽象 + 至少一个实现（可用 `EchoLLM`）
- `Tool` 抽象/基类 + `SearchTool`
- `Agent` 通过构造函数注入 `llm` 与 `tools`

并写一段 demo：用注入对象跑通。

**验收**：不改 Agent 类体，只换注入对象，就能改变行为。

---

### A2. ToolRegistry 魔法方法

实现 `ToolRegistry`：

- `register(tool)`
- `names()` / `__len__` / `__contains__` / `__getitem__`
- `run(name, **kwargs)` 调用对应工具

**验收**：`"search" in registry`、`registry["search"]`、`len(registry)` 都能用。

---

## 挑战题（可选）

### C1. 迷你 Agent Runtime（OOP 版）

综合实现：

```text
Message (dataclass)
LLMClient (ABC)
BaseTool (ABC) + SearchTool + CalcTool
Agent
  - history: list[Message]
  - ask(user_input) -> str
  - 规则（刻意简化）：
      1) 先用 search 工具取 docs
      2) 拼 prompt 调 llm
      3) 把 user/assistant 消息写入 history
  - property: step_count（assistant 消息数）
```

额外加分：

- `Agent` 不在内部写死具体 LLM 类
- 提供 `as_transcript() -> str`，把 history 格式化成可读文本

**验收**：换 `EchoLLM` / 另一个实现，脚本都能跑；history 长度随对话增长。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成
- [ ] 能口述：继承 vs 组合；ABC 解决什么问题；dataclass 何时用
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）完成 C1

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。

### W1 参考答案

```python
class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def as_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


p = Point(3, 4)
assert p.as_tuple() == (3, 4)
```

### W2 参考答案

```python
class Counter:
    def __init__(self) -> None:
        self._value = 0

    def inc(self) -> None:
        self._value += 1

    @property
    def value(self) -> int:
        return self._value


c = Counter()
c.inc()
c.inc()
assert c.value == 2
```

### W3 参考答案

```python
class Greeter:
    def hello(self) -> str:
        return "hi"


class LoudGreeter(Greeter):
    def hello(self) -> str:
        return "HI"


g = LoudGreeter()
assert g.hello() == "HI"
assert isinstance(g, Greeter)
```

### W4 参考答案

```python
from dataclasses import dataclass


@dataclass
class Msg:
    role: str
    content: str


assert Msg("user", "hi").content == "hi"
```

### B1 思路 + 参考答案

**思路**

1. 内部 list 存消息；对外返回时做浅拷贝，避免调用方改到内部状态。
2. `add` 先 `strip` 再判空。
3. `__len__` 让 `len(history)` 可用。

**参考答案**

```python
class ChatHistory:
    def __init__(self) -> None:
        self._items: list[dict] = []

    def add(self, role: str, content: str) -> None:
        cleaned = content.strip()
        if not cleaned:
            raise ValueError("content empty")
        self._items.append({"role": role, "content": cleaned})

    def last(self, n: int = 1) -> list[dict]:
        # 每条 dict 再拷贝一层，避免改 content 影响内部
        return [dict(m) for m in self._items[-n:]]

    def as_list(self) -> list[dict]:
        return [dict(m) for m in self._items]

    def __len__(self) -> int:
        return len(self._items)


history = ChatHistory()
history.add("system", "You are helpful.")
history.add("user", "  hi  ")
history.add("assistant", "hello")
assert len(history) == 3

stolen = history.last(1)
stolen[0]["content"] = "hacked"
assert history.as_list()[-1]["content"] == "hello"  # 内部未变

try:
    history.add("user", "   ")
    raise AssertionError("should have raised")
except ValueError:
    pass
```

### B2 思路 + 参考答案

**思路**

1. 基类约定接口；子类实现具体工具（Agent 工具调用的 OOP 影子）。
2. `SimpleAgent` **组合** tools，而不是继承某个具体 Tool。
3. 内部用 `name -> tool` 字典查找。

**参考答案**

```python
class Tool:
    name: str

    def run(self, **kwargs: object) -> object:
        raise NotImplementedError


class SearchTool(Tool):
    name = "search"

    def run(self, **kwargs: object) -> list[str]:
        query = str(kwargs.get("query", ""))
        top_k = int(kwargs.get("top_k", 3))
        return [f"doc:{query}:{i}" for i in range(top_k)]


class CalcTool(Tool):
    name = "calc"

    def run(self, **kwargs: object) -> float:
        expression = str(kwargs.get("expression", ""))
        table = {"1+2": 3.0, "10/2": 5.0}
        if expression not in table:
            raise ValueError(f"unsupported: {expression!r}")
        return table[expression]


class SimpleAgent:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {t.name: t for t in tools}

    def get_tool(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]

    def call(self, name: str, **kwargs: object) -> object:
        return self.get_tool(name).run(**kwargs)


agent = SimpleAgent([SearchTool(), CalcTool()])
assert agent.call("search", query="RAG", top_k=2) == ["doc:RAG:0", "doc:RAG:1"]
assert agent.call("calc", expression="1+2") == 3.0
try:
    agent.call("browse")
    raise AssertionError("should have raised")
except KeyError:
    pass
```

### B3 思路 + 参考答案

**思路**

1. ABC + `@abstractmethod` 强制子类实现 `complete`。
2. `run_prompt` 只依赖抽象类型 → 可替换实现（Agent 里换模型同理）。
3. 直接实例化抽象类会 `TypeError`。

**参考答案**

```python
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...


class EchoLLM(LLMClient):
    def complete(self, prompt: str) -> str:
        return "ECHO: " + prompt


class ReverseLLM(LLMClient):
    def complete(self, prompt: str) -> str:
        return prompt[::-1]


def run_prompt(llm: LLMClient, prompt: str) -> str:
    return llm.complete(prompt)


assert run_prompt(EchoLLM(), "hi") == "ECHO: hi"
assert run_prompt(ReverseLLM(), "ab") == "ba"

# 期望：Can't instantiate abstract class LLMClient...
try:
    LLMClient()  # type: ignore[abstract]
    raise AssertionError("should have raised")
except TypeError as exc:
    # 把关键信息留在注释/打印里即可
    print("expected TypeError:", exc)
```

### B4 思路 + 参考答案

**思路**

1. `tags` 必须 `field(default_factory=list)`，否则多实例共享同一 list。
2. `preview` / `is_relevant` 用 `@property` 暴露只读计算字段。
3. `RagResult.relevant_chunks` 过滤 `is_relevant`。

**参考答案**

```python
from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    text: str
    score: float
    source: str = "unknown"
    tags: list[str] = field(default_factory=list)

    @property
    def preview(self) -> str:
        s = self.text.strip()
        if len(s) > 30:
            return s[:27] + "..."
        return s

    @property
    def is_relevant(self) -> bool:
        return self.score >= 0.6


@dataclass
class RagResult:
    chunks: list[DocumentChunk]

    @property
    def relevant_chunks(self) -> list[DocumentChunk]:
        return [c for c in self.chunks if c.is_relevant]


a = DocumentChunk("短文本", 0.9)
b = DocumentChunk("x" * 40, 0.5)
c = DocumentChunk("RAG 很有用", 0.7, tags=["rag"])
a.tags.append("a")
assert b.tags == []  # 不共享
assert a.preview == "短文本"
assert b.preview.endswith("...")
assert len(b.preview) == 30
result = RagResult([a, b, c])
assert [x.text for x in result.relevant_chunks] == ["短文本", "RAG 很有用"]
```

### A1 思路 + 参考答案

**思路**

1. 把「创建依赖」从类内部挪到构造参数（组合注入）。
2. 测试时注入 Echo / 假 Tool，断言行为变化。
3. Agent 类体不写死具体供应商。

**参考答案**

```python
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str: ...


class EchoLLM(LLMClient):
    def complete(self, prompt: str) -> str:
        return "ECHO: " + prompt


class Tool(ABC):
    name: str

    @abstractmethod
    def run(self, **kwargs: object) -> object: ...


class SearchTool(Tool):
    name = "search"

    def run(self, **kwargs: object) -> list[str]:
        q = str(kwargs.get("query", ""))
        return [f"hit:{q}"]


class Agent:
    def __init__(self, llm: LLMClient, tools: list[Tool]) -> None:
        self.llm = llm
        self.tools = {t.name: t for t in tools}

    def ask(self, q: str) -> str:
        docs = self.tools["search"].run(query=q)
        prompt = f"q={q}; docs={docs}"
        return self.llm.complete(prompt)


agent = Agent(EchoLLM(), [SearchTool()])
out = agent.ask("RAG")
assert out.startswith("ECHO:")
assert "hit:RAG" in out

# 换 LLM 不改 Agent 类体
class UpperLLM(LLMClient):
    def complete(self, prompt: str) -> str:
        return prompt.upper()


agent2 = Agent(UpperLLM(), [SearchTool()])
assert "HIT:RAG" in agent2.ask("RAG")
```

### A2 思路 + 参考答案

**思路**

1. 内部 `dict[str, Tool]`；`__getitem__` 找不到抛 `KeyError`。
2. `__contains__` / `__len__` 让 `in` 与 `len` 自然可用。

**参考答案**

```python
class Tool:
    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, **kwargs: object) -> object:
        return {"name": self.name, "kwargs": kwargs}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __getitem__(self, name: str) -> Tool:
        return self._tools[name]

    def run(self, name: str, **kwargs: object) -> object:
        return self[name].run(**kwargs)


reg = ToolRegistry()
reg.register(Tool("search"))
reg.register(Tool("calc"))
assert len(reg) == 2
assert "search" in reg
assert reg["search"].name == "search"
assert reg.run("calc", expression="1+2")["kwargs"]["expression"] == "1+2"
```

### C1 思路 + 参考答案

**思路**

1. Message / Tool / LLM 分层；Agent 只编排。
2. `ask`：search → 拼 prompt → llm.complete → 写 history。
3. `step_count` 统计 assistant 条数。

**参考答案**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str: ...


class EchoLLM(LLMClient):
    def complete(self, prompt: str) -> str:
        return "ECHO: " + prompt


class BaseTool(ABC):
    name: str

    @abstractmethod
    def run(self, **kwargs: object) -> object: ...


class SearchTool(BaseTool):
    name = "search"

    def run(self, **kwargs: object) -> list[str]:
        q = str(kwargs.get("query", ""))
        return [f"doc:{q}:0", f"doc:{q}:1"]


class CalcTool(BaseTool):
    name = "calc"

    def run(self, **kwargs: object) -> float:
        return 3.0


class Agent:
    def __init__(self, llm: LLMClient, tools: list[BaseTool]) -> None:
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.history: list[Message] = []

    def ask(self, user_input: str) -> str:
        docs = self.tools["search"].run(query=user_input)
        prompt = f"User: {user_input}\nDocs: {docs}"
        answer = self.llm.complete(prompt)
        self.history.append(Message("user", user_input))
        self.history.append(Message("assistant", answer))
        return answer

    @property
    def step_count(self) -> int:
        return sum(1 for m in self.history if m.role == "assistant")

    def as_transcript(self) -> str:
        return "\n".join(f"[{m.role}] {m.content}" for m in self.history)


agent = Agent(EchoLLM(), [SearchTool(), CalcTool()])
ans = agent.ask("什么是 RAG？")
assert ans.startswith("ECHO:")
assert len(agent.history) == 2
assert agent.step_count == 1
print(agent.as_transcript())
```
