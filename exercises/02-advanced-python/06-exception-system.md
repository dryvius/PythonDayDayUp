# 练习：异常系统

> 对应文档：[`docs/02-advanced-python/06-exception-system.md`](../../docs/02-advanced-python/06-exception-system.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/02-advanced-python/06-exception-system/
```

4. 验证异常链时，可打印 `exc.__cause__` 或看 traceback。

---

## 基础题（必做）

### B1. try/except/else/finally 行为观察

写一个函数 `divide(a, b)`：

- `b == 0` 时捕获 `ZeroDivisionError`，返回 `"div0"`
- 成功时走 `else`，返回商
- 无论成败，`finally` 里给全局列表 `events` append `"done"`

再分别调用 `divide(6, 3)` 与 `divide(1, 0)`，检查返回值与 `events`。

**验收**：成功返回 `2`；失败返回 `"div0"`；两次调用后 `events` 至少含两个 `"done"`。

---

### B2. 自定义异常层次

实现：

```python
class AgentError(Exception): ...
class ToolNotFoundError(AgentError): ...
class ToolExecutionError(AgentError):
    def __init__(self, tool_name: str, message: str, *, retryable: bool = False): ...
```

并写 `get_tool(registry, name)`：不存在则 `raise ToolNotFoundError(name)`。

**验收**：捕获 `ToolNotFoundError` 时能读到工具名；它同时也是 `AgentError` 的实例（`isinstance` 检查）。

---

### B3. 异常链

实现 `parse_json_object(text: str) -> dict`：

- JSON 非法 → `raise ToolExecutionError("parser", "invalid json") from exc`
- 解析结果非 dict → `raise ToolExecutionError("parser", "must be object")`（可不带 cause）

**验收**：非法 JSON 时 `exc.__cause__` 不为 `None`；非对象 JSON（如 `[1]`）也能报错。

---

### B4. 捕获宽度对比（认知 + 代码）

写两段代码：

1. `except Exception:` 把 `ValueError` 和你故意埋的 `NameError`（或其它）一起吞掉（演示坏味道，打日志即可）
2. 改成只捕获 `ValueError`，让另一类错误冒泡

在 `b4_notes.md` 写 3～5 行：为什么边界层可以宽捕，业务核心通常要窄捕。

**验收**：有对比代码 + 笔记。

---

## 进阶题（建议至少做 1 题）

### A1. ToolRuntime.call

按文档综合例子实现精简版 `ToolRuntime`：

- `register` / `call(name, arguments_json)`
- 未知工具 → `ToolNotFoundError`
- JSON 坏 → `ToolExecutionError`（带 cause）
- `ConnectionError` → `ToolExecutionError(retryable=True)`
- 其它执行错误 → `retryable=False`

注册假 `search`，覆盖：成功、未知工具、坏 JSON、网络错误四条路径。

**验收**：四条路径行为正确；网络错误路径 `retryable is True`。

---

### A2. 重试只针对 retryable

写 `call_with_retry(runtime, name, arguments_json, max_attempts=3)`：

- 捕获 `ToolExecutionError`，仅当 `retryable` 才重试
- `ToolNotFoundError` 不重试
- 次数用尽后抛出最后一次异常（保持 cause）

**验收**：对 retryable 错误会尝试多次；对 not found 只尝试 1 次。

---

## 挑战题（可选）

### C1. 把错误回传给「模型」

实现 `agent_once(runtime, tool_name, arguments_json) -> dict`：

成功：

```python
{"ok": True, "result": ...}
```

失败：

```python
{"ok": False, "error_type": "...", "message": "...", "retryable": false}
```

不要让异常直接打爆主流程（在该函数边界转成结构化结果）。  
同时在日志里打印原始 cause（若有）。

**验收**：成功/失败都返回 dict；失败信息不丢关键字段。

---

### C2. 异常层次图（书面）

画或列出你为「LLM 调用 + Tool 调用」设计的异常树（8～12 行即可），并标注每类错误的处理策略：重试 / 换工具 / 终止 / 回传模型。

**验收**：有 `c2_errors.md`；策略不是全写成「重试」。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成
- [ ] 能口述：else/finally 用途；为何需要自定义异常；`from` 链的价值
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

`events` 可用模块级 list。`else` 里 `return a / b`（或返回已算好的值）。

</details>

<details>
<summary>B3 提示</summary>

```python
except json.JSONDecodeError as exc:
    raise ToolExecutionError(...) from exc
```

</details>

<details>
<summary>A1 提示</summary>

先 `json.loads`，再 `fn(**args)`，分层转换异常。注意不要把 `ToolNotFoundError` 包成 ExecutionError。

</details>

<details>
<summary>A2 提示</summary>

```python
for attempt in range(max_attempts):
    try:
        return runtime.call(...)
    except ToolExecutionError as exc:
        if not exc.retryable or attempt == max_attempts - 1:
            raise
```

</details>

<details>
<summary>C1 思路</summary>

`except AgentError as exc:` 组装 dict；`error_type=type(exc).__name__`。

</details>
