# 练习：RAG 实战与调优

> 对应文档：[`docs/10-rag/03-rag-practice.md`](../../docs/10-rag/03-rag-practice.md)  
> 状态：`已完成出题` · 建议用时：90～150 分钟

目录建议：`playground/10-rag/03-rag-practice/`

---

## 基础题（必做）

### B1. MiniRAG.ingest / ask

实现最小类：内存索引 + Fake embed + Fake LLM（答案中拼接命中的 source 列表亦可）。  
ingest 至少 2 篇短文档，ask 返回 `answer` + `citations`。

### B2. 题集

准备 ≥5 条 `{question, expected_sources}`。

### B3. Hit@K

实现 `hit_at_k`，对题集跑一遍，打印平均命中率。

### B4. 失败模式演练

故意制造 2 种失败（如 empty index、过滤过严），写下你如何从症状定位。

---

## 进阶题（建议）

### A1. Chunk 对比实验

至少两组 `size/overlap`，同一题集比 Hit@K，结果写入 `experiment.md`。

### A2. 生成约束

改 prompt：资料不足时 FakeLLM/规则必须返回固定「不知道」文案；加测试断言。

---

## 挑战题（可选）

### C1. 对接真 embedding 或真 LLM

有条件则换真模型，对比 Fake 的 Hit@K/体验；无名与费用注意脱敏。

---

## 模块 10 通关自检

- [ ] 理解 embedding/相似度/向量库
- [ ] 能画出并实现 RAG 主链路
- [ ] 有题集与 Hit@K
- [ ] 能按失败模式排障

完成后进入模块 11《Agent 核心开发》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
