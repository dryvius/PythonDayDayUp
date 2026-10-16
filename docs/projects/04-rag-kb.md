# Project 4：RAG 知识库

> 状态：`已完成实战说明`  
> 建议时机：完成模块 10 后  
> 建议工时：12～20 小时  
> 推荐目录：`playground/projects/04-rag-kb/`

## 项目目标

从本地文档建库 → 检索 → 带引用生成答案；有最小评测集；Fake embedding 可跑通管线。

## 你将练习到的能力

| 模块 | 知识点 |
|------|--------|
| 09 | Prompt 约束「仅依据资料」、结构化引用 |
| 10 | Chunk、Embedding、Top-K、元数据、Hit@K、失败模式 |
| 06/07 | 可选：API 化 + 索引元数据存 DB |

## 需求概述

### 功能

1. **建库**：指定目录 ingest（至少支持 `.md`/`.txt`）  
2. **问答**：`ask(question) -> {answer, citations: [{source, snippet}]}`  
3. 无命中或材料不足 → 明确拒答，不瞎编  
4. CLI 或 FastAPI 二选一（推荐先 CLI 再挂 API）  

### 非功能

- 学习期可用 Fake embedding + 内存索引；接口预留真模型  
- 切分默认用 **同一 tokenizer 计 token**（与模块 10 一致）；若改用字符策略，必须在 README 标明且评测固定口径，**不得与 token 实验混比**  

- 小题集 ≥8：含应命中 / 应拒答  
- 检索指标与生成忠实度**分开**记录  

## 建议目录

```text
playground/projects/04-rag-kb/
├── app/
│   ├── chunking.py
│   ├── embed.py             # Fake + 真实现
│   ├── index.py             # 内存或 chroma/pgvector
│   ├── retrieve.py
│   ├── generate.py
│   └── pipeline.py          # ingest / ask
├── data/sample_docs/
├── eval/cases.json
├── scripts/run_eval.py
├── tests/
└── README.md
```

## 里程碑

- [ ] **M1**：ingest + 暴力 Top-K；能打印命中 chunk  
- [ ] **M2**：组装 Prompt + Fake/真 LLM 生成；强制引用格式  
- [ ] **M3**：`run_eval.py` 输出 Hit@K；至少一组拒答 case 通过  

## 验收标准

- [ ] 换 embedding 实现不改 pipeline 签名  
- [ ] 评测可一键跑；结果可复现（Fake 路径）  
- [ ] README 写明 chunk 参数、K、过滤策略  
- [ ] 不把私有文档密钥提交进 git（sample 用公开假数据）  

## 延伸挑战

- Hybrid（关键词 + 向量）或简易 rerank  
- `tenant_id` 元数据过滤（造两条租户数据证明不串）  
- 文档更新后增量重建  

## 导航

- 返回项目列表：[./README.md](./README.md)
- 相关文档：[Embedding](../10-rag/01-embedding-vector-search.md) · [架构](../10-rag/02-rag-architecture.md) · [实战](../10-rag/03-rag-practice.md)
- 返回总览：[../../README.md](../../README.md)
