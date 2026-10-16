# 练习：Observability

> 对应章节：[`docs/12-agent-production/02-observability.md`](../../docs/12-agent-production/02-observability.md)  
> 建议时间：45～75 分钟  
> 难度：★★★★☆

## 目标

给 Agent 请求加上结构化日志、关键指标与简易 trace。

## 任务清单

### A. 结构化日志（必做）

在 Agent 入口生成 `trace_id`（uuid），全程写入每次：

- LLM 调用开始/结束（model、latency_ms、token 估算）
- 工具调用（name、ok、latency_ms）
- 最终状态（success / error）

日志用 JSON 行格式写到 `playground/12-agent-production/observability/app.log`。

### B. 指标计数（必做）

用内存 dict 或简单类统计：

- `requests_total`
- `errors_total`
- `tool_calls_total`（可按 name）
- `latency_ms` 列表（或 p50/p95 简易计算）

提供 `GET /metrics`（FastAPI）或 CLI `print_metrics()`。

### C. Trace 树（必做）

实现 `TraceSpan`：`name, start, end, children, attrs`。  
一次请求结束后 `dump_trace(trace_id)` 打印树形结构。

### D. 允许列表与成本（必做）

1. 定义日志字段允许列表：默认不写完整 `messages` / API Key  
2. `args` / `result_preview` 经截断与白名单后再落盘  
3. 用假 `usage` 实现 `estimate_cost(model, usage)`，在 run 结束打印累计成本  

### E. 错误关联（建议）

故意制造一次工具异常，确认日志里同一 `trace_id` 能串起入口 → 工具失败 → 响应错误。

## 验收标准

- [ ] 任意一次请求可凭 `trace_id` 在日志中还原路径
- [ ] 有可展示的 metrics
- [ ] 有 span 树输出（run → llm/tool）
- [ ] 完整 messages / Key 不会出现在日志里；有成本估算

## 提示

- 不必上 OpenTelemetry SDK；先自研最小实现再对照概念迁移
- 密钥、用户原文不要明文进日志；对照正文 §2.2 允许列表
