# Embedding 与向量检索

> 所属模块：`10-rag` · Embedding 与 RAG  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/10-rag/01-embedding-vector-search.md`](../../exercises/10-rag/01-embedding-vector-search.md)

## 本章定位

- **模块目标**：能构建可用的知识库问答系统，并理解失败原因。
- **本章角色**：弄清 Embedding 是什么、相似度如何度量、向量库扮演什么角色——RAG 的检索地基。
- **前置**：模块 09 的 LLM / Token / 结构化输出基础。

## 学习目标

1. 用自己的话解释 Embedding。
2. 理解余弦相似度等常用度量及使用注意。
3. 说清向量库与「暴力扫 list」的差异。
4. 对常见向量库与 ANN 有选型级认知。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | Embedding、相似度、向量库角色 | 能讲清检索链路 |
| **建议掌握** | 常见向量库对比 | 能做初步选型 |
| **了解即可** | ANN 算法 | 扫盲 |

---

## 1. 为什么要学

LLM 不会自动知道你公司的私有文档。  
RAG 的第一步是：**把文档变成可检索的向量，按问题找出相关片段**。

```text
文档 → 切分 → Embedding → 写入向量库
问题 → Embedding → 近邻检索 → 得到 chunks
```

---

## 2. 必掌握：Embedding 是什么

Embedding = 把文本映射到**稠密向量**（如 768/1536 维浮点数组），使语义相近的文本在空间中更近。

直觉：

```text
"如何重置密码" ≈ "忘记密码怎么办"
两者向量距离更近；与 "今天股市" 更远
```

工程点：

- 查询与文档向量必须在**同一嵌入空间**（多数句向量：同一模型；少数双塔：配套的 query/doc encoder，仍属「一套体系」）
- 模型升级通常要**重建索引**
- 有长度限制；超长文本先切分再嵌入

```python
# 概念接口
async def embed(texts: list[str]) -> list[list[float]]:
    ...
```

可用：云 API embedding、开源句向量模型、本地服务。学习阶段可用假 embedding（哈希到固定维）验证管线，但语义质量不会好。

---

## 3. 必掌握：相似度

常用：

| 度量 | 直觉 |
|------|------|
| 余弦相似度 | 看方向夹角，常用 |
| 点积 | 与归一化向量搭配时近余弦 |
| 欧氏距离 | 看直线距离，需注意尺度 |

注意：

- 比较前是否 **L2 归一化** 会影响点积含义
- 「分数高就绝对相关」不一定：阈值差、同主题干扰都存在
- Top-K 是相对排序，要配合阈值与业务过滤

```python
import math


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-12)
```

---

## 4. 必掌握：向量库角色

向量库负责：

```text
存储向量 + 元数据
高效近似最近邻检索（ANN）
过滤（按租户、文档类型、时间…）
```

相对「把所有向量放 Python list 里扫」：

| | list 暴力 | 向量库 |
|--|-----------|--------|
| 数据量小 | 可用 | 可选 |
| 数据量大 | 太慢 | 必要 |
| 过滤/持久化 | 自己造 | 现成 |

元数据示例：`doc_id`、`source`、`chunk_id`、`permissions`。

---

## 5. 建议掌握：常见向量库对比（认知）

| 选项 | 粗印象 |
|------|--------|
| pgvector | PG 扩展，栈统一 |
| Chroma | 本地/原型友好 |
| Qdrant / Milvus / Weaviate | 专用向量库，能力强 |
| 云托管向量检索 | 少运维 |

选型看：数据规模、过滤需求、是否已有 PG、运维能力、延迟/成本。

---

## 6. 了解即可：ANN

HNSW、IVF 等近似算法：用少许精度换数量级速度。

要点：

- **ANN ≠ 精确 Top-K**：暴力余弦阈值不能直接当成 ANN 上的同一阈值
- 评测 Hit@K 时要标明是否 ANN，以及索引参数
- 与元数据过滤组合时另有坑（见下一章）

参数影响召回与延迟；调参属进阶。

---

## 7. 最小内存检索示例

```python
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    vector: list[float]
    source: str


def search(query_vec: list[float], chunks: list[Chunk], k: int = 3) -> list[Chunk]:
    ranked = sorted(
        chunks,
        key=lambda c: cosine(query_vec, c.vector),
        reverse=True,
    )
    return ranked[:k]
```

---

## 8. 练习指引

[`exercises/10-rag/01-embedding-vector-search.md`](../../exercises/10-rag/01-embedding-vector-search.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能解释 embedding 与相似度
- [ ] 知道为何需要向量库与元数据
- [ ] 能写暴力 Top-K 检索原型

### 下一章

[`02-rag-architecture.md`](./02-rag-architecture.md) —— 把检索接到生成，形成完整 RAG。

## 导航

- 返回模块：[README](./README.md)
- 下一章：[RAG 架构](./02-rag-architecture.md)
