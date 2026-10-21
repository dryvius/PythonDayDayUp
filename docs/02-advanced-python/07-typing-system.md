# 类型系统

> 所属模块：`02-advanced-python` · Python 高级特性与类型系统  
> 状态：`已完成正文`  
> 建议学时：5～8 小时（有 TypeScript 基础可更快；TypedDict / Protocol / Generic 建议动手踩一遍）  
> 对应练习：[`exercises/02-advanced-python/07-typing-system.md`](../../exercises/02-advanced-python/07-typing-system.md)

## 本章定位

- **模块目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **本章角色**：用类型注解把「约定」写清楚——尤其是 Message、Tool、LLM Client、Generic Repository 这类 Agent 核心抽象。
- **重要事实**：注解**默认不在运行时强制检查**；要靠 Pyright / mypy 等工具在开发期发挥作用。
- **你的优势**：前端 TS 里的 `interface` / `type` / generics / null 收窄经验可以直接迁移；重点盯住 Python 的 `Protocol`（结构化接口）、`TypedDict`（dict 形状）、以及「静态检查 ≠ 运行时校验」。

## 学习目标（学完应能做到）

1. 给函数/变量写清楚的类型注解（含 `list[str]`、`dict[str, int]`、`str | None`）。
2. 正确使用 `|` / `Optional` / `Literal` / `TypedDict`（含 `NotRequired`）。
3. 用 `Protocol` 描述「鸭子类型接口」，用 `Generic` / `TypeVar` 写可复用容器/仓储抽象。
4. 会用 Pyright（或 mypy）做基本校验；不陷入类型体操。
5. 完成课后练习，分清必掌握 / 建议掌握 / 了解即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 类型注解、Optional/Union/Literal、TypedDict、Protocol、Generic | 能读框架、能为自己的 Agent 代码标注 |
| **建议掌握** | TypeVar、pyright/mypy 基础 | 会跑检查、会写简单泛型函数 |
| **了解即可** | 类型体操进阶 | 见到不慌，不主动炫技 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要类型注解？

没有类型时，Agent 代码的「约定」往往只存在于脑子里或注释里：

```text
messages 应该是 list[dict]，每项有 role / content
llm 应该有 complete 方法
tool 结果可能是 list[str]，也可能是 float
content 可能是 None……
```

一旦换人、换实现、重构参数名，这些约定很容易 silently 坏掉。

有了类型，框架源码通常长这样：

```python
class LLM(Protocol):
    async def generate(self, prompt: str) -> str: ...

def run_agent(llm: LLM, tools: list[Tool]) -> AgentResult:
    ...
```

#### 本章要练的四种收益

1. **可读**：函数输入输出一目了然
2. **可换实现**：`Protocol` / ABC 让 FakeLLM 与真 LLM 可替换
3. **少一类 bug**：把 `None`、错误字段名、工具参数结构问题提前暴露
4. **更好的编辑器补全**：前端 TS 用户会非常有熟悉感

可以先记一句：

> 注解是给**人和检查器**看的契约；默认**不会**在运行时替你拦错。要拦运行时，用 pydantic / 手写校验；要拦开发期，用 Pyright / mypy。

#### 和 TypeScript 的粗对照（先建立地图）

| TypeScript | Python typing |
|------------|---------------|
| `string \| null` | `str \| None` |
| `interface`（对象形状） | `TypedDict`（dict）/ `Protocol`（能力） |
| `type Role = "a" \| "b"` | `Literal["a", "b"]` |
| `generics <T>` | `Generic[T]` / `TypeVar` |
| 编译期检查 | Pyright/mypy 静态检查（运行时默认不查） |
| `as T` / 收窄 | `isinstance` / `is None` 收窄；真需要时用 `cast` / `TypeGuard` |

---

## 2. 必掌握：类型注解基础

这一节会刻意写细——注解是后面 TypedDict、Protocol、Generic 的共同底座。

### 2.1 函数注解

#### 为什么需要给函数写注解？

上一章你会写「能跑的函数」。但调用方看 `def create_message(role, content)` 时，并不知道：

- `role` 该传什么？
- 返回的是 `dict` 还是对象？
- 会不会返回 `None`？

注解把这些边界写进签名。

#### 怎么写

```python
def create_message(role: str, content: str) -> dict[str, str]:
    return {"role": role, "content": content}


def clip(text: str, max_len: int = 20) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
```

拆开看：

1. `role: str` —— 参数注解
2. `-> dict[str, str]` —— 返回值注解
3. 默认参数写法：`max_len: int = 20`（类型在前，默认值在后）
4. Python ≥ 3.9 起，内置容器可直接当泛型用：`list[str]`、`dict[str, int]`（本课程按 ≥ 3.11）

#### 跑一下

```python
msg = create_message("user", "hello")
print(msg)                 # {'role': 'user', 'content': 'hello'}
print(clip("abcdefghij", 8))  # abcde...
```

注意：即使你写错类型，**默认也能跑**：

```python
# 运行时通常不会报错；Pyright 才会报警
create_message(1, 2)  # type: ignore[arg-type]  # 故意示意
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 以为注解会拦错类型 | 默认不会；`clip(123)` 仍可能在运行时报错或怪结果 |
| 只标参数、不标返回 | 调用链推断变弱，补全和检查都变差 |
| 返回了 `None` 却标成 `-> str` | 检查器报错；运行时可能在调用方炸 |
| 把注解写成运行时校验 | 注解不是 `assert isinstance`；要校验请显式写 |

#### TS 对照

| TypeScript | Python |
|------------|--------|
| `function f(x: string): number` | `def f(x: str) -> int` |
| `function clip(text: string, maxLen = 20): string` | `def clip(text: str, max_len: int = 20) -> str` |
| 编译失败才能跑（tsc） | 注解错了也能跑；靠 Pyright/mypy |

```typescript
function createMessage(role: string, content: string): Record<string, string> {
  return { role, content }
}
```

---

### 2.2 常见容器注解

#### 为什么容器要写元素类型？

只写 `list` / `dict` 时，检查器不知道你取出的是什么，补全几乎失效。Agent 里到处是「字符串列表」「消息列表」「分数映射」，元素类型才是有用信息。

#### 怎么写

```python
names: list[str] = ["search", "calc"]
scores: dict[str, float] = {"search": 0.9}
pair: tuple[str, int] = ("page", 1)
unique: set[str] = {"a", "b"}

# 嵌套也很常见
messages: list[dict[str, str]] = [
    {"role": "user", "content": "hi"},
]
```

口诀：

```text
list[元素类型]
dict[键类型, 值类型]
tuple[第1项, 第2项, ...]   # 定长异构
tuple[str, ...]            # 同质不定长（了解）
set[元素类型]
```

#### 跑一下

```python
tools: list[str] = ["search", "calc"]
tools.append("read_file")
print(tools[0].upper())  # SEARCH —— 检查器知道是 str，才敢补全 .upper()

page: tuple[str, int] = ("docs", 3)
print(f"{page[0]}#{page[1]}")
```

#### 易错点

- **老写法**：`from typing import List, Dict` → `List[str]`。能读懂即可；**新代码优先 `list[str]`**。
- **`tuple` vs `list`**：定长异构（如 `(name, score)`）用 `tuple[...]`；可变序列用 `list[...]`。
- **空列表推断**：`xs = []` 常被推断成 `list[Unknown]` / `list[Any]`。需要时显式写 `xs: list[str] = []`。
- **`dict` 键几乎总是 `str`**（JSON 场景）；别写成含糊的 `dict`。

#### TS 对照

| TypeScript | Python |
|------------|--------|
| `string[]` / `Array<string>` | `list[str]` |
| `Record<string, number>` | `dict[str, float]`（或更具体） |
| `[string, number]` | `tuple[str, int]` |
| `Set<string>` | `set[str]` |

---

### 2.3 变量注解与逐步标注策略

#### 为什么变量也要标？

局部变量常常靠推断；但「初始为 `None`、稍后赋值」「空容器稍后 append」这两类场景，推断经常不够，需要手写注解。

#### 怎么写

```python
messages: list[dict[str, str]] = []
result: str | None = None

if True:
    result = "ok"

# 使用前收窄
if result is not None:
    print(result.upper())
```

#### 跑一下

```python
history: list[str] = []
history.append("user: hi")
history.append("assistant: hello")
print(len(history))  # 2
```

#### 落地建议（避免一开始就全项目炫技）

1. 先标**公共函数边界**（别人会调用的）
2. 再标**核心数据结构**（Message、Tool、Config）
3. 内部小函数可以后补
4. 出现 `Any` 时问自己：是暂时逃逸，还是放弃检查？

#### 易错点

> 注解改变的是**检查器眼中的类型**，不是运行时对象本身。

```python
x: int = "hello"  # 检查器报警；运行时 x 仍是 str
print(type(x))    # <class 'str'>
```

#### TS 对照

```typescript
let result: string | null = null
result = "ok"
if (result !== null) {
  console.log(result.toUpperCase())
}
```

Python 侧对应：`str | None` + `if result is not None`。

---

## 3. 必掌握：`Optional` / `Union` / `Literal`

### 3.1 可空：`str | None`

#### 为什么需要 `| None`？

Agent 里「可能没有」极其常见：

- 模型没返回 content
- 字典里找不到 key
- 工具可选参数没传
- 截断/清洗后变成空，你想用 `None` 表示「无效」

如果不标 `| None`，调用方会假装它永远是 `str`，然后在 `.strip()` 上炸。

#### 怎么写

```python
def normalize(content: str | None) -> str | None:
    if content is None:
        return None
    text = content.strip()
    return text or None
```

等价老写法（能读即可，新代码优先 `|`）：

```python
from typing import Optional

def normalize_old(content: Optional[str]) -> Optional[str]:
    ...
```

`Optional[str]` ≡ `Union[str, None]` ≡ `str | None`。

#### 跑一下

```python
print(normalize(None))       # None
print(normalize("  hi  "))   # hi
print(normalize("   "))      # None（空白视为无效）
```

**关键习惯**：标了 `| None` 就要在使用前收窄：

```python
raw: str | None = normalize("  hello  ")
if raw is None:
    print("empty")
else:
    print(raw.upper())  # 这里 raw 被收窄为 str
```

#### 易错点

| 错法 | 正确做法 |
|------|----------|
| 标了 `str \| None` 却直接 `.upper()` | 先 `if x is None` |
| 用 `if not x` 收窄字符串 | 空字符串 `""` 也会被当成假；要区分「无值」和「空串」时用 `is None` |
| 到处返回 `""` 假装没有 | 语义是「缺失」时用 `None` 更清晰 |
| 混用 `Optional[str]` 与 `str \| None` 风格 | 同一项目统一；本课程统一 `str \| None` |

#### TS 对照

| TypeScript | Python |
|------------|--------|
| `string \| null` | `str \| None` |
| `string \| undefined`（可选属性） | 参数默认值 / `NotRequired` / `X \| None` |
| `if (x !== null) { x.toUpperCase() }` | `if x is not None: x.upper()` |

> Python 没有 TS 那种「未传参是 `undefined`」的运行时区分；可选通常用默认值或 `None`。

---

### 3.2 联合类型：`Union` / `|`

#### 为什么需要联合类型？

同一个位置可能接受多种合法形态：ID 既可能是 `int` 也可能是 `str`；工具结果可能是文本或结构化 dict。

#### 怎么写

```python
Id = int | str

def as_str_id(value: Id) -> str:
    return str(value)


# 更贴近 Agent：工具输出
ToolOutput = str | dict[str, object] | list[str]
```

老写法：`from typing import Union` → `Union[int, str]`。新代码优先 `int | str`。

#### 跑一下

```python
print(as_str_id(42))     # 42
print(as_str_id("u-7"))  # u-7
```

使用前按分支收窄：

```python
def summarize(output: str | list[str]) -> str:
    if isinstance(output, list):
        return ", ".join(output)
    return output
```

#### 易错点

- 联合类型不是「随便什么都行」——那是 `Any` / `object`。
- 收窄要用 `isinstance` / 比较 / 标签字段（discriminated union 思路），不要靠注释。
- `dict[str, object]` 取值后往往还要再校验；别误以为注完就安全。

#### TS 对照

```typescript
type Id = number | string
function asStrId(value: Id): string {
  return String(value)
}
```

---

### 3.3 `Literal`：限定有限取值

#### 为什么需要 `Literal`？

`role: str` 太宽：`"admin"`、`"USER"`、拼错的 `"assisstant"` 都能过注解。  
Agent 里 role、模式开关、工具名枚举，本质是**有限集合**。

#### 怎么写

```python
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]


def create_message(role: Role, content: str) -> dict[str, str]:
    return {"role": role, "content": content}
```

也可以内联：

```python
def set_mode(mode: Literal["json", "text"]) -> None:
    print("mode =", mode)
```

#### 跑一下

```python
create_message("user", "hi")
set_mode("json")

# 下面两行：运行时可能还能跑，但类型检查器应报警
# create_message("admin", "hi")
# set_mode("yaml")
```

从 `str`「升级」成 `Literal` 时，通常需要显式校验函数（练习 B2 会练）：

```python
def assert_role(role: str) -> Role:
    allowed: tuple[Role, ...] = ("system", "user", "assistant", "tool")
    if role not in allowed:
        raise ValueError(f"invalid role: {role}")
    return role  # 检查器若仍不收窄，见 §9 TypeGuard；练习里可先这样写
```

#### 易错点

- `Literal` 区分大小写：`"User"` ≠ `"user"`。
- 运行时**不会**自动拒绝非法字符串；要拦得自己 `raise` 或用 pydantic。
- 和 `Enum` 的分工：需要命名空间/行为时用 `Enum`；只是字符串字面量集合时 `Literal` 更轻。

#### TS 对照

| TypeScript | Python |
|------------|--------|
| `type Role = "system" \| "user" \| ...` | `Role = Literal["system", "user", ...]` |
| `mode: "json" \| "text"` | `mode: Literal["json", "text"]` |

Agent 高频：`role`、工具名枚举、模式开关（`"json" | "text"`）。

---

## 4. 必掌握：`TypedDict`

这一节是本章「dict 形状」的核心，建议写细、多手敲。

### 4.1 为什么需要 TypedDict？

Agent / 后端大量数据天生就是 **JSON → dict**：

```python
{"role": "user", "content": "hello"}
```

若只用 `dict[str, str]`：

- 不知道必有哪些 key
- 拼错 `"contnet"` 检查器发现不了
- 可选字段（如 `name`）无法表达

`TypedDict` 专门描述「这就是一个有固定字段的 dict」。

### 4.2 怎么写：基础形态

```python
from typing import TypedDict, NotRequired


class MessageDict(TypedDict):
    role: str
    content: str
    name: NotRequired[str]  # 可以没有这个 key


def last_content(messages: list[MessageDict]) -> str | None:
    if not messages:
        return None
    return messages[-1]["content"]
```

要点：

1. **语法像 class，运行时仍是 dict**——没有变成真正的类实例
2. 取值用 `m["content"]`，不是 `m.content`
3. `NotRequired[T]`：key 可以缺失（Python 3.11+ 也可 `from typing import NotRequired`）
4. 全部必填是默认行为；若多数可选，可用 `TypedDict(..., total=False)`（了解）

### 4.3 跑一下

```python
msg: MessageDict = {"role": "user", "content": "hi"}
print(msg["role"])  # user

msgs: list[MessageDict] = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "what is RAG", "name": "alice"},
]
print(last_content(msgs))  # what is RAG

# 检查器通常会报警的例子（可在编辑器里试）：
# bad: MessageDict = {"role": "user"}              # 缺 content
# also_bad: MessageDict = {"role": "user", "content": "hi", "age": 1}  # 多未知键（视配置）
```

结合 `Literal` 更贴近真实 Agent：

```python
from typing import Literal, TypedDict

Role = Literal["system", "user", "assistant", "tool"]


class Message(TypedDict):
    role: Role
    content: str
```

### 4.4 和 `@dataclass` 怎么选

| 更用 TypedDict | 更用 dataclass |
|----------------|----------------|
| 本来就是 JSON/dict 形态 | 需要方法/行为 |
| 与外部 API 载荷对齐 | 领域对象更丰富 |
| 轻量标注现有 dict | 想要运行时对象 |
| 序列化几乎零成本 | 要 `asdict` / 自己转换 |

两者常同时存在：

```text
边界（HTTP / LLM JSON）→ TypedDict / pydantic
内部领域逻辑       → dataclass / 普通 class
```

### 4.5 易错点（TypedDict 专场）

1. **误以为 TypedDict 会在运行时校验**  
   `MessageDict(role=1, content=2)` 这种构造方式本身就不对——正确是写字面量 dict；且即便字段错了，运行时也可能默默接受。

2. **用属性访问**  
   `msg.content` ❌（那是对象）；`msg["content"]` ✅。

3. **`total=False` 与 `NotRequired` 混用时没读清语义**  
   新手优先：必填字段正常写，可选字段用 `NotRequired`。

4. **和 `dict[str, str]` 互相赋值**  
   结构不兼容时检查器会报错——这是好事，别急着 `cast`。

5. **修改共享 list 里的 dict**  
   TypedDict 不改变「dict 可变」的事实；需要不可变语义时自己复制（`{**m, "content": ...}` 或新 list）。

### 4.6 TS 对照

| TypeScript | Python |
|------------|--------|
| `type Message = { role: string; content: string }` | `class Message(TypedDict): ...` |
| `name?: string` | `name: NotRequired[str]` |
| `Message[]` | `list[Message]` |
| 接口多余属性检查（结构化） | 视 Pyright 配置；别假设和 tsc 完全一致 |

```typescript
type Message = {
  role: "system" | "user" | "assistant" | "tool"
  content: string
  name?: string
}
```

---

## 5. 必掌握：`Protocol`（结构化接口）

### 5.1 为什么不用死继承？

#### 为什么需要 Protocol？

你希望任何「长得像 LLM」的对象都能传入，而不强制继承某个基类——测试替身、第三方 SDK 包装、本地 Echo 实现都应该能插拔。

这和前端 TS 的 `interface` 很像：**看形状，不看血缘**。

### 5.2 怎么写

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
```

要点：

1. Protocol 里方法体用 `...`（或 `pass`）即可
2. **实现类不必写 `class EchoLLM(LLMClient)`**
3. 只要方法名、参数、返回类型匹配，静态检查就认可
4. 这叫结构化定型（structural typing）

> 命名提醒：早期章用 `EchoLLM` 演示 Protocol；模块 09 起的 **FakeLLM** 必须遵守 `complete(messages, tools=None) -> assistant_message`。

### 5.3 跑一下

```python
class UpperLLM:
    def complete(self, prompt: str) -> str:
        return prompt.upper()


print(ask(EchoLLM(), "hi"))   # ECHO: hi
print(ask(UpperLLM(), "hi"))  # HI
```

故意写错签名时（编辑器 / pyright）：

```python
class BrokenLLM:
    def complete(self, prompt: int) -> str:  # 参数类型不对
        return "x"


# ask(BrokenLLM(), "hi")  # 类型检查应报警
```

异步版（读框架时常见；手写 Agent 教学可用同步）：

```python
from typing import Protocol


class AsyncLLM(Protocol):
    async def complete(self, prompt: str) -> str: ...
```

### 5.4 对比 ABC

| ABC | Protocol |
|-----|----------|
| 运行时也可拦（不能实例化抽象类） | 更偏静态检查 |
| 需要显式继承 | 不必继承，有匹配方法即可 |
| 适合强制实现、共享默认逻辑 | 适合解耦、插件、鸭子类型 |
| `@abstractmethod` | 方法体写 `...` 即可 |

Agent 框架两者都常见：学会认即可；新代码里描述「能力接口」优先想到 Protocol。

什么时候仍用 ABC？

- 需要运行时 `isinstance(x, BaseTool)` 且愿意强制继承
- 基类要提供可复用的默认实现

什么时候用 Protocol？

- 第三方类你改不了继承
- 测试替身想保持轻量
- 只关心「有没有这个能力」

### 5.5 `@runtime_checkable`（建议知道）

默认 `isinstance(obj, LLMClient)` 对普通 Protocol **不可用**（或不符合直觉）。若确实需要运行时检查：

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsComplete(Protocol):
    def complete(self, prompt: str) -> str: ...


print(isinstance(EchoLLM(), SupportsComplete))  # True
```

注意：runtime_checkable **只检查属性/方法是否存在**，不深度检查签名——别把它当 mypy。

### 5.6 易错点

| 错法 | 说明 |
|------|------|
| Protocol 里写 `@abstractmethod` 又继承搞混 | Protocol 用 `...`；ABC 才是抽象类那套 |
| 方法名一样但参数含义不同 | 结构化匹配看类型签名；语义仍靠你自己保证 |
| 把教学 `EchoLLM` 命名成 `FakeLLM` | 与 CONVENTIONS 冲突；模块 09 契约不同 |
| 指望 Protocol 在运行时拦截错误实现 | 默认只是静态契约 |
| 在 Protocol 里塞大量实现代码 | 那更像基类；Protocol 保持「接口」干净 |

### 5.7 TS 对照

| TypeScript | Python |
|------------|--------|
| `interface LLM { complete(prompt: string): string }` | `class LLMClient(Protocol): def complete...` |
| 结构化类型（鸭式） | Protocol 结构化匹配 |
| `class Echo implements LLM`（可选） | 通常**不必**显式继承 Protocol |
| `type` 与 `interface` 都能描述对象 | 能力 → Protocol；dict 形状 → TypedDict |

```typescript
interface LLMClient {
  complete(prompt: string): string
}

function ask(llm: LLMClient, prompt: string): string {
  return llm.complete(prompt)
}
```

---

## 6. 必掌握：`Generic` 基础

### 6.1 为什么需要泛型类？

`Response` / `ToolResult` / `Repository` 这类容器，**结构相同、装的东西不同**：

```text
Response[str]           → data 是 str
Response[list[int]]     → data 是 list[int]
ToolResult[float]       → value 是 float
```

若写成 `data: Any`，等于放弃检查；若为每种类型复制一个类，又太吵。Generic 解决这件事。

### 6.2 怎么写：泛型类

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class Response(Generic[T]):
    def __init__(self, data: T, ok: bool = True) -> None:
        self.data = data
        self.ok = ok
```

使用时「填入」类型参数：

```python
text_resp: Response[str] = Response("hello")
list_resp: Response[list[int]] = Response([1, 2, 3])
```

### 6.3 跑一下

```python
r1 = Response[str]("hello")
print(r1.data.upper())  # HELLO —— 检查器知道 data 是 str

r2 = Response[list[int]]([1, 2, 3])
print(sum(r2.data))     # 6
```

### 6.4 Agent 味例子：工具结果

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class ToolResult(Generic[T]):
    def __init__(self, name: str, value: T) -> None:
        self.name = name
        self.value = value


search_result = ToolResult[list[str]]("search", ["a", "b"])
calc_result = ToolResult[float]("calc", 3.0)

print(search_result.value[0])  # a
print(calc_result.value * 2)   # 6.0
```

先掌握「容器/结果类型带类型参数」；复杂约束（bound、变型）放到下一节。

### 6.5 易错点

- **忘记 `Generic[T]`**：只写 `TypeVar` 却不继承 `Generic[T]`，类级参数接不住。
- **`T` 只在类里用、却在模块别处乱复用同名 TypeVar**：可以共用一个 `T = TypeVar("T")`，但含义要始终是「某未知类型」，别赋予额外语义。
- **运行时擦除**：`Response[str]` 在运行时信息有限（别靠它做业务分支）；业务分支用真正的值 / `isinstance`。
- **和 TS 一样：泛型是编译期（检查期）工具**，不是新的运行时容器魔法。

### 6.6 TS 对照

```typescript
class Response<T> {
  constructor(public data: T, public ok: boolean = true) {}
}

const textResp = new Response<string>("hello")
const listResp = new Response<number[]>([1, 2, 3])
```

| TypeScript | Python |
|------------|--------|
| `class Response<T>` | `class Response(Generic[T])` |
| `Response<string>` | `Response[str]` |
| `T` 类型参数 | `T = TypeVar("T")` |

---

## 7. 建议掌握：`TypeVar` 与泛型函数

### 7.1 为什么函数也需要 TypeVar？

你想写一个通用的 `first(items)`：

- 传入 `list[int]` → 返回 `int | None`
- 传入 `list[str]` → 返回 `str | None`

若写成 `list[Any] -> Any`，调用方失去类型；若只写 `list[int]`，又不够通用。`TypeVar` 把「同一未知类型」在参数和返回值之间**钉在一起**。

### 7.2 怎么写

```python
from typing import TypeVar

T = TypeVar("T")


def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

多参数保持同一类型：

```python
def pick(a: T, b: T) -> T:
    return a if a else b
```

带上界（bound）：T 必须是某类型的子类（或兼容）：

```python
from typing import TypeVar

class Message:
    content: str


M = TypeVar("M", bound=Message)


def contents_of(items: list[M]) -> list[str]:
    return [m.content for m in items]
```

### 7.3 跑一下

```python
print(first([1, 2, 3]))        # 1 —— 推断为 int | None
print(first(["a", "b"]))       # a —— 推断为 str | None
print(first([]))               # None
```

再写一个「解包 ToolResult」：

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class ToolResult(Generic[T]):
    def __init__(self, name: str, value: T) -> None:
        self.name = name
        self.value = value


def unwrap(result: ToolResult[T]) -> T:
    return result.value


n = unwrap(ToolResult[int]("calc", 42))
print(n + 1)  # 43
```

### 7.4 易错点

| 错法 | 说明 |
|------|------|
| 返回类型写成 `list` 却期望保留元素类型 | 用 `list[T]` / `T` |
| 两个无关 TypeVar 却想表达同一类型 | 同一 `T` 才能钉住关系 |
| 过早纠结 covariant/contravariant | 变型是类型体操区；先会用 `TypeVar` + `bound` |
| 用 `T` 做运行时判断 | TypeVar 在运行时不是具体类型对象用途 |

### 7.5 常见进阶名字（了解即可，下节地图会再列）

- `bound=`：限制 T 必须是某基类子类型
- `covariant` / `contravariant`：变型（容器只读/只写场景；先别深挖）
- `TypeVar("T", str, bytes)`：约束为若干候选类型（老式约束写法，能读即可）

### 7.6 TS 对照

```typescript
function first<T>(items: T[]): T | null {
  return items.length ? items[0] : null
}
```

| TypeScript | Python |
|------------|--------|
| `function first<T>(items: T[]): T \| null` | `def first(items: list[T]) -> T \| None` |
| `<T extends Message>` | `TypeVar("M", bound=Message)` |

---

## 8. 建议掌握：Pyright / mypy 基础

### 8.1 为什么需要类型检查器？

注解本身不会喊疼。没有检查器时，你只是写了「高级注释」。  
有了 Pyright / mypy，契约才真正开始工作——这和 TS 必须经过 `tsc` / IDE 检查是同一逻辑。

### 8.2 你需要什么

- **Pyright**（VS Code / Cursor 的 Pylance 底层常用）或 **mypy**
- 在项目里跑检查，而不是只靠肉眼
- 本课程不强制二选一：编辑器红线 + 命令行，都能建立直觉

最小体验（任选其一）：

```bash
# mypy 示例
pip install mypy
mypy your_file.py

# pyright 示例
pip install pyright
pyright your_file.py

# 若用 uv 可按你环境安装；工程化章再系统化
```

Cursor / VS Code：安装 Python 相关扩展后，Pylance 通常会直接在编辑器里显示 Pyright 诊断。

### 8.3 怎么写一个「故意出错」的文件来感受

```python
# demo_typing.py
from typing import TypedDict


class Message(TypedDict):
    role: str
    content: str


def last_content(messages: list[Message]) -> str:
    return messages[-1]["content"]


def boom(x: str | None) -> str:
    return x.upper()  # 期望报警：x 可能是 None


# last_content([])                 # 运行时 IndexError；类型也可能觉得不舒服
# boom(None)
msg: Message = {"role": "user"}  # 期望报警：缺 content
```

对这个文件跑 `pyright demo_typing.py` 或打开编辑器看波浪线。

### 8.4 跑一下：看懂最常见报错

```text
表达式类型为 "None"，无法访问属性 "upper"
参数类型不匹配...
TypedDict 缺少 key "content"
无法访问属性...（Protocol 不匹配）
List item 0 has incompatible type...
```

处理思路：

1. 先收窄 `None`（`if x is None: return ...`）
2. 修正函数签名，而不是到处 `# type: ignore`
3. TypedDict 缺字段 → 补字段或把字段标成 `NotRequired`
4. Protocol 不匹配 → 改实现签名，或承认类型不是那个 Protocol
5. 真需要忽略时写明原因（少数情况）：`# type: ignore[return-value]  # 第三方 stub 不准`

### 8.5 `from __future__ import annotations`

#### 为什么需要它？

注解默认在定义时求值。若类还没定义完就自我引用，或想减少运行时开销，常用：

```python
from __future__ import annotations
```

效果：注解变成延迟求值（字符串化/惰性），便于前向引用。

#### 怎么写 / 跑一下

```python
from __future__ import annotations

from typing import TypedDict


class Node(TypedDict):
    value: str
    children: list[Node]  # 前向引用自身，有 future 更轻松
```

现代项目很常见；Python 3.11 里也能写不少直接引用，但看到这行要认识。

#### 易错点

- 有 `from __future__ import annotations` 时，**运行时** `get_type_hints` 才解析；普通 `__annotations__` 可能是字符串——写框架反射时要注意。
- 它不替代类型检查器；只是改变注解的求值时机。

### 8.6 最小配置直觉（了解）

不同严格度差很多。例如 Pyright：

- `basic`：较松
- `standard`：常用
- `strict`：很严（`Any` 也会被盯）

落地建议：学习阶段用编辑器默认即可；项目里再定 `pyrightconfig.json` / `mypy.ini`。别一上来全库 `strict` 然后靠 `ignore` 堆出来。

### 8.7 TS 对照

| TypeScript 世界 | Python 世界 |
|-----------------|-------------|
| `tsc --noEmit` | `pyright` / `mypy` |
| IDE 红线（Volar/TS server） | Pylance / Pyright |
| `// @ts-expect-error` | `# type: ignore[...]` |
| `tsconfig` strict | pyright `typeCheckingMode` / mypy strict |
| 编译产物 | **无编译步骤**；检查是独立工具 |

---

## 9. 了解即可：类型体操进阶

以下内容读框架时可能见到，**不要求会写**——建立地图，防止过载。

### 9.1 常见名词地图

| 名词 | 一句话 | 你何时会撞见 |
|------|--------|--------------|
| `ParamSpec` / `Concatenate` | 给装饰器「保住原函数参数类型」 | 装饰器库、重试封装 |
| `TypedDict` 继承合并 / `Required` / `NotRequired` | 组合复杂 JSON 形状 | OpenAPI / LLM tool schema |
| `TypeGuard` / `TypeIs` | 自定义收窄函数的返回含义 | `is_role(x) -> TypeGuard[Role]` |
| `@overload` | 同一函数多种参数-返回对应关系 | `open` 风格 API、便捷构造器 |
| 递归类型 | 类型里引用自身 | 树、JSON 值、嵌套消息 |
| 高阶 Generic 约束 / 变型 | `covariant` 等 | 只读容器、框架内部 |

### 9.2 原则

> **类型是为了降低风险与提升可读，不是为了展示。**  
> 标注到「公共边界清晰」就够；过深的体操收益下降、可读性变差。

若你发现自己在写「只有检查器看得懂、人类读得痛苦」的别名迷宫——停下来，改用更直的 `Protocol` + `TypedDict` + 小函数。

### 9.3 TS 对照（地图级）

| TypeScript | Python |
|------------|--------|
| 条件类型 / `infer` | 较少同款表达；多用 overload / TypeGuard |
| 装饰器保签名 | `ParamSpec` |
| `x is string` 谓词 | `TypeGuard` / `TypeIs` |
| 函数重载 | `@overload` |

---

## 10. 常见坑

1. **以为注解会在运行时拦错**  
   `def f(x: int): ...` + `f("a")` 默认仍能跑；要靠检查器或 pydantic 等运行时校验。

2. **可变默认与注解无关，坑还在**  
   `def f(xs: list[int] = [])` 依然危险。用 `None` 哨兵：

   ```python
   def f(xs: list[int] | None = None) -> list[int]:
       if xs is None:
           xs = []
       return xs
   ```

3. **`list` 与 `list[str]` 混用导致检查失败**  
   尽量写完整；空列表写 `xs: list[str] = []`。

4. **把 `Any` 当万能胶水**  
   偶尔可以（第三方无 stub），多了等于放弃检查。优先 `object` + 收窄，或补 TypedDict。

5. **Protocol 方法写成了 `@abstractmethod` 却忘了 ABC**  
   Protocol 体中用 `...` 即可；不要两套概念搅在一起。

6. **JSON 载荷过度 dataclass 化**  
   边界 TypedDict / pydantic，内部再转换。

7. **用 `cast` 消红线掩盖真问题**  
   `cast(str, x)` 不转换运行时值；滥用等于骗检查器。

8. **`str | None` 却用 `if not x` 收窄**  
   空串会被误判；区分缺失与空串时用 `is None`。

9. **TypedDict 当类用**  
   写 `Message(role="user", content="hi")` 期望得到实例——不对；写 dict 字面量。

10. **检查器没跑就说「类型没用」**  
    没接 Pyright/mypy/Pylance 时，注解确实接近注释。

---

## 11. 综合小例子：给迷你 Agent 加类型

把本章必掌握点串起来：Literal + TypedDict + Protocol + Generic + TypeVar。

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

#### 跑一下时建议做的三件破坏实验

1. 把 `role` 改成 `"admin"` —— 看 Literal/TypedDict 如何报警  
2. 删掉 `EchoLLM.complete` 或改参数类型 —— 看 Protocol 如何报警  
3. 对可能为 `None` 的值直接 `.upper()` —— 看可空收窄如何报警  

（此处 `EchoLLM` 是教学玩具签名；模块 09 起 FakeLLM 以 CONVENTIONS 为准。）

#### 这段例子对应的 TS 心智

```text
Role          ≈ type Role = "system" | ...
Message       ≈ interface / type 对象形状
LLMClient     ≈ interface（能力）
Tool<T>       ≈ class Tool<T>
ask(llm, ...) ≈ 依赖注入：要的是能力，不是某个具体类
```

---

## 12. 练习指引

请打开并完成：

[`exercises/02-advanced-python/07-typing-system.md`](../../exercises/02-advanced-python/07-typing-system.md)

建议代码位置：

```text
playground/02-advanced-python/07-typing-system/
```

做题顺序建议：

1. 基础题 B1～B4（注解 / Literal / TypedDict / Protocol）
2. 进阶题至少一题（Generic / TypeVar）
3. 若环境有 Pylance/Pyright，故意留一行错误看诊断，再改掉

---

## 13. 小结与下一站

### 心智模型

```text
注解 = 给人和检查器看的契约
Protocol = 能力接口（像不像）
TypedDict/dataclass = 数据结构（dict 形状 / 对象行为）
Generic/TypeVar = 可复用抽象（结构同、元素异）
检查器 = 让契约真正发挥作用
运行时校验（pydantic 等）= 另一条线，别和注解混为一谈
```

### 自检清单

- [ ] 能给公共函数写清参数与返回类型（`list[str]`、`str | None`）
- [ ] 会用 `str | None`、`Literal`、`TypedDict`（含可选字段）
- [ ] 能写 `Protocol` 描述 LLM/Tool 能力，并理解与 ABC 的差别
- [ ] 能写简单 `Generic` / `TypeVar` 例子，说清「钉住同一类型」
- [ ] 会在编辑器或命令行跑 Pyright/mypy，看懂 None / TypedDict / 参数不匹配类报错
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
