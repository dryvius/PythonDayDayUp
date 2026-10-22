# 模块 12-agent-production：Agent 工程化与生产落地

> 状态：`四章正文与练习已全部完成` · 预计周期：2～3 周

## 模块目标

具备评测、可观测、安全与系统设计能力，接近生产级。

## 为什么现在学

Demo 与生产的鸿沟主要在这里：没有评测就没有迭代，没有观测就无法排障，没有安全护栏就不能对外开放，没有系统设计就只会堆功能。

## 章节目录

1. [Agent Evaluation](./01-evaluation.md) · [练习](../../exercises/12-agent-production/01-evaluation.md)
2. [Observability](./02-observability.md) · [练习](../../exercises/12-agent-production/02-observability.md)
3. [Agent Security](./03-security.md) · [练习](../../exercises/12-agent-production/03-security.md)
4. [Agent 系统设计](./04-system-design.md) · [练习](../../exercises/12-agent-production/04-system-design.md)

## 建议学习方式

1. 严格按顺序：评测 → 观测 → 安全 → 系统设计（每章保留知识地图骨架；知识点按「为什么 → 怎么写 → 跑一下 → 易错点」推进）
2. 用你在模块 11 / Project 5～6 里的 Agent 作为实验对象；先落地最小 harness 与 trace，再谈安全与架构
3. 系统设计章以「可评审文档」为目标，不必一次写完全部代码
4. 全程可用 FakeLLM；评测与 CI 必须能离线复现（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）

## 模块自检

- [ ] 能跑通最小 harness（cases.jsonl → report → baseline 对比；Fake 可离线）
- [ ] 能用 trace_id 串起一次请求的日志与指标
- [ ] 能说明注入风险与工具 ACL / 脱敏策略
- [ ] 能画出同步/异步边界与降级路径
- [ ] 能做一份可评审的系统设计检查清单

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Agent 核心开发](../11-agent-core/README.md)
- 项目线：[../projects/README.md](../projects/README.md)
