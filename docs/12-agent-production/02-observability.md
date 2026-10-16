# Observability

> 所属模块：`12-agent-production` · Agent 工程化与生产落地  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/12-agent-production/02-observability.md`](../../exercises/12-agent-production/02-observability.md)

## 本章定位

- **本章角色**：日志 / 指标 / 追踪三件套；聚焦 Token、延迟、工具调用轨迹；定下**字段允许列表与脱敏**。
- **前置**：模块 03 Logging；本章升到 Agent 语义。与评测章的 `trace` 事件对齐。

## 学习目标

1. 区分 logs、metrics、traces。
2. 为一次 Agent run 打齐关键字段，并遵守允许列表。
3. 能从轨迹复盘工具链；会从 `usage` 汇总成本。
4. 了解 Tracing 平台与 SLO 地图。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 三支柱、Run 字段、允许列表/脱敏、Token/延迟、工具轨迹 | 能落地规范 |
| **建议掌握** | span 层级、成本汇总、采样 | 能接平台 |
| **了解即可** | SLO | 地图 |

---

## 1. 三支柱

| 支柱 | 回答 |
|------|------|
| Logs | 某次发生了什么（事件） |
| Metrics | 整体好不好（聚合） |
| Traces | 一次请求跨组件怎么走（因果链） |

Agent 特别需要 **trace**：一次用户问题可能含多次 LLM 与工具调用。

---

## 2. 必掌握：一次 Run 的字段

### 2.1 建议字段

```text
trace_id / run_id
user_id（注意隐私）
session_id
step
event_type: llm | tool | retrieve | error
model
tool_name
latency_ms
input_tokens / output_tokens / total_tokens
ok / error_type
```

日志示例：

```text
INFO run_id=ab12 step=2 event=tool name=search ok=true latency_ms=182
INFO run_id=ab12 step=3 event=llm model=gpt-x tokens_in=1200 tokens_out=80 latency_ms=1400
```

### 2.2 字段允许列表（必守）

默认**拒绝**记录完整 prompt / 完整 messages / Authorization。用允许列表约束：

| 允许 | 禁止（默认） |
|------|----------------|
| `run_id`、`step`、`event_type`、`model`、`tool_name` | 完整 `messages` / system prompt 全文 |
| `latency_ms`、token 计数、`ok`、`error_type` | API Key、Cookie、密码 |
| `args` 的**已脱敏摘要**（见下） | 原始身份证号、邮箱明文（视合规） |
| `result_preview`（截断后） | 工具返回的完整敏感载荷 |

```python
ALLOWED_ARG_KEYS = {"query", "top_k", "expr"}  # 按工具再收紧
MAX_PREVIEW = 200


def summarize_args(tool: str, args: dict) -> dict:
    return {k: args[k] for k in ALLOWED_ARG_KEYS if k in args}


def preview(text: str, n: int = MAX_PREVIEW) -> str:
    t = text.replace("\n", " ")
    return t if len(t) <= n else t[: n - 3] + "..."
```

禁止：完整 API Key、明文密码、默认 verbose 倾倒整段对话。

---

## 3. 建议掌握：Span 层级（因果链）

把一次请求想成树，而不是扁平日志：

```text
run (trace_id)
├─ retrieve          latency, hit_k
├─ llm               model, tokens_in/out
├─ tool:search       args_summary, result_preview
├─ llm
└─ end               status, total_latency, total_tokens
```

与 OpenTelemetry 粗映射：`run` = root span；每次 `llm` / `tool` = child span；`trace_id` 贯穿。  
本地起步：把每条事件写成 JSONL 一行，字段与评测 `trace` 兼容，便于同一套 `check_trace`。

---

## 4. 必掌握：Token、延迟与成本

指标建议：

```text
agent_latency_ms (p50/p95)
llm_latency_ms
tool_latency_ms{tool}
tokens_total / tokens_in / tokens_out
cost_estimate
success_rate
max_steps_hit_rate
```

延迟拆解：才能知道是模型慢还是工具慢还是排队。

### 从 usage 汇总成本

```python
# 单价放配置，勿写死在业务里；按「每 1M tokens」计更常见
PRICE_PER_1M = {"gpt-x": {"in": 0.5, "out": 1.5}}  # 示意货币单位


def estimate_cost(model: str, usage: dict) -> float:
    p = PRICE_PER_1M.get(model) or {"in": 0.0, "out": 0.0}
    tin = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    tout = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    return (tin * p["in"] + tout * p["out"]) / 1_000_000
```

把每次 `llm` span 的 cost 累加到 `run` 结束事件；评测报表可并列 `avg_tokens` / `avg_cost`。

---

## 5. 必掌握：工具调用轨迹

保存结构化 span：

```json
{
  "type": "tool",
  "name": "search",
  "args": {"query": "密码策略"},
  "result_preview": "doc:Orion:…",
  "ok": true,
  "latency_ms": 182
}
```

用途：评测轨迹断言、线上事故复盘、提示注入调查。  
`args` / `result_preview` 必须先过允许列表与截断。

---

## 6. 建议掌握：采样与平台

- **错误与慢请求**：全量或高采样  
- **成功快路径**：可降采样，控成本  
- 平台：OpenTelemetry、Langfuse、厂商 tracing 等——先把字段打对，平台是采集与展示  
- 本地：JSONL 落盘即可起步

---

## 7. 了解即可：SLO

例：p95 延迟 < 8s、成功率 > 95%、单次 run 成本 < 预算。  
有基线数据再定，避免拍脑袋。

---

## 8. 练习指引

[`exercises/12-agent-production/02-observability.md`](../../exercises/12-agent-production/02-observability.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能画出 run → llm/tool 的 span 树
- [ ] 有字段允许列表，默认不记完整 messages
- [ ] 能从 usage 估算单次 run 成本
- [ ] 工具轨迹可被评测 `check_trace` 复用

### 下一章

[`03-security.md`](./03-security.md) —— 注入、权限、泄露与沙箱。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Evaluation](./01-evaluation.md)
- 下一章：[Agent Security](./03-security.md)
