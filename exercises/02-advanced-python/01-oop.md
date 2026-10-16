# 练习：面向对象编程

> 对应文档：[`docs/02-advanced-python/01-oop.md`](../../docs/02-advanced-python/01-oop.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/02-advanced-python/01-oop/
```

4. 优先把类写在模块文件里，再用 `*_main.py` 演示；先做题再看提示。

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

要求：

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

1. `EchoLLM`：返回 `"ECHO: " + prompt`
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

要求：

1. `preview`：strip 后长度 > 30 则截断到 27 字符 + `...`
2. `is_relevant`：`score >= 0.6`
3. 再写 `@dataclass` 的 `RagResult(chunks: list[DocumentChunk])`，提供 property `relevant_chunks`（过滤相关片段）

**验收**：自己构造 3 个 chunk，打印 preview / relevant_chunks 符合预期；`tags` 默认值互不污染（两个实例互不共享 list）。

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

- `LLMClient` 抽象 + 至少一个实现
- `Tool` 抽象/基类 + `SearchTool`
- `Agent` 通过构造函数注入 `llm` 与 `tools`

并写一段 demo：用 FakeLLM 跑通。

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

**验收**：换 `EchoLLM` / 另一个 FakeLLM，脚本都能跑；history 长度随对话增长。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成
- [ ] 能口述：继承 vs 组合；ABC 解决什么问题；dataclass 何时用
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）完成 C1

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

返回拷贝用 `list(self._items[-n:])` 或切片后再拷贝 dict：`[dict(x) for x in ...]`。浅拷贝对一层 dict 通常够用。

</details>

<details>
<summary>B2 提示</summary>

`get_tool` 可用字典缓存 `name -> tool`。`call` 即 `self.get_tool(name).run(**kwargs)`。

</details>

<details>
<summary>B3 提示</summary>

`LLMClient()` 应触发 `TypeError`。`run_prompt` 内只调用 `llm.complete`。

</details>

<details>
<summary>B4 提示</summary>

`tags` 必须 `field(default_factory=list)`。`relevant_chunks` 用列表推导式过滤。

</details>

<details>
<summary>A1 思路</summary>

把“创建依赖”从类内部挪到构造参数。测试时注入 Fake 对象，断言 `ask` 输出包含 fake 标记。

</details>

<details>
<summary>A2 思路</summary>

内部 `dict[str, Tool]`；`__getitem__` 找不到就抛 `KeyError`（或自定义异常）。

</details>

<details>
<summary>C1 思路</summary>

文档第 11 节综合例子几乎就是骨架。先让 Echo 跑通，再抽 ABC。`step_count` 统计 `role == "assistant"` 的数量。

</details>
