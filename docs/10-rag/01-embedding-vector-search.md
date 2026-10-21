# Embedding 与向量检索

> 所属模块：`10-rag` · Embedding 与 RAG  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（无 API Key 用 Fake embedding + 内存 list 也能跑通主线；有 Key / 本地模型再换真嵌入）  
> 对应练习：[`exercises/10-rag/01-embedding-vector-search.md`](../../exercises/10-rag/01-embedding-vector-search.md)

## 本章定位

- **模块目标**：能构建可用的知识库问答系统，并理解失败原因。
- **本章角色**：弄清 Embedding 是什么、相似度如何度量、向量库扮演什么角色——RAG 的检索地基。
- **前置**：模块 09 的 LLM / Token / 结构化输出基础；知道「把资料塞进 Prompt」有长度与成本上限。
- **实践约定**：学习阶段优先 **Fake embedding + 内存暴力 Top-K** 验证管线；语义质量以后再换真模型。真向量库与 ANN 先建立选型级认知。
- **目标不是**：背全向量库文档或成为 ANN 算法研究员；能讲清链路、能写最小检索、能做初步选型即可。

## 学习目标（学完应能做到）

1. 用自己的话解释 Embedding：文本 → 稠密向量，语义近则空间近。
2. 理解余弦相似度、点积、欧氏距离的直觉与归一化注意点。
3. 说清向量库与「暴力扫 Python list」的差异：存什么、查什么、何时该换。
4. 对常见向量库（pgvector / Chroma / Qdrant 等）有选型级认知。
5. 知道 ANN 是「用精度换速度」，不能把暴力阈值直接当 ANN 阈值。
6. 能实现 Fake embedder + 内存 Top-K，并完成课后练习。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | Embedding、相似度、向量库角色、内存暴力 Top-K | 能讲清检索链路，能手写最小原型 |
| **建议掌握** | 常见向量库对比、元数据过滤雏形 | 能做初步选型与租户过滤 |
| **了解即可** | ANN 算法（HNSW / IVF 等） | 扫盲：知道近似 ≠ 精确 |

---

## 1. 为什么要学（和 RAG / Agent 有什么关系）

#### 为什么需要 Embedding 与向量检索？

LLM **不会**自动知道你公司的私有文档、最新制度、产品手册。把整库 PDF 塞进 Prompt 会撞上 Context Window、计费与延迟。工程上的默认解法是：

```text
文档 → 切分 → Embedding → 写入索引（向量库或内存）
问题 → Embedding → 近邻检索 → 得到相关 chunks
       →（下一章）拼进 Prompt → LLM 生成
```

这一章只钉死前半段：**如何把文字变成可比较的向量，并按问题找出「近」的片段**。没有它，后面的 RAG 架构、Hit@K 调优都没有地基。

#### 没有这层时，常见死法

| 口头说法 | 实际常指的是 | 错位后果 |
| --- | --- | --- |
| 「模型不懂我们公司」 | 缺私有知识进上下文 | 立刻上微调，忽略检索 |
| 「全文搜关键词就行」 | 词面匹配 | 「重置密码」搜不到「忘记口令」 |
| 「把所有文档拼进 system」 | Context 硬塞 | 超窗、贵、慢、还噪声多 |
| 「分数高就一定对」 | 相对排序当绝对真理 | Top-1 同主题干扰、答非所问 |

#### 本章要练的四种能力

1. **表示直觉**：Embedding 把语义变成可算距离的坐标
2. **度量纪律**：余弦 / 点积 / 欧氏何时等价、何时翻车（归一化）
3. **存储角色**：向量库 = 存向量 + 元数据 + 近邻检索（+ 过滤）
4. **最小可跑**：Fake embedding + list 暴力 Top-K，先通管线再谈规模

可以先记一句：

> Embedding 解决「语义上像不像」；向量检索解决「在一大堆向量里怎么快找到像的」。

#### 工程对照（先建立地图）

| 你熟悉的概念 | 本章对应 |
| --- | --- |
| 搜索引擎倒排索引（词 → 文档） | 向量索引（向量 → chunk；比的是方向/距离） |
| CDN / 缓存里的 key | `chunk_id` / `doc_id` + 元数据过滤 |
| DB 的 `ORDER BY score LIMIT K` | Top-K 近邻（暴力或 ANN） |
| 前端「模糊搜」vs「精确 ID」 | 语义近邻 vs 元数据精确过滤（常要组合） |

---

## 2. 必掌握：Embedding 是什么

这一节会刻意写细——后面相似度、向量库、ANN、整条 RAG 都建立在「文本如何变成向量」之上。

### 2.1 一句话定义与直觉

#### 为什么需要先钉死定义？

同事说「上个 embedding」「换个模型重建索引」「维度对不上」时，主语必须清楚。定义模糊时，你会把「关键词搜索」「微调」「把 PDF 贴进 Prompt」搅在一起。

#### 怎么理解

**Embedding** = 把文本（或图片等）映射到**稠密向量**（如 384 / 768 / 1536 维浮点数组），使得：

```text
语义相近 → 向量在空间中更「近」
语义无关 → 更「远」
```

直觉例子：

```text
"如何重置密码"  ≈  "忘记密码怎么办"     → 向量更近
"如何重置密码"  ≉  "今天股市怎么样"     → 向量更远
```

注意：这里的「近」由**具体模型学到的空间**决定，不是人类词典的同义词表。换模型 = 换坐标系。

心智图：

```text
"忘记密码怎么办"
        │
        ▼
   embed(text)          ← 同一模型 / 同一套 encoder 体系
        │
        ▼
 [0.12, -0.03, 0.88, …]  ← 固定维度 D 的 list[float]
        │
        ▼
 与库中其它向量比相似度 → 排出 Top-K
```

#### 工程要点（先记三条）

1. **同一嵌入空间**：查询向量与文档向量必须可比。多数句向量模型：query / doc 用同一模型即可；少数双塔（query encoder + doc encoder）仍属「一套体系」，不要拿 A 模型的 query 去搜 B 模型的库。
2. **模型升级 ≈ 重建索引**：维度或空间变了，旧向量不能和新向量混排。
3. **有长度限制**：超长文本先切分（Chunking，下一章展开）再嵌入；整本手册塞进一次 `embed` 会截断或失败。

#### 怎么写（概念接口）

先钉一个最小异步接口（与后面 Fake / 真 API 对齐）：

```python
from typing import Protocol


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """一批文本 → 一批等长向量（维度由实现决定）。"""
        ...
```

同步版练习里写成普通函数也完全可以：

```python
def embed(texts: list[str]) -> list[list[float]]:
    ...
```

#### 跑一下（Fake：哈希到固定维）

学习阶段**强烈建议**先用确定性 Fake，验证「建库 → 查询 → Top-K」管线，不依赖 Key 与网络：

```python
import hashlib
import math
import re


def fake_embed(text: str, dim: int = 32) -> list[float]:
    """确定性假嵌入：同一字符串多次结果相同；语义质量很差，只测管线。"""
    vec = [0.0] * dim
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        tokens = ["_empty_"]
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        # 用哈希字节把能量洒到若干维上
        for i in range(0, min(len(h), dim)):
            vec[i] += (h[i] / 255.0) * 2.0 - 1.0
    # L2 归一化，便于后面用点积≈余弦
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def fake_embed_batch(texts: list[str], dim: int = 32) -> list[list[float]]:
    return [fake_embed(t, dim=dim) for t in texts]


# 确定性：同一输入 → 同一输出
a1 = fake_embed("忘记密码怎么办")
a2 = fake_embed("忘记密码怎么办")
assert a1 == a2
print(len(a1), round(sum(x * x for x in a1), 5))  # 32  1.0
```

真 embedding 可来自：云 API（OpenAI / 兼容端点）、开源句向量模型（本地或服务）、自建推理服务。接口形状尽量保持 `embed(texts) -> list[list[float]]`，业务不散落 SDK 细节。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| query 用模型 A、库用模型 B | 分数乱跳，Top-K 无意义 |
| 模型升级后不重建索引 | 新旧向量混在同一表，检索漂移 |
| 超长文本不切分直接 embed | 截断丢后半段，或 API 报错 |
| 把 Fake 当「语义评测」基准 | Fake 几乎无语义；Hit@K 要用真模型才有意义 |
| 维度假设写死却换了模型 | `zip` / 矩阵乘法维度不对；入库前校验 `len(vec) == D` |

#### 对照：关键词检索 vs Embedding 检索

| | 关键词 / 倒排 | Embedding 近邻 |
| --- | --- | --- |
| 匹配依据 | 词面、词法 | 向量空间距离 / 夹角 |
| 「重置密码」vs「忘记口令」 | 常漏 | 较易命中（真模型下） |
| 可解释性 | 高（命中了哪些词） | 较低（分数是相对的） |
| 学习阶段 | 可跳过 | 用 Fake 先通管线 |

---

### 2.2 维度、批次与「一套体系」

#### 为什么还要单独说维度与批次？

工程事故里很大一部分是：维度不一致、一次 embed 太长被截断、query/doc 编码器拆着用错。把这些钉死，排障会快很多。

#### 怎么理解

| 概念 | 直觉 | 工程动作 |
| --- | --- | --- |
| 维度 `D` | 每个向量长度 | 建库时固定；入库校验 |
| 批次 `batch` | 一次 API 多条文本 | 降 RTT；注意供应商上限 |
| 同一空间 | 分值可比 | 同一模型或配套双塔 |
| 归一化 | 模长压到 1 | 点积可当余弦用（见 §3） |

双塔提醒（了解形状即可）：

```text
常见句向量：embed_query(q) 与 embed_doc(d) 是同一个函数
双塔：      encode_query(q) 与 encode_doc(d) 成对训练，仍是「一套」
错误：      encode_query_A(q) 去搜 encode_doc_B 建的库
```

#### 跑一下（校验维度）

```python
def assert_dim(vectors: list[list[float]], dim: int) -> None:
    for i, v in enumerate(vectors):
        if len(v) != dim:
            raise ValueError(f"vector[{i}] dim={len(v)}, expected {dim}")


docs = ["重置密码步骤", "请假制度", "今日午餐菜单"]
vecs = fake_embed_batch(docs, dim=32)
assert_dim(vecs, 32)
print("ok", len(vecs), "x", len(vecs[0]))
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 有的向量 768、有的 1536 进同一 list | 相似度函数直接炸或静默错位 |
| 一次把 1 万条塞进单次 API | 超时 / 边界错误；应分批 |
| 只 embed 文档、查询时用随机向量「占位」 | Top-K 等于抽奖 |

---

## 3. 必掌握：相似度

检索的本质：**给 query 向量，按与库中向量的「像不像」排序，取 Top-K**。像不像由相似度（或距离）定义。

### 3.1 三种常用度量

#### 为什么需要搞清度量？

同一批向量，用余弦还是欧氏、是否归一化，**排序可能变**。向量库的默认度量、索引类型也常绑在某一种上。度量不清时，你会抄到「阈值 0.8」却不知道对方空间是否归一化。

#### 怎么理解

| 度量 | 直觉 | 常见用法 |
| --- | --- | --- |
| **余弦相似度** | 看方向夹角，忽略模长差异 | 文本检索最常用；范围约 `[-1, 1]`，同向接近 `1` |
| **点积** | `sum(a_i * b_i)` | 向量已 L2 归一化时，点积 = 余弦，算得更快 |
| **欧氏距离** | 直线距离，越小越近 | 注意尺度；未归一化时模长会主导 |

关系（重要）：

```text
若 a、b 都已 L2 归一化（||a||=||b||=1）：
  cosine(a, b) = dot(a, b)
  欧氏距离² = ||a-b||² = 2 - 2·dot(a,b)   → 排序与余弦一致（越大越近 ↔ 越小越近要翻转）
```

#### 怎么写

```python
import math


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dim mismatch")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-12)


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def l2_normalize(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))
```

#### 跑一下

```python
u = [1.0, 0.0, 0.0]
v = [1.0, 0.0, 0.0]
w = [0.0, 1.0, 0.0]
x = [2.0, 0.0, 0.0]  # 与 u 同向，模长不同

print("相同", round(cosine(u, v), 5))          # 1.0
print("正交", round(cosine(u, w), 5))          # 0.0
print("同向未归一", round(cosine(u, x), 5))    # 1.0（余弦不看模长）
print("点积未归一", round(dot(u, x), 5))       # 2.0（看模长）
print("点积归一后", round(dot(u, l2_normalize(x)), 5))  # 1.0
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 未归一化却用点积当「语义分」 | 模长长的向量被偏爱，排序偏掉 |
| 把欧氏距离当「越大越好」 | 距离是越小越近；排序要 `reverse=False` |
| 认为「分数 > 0.8 就绝对相关」 | Top-K 是**相对**排序；语料同质时分数整体抬高 |
| 混用「距离」与「相似度」阈值 | 抄别人的 `0.75` 可能完全不适用 |
| `zip` 不等长静默截断（未 `strict`） | 旧 Python 行为；维数错了还算出数 |

#### 对照：选度量时怎么记

| 场景 | 更稳妥的默认 |
| --- | --- |
| 文本句向量、自己写暴力检索 | 余弦；或先 L2 再点积 |
| 向量库文档写 `metric=cosine` / `ip` / `l2` | 与建库、模型输出约定一致 |
| 评测对比两次实验 | **同一度量 + 是否归一化** 必须写进实验记录 |

---

### 3.2 Top-K、阈值与「相对排序」

#### 为什么需要把 Top-K 和阈值分开想？

`search(..., k=3)` 永远返回 3 条——哪怕三条都无关。业务上常要：**先 Top-K，再按阈值丢掉明显垃圾**，或「低于阈值则回答不知道」。

#### 怎么理解

```text
全库打分 → 按相似度降序 → 取前 K 名          ← Top-K（相对）
再丢弃 score < threshold 的结果              ← 阈值（绝对，需标定）
再按 metadata 过滤（租户、类型、时间…）      ← 业务约束
```

注意：

- 阈值依赖模型、是否归一化、语料领域；**不能**从博客抄一个万能数。
- Fake embedding 上标定的阈值，换真模型后作废。
- 同主题干扰：库里全是「密码 / 账号」类文档时，问「股市」也可能得到不低的相对分——要靠语料质量、过滤、下一章的 Rerank。

#### 跑一下（带分数返回）

```python
def top_k_with_scores(
    query: list[float],
    corpus: list[list[float]],
    k: int = 3,
) -> list[tuple[int, float]]:
    scored = [(i, cosine(query, v)) for i, v in enumerate(corpus)]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:k]


q = fake_embed("怎么改密码")
corpus_texts = ["重置登录密码", "年假如何申请", "食堂菜单"]
corpus = fake_embed_batch(corpus_texts)
for idx, score in top_k_with_scores(q, corpus, k=3):
    print(f"{score:.4f}  {corpus_texts[idx]}")
```

Fake 下「语义谁近」不可靠，但你应看到：**管线能稳定打出分数与排序**。换真模型后，同一打印逻辑才有评测意义。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只取 Top-K、从不看分数 | 空知识库或全无关时仍「一本正经引用」 |
| 阈值在 ANN 索引上直接复用暴力标定值 | 近似分与精确分不可互换（见 §6） |
| K 固定很大又全塞进 Prompt | 噪声多、超窗、贵（预算在下一章） |

---

## 4. 必掌握：向量库角色

### 4.1 它到底存什么、查什么

#### 为什么需要「向量库」这个角色？

你可以暂时把所有 `list[float]` 放在 Python 进程的 list 里暴力扫——数据量小、做练习时**完全正确**。一旦文档上万、要持久化、要按租户过滤、要多进程共享，就需要专门组件把三件事绑在一起：

```text
1. 存储：向量 + 元数据（doc_id / source / chunk_id / permissions …）
2. 检索：近似最近邻（ANN）或精确扫描
3. 过滤：先（或同时）按元数据缩小候选，再比向量
```

#### 怎么理解

```text
                  ┌─────────────────────────┐
  embed(chunk) →  │  Vector Store           │
                  │  id | vector | metadata │
  embed(query) →  │  search(q, k, filter)   │ → Top-K chunks
                  └─────────────────────────┘
```

元数据示例（后面章节会反复用）：

| 字段 | 用途 |
| --- | --- |
| `doc_id` / `chunk_id` | 回溯原文、去重、引用 |
| `source` | 展示「出自哪份文档」 |
| `tenant_id` / `permissions` | 多租户隔离，防越权召回 |
| `doc_type` / `created_at` | 业务过滤（只要制度、只要近一年） |

#### 对照：list 暴力 vs 向量库

| | Python list 暴力 | 向量库 |
| --- | --- | --- |
| 数据量小（练习 / 原型） | **可用，推荐先走这条** | 可选 |
| 数据量大 | 太慢、占内存 | 必要（ANN） |
| 持久化 / 多进程 | 自己造 | 现成 |
| 元数据过滤 | 自己写 `if` | 索引侧或查询侧支持 |
| 运维 | 无 | 有学习与部署成本 |

一句话：

> **向量库不是魔法语义引擎**——语义来自 Embedding 模型；向量库负责存得下、查得快、滤得动。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为换了向量库就能「更懂中文」 | 不懂来自模型与切分，不来自品牌 |
| 只存向量不存原文 / source | 召回了 ID 却拼不出给 LLM 的资料 |
| 过滤只在应用层、库里全量扫 | 规模上来后又慢又易漏隔离 |
| 多租户共用索引却不过滤 `tenant_id` | **越权召回**（严重事故） |

---

### 4.2 内存里的最小「库」长什么样

#### 为什么先在内存里造一个？

下一节的暴力 Top-K、练习 B4 / A1，都建立在这个形状上。真向量库的 insert / search / filter，不过是把这里的 list 换成服务调用。

#### 怎么写

```python
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    vector: list[float]
    source: str = ""
    chunk_id: str = ""
    tenant_id: str = "default"
    meta: dict = field(default_factory=dict)


@dataclass
class MemoryStore:
    chunks: list[Chunk] = field(default_factory=list)

    def add(self, chunk: Chunk) -> None:
        if self.chunks and len(chunk.vector) != len(self.chunks[0].vector):
            raise ValueError("dim mismatch on insert")
        self.chunks.append(chunk)

    def search(
        self,
        query_vec: list[float],
        k: int = 3,
        *,
        tenant_id: str | None = None,
        min_score: float | None = None,
    ) -> list[tuple[Chunk, float]]:
        candidates = self.chunks
        if tenant_id is not None:
            candidates = [c for c in candidates if c.tenant_id == tenant_id]
        scored = [(c, cosine(query_vec, c.vector)) for c in candidates]
        scored.sort(key=lambda t: t[1], reverse=True)
        out: list[tuple[Chunk, float]] = []
        for c, s in scored[:k]:
            if min_score is not None and s < min_score:
                continue
            out.append((c, s))
        return out
```

#### 跑一下

```python
store = MemoryStore()
rows = [
    ("重置密码：登录页点击忘记密码", "handbook.md", "t1"),
    ("年假申请找直属经理审批", "hr.md", "t1"),
    ("食堂本周菜单：盖浇饭", "life.md", "t2"),
]
for i, (text, source, tenant) in enumerate(rows):
    store.add(
        Chunk(
            text=text,
            vector=fake_embed(text),
            source=source,
            chunk_id=f"c{i}",
            tenant_id=tenant,
        )
    )

q = fake_embed("忘记密码怎么办")
hits = store.search(q, k=2, tenant_id="t1")
for c, s in hits:
    print(f"{s:.4f}  [{c.source}] {c.text}")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `search` 忘记过滤租户 | t2 的菜单可能进 t1 的问答 |
| insert 不校验维度 | 埋雷到查询时才炸 |
| 只返回 `Chunk` 不带 score | 上层无法做阈值与日志 |

---

## 5. 建议掌握：常见向量库对比（认知）

### 5.1 选型地图

#### 为什么需要一张对比表？

面试与立项常问「为什么选 X」。你不需要会运维所有产品，但要能按**规模 / 过滤 / 是否已有 PG / 运维能力 / 延迟与成本**说清取舍。

#### 怎么理解

| 选项 | 粗印象 | 更适合 |
| --- | --- | --- |
| **pgvector** | PostgreSQL 扩展，SQL + 向量同库 | 已有 PG、要事务与关系数据一体 |
| **Chroma** | 本地 / 原型友好，心智负担低 | 个人项目、课程、快速验证 |
| **Qdrant** | 专用向量库，过滤与 API 体验好 | 中等及以上规模、过滤多 |
| **Milvus** | 专用、偏大规模与生态 | 大数据量、独立检索集群 |
| **Weaviate** | 专用，带模块化生态 | 需要其混合能力 / 生态时 |
| **云托管向量检索** | 托管省运维 | 团队不想养集群、肯付云费 |

选型问题清单（书面题 A2 可直接用）：

```text
1. 大概多少向量？增长曲线？
2. 是否已有 PostgreSQL / 必须新组件？
3. 元数据过滤复杂度？（多租户、权限、时间窗）
4. 延迟目标？（P95）
5. 谁运维？能否接受独立集群？
6. 预算：自建机器 vs 云 API / 托管
```

#### 对照：两种常见起点

| 情境 | 常见选择 | 理由（示例表述） |
| --- | --- | --- |
| 已有 PostgreSQL，业务表都在 PG | **pgvector** | 少引入组件；向量与业务行同事务；运维栈统一 |
| 从零本地原型、课程练习 | **Chroma** 或 **纯 MemoryStore** | 启动快；先验证切分与 embedding，再迁生产库 |

没有唯一正确答案；要能说出**约束 → 选择 → 放弃了什么**。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 按明星项目选、不看数据量 | 小项目上重集群，或大项目用玩具库硬撑 |
| 忽略过滤与多租户 | 上线后才发现「能搜但不能安全搜」 |
| 原型用 A、生产换 B 却不重测 Hit@K | 度量/归一化/ANN 参数一变，效果不可比 |

---

### 5.2 和「内存 list」如何衔接

#### 怎么理解迁移路径

```text
阶段 0：Fake embed + MemoryStore.search（本章）
阶段 1：真 embed + MemoryStore（数据仍小）
阶段 2：真 embed + pgvector / Chroma / Qdrant …
阶段 3：调 ANN 参数 + 元数据过滤 +（下一章）Hybrid / Rerank
```

业务代码尽量依赖窄接口，例如：

```python
class VectorStore(Protocol):
    def add(self, chunk: Chunk) -> None: ...
    def search(
        self,
        query_vec: list[float],
        k: int = 3,
        *,
        tenant_id: str | None = None,
        min_score: float | None = None,
    ) -> list[tuple[Chunk, float]]: ...
```

换存储时只换实现，不改「问答编排」主线。

---

## 6. 了解即可：ANN 预告

### 6.1 近似最近邻在干什么

#### 为什么需要 ANN？

暴力 Top-K 是 **O(N·D)**：每条都算相似度。N 到百万、千万时，一次查询的 CPU / 内存扫库不可接受。ANN（Approximate Nearest Neighbor）用索引结构**少算很多对**，换取数量级加速，并接受：**结果可能不是精确的全局 Top-K**。

#### 怎么理解（扫盲级）

| 名字 | 极简直觉 |
| --- | --- |
| **HNSW** | 多层图上「贪心跳」；召回高、占内存；很常见 |
| **IVF** | 先把空间划成桶，只扫部分桶；要调 nprobe 等 |
| 其它（PQ 等） | 压缩向量省内存 / 加速；再换一点精度 |

你只需要记住工程结论：

```text
ANN ≠ 精确 Top-K
速度 ↑↑    精确召回可能 ↓（可调参折中）
```

#### 和评测的关系（为第三章埋伏笔）

- 报 Hit@K / 召回时，要标明：**暴力精确**还是 **ANN**，以及索引参数。
- 在暴力 list 上标定的相似度阈值，**不能**直接当成 ANN 查询的同一阈值。
- 元数据过滤 + ANN 组合时另有坑（过滤过狠导致候选不足、参数与过滤顺序等）——下一章与实战章会碰到。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为「上了 HNSW 就一定更准」 | ANN 优化的是速度；准要靠模型、切分、参数与评测 |
| 用 ANN 结果调一个很紧的阈值 | 近似分抖动，线上忽灵忽不灵 |
| 算法细节硬背公式却从不测 Hit@K | 选型访谈能背名，系统效果失控 |

#### 对照：暴力 vs ANN

| | 暴力（本章 MemoryStore） | ANN（向量库默认能力） |
| --- | --- | --- |
| 正确性 | 精确 Top-K（在选定度量下） | 近似 |
| 速度 | N 小可用 | N 大必要 |
| 参数 | 几乎没有 | ef / nprobe 等影响召回与延迟 |
| 学习用途 | **先掌握语义与度量** | 选型与调参进阶 |

---

## 7. 最小示例：Fake embedding + 内存暴力 Top-K

把前面拼成一条可复制主线——练习 B1～B4 的目标形状。

### 7.1 完整可跑脚本

#### 为什么需要一整段？

拆开的函数懂了，不等于管线通了。下面这段从「假嵌入 → 入库 → 查询 → 打印」一次跑通。

```python
"""最小向量检索原型：Fake embed + 暴力 Top-K。可直接粘贴运行。"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field


def fake_embed(text: str, dim: int = 32) -> list[float]:
    vec = [0.0] * dim
    tokens = re.findall(r"\w+", text.lower()) or ["_empty_"]
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        for i in range(min(len(h), dim)):
            vec[i] += (h[i] / 255.0) * 2.0 - 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-12)


@dataclass
class Chunk:
    text: str
    vector: list[float]
    source: str = ""
    tenant_id: str = "default"


def search(
    query_vec: list[float],
    chunks: list[Chunk],
    k: int = 3,
) -> list[Chunk]:
    ranked = sorted(
        chunks,
        key=lambda c: cosine(query_vec, c.vector),
        reverse=True,
    )
    return ranked[:k]


def main() -> None:
    texts = [
        ("如何重置登录密码", "账号手册"),
        ("忘记密码时走邮箱验证", "账号手册"),
        ("年假天数与司龄有关", "人事制度"),
        ("报销需附发票原件", "财务制度"),
        ("今日股市行情摘要", "财经日报"),
    ]
    chunks = [
        Chunk(text=t, vector=fake_embed(t), source=s) for t, s in texts
    ]
    query = "忘记密码怎么办"
    hits = search(fake_embed(query), chunks, k=3)
    print("Q:", query)
    for i, c in enumerate(hits, 1):
        score = cosine(fake_embed(query), c.vector)
        print(f"  {i}. {score:.4f}  [{c.source}] {c.text}")


if __name__ == "__main__":
    main()
```

#### 跑一下时你在验证什么

| 检查项 | 期望 |
| --- | --- |
| 同一 `fake_embed(text)` 两次 | 向量完全一致 |
| `cosine` 相同向量 | ≈ `1.0` |
| `search` 返回条数 | `min(k, len(chunks))` |
| 换真 embedder | **只换 `fake_embed`**，`Chunk` / `search` 尽量不动 |

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 每次 `cosine` 时重新 `fake_embed(query)` 却在循环里 embed 文档 | 慢；应建库时算好 `chunk.vector` |
| Fake 下纠结「为什么没把最语义相关的排第一」 | Fake 无语义；管线对了即可 |
| 把完整脚本里的阈值抄到生产 ANN | 度量与近似都变了 |

#### 对照：本章原型 vs 下一章 RAG

```text
本章：query → embed → Top-K chunks（检索地基）
下章：Top-K chunks → 拼 Prompt → LLM → 回答（生成接上）
```

---

## 8. 练习指引

按 [`exercises/10-rag/01-embedding-vector-search.md`](../../exercises/10-rag/01-embedding-vector-search.md) 做：

| 题 | 对应本节 | 提示 |
| --- | --- | --- |
| B1 同一 embedding 模型 | §2 | 空间不一致 → 分数量纲乱 |
| B2 `cosine` | §3.1 | 相同≈1，正交≈0 |
| B3 Fake embedder | §2.1 / §7 | 确定性；固定 `dim` |
| B4 暴力 `search` | §4.2 / §7 | 5 条入库，打印 Top-K 文本 |
| A1 `tenant_id` 过滤 | §4.1～4.2 | 过滤后再排序 |
| A2 向量库选型书面 | §5 | PG 存量 vs 本地原型 |
| C1 归一化 vs 点积 | §3.1 | 构造模长不同的同向向量 |

playground 可自建目录实验；保持「embed → 存 Chunk → cosine Top-K」骨架即可。无 Key 不必上真模型。

---

## 9. 小结与下一站

### 知识地图（收回来）

```text
为什么检索：私有知识进不了模型权重 → 外挂向量近邻
  → Embedding（文本→稠密向量；同一空间；Fake 先通管线）
  → 相似度（余弦 / 点积 / 欧氏；归一化；Top-K 是相对排序）
  → 向量库角色（存向量+元数据、近邻、过滤；小数据 list 也行）
  → 选型（pgvector / Chroma / Qdrant / Milvus / 云托管…）
  → ANN 预告（近似≠精确；阈值与 Hit@K 要标明条件）
  → 最小原型（Fake embed + 内存暴力 Top-K）
```

### 自检

- [ ] 能解释 Embedding，并说明为何 query/文档要同一套嵌入体系
- [ ] 能手写 `cosine`，并说明归一化对点积的影响
- [ ] 知道向量库相对 list 暴力多解决了什么问题
- [ ] 能对「已有 PG」vs「本地原型」做一版选型陈述
- [ ] 知道 ANN 是近似，评测与阈值不能想当然搬
- [ ] 能写 Fake embedder + `Chunk` + 暴力 Top-K 原型

### 下一章

[`02-rag-architecture.md`](./02-rag-architecture.md) —— 把检索接到生成，形成完整 RAG（切分、召回质量、元数据过滤、Hybrid / Rerank）。

## 导航

- 返回模块：[README](./README.md)
- 上一模块：[AI / LLM 基础](../09-ai-llm/README.md)
- 下一章：[RAG 架构](./02-rag-architecture.md)
- 相关练习：[`exercises/10-rag/01-embedding-vector-search.md`](../../exercises/10-rag/01-embedding-vector-search.md)
