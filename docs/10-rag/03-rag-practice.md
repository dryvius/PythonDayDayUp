# RAG 实战与调优

> 所属模块：`10-rag` · Embedding 与 RAG  
> 状态：`已完成正文`  
> 建议学时：4～7 小时  
> 对应练习：[`exercises/10-rag/03-rag-practice.md`](../../exercises/10-rag/03-rag-practice.md)

## 本章定位

- **本章角色**：落地最小可用知识库；学会评测召回；认识并排查常见失败；做 chunk 策略实验。
- **产出**：一个可演示的「文档问答」闭环（可用 Fake embedding + 内存索引）。

## 学习目标

1. 实现最小 RAG（ingest → ask）。
2. 用简单指标评估召回（命中率等）。
3. 对照失败模式清单排障。
4. 会做 chunk 大小/重叠对比实验。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 最小知识库、评测召回、失败模式 | 能跑通并诊断 |
| **建议掌握** | chunk 策略实验 | 能用数据说话 |
| **了解即可** | 多模态 RAG | 扫盲 |

---

## 1. 最小可用知识库（MVP）

组件：

```text
DocumentStore   原文与元数据（可先文件/SQLite）
Chunker         切分
Embedder        向量化（可 Fake）
VectorIndex     内存 list 或真向量库
Generator       LLM（可 Fake：返回“基于资料：...”）
```

API 形状：

```text
POST /ingest  {source, text}
POST /ask     {question, top_k} → {answer, citations[]}
```

本地库函数亦可：

```python
class MiniRAG:
    def ingest(self, source: str, text: str) -> int: ...
    def ask(self, question: str, top_k: int = 3) -> dict: ...
```

---

## 2. 必掌握：评测——先检索，再生成

两套指标**分开**看，别搅在「召回」一个篮子里。

### 2.1 检索侧

准备小题集：

```text
question → 期望应命中的 source 或 chunk_id 集合
```

| 指标 | 含义 |
|------|------|
| Hit@K | Top-K 是否命中**任一**期望项 |
| MRR | 第一个相关结果有多靠前 |

```python
def hit_at_k(retrieved_sources: list[str], expected: set[str], k: int) -> bool:
    return any(s in expected for s in retrieved_sources[:k])
```

注意：

- **K 越大 Hit@K 通常越高**（单调不降）；对比实验要固定 K，或同时看 MRR / 更小 K
- 用粗 `source` 比精确 `chunk_id` 更容易「看起来很好」；标注粒度要写进题集说明

### 2.2 生成侧（另开账）

| 指标 | 含义 |
|------|------|
| 忠实度 | 答案是否有材料支撑（人工 / 谨慎使用 LLM-as-judge） |
| 有用性 | 是否回答了问题（与检索好坏分开记） |

检索差 → 先改切分/embedding/过滤；生成胡编 → 先改提示与「无材料则拒答」，别只狂调 chunk。

没有题集就无法调参——凭感觉改 chunk 会空转。

---

## 3. 必掌握：常见失败模式

1. **建库了但没 embed 成功**（静默空索引）  
2. **查询向量与文档向量模型不一致**  
3. **切分破坏表格/代码块**  
4. **Top-K 过大，prompt 噪声淹没**  
5. **未过滤权限，串租户**  
6. **提示允许瞎编**，材料不足仍给确定答案  
7. **重复文档未去重**，浪费上下文  
8. **更新文档未重建对应向量**（脏索引）  
9. **间接提示注入**：网页/PDF 等检索正文不可信，可能诱导模型乱调工具或泄露数据（缓解见模块 09 分隔符弱缓解 + 模块 12 工具 ACL；citations ≠ 授权）

排障顺序：

```text
索引是否非空？ → 手工看 Top-K 文本是否相关？
→ 换 query 改写？ → 调 K/阈值/切分？ → 再看生成提示
```

---

## 4. 建议掌握：chunk 实验

固定题集，只改一个变量：

| 实验 | 变量（单位：tokens，用同一 tokenizer） |
|------|------|
| A | chunk_size=200 vs 500 vs 800 tokens |
| B | overlap=0 vs 50 vs 100 tokens |
| C | K=3 vs 5 vs 8 |

记录 Hit@K 与主观答案质量，选帕累托可接受点。

---

## 5. 了解即可：多模态 RAG

图文 PDF、截图 OCR、图像向量……链路更长。  
文本 RAG 稳了再加。

---

## 6. 综合伪实现要点

```python
def ingest(self, source: str, text: str) -> int:
    chunks = chunk_text(text, size=500, overlap=50)  # size/overlap：tokens
    vectors = self.embedder.embed(chunks)
    for t, v in zip(chunks, vectors, strict=True):
        self.index.add(Chunk(text=t, vector=v, source=source))
    return len(chunks)


async def ask(self, question: str, top_k: int = 3) -> dict:
    qv = self.embedder.embed([question])[0]
    hits = self.index.search(qv, k=top_k)
    messages = build_rag_prompt(question, [h.__dict__ for h in hits])
    # complete 返回 assistant dict（见 CONVENTIONS / 模块 09）
    assistant = await self.llm.complete(messages)
    answer = assistant.get("content") or ""
    return {
        "answer": answer,
        "citations": [{"source": h.source, "text": h.text[:120]} for h in hits],
    }
```

---

## 7. 练习指引

[`exercises/10-rag/03-rag-practice.md`](../../exercises/10-rag/03-rag-practice.md)

---

## 8. 小结与下一站

### 自检

- [ ] 有可运行的 ingest/ask
- [ ] 至少 5 道题的 Hit@K 统计
- [ ] 能按失败模式清单排查

### 模块 10 收官

下一模块：[`../11-agent-core/README.md`](../11-agent-core/README.md) —— Agent 核心开发（Tool Calling 起）。

也可对照总览 **Project 4：RAG 知识库** 做完整小项目。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[RAG 架构](./02-rag-architecture.md)
- 下一模块：[Agent 核心开发](../11-agent-core/README.md)
