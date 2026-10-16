# 练习：Python 数据模型

> 对应文档：[`docs/02-advanced-python/02-data-model.md`](../../docs/02-advanced-python/02-data-model.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/02-advanced-python/02-data-model/
```

4. 每题写少量断言或清晰打印；先做题再看提示。

---

## 基础题（必做）

### B1. 协议对照表（书面 + 代码）

1. 在 `b1_notes.md` 中列出至少 6 组对照：`写法 → dunder`
2. 写一个最小类 `Demo`，实现 `__str__` 与 `__repr__`，并打印证明二者不同

**验收**：笔记存在；`str(demo) != repr(demo)`（内容不同即可）。

---

### B2. MessageList 容器协议

实现 `MessageList`，内部存 `dict` 或简单对象均可，需支持：

```python
messages.add("user", "hi")
len(messages)
"user" in messages          # 按 role 判断
messages[0]                 # 取第 0 条
for m in messages: ...      # 可迭代
bool(messages)              # 空为 False
```

额外要求：

- 索引越界抛 `IndexError`
- `messages[0]` 返回的应是拷贝，或文档明确「返回内部引用」并在注释说明风险（二选一，推荐返回拷贝）

**验收**：上述操作均可运行；空列表 `if messages:` 为假。

---

### B3. 可调用 Tool

实现：

```python
@dataclass
class Tool:
    name: str
    handler: Callable[..., Any]

    def __call__(self, **kwargs): ...
    def __str__(self) -> str: ...
```

再用它包装：

```python
def calc(expression: str) -> float: ...
tool = Tool("calc", calc)
result = tool(expression="1+2")
```

**验收**：`callable(tool) is True`；`print(tool)` 友好；调用返回正确结果。

---

### B4. `__eq__` 与业务去重

实现 `ToolCall(name: str, arguments: dict)`：

1. 同 name + 同 arguments → 相等
2. 把一组可能重复的 `ToolCall` 放进 list，写函数 `unique_calls(calls) -> list[ToolCall]` 去重且保序

注意：`dict` 不能直接放进 `set`；去重可用「已见过的签名」集合，例如 `(name, json.dumps(arguments, sort_keys=True))`。

**验收**：输入 4 条含重复，输出去重后数量正确且顺序保留首次出现。

---

## 进阶题（建议至少做 1 题）

### A1. 完整 ToolRegistry

实现文档综合例子同款能力：

- `register` / `__len__` / `__contains__` / `__getitem__` / `__iter__` / `__repr__`
- 通过 `registry["search"](query="x")` 直接调用

并补上：未知工具名时 `__getitem__` 抛 `KeyError`（或自定义异常，但要明确）。

**验收**：注册 2 个工具后，遍历名称集合与 `repr(registry)` 合理。

---

### A2. 可调用重试器

实现 `Retry(max_attempts: int)`：

- `__call__(self, fn, *args, **kwargs)` 按次数重试
- 属性 `attempts` 记录总共尝试次数（跨多次调用可累计，或每次调用重置——在注释说明你的选择）
- 最终失败抛 `RuntimeError`，并用 `from` 链接最后一次异常

写一个「前两次失败、第三次成功」的假函数验证。

**验收**：成功路径返回值正确；一直失败时异常类型正确。

---

## 挑战题（可选）

### C1. 描述符：NonEmptyName（选做）

实现文档中的 `NonEmpty` 描述符，用于：

```python
class ToolSpec:
    name = NonEmpty("name")
```

空字符串或空白赋值时报错；正常赋值自动 strip。

**验收**：非法赋值抛 `ValueError`；合法赋值后读回无首尾空格。

---

### C2. TokenBudget 小对象（贴近 Agent）

实现 `TokenBudget(limit: int)`：

- `consume(n: int)` 扣减
- `remaining` property
- `__bool__`：还有剩余额度则为 True
- `__lt__`：可与另一 budget 比 remaining（或比 limit，自行定义并写清）

模拟：多轮 tool calling 每轮消耗若干 token，额度用尽停止。

**验收**：循环在额度用尽时停止；打印剩余额度。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成
- [ ] 能不看资料说出至少 5 个「语法 → dunder」
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

至少覆盖：`len`、`in`、下标、`str`、`repr`、调用 `obj()`。

</details>

<details>
<summary>B2 提示</summary>

`__contains__` 里比较 `role`。`__bool__` 可显式写，或只写 `__len__`。迭代用 `return iter(self._items)`。

</details>

<details>
<summary>B3 提示</summary>

`__call__` 内 `return self.handler(**kwargs)`。`calc` 可用固定字典映射表达式。

</details>

<details>
<summary>B4 提示</summary>

```python
import json
sig = (call.name, json.dumps(call.arguments, sort_keys=True, ensure_ascii=False))
```

用 `seen: set[tuple]` 保序去重。

</details>

<details>
<summary>A1 思路</summary>

与文档第 8 节几乎相同。重点把错误路径补齐。

</details>

<details>
<summary>A2 思路</summary>

```python
except Exception as exc:
    last = exc
raise RuntimeError(...) from last
```

</details>

<details>
<summary>C1 思路</summary>

描述符挂在类上；`__set__` 校验后 `setattr(obj, self.private_name, value)`。

</details>
