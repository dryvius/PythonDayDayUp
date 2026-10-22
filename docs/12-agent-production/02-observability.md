# Observability

> 所属模块：`12-agent-production` · Agent 工程化与生产落地  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（建议边写 JSONL / span 树边跑断言；无 Key 全程可离线）  
> 对应练习：[`exercises/12-agent-production/02-observability.md`](../../exercises/12-agent-production/02-observability.md)  
> 运行环境：Python ≥ 3.11 · 约定见 [`../CONVENTIONS.md`](../CONVENTIONS.md)

## 本章定位

- **模块目标**：具备评测、可观测、安全与系统设计能力，接近生产级。
- **本章角色**：把模块 03 的 Logging 升到 **Agent 语义**——logs / metrics / traces 三支柱；定下 **Run 字段、允许列表与脱敏**；能从轨迹复盘工具链、汇总 Token / 延迟 / 成本。
- **你已具备**：[`../03-engineering/04-logging.md`](../03-engineering/04-logging.md) 的分级与结构化直觉；[`01-evaluation.md`](./01-evaluation.md) 的 `trace` + `check_trace`；模块 11 手写 Agent 的 `trace: list[dict]`。
- **核心观点**：平台是展示层；**字段先打对**。默认不记录完整 `messages` / API Key。
- **产出直觉**：本地 JSONL + 内存 metrics 就能起步；同一套事件可喂评测与线上排障。
- **目标不是**：一上来接齐 OpenTelemetry 全家桶，或拍脑袋定 SLO。

## 学习目标（学完应能做到）

1. 用一句话说清 logs、metrics、traces 各回答什么；说明 Agent 为何特别依赖 trace。
2. 为一次 Agent run 打齐关键字段，并落地**字段允许列表与脱敏**（args 摘要、preview 截断）。
3. 画出 `run → retrieve / llm / tool` 的 span 树，并与 OTel 做粗映射；本地用 JSONL 起步。
4. 拆解延迟（模型 vs 工具 vs 排队）；从 `usage` 估算成本（单价配置化）。
5. 让工具轨迹可被评测章的 `check_trace` 复用；了解采样策略与 SLO 地图。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 三支柱、Run 字段、允许列表/脱敏、Token/延迟/成本、工具轨迹 | 能落地规范；默认不倾倒 messages |
| **建议掌握** | span 层级、成本汇总进 run、采样与平台接入心态 | 能接平台；字段兼容评测 |
| **了解即可** | SLO 地图 | 有基线再定；防拍脑袋 |

---

## 1. 为什么要学（Agent 可观测性）

这一节会刻意写细——后面所有「字段、span、成本、采样」都建立在同一个动机上：

> **Agent 出事故时，你要的不是「日志很多」，而是「这一次 run 怎么走的、卡在哪、花了多少」。**

### 1.1 一次失败长什么样？

没有 `run_id` / step / 工具名 / 延迟拆解时，日志只剩 `ERROR something went wrong`——你只能猜。有可观测性时，应立刻能答：

```text
哪一次 run_id？第几步调了 search？args 摘要？
模型慢 / 工具慢 / 排队？tokens 与估算成本？
有没有禁调工具、触达 max_steps？
```

### 1.2 为什么 Agent 特别需要 trace？

Chat 单轮扁平日志还能凑合。Agent 多步常见：

```text
retrieve → llm → tool:search → llm → tool:calc → llm → end
```

扁平 `INFO` 难表达父子与因果。Span 树把「同一次请求里谁嵌套谁」钉死——与评测看路径、安全查注入是同一条证据链。

### 1.3 三支柱各回答什么？

| 支柱 | 回答 | Agent 例子 |
|------|------|------------|
| **Logs** | 某次发生了什么 | `event=tool name=search ok=true` |
| **Metrics** | 整体好不好 | `agent_latency_ms` p95、`success_rate` |
| **Traces** | 一次请求怎么走 | `run` 下挂 `llm` / `tool` span |

互补而非三选一：只有 logs 难算 p95；只有 metrics 不知哪一步；只有 traces 缺趋势。

### 1.4 与模块 03 / 评测对齐

| 来源 | 本章升什么 |
|------|------------|
| 模块 03 Logging | 结构化直觉 → **允许列表 + 脱敏** |
| 评测 `trace` / `check_trace` | 线上字段兼容，断言可复用 |
| 手写 Agent `trace` | 加 latency / tokens / preview，不换形状 |

契约（[`CONVENTIONS.md`](../CONVENTIONS.md)）：Python ≥ 3.11；FakeLLM 可离线；**默认不记完整 messages / API Key**。

### 1.5 易错点（动机层）

| 错法 | 会发生什么 |
| --- | --- |
| 当成「多打几行 print」 | 无字段、无关联、无法聚合 |
| 一上来接齐平台 | 字段没约定 → 漂亮垃圾场 |
| 默认 `verbose` 倾倒 messages | 密钥/PII 进盘 |
| 评测与线上两套字段 | `check_trace` 复用不上 |

> **字段先打对，平台后接入；脱敏默认开，完整对话默认关。**

---

## 2. 必掌握：三支柱怎么落地（最小心智）

这一节会刻意写细——先钉「各记什么」，再进 Run 字段与 span。

### 2.1 为什么不要混成一锅？

全塞进 `logger.info(json.dumps(everything))` 会导致：指标靠正则抠、父子靠时间戳猜、采样无法按错误/成功分开。职责应分开：

```text
Logs     → 事件行（可检索、可告警）
Metrics  → 计数/直方图（看板、SLO）
Traces   → span 树（单次复盘、与评测同源）
```

本地可**同源写入**：同一事件 dict → `trace.append` + JSONL + 更新 counter；形状一致最重要。

### 2.2 怎么写：一次事件的最小 dict

```python
from __future__ import annotations

import time
import uuid
from typing import Any


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


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
        "event_type": event_type,  # llm | tool | retrieve | error | end
    }
    if step is not None:
        ev["step"] = step
    ev.update(fields)
    return ev
```

### 2.3 跑一下：三支柱各记一笔

```python
run_id = new_run_id()
trace: list[dict[str, Any]] = []
metrics: dict[str, Any] = {"requests_total": 0, "latency_ms": []}

ev = make_event(
    run_id=run_id, event_type="tool", step=1,
    tool_name="search", ok=True, latency_ms=182,
)
trace.append(ev)
metrics["requests_total"] += 1
metrics["latency_ms"].append(ev["latency_ms"])

assert trace[0]["run_id"] == run_id and metrics["requests_total"] == 1
print(ev["event_type"], ev["tool_name"], ev["latency_ms"])
```

### 2.4 易错点与对照

| 错法 / 支柱 | 后果 / 类比 |
| --- | --- |
| metrics 用高基数标签（完整 query） | 时序库爆炸 |
| 只打 metrics 不打 trace | 知 p95 升、不知哪次 run |
| Logs / Metrics / Traces | 黑匣子语音 / 油表转速 / 完整航迹 |

---

## 3. 必掌握：一次 Run 的字段

这一节会刻意写细——字段是契约；契约糊，后面脱敏、span、成本全糊。

### 3.1 为什么要固定字段名？

评测 harness、线上 JSONL、未来 OTel exporter，最好读**同一套键**。  
改名成本极高：一旦 `tokens_in` / `input_tokens` / `prompt_tokens` 三套并存，报表永远对不齐。

建议在项目里定一页「观测字段表」，新增字段走评审——和 API 字段一样严肃。

### 3.2 怎么写：建议字段清单

贯穿一次用户请求（`run`）：

```text
trace_id / run_id     # 二者可同一；或 trace_id=分布式，run_id=业务
user_id               # 注意隐私：哈希 / 内部 id，勿明文邮箱当主键日志
session_id            # 多轮会话
step                  # Agent 循环步号
event_type            # llm | tool | retrieve | error | end
model                 # llm 事件
tool_name             # tool 事件
latency_ms            # 该 span / 事件耗时
input_tokens / output_tokens / total_tokens
ok / error_type
status                # end 事件：success | failed | cancelled
```

日志观感（人读）：

```text
INFO run_id=ab12 step=2 event=tool name=search ok=true latency_ms=182
INFO run_id=ab12 step=3 event=llm model=gpt-x tokens_in=1200 tokens_out=80 latency_ms=1400
INFO run_id=ab12 event=end status=success total_latency_ms=2100 total_tokens=1280
```

机器读：同一信息用 JSONL（见 §5）。

### 3.3 怎么写：RunContext 小对象

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunContext:
    run_id: str
    session_id: str | None = None
    user_id: str | None = None  # 已是内部 id / 哈希
    step: int = 0
    trace: list[dict[str, Any]] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cost_estimate: float = 0.0

    def next_step(self) -> int:
        self.step += 1
        return self.step

    def emit(self, event_type: str, **fields: Any) -> dict[str, Any]:
        ev = make_event(
            run_id=self.run_id,
            event_type=event_type,
            step=self.step or None,
            session_id=self.session_id,
            user_id=self.user_id,
            **fields,
        )
        self.trace.append(ev)
        return ev
```

### 3.4 跑一下：一次假 run 打齐字段

```python
ctx = RunContext(run_id=new_run_id(), session_id="s-demo")
ctx.next_step()
ctx.emit(
    "llm",
    model="gpt-x",
    input_tokens=100,
    output_tokens=20,
    latency_ms=50.0,
    ok=True,
)
ctx.next_step()
ctx.emit(
    "tool",
    tool_name="search",
    ok=True,
    latency_ms=12.0,
)
ctx.emit(
    "end",
    status="success",
    total_latency_ms=62.0,
    total_tokens=120,
)

types = [e["event_type"] for e in ctx.trace]
assert types == ["llm", "tool", "end"]
assert all(e["run_id"] == ctx.run_id for e in ctx.trace)
print(ctx.run_id, types)
```

### 3.5 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 每一步重新生成 `run_id` | 链路碎成多段，过滤失败 |
| `user_id` 直接打邮箱/手机号 | 合规风险；应用哈希或内部 id |
| `event_type` 与评测 `type` 完全两套 | 复用 `check_trace` 要写适配层（可以，但要显式） |
| 把整份 `messages` 塞进 `emit` | 见下一节允许列表——默认禁止 |

### 3.6 对照：评测事件 vs 线上事件

评测最小形：`{"type":"llm"|"tool_call"|"tool_result", "name"?, "step", "ok"?}`。  
线上可更富，教学推荐**直接兼容**：保留 `type` + `name` + `ok` + `step`，再加 `latency_ms` / `args` 摘要等；断言里可用 `event.get("name") or event.get("tool_name")`。勿另起一套无法映射的键名。

---

## 4. 必掌握：字段允许列表与脱敏

这一节会刻意写细——这是 Agent 观测的红线，也是练习验收硬项。

### 4.1 为什么必须有允许列表？

Agent 上下文里几乎全是敏感或高价值数据：

- system prompt / 完整 messages  
- 用户隐私、工单正文  
- 工具返回的内部文档、密钥片段  
- `Authorization`、API Key、Cookie  

「出了 bug 先把 messages 打出来」在 Demo 里爽，在生产里是事故。  
正确默认：**拒绝记录**，按允许列表**白名单放出**。

### 4.2 怎么写：允许 / 禁止表

| 允许 | 禁止（默认） |
|------|----------------|
| `run_id`、`step`、`event_type`、`model`、`tool_name` | 完整 `messages` / system prompt 全文 |
| `latency_ms`、token 计数、`ok`、`error_type` | API Key、Cookie、密码、`Authorization` |
| `args` 的**已脱敏摘要** | 原始身份证号、邮箱明文（视合规） |
| `result_preview`（截断后） | 工具返回的完整敏感载荷 |
| `user_id`（内部 id / 哈希） | 把邮箱当 `user_id` 明文打日志 |

禁止心态补充：

1. **不要** `verbose=True` 默认倾倒整段对话  
2. **不要**在异常消息里拼接 `str(messages)`  
3. 临时排障需要全文时：走**受控**通道（短 TTL、权限、审计），不要写进常驻 JSONL

### 4.3 怎么写：摘要、截断、简单脱敏

```python
from __future__ import annotations

import re
from typing import Any

# 按工具再收紧；全局再宽也危险
ALLOWED_ARG_KEYS: dict[str, set[str]] = {
    "search": {"query", "top_k"},
    "calc": {"expr"},
    "*": {"query", "top_k", "expr"},  # 未知工具的兜底（仍很窄）
}

MAX_PREVIEW = 200
REDACT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(api[_-]?key|authorization)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9]{8,}"), "sk-[REDACTED]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
]


def redact_text(text: str) -> str:
    out = text
    for pat, repl in REDACT_PATTERNS:
        out = pat.sub(repl, out)
    return out


def preview(text: str, n: int = MAX_PREVIEW) -> str:
    t = redact_text(text.replace("\n", " "))
    return t if len(t) <= n else t[: n - 3] + "..."


def summarize_args(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    allowed = ALLOWED_ARG_KEYS.get(tool) or ALLOWED_ARG_KEYS["*"]
    out: dict[str, Any] = {}
    for k in allowed:
        if k not in args:
            continue
        v = args[k]
        if isinstance(v, str):
            out[k] = preview(v, n=120)
        else:
            out[k] = v
    return out


def safe_tool_event(
    tool: str,
    args: dict[str, Any],
    result_text: str,
    *,
    ok: bool,
    latency_ms: float,
) -> dict[str, Any]:
    return {
        "type": "tool",
        "name": tool,
        "args": summarize_args(tool, args),
        "result_preview": preview(result_text),
        "ok": ok,
        "latency_ms": latency_ms,
    }
```

### 4.4 跑一下：断言「不出现密钥 / 完整 messages」

```python
args = {
    "query": "Orion 密码策略",
    "top_k": 3,
    "authorization": "Bearer secret-token",  # 不应进摘要
}
raw_result = "doc:Orion:… contact admin@example.com key=sk-abcdefghirandom"

ev = safe_tool_event("search", args, raw_result, ok=True, latency_ms=182.0)

assert "authorization" not in ev["args"]
assert ev["args"]["query"] == "Orion 密码策略"
assert "sk-[REDACTED]" in ev["result_preview"] or "sk-" not in ev["result_preview"]
assert "admin@example.com" not in ev["result_preview"]
assert "messages" not in ev
print(ev["args"], ev["result_preview"][:60])
```

再钉一条「禁止倾倒」：

```python
FORBIDDEN_LOG_KEYS = {"messages", "api_key", "authorization", "cookie", "password"}


def assert_safe_payload(payload: dict[str, Any]) -> None:
    lowered = {k.lower() for k in payload}
    leak = lowered & FORBIDDEN_LOG_KEYS
    assert not leak, f"forbidden keys in log payload: {leak}"


assert_safe_payload(ev)
# 故意违规应失败：
try:
    assert_safe_payload({"messages": [{"role": "user", "content": "hi"}]})
    raise AssertionError("should have failed")
except AssertionError as e:
    assert "forbidden" in str(e)
```

### 4.5 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只截断不脱敏 | `sk-...` 仍完整落在前 200 字里 |
| 允许列表按「我觉得有用」越扩越大 | 最后等于没有名单 |
| 在 `logger.exception` 里带 `repr(request)` | 框架对象常含 headers / body |
| DEBUG 环境默认打印 messages，忘了关 | 生产配置继承了开发习惯 |

### 4.6 对照：模块 03 vs 本章

| 模块 03 | 本章 |
|---------|------|
| 结构化：`run_id` / `latency_ms` | 同上，并升到 **event_type / tokens / preview** |
| 「别把 Key 拼进日志」口头提醒 | **代码级允许列表 + 断言** |
| Formatter / JSON logger | JSONL 事件流，供 trace / 评测复用 |

---

## 5. 建议掌握：Span 层级（因果链）

这一节会刻意写细——把扁平事件收成树；并说明与 OTel 的粗映射。

### 5.1 为什么需要树，而不是只有列表？

列表能回答「发生过哪些事件」。  
树能回答：

```text
这次 run 总耗时里，retrieve / llm / tool 各占多少？
某个 llm span 下面是否串了两个 tool？
错误挂在哪个子 span 上？
```

Agent 的自然树：

```text
run (trace_id)
├─ retrieve          latency, hit_k
├─ llm               model, tokens_in/out
├─ tool:search       args_summary, result_preview
├─ llm
└─ end               status, total_latency, total_tokens
```

### 5.2 怎么写：本地 Span（不必先上 OTel SDK）

```python
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    attrs: dict[str, Any] = field(default_factory=dict)
    children: list[Span] = field(default_factory=list)
    start_ms: float = 0.0
    end_ms: float = 0.0

    def __enter__(self) -> Span:
        self.start_ms = time.perf_counter() * 1000
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.end_ms = time.perf_counter() * 1000
        self.attrs.setdefault("latency_ms", round(self.end_ms - self.start_ms, 2))
        if exc_type is not None:
            self.attrs["ok"] = False
            self.attrs["error_type"] = getattr(exc_type, "__name__", str(exc_type))
        else:
            self.attrs.setdefault("ok", True)

    @property
    def latency_ms(self) -> float:
        return float(self.attrs.get("latency_ms") or 0.0)


def start_child(parent: Span, name: str, **attrs: Any) -> Span:
    child = Span(name=name, attrs=dict(attrs))
    parent.children.append(child)
    return child


def dump_tree(span: Span, indent: int = 0) -> str:
    pad = "  " * indent
    line = f"{pad}├─ {span.name}  {span.attrs}"
    parts = [line]
    for ch in span.children:
        parts.append(dump_tree(ch, indent + 1))
    return "\n".join(parts)
```

### 5.3 怎么写：拍平为评测列表 + JSONL

树给人看；**拍平列表**给 `check_trace` 与 JSONL。深度优先时带上 `type`/`name`/`step`/`latency_ms` 即可：

```python
import json
from pathlib import Path


def span_to_events(span: Span, run_id: str, step: list[int]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if span.name != "run":
        step[0] += 1
        etype = span.name.split(":")[0]
        name = span.attrs.get("name") or span.name.split(":")[-1]
        ev = {
            "type": etype if etype in {"llm", "tool", "retrieve", "error"} else "span",
            "name": name,
            "step": step[0],
            "run_id": run_id,
            "ok": span.attrs.get("ok", True),
            "latency_ms": span.latency_ms,
        }
        for k in ("model", "input_tokens", "output_tokens", "args", "result_preview"):
            if k in span.attrs:
                ev[k] = span.attrs[k]
        events.append(ev)
    for ch in span.children:
        events.extend(span_to_events(ch, run_id, step))
    return events


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
```

练习落盘：`playground/12-agent-production/observability/app.log`（一行一事件或一行一整棵树均可，字段先统一）。

### 5.4 跑一下：假 Agent 树

```python
run_id = new_run_id()
root = Span(name="run", attrs={"run_id": run_id})

with root:
    with start_child(root, "retrieve", hit_k=2) as r:
        r.attrs["hit_k"] = 2
    with start_child(root, "llm", model="gpt-x") as llm:
        llm.attrs.update(model="gpt-x", input_tokens=100, output_tokens=20)
    with start_child(root, "tool:search", name="search") as tool:
        tool.attrs.update(
            name="search",
            args=summarize_args("search", {"query": "密码", "top_k": 2}),
            result_preview=preview("doc:Orion:…"),
        )

tree_txt = dump_tree(root)
assert "retrieve" in tree_txt and "tool:search" in tree_txt
flat = span_to_events(root, run_id, [0])
assert [e["type"] for e in flat] == ["retrieve", "llm", "tool"]
assert flat[2]["name"] == "search"
print(tree_txt)
```

### 5.5 与 OpenTelemetry 粗映射

| 本章 | OpenTelemetry |
|------|----------------|
| `run` / `trace_id` | Root span / TraceId |
| 每次 `llm` / `tool` / `retrieve` | Child span |
| `attrs`（model、tokens…） | Span attributes |
| JSONL 落盘 | Exporter 的一种本地形态 |
| `ok` / `error_type` | Span status + exception event |

迁移：先字段与父子做对 → 再换 exporter（OTel / Langfuse / 厂商）→ 平台只负责采集展示，**业务语义仍是你的**。

### 5.6 易错点与对照

| 错法 / 表象 | 后果 / 本质 |
| --- | --- |
| 全部挂 root、丢掉嵌套 | 延迟归因不准 |
| span 名用整句中文 | 过滤困难；用稳定短名 |
| 只接平台、不留 JSONL | CI / 本地难复现 |
| 漂亮 Trace UI | 仍取决于 attrs 准不准 |
| 评测 `trace` 列表 | 常常是树的拍平投影 |

---

## 6. 必掌握：Token、延迟与成本

这一节会刻意写细——没有拆解的「慢了」和没有单价的「贵了」都无法行动。

### 6.1 为什么要拆延迟？

只看 `total_latency_ms`：

```text
p95 = 8s  →  然后呢？加机器？换模型？优化检索？
```

拆开后才有动作：

| 分量 | 常见原因 | 动作方向 |
|------|----------|----------|
| `llm_latency_ms` | 模型/区域/输出过长 | 换模型、限 `max_tokens`、流式体验 |
| `tool_latency_ms{tool}` | 下游慢、超时重试 | 缓存、并发、治工具 |
| `queue_wait_ms` | 线程池/队列堆积 | 扩容、限流、背压 |
| `retrieve_latency_ms` | 向量库/ES 慢 | 索引、top_k、超时 |

### 6.2 怎么写：延迟累加器 + 成本估算

单价**放配置**（settings / yaml），勿写死业务；按「每 1M tokens」计更常见：

```python
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

PRICE_PER_1M: dict[str, dict[str, float]] = {
    "gpt-x": {"in": 0.5, "out": 1.5},
    "gpt-mini": {"in": 0.1, "out": 0.4},
}


@dataclass
class LatencyBudget:
    llm_ms: float = 0.0
    retrieve_ms: float = 0.0
    tool_ms: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    queue_wait_ms: float = 0.0

    def add(self, kind: str, ms: float, *, tool: str | None = None) -> None:
        if kind == "llm":
            self.llm_ms += ms
        elif kind == "retrieve":
            self.retrieve_ms += ms
        elif kind == "tool":
            self.tool_ms[tool or "unknown"] += ms
        elif kind == "queue":
            self.queue_wait_ms += ms

    def as_metrics(self) -> dict[str, Any]:
        total = self.llm_ms + self.retrieve_ms + self.queue_wait_ms + sum(self.tool_ms.values())
        return {
            "llm_latency_ms": round(self.llm_ms, 2),
            "retrieve_latency_ms": round(self.retrieve_ms, 2),
            "queue_wait_ms": round(self.queue_wait_ms, 2),
            "tool_latency_ms": {k: round(v, 2) for k, v in self.tool_ms.items()},
            "agent_latency_ms": round(total, 2),
        }


def estimate_cost(model: str, usage: dict[str, Any]) -> float:
    p = PRICE_PER_1M.get(model) or {"in": 0.0, "out": 0.0}
    tin = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    tout = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    return (int(tin) * p["in"] + int(tout) * p["out"]) / 1_000_000


def on_llm_end(
    ctx: RunContext, model: str, usage: dict[str, Any], latency_ms: float
) -> None:
    cost = estimate_cost(model, usage)
    ctx.total_input_tokens += int(
        usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    )
    ctx.total_output_tokens += int(
        usage.get("output_tokens") or usage.get("completion_tokens") or 0
    )
    ctx.cost_estimate += cost
    ctx.emit(
        "llm",
        type="llm",
        model=model,
        input_tokens=usage.get("input_tokens") or usage.get("prompt_tokens"),
        output_tokens=usage.get("output_tokens") or usage.get("completion_tokens"),
        latency_ms=latency_ms,
        cost_estimate=cost,
        ok=True,
    )
```

建议指标：`agent_latency_ms`（p50/p95）、`llm_latency_ms`、`tool_latency_ms{tool}`、`tokens_*`、`cost_estimate`、`success_rate`、`max_steps_hit_rate`。评测报表可并列 `avg_tokens` / `avg_cost`（见评测章）。

### 6.3 跑一下：拆解 + 成本断言

```python
budget = LatencyBudget()
budget.add("queue", 30)
budget.add("retrieve", 40)
budget.add("llm", 800)
budget.add("tool", 120, tool="search")
budget.add("llm", 600)
m = budget.as_metrics()
assert m["agent_latency_ms"] == 1590.0
assert m["tool_latency_ms"]["search"] == 120.0
assert m["llm_latency_ms"] == 1400.0

assert abs(estimate_cost("gpt-x", {"input_tokens": 1_000_000, "output_tokens": 0}) - 0.5) < 1e-9
assert abs(estimate_cost("gpt-x", {"prompt_tokens": 0, "completion_tokens": 1_000_000}) - 1.5) < 1e-9

ctx = RunContext(run_id=new_run_id())
ctx.next_step()
on_llm_end(ctx, "gpt-x", {"input_tokens": 1000, "output_tokens": 500}, latency_ms=200)
assert ctx.total_input_tokens == 1000
print(m, "cost", round(ctx.cost_estimate, 6))
```

简易分位数（练习够用）：

```python
def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    k = int(round((len(xs) - 1) * p))
    return xs[max(0, min(k, len(xs) - 1))]


assert percentile([100.0, 200.0, 300.0, 800.0, 900.0], 0.5) == 300.0
```

### 6.4 易错点与对照

| 错法 / 问题 | 后果 / 看什么 |
| --- | --- |
| 单价写死多处 | 调价后报表撒谎 |
| 只计最后一次 LLM tokens | 多步严重低估 |
| 墙钟总时间减 llm 当工具时间 | 忽略排队；用各 span 自己的 `latency_ms` |
| 整体变慢 / 模型慢 / 某工具慢 | `agent` p95 / `llm_*` / `tool_*{name}` |
| 变贵 / 烧步数 | `cost_estimate`；联评测看 `max_steps_hit_rate` |

---

## 7. 必掌握：工具调用轨迹与 `check_trace` 复用

这一节会刻意写细——轨迹是评测与事故复盘的共同语言。

### 7.1 为什么工具轨迹单独强调？

Agent 的「行动」几乎都落在工具上。轨迹要能回答：

```text
调了谁？参数摘要？成功吗？耗时？
有没有禁调工具？
是否死循环 / 触达 max_steps？
注入攻击有没有真的触发了 shell？
```

结构化事件（落盘前已过允许列表）：

```json
{
  "type": "tool",
  "name": "search",
  "args": {"query": "密码策略", "top_k": 3},
  "result_preview": "doc:Orion:…",
  "ok": true,
  "latency_ms": 182,
  "step": 2,
  "run_id": "ab12cd34ef56"
}
```

### 7.2 怎么写：兼容评测的 `check_trace` + 边跑边记

评测章逻辑可原样复用（略作健壮：同时认 `type`/`event_type`、`name`/`tool_name`）：

```python
def check_trace(
    trace: list[dict[str, Any]],
    forbidden_tools: set[str],
    max_llm_calls: int = 8,
) -> list[str]:
    errors: list[str] = []
    for event in trace:
        etype = event.get("type") or event.get("event_type")
        name = event.get("name") or event.get("tool_name")
        if etype in {"tool", "tool_call"} and name in forbidden_tools:
            errors.append(f"forbidden tool: {name}")
    llm_calls = len(
        [e for e in trace if (e.get("type") or e.get("event_type")) == "llm"]
    )
    if llm_calls > max_llm_calls:
        errors.append(f"too many llm calls: {llm_calls}")
    return errors


def record_tool(
    ctx: RunContext,
    name: str,
    args: dict[str, Any],
    result_text: str,
    *,
    ok: bool,
    latency_ms: float,
) -> None:
    ctx.next_step()
    payload = safe_tool_event(
        name, args, result_text, ok=ok, latency_ms=latency_ms
    )
    ctx.emit(
        "tool",
        type="tool",
        name=payload["name"],
        tool_name=payload["name"],
        args=payload["args"],
        result_preview=payload["result_preview"],
        ok=payload["ok"],
        latency_ms=payload["latency_ms"],
    )
```

线上 JSONL 读回后，**同一 `check_trace`** 可做抽检或事故脚本。

### 7.3 跑一下：禁工具 + 步数

```python
ctx = RunContext(run_id=new_run_id())
ctx.next_step()
ctx.emit("llm", type="llm", model="gpt-x", ok=True, latency_ms=10)
record_tool(ctx, "search", {"query": "x", "top_k": 1}, "doc:x:0", ok=True, latency_ms=5)
ctx.next_step()
ctx.emit("llm", type="llm", model="gpt-x", ok=True, latency_ms=10)

assert check_trace(ctx.trace, {"shell"}) == []
assert check_trace(ctx.trace, {"search"}) == ["forbidden tool: search"]
errs = check_trace([{"type": "llm", "step": i} for i in range(10)], set(), max_llm_calls=8)
assert any("too many llm calls" in e for e in errs)
print("trace ok")
```

### 7.4 用途、易错点与对照

| 场景 / 错法 | 要点 |
|-------------|------|
| 评测 | `forbidden_tools` / `max_llm_calls` |
| 事故 / 注入调查 | 按 `run_id` 还原树；看禁工具与异常 args 摘要 |
| `args` 未过允许列表 | 日志与评测集一起泄敏 |
| 只记 call 不记 `ok` | 分不清失败在执行还是模型 |
| `messages` vs `trace` | 前者给模型；后者给人/评测/平台，**默认不进 context**，写入前脱敏 |

---

## 8. 建议掌握：采样与平台

这一节会刻意写细——流量上来以后，全量明细会先打爆账单与磁盘。

### 8.1 为什么要采样？

QPS=50、每 run 10 span ≈ 四千万条/天——全量明细贵且难查。但**错误与慢请求**必须看明细，故采样要**有偏**，不是一刀切 1%。Metrics 通常仍全量；降的是明细 trace / 胖日志。

### 8.2 怎么写：有偏采样（教学）

```python
import hashlib


def should_sample(
    *,
    run_id: str,
    status: str,
    total_latency_ms: float,
    slow_threshold_ms: float = 5000.0,
    success_rate: float = 0.1,
) -> bool:
    """错误/慢：全要；成功快路径：稳定哈希按比例。"""
    if status != "success" or total_latency_ms >= slow_threshold_ms:
        return True
    h = int(hashlib.sha256(run_id.encode()).hexdigest(), 16)
    return (h % 10_000) < int(success_rate * 10_000)
```

```python
assert should_sample(run_id="a", status="failed", total_latency_ms=10) is True
assert should_sample(run_id="a", status="success", total_latency_ms=9000) is True
a = should_sample(run_id="stable-1", status="success", total_latency_ms=100, success_rate=0.0)
assert a is False
```

| 流量 | 建议 |
|------|------|
| 错误 / 慢请求 / 安全标签 | 全量或极高采样 |
| 成功快路径 | 降采样（如 1%～10%） |

### 8.3 平台心态与易错点

> **平台是采集与展示；字段打对之前，换平台解决不了语义问题。**

顺序：字段+脱敏 → 本地 JSONL/metrics 跑绿 → 再接 OTel/Langfuse/厂商 exporter → 拍平事件仍可被 `check_trace` 理解。

| 错法 | 后果 |
| --- | --- |
| 成功/失败同一低采样 | 事故刚好没采到 |
| 先买平台再定字段 | 看板漂亮、字段全 `null` |
| 采样掉 metrics | 趋势断档 |

对照：本地 JSONL/`dump_tree` ≈ 平台瀑布图；`check_trace` ≈ 告警链到 `trace_id`。

---

## 9. 了解即可：SLO 地图

先建立地图，细节等你有基线再定——**避免拍脑袋**。

### 9.1 为什么「先有基线」？

没有历史分布时写「p95 < 8s」：

- 可能永远红（模型本身就要 10s）  
- 可能永远绿（阈值太松，失去意义）  

正确顺序：

```text
先打点 1～2 周 → 看 p50/p95/成本分布 → 再定 SLO / 告警
```

### 9.2 常见 Agent SLO 候选

| 目标 | 例（仅示意） | 依赖指标 |
|------|--------------|----------|
| 延迟 | p95 `agent_latency_ms` < 基线×1.2 | 延迟直方图 |
| 可靠性 | 成功率 > 95% | `success_rate` / errors |
| 成本 | 单次 run `cost_estimate` p95 < 预算 | usage 汇总 |
| 行为 | `max_steps_hit_rate` < 5% | trace |
| 安全 | 禁工具触发率 = 0（抽检） | `check_trace` |

### 9.3 和评测的关系

| 离线评测 | 在线 SLO |
|----------|----------|
| 固定 case 集、可复现 | 真实流量分布 |
| accuracy / avg_steps | success_rate / p95 |
| 改 prompt 看回归 | 发版后看是否破线 |

两者一起才完整：离线防「改坏」，在线防「线上漂」。

### 9.4 易错点（地图层）

| 错法 | 会发生什么 |
| --- | --- |
| 照抄别人博客的 8s | 与你的模型/工具栈无关 |
| SLO 十几个一起上 | 告警疲劳，全被静音 |
| 只盯成功率不盯成本 | 「更对」但烧穿预算 |

了解即可：等模块项目线有稳定流量，再和团队一起定第一版（通常 2～3 个指标就够）。

---

## 10. 串起来：最小观测环

无外网、无平台时的闭环：

```text
new run_id → RunContext / 根 Span
  → 每步 llm/tool：允许列表 + latency + usage/cost
  → trace + 可选 JSONL + metrics
  → end（status / total_*）→ 有偏采样导出
  → 同一 trace → check_trace（联评测）
```

外层可包一层「总耗时 + 合并内部 trace + 采样决策」；**拆解必须在 `run_fn` 内部打 span**，否则只有 `agent_latency_ms`。Fake 路径验收：

```python
def fake_agent(q: str) -> dict[str, Any]:
    return {
        "answer": f"ECHO:{q}",
        "trace": [
            {"type": "llm", "step": 1, "model": "gpt-x", "latency_ms": 12},
            {
                "type": "tool",
                "name": "search",
                "step": 1,
                "ok": True,
                "latency_ms": 5,
                "args": summarize_args("search", {"query": q, "top_k": 1}),
                "result_preview": preview("doc:demo"),
            },
        ],
        "usage": {"model": "gpt-x", "input_tokens": 100, "output_tokens": 50},
    }


out = fake_agent("查密码策略")
assert check_trace(out["trace"], {"shell"}) == []
assert "authorization" not in str(out["trace"])
cost = estimate_cost("gpt-x", out["usage"])
assert cost > 0
print("ok", cost, should_sample(run_id="x", status="success", total_latency_ms=20))
```

易错：只包外壳不打内部 span；重复写 `end`；合并前未过允许列表。

---

## 11. 练习指引

[`exercises/12-agent-production/02-observability.md`](../../exercises/12-agent-production/02-observability.md)

建议路径：

1. **A**：入口 `trace_id`/`run_id`，LLM/工具/结束事件写 JSONL  
2. **B**：内存 metrics + `print_metrics` 或 `GET /metrics`  
3. **C**：`TraceSpan` + `dump_trace` 树形输出  
4. **D**：允许列表、`preview`、`estimate_cost`  
5. **E**（建议）：故意工具异常，同一 `trace_id` 串起失败链  

与评测章共用 `check_trace`；与模块 03 对照：级别/handler 仍按工程章，本章补 **Agent 字段语义与脱敏**。目录：`playground/12-agent-production/observability/`。

---

## 12. 小结与下一站

### 记住这些

1. **三支柱**：logs / metrics / traces；Agent 多步尤其依赖 trace。  
2. **Run 字段是契约**：与评测 `type`/`name` 对齐；加 latency、tokens、preview。  
3. **允许列表默认拒绝**完整 messages / API Key；只要摘要 + `preview`。  
4. **Span 树**本地 JSONL 起步；平台是后一步。  
5. **延迟要拆、成本要估**（单价配置化）；轨迹复用 `check_trace`。  
6. **采样有偏、SLO 有基线**；字段先打对再接平台。

### 自检

- [ ] 能画出 `run → llm/tool` 的 span 树，并说明与 OTel 粗映射  
- [ ] 有字段允许列表；默认不记完整 messages / API Key  
- [ ] 能从 `usage` 估算成本，并拆解 llm vs tool 延迟  
- [ ] 工具轨迹可被 `check_trace` 复用  
- [ ] 知道错误/慢请求高采样、成功快路径可降采样  
- [ ] 明白 SLO 要先有基线再定

### 下一章

[`03-security.md`](./03-security.md) —— 注入、权限、泄露与沙箱；观测轨迹会成为安全调查的证据入口。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Evaluation](./01-evaluation.md)
- 下一章：[Agent Security](./03-security.md)
- 约定：[CONVENTIONS.md](../CONVENTIONS.md)
- 相关：[`../03-engineering/04-logging.md`](../03-engineering/04-logging.md)
