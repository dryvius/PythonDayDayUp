# 测试（pytest）

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/03-engineering/03-testing.md`](../../exercises/03-engineering/03-testing.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：学会用 pytest 给工具函数、解析逻辑、Agent 纯规则写自动化测试。
- **原则**：先测「纯逻辑与边界」；LLM 真实调用放到集成/评测，不要全塞单元测试。

## 学习目标（学完应能做到）

1. 编写并运行 pytest 测试文件。
2. 使用断言、`pytest.raises`、基础 fixture。
3. 判断什么该测、什么不该测（尤其 Agent 场景）。
4. 会用参数化；了解 mock 与覆盖率/CI。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | pytest 基础、断言与 fixture、测什么不测什么 | 能为 tools/utils 写测试 |
| **建议掌握** | 参数化、mock 基础 | 会减少重复、隔离外部依赖 |
| **了解即可** | 覆盖率与 CI | 建立地图 |

---

## 1. 为什么要学

Agent 项目里最值得测的往往是：

```text
JSON 参数解析
消息截断 / 清洗
工具注册与路由
重试是否只对可重试错误生效
RAG 过滤与 Top-K
```

这些一改就容易静默坏掉。pytest 让你每次改完跑一遍就有底。

---

## 2. 必掌握：pytest 基础

### 2.1 安装与运行

```bash
pip install pytest
# 或
uv add --dev pytest

pytest
pytest tests/test_tools.py -q
```

约定：

- 文件名：`test_*.py` 或 `*_test.py`
- 函数名：`test_*`
- 放在 `tests/` 目录

### 2.2 最小例子

```python
# app/tools/calc.py
def add(a: float, b: float) -> float:
    return a + b
```

```python
# tests/test_calc.py
from app.tools.calc import add  # 需先 editable install 或 pytest pythonpath（见依赖章 §5.1）


def test_add():
    assert add(1, 2) == 3
```

### 2.3 断言

pytest 直接用 `assert`，失败时会做断言重写，显示左右值：

```python
assert normalize("  a  ") == "a"
assert "user" in roles
```

---

## 3. 必掌握：异常与 fixture

### 3.1 断言抛错

```python
import pytest
from app.tools.calc import divide


def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
```

带匹配：

```python
with pytest.raises(ValueError, match="empty"):
    create_message("user", "   ")
```

### 3.2 fixture：可复用准备工作

```python
import pytest


@pytest.fixture
def registry():
    return {"search": lambda query: [query]}


def test_has_search(registry):
    assert "search" in registry
```

fixture 也可以 yield 做清理（类似上下文管理器）。

---

## 4. 必掌握：测什么，不测什么

### 应该优先测

| 类型 | 例子 |
|------|------|
| 纯函数 | 清洗、截断、排序、合并 |
| 解析/校验 | JSON schema、工具参数 |
| 状态机规则 | max_steps、终止条件 |
| 错误分类 | retryable 判断 |

### 先不要死磕

| 类型 | 原因 |
|------|------|
| 真 LLM 输出文案 | 不稳定、贵、慢 |
| 完整多轮 Agent 主观质量 | 属于评测（Evaluation），后面专章 |
| 第三方库内部行为 | 相信库，测你的适配层即可 |

策略：

```text
单元测试：FakeLLM + 纯逻辑
集成测试：少量真 API（可选，标记 slow）
评测集：Agent 任务成功率（模块 12）
```

---

## 5. 建议掌握：参数化与 mock

### 5.1 参数化

```python
import pytest
from app.text import clip


@pytest.mark.parametrize(
    ("text", "n", "expected"),
    [
        ("hi", 10, "hi"),
        ("abcdefghij", 5, "ab..."),
    ],
)
def test_clip(text, n, expected):
    assert clip(text, n) == expected
```

### 5.2 mock 基础

当函数内部会打网络，单测可替换：

```python
from unittest.mock import patch


def test_call_llm_uses_client():
    with patch("app.services.llm.http_post", return_value={"text": "ok"}) as m:
        ...
        m.assert_called()
```

也可用 pytest-mock 插件。先会 `patch` 即可。

---

## 6. 了解即可：覆盖率与 CI

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

CI（GitHub Actions 等）里每次 PR 跑 `pytest`。  
覆盖率是参考不是KPI：别为了 100% 测无价值代码。

---

## 7. 常见坑

1. 测试依赖执行顺序（应用 fixture/工厂，不要靠全局可变状态）
2. 测到了实现细节，一重构测试全挂——优先测行为
3. 单测里真的去扣 LLM 额度
4. 断言无信息：多个断言可拆成多个 test

---

## 8. 综合小例子

```python
# app/messages.py
def truncate_messages(messages: list[dict], max_messages: int = 3) -> list[dict]:
    if not messages:
        return []
    if messages[0].get("role") == "system":
        return [messages[0]] + messages[1:][-max_messages:]
    return messages[-max_messages:]
```

```python
# tests/test_messages.py
from app.messages import truncate_messages


def test_keeps_system_and_last_n():
    msgs = [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": str(i)} for i in range(5)
    ]
    out = truncate_messages(msgs, max_messages=2)
    assert out[0]["role"] == "system"
    assert [m["content"] for m in out[1:]] == ["3", "4"]
```

---

## 9. 练习指引

[`exercises/03-engineering/03-testing.md`](../../exercises/03-engineering/03-testing.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能写并跑通 pytest
- [ ] 会 `raises` 与简单 fixture
- [ ] 能说出 Agent 里优先测什么

### 下一章

[`04-logging.md`](./04-logging.md) —— 用日志代替乱 `print`，为排障与可观测性打底。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[依赖与虚拟环境](./02-deps-venv.md)
- 下一章：[Logging](./04-logging.md)
