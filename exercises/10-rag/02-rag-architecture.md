# 练习：RAG 架构

> 对应文档：[`docs/10-rag/02-rag-architecture.md`](../../docs/10-rag/02-rag-architecture.md)  
> 状态：`已完成出题` · 建议用时：50～80 分钟

---

## 基础题（必做）

### B1. 流程图

分别画出「建库」与「问答」两段流程（可用 markdown）。

### B2. Chunker

实现 `chunk_text(text, size, overlap)`，断言重叠行为符合预期（用短文本手工算）。

### B3. 召回问题分类

给出 4 个故障现象，归类到空/偏/编/权限，并各写一条处理方向。

### B4. Prompt 组装

实现 `build_rag_prompt(question, chunks)`，包含「资料不足要承认」的系统约束。

---

## 进阶题（建议）

### A1. Hybrid 直觉（书面）

举 2 个更适合关键词、2 个更适合向量语义的查询例子。

### A2. Rerank 位置

在流程图上标出 rerank 插入点，并写延迟/成本权衡 3 行。

---

## 挑战题（可选）

### C1. 权限过滤伪代码

写 `search(query, user)` 必须带 `tenant_id` 过滤的伪代码，防止漏写。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
