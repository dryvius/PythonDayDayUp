# 练习：Observability

> 对应文档：[`docs/12-agent-production/02-observability.md`](../../docs/12-agent-production/02-observability.md)  
> 状态：`已完成出题`  
> 建议用时：70～110 分钟（含热身）  
> 运行环境：Python ≥ 3.11 · 无 Key 全程可离线（见 [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)）

## 练习说明

1. 先读完文档「必掌握」：三支柱、Run 字段、允许列表与脱敏、Token/延迟、工具轨迹。
2. 题目分档：**热身 / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/12-agent-production/observability/
```

4. 与评测章对齐：线上事件最好兼容 `{"type","name","step","ok"}`，便于复用 `check_trace`。评测可跑入口：

```bash
python playground/12-agent-production/evaluation/run_eval.py
```

5. **硬约定**：字段允许列表；默认不记完整 `messages` / system prompt / API Key；`args` / 结果用摘要与截断。
6. FakeLLM `complete` 返回 assistant dict；Agent 对外可汇总为 `{answer, trace, usage}`。
7. 先自己做完，再看文末「提示与参考答案」。

---

## 热身题（建议先做）

### W1. 生成 `run_id`

**要求**：实现 `new_run_id() -> str`（uuid hex 截断即可），连续两次调用结果不同。

**验收**：`assert new_run_id() != new_run_id()`。

---

### W2. 最小事件 dict

**要求**：实现 `make_event(run_id, event_type, step=None, **fields) -> dict`，至少含 `ts`、`run_id`、`event_type`。

**验收**：`ev["run_id"] == "abc"` 且 `"ts" in ev`。

---

### W3. 脱敏一串 Key

**给定**：`text = "Authorization: Bearer sk-abcdefghijklmnop"`。

**要求**：实现或调用 `redact(text)`，结果中不再含完整 `sk-` 密钥体，且不含明文 `Bearer` 后的 token（可用 `[REDACTED]`）。

**验收**：`"sk-abcdefghijklmnop" not in redact(text)`。

---

### W4. 口令默写

**要求**：用三行以内文字写出：logs / metrics / traces 各回答什么问题。

**验收**：能口述「发生了什么 / 整体好不好 / 一次请求怎么走」。

---

## 基础题（必做）

### B1. Run 字段表

在 `playground/12-agent-production/observability/run_fields.md`（或同级 README 段落）列出一次 Agent run 的**字段表**，至少包含：

| 字段 | 出现位置 | 说明 | 是否允许进常驻日志 |
|------|----------|------|-------------------|
| `run_id` / `trace_id` | 全程 | … | 是 |
| `step` | llm/tool | … | 是 |
| `event_type` / `type` | 事件 | … | 是 |
| `model` | llm | … | 是 |
| `tool_name` / `name` | tool | … | 是 |
| `latency_ms` | 事件 | … | 是 |
| `input_tokens` / `output_tokens` / `total_tokens` | llm/end | … | 是 |
| `ok` / `error_type` / `status` | 事件/end | … | 是 |
| `args` 摘要 | tool | … | 条件允许 |
| `messages` 全文 | — | … | **否（默认）** |
| API Key / Authorization | — | … | **否** |

再实现 `RunContext`（可用 dataclass）：持有 `run_id`、`step`、`trace`，提供 `next_step()` 与 `emit(event_type, **fields)`。

**验收**：字段表齐全；一次假 run 发出 `llm → tool → end`，且全部事件共享同一 `run_id`。

---

### B2. 允许列表日志 + `redact`

实现：

```python
ALLOWED_LOG_KEYS: set[str] = {...}

def summarize_args(tool: str, args: dict) -> dict: ...
def preview(text: str, max_len: int = 200) -> str: ...
def redact(text: str) -> str: ...
def to_log_record(event: dict) -> dict: ...
```

要求：

1. `to_log_record` **只保留**允许键；若误传 `messages` / `api_key`，不得出现在输出
2. `redact` 至少处理：`sk-...`、邮箱、`Authorization` / `api_key` 赋值形
3. `summarize_args` 按工具白名单键过滤（如 `search` 仅 `query`/`top_k`），值经 `preview` + `redact`
4. 将若干事件以 JSONL 追加写入 `app.log`（路径自定）

**验收**：构造含 Key 与假 `messages` 的脏事件，落盘记录中不含密钥与完整 messages；附 ≥3 条 `redact` 断言。

---

### B3. Token / 延迟汇总

实现内存指标与汇总：

```python
class Metrics:
    def observe_llm(self, *, latency_ms: float, input_tokens: int, output_tokens: int) -> None: ...
    def observe_tool(self, *, name: str, latency_ms: float, ok: bool) -> None: ...
    def summary(self) -> dict: ...
```

`summary()` 至少含：

- `requests_total`（或 `llm_calls` / `tool_calls`）
- `errors_total`（工具失败计数）
- `total_input_tokens` / `total_output_tokens`
- `avg_latency_ms` 或分项平均
- 可选：`estimate_cost(model, usage)`（单价写死在 dict 配置里即可）

跑一段假数据后 `print_metrics()`。

**验收**：数字与手工累加一致；成本函数对固定 usage 返回稳定值。

---

### B4. 工具轨迹事件（兼容评测）

实现 `emit_tool_call` / `emit_tool_result`（或统一 `emit`），使 `RunContext.trace` 中出现：

```python
{"type": "tool_call", "name": "search", "step": 1, ...}
{"type": "tool_result", "name": "search", "ok": True, "step": 1, ...}
```

可用评测章同款检查：

```python
# 语义对齐 playground/12-agent-production/evaluation/run_eval.py
errors = check_trace(ctx.trace, forbidden_tools={"shell"})
assert errors == []
```

**验收**：轨迹可被 `check_trace` 消费；故意插入 `shell` 的 `tool_call` 能被抓到。

---

## 进阶题（建议至少做 1 题）

### A1. Span 父子假实现

实现最小 span 树（不必上 OTel SDK）：

```python
@dataclass
class Span:
    name: str
    span_id: str
    parent_id: str | None
    start_ms: float
    end_ms: float | None = None
    attrs: dict = ...
    children: list[Span] = ...
```

要求：

1. `start_span(name, parent=None) -> Span` / `end_span(span, **attrs)`
2. 一次假请求形成：`run` → 子 `llm`、子 `tool:search` →（可选）再 `llm`
3. `dump_tree(root)` 打印缩进树，并断言父子 `span_id` / `parent_id` 链接正确

**验收**：树形输出可读；`run` 的 children 含 llm 与 tool。

---

### A2. 采样策略说明

写一页 `sampling_notes.md`（或模块 docstring），说明你准备采用的采样策略，至少覆盖：

| 场景 | 建议采样 | 理由 |
|------|----------|------|
| 错误 / 拒绝 / 禁工具 | 100% 或高采样 | … |
| 成功短路径 | 较低采样（如 1%～10%） | … |
| 高成本 / 高步数 run | 提高采样或必留 | … |
| 含 PII 风险字段 | 采样前后仍走脱敏 | … |

明确：**采样不等于可以记录完整 messages**；允许列表优先于采样率。

**验收**：文档 ≥1 屏；含「错误必留、成功降采样、脱敏不豁免」三点。

---

## 挑战题（可选）

### C1. 最小观测环串 FakeLLM Agent

把观测接到一个确定性 Agent 环路上（同步即可）：

```text
user → Agent.run → FakeLLM.complete → (可选 tool) → 返回 {answer, trace, usage}
         │
         └─ 全程 RunContext.emit + Metrics + JSONL（已脱敏）
```

约束：

1. `FakeLLM.complete(messages, tools=None) -> dict`，返回 assistant 消息 dict
2. 工具执行前后打点；最终 `usage` 含 `total_tokens`
3. 日志中无完整 messages、无 API Key
4. 对外 `trace` 可供 `check_trace` 使用

写一段 demo：普通问答 + 一次假 search 工具调用；打印 metrics 与 span/事件列表。

**验收**：别人只看 demo 能复现「一次请求的观测闭环」。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4 完成
- [ ] **通过线**：B1～B4 全部完成（字段表、允许列表+脱敏、token/延迟、工具轨迹）
- [ ] 默认不落盘完整 messages / API Key
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 观测环可跑

---

## 提示与参考答案（先做题再看）

W1 参考答案

```python
from __future__ import annotations

import uuid


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


assert new_run_id() != new_run_id()
```

W2 参考答案

```python
from __future__ import annotations

import time
from typing import Any


def make_event(
    *,
    run_id: str,
    event_type: str,
    step: int | None = None,
    **fields: Any,
) -> dict[str, Any]:
    ev: dict[str, Any] = {
        "ts": time.time(),
        "run_id": run_id,
        "event_type": event_type,
    }
    if step is not None:
        ev["step"] = step
    ev.update(fields)
    return ev


ev = make_event(run_id="abc", event_type="llm", step=1, model="fake")
assert ev["run_id"] == "abc" and "ts" in ev
```

W3 参考答案

```python
from __future__ import annotations

import re


def redact(text: str) -> str:
    out = text
    out = re.sub(r"(?i)(api[_-]?key|authorization)\s*[:=]\s*\S+", r"\1=[REDACTED]", out)
    out = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-[REDACTED]", out)
    out = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[EMAIL]", out)
    return out


raw = "Authorization: Bearer sk-abcdefghijklmnop"
assert "sk-abcdefghijklmnop" not in redact(raw)
```

W4 参考答案

```text
Logs：某次发生了什么（可检索事件）
Metrics：整体好不好（计数、延迟分布）
Traces：一次请求怎么走（父子 span / 步骤链）
```

B1 思路 + 参考答案

**思路**

字段是契约；`run_id` 全程不变；`event_type` 与评测 `type` 可并存或别名映射。

**参考答案（字段表要点）**

```markdown
| 字段 | 出现位置 | 说明 | 常驻日志 |
|------|----------|------|----------|
| run_id | 全程 | 一次请求主键 | 是 |
| step | llm/tool | Agent 循环步号 | 是 |
| event_type | 事件 | llm/tool/end/... | 是 |
| model | llm | 模型名 | 是 |
| tool_name | tool | 工具名 | 是 |
| latency_ms | 事件 | 耗时 | 是 |
| *tokens | llm/end | 用量 | 是 |
| ok/status | 事件/end | 成败 | 是 |
| args 摘要 | tool | 白名单+截断 | 条件 |
| messages 全文 | — | 对话全文 | 否 |
| API Key | — | 密钥 | 否 |
```

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunContext:
    run_id: str
    session_id: str | None = None
    step: int = 0
    trace: list[dict[str, Any]] = field(default_factory=list)

    def next_step(self) -> int:
        self.step += 1
        return self.step

    def emit(self, event_type: str, **fields: Any) -> dict[str, Any]:
        # 兼容评测：同时写 type
        ev = make_event(
            run_id=self.run_id,
            event_type=event_type,
            step=self.step or None,
            session_id=self.session_id,
            type=event_type if event_type in {"llm", "tool_call", "tool_result"} else event_type,
            **fields,
        )
        self.trace.append(ev)
        return ev


ctx = RunContext(run_id=new_run_id(), session_id="s-demo")
ctx.next_step()
ctx.emit("llm", model="fake", input_tokens=10, output_tokens=5, latency_ms=12.0, ok=True)
ctx.next_step()
ctx.emit("tool_call", name="search", tool_name="search")
ctx.emit("tool_result", name="search", tool_name="search", ok=True, latency_ms=8.0)
ctx.emit("end", status="success", total_tokens=15)
assert [e["event_type"] for e in ctx.trace][:2] == ["llm", "tool_call"]
assert len({e["run_id"] for e in ctx.trace}) == 1
```

B2 思路 + 参考答案

**思路**

默认拒绝记录；白名单放出。脱敏在摘要之后仍要做——截断不等于脱敏。

**参考答案**

```python
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ALLOWED_LOG_KEYS = {
    "ts",
    "run_id",
    "session_id",
    "step",
    "event_type",
    "type",
    "model",
    "name",
    "tool_name",
    "latency_ms",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "ok",
    "error_type",
    "status",
    "args",
    "result_preview",
}

ALLOWED_ARG_KEYS: dict[str, set[str]] = {
    "search": {"query", "top_k"},
    "calculator": {"expr"},
    "*": {"query", "top_k", "expr"},
}

MAX_PREVIEW = 200


def preview(text: str, max_len: int = MAX_PREVIEW) -> str:
    text = text if isinstance(text, str) else str(text)
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def redact(text: str) -> str:
    out = text
    out = re.sub(r"(?i)(api[_-]?key|authorization)\s*[:=]\s*\S+", r"\1=[REDACTED]", out)
    out = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-[REDACTED]", out)
    out = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[EMAIL]", out)
    return out


def summarize_args(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    allow = ALLOWED_ARG_KEYS.get(tool) or ALLOWED_ARG_KEYS["*"]
    out: dict[str, Any] = {}
    for k, v in args.items():
        if k not in allow:
            continue
        out[k] = redact(preview(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)))
    return out


def to_log_record(event: dict[str, Any]) -> dict[str, Any]:
    rec = {k: event[k] for k in ALLOWED_LOG_KEYS if k in event}
    # 双保险：即便上游塞了敏感键也不会留下
    for banned in ("messages", "api_key", "authorization", "system_prompt"):
        rec.pop(banned, None)
    if "args" in rec and isinstance(rec["args"], dict):
        tool = str(event.get("name") or event.get("tool_name") or "*")
        rec["args"] = summarize_args(tool, rec["args"])
    if "result_preview" in rec:
        rec["result_preview"] = redact(preview(str(rec["result_preview"])))
    return rec


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(to_log_record(event), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---- 断言 ----
assert "sk-abcdefghijklmnop" not in redact("key=sk-abcdefghijklmnop")
assert "[EMAIL]" in redact("mail me@x.com")
dirty = {
    "run_id": "r1",
    "event_type": "llm",
    "messages": [{"role": "user", "content": "secret"}],
    "api_key": "sk-abcdefghijklmnop",
    "model": "fake",
}
rec = to_log_record(dirty)
assert "messages" not in rec and "api_key" not in rec
```

B3 思路 + 参考答案

**思路**

指标与 trace 同源更新，避免各打各的。成本单价配置化，勿写死在业务分支里。

**参考答案**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PRICE_PER_1K = {
    "fake": {"input": 0.0, "output": 0.0},
    "gpt-x": {"input": 0.005, "output": 0.015},
}


def estimate_cost(model: str, usage: dict[str, int]) -> float:
    p = PRICE_PER_1K.get(model) or PRICE_PER_1K["fake"]
    inn = usage.get("input_tokens", 0)
    out = usage.get("output_tokens", 0)
    return (inn / 1000.0) * p["input"] + (out / 1000.0) * p["output"]


@dataclass
class Metrics:
    llm_calls: int = 0
    tool_calls: int = 0
    errors_total: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    latency_ms: list[float] = field(default_factory=list)
    tool_latency_ms: list[float] = field(default_factory=list)
    cost_estimate: float = 0.0

    def observe_llm(
        self,
        *,
        model: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        self.llm_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.latency_ms.append(latency_ms)
        self.cost_estimate += estimate_cost(
            model, {"input_tokens": input_tokens, "output_tokens": output_tokens}
        )

    def observe_tool(self, *, name: str, latency_ms: float, ok: bool) -> None:
        _ = name
        self.tool_calls += 1
        self.tool_latency_ms.append(latency_ms)
        if not ok:
            self.errors_total += 1

    def summary(self) -> dict[str, Any]:
        def avg(xs: list[float]) -> float:
            return round(sum(xs) / len(xs), 2) if xs else 0.0

        return {
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "errors_total": self.errors_total,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "avg_llm_latency_ms": avg(self.latency_ms),
            "avg_tool_latency_ms": avg(self.tool_latency_ms),
            "cost_estimate": round(self.cost_estimate, 6),
        }


m = Metrics()
m.observe_llm(model="gpt-x", latency_ms=100, input_tokens=1000, output_tokens=200)
m.observe_tool(name="search", latency_ms=20, ok=True)
m.observe_tool(name="search", latency_ms=30, ok=False)
s = m.summary()
assert s["llm_calls"] == 1 and s["tool_calls"] == 2 and s["errors_total"] == 1
assert s["total_input_tokens"] == 1000
print(s)
```

B4 思路 + 参考答案

**思路**

评测看路径、线上排障看路径——同一条证据链。`type`/`name`/`ok`/`step` 是最小公约数。

**参考答案**

```python
from __future__ import annotations

from typing import Any


def check_trace(trace: list[dict], forbidden_tools: set[str], max_llm_calls: int = 8) -> list[str]:
    """与 evaluation/run_eval.py 对齐的精简版。"""
    errors: list[str] = []
    for event in trace:
        if event.get("type") == "tool_call" and event.get("name") in forbidden_tools:
            errors.append(f"forbidden tool: {event['name']}")
    llm_calls = len([e for e in trace if e.get("type") == "llm"])
    if llm_calls > max_llm_calls:
        errors.append(f"too many llm calls: {llm_calls}")
    return errors


def emit_tool_pair(ctx: RunContext, name: str, *, ok: bool, latency_ms: float) -> None:
    ctx.emit("tool_call", type="tool_call", name=name, tool_name=name)
    ctx.emit(
        "tool_result",
        type="tool_result",
        name=name,
        tool_name=name,
        ok=ok,
        latency_ms=latency_ms,
    )


ctx = RunContext(run_id="r-tool")
ctx.next_step()
ctx.emit("llm", type="llm", model="fake")
emit_tool_pair(ctx, "search", ok=True, latency_ms=15)
assert check_trace(ctx.trace, {"shell"}) == []

evil = list(ctx.trace) + [{"type": "tool_call", "name": "shell", "step": 9}]
assert check_trace(evil, {"shell"})
```

A1 思路 + 参考答案

**思路**

Span 表达嵌套；本地用 id/parent_id 即可，不必先接平台。

**参考答案**

```python
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    span_id: str
    parent_id: str | None
    start_ms: float
    end_ms: float | None = None
    attrs: dict[str, Any] = field(default_factory=dict)
    children: list[Span] = field(default_factory=list)


def start_span(name: str, parent: Span | None = None) -> Span:
    sp = Span(
        name=name,
        span_id=uuid.uuid4().hex[:8],
        parent_id=parent.span_id if parent else None,
        start_ms=time.perf_counter() * 1000,
    )
    if parent is not None:
        parent.children.append(sp)
    return sp


def end_span(span: Span, **attrs: Any) -> Span:
    span.end_ms = time.perf_counter() * 1000
    span.attrs.update(attrs)
    return span


def dump_tree(span: Span, indent: int = 0) -> None:
    dur = (span.end_ms - span.start_ms) if span.end_ms is not None else -1
    print("  " * indent + f"- {span.name} ({dur:.1f}ms) {span.attrs}")
    for ch in span.children:
        dump_tree(ch, indent + 1)


root = start_span("run")
llm = start_span("llm", root)
end_span(llm, model="fake", tokens=30)
tool = start_span("tool:search", root)
end_span(tool, ok=True)
end_span(root, status="success")
dump_tree(root)
assert {c.name for c in root.children} == {"llm", "tool:search"}
assert all(c.parent_id == root.span_id for c in root.children)
```

A2 思路 + 参考答案

**思路**

采样是成本杠杆；安全与合规字段策略不因采样而放松。

**参考答案（sampling_notes.md 提纲）**

```markdown
# 采样策略（教学稿）

## 原则
1. 错误 / 拒绝 / 触发禁工具 / ACL 拒绝：**必采样（100%）**
2. 成功短路径：可降到 1%～10%，保留 metrics 全量计数
3. 高成本（tokens 高 / steps 高）或用户投诉关联 run：**提高采样或强制保留**
4. 无论采样与否：走字段允许列表 + redact；禁止因「要排障」默认倾倒 messages

## 落地建议
- 头：`X-Force-Trace: 1` 或内部 debug 角色可提升采样（仍脱敏）
- 尾：end 事件带 `status` / `total_tokens`，供事后补拉（若有受控全文通道则短 TTL）

## 反例
- 成功也 100% 记全文 messages → 成本与泄露双爆
- 错误丢弃 → 线上不可复盘
```

C1 思路 + 参考答案

**思路**：观测环 = FakeLLM Agent + RunContext + Metrics + JSONL；输出 `{answer, trace, usage}` 对齐评测。

**参考答案**

```python
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable


class FakeLLM:
    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        _ = tools
        last = (messages[-1].get("content") or "") if messages else ""
        if "搜索" in last:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "search", "arguments": '{"query": "RAG", "top_k": 2}'},
                }],
            }
        return {"role": "assistant", "content": f"ECHO:{last}"}


def search(query: str, top_k: int = 5) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]


class ObservedAgent:
    def __init__(self, llm: FakeLLM, log_path: Path) -> None:
        self.llm, self.log_path, self.metrics = llm, log_path, Metrics()

    def run(self, user_input: str) -> dict[str, Any]:
        ctx = RunContext(run_id=new_run_id())
        messages: list[dict] = [{"role": "user", "content": user_input}]
        total_in = total_out = 0
        registry: dict[str, Callable[..., Any]] = {"search": search}

        for _ in range(4):
            ctx.next_step()
            t0 = time.perf_counter()
            msg = self.llm.complete(messages)
            latency = (time.perf_counter() - t0) * 1000
            inn, out = 20, 10
            total_in += inn
            total_out += out
            self.metrics.observe_llm(model="fake", latency_ms=latency, input_tokens=inn, output_tokens=out)
            ctx.emit("llm", type="llm", model="fake", latency_ms=round(latency, 2),
                     input_tokens=inn, output_tokens=out, ok=True)
            append_jsonl(self.log_path, ctx.trace[-1])

            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                ctx.emit("end", status="success", total_tokens=total_in + total_out)
                append_jsonl(self.log_path, to_log_record(ctx.trace[-1]))
                return {
                    "answer": msg.get("content") or "",
                    "trace": ctx.trace,
                    "usage": {"total_tokens": total_in + total_out,
                              "input_tokens": total_in, "output_tokens": total_out},
                }

            # 演示执行；生产须先 authorize
            tc = tool_calls[0]["function"]
            name, args = tc["name"], json.loads(tc["arguments"])
            ctx.emit("tool_call", type="tool_call", name=name, args=summarize_args(name, args))
            append_jsonl(self.log_path, ctx.trace[-1])
            t1 = time.perf_counter()
            result = registry[name](**args)
            tool_ms = (time.perf_counter() - t1) * 1000
            self.metrics.observe_tool(name=name, latency_ms=tool_ms, ok=True)
            ctx.emit("tool_result", type="tool_result", name=name, ok=True,
                     latency_ms=round(tool_ms, 2), result_preview=preview(str(result)))
            append_jsonl(self.log_path, ctx.trace[-1])
            messages += [msg, {"role": "tool", "name": name, "content": json.dumps(result, ensure_ascii=False)}]

        return {"answer": "max steps", "trace": ctx.trace, "usage": {"total_tokens": total_in + total_out}}


agent = ObservedAgent(FakeLLM(), Path("playground/12-agent-production/observability/app.log"))
out1, out2 = agent.run("你好"), agent.run("请搜索 RAG 资料")
assert out1["answer"].startswith("ECHO:")
assert any(e.get("name") == "search" for e in out2["trace"] if e.get("type") == "tool_call")
assert check_trace(out2["trace"], {"shell"}) == []
print(agent.metrics.summary(), "C1 ok", out2["usage"])
```

---

## 导航

- 文档：[Observability](../../docs/12-agent-production/02-observability.md)
- 上一练习：[01-evaluation](./01-evaluation.md)
- 下一练习：[03-security](./03-security.md)
