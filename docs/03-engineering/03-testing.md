# 测试（pytest）

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有 Jest/Vitest 经验可更快；fixture 与「测什么」建议动手踩一遍）  
> 对应练习：[`exercises/03-engineering/03-testing.md`](../../exercises/03-engineering/03-testing.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：学会用 pytest 给工具函数、解析逻辑、Agent 纯规则写自动化测试。
- **原则**：先测「纯逻辑与边界」；LLM 真实调用放到集成/评测，不要全塞单元测试。
- **你的优势**：若你写过 Jest / Vitest，多数心智可直接迁移；重点盯住 pytest 的 `assert` 重写、fixture、以及 Agent 场景里「不该测什么」。

## 学习目标（学完应能做到）

1. 编写并运行 pytest 测试文件。
2. 使用断言、`pytest.raises`、基础 fixture。
3. 判断什么该测、什么不该测（尤其 Agent 场景）。
4. 会用参数化；了解 mock 与覆盖率/CI。
5. 完成课后练习，分清必掌握 / 建议掌握 / 了解即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | pytest 基础、断言与 fixture、测什么不测什么 | 能为 tools/utils 写测试 |
| **建议掌握** | 参数化、mock 基础 | 会减少重复、隔离外部依赖 |
| **了解即可** | 覆盖率与 CI | 建立地图 |

---

## 1. 为什么要学

#### 为什么 Agent 项目特别需要测试？

没有自动化测试时，改一行「消息截断」或「工具参数解析」，你只能靠人肉点一点：

```text
改了 truncate → 手动跑一遍对话 → 好像没坏
改了 retry 分类 → 忘了测超时场景 → 线上静默失败
```

Agent 项目里最值得测的往往是：

```text
JSON 参数解析
消息截断 / 清洗
工具注册与路由
重试是否只对可重试错误生效
RAG 过滤与 Top-K
```

这些一改就容易**静默坏掉**——程序不崩溃，但行为悄悄错了。pytest 让你每次改完跑一遍就有底。

#### 和「打印调试」差在哪？

| 方式 | 优点 | 缺点 |
| --- | --- | --- |
| `print` / 手动跑 | 上手快 | 不可重复、难覆盖边界、重构后容易忘验 |
| pytest | 可重复、可进 CI、失败信息清晰 | 要先写一点测试代码 |

可以先记一句：

> 测试不是「证明程序完美」，而是给关键行为上锁——改了相关代码，锁会响。

#### JS / Jest / Vitest 对照（心智地图）

| 概念 | Jest / Vitest | pytest |
| --- | --- | --- |
| 测试文件 | `*.test.ts` / `*.spec.ts` | `test_*.py` / `*_test.py` |
| 用例 | `test('...', () => {})` / `it(...)` | `def test_...():` |
| 断言 | `expect(x).toBe(y)` | `assert x == y` |
| 抛错 | `expect(() => fn()).toThrow()` | `with pytest.raises(...):` |
| 夹具/准备 | `beforeEach` / 自定义 fixture | `@pytest.fixture` |
| 参数化 | `test.each` / `it.each` | `@pytest.mark.parametrize` |
| 模拟 | `vi.mock` / `jest.mock` | `unittest.mock.patch` |

---

## 2. 必掌握：pytest 基础

这一节会刻意写细——后面异常、fixture、参数化都建立在「能跑起来第一个测试」之上。

### 2.1 安装与运行

#### 为什么单独装 pytest？

pytest 是**开发时**用的工具，不属于线上运行依赖。通常装进开发依赖（`--dev` / optional dependency），避免生产镜像多塞不需要的包。

#### 怎么写 / 怎么装

```bash
pip install pytest
# 或（推荐，与依赖章一致）
uv add --dev pytest
```

常用运行方式：

```bash
pytest                          # 自动发现当前目录下的测试
pytest tests/                   # 只跑 tests 目录
pytest tests/test_tools.py -q   # 单个文件，安静模式
pytest -k "clip"                # 名字里含 clip 的用例
pytest -x                       # 第一个失败就停
```

约定（pytest 默认发现规则）：

| 约定 | 要求 |
| --- | --- |
| 文件名 | `test_*.py` 或 `*_test.py` |
| 函数名 | `test_*` |
| 类名（可选） | `Test*`，且类里不要有 `__init__` |
| 目录 | 通常放 `tests/` |

#### 跑一下

假设项目根目录已有虚拟环境并装好 pytest：

```bash
pytest -q
```

若还没有任何测试，你会看到类似：

```text
no tests ran in 0.01s
```

这是正常的——说明 pytest 已能跑，只是还没写用例。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 文件叫 `tools_tests.py`（不符合约定） | 默认不被收集 |
| 函数叫 `check_add` 而不是 `test_add` | 不会被当成测试 |
| 没激活 venv 就跑 `pytest` | 可能用到系统全局的旧版本，或直接 `command not found` |
| 在错误目录跑 | 发现不到 `tests/`，以为「测试丢了」 |

#### JS / Jest / Vitest 对照

| Jest / Vitest | pytest |
| --- | --- |
| `npm test` / `npx vitest run` | `pytest` |
| `vitest run src/foo.test.ts` | `pytest tests/test_foo.py` |
| 配置里 `include: ['**/*.{test,spec}.ts']` | 文件名约定 + 可选 `pytest.ini` / `pyproject.toml` |

---

### 2.2 最小例子：从被测函数到绿灯

#### 为什么先写「加法」这种玩具？

不是因为 Agent 里真有 `add`，而是先把链路打通：

```text
被测代码（app/） → 测试代码（tests/） → 导入成功 → assert 通过
```

导入失败时，问题往往在「路径 / 包安装」，不在测试逻辑本身——依赖章 §5.1 讲过 editable install 与 `pythonpath`。

#### 怎么写

被测代码：

```python
# app/tools/calc.py
def add(a: float, b: float) -> float:
    return a + b
```

测试代码：

```python
# tests/test_calc.py
from app.tools.calc import add  # 需先 editable install 或 pytest pythonpath（见依赖章 §5.1）


def test_add():
    assert add(1, 2) == 3
```

若用 `pyproject.toml` 配路径（不装包也能导入）：

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

或 editable 安装：

```bash
pip install -e .
# / uv sync 后确保包可导入
```

#### 跑一下

```bash
pytest tests/test_calc.py -q
```

期望输出类似：

```text
.                                                                        [100%]
1 passed in 0.01s
```

一个 `.` = 一个通过的用例。

故意写错断言看失败长什么样：

```python
def test_add_wrong():
    assert add(1, 2) == 4  # 故意错
```

pytest 会重写 `assert`，直接显示左右值（不必手写「期望 / 实际」消息）：

```text
AssertionError: assert 3 == 4
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `from app...` 报 `ModuleNotFoundError` | 没装包 / 没配 `pythonpath` / 不在项目根跑 |
| 测试文件放在 `app/` 里且被当成包的一部分 | 容易和正式代码搅在一起；优先独立 `tests/` |
| 一个 `test_*` 里塞十个无关断言 | 失败时难定位；一个用例测一件事更清晰 |

#### JS / Jest / Vitest 对照

```javascript
// calc.test.ts（Vitest / Jest 风格）
import { describe, it, expect } from "vitest"
import { add } from "./calc"

describe("add", () => {
  it("adds two numbers", () => {
    expect(add(1, 2)).toBe(3)
  })
})
```

pytest 通常**不强制** `describe` 嵌套；用文件名 + 函数名组织即可。需要分组时可用类或 `pytest` 的 mark。

---

### 2.3 断言：直接用 `assert`

#### 为什么 pytest 不用 `self.assertEqual`？

unittest 风格要写：

```python
self.assertEqual(normalize("  a  "), "a")
```

pytest 鼓励原生 `assert`：失败时会做**断言重写（assertion introspection）**，把表达式拆开显示。对前端同学来说，这比 `expect(...).toBe(...)` 更「薄」——少一层 API，但失败信息仍然清楚。

#### 怎么写

```python
assert normalize("  a  ") == "a"
assert "user" in roles
assert len(messages) == 3
assert result is not None
assert abs(score - 0.85) < 1e-6  # 浮点别直接 ==
```

常见模式：

| 场景 | 写法 |
| --- | --- |
| 相等 | `assert a == b` |
| 同一性 | `assert a is b` / `assert a is None` |
| 成员 | `assert x in xs` |
| 近似浮点 | `assert a == pytest.approx(b)` |
| 多字段 | 先算中间结果，再分别 assert |

#### 跑一下

```python
# tests/test_normalize.py
from app.textutil import normalize


def test_normalize_strips_and_collapses():
    assert normalize("  hello   world  ") == "hello world"
```

```bash
pytest tests/test_normalize.py -v
```

`-v` 会打印每个用例名，适合刚上手时看清跑了哪些。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 浮点用 `==` 比分数 | 偶发失败（`0.1 + 0.2` 那类） |
| `assert a == b, "msg"` 写得很长却断言太宽 | 失败时仍不清楚哪个子字段错了 |
| 用 `print` 代替 assert | 测试永远「绿」，等于没测 |
| 断言实现细节（私有变量名） | 一重构全挂——优先断言**对外行为** |

#### JS / Jest / Vitest 对照

| Jest / Vitest | pytest |
| --- | --- |
| `expect(x).toBe(3)` | `assert x == 3`（或 `is` 视需求） |
| `expect(x).toEqual({a: 1})` | `assert x == {"a": 1}` |
| `expect(arr).toContain("user")` | `assert "user" in arr` |
| `expect(n).toBeCloseTo(0.85)` | `assert n == pytest.approx(0.85)` |
| `expect(x).toBeTruthy()` | `assert x`（注意空容器在 Python 为假） |

---

### 2.4 测试组织：一个行为一个名字

#### 为什么命名很重要？

失败报告里最先看到的是函数名。好名字等于自带文档：

```text
FAILED test_truncate_keeps_system_and_last_n
```

比 `FAILED test1` 有用得多。

#### 怎么写

推荐模式：`test_<动作或函数>_<场景或期望>`

```python
def test_clip_short_text_unchanged():
    ...


def test_clip_long_text_adds_ellipsis():
    ...


def test_clip_rejects_max_len_below_three():
    ...
```

目录示意（与项目结构章一致）：

```text
my-agent/
  app/
    tools/
      calc.py
    messages.py
  tests/
    test_calc.py
    test_messages.py
  pyproject.toml
```

#### 易错点

| 错法 | 更好做法 |
| --- | --- |
| `test_1` / `test_tmp` | 用场景命名 |
| 一个文件测整个项目 | 按模块拆 `test_*.py` |
| 测试之间共享可变全局列表并原地改 | 用 fixture 每次给新数据（见下一节） |

---

## 3. 必掌握：异常与 fixture

### 3.1 断言抛错：`pytest.raises`

#### 为什么要专门测异常？

合法输入要测；**非法输入的失败方式**同样是契约的一部分。例如：

- `max_len < 3` 必须立刻 `ValueError`，而不是静默截成怪串
- 空消息拒绝创建，而不是存进 `"   "`
- 除零要抛，而不是返回 `inf` 却被后面逻辑吞掉

若不测异常，重构时很容易把「该失败」改成「默默返回错误值」。

#### 怎么写

```python
import pytest
from app.tools.calc import divide


def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
```

带消息匹配（正则）：

```python
with pytest.raises(ValueError, match="empty"):
    create_message("user", "   ")
```

需要检查异常对象时：

```python
with pytest.raises(ValueError) as exc_info:
    clip("hi", max_len=1)

assert "max_len" in str(exc_info.value)
```

#### 跑一下

假设：

```python
# app/textutil.py
def clip(text: str, max_len: int) -> str:
    if max_len < 3:
        raise ValueError("max_len must be >= 3")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
```

```python
# tests/test_textutil.py
import pytest
from app.textutil import clip


def test_clip_rejects_small_max_len():
    with pytest.raises(ValueError, match="max_len"):
        clip("hello", max_len=2)
```

```bash
pytest tests/test_textutil.py::test_clip_rejects_small_max_len -q
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 不用 `raises`，直接调用指望它崩 | 若没抛，测试仍可能「通过」（你根本没断言） |
| `raises` 包住太多行 | 可能是**别的行**抛了同类异常，误判为通过 |
| `match` 写死整句文案 | 文案微调就挂；匹配关键词更稳 |
| 期望 `Exception` 太大 | 太宽，捕捉到意外错误也算过 |

#### JS / Jest / Vitest 对照

```javascript
import { expect, it } from "vitest"

it("rejects small maxLen", () => {
  expect(() => clip("hello", 2)).toThrow(/maxLen/i)
})
```

| Jest / Vitest | pytest |
| --- | --- |
| `expect(() => fn()).toThrow(Error)` | `with pytest.raises(Error): fn()` |
| `toThrow(/empty/)` | `raises(..., match="empty")` |
| `rejects`（async） | `pytest.raises` + `await`（async 测试见后文了解向） |

---

### 3.2 fixture：可复用的准备工作

#### 为什么需要 fixture？

真实测试里，准备数据往往比断言还长：

```python
messages = [
    {"role": "system", "content": "s"},
    {"role": "user", "content": "0"},
    # ... 重复粘贴
]
```

多个用例都要同一份「样本消息」时，复制粘贴会漂移。fixture 的作用类似 Jest 的 `beforeEach` + 返回值：把准备工作抽出来，测试函数通过**参数名**自动注入。

#### 怎么写

```python
import pytest


@pytest.fixture
def registry():
    return {"search": lambda query: [query]}


def test_has_search(registry):
    assert "search" in registry


def test_search_callable(registry):
    assert registry["search"]("py") == ["py"]
```

pytest 看到参数名 `registry`，就去找同名 fixture，调用后把返回值传进来。

带清理（类似 `try/finally` 或上下文管理器）：

```python
@pytest.fixture
def temp_workspace(tmp_path):
    # tmp_path 是 pytest 内置 fixture：每人用例一个临时目录
    db = tmp_path / "state.json"
    db.write_text("{}", encoding="utf-8")
    yield db
    # yield 之后是清理（本例临时目录会自动删，常可省略）
```

常用内置 fixture（先混个脸熟）：

| fixture | 用途 |
| --- | --- |
| `tmp_path` | 临时目录（`pathlib.Path`） |
| `capsys` | 捕获 stdout/stderr |
| `monkeypatch` | 改环境变量、属性（轻量 mock） |

#### 跑一下

```python
# tests/test_messages.py
import pytest
from app.messages import truncate_messages


@pytest.fixture
def sample_messages():
    return [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": str(i)} for i in range(5)
    ]


def test_keeps_system_and_last_n(sample_messages):
    out = truncate_messages(sample_messages, max_messages=2)
    assert out[0]["role"] == "system"
    assert [m["content"] for m in out[1:]] == ["3", "4"]
```

```bash
pytest tests/test_messages.py -q
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| fixture 里返回可变对象，又在测试里原地 `append` | 默认每个测试重新调用 fixture（function 作用域）通常安全；若改成 `scope="module"` 又可变，就会互相污染 |
| 参数名写错（`registrty`） | `fixture 'registrty' not found` |
| 用全局列表当「共享夹具」 | 顺序依赖、并行时更惨 |
| fixture 里打真网络 | 单测变慢变脆；网络应 mock / Fake |

作用域了解即可：默认 `function`（每个测试一次）。`module` / `session` 用于昂贵资源，但更要避免共享可变状态。

#### JS / Jest / Vitest 对照

```javascript
import { beforeEach, describe, it, expect } from "vitest"

describe("registry", () => {
  let registry
  beforeEach(() => {
    registry = { search: (q) => [q] }
  })

  it("has search", () => {
    expect(registry).toHaveProperty("search")
  })
})
```

| Jest / Vitest | pytest |
| --- | --- |
| `beforeEach(() => { ... })` | `@pytest.fixture` + 参数注入 |
| 工厂函数 `makeUser()` | fixture 或普通 helper 都行 |
| `afterEach` 清理 | fixture 里 `yield` 后清理 |

pytest 的「按参数名注入」是最大体感差异：不用在每个文件手写 `beforeEach`，同名即用。

---

### 3.3 fixture 进阶一点点（建议掌握边缘）

#### 为什么还要 `conftest.py`？

多个测试文件都要同一份 `sample_messages` 时，可以放到 `tests/conftest.py`——pytest 会自动发现，无需显式 import。

```python
# tests/conftest.py
import pytest


@pytest.fixture
def sample_messages():
    return [{"role": "system", "content": "s"}]
```

先会「本文件内 fixture」即可；项目变大再抽到 `conftest.py`。

---

## 4. 必掌握：测什么，不测什么

这一节决定你写测试时**值不值得**——比语法更重要。

### 4.1 应该优先测

#### 为什么这些优先？

它们通常是**纯函数或接近纯**：输入固定 → 输出可预期；跑得快；失败信号清晰。Agent 里真正拖垮可靠性的，经常是这些「不起眼」的规则，而不是模型文采。

| 类型 | 例子 | 为什么值得测 |
| --- | --- | --- |
| 纯函数 | 清洗、截断、排序、合并 | 边界多，改了就容易 silently wrong |
| 解析/校验 | JSON schema、工具参数 | 脏输入多，是安全与稳定性前线 |
| 状态机规则 | max_steps、终止条件 | 错了会空转或早停 |
| 错误分类 | retryable 判断 | 错了会狂重试或该重试却放弃 |
| 路由/注册表 | 工具名 → 调用函数 | 错了表现为「找不到工具」 |

#### 怎么写（思维方式）

对每个优先测的函数，至少想三组：

```text
1. 正常路径（happy path）
2. 边界（空列表、刚好截断点、max_steps=1）
3. 非法输入（该抛的要抛）
```

#### 跑一下（对照练习 B4 的思路）

书面列清单时，可以像这样：

```text
优先单测：
- truncate_messages：保留 system + 最近 N 条
- parse_tool_args：缺字段 / 类型错要失败
- is_retryable：Timeout 是，AuthError 否

不该塞单测：
- 「模型是否礼貌」——主观、非确定性
- 每次 CI 真调 OpenAI——贵、慢、不稳
```

### 4.2 先不要死磕

| 类型 | 原因 | 放到哪 |
| --- | --- | --- |
| 真 LLM 输出文案 | 不稳定、贵、慢 | 可选集成测试 / 人工抽查 |
| 完整多轮 Agent 主观质量 | 属于评测，不是单元断言 | Evaluation（模块 12） |
| 第三方库内部行为 | 你测的是库，不是你的代码 | 相信库；测适配层 |
| UI 文案像素级 | 成本高、易碎 | 视项目需要，非本章重点 |

#### 策略一张图

```text
单元测试：FakeLLM + 纯逻辑          ← 本章主场，CI 必跑
集成测试：少量真 API（可选，标记 slow）
评测集：Agent 任务成功率            ← 模块 12
```

约定提醒（见 [`docs/CONVENTIONS.md`](../CONVENTIONS.md)）：

- 单测与 CI **必须**可在 FakeLLM 下绿
- 真模型作为可选升级，不要挡合并

### 4.3 FakeLLM / EchoLLM：把不确定性关在门外

#### 为什么 Fake 比 mock 网络更适合入门？

对「调用 LLM 的那一层」，最干净的测法常常是：**注入一个假客户端**，而不是让单测穿透到 HTTP。

教学用同步示意（早期语言章风格，勿与生产 FakeLLM 契约混淆）：

```python
class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"echo: {prompt}"


def ask(llm: EchoLLM, prompt: str) -> str:
    return llm.complete(prompt)


def test_ask_echoes():
    assert "hi" in ask(EchoLLM(), "hi")
```

后面模块会统一到 async `complete(messages, tools=...) -> dict`；本章先建立「可注入、可假造」的习惯。

#### 易错点

| 错法 | 更好做法 |
| --- | --- |
| 单测里读真实 `OPENAI_API_KEY` 并请求 | Fake / mock；真调用标 `@pytest.mark.slow` 且默认跳过 |
| 断言模型返回「必须含某金句」 | 断言结构（有 `role`、有 `tool_calls` 字段）而非文采 |
| 为了覆盖率去测 `print` 样式日志 | 价值低；测关键分支即可 |

#### JS / Jest / Vitest 对照

前端常见「测什么」同样适用：

| 值得测 | 少测 |
| --- | --- |
| 纯函数、reducer、zod 校验 | 第三方组件库内部 |
| API client 的 URL/参数拼装（mock fetch） | 每次 E2E 打真实支付 |
| 错误码分支 | 「文案是否好听」 |

Vitest 里注入 Fake 与 Python 同一思想：

```typescript
const fakeLlm = { complete: async () => ({ role: "assistant", content: "ok" }) }
await ask(fakeLlm, messages)
```

---

## 5. 建议掌握：参数化与 mock

### 5.1 参数化：一张表跑多组输入

#### 为什么要用参数化？

同一规则、多组输入时，复制多个 `test_*` 会又臭又长：

```python
def test_clip_case1(): ...
def test_clip_case2(): ...
def test_clip_case3(): ...
```

`@pytest.mark.parametrize` 让你用**数据表**驱动：失败时会显示是哪一组参数挂了。

#### 怎么写

```python
import pytest
from app.text import clip


@pytest.mark.parametrize(
    ("text", "n", "expected"),
    [
        ("hi", 10, "hi"),
        ("abcdefghij", 5, "ab..."),
        ("abcd", 4, "abcd"),
    ],
)
def test_clip(text, n, expected):
    assert clip(text, n) == expected
```

也可以参数化「期望异常」：

```python
@pytest.mark.parametrize("n", [0, 1, 2])
def test_clip_invalid_n(n):
    with pytest.raises(ValueError):
        clip("hello", n)
```

#### 跑一下

```bash
pytest tests/test_text.py::test_clip -v
```

会看到类似：

```text
test_clip[hi-10-hi] PASSED
test_clip[abcdefghij-5-ab...] PASSED
test_clip[abcd-4-abcd] PASSED
```

方括号里就是参数组合——哪一组挂了，一眼能看出来。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 参数元组顺序和声明不一致 | 静默测错（`n` 接到了字符串） |
| 一组里塞完全无关的场景 | 表难读；拆成两个 parametrize/两个测试 |
| 用参数化替代清晰的独立用例 | 复杂分支仍可写独立 `test_*`，不必强行一张表 |

#### JS / Jest / Vitest 对照

```javascript
import { describe, it, expect } from "vitest"

describe.each([
  ["hi", 10, "hi"],
  ["abcdefghij", 5, "ab..."],
])("clip(%s, %i)", (text, n, expected) => {
  it(`returns ${expected}`, () => {
    expect(clip(text, n)).toBe(expected)
  })
})
```

| Jest / Vitest | pytest |
| --- | --- |
| `it.each` / `test.each` / `describe.each` | `@pytest.mark.parametrize` |
| 表格在 JS 侧 | 表格在装饰器参数里 |

---

### 5.2 mock 基础：替换外部依赖

#### 为什么需要 mock？

当函数**内部**会打网络、读时钟、碰文件系统，单测有两条路：

1. **重构为可注入**（推荐）：`def fetch(client): ...`，测试传 Fake client  
2. **临时 patch**：在不改代码的情况下替换符号

两条都合法；能注入就注入，碰遗留代码再 patch。

#### 怎么写

```python
from unittest.mock import patch


def test_call_llm_uses_client():
    with patch("app.services.llm.http_post", return_value={"text": "ok"}) as m:
        from app.services.llm import call_llm

        result = call_llm("hi")
        assert result["text"] == "ok"
        m.assert_called()
        # 需要更严时：
        # m.assert_called_once_with(...)
```

关键点：

1. **patch 的路径是「使用处」的导入路径**，不是定义处。若 `call_llm` 里 `from app.services import http_post`，要 patch `app.services.llm.http_post`（视你的导入写法而定）。
2. `return_value` 定假返回；`side_effect` 可抛异常或多次不同返回。
3. 也可用 `pytest-mock` 插件的 `mocker.patch`——先会标准库 `patch` 即可。

用 `monkeypatch` 改环境变量（很常见）：

```python
def test_reads_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    # ... 断言配置读取逻辑
```

#### 跑一下（最小可感例）

```python
# app/services/weather.py
def http_get(url: str) -> dict:
    raise RuntimeError("network disabled in unit tests")


def temperature_label(city: str) -> str:
    data = http_get(f"/weather?city={city}")
    temp = data["temp"]
    return "hot" if temp >= 30 else "ok"
```

```python
# tests/test_weather.py
from unittest.mock import patch
from app.services.weather import temperature_label


def test_temperature_label_hot():
    with patch(
        "app.services.weather.http_get",
        return_value={"temp": 35},
    ) as m:
        assert temperature_label("Xiamen") == "hot"
        m.assert_called_once()
```

```bash
pytest tests/test_weather.py -q
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| patch 错路径 | 仍走真函数，单测打到真网络或 `RuntimeError` |
| 断言 `called` 却不关心参数 | 改错 URL 也能绿；关键参数应 `assert_called_with` |
| mock 过多、测到实现细节 | 重构必挂；优先测返回行为 |
| 单测里真的去扣 LLM 额度 | 慢、贵、不稳定——违反本章原则 |

#### JS / Jest / Vitest 对照

```javascript
import { vi, it, expect } from "vitest"
import * as weather from "./weather"

it("labels hot weather", async () => {
  vi.spyOn(weather, "httpGet").mockResolvedValue({ temp: 35 })
  expect(await weather.temperatureLabel("Xiamen")).toBe("hot")
})
```

| Jest / Vitest | Python |
| --- | --- |
| `vi.mock` / `jest.mock` | `unittest.mock.patch` |
| `mockResolvedValue` | `AsyncMock` / `return_value`（async 时） |
| `toHaveBeenCalledWith` | `assert_called_with` |
| 依赖注入更香 | 同样更香——mock 是后备方案 |

---

## 6. 了解即可：覆盖率与 CI

### 6.1 覆盖率：参考不是 KPI

#### 为什么要看覆盖率？

覆盖率回答：「测试跑的时候，哪些代码行从未执行到？」它帮你发现**漏测的分支**，而不是证明质量已经够好。

#### 怎么写 / 怎么跑

```bash
pip install pytest-cov
# 或
uv add --dev pytest-cov

pytest --cov=app --cov-report=term-missing
```

`term-missing` 会在终端列出未覆盖行号，方便补边界用例。

也可生成 HTML：

```bash
pytest --cov=app --cov-report=html
# 打开 htmlcov/index.html
```

#### 怎么读

```text
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
app/messages.py             20      2    90%   14-15
```

`Missing` 指向没跑到的行——去看是不是忘了测「空列表」或「无 system」分支。

#### 易错点

| 错法 | 更好做法 |
| --- | --- |
| 追求 100% | 为 `if TYPE_CHECKING` / 调试分支硬凑测试，收益低 |
| 只看总百分比 | 看关键模块的 miss 行 |
| 覆盖率当 KPI 压人 | 当作「漏测提示器」 |

口诀：

> 覆盖率是手电筒，不是分数榜。

### 6.2 CI：每次 PR 自动跑 pytest

#### 为什么进 CI？

本地绿了不够——别人的机器、合并前的分支，都该用同一条命令验证。CI 把 `pytest` 变成合并门槛。

#### 怎么写（GitHub Actions 示意）

```yaml
# .github/workflows/test.yml
name: test
on:
  pull_request:
  push:
    branches: [main]

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install
        run: |
          python -m pip install -U pip
          pip install -e ".[dev]"
          # 或：pip install pytest pytest-cov && pip install -e .
      - name: Test
        run: pytest -q
```

若用 uv：

```yaml
- uses: astral-sh/setup-uv@v4
- run: uv sync --dev
- run: uv run pytest -q
```

标记慢测并默认跳过（了解即可）：

```python
import pytest


@pytest.mark.slow
def test_real_api():
    ...
```

```bash
pytest -q              # 默认跑
pytest -q -m "not slow"  # CI 常用：跳过 slow
```

需在配置里注册 mark（避免 warn）：

```toml
[tool.pytest.ini_options]
markers = [
  "slow: hits real network or long-running",
]
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| CI 依赖本机已存在的密钥文件 | 流水线无该文件 → 红 |
| CI 里跑真 LLM | 抖动、耗钱、密钥管理复杂 |
| 只跑覆盖率不跑断言 | 数字好看但行为没锁住 |

#### JS / Jest / Vitest 对照

| 前端常见 | Python 常见 |
| --- | --- |
| `vitest run --coverage` | `pytest --cov=app` |
| GitHub Action 里 `npm test` | Action 里 `pytest` |
| codecov / 覆盖率评论 bot | 同样可接，非必须 |

---

## 7. 常见坑

1. **测试依赖执行顺序**  
   应用 fixture / 工厂，不要靠全局可变状态「上一个测试留下的数据」。

2. **测到了实现细节**  
   一重构测试全挂——优先测对外行为（输入 → 输出 / 异常），少断言私有属性名。

3. **单测里真的去扣 LLM 额度**  
   用 FakeLLM / EchoLLM / mock；真调用标 slow 且默认不进 CI。

4. **断言无信息**  
   多个无关断言可拆成多个 `test_*`；需要时先把中间结果赋给变量再 assert。

5. **导入路径与 patch 路径不一致**  
   `ModuleNotFoundError` 先查依赖章的 editable / `pythonpath`；mock 无效先查 patch 目标。

6. **文件/函数命名不符合发现规则**  
   不是 pytest「坏了」，是用例根本没被收集——用 `pytest --collect-only` 查看。

7. **为了覆盖率测试无价值代码**  
   配置样板、`__repr__` 调试字符串等，不必强行 100%。

---

## 8. 综合小例子

把「截断消息」从实现到测试跑通——这是 Agent 里极常见的纯逻辑。

#### 为什么选这个例子？

- 有边界：空列表、有/无 system、N 的大小  
- 无网络、无 LLM，单元测试友好  
- 和练习 B3 直接对应

#### 怎么写（被测代码）

```python
# app/messages.py
def truncate_messages(
    messages: list[dict],
    max_messages: int = 3,
) -> list[dict]:
    """保留可选的首条 system，再保留最近 max_messages 条非 system 历史。"""
    if not messages:
        return []
    if messages[0].get("role") == "system":
        return [messages[0]] + messages[1:][-max_messages:]
    return messages[-max_messages:]
```

#### 怎么写（测试）

```python
# tests/test_messages.py
import pytest
from app.messages import truncate_messages


@pytest.fixture
def long_dialog():
    return [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": str(i)} for i in range(5)
    ]


def test_keeps_system_and_last_n(long_dialog):
    out = truncate_messages(long_dialog, max_messages=2)
    assert out[0]["role"] == "system"
    assert [m["content"] for m in out[1:]] == ["3", "4"]


def test_empty():
    assert truncate_messages([]) == []


@pytest.mark.parametrize(
    ("max_messages", "expected_tail"),
    [
        (1, ["4"]),
        (3, ["2", "3", "4"]),
    ],
)
def test_tail_length(long_dialog, max_messages, expected_tail):
    out = truncate_messages(long_dialog, max_messages=max_messages)
    assert [m["content"] for m in out[1:]] == expected_tail
```

#### 跑一下

```bash
pytest tests/test_messages.py -v
```

期望：全部 PASSED。再改一处实现（例如不小心丢掉 system），对应用例应立刻变红——这就是测试的价值。

#### 易错点（本例特有）

| 错法 | 说明 |
| --- | --- |
| 断言整份 `out == [...]` 写死所有字段 | 字段一增就挂；可只断言关键字段 |
| fixture 里共享并 `pop` 同一列表且改 scope | 污染其他用例 |
| 把「模型是否仍遵守 system」当成单测 | 那是评测问题，不是 `truncate` 的职责 |

#### JS / Vitest 对照（同逻辑）

```typescript
import { describe, it, expect } from "vitest"

describe("truncateMessages", () => {
  it("keeps system and last n", () => {
    const messages = [
      { role: "system", content: "s" },
      ...[0, 1, 2, 3, 4].map((i) => ({ role: "user", content: String(i) })),
    ]
    const out = truncateMessages(messages, 2)
    expect(out[0].role).toBe("system")
    expect(out.slice(1).map((m) => m.content)).toEqual(["3", "4"])
  })
})
```

---

## 9. 练习指引

按文档节奏动手：

1. 先让 `pytest -q` 对一个 `add` / `normalize` 绿灯（§2）  
2. 补 `raises` 与 fixture（§3）  
3. 写一段「测什么 / 不测什么」笔记（§4）  
4. 有余力再上参数化与 mock（§5）

题目与验收：

[`exercises/03-engineering/03-testing.md`](../../exercises/03-engineering/03-testing.md)

代码建议落在 `playground/03-engineering/03-testing/`（可含迷你 `app/` + `tests/`）。

---

## 10. 小结与下一站

### 自检

- [ ] 能写并跑通 pytest（发现规则、断言、`-q` / `-v`）
- [ ] 会 `pytest.raises` 与简单 fixture（含「参数名注入」直觉）
- [ ] 能说出 Agent 里优先测什么、单测为何不该打真 LLM
- [ ] （建议）会 `parametrize`；能用 `patch` 或注入 Fake 隔离网络
- [ ] （了解）知道覆盖率怎么看、CI 里为何要跑 `pytest`

### 一句话带走

> pytest 给纯逻辑上锁；FakeLLM 把非确定性关在门外；CI 让这把锁在每次合并时自动响。

### 下一章

[`04-logging.md`](./04-logging.md) —— 用日志代替乱 `print`，为排障与可观测性打底。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[依赖与虚拟环境](./02-deps-venv.md)
- 下一章：[Logging](./04-logging.md)
