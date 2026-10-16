# 类型系统

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/02-advanced-python/07-typing-system.md`](../../exercises/02-advanced-python/07-typing-system.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：用类型注解把「约定」写清楚——尤其是 Message、Tool、LLM Client、Generic Repository 这类 Agent 核心抽象。
- **重要事实**：注解**默认不在运行时强制检查**；要靠 Pyright / mypy 等工具在开发期发挥作用。

## 学习目标（学完应能做到）

1. 给函数/变量写清楚的类型注解（含 `list[str]`、`dict[str, int]`）。
2. 正确使用 `|` / `Optional` / `Literal` / `TypedDict`。
3. 用 `Protocol` 描述「鸭子类型接口」，用 `Generic` 写可复用容器/仓储抽象。
4. 知道如何用类型检查器做基本校验；不陷入类型体操。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 类型注解、Optional/Union/Literal、TypedDict、Protocol、Generic | 能读框架、能为自己的 Agent 代码标注 |
| **建议掌握** | TypeVar、pyright/mypy 基础 | 会跑检查、会写简单泛型函数 |
| **了解即可** | 类型体操进阶 | 见到不慌，不主动炫技 |

---

## 1. 为什么要学（和 Agent 有什么关系）

Agent 框架源码里到处是：

```python
class LLM(Protocol):
    async def generate(self, prompt: str) -> str: ...

def run_agent(llm: LLM, tools: list[Tool]) -> AgentResult:
    ...
```

收益：

1. **可读**：函数输入输出一目了然
2. **可换实现**：`Protocol` / ABC 让 FakeLLM 与真 LLM 可替换
3. **少一类 bug**：把 `None`、错误字段名、工具参数结构问题提前暴露
4. **更好的编辑器补全**：前端 TS 用户会非常有熟悉感

和 TypeScript 的粗对照：

| TypeScript | Python typing |
|------------|---------------|
| `string \| null` | `str \| None` |
| `interface` | `Protocol` / `TypedDict` |
| `generics <T>` | `Generic[T]` / `TypeVar` |
| 编译期检查 | Pyright/mypy 静态检查（运行时默认不查） |

---

## 2. 必掌握：类型注解基础

### 2.1 函数注解

```python
def create_message(role: str, content: str) -> dict[str, str]:
    return {"role": role, "content": content}


def clip(text: str, max_len: int = 20) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
```

### 2.2 常见容器

```python
names: list[str] = ["search", "calc"]
scores: dict[str, float] = {"search": 0.9}
pair: tuple[str, int] = ("page", 1)
unique: set[str] = {"a", "b"}
```

Python 3.9+ 可直接用内置类型做泛型；老代码里常见 `from typing import List, Dict`。

### 2.3 变量注解与逐步标注策略

```python
messages: list[dict[str, str]] = []
result: str | None = None
```

落地建议（避免一开始就全项目炫技）：

1. 先标**公共函数边界**
2. 再标**核心数据结构**
3. 内部小函数可以后补

---

## 3. 必掌握：`Optional` / `Union` / `Literal`

### 3.1 可空：`str | None`

```python
def normalize(content: str | None) -> str | None:
    if content is None:
        return None
    text = content.strip()
    return text or None
```

等价老写法：`Optional[str]`（即 `Union[str, None]`）。

**关键习惯**：标了 `| None` 就要在使用前收窄（`if x is None`），类型检查器才会认可后续当 `str` 用。

### 3.2 联合类型：`Union` / `|`

```python
Id = int | str

def as_str_id(value: Id) -> str:
    return str(value)
```

### 3.3 `Literal`：限定有限取值

```python
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]


def create_message(role: Role, content: str) -> dict[str, str]:
    return {"role": role, "content": content}


create_message("user", "hi")
# create_message("admin", "hi")  # 类型检查器应报警
```

Agent 里非常适合：`role`、工具名枚举、模式开关（`"json" | "text"`）。

---

## 4. 必掌握：`TypedDict`

当你还在用 `dict`，但想描述固定字段结构时：

```python
from typing import TypedDict, NotRequired


class MessageDict(TypedDict):
    role: str
    content: str
    name: NotRequired[str]


def last_content(messages: list[MessageDict]) -> str | None:
    if not messages:
        return None
    return messages[-1]["content"]
```

和 `@dataclass` 怎么选：

| 更用 TypedDict | 更用 dataclass |
|----------------|----------------|
| 本来就是 JSON/dict 形态 | 需要方法/行为 |
| 与外部 API 载荷对齐 | 领域对象更丰富 |
| 轻量标注现有 dict | 想要运行时对象 |

两者常同时存在：边界用 TypedDict，内部用 dataclass。

---

## 5. 必掌握：`Protocol`（结构化接口）

### 5.1 为什么不用死继承？

你希望任何「长得像 LLM」的对象都能传入，而不强制继承某个基类：

```python
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class EchoLLM:
    """教学用玩具签名。仓库 FakeLLM 契约见 CONVENTIONS（messages → assistant dict）。"""

    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


def ask(llm: LLMClient, prompt: str) -> str:
    return llm.complete(prompt)


print(ask(EchoLLM(), "hi"))
```

`EchoLLM` **没有继承** `LLMClient`，但只要方法签名匹配，类型检查就通过。  
这叫结构化定型（structural typing），和 TS 的 interface 很像。

> 命名提醒：早期章用 `EchoLLM` 演示 Protocol；模块 09 起的 **FakeLLM** 必须遵守 `complete(messages, tools=None) -> assistant_message`。

### 5.2 对比 ABC

| ABC | Protocol |
|-----|----------|
| 运行时也可拦（不能实例化抽象类） | 更偏静态检查 |
| 需要显式继承 | 不必继承，有匹配方法即可 |
| 适合强制实现 | 适合解耦、插件、鸭子类型 |

Agent 框架两者都常见：学会认即可；新代码里描述「能力接口」优先想到 Protocol。

---

## 6. 必掌握：`Generic` 基础

### 6.1 泛型类

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class Response(Generic[T]):
    def __init__(self, data: T, ok: bool = True) -> None:
        self.data = data
        self.ok = ok


text_resp: Response[str] = Response("hello")
list_resp: Response[list[int]] = Response([1, 2, 3])
```

### 6.2 Agent 味例子：工具结果

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class ToolResult(Generic[T]):
    def __init__(self, name: str, value: T) -> None:
        self.name = name
        self.value = value


search_result = ToolResult[list[str]]("search", ["a", "b"])
calc_result = ToolResult[float]("calc", 3.0)
```

先掌握「容器/结果类型带类型参数」；复杂约束后面再学。

---

## 7. 建议掌握：`TypeVar` 与泛型函数

```python
from typing import TypeVar

T = TypeVar("T")


def first(items: list[T]) -> T | None:
    return items[0] if items else None


print(first([1, 2, 3]))        # 推断为 int | None
print(first(["a", "b"]))       # 推断为 str | None
```

`TypeVar` 让函数在「保持元素类型」的同时保持通用。

常见进阶（了解名字即可）：

- `bound=`：限制 T 必须是某基类子类型
- `covariant/contravariant`：变型（类型体操区，先别深挖）

---

## 8. 建议掌握：Pyright / mypy 基础

### 8.1 你需要什么

- **Pyright**（VS Code/Cursor 的 Pylance 常用）或 **mypy**
- 在项目里跑检查，而不是只靠肉眼

最小体验（任选其一）：

```bash
# mypy 示例
pip install mypy
mypy your_file.py

# 若用 uv/x 可按你环境安装；工程化章再系统化
```

### 8.2 看懂最常见报错

```text
表达式类型为 "None"，无法访问属性...
参数类型不匹配...
TypedDict 缺少 key...
```

处理思路：

1. 先收窄 `None`
2. 修正函数签名，而不是到处 `# type: ignore`
3. 真需要忽略时写明原因（少数情况）

### 8.3 `from __future__ import annotations`

```python
from __future__ import annotations
```

让注解延迟求值，便于前向引用、减少运行时开销。现代项目很常见；能看懂即可。

---

## 9. 了解即可：类型体操进阶

以下内容读框架时可能见到，**不要求会写**：

- `ParamSpec` / `Concatenate`（给装饰器保签名）
- `TypedDict` 的继承合并与 `Required/NotRequired` 复杂组合
- `TypeGuard` / `TypeIs`
- `overload`
- 递归类型、高阶 Generic 约束

原则：

> **类型是为了降低风险与提升可读，不是为了展示。**  
> 标注到「公共边界清晰」就够；过深的体操收益下降、可读性变差。

---

## 10. 常见坑

1. **以为注解会在运行时拦错**  
   `def f(x: int): ...` + `f("a")` 默认仍能跑；要靠检查器或 pydantic 等运行时校验。

2. **可变默认与注解无关，坑还在**  
   `def f(xs: list[int] = [])` 依然危险。

3. **`list` 与 `list[str]` 混用导致检查失败**  
   尽量写完整。

4. **把 `Any` 当万能胶水**  
   偶尔可以，多了等于放弃检查。

5. **Protocol 方法写成了 `@abstractmethod` 却忘了 ABC**  
   Protocol 体中用 `...` 即可；不要两套概念搅在一起。

6. **JSON 载荷过度 dataclass 化**  
   边界 TypedDict / pydantic，内部再转换。

---

## 11. 综合小例子：给迷你 Agent 加类型

```python
from __future__ import annotations

from typing import Callable, Generic, Literal, Protocol, TypeVar, TypedDict

Role = Literal["system", "user", "assistant", "tool"]


class Message(TypedDict):
    role: Role
    content: str


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


T = TypeVar("T")


class Tool(Generic[T]):
    def __init__(self, name: str, handler: Callable[..., T]) -> None:
        self.name = name
        self.handler = handler

    def run(self, **kwargs: object) -> T:
        return self.handler(**kwargs)


class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


def build_prompt(messages: list[Message]) -> str:
    return "\n".join(f'{m["role"]}: {m["content"]}' for m in messages)


def ask(llm: LLMClient, messages: list[Message]) -> str:
    return llm.complete(build_prompt(messages))


search: Tool[list[str]] = Tool("search", lambda query, top_k=3: [query] * top_k)
msgs: list[Message] = [{"role": "user", "content": "what is RAG"}]
print(ask(EchoLLM(), msgs))
print(search.run(query="RAG", top_k=2))
```

建议你把这段贴进编辑器，故意改错 `role` 或 `complete` 签名，观察类型检查器如何报警。  
（此处 `EchoLLM` 是教学玩具签名；模块 09 起 FakeLLM 以 CONVENTIONS 为准。）

---

## 12. 练习指引

请打开并完成：

[`exercises/02-advanced-python/07-typing-system.md`](../../exercises/02-advanced-python/07-typing-system.md)

建议代码位置：

```text
playground/02-advanced-python/07-typing-system/
```

---

## 13. 小结与下一站

### 心智模型

```text
注解 = 给人和检查器看的契约
Protocol = 能力接口（像不像）
TypedDict/dataclass = 数据结构
Generic/TypeVar = 可复用抽象
检查器 = 让契约真正发挥作用
```

### 自检清单

- [ ] 能给公共函数写清参数与返回类型
- [ ] 会用 `str | None`、`Literal`、`TypedDict`
- [ ] 能写 `Protocol` 描述 LLM/Tool 能力
- [ ] 能写简单 `Generic`/`TypeVar` 例子
- [ ] 独立完成练习基础题

### 模块 02 收官

到这里，Python 高级特性主线已齐：

```text
OOP → 数据模型 → 迭代生成 → 装饰器 → 上下文 → 异常 → 类型
```

下一模块：[`../03-engineering/README.md`](../03-engineering/README.md)  
从「会语言」转入「会做项目」：项目结构、依赖与虚拟环境、测试、日志。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[异常系统](./06-exception-system.md)
- 下一模块：[Python 工程化](../03-engineering/README.md)
