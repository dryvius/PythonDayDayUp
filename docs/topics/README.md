# 专题（非主线编号）

主线仍是模块 01～12。本目录放**加深专题**：不占大模块名额，学有余力或项目卡壳时再读。

约定见 [`../CONVENTIONS.md`](../CONVENTIONS.md)（Python ≥ 3.11、FakeLLM、刻意简化清单）。

## 这一线是什么（也是什么不是）

| | 专题（本目录） | 主线 `docs/01～12` | 项目 `docs/projects/` |
|---|---|---|---|
| **产出** | 决策地图 + 进阶边界 + 何时上/不上 | 辅导正文（为什么→怎么写→跑一下） | 规格与验收 |
| **默认** | **了解即可**；有评测/卡壳再深挖 | 必掌握按章自检 | 阶段性做 |
| **不要** | 代替主线 Memory / Eval 章 | 代替专题的「业界名词对照」 | 在这里写完整实现 |

先过主线门槛，再读专题；专题里的「工程清单」不过关时，**不要**上图谱 / 平台级 harness。

## 专题列表

| 专题 | 说明 | 主线挂靠 | 何时读 |
|------|------|----------|--------|
| [记忆工程进阶](./memory-engineering.md) | 摘要树 / 图谱 / 向量长期记忆 / OS 式记忆地图 | [11 · Memory](../11-agent-core/05-agent-memory.md) + playground Store | Store 污染单测已绿，仍不够用时 |
| [Agent Harness 总览](./agent-harness.md) | Runtime 外壳 vs Eval harness，名词不打架 | [11 手写 Agent](../11-agent-core/02-handwritten-agent.md) · [12 Eval](../12-agent-production/01-evaluation.md) | 做 Project 5/6 或对接业界「harness」说法时 |

## 可跑示例

- Memory Store：[`../../playground/11-agent-core/memory/`](../../playground/11-agent-core/memory/)
- Eval harness：[`../../playground/12-agent-production/evaluation/`](../../playground/12-agent-production/evaluation/)

## 建议读法

```text
主线章节自检通过
  → 跑通对应 playground
  →（卡壳 / 要选型）再读专题地图
  → 有评测证明收益，再上进阶实现
```

每篇专题保留：定位 → 你已有什么 → 进阶地图 → 决策/易错 → 工程清单 → 导航。

## 导航

- 返回总览：[../../README.md](../../README.md)
- 约定：[../CONVENTIONS.md](../CONVENTIONS.md)
- 项目线：[../projects/README.md](../projects/README.md)
