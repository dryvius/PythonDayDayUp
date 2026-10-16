# 练习：函数与作用域

> 对应文档：[`docs/01-python-basics/02-functions-scope.md`](../../docs/01-python-basics/02-functions-scope.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/01-python-basics/02-functions-scope/
```

4. 先自己做完，再看文末提示。计算型函数请 `return`，不要只靠 `print` 交差。

---

## 基础题（必做）

### B1. 函数定义与返回值：消息工厂

实现：

```python
def create_message(
    role: str,
    content: str,
    *,
    name: str | None = None,
) -> dict:
    ...
```

要求：

1. 返回字典，至少包含 `"role"`、`"content"`
2. 仅当 `name is not None` 时加入 `"name"` 字段
3. `content` 先 `.strip()`；若 strip 后为空，抛出 `ValueError("content empty")`
4. `role` 只允许：`"system"` / `"user"` / `"assistant"` / `"tool"`，否则抛出 `ValueError`

自行写几组调用做验证（正常 + 异常）。

**验收**：非法 role / 空 content 会报错；合法调用返回结构正确，且 `name` 缺省时键不存在（不是 `"name": None`）。

---

### B2. `*args` / `**kwargs`：工具调用构建与转发

实现两个函数：

```python
def build_tool_call(name: str, **arguments) -> dict:
    """返回 {"name": name, "arguments": arguments}"""


def run_tool(tool_call: dict, registry: dict) -> dict:
    """
    registry 形如：{"search": search_fn, "calc": calc_fn}
    从 tool_call 取出 name / arguments，调用对应函数。
    返回 {"name": name, "result": ..., "ok": True/False}
    """
```

约定：

1. `build_tool_call("search", query="RAG", top_k=3)` 得到标准结构
2. `run_tool` 若 name 不在 registry：`ok=False`，`result` 为错误说明字符串
3. 若调用函数过程抛异常：捕获后 `ok=False`，`result` 为异常字符串
4. 成功则 `ok=True`，`result` 为函数返回值

可先在 registry 里放两个假工具：

```python
def search(query: str, top_k: int = 5) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


def calc(expression: str) -> float:
    # 练习里允许用安全的极简实现，例如只处理 "1+2" 这类；
    # 或直接写死几个 case。不要用 eval 处理任意字符串（习惯上不安全）。
    ...
```

**验收**：成功 / 未知工具 / 工具抛错 三条路径都能跑通。

---

### B3. 作用域与闭包：计数器与限流器

1. 实现 `make_counter(start: int = 0)`，返回一个无参函数；每调用一次返回递增后的值。
2. 实现 `make_rate_limiter(max_calls: int)`，返回函数 `allow() -> bool`：
   - 前 `max_calls` 次调用返回 `True`
   - 之后返回 `False`
   - 内部用闭包计数（需要 `nonlocal`）

**验收**：

```python
c = make_counter(10)
assert c() == 11 and c() == 12

limit = make_rate_limiter(2)
assert limit() is True and limit() is True and limit() is False
```

---

### B4. lambda 与排序

给定：

```python
tool_results = [
    {"name": "browse", "ok": False, "latency_ms": 800},
    {"name": "search", "ok": True, "latency_ms": 120},
    {"name": "calc", "ok": True, "latency_ms": 30},
    {"name": "search", "ok": True, "latency_ms": 90},
]
```

要求（可用 `sorted` + `lambda`，也可先 `def` 再当 key）：

1. 得到 `ok_first`：先按 `ok` 降序（True 在前），再按 `latency_ms` 升序
2. 得到 `names`：所有 `ok is True` 的工具名列表（推导式或 filter 均可）

**验收**：`ok_first[0]["name"] == "calc"`；`names` 含 `search`/`calc`，不含失败的 `browse`。

---

## 进阶题（建议至少做 1 题）

### A1. 修复可变默认参数 + 不可变更新

下面函数有 bug，请改成正确版本，并补充测试证明多次调用互不影响：

```python
def add_message(history, message):
    # 错误示范思路：用 history=[] 当默认值
    history.append(message)
    return history
```

正确要求：

1. `history` 默认应为「空历史」，多次调用互不污染
2. **不要修改**传入的原 list；返回新 list  
   （即：调用方传入的 list 内容保持不变）

---

### A2. partial 配置聊天函数

```python
def chat(model: str, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> dict:
    return {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
```

用 `functools.partial` 生成：

- `ask_strict`：`model="gpt-4.1-mini"`, `temperature=0`, `max_tokens=256`
- 再调用 `ask_strict(prompt="一句话解释闭包")` 并打印结果

**验收**：返回 dict 中预填字段正确，且只需传 `prompt`。

---

## 挑战题（可选）

### C1. 迷你 Tool Runtime

综合本章，实现一个极简运行时：

```python
class_or_functions_whatever_you_like = ...

# 期望能力：
# 1) register(name, fn) 注册工具
# 2) call(name, **kwargs) 调用工具，返回 {ok, result, name}
# 3) 提供 calls() -> int 统计成功调用次数（闭包或对象属性均可）
# 4) 提供 with_logging(fn) 高阶函数：包装后先打印 "calling <name>" 再执行
```

约束：

- 注册时若 name 重复，直接覆盖或拒绝均可，但要在注释里说明
- `call` 内部应使用 `**kwargs` 转发给工具
- 写一段 demo：注册 `search`/`calc`，成功调用 + 一次失败调用

**验收**：别人只看你的 demo，能看懂如何注册与调用。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成，关键路径有断言或清晰打印
- [ ] 能口述：可变默认参数为什么危险；闭包里何时需要 `nonlocal`
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

先校验 `role` 与 `content`，再组装 dict。关键字-only 的 `name` 用 `*` 分隔。判空：`if not content.strip():`。

</details>

<details>
<summary>B2 提示</summary>

```python
fn = registry.get(name)
if fn is None:
    return {"name": name, "ok": False, "result": "unknown tool"}
try:
    result = fn(**tool_call["arguments"])
    return {"name": name, "ok": True, "result": result}
except Exception as exc:
    return {"name": name, "ok": False, "result": str(exc)}
```

`calc` 可用：`{"1+2": 3.0, "10/2": 5.0}.get(expression)`，找不到再报错。

</details>

<details>
<summary>B3 提示</summary>

`inc` / `allow` 内对计数变量赋值前加 `nonlocal count`。`allow` 在 `count < max_calls` 时先加再返回 True。

</details>

<details>
<summary>B4 提示</summary>

`key=lambda r: (not r["ok"], r["latency_ms"])`：`False`&lt;`True`，所以 `not ok` 为 False（即成功）会排前面。

</details>

<details>
<summary>A1 思路</summary>

```python
def add_message(history=None, message=None):
    base = list(history) if history is not None else []
    base.append(message)
    return base
```

注意参数设计要合理；测试：两次默认调用返回值应独立；传入旧 list 后旧 list 不变。

</details>

<details>
<summary>A2 思路</summary>

`partial(chat, model=..., temperature=0, max_tokens=256)`，调用时只传 `prompt=`。

</details>

<details>
<summary>C1 思路</summary>

用 dict 做 registry；用闭包变量或简单类保存 `success_count`；`with_logging` 返回 `wrapper(*args, **kwargs)`。文档第 3、6 节几乎覆盖全部零件。

</details>
