# 练习：项目结构

> 对应文档：[`docs/03-engineering/01-project-structure.md`](../../docs/03-engineering/01-project-structure.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题；包边界与 `python -m` 建议动手踩一遍。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：确认包、导入、`python -m` 手感；再搭完整骨架会顺很多。
4. 建议代码目录：

```text
playground/03-engineering/01-project-structure/my-agent/
```

5. 先自己做完，再看文末「提示与参考答案」。教学 LLM 用 **`EchoLLM`**（`complete(prompt) -> str`），**勿命名为 FakeLLM**（见 `docs/CONVENTIONS.md`）。
6. Python ≥ 3.11；注解用 `list[str]`、`str | None`。

---

## 热身题（建议先做）

> 每题几分钟。不必搭完整项目；在 playground 里确认「包能 import、能 `-m` 跑」即可。

### W1. 空包也能 `import`

**给定**：在练习目录建最小包：

```text
probe/
└── app/
    └── __init__.py
```

**要求**：在 `probe/` 根执行：

```bash
python -c "import app; print(app.__name__)"
```

**验收**：输出 `app`，且无 `ModuleNotFoundError`。

---

### W2. `python -m` vs 直接跑脚本

**给定**：`app/hello.py`：

```python
def main() -> None:
    print("hello-from-package")


if __name__ == "__main__":
    main()
```

**要求**：

1. 在包根执行 `python -m app.hello`
2. 再试一次「进到 `app/` 里直接 `python hello.py`」，观察工作目录 / 导入习惯差异（写一句笔记即可）

**验收**：`-m` 路径能打印 `hello-from-package`；笔记里写清「入口应以包根为 cwd」。

---

### W3. 依赖方向一句话

**给定**：文档里的分层：`main` / `agents` / `tools` / `services` / `models`。

**要求**：用一句话写出允许的依赖方向（谁可以 import 谁），并点名一个**禁止**的反向依赖例子。

**验收**：能说出类似「上层组装 → 下层库；`tools` 不 import `main`」。

---

## 基础题（必做）

### B1. 搭骨架

在 `playground/03-engineering/01-project-structure/my-agent/` 下创建：

```text
my-agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── llm.py
│   └── models/
│       ├── __init__.py
│       └── message.py
├── tests/
│   └── test_smoke.py
├── .env.example
└── README.md
```

**验收**：目录存在；`README.md` 用约 5 行说明如何进入目录、如何运行（至少写 `python -m app.main`）。

---

### B2. 实现最小可运行链路

按文档综合例子实现（可照文档骨架，但要自己敲一遍）：

1. `models/message.py`：`create_message(role: str, content: str) -> dict`
2. `tools/search.py`：`search(query: str, top_k: int = 3) -> list[str]`，返回形如 `doc:{query}:{i}` 的列表
3. `services/llm.py`：`EchoLLM.complete(prompt: str) -> str`，返回 `f"ECHO: {prompt}"`
4. `config.py`：`Settings.from_env()`，至少读取 `APP_MAX_STEPS`（默认 `8`）
5. `main.py`：读配置 → 调 `search` → 调 `EchoLLM.complete` → 打印结果（B2 阶段编排可先写在 `main`，A1 再拆）

**验收**：在 `my-agent/` 根执行：

```bash
python -m app.main
```

成功打印一行以 `ECHO:` 开头的结果；且能看到 `docs=[...]` 一类检索痕迹。

---

### B3. 包边界检查（书面）

在 `b3_notes.md`（放在 `my-agent/` 下）画出依赖方向：

- 谁 import 谁（至少覆盖 `main`、`tools`、`services`、`models`、`config`）
- 你刻意避免的反向依赖（至少写 1 条，例如 `tools` 不 import `main`）

**验收**：有笔记；用全文搜索确认 `tools/` 下没有 `import app.main` 或 `from app.main`。

---

### B4. `.env.example`

写入至少：

```text
APP_MAX_STEPS=
APP_API_KEY=
```

（值为空即可。）并在 README 说明：**不要提交真实 `.env`**。

**验收**：文件存在且无真实密钥；README 有一句「密钥不进仓库」。

---

## 进阶题（建议至少做 1 题）

### A1. 增加 `agents/runner.py`

把「拼 prompt + 调 search + 调 llm」从 `main` 挪到 `AgentRunner`：

```python
class AgentRunner:
    def __init__(self, llm, tools, max_steps: int = 8) -> None: ...
    def run(self, question: str) -> str: ...
```

`main` 只负责：`Settings.from_env()`、构造依赖、调用 `agent.run(...)`、打印。

可选：用 `Protocol` 描述 `LLMLike.complete`，让 `agents` **不** import 具体的 `EchoLLM`。

**验收**：`python -m app.main` 仍可跑；`main.py` 不再直接拼业务 prompt（或明显变薄）。

---

### A2. smoke test

`tests/test_smoke.py` 至少断言：

```python
from app.tools.search import search

def test_search_non_empty() -> None:
    assert search("x")  # 非空 list
    assert isinstance(search("x"), list)
```

下一章再系统学 pytest；这里能 `pytest -q` 跑过更佳。

**验收**：在 `my-agent/` 根执行 `pytest -q`（需已装 pytest）至少 1 个用例通过。

---

## 挑战题（可选）

### C1. 扩展点说明

1. 按文档模板补全空包 `app/agents/`（若 A1 已建则跳过建包）。
2. 在 README 增加「扩展点」小节：说明你准备把 **memory** / **router** 放在哪一层，以及为什么不塞进 `tools/`。

**验收**：README 有扩展点；分层理由能自洽（不必写代码实现 memory）。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W3 先做完
- [ ] **通过线**：B1～B4 完成且 `python -m app.main` 可跑
- [ ] 能口述：`main` 只组装、库代码可测、配置集中、密钥不进仓
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给**完整参考**（含目录树、关键文件全文、命令）。答案不是唯一写法，能通过验收、边界清晰即可。

### W1 参考答案

```bash
mkdir -p probe/app   # Windows 可用 New-Item / 资源管理器
# 创建空文件 probe/app/__init__.py
cd probe
python -c "import app; print(app.__name__)"
# 期望：app
```

### W2 参考答案

```python
# app/hello.py
def main() -> None:
    print("hello-from-package")


if __name__ == "__main__":
    main()
```

```bash
# 在含 app/ 的包根：
python -m app.hello
```

笔记示例：`python -m` 把包根放进 `sys.path` 逻辑更稳；钻进子目录直接跑脚本容易让「相对导入 / 找包」变脆。习惯：**永远在项目根用 `-m` 启入口**。

### W3 参考答案

允许方向大致是：

```text
main → agents / config / services / tools / models
agents → tools / services / models / config（按需）
tools / services → models（可选）
tests → 任意被测库代码
```

禁止例子：`tools.search` import `app.main`；或 `models` import `agents`（数据层被编排反向拖住）。

---

### B1 思路 + 参考答案

**思路**

1. 先建空文件与 `__init__.py`，再填实现——避免目录漏建。
2. README 写「cwd + 命令」比写长篇教程更重要。

**参考：目录树（创建后应存在）**

```text
my-agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── llm.py
│   └── models/
│       ├── __init__.py
│       └── message.py
├── tests/
│   └── test_smoke.py
├── .env.example
└── README.md
```

**参考：`README.md`（约 5 行）**

```markdown
# my-agent

1. `cd` 到本目录（含 `app/` 的那一层）
2. 建议使用虚拟环境（见依赖章）
3. 运行：`python -m app.main`
4. 不要提交真实 `.env`；只提交 `.env.example`
5. 测试：`pytest -q`（需已安装 pytest）
```

---

### B2 思路 + 参考答案

**思路**

1. 每一层只做一件事：`models` 造 dict，`tools` 假检索，`services` 假 LLM，`config` 读环境变量，`main` 组装。
2. `EchoLLM` 命名对齐课程约定；返回字符串便于本章打印验收。
3. 启动方式固定为 `python -m app.main`，不要依赖「碰巧在某目录」。

**参考：关键文件完整内容**

```python
# app/__init__.py
# 可为空
```

```python
# app/config.py
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_steps: int = 8

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(max_steps=int(os.getenv("APP_MAX_STEPS", "8")))
```

```python
# app/models/__init__.py
```

```python
# app/models/message.py
def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}
```

```python
# app/tools/__init__.py
```

```python
# app/tools/search.py
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]
```

```python
# app/services/__init__.py
```

```python
# app/services/llm.py
class EchoLLM:
    """教学用同步回声模型；勿改名为 FakeLLM。"""

    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"
```

```python
# app/main.py  —— B2 阶段：编排暂放 main；A1 再拆到 AgentRunner
from app.config import Settings
from app.models.message import create_message
from app.services.llm import EchoLLM
from app.tools.search import search


def main() -> None:
    settings = Settings.from_env()
    question = "what is RAG"
    _ = create_message("user", question)
    docs = search(question, top_k=3)
    llm = EchoLLM()
    # max_steps 先占位，证明配置已读到
    _ = settings.max_steps
    print(llm.complete(f"q={question}; docs={docs}"))


if __name__ == "__main__":
    main()
```

**命令与期望**

```bash
cd my-agent
python -m app.main
```

期望类似：

```text
ECHO: q=what is RAG; docs=['doc:what is RAG:0', 'doc:what is RAG:1', 'doc:what is RAG:2']
```

可用断言自检（可选脚本）：

```python
from app.tools.search import search
from app.services.llm import EchoLLM
from app.config import Settings

assert search("x", top_k=2) == ["doc:x:0", "doc:x:1"]
assert EchoLLM().complete("hi").startswith("ECHO:")
assert Settings.from_env().max_steps >= 1
```

---

### B3 思路 + 参考答案

**思路**

依赖只允许「组装层 → 库层」。库层互不拖入口；测试可以 import 库，但业务不 import 测试。

**参考：`b3_notes.md`**

```markdown
# 包边界笔记

## 依赖方向（箭头 = import）

```text
main ----------> config
main ----------> services.llm (EchoLLM)
main ----------> tools.search
main ----------> models.message   （若 main 直接用）
agents.runner -> models / tools / (Protocol 描述的 llm)
tests ---------> tools / models / ...
```

## 刻意避免的反向依赖

1. `tools/*` 绝不 import `app.main`（工具是库，入口是组装）
2. `models/*` 不 import `agents`（数据结构保持纯）
3. `services/llm.py` 不 import `agents.runner`（避免环）

## 自检

在仓库内搜索：`from app.main` / `import app.main` —— 业务包内应为 0 命中。
```

---

### B4 思路 + 参考答案

**思路**

`.env.example` 只声明「需要哪些键」；真值留在本机未跟踪的 `.env`。README 写一句防呆即可。

**参考：`.env.example`**

```text
APP_MAX_STEPS=
APP_API_KEY=
```

**README 追加一句**

```markdown
配置：复制 `.env.example` 为 `.env` 后填写；**切勿把含真实密钥的 `.env` 提交进 git**。
```

---

### A1 思路 + 参考答案

**思路**

1. `AgentRunner.run` 承担编排；`main` 只 new 对象。
2. 用 `Protocol` 可让 agents 不依赖具体 `EchoLLM` 类（建议掌握）。

**参考实现**

```python
# app/agents/__init__.py
```

```python
# app/agents/runner.py
from collections.abc import Callable, Protocol

from app.models.message import create_message


class LLMLike(Protocol):
    def complete(self, prompt: str) -> str: ...


class AgentRunner:
    def __init__(
        self,
        llm: LLMLike,
        tools: list[Callable[..., list[str]]],
        max_steps: int = 8,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def run(self, question: str) -> str:
        _ = create_message("user", question)
        docs = self.tools[0](question)
        _ = self.max_steps  # 后续真 Agent 循环再用
        return self.llm.complete(f"q={question}; docs={docs}")
```

```python
# app/main.py
from app.agents.runner import AgentRunner
from app.config import Settings
from app.services.llm import EchoLLM
from app.tools.search import search


def main() -> None:
    settings = Settings.from_env()
    agent = AgentRunner(
        llm=EchoLLM(),
        tools=[search],
        max_steps=settings.max_steps,
    )
    print(agent.run("what is RAG"))


if __name__ == "__main__":
    main()
```

```bash
python -m app.main
```

---

### A2 思路 + 参考答案

**思路**

smoke 只锁「主路径没碎」：`search` 返回非空。不测 LLM 文采，不打外网。

**参考：`tests/test_smoke.py`**

```python
from app.tools.search import search


def test_search_non_empty() -> None:
    result = search("x")
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0].startswith("doc:x:")
```

```bash
cd my-agent
pip install pytest   # 或 uv add --dev pytest
pytest -q
```

---

### C1 思路 + 参考答案

**思路**

memory / router 属于「编排与状态」，更靠近 `agents/`；`tools/` 只放可调用动作。

**参考：README「扩展点」**

```markdown
## 扩展点

- **memory**：计划放在 `app/agents/memory.py` 或未来 `app/memory/`，由 `AgentRunner` 读写；不放进 `tools/`（记忆不是「模型可点名调用的外部动作」的唯一形态，避免和 search 混层）。
- **router**：计划放在 `app/agents/router.py`，决定下一步调哪个 tool / 是否结束；仍由 `main` 注入依赖。
- **新工具**：只新增 `app/tools/*.py` 并在组装处注册，尽量不改 `models`。
```

---

### 本章速查

| 主题 | 记住 |
|------|------|
| 布局 | `app/` + `tests/` + `.env.example` + README |
| 入口 | `python -m app.main` |
| LLM 教学名 | `EchoLLM`，不是 FakeLLM |
| 边界 | 入口组装；库可测；禁止 tools→main |
