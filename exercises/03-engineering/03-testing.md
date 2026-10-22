# 练习：测试（pytest）

> 对应文档：[`docs/03-engineering/03-testing.md`](../../docs/03-engineering/03-testing.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：pytest 发现规则、断言、`raises`、fixture、测什么不测什么。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/03-engineering/03-testing/
├── app/
│   ├── __init__.py
│   ├── textutil.py
│   └── messages.py
└── tests/
    ├── test_textutil.py
    └── test_messages.py
```

4. 先安装：`pip install pytest` 或 `uv add --dev pytest`。
5. 教学假模型用 **`EchoLLM`**（同步 `complete(prompt) -> str`），**勿叫 FakeLLM**。模块 09 起的 async FakeLLM 契约本章不要求。
6. Python ≥ 3.11；先自己做完再看文末答案。

---

## 热身题（建议先做）

### W1. 空跑 pytest

**要求**：在项目根执行 `pytest -q`，确认命令可用。

**验收**：若尚无测试，看到 `no tests ran` 也算成功（证明 pytest 已装对）。

---

### W2. 最小断言

**给定**：

```python
def add(a: int, b: int) -> int:
    return a + b
```

**要求**：写 `tests/test_add.py` 含 `test_add_basic`，断言 `add(2, 3) == 5`。

**验收**：`pytest -q` 通过。

---

### W3. 命名约定速记

**要求**：写出 pytest 默认会收集的文件名与函数名模式各一个例子。

**验收**：文件如 `test_*.py`；函数如 `test_*`。

---

## 基础题（必做）

### B1. 第一个业务测试

实现 `app/textutil.py`：

```python
def normalize(text: str) -> str:
    """strip，并把连续空白压缩成单个空格。"""

def clip(text: str, max_len: int) -> str:
    """
    若 len(text) <= max_len：原样返回。
    否则返回前 max_len-3 个字符 + '...'（总长度 == max_len）。
    """
```

写 `tests/test_textutil.py` 至少 2 个测试（建议各测一个函数）。

**验收**：`pytest -q` 全绿。

---

### B2. `pytest.raises`

为 `clip` 增加规则：`max_len < 3` 时抛 `ValueError`（信息可自定，建议含 `"max_len"`）。

写测试用 `pytest.raises` 断言该异常。

**验收**：对应用例存在且通过；合法 `max_len` 仍可用。

---

### B3. fixture + `truncate_messages`

实现 `app/messages.py` 中的 `truncate_messages`（逻辑对齐文档例子）：

- 空列表 → `[]`
- 若首条是 `system`：保留它，再保留最近 `max_messages` 条非 system 历史
- 否则：直接保留最近 `max_messages` 条

写 fixture 提供样本 `messages`，至少 1 个测试使用该 fixture。

**验收**：`pytest tests/test_messages.py -q` 通过。

---

### B4. 测什么不测什么（书面）

在 `b4_notes.md` 列出：

- 3 件「Agent 项目里优先单测」的事 + 各一句原因
- 2 件「不该塞进单测」的事 + 各一句原因

**验收**：有完整笔记，不是关键词列表。

---

## 进阶题（建议至少做 1 题）

### A1. 参数化

对 `normalize` 或 `clip` 用 `@pytest.mark.parametrize` 写 **3 组以上**用例。

**验收**：参数化测试能跑；失败时应能看出是哪一组参数。

---

### A2. EchoLLM 测试

```python
class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"echo: {prompt}"


def ask(llm: EchoLLM, prompt: str) -> str:
    return llm.complete(prompt)
```

测试：`ask(EchoLLM(), "hi")` 返回值包含 `"hi"`。不要打真实网络。

**验收**：单测绿；代码中名称是 `EchoLLM`。

---

## 挑战题（可选）

### C1. mock 外部调用

写一个函数，内部调用可替换的 `http_post(url, json)`（可放在同一模块）。  
用 `unittest.mock.patch` 替换返回值，断言：

1. 返回被正确解析/转发
2. `http_post` 被调用了预期 URL

**验收**：不联网；测试稳定通过。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W3
- [ ] **通过线**：B1～B4 完成，`pytest` 绿
- [ ] 能口述：纯逻辑优先测；真 LLM/真 HTTP 默认不进单测
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

### W1 参考答案

```bash
pip install pytest
pytest -q
# no tests ran in 0.0Xs  ← 也可接受
```

### W2 参考答案

```python
# app/calc.py（或直接写在 test 文件旁的模块）
def add(a: int, b: int) -> int:
    return a + b
```

```python
# tests/test_add.py
from app.calc import add


def test_add_basic() -> None:
    assert add(2, 3) == 5
```

### W3 参考答案

- 文件：`test_textutil.py`（模式 `test_*.py`）
- 函数：`test_clip_short`（模式 `test_*`）
- 反例：`tools_tests.py`、`check_add` 默认不会被收集

---

### B1 思路 + 参考答案

**思路**

1. `normalize`：先 `strip`，再把空白段用 `" ".join(text.split())` 压缩。
2. `clip`：短文本直接返回；长文本保证总长为 `max_len` 且以 `...` 结尾。

**参考：`app/textutil.py`**

```python
def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def clip(text: str, max_len: int) -> str:
    if max_len < 3:
        raise ValueError("max_len must be >= 3")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
```

> 注：B1 可先不写 `max_len < 3` 分支，B2 再补；上面给出最终版以便一次粘贴。

**参考：`tests/test_textutil.py`（B1 最小集）**

```python
from app.textutil import clip, normalize


def test_normalize_compresses_whitespace() -> None:
    assert normalize("  hello   world  ") == "hello world"


def test_clip_short_unchanged() -> None:
    assert clip("hi", 10) == "hi"


def test_clip_long_adds_ellipsis() -> None:
    assert clip("abcdefghij", 5) == "ab..."
    assert len(clip("abcdefghij", 5)) == 5
```

```bash
pytest -q
```

---

### B2 思路 + 参考答案

**思路**

边界尽早 `raise`；测试用 `with pytest.raises(ValueError):` 包住调用。

**参考测试增量**

```python
import pytest
from app.textutil import clip


def test_clip_rejects_small_max_len() -> None:
    with pytest.raises(ValueError) as exc_info:
        clip("hello", 2)
    assert "max_len" in str(exc_info.value).lower()
```

**断言自检**

```python
import pytest
from app.textutil import clip

assert clip("abcd", 4) == "abcd"
with pytest.raises(ValueError):
    clip("abcd", 1)
```

---

### B3 思路 + 参考答案

**思路**

1. 先处理空列表。
2. 首条 system 时：`[system] + rest[-max_messages:]`。
3. fixture 返回新列表，测试里避免 `pop` 污染（或改用工厂）。

**参考：`app/messages.py`**

```python
def truncate_messages(
    messages: list[dict],
    max_messages: int = 3,
) -> list[dict]:
    """清除过长历史：可选保留首条 system，再留最近 max_messages 条。"""
    if not messages:
        return []
    if messages[0].get("role") == "system":
        return [messages[0]] + messages[1:][-max_messages:]
    return messages[-max_messages:]
```

**参考：`tests/test_messages.py`**

```python
import pytest
from app.messages import truncate_messages


@pytest.fixture
def long_dialog() -> list[dict]:
    return [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": str(i)} for i in range(5)
    ]


def test_keeps_system_and_last_n(long_dialog: list[dict]) -> None:
    out = truncate_messages(long_dialog, max_messages=2)
    assert out[0]["role"] == "system"
    assert [m["content"] for m in out[1:]] == ["3", "4"]


def test_empty() -> None:
    assert truncate_messages([]) == []


def test_without_system() -> None:
    msgs = [{"role": "user", "content": str(i)} for i in range(4)]
    out = truncate_messages(msgs, max_messages=2)
    assert [m["content"] for m in out] == ["2", "3"]
```

```bash
pytest tests/test_messages.py -q
```

---

### B4 思路 + 参考答案

**参考：`b4_notes.md`（完整作答）**

```markdown
# B4：测什么 / 不测什么

## 优先单测（3）

1. **消息截断 / 清洗（如 truncate_messages、normalize）**  
   原因：纯函数、边界多（空列表、system、N 大小），一改就容易静默坏掉，且不依赖网络。

2. **工具参数解析 / 校验（JSON schema、必填字段）**  
   原因：Agent 把模型输出转成 kwargs，错了会「看起来在跑但工具总失败」；单测能锁住契约。

3. **重试分类器（哪些 status / 异常可重试）**  
   原因：规则稳定、输入离散；测真 HTTP 波动大，测纯函数稳定。

## 不该塞进单测（2）

1. **真实 LLM 是否「回答得漂亮」**  
   原因：非确定性、贵、慢；应放到评测集 / Eval harness，并用 Fake/Echo 测编排结构。

2. **第三方 SDK 内部实现或完整外网联调**  
   原因：脆弱且慢；单测应 mock / 注入假客户端，联调留给集成测试并默认不进 CI 必跑集。
```

---

### A1 思路 + 参考答案

```python
import pytest
from app.textutil import clip, normalize


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("  a  b  ", "a b"),
        ("\thello\n", "hello"),
        ("x", "x"),
        ("", ""),
    ],
)
def test_normalize_param(text: str, expected: str) -> None:
    assert normalize(text) == expected


@pytest.mark.parametrize(
    ("text", "n", "expected"),
    [
        ("hi", 10, "hi"),
        ("abcdefghij", 5, "ab..."),
        ("abcd", 4, "abcd"),
    ],
)
def test_clip_param(text: str, n: int, expected: str) -> None:
    assert clip(text, n) == expected
```

---

### A2 思路 + 参考答案

**思路**

把不确定性关在门外：注入 Echo，只断言「回声包含输入」。名称用 `EchoLLM`，对齐 CONVENTIONS。

```python
# app/llm_echo.py
class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"echo: {prompt}"


def ask(llm: EchoLLM, prompt: str) -> str:
    return llm.complete(prompt)
```

```python
# tests/test_llm_echo.py
from app.llm_echo import EchoLLM, ask


def test_ask_echoes() -> None:
    out = ask(EchoLLM(), "hi")
    assert "hi" in out
    assert out.startswith("echo:")
```

---

### C1 思路 + 参考答案

```python
# app/client.py
from typing import Any, Callable


def http_post(url: str, json: dict[str, Any]) -> dict[str, Any]:
    raise RuntimeError("network disabled in unit tests")


def create_ticket(
    title: str,
    *,
    poster: Callable[..., dict[str, Any]] = http_post,
) -> str:
    resp = poster("https://api.example.com/tickets", {"title": title})
    return str(resp["id"])
```

```python
# tests/test_client.py
from unittest.mock import patch

from app.client import create_ticket


def test_create_ticket_uses_poster() -> None:
    with patch("app.client.http_post") as mocked:
        mocked.return_value = {"id": "t-1"}
        ticket_id = create_ticket("bug")
        assert ticket_id == "t-1"
        mocked.assert_called_once_with(
            "https://api.example.com/tickets",
            {"title": "bug"},
        )
```

```bash
pytest tests/test_client.py -q
```

---

### 本章速查

| 主题 | 记住 |
|------|------|
| 发现规则 | `test_*.py` + `test_*` |
| 异常 | `pytest.raises` |
| 夹具 | `@pytest.fixture` |
| 假模型 | `EchoLLM`，勿叫 FakeLLM |
| 边界 | 单测锁纯逻辑；真模型进评测 |
