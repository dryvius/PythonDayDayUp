# AI 发展脉络与名词词典

> 所属模块：`09-ai-llm` · AI / LLM 基础与认知地图  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/09-ai-llm/01-ai-landscape-glossary.md`](../../exercises/09-ai-llm/01-ai-landscape-glossary.md)

## 本章定位

- **模块目标**：对现阶段 AI 发展与常用名词建立较深入认知，并能调用 LLM。
- **本章角色**：统一术语地图——后续 RAG / Agent 不再被名词吓住。
- **路线提醒**：目标是 Agent 工程，不是先成为训练大模型的算法研究员。

## 学习目标

1. 准确解释 LLM、Token、Context Window。
2. 分清预训练 / 微调 / 推理（inference）。
3. 分清 Chat 与 Completion 形态。
4. 建立 RAG / Agent / Tool / Embedding 总览与开闭源格局直觉。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | LLM/Token/Context、预训练/微调/推理、Chat vs Completion | 能对外讲清 |
| **建议掌握** | RAG/Agent/Tool/Embedding、开闭源格局 | 能画关系图 |
| **了解即可** | 训练细节与论文脉络 | 扫盲 |

---

## 1. 极简脉络（工程视角）

```text
统计学习 / 深度学习
  → 表示学习与大模型规模化
  → Transformer 成为主流骨架
  → 大规模预训练语言模型（LLM）
  → 对齐（指令跟随/对话）后成为 Chat 产品
  → 工具调用 + RAG + Agent 进入应用工程主战场
```

你要站的位置：

> **应用层：API → 编排 → 数据 → 评测 → 生产化**

---

## 2. 必掌握：LLM / Token / Context Window

### LLM

Large Language Model：在大规模文本上训练的生成式模型，核心能力是**根据上下文预测续写**；对齐后表现为对话、指令跟随。

### Token

模型读写文本的基本单位（子词/字节级等），**不等于汉字或英文单词一一对应**。

工程含义：

- 计费常按 token
- 上下文长度按 token 限制
- **不要用「字数 ≈ token」估预算**：中文往往比英文「每词」更贵，但系数因分词器差异很大，只能当数量级直觉。**唯一准绳**是目标模型的 tokenizer / 响应里的 `usage`。

### Context Window

一次请求里模型能「看见」的上下文上限；**计法因厂商而异**：

- 常见：input + output **合计**不超过窗口
- 也有：input / output **分项上限**

它不是「会话永久记忆」。RAG / 外挂库扩大的是**可检索资料**，不会自动增大模型窗口本身。

爆窗后果：截断、拒绝、质量下降。  
Agent 必须做：历史截断、摘要、RAG 只塞相关片段。

---

## 3. 必掌握：预训练 / 微调 / 推理

| 阶段 | 做什么 | 你常不常做 |
|------|--------|------------|
| 预训练 Pretrain | 海量数据上学语言规律 | 很少自己做 |
| 微调 Finetune | 用领域数据改行为 | 有时（LoRA 等） |
| 推理 Inference | 用训练好的模型生成 | **天天做** |

相关词：

- **SFT**：监督微调
- **RLHF / 偏好优化**：让模型更符合人类偏好
- **对齐 Alignment**：更安全、更听指令

Agent 开发默认：调用已对齐好的 Chat 模型 API。

---

## 4. 必掌握：Chat vs Completion

| | Completion | Chat |
|--|------------|------|
| 形态 | 续写一段文本 | 消息列表（system/user/assistant/...） |
| 现代 API | 仍存在 | **主流** |
| Agent | 少直接用 | 会话、工具循环都基于 messages |

消息角色直觉：

```text
system     设定规则与人设
user       用户输入
assistant  模型回复
tool       工具结果回传（工具调用场景）
```

---

## 5. 建议掌握：RAG / Agent / Tool / Embedding 总览

```text
Embedding：文本 → 向量，用于相似度检索
RAG：先检索知识，再让 LLM 基于材料生成
Tool：模型可调用的外部能力（搜索、DB、代码…）
Agent：模型 + 记忆/规划 + 工具循环，完成多步任务
```

关系：

```text
Chat LLM 是引擎
RAG 给它外挂知识
Tool 给它行动能力
Agent 是编排这些能力的系统
```

---

## 6. 建议掌握：开源 vs 闭源格局（认知级）

| 类型 | 特点 | 选用直觉 |
|------|------|----------|
| 闭源 API | 强、省运维、数据出域需评估 | 快速做产品 |
| 开源可自托管 | 可控、可私有化、要算力与工程 | 合规/成本/定制 |

没有永远的「第一」；工程上做 **适配层**，避免写死一家 SDK。

---

## 7. 了解即可：训练与论文

Attention、MoE、并行训练、缩放定律……感兴趣再读。  
不影响你先做出 Agent。

---

## 8. 名词速查（常挂嘴边）

| 名词 | 一句话 |
|------|--------|
| Hallucination | 一本正经胡说 |
| Temperature | 采样随机性，影响稳/活 |
| Top-p | 核采样，另一种多样性控制 |
| Latency | 延迟 |
| Throughput | 吞吐 |
| Function/Tool Calling | 结构化调用外部工具 |
| Multimodal | 多模态（图文等） |
| Guardrails | 安全护栏 |

---

## 9. 练习指引

[`exercises/09-ai-llm/01-ai-landscape-glossary.md`](../../exercises/09-ai-llm/01-ai-landscape-glossary.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能讲清 Token 与上下文窗口为何限制 Agent 设计
- [ ] 能区分预训练/微调/推理
- [ ] 能画 RAG/Tool/Agent 关系

### 下一章

[`02-llm-api.md`](./02-llm-api.md) —— 真正调用 Chat API。

## 导航

- 返回模块：[README](./README.md)
- 下一章：[LLM API 实战](./02-llm-api.md)
