# 实战项目线

项目线与文档主线并行：学完相关模块后立刻做项目，用项目反哺「为什么要学」。

约定见 [`../CONVENTIONS.md`](../CONVENTIONS.md)（Python ≥ 3.11、FakeLLM、刻意简化清单）。

## 项目列表

| # | 项目 | 建议时机 | 状态 |
|---|------|----------|------|
| 1 | [Python CLI 工具](./01-cli-tool.md) | 模块 01～03 后 | 实战说明已齐 |
| 2 | [FastAPI Todo](./02-fastapi-todo.md) | 模块 05～07 核心后 | 实战说明已齐 |
| 3 | [AI Chat](./03-ai-chat.md) | 模块 09 后 | 实战说明已齐 |
| 4 | [RAG 知识库](./04-rag-kb.md) | 模块 10 后 | 实战说明已齐 |
| 5 | [Tool Agent](./05-tool-agent.md) | 模块 11 前半后 | 实战说明已齐 |
| 6 | [Research Agent](./06-research-agent.md) | 模块 11～12 后 | 实战说明已齐（收官集成） |

推荐代码目录：`playground/projects/0x-.../`（可按项目文档搭建）。

可先跑的最小示例（非完整项目）：

- Memory Store：[`../../playground/11-agent-core/memory/`](../../playground/11-agent-core/memory/)
- Eval harness：[`../../playground/12-agent-production/evaluation/`](../../playground/12-agent-production/evaluation/)
- 专题总览：[`../topics/README.md`](../topics/README.md)

## 建议节奏

```text
文档小章节 → 练习题 →（阶段性）项目里程碑
```

不要等「全部学完」再做项目。Project 6 刻意集成评测、观测与安全，作为主线收官。

## 导航

- 返回总览：[../../README.md](../../README.md)
- 课程约定：[../CONVENTIONS.md](../CONVENTIONS.md)
