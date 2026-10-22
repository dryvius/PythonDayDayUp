# 练习：模块、包与导入系统

> 对应文档：[`docs/01-python-basics/03-modules-packages.md`](../../docs/01-python-basics/03-modules-packages.md)  
> 状态：`已完成出题`  
> 建议用时：70～110 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。本章以**搭包 + 跑通导入**为主，请在指定目录创建真实文件。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：先弄清 `import` / `from ... import` / `__name__`，再搭 `chatkit` 包会轻松很多。
4. 建议根目录：

```text
playground/01-python-basics/03-modules-packages/
```

5. 每做完一题，用命令行真正运行一次，不要只看代码「感觉没问题」。
6. 先自己做完，再看文末「提示与参考答案」。

---

## 热身题（建议先做）

> 热身可在同一目录用极小文件完成；不必一开始就搭完整包。

### W1. 最简单的 `import`

**给定**：同目录两个文件 `mathy.py` 与 `w1_main.py`。

**要求**：

1. `mathy.py` 定义 `def double(x: int) -> int: return x * 2`
2. `w1_main.py` 使用 `import mathy`，调用并打印结果

**验收**：

```bash
cd playground/01-python-basics/03-modules-packages
python w1_main.py
```

且 `mathy.double(21) == 42`。

---

### W2. `from ... import` 与别名

**给定**：复用 `mathy.py`。

**要求**：在 `w2_main.py` 里写 `from mathy import double as dup`，断言 `dup(3) == 6`。

**验收**：`python w2_main.py` 无报错。

---

### W3. `__name__` 打印观察

**给定**：在 `mathy.py` 末尾临时加：

```python
print("mathy __name__ =", __name__)
```

**要求**：分别执行 `python mathy.py` 与 `python -c "import mathy"`，观察两次 `__name__` 的差异，用一句话写结论。

**验收**：能说出「直接运行是 `__main__`，被 import 时是模块名」。

---

### W4. 标准库三件套摸一眼

**要求**：在 `w4_stdlib.py` 里各用一次：

- `pathlib.Path.cwd()`
- `json.dumps({"ok": True})`
- `datetime.datetime.now(datetime.timezone.utc).isoformat()`

**验收**：脚本可运行并打印三行可读输出。

---

### W5. 包目录最小骨架

**要求**：创建空包：

```text
tinykit/
└── __init__.py   # 可为空，或写 VERSION = "0.1.0"
```

再写 `w5_main.py`：`import tinykit` 并打印 `tinykit.VERSION`（若你写了）或 `tinykit.__file__`。

**验收**：`python w5_main.py` 能导入成功。

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

`b1_main.py` 使用 `import textkit`（不要 `from import *`），演示两次调用并打印结果。

**验收**：

```bash
cd playground/01-python-basics/03-modules-packages
python b1_main.py
```

例如 `normalize("  a   b  ")` → `"a b"`。

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

**要求**：

1. `messages.py`：`create_message(role, content) -> dict`
2. `formatters.py`：`format_message(msg: dict) -> str`，返回形如 `[user] hello`
3. `chatkit/__init__.py` 再导出 `create_message`、`format_message`，并定义 `__all__`
4. 另写 `b2_main.py`，只允许：

```python
from chatkit import create_message, format_message
```

**验收**：`python b2_main.py` 打印至少一行格式化消息；`from chatkit import *` 时只暴露 `__all__` 里声明的名字（手工确认即可）。

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

**要求**：

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

**验收**：方式 1 有 demo 输出；方式 2 只有 `imported ok`。

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

**要求**：

1. `chatkit/tools/__init__.py` 在导入时把 `search`、`add` 注册进 registry（学习阶段可接受简单副作用）
2. `c1_main.py` 演示：`list_tools()`、成功 `call`、调用未知工具返回 `ok=False`
3. 包的公共 API 依然清晰：外部不必深入知道内部文件名

**验收**：`python c1_main.py` 能看懂工具列表与调用结果。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W5 先做完
- [ ] **通过线**：B1～B4 全部完成，命令行实际跑通
- [ ] 能手绘（或口述）`chatkit/` 目录树，并说明谁导入谁
- [ ] 能解释 `ModuleNotFoundError` / 相对导入报错的常见原因
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。包结构题请按目录真正落盘后再跑。

### W1 参考答案

`mathy.py`：

```python
def double(x: int) -> int:
    return x * 2
```

`w1_main.py`：

```python
import mathy

assert mathy.double(21) == 42
print(mathy.double(21))
```

### W2 参考答案

```python
from mathy import double as dup

assert dup(3) == 6
print(dup(3))
```

### W3 参考答案

```python
# 直接 python mathy.py → __name__ == "__main__"
# import mathy        → __name__ == "mathy"
# 结论：用 if __name__ == "__main__": 区分「脚本入口」与「被导入」
```

### W4 参考答案

```python
import json
from datetime import datetime, timezone
from pathlib import Path

print(Path.cwd())
print(json.dumps({"ok": True}))
print(datetime.now(timezone.utc).isoformat())
```

### W5 参考答案

`tinykit/__init__.py`：

```python
VERSION = "0.1.0"
```

`w5_main.py`：

```python
import tinykit

print(tinykit.VERSION)
print(tinykit.__file__)
```

### B1 思路 + 参考答案

**思路**

1. `normalize`：`strip` 后再 `" ".join(text.split())` 压缩空白。
2. `clip`：若 `len(text) <= max_len` 原样返回；否则留给 `...` 三个字符，前面截断。
3. 学习阶段可约定 `max_len >= 3`。

**参考答案**

`textkit.py`：

```python
def normalize(text: str) -> str:
    """strip + 压缩连续空白为单空格。"""
    return " ".join(text.split())


def clip(text: str, max_len: int = 20) -> str:
    """超长则截断并加 ...，总长不超过 max_len。"""
    if max_len < 3:
        raise ValueError("max_len must be >= 3")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
```

`b1_main.py`：

```python
import textkit

assert textkit.normalize("  a   b  ") == "a b"
assert textkit.clip("abcdefghij", max_len=8) == "abcde..."
print(textkit.normalize("  hello   agent  "))
print(textkit.clip("这是一段比较长的工具描述文本", max_len=12))
```

### B2 思路 + 参考答案

**思路**

1. 包内模块各司其职：`messages` 负责结构，`formatters` 负责展示。
2. `__init__.py` 再导出，让调用方写 `from chatkit import ...`。
3. `__all__` 控制 `import *` 暴露面。

**参考答案**

`chatkit/messages.py`：

```python
def create_message(role: str, content: str) -> dict:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("content empty")
    return {"role": role, "content": cleaned}
```

`chatkit/formatters.py`：

```python
def format_message(msg: dict) -> str:
    return f"[{msg['role']}] {msg['content']}"
```

`chatkit/__init__.py`：

```python
from chatkit.messages import create_message
from chatkit.formatters import format_message

__all__ = ["create_message", "format_message"]
```

`b2_main.py`：

```python
from chatkit import create_message, format_message

msg = create_message("user", "  hello  ")
line = format_message(msg)
assert line == "[user] hello"
print(line)
```

### B3 思路 + 参考答案

**思路**

1. 每个包目录都要有 `__init__.py`。
2. 在「包含 `chatkit` 的那一层」运行，而不是进到子目录再跑。
3. `runtime` 用绝对导入，依赖关系一目了然。

**参考答案**

`chatkit/tools/search.py`：

```python
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


if __name__ == "__main__":
    # B4 也会用到这个入口
    print(search("agent"))
```

`chatkit/tools/calc.py`：

```python
def add(a: float, b: float) -> float:
    return a + b
```

`chatkit/tools/__init__.py`：

```python
from chatkit.tools.search import search
from chatkit.tools.calc import add

__all__ = ["search", "add"]
```

`chatkit/runtime.py`：

```python
from chatkit.messages import create_message
from chatkit.tools import search, add


def run_demo(query: str) -> list[dict]:
    messages = [create_message("user", query)]
    hits = search(query, top_k=3)
    total = add(1, 2)
    assistant = create_message(
        "assistant",
        f"检索到 {len(hits)} 条；1+2={total}",
    )
    messages.append(assistant)
    return messages
```

`b3_main.py`：

```python
from chatkit.runtime import run_demo

msgs = run_demo("RAG")
assert msgs[0]["role"] == "user"
assert "3" in msgs[1]["content"] or "检索到 3" in msgs[1]["content"]
for m in msgs:
    print(m)
```

### B4 思路 + 参考答案

**思路**

1. demo 代码放进 `if __name__ == "__main__":`，只有「作为主模块运行」才执行。
2. 推荐 `python -m chatkit.tools.search`，保证包上下文正确。

**参考答案**（`search.py` 末尾）：

```python
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


if __name__ == "__main__":
    print(search("agent"))
```

验证：

```bash
python -m chatkit.tools.search
python -c "from chatkit.tools.search import search; print('imported ok')"
```

### A1 思路 + 参考答案

**思路**

1. 相对导入需要「父母包」上下文（`__package__` 非空）。
2. 直接 `python search.py` 时常把文件当顶层脚本，`from .calc` 会报错。
3. `python -m chatkit.tools.search` 按包加载，相对导入可用。

**参考答案片段**（`search.py`）：

```python
from .calc import add


def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


def search_and_add(query: str) -> dict:
    return {"hits": search(query), "sum": add(1, 2)}


if __name__ == "__main__":
    print(search("agent"))
    print(search_and_add("agent"))
```

`notes_a1.md` 示例：

```text
直接 python search.py 报错类似：
ImportError: attempted relative import with no known parent package

原因：此时 __package__ 为空，相对导入不知道「同包」是谁。
用 python -m chatkit.tools.search 时，模块以 chatkit.tools.search 加载，相对导入正常。
```

### A2 思路 + 参考答案

**思路**

1. UTC 时间用 `datetime.now(timezone.utc).isoformat()`。
2. 消息与 search 复用 `chatkit`，保持练习连贯。
3. `Path.write_text` 覆盖写入即可。

**参考答案**

```python
import json
from datetime import datetime, timezone
from pathlib import Path

from chatkit import create_message
from chatkit.tools import search

payload = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "demo_messages": [
        create_message("user", "hello"),
        create_message("assistant", "hi"),
    ],
    "search_preview": search("RAG", top_k=2),
}

path = Path("snapshot.json")
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

loaded = json.loads(path.read_text(encoding="utf-8"))
print(loaded["created_at"])
assert len(loaded["search_preview"]) == 2
```

### C1 思路 + 参考答案

**思路**

1. 模块级 dict 做 registry；`call` 里 `fn(**kwargs)` 并捕获异常。
2. `registry` 不要反向 import `tools`，避免循环导入；由 `tools/__init__.py` 去 register。
3. 这是 Agent「工具注册表」的最小形态：名字 → 可调用对象。

**参考答案**

`chatkit/registry.py`：

```python
from collections.abc import Callable

ToolFn = Callable[..., object]

_REGISTRY: dict[str, ToolFn] = {}


def register(name: str, fn: ToolFn) -> None:
    _REGISTRY[name] = fn


def get(name: str) -> ToolFn:
    if name not in _REGISTRY:
        raise KeyError(name)
    return _REGISTRY[name]


def list_tools() -> list[str]:
    return sorted(_REGISTRY)


def call(name: str, **kwargs: object) -> dict:
    fn = _REGISTRY.get(name)
    if fn is None:
        return {"name": name, "ok": False, "result": f"unknown tool: {name}"}
    try:
        return {"name": name, "ok": True, "result": fn(**kwargs)}
    except Exception as exc:
        return {"name": name, "ok": False, "result": str(exc)}
```

`chatkit/tools/__init__.py`（注册副作用）：

```python
from chatkit.tools.search import search
from chatkit.tools.calc import add
from chatkit import registry

registry.register("search", search)
registry.register("add", add)

__all__ = ["search", "add"]
```

`c1_main.py`：

```python
import chatkit.tools  # noqa: F401  # 触发注册
from chatkit import registry

print("tools:", registry.list_tools())
print(registry.call("search", query="Agent", top_k=2))
print(registry.call("add", a=1, b=2))
print(registry.call("browse", url="x"))

assert "search" in registry.list_tools()
assert registry.call("browse")["ok"] is False
```
