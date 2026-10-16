# 练习：模块、包与导入系统

> 对应文档：[`docs/01-python-basics/03-modules-packages.md`](../../docs/01-python-basics/03-modules-packages.md)  
> 状态：`已完成出题`  
> 建议用时：60～100 分钟

## 练习说明

1. 本章以**搭包 + 跑通导入**为主，请在指定目录创建真实文件。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议根目录：

```text
playground/01-python-basics/03-modules-packages/
```

4. 每做完一题，用命令行真正运行一次，不要只看代码“感觉没问题”。
5. 先做题，再看文末提示。

---

## 基础题（必做）

### B1. 单文件模块导入

在练习目录创建：

```text
03-modules-packages/
├── textkit.py
└── b1_main.py
```

`textkit.py` 需提供：

```python
def normalize(text: str) -> str:
    """strip + 压缩连续空白为单空格"""

def clip(text: str, max_len: int = 20) -> str:
    """超长则截断并加 ...（总长不超过 max_len）"""
```

`b1_main.py` 使用 `import textkit`（不要 from import *），演示两次调用并打印结果。

**验收**：

```bash
cd playground/01-python-basics/03-modules-packages
python b1_main.py
```

能输出合理结果；例如 `normalize("  a   b  ")` → `"a b"`。

---

### B2. 创建包结构 + `__init__.py` 再导出

创建：

```text
03-modules-packages/
└── chatkit/
    ├── __init__.py
    ├── messages.py
    └── formatters.py
```

要求：

1. `messages.py`：`create_message(role, content) -> dict`
2. `formatters.py`：`format_message(msg: dict) -> str`  
   返回形如 `[user] hello`
3. `chatkit/__init__.py` 再导出 `create_message`、`format_message`，并定义 `__all__`
4. 另写 `b2_main.py`，只允许：

```python
from chatkit import create_message, format_message
```

**验收**：`python b2_main.py` 打印至少一行格式化消息；`from chatkit import *` 时（可自行试）应只暴露你在 `__all__` 里声明的名字（不必写测试框架，手工确认即可）。

---

### B3. 子包 + 绝对导入打通 runtime

扩展为：

```text
chatkit/
├── __init__.py
├── messages.py
├── formatters.py
├── runtime.py
└── tools/
    ├── __init__.py
    ├── search.py
    └── calc.py
```

要求：

1. `tools/search.py`：`search(query: str, top_k: int = 3) -> list[str]`
2. `tools/calc.py`：`add(a: float, b: float) -> float`
3. `tools/__init__.py` 导出 `search`、`add`
4. `runtime.py` 使用**绝对导入**：

```python
from chatkit.messages import create_message
from chatkit.tools import search, add
```

实现 `run_demo(query: str) -> list[dict]`：

- 创建一条 user 消息
- 调用 `search` 与 `add(1, 2)`
- 追加一条 assistant 消息，content 里包含检索条数与加法结果
- 返回消息列表

5. `b3_main.py` 调用 `run_demo` 并打印

**验收**：在 `03-modules-packages/` 下 `python b3_main.py` 成功运行。

---

### B4. `__name__ == "__main__"` 入口

给 `chatkit/tools/search.py` 增加主程序入口：直接运行该模块时，打印一次 `search("agent")` 的结果；但被 import 时不自动打印。

用两种方式都验证一次：

```bash
# 1）作为模块运行（推荐）
python -m chatkit.tools.search

# 2）被 import 时不应触发 demo 打印
python -c "from chatkit.tools.search import search; print('imported ok')"
```

**验收**：方式 1 有 demo 输出；方式 2 只有 `imported ok`（不应再打印 search demo，或至少你能区分并说明行为是否符合预期）。

> Windows PowerShell 同样可在该目录执行上述命令。

---

## 进阶题（建议至少做 1 题）

### A1. 相对导入小实验（理解报错）

在 `chatkit/tools/search.py` 中临时增加一行相对导入（例如从同包导入 `add`）：

```python
from .calc import add
```

并写一个仅供实验的函数 `search_and_add(query: str) -> dict`。

然后对比：

1. `python -m chatkit.tools.search`（或通过 `b3_main` 间接导入）——应成功  
2. 若你在 `chatkit/tools/` 目录里直接 `python search.py`——大概率失败

把你看到的报错信息抄到 `notes_a1.md`（几行即可），并用自己的话解释：**为什么直接跑会挂，用 `-m` 或包外入口就正常。**

**验收**：有笔记文件；能说清 “parent package” 相关原因。

---

### A2. 标准库拼装小脚本

新建 `a2_snapshot.py`：

1. 用 `pathlib` + `json` + `datetime` 生成一个快照文件 `snapshot.json`
2. 内容包含：
   - `created_at`：UTC ISO 时间
   - `demo_messages`：来自 `chatkit` 的 1～2 条消息
   - `search_preview`：`search("RAG", top_k=2)` 的结果
3. 写完后再读回打印 `created_at`

**验收**：生成文件可被 JSON 解析；脚本可重复运行覆盖写入。

---

## 挑战题（可选）

### C1. 迷你工具注册包（贴近 Agent）

在 `chatkit` 下新增 `registry.py`：

```python
from collections.abc import Callable

ToolFn = Callable[..., object]

def register(name: str, fn: ToolFn) -> None: ...
def get(name: str) -> ToolFn: ...
def list_tools() -> list[str]: ...
def call(name: str, **kwargs) -> dict: ...
```

要求：

1. `chatkit/tools/__init__.py` 在导入时把 `search`、`add` 注册进 registry（注意避免笨重副作用；可接受学习阶段的简单做法）
2. `c1_main.py` 演示：`list_tools()`、成功 `call`、调用未知工具返回 `ok=False`
3. 包的公共 API 依然清晰：外部不必深入知道内部文件名

**验收**：`python c1_main.py` 能看懂工具列表与调用结果。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成，命令行实际跑通
- [ ] 能手绘（或口述）`chatkit/` 目录树，并说明谁导入谁
- [ ] 能解释 `ModuleNotFoundError` / 相对导入报错的常见原因
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

`normalize` 可用 `" ".join(text.split())`。  
`clip` 注意 `max_len` 小于 3 时的边界；学习阶段可要求 `max_len >= 3`。

</details>

<details>
<summary>B2 提示</summary>

```python
# chatkit/__init__.py
from chatkit.messages import create_message
from chatkit.formatters import format_message

__all__ = ["create_message", "format_message"]
```

也可在包内用相对导入：`from .messages import create_message`。

</details>

<details>
<summary>B3 提示</summary>

确保每个包目录都有 `__init__.py`。  
在 `03-modules-packages/` 下运行，而不是在更深的子目录运行，否则可能找不到 `chatkit`。

</details>

<details>
<summary>B4 提示</summary>

```python
if __name__ == "__main__":
    print(search("agent"))
```

`python -m chatkit.tools.search` 的当前工作目录应是包含 `chatkit` 的那一层。

</details>

<details>
<summary>A1 思路</summary>

直接 `python search.py` 时，`__package__` 往往是空的，相对导入没有“父母包”。  
`python -m chatkit.tools.search` 会按包上下文加载。把报错原文记下来最有价值。

</details>

<details>
<summary>A2 思路</summary>

`datetime.now(timezone.utc).isoformat()`；`Path("snapshot.json").write_text(...)`。消息用 `create_message` 生成，保持练习连贯。

</details>

<details>
<summary>C1 思路</summary>

模块级 dict 做 registry；`call` 里 `fn(**kwargs)` 并捕获异常。注册放在 `tools/__init__.py` 末尾即可。注意避免 `registry` 与 `tools` 循环导入：可让 `registry` 不导入 tools，只被 tools 导入。

</details>
