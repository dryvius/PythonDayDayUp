# 模块 10-rag：Embedding 与 RAG

> 状态：`三章正文与练习已全部完成` · 预计周期：2 周

## 模块目标

能构建可用的知识库问答系统，并理解失败原因。

## 为什么现在学

企业 Agent 最常见落地形态之一：先检索私有知识，再生成回答。RAG 也是进入 Tool/Agent 前最重要的应用拼图。

## 章节目录

1. [Embedding 与向量检索](./01-embedding-vector-search.md) · [练习](../../exercises/10-rag/01-embedding-vector-search.md)
2. [RAG 架构](./02-rag-architecture.md) · [练习](../../exercises/10-rag/02-rag-architecture.md)
3. [RAG 实战与调优](./03-rag-practice.md) · [练习](../../exercises/10-rag/03-rag-practice.md)

## 建议学习方式

1. 先用 Fake embedding + 内存索引把管线跑通，再换真模型/向量库（每章保留知识地图骨架；知识点按「为什么 → 怎么写 → 跑一下 → 易错点」推进）
2. 第三章务必准备题集，用 Hit@K 指导调参
3. 始终区分「检索问题」与「生成问题」
4. 可与总览 Project 4（RAG 知识库）合并完成；先自己写再对照文档

## 模块自检

- [ ] 能解释 Embedding 与相似度，并实现暴力 Top-K
- [ ] 能画出切分/检索/生成流水线并做元数据过滤
- [ ] 能交付 MiniRAG + 题集评测 + 失败排障笔记

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[AI / LLM 基础](../09-ai-llm/README.md)
- 下一模块：[Agent 核心开发](../11-agent-core/README.md)
