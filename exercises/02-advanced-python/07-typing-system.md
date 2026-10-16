# 练习：类型系统

> 对应文档：[`docs/02-advanced-python/07-typing-system.md`](../../docs/02-advanced-python/07-typing-system.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/02-advanced-python/07-typing-system/
```

4. 若环境有 Pylance/Pyright/mypy，请用它检查你的标注；没有也能先完成代码与注解书写。

---

## 基础题（必做）

### B1. 给函数补全注解

把下面函数补上参数与返回类型（可按你的理解微调实现）：

```python
def clip(text, max_len=20):
    ...

def safe_get(mapping, key, default=None):
    ...

def average(nums):
    # 空列表返回 None
    ...
```

**验收**：注解完整；`average([]) is None`；`average([1, 2, 3]) == 2`。

---

### B2. `Literal` + 收窄

```python
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]

def create_message(role: Role, content: str) -> dict[str, str]:
    ...
```

再写 `assert_role(role: str) -> Role`：若 role 合法则返回（类型上视为 Role），否则抛 `ValueError`。

**验收**：合法 role 通过；非法 role 抛错。可用 `# 期望类型检查报警` 注释标出故意写错的调用（可选）。

---

### B3. TypedDict 消息列表

定义 `Message` TypedDict（字段至少 `role`、`content`），实现：

```python
def append_message(messages: list[Message], role: Role, content: str) -> list[Message]:
    """返回新列表，不修改入参。"""

def contents(messages: list[Message]) -> list[str]:
    ...
```

**验收**：原列表不被修改；`contents` 正确。

---

### B4. Protocol：可替换 LLM

定义 `LLMClient(Protocol)`，实现 `EchoLLM` 与 `UpperLLM`，再写：

```python
def ask(llm: LLMClient, prompt: str) -> str: ...
```

**验收**：两个实现都能传入 `ask`；不要用继承 ABC 完成（本题刻意练 Protocol）。

---

## 进阶题（建议至少做 1 题）

### A1. Generic ToolResult

实现：

```python
class ToolResult(Generic[T]):
    def __init__(self, name: str, value: T) -> None: ...

def unwrap(result: ToolResult[T]) -> T: ...
```

构造 `ToolResult[list[str]]` 与 `ToolResult[float]` 并 unwrap。

**验收**：类型标注齐全；运行结果正确。

---

### A2. 类型检查实践笔记

1. 故意写 2～3 个类型错误（错误 role、把 `None` 当 `str` 用、Protocol 缺方法）
2. 用编辑器或 mypy/pyright 跑一下
3. 在 `a2_notes.md` 记录报错要点与你的修法

若暂时装不了检查器：至少写出「你认为检查器会骂哪一行」并在笔记标明。

**验收**：有笔记；错误与修复成对出现。

---

## 挑战题（可选）

### C1. 迷你 Agent 类型化

综合实现并标注：

- `Message` TypedDict + `Role` Literal
- `LLMClient` Protocol
- `Tool[T]` Generic（或非泛型但注解清晰）
- `run(llm, tools, user_input) -> str`

要求：公共函数都有注解；用 FakeLLM 跑通。

**验收**：可运行；文件顶部可加 `from __future__ import annotations`。

---

### C2. TypedDict vs dataclass（书面）

写 `c2_notes.md`（10 行内）：在「LLM API 响应 JSON」和「Agent 运行时状态」两个场景，你分别选 TypedDict 还是 dataclass，为什么。

**验收**：有明确选择，不是两边都说「都可以」糊弄过去。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成
- [ ] 能口述：注解不运行时强制；Protocol 与 ABC 差异；TypedDict 适用场景
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 模块 02 通关自检（本章做完后）

- [ ] OOP：组合优先、ABC/dataclass/property 会用
- [ ] 数据模型：常用 dunder / `__call__` 会读会写
- [ ] 迭代生成：惰性管道会写
- [ ] 装饰器：retry/timed + wraps
- [ ] 上下文：with / contextmanager
- [ ] 异常：自定义层次 + 异常链
- [ ] 类型：Protocol / TypedDict / Generic 基础

全部勾上后，进入模块 03《Python 工程化》。

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

`safe_get` 可用 `TypeVar` 或简单写成 `dict[str, object]`；学习阶段写成 `dict[str, str] | ...` 也可，关键是注解完整。

</details>

<details>
<summary>B2 提示</summary>

```python
allowed = {"system", "user", "assistant", "tool"}
if role not in allowed:
    raise ValueError(...)
return role  # 对检查器可用 cast[Role](role) 或 if 分支收窄
```

</details>

<details>
<summary>B4 提示</summary>

Protocol 里方法体用 `...`。实现类只需提供同名方法。

</details>

<details>
<summary>A1 提示</summary>

`T = TypeVar("T")`，类继承 `Generic[T]`，`unwrap` 返回 `result.value`。

</details>
