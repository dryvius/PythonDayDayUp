# Project 6：Research Agent

> 状态：`已完成实战说明`  
> 建议时机：完成模块 11～12 后  
> 建议工时：16～30 小时  
> 推荐目录：`playground/projects/06-research-agent/`  
> 运行环境：Python ≥ 3.11 · FakeLLM / 刻意简化见 [`../CONVENTIONS.md`](../CONVENTIONS.md)

## 项目目标

做一个「可研究、可引用、可评测、可观测」的小型研究 Agent：多步工具、记忆/材料夹、异步 Job、最小评测与安全护栏。这是课程收官集成件。

## 你将练习到的能力

| 模块 | 知识点 |
|------|--------|
| 11 | Agent 环、可选图编排、短记忆 |
| 10 | 检索作工具、引用 |
| 07 | 队列/Job 状态机（可用内存队列起步） |
| 12 | 评测回归、trace、工具 ACL、降级、成本边界 |

## 需求概述

### 功能

1. 用户给研究主题 → Agent 分解步骤（可写死计划模板 + LLM 填空）  
2. 工具：`search_kb`（可接 Project 4）、`fetch_url`（建议 mock）、`write_note`、`finalize_report`  
3. 输出 Markdown 报告：**结论 + 引用列表**；材料不足要写明缺口  
4. `POST /v1/jobs` 入队，`GET /v1/jobs/{id}` 查状态（同步短路径可保留作调试）  

### 非功能

- FakeLLM + mock 工具下可全链路演示；`complete` → **assistant dict**  
- smoke 评测集 ≥5（含：应拒答、应引用、禁止 shell）；**强制**对齐 [`playground/12-agent-production/evaluation/`](../../playground/12-agent-production/evaluation/) 的 harness 约定  
- Notes/长期记忆写入必须过 `should_write_long_term`（可复用 [`playground/11-agent-core/memory/`](../../playground/11-agent-core/memory/)）  
- 结构化日志带 `trace_id` / `job_id`；字段允许列表，**默认不记完整 messages / API Key**  
- 危险工具默认不注册；ACL 默认拒绝（**含参数级**：URL host、路径前缀）  
- 成本控制：`max_steps`、工具超时、可选预算计数  
- **长任务上队列**；勿用 FastAPI `BackgroundTasks` 扛研究 Job（CONVENTIONS）  

## 建议架构

```text
Client → FastAPI
          ├─ POST /v1/jobs → Queue
          └─ GET  /v1/jobs/{id}
                ↓
             Worker → Agent Runtime
                        ├─ LLM Adapter
                        ├─ Tools (ACL)
                        ├─ Memory / Notes
                        └─ (可选) RAG
                ↓
             Observability + eval/cases.jsonl
```

## 建议目录

```text
playground/projects/06-research-agent/
├── app/
│   ├── api/
│   ├── worker/
│   ├── agent/
│   ├── tools/
│   ├── llm/
│   └── obs/                 # log metrics trace
├── eval/
│   ├── cases.jsonl
│   ├── run_eval.py
│   └── baseline.json
├── app/memory/              # Store + 拒写
├── tests/
├── compose.yaml             # 可选 redis
└── README.md
```

若用 Redis：`LIST`+`BRPOP` 仅演示入队出队（**不是** at-least-once，见 CONVENTIONS）；可靠 Job 请用带 ack / 可见性超时的机制，或先用内存队列把状态机跑通。

## 起步建议（第一天）

1. **先同步 Fake 全链路**：主题 → 工具 → 带 citations（或缺口）的短报告  
2. 再抽 Job：内存队列 + `job_id` 状态机；给每条日志打上 `trace_id`  
3. 接入模块 12 harness（`cases.jsonl` + baseline）；最后补 ACL / 记忆拒写单测  

必读章节：

- [Evaluation](../12-agent-production/01-evaluation.md)  
- [Observability](../12-agent-production/02-observability.md)  
- [Security](../12-agent-production/03-security.md)  
- [系统设计](../12-agent-production/04-system-design.md)  
- 前置项目：[Tool Agent](./05-tool-agent.md) · [RAG](./04-rag-kb.md)  

## 里程碑

- [ ] **M1**：同步 Agent 出带引用的短报告（Fake 全链路）  
- [ ] **M2**：Job 队列 + 状态查询；trace_id（非 BackgroundTasks 冒充）  
- [ ] **M3**：评测回归脚本（`--write-baseline` / 改坏见 regressions）；ACL（名+参）；记忆污染单测  
- [ ] **M4**（可选）：真 LLM + 真检索；基线对比  

## 验收标准

- [ ] Fake 模式下：创建 Job → 轮询 → succeeded，报告含 citations 或明确缺口  
- [ ] `run_eval.py` 对齐模块 12 最小 harness（cases.jsonl + baseline 对比）；改坏 prompt 能出现 regressions  
- [ ] 未授权工具无法执行（有测试）；注入内容不得写入长期记忆（有测试）  
- [ ] 日志遵守字段允许列表；README 含架构图、环境变量、演示脚本  

## 设计检查清单（对照模块 12）

- [ ] 同步/异步边界清晰（短问答 vs Job）  
- [ ] 超时 / 重试 / 幂等（job_id）  
- [ ] 日志脱敏；不默认倾倒 messages  
- [ ] 评测集进仓库（脱敏）；Fake CI 可绿  
- [ ] 降级与人工兜底说明  
- [ ] 成本：`max_steps` / 超时 / 可选预算  

## 常见易错

| 坑 | 正确做法 |
|----|----------|
| 用 `BackgroundTasks` 扛长研究 | 上队列 + Worker（CONVENTIONS） |
| 以为 `LIST`+`BRPOP` = at-least-once | 仅演示；可靠投递另选机制 |
| 只测同步路径 | Job 轮询 + Fake 全链路验收 |
| ACL 只有工具名 | `fetch_url` / 路径必须参数级拒绝 |
| 日志打满 prompt | 允许列表 + preview 截断 |
| baseline 悄悄下调 | 确认整体变好再 `--write-baseline` |
| 无拒答 / 无缺口说明 | 材料不足必须写明，评测有对应 case |

## 延伸挑战

- Human-in-the-loop：finalize 前确认  
- 将微型图执行器用于「检索失败 → 改写再检索」  
- 简单前端展示 Job 进度  

## 导航

- 返回项目列表：[./README.md](./README.md)
- 相关文档：[生产模块](../12-agent-production/README.md) · [Tool Agent](./05-tool-agent.md) · [RAG](./04-rag-kb.md)
- 约定：[../CONVENTIONS.md](../CONVENTIONS.md)
- 返回总览：[../../README.md](../../README.md)
