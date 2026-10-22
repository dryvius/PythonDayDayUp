# 练习：Embedding 与向量检索

> 对应文档：[`docs/10-rag/01-embedding-vector-search.md`](../../docs/10-rag/01-embedding-vector-search.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）  
> Python：≥ 3.11

## 练习说明

1. 先读完文档「必掌握」再做题：Embedding 直觉、余弦相似度、内存暴力 Top-K、向量库角色。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **实践约定**：全程优先 **Fake embedding + 内存 list 暴力 Top-K**；无 API Key 也能绿。真模型仅作可选升级。
4. 建议代码目录：

```text
playground/10-rag/01-embedding-vector-search/
```

5. 先自己做完，再看文末「提示与参考答案」。计算型函数请 `return`，并用 `assert` 验收；不要只靠 `print` 交差。
6. 注解写法用 `list[float]`、`str | None`（勿强制 `List` / `Optional`）。

---

## 热身题（建议先做）

> 每题几分钟。把「向量长度」「点积」「确定性」摸一遍，再上基础题会顺很多。

### W1. 向量长度与 L2 模长

**给定**：向量 `v = [3.0, 4.0]`。

**要求**：手算或写函数 `l2_norm(v) -> float`，返回欧氏模长。

**验收**：

```python
import math

assert math.isclose(l2_norm([3.0, 4.0]), 5.0)
assert math.isclose(l2_norm([0.0, 0.0]), 0.0)
```

---

### W2. 点积一眼看懂

**给定**：`a = [1.0, 2.0]`，`b = [3.0, 4.0]`。

**要求**：实现 `dot(a, b) -> float`；维度不一致时抛 `ValueError("dim mismatch")`。

**验收**：

```python
assert dot([1.0, 2.0], [3.0, 4.0]) == 11.0
try:
    dot([1.0], [1.0, 2.0])
    raise AssertionError("should raise")
except ValueError as e:
    assert "dim mismatch" in str(e)
```

---

### W3. 确定性：同一字符串两次嵌入相同

**给定**：文档中的 `fake_embed` 思路（哈希洒维 + 可选归一化）。

**要求**：实现 `fake_embed(text: str, dim: int = 32) -> list[float]`，保证同一输入多次调用结果完全一致。

**验收**：

```python
a = fake_embed("忘记密码怎么办")
b = fake_embed("忘记密码怎么办")
c = fake_embed("今天天气不错")
assert a == b
assert len(a) == 32
assert a != c
```

---

### W4. 相同向量余弦 ≈ 1

**给定**：已实现或即将实现的 `cosine`。

**要求**：构造一对完全相同的向量，验证余弦接近 `1.0`。

**验收**：

```python
import math

u = [1.0, 0.0, 0.0]
assert math.isclose(cosine(u, u), 1.0, abs_tol=1e-9)
```

---

## 基础题（必做）

### B1. `fake_embed`：确定性假嵌入（批次版）

实现：

```python
def fake_embed(text: str, dim: int = 32) -> list[float]:
    """单条：确定性假嵌入；语义很弱，只测管线。"""
    ...


def fake_embed_batch(texts: list[str], dim: int = 32) -> list[list[float]]:
    """批次：与真 API 的 embed(texts) 形状对齐。"""
    ...
```

**要求**：

1. 固定 `dim`；返回长度恒为 `dim` 的 `list[float]`。
2. 同一字符串多次结果**完全相同**（确定性）。
3. 建议对结果做 L2 归一化（模长 ≈ 1），便于后面点积≈余弦。
4. 空字符串也要给出合法向量（勿崩）。

**验收**：

```python
import math

v1 = fake_embed("重置密码步骤", dim=32)
v2 = fake_embed("重置密码步骤", dim=32)
assert v1 == v2
assert len(v1) == 32
assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0, abs_tol=1e-6)

batch = fake_embed_batch(["a", "b"], dim=16)
assert len(batch) == 2 and all(len(v) == 16 for v in batch)
```

---

### B2. `cosine`：余弦相似度 + 维度校验

实现：

```python
def cosine(a: list[float], b: list[float]) -> float:
    ...
```

**要求**：

1. 维度不一致 → `ValueError("dim mismatch")`。
2. 用 `1e-12`（或同类）保护分母，避免零向量除零。
3. 相同向量 ≈ `1.0`；正交向量 ≈ `0.0`。

**验收**：

```python
import math

u = [1.0, 0.0, 0.0]
v = [1.0, 0.0, 0.0]
w = [0.0, 1.0, 0.0]
x = [2.0, 0.0, 0.0]  # 同向未归一

assert math.isclose(cosine(u, v), 1.0, abs_tol=1e-9)
assert math.isclose(cosine(u, w), 0.0, abs_tol=1e-9)
assert math.isclose(cosine(u, x), 1.0, abs_tol=1e-9)  # 余弦不看模长

try:
    cosine([1.0], [1.0, 2.0])
    raise AssertionError("should raise")
except ValueError as e:
    assert "dim mismatch" in str(e)
```

---

### B3. `MemoryVectorStore`：`add` / `search` Top-K

实现最小内存向量库（名称可与文档 `MemoryStore` 对齐，本练习统一叫 `MemoryVectorStore`）：

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


class MemoryVectorStore:
    def add(self, chunk: Chunk) -> None:
        ...

    def __len__(self) -> int:
        ...

    def search(
        self,
        query_vec: list[float],
        k: int = 3,
    ) -> list[tuple[Chunk, float]]:
        """暴力余弦 Top-K；返回 [(chunk, score), ...]，分数降序。"""
        ...
```

**要求**：

1. `add` 时若库非空且新向量维度与首条不一致 → `ValueError`（维度校验）。
2. `search`：对全部 chunk 算 `cosine`，按分数降序取 Top-K。
3. `k <= 0` 或库空 → 返回 `[]`。
4. 返回条数 = `min(k, len(store))`（无阈值时）。
5. 插入至少 5 条假文档，查询「忘记密码怎么办」，打印或断言 Top-K 文本。

**验收**：

```python
store = MemoryVectorStore()
rows = [
    ("如何重置登录密码", "账号手册"),
    ("忘记密码时走邮箱验证", "账号手册"),
    ("年假天数与司龄有关", "人事制度"),
    ("报销需附发票原件", "财务制度"),
    ("今日股市行情摘要", "财经日报"),
]
for i, (text, source) in enumerate(rows):
    store.add(
        Chunk(
            text=text,
            vector=fake_embed(text),
            source=source,
            chunk_id=f"c{i}",
        )
    )

assert len(store) == 5
hits = store.search(fake_embed("忘记密码怎么办"), k=3)
assert len(hits) == 3
assert all(isinstance(s, float) for _, s in hits)
# 分数降序
scores = [s for _, s in hits]
assert scores == sorted(scores, reverse=True)

# 维度校验
try:
    store.add(Chunk(text="bad", vector=[0.0, 1.0], source="x"))
    raise AssertionError("should raise")
except ValueError:
    pass
```

建议在 playground 跑通：`playground/10-rag/01-embedding-vector-search/test_store.py`。

---

### B4. 维度校验工具：`assert_dim`

实现：

```python
def assert_dim(vectors: list[list[float]], dim: int) -> None:
    """任一向量长度 != dim 时抛 ValueError，信息中带索引。"""
    ...
```

**要求**：与 `fake_embed_batch` 联用；入库前先校验批次维度。

**验收**：

```python
docs = ["重置密码步骤", "请假制度", "今日午餐菜单"]
vecs = fake_embed_batch(docs, dim=32)
assert_dim(vecs, 32)  # 不抛

try:
    assert_dim([[0.0, 1.0], [0.0, 1.0, 2.0]], 2)
    raise AssertionError("should raise")
except ValueError as e:
    assert "1" in str(e)  # 指出第 1 条（0-based 或 1-based 均可，文档写清）
```

---

## 进阶题（建议）

### A1. 元数据 filter：按 `tenant_id` 过滤后再排序

扩展 `MemoryVectorStore.search`：

```python
def search(
    self,
    query_vec: list[float],
    k: int = 3,
    *,
    tenant_id: str | None = None,
    min_score: float | None = None,
) -> list[tuple[Chunk, float]]:
    ...
```

**要求**：

1. `tenant_id is not None` 时，只在该租户的 chunk 中检索（**先过滤再排序**）。
2. 可选 `min_score`：分数低于阈值的不要返回。
3. 多租户数据混库时，租户 A 的问答不得召回租户 B 的内容。

**验收**：

```python
store = MemoryVectorStore()
data = [
    ("重置密码：登录页点击忘记密码", "handbook.md", "t1"),
    ("年假申请找直属经理审批", "hr.md", "t1"),
    ("食堂本周菜单：盖浇饭", "life.md", "t2"),
]
for i, (text, source, tenant) in enumerate(data):
    store.add(
        Chunk(
            text=text,
            vector=fake_embed(text),
            source=source,
            chunk_id=f"c{i}",
            tenant_id=tenant,
        )
    )

hits = store.search(fake_embed("忘记密码怎么办"), k=5, tenant_id="t1")
assert hits  # 至少有命中
assert all(c.tenant_id == "t1" for c, _ in hits)
assert all(c.source != "life.md" for c, _ in hits)
```

---

### A2. 向量库选型对照表（书面）

**给定**两种情境：

| 情境 | 约束摘要 |
| --- | --- |
| S1 | 已有 PostgreSQL，业务表都在 PG，向量量级中小，要事务一致 |
| S2 | 从零本地原型 / 课程练习，先验证切分与 embedding，运维能力弱 |

**要求**：为每种情境选一个方案（从 pgvector / Chroma / Qdrant / Milvus / 纯 MemoryVectorStore / 云托管 中选），写一张对照表，至少含列：

- 情境
- 选择
- 理由（约束 → 选择）
- 放弃了什么（trade-off）

**验收**：能口头讲清「不是唯一正确答案，但约束→选择→放弃」三条链完整；不要只写品牌名。

参考文档 §5 选型地图。可把表格写在：

```text
playground/10-rag/01-embedding-vector-search/选型对照.md
```

---

## 挑战题（可选）

### C1. `Protocol Embedder`：可切换 Fake / 真（真可选）

定义窄接口，业务只依赖 Protocol：

```python
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """一批文本 → 一批等长向量。"""
        ...
```

实现至少：

1. `FakeEmbedder(dim: int = 32)`：内部调用你的 `fake_embed`。
2. （可选）`HashingEmbedder` 或真模型适配器——接口相同即可；无 Key 可只写骨架 + `NotImplementedError` / 跳过。

再写一个**不依赖具体类名**的建库函数：

```python
def build_store(texts: list[tuple[str, str]], embedder: Embedder) -> MemoryVectorStore:
    """texts: [(text, source), ...]；用 embedder.embed 批量嵌入后 add。"""
    ...
```

**要求**：

1. 换 Fake →（可选）真 embedding 时，`build_store` / `search` **签名不动**。
2. Fake 路径必须有完整 `assert`。
3. 若实现真模型：注意脱敏、费用；CI 默认仍走 Fake。

**验收（Fake 路径必过）**：

```python
class FakeEmbedder:
    def __init__(self, dim: int = 32) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return fake_embed_batch(texts, dim=self.dim)


emb = FakeEmbedder(dim=32)
store = build_store(
    [
        ("如何重置登录密码", "账号手册"),
        ("年假天数与司龄有关", "人事制度"),
    ],
    emb,
)
assert len(store) == 2
hits = store.search(emb.embed(["忘记密码"])[0], k=1)
assert len(hits) == 1
```

---

## 验收标准

- [ ] 热身 W1～W4 建议完成（帮助建立直觉）
- [ ] **必做** B1～B4：`fake_embed` / `cosine` / `MemoryVectorStore` / `assert_dim`，均有 `assert`
- [ ] （建议）A1 租户过滤；A2 选型对照表
- [ ] （可选）C1 Protocol Embedder，Fake 路径绿；真模型可选
- [ ] 无 Key、无网络时 Fake + 内存暴力 Top-K 可完整演示检索链路

---

## 提示与参考答案

> 先自己做。卡住超过 15 分钟再看对应题的「思路」，最后才对完整代码。

### W1 参考答案

```python
import math


def l2_norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


assert math.isclose(l2_norm([3.0, 4.0]), 5.0)
assert math.isclose(l2_norm([0.0, 0.0]), 0.0)
```

### W2 参考答案

```python
def dot(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dim mismatch")
    return sum(x * y for x, y in zip(a, b, strict=True))


assert dot([1.0, 2.0], [3.0, 4.0]) == 11.0
```

### W3 / B1 思路 + 参考答案

**思路**

1. 用稳定哈希（如 `sha256`）把 token 洒到固定维，保证确定性。
2. 归一化后模长 ≈ 1，后续可用点积近似余弦。
3. `fake_embed_batch` 只是对列表 map，形状对齐真 API。

**参考答案**

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
        for i in range(0, min(len(h), dim)):
            vec[i] += (h[i] / 255.0) * 2.0 - 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def fake_embed_batch(texts: list[str], dim: int = 32) -> list[list[float]]:
    return [fake_embed(t, dim=dim) for t in texts]


# ---- 验收 ----
v1 = fake_embed("重置密码步骤", dim=32)
v2 = fake_embed("重置密码步骤", dim=32)
assert v1 == v2
assert len(v1) == 32
assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0, abs_tol=1e-6)
batch = fake_embed_batch(["a", "b"], dim=16)
assert len(batch) == 2 and all(len(v) == 16 for v in batch)
assert fake_embed("")  # 空串也合法
```

### W4 / B2 思路 + 参考答案

**思路**

1. 先校验维度，再算点积与模长。
2. 分母加 `1e-12` 防零向量。
3. 余弦看方向：同向未归一化向量余弦仍为 1。

**参考答案**

```python
import math


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dim mismatch")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-12)


u = [1.0, 0.0, 0.0]
v = [1.0, 0.0, 0.0]
w = [0.0, 1.0, 0.0]
x = [2.0, 0.0, 0.0]

assert math.isclose(cosine(u, v), 1.0, abs_tol=1e-9)
assert math.isclose(cosine(u, w), 0.0, abs_tol=1e-9)
assert math.isclose(cosine(u, x), 1.0, abs_tol=1e-9)

try:
    cosine([1.0], [1.0, 2.0])
    raise AssertionError("should raise")
except ValueError as e:
    assert "dim mismatch" in str(e)
```

### B3 思路 + 参考答案

**思路**

1. 向量库最小职责：存 `Chunk`（原文 + 向量 + 元数据）+ 近邻检索。
2. `add` 时校验维度，把雷排在入库阶段。
3. `search` = 全量打分 → 排序 → 切片；小数据暴力即可，行为可解释。

**参考答案**

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


class MemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []

    def add(self, chunk: Chunk) -> None:
        if self._chunks and len(chunk.vector) != len(self._chunks[0].vector):
            raise ValueError(
                f"dim mismatch on insert: got {len(chunk.vector)}, "
                f"expected {len(self._chunks[0].vector)}"
            )
        self._chunks.append(chunk)

    def __len__(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query_vec: list[float],
        k: int = 3,
    ) -> list[tuple[Chunk, float]]:
        if k <= 0 or not self._chunks:
            return []
        scored = [(c, cosine(query_vec, c.vector)) for c in self._chunks]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:k]


# ---- 验收 ----
store = MemoryVectorStore()
rows = [
    ("如何重置登录密码", "账号手册"),
    ("忘记密码时走邮箱验证", "账号手册"),
    ("年假天数与司龄有关", "人事制度"),
    ("报销需附发票原件", "财务制度"),
    ("今日股市行情摘要", "财经日报"),
]
for i, (text, source) in enumerate(rows):
    store.add(
        Chunk(
            text=text,
            vector=fake_embed(text),
            source=source,
            chunk_id=f"c{i}",
        )
    )

assert len(store) == 5
hits = store.search(fake_embed("忘记密码怎么办"), k=3)
assert len(hits) == 3
scores = [s for _, s in hits]
assert scores == sorted(scores, reverse=True)

try:
    store.add(Chunk(text="bad", vector=[0.0, 1.0], source="x"))
    raise AssertionError("should raise")
except ValueError:
    pass

# 可选：打印 Top-K
for i, (c, s) in enumerate(hits, 1):
    print(f"{i}. {s:.4f} [{c.source}] {c.text}")
```

### B4 思路 + 参考答案

**思路**

入库前统一校验批次维度，错误信息带索引，排障更快。

**参考答案**

```python
def assert_dim(vectors: list[list[float]], dim: int) -> None:
    for i, v in enumerate(vectors):
        if len(v) != dim:
            raise ValueError(f"vector[{i}] dim={len(v)}, expected {dim}")


docs = ["重置密码步骤", "请假制度", "今日午餐菜单"]
vecs = fake_embed_batch(docs, dim=32)
assert_dim(vecs, 32)

try:
    assert_dim([[0.0, 1.0], [0.0, 1.0, 2.0]], 2)
    raise AssertionError("should raise")
except ValueError as e:
    assert "vector[1]" in str(e)
```

### A1 思路 + 参考答案

**思路**

1. 多租户安全：**检索侧强制过滤**，不要指望 Prompt「别提及其他客户」。
2. 顺序：filter → score → sort →（可选阈值）→ top-k。
3. 返回带 score，便于日志与阈值。

**参考答案**

```python
class MemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []

    def add(self, chunk: Chunk) -> None:
        if self._chunks and len(chunk.vector) != len(self._chunks[0].vector):
            raise ValueError("dim mismatch on insert")
        self._chunks.append(chunk)

    def __len__(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query_vec: list[float],
        k: int = 3,
        *,
        tenant_id: str | None = None,
        min_score: float | None = None,
    ) -> list[tuple[Chunk, float]]:
        if k <= 0 or not self._chunks:
            return []
        candidates = self._chunks
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


store = MemoryVectorStore()
data = [
    ("重置密码：登录页点击忘记密码", "handbook.md", "t1"),
    ("年假申请找直属经理审批", "hr.md", "t1"),
    ("食堂本周菜单：盖浇饭", "life.md", "t2"),
]
for i, (text, source, tenant) in enumerate(data):
    store.add(
        Chunk(
            text=text,
            vector=fake_embed(text),
            source=source,
            chunk_id=f"c{i}",
            tenant_id=tenant,
        )
    )

hits = store.search(fake_embed("忘记密码怎么办"), k=5, tenant_id="t1")
assert hits
assert all(c.tenant_id == "t1" for c, _ in hits)
assert all(c.source != "life.md" for c, _ in hits)
```

### A2 参考答案（示例表述，非唯一）

| 情境 | 选择 | 理由 | 放弃了什么 |
| --- | --- | --- | --- |
| S1 已有 PG | **pgvector** | 少引入组件；向量与业务行可同事务；运维栈统一 | 专用向量库在极大规模/复杂过滤上的极致能力 |
| S2 本地原型 | **Chroma** 或 **MemoryVectorStore** | 启动快；先验证切分与 embedding；心智负担低 | 生产级持久化、副本、复杂 ACL（原型阶段本就不该先上） |

口头检查：能说出「约束 → 选择 → 放弃」即可。规模上来后再迁 Qdrant/Milvus/云托管，并用同一题集重测 Hit@K。

### C1 思路 + 参考答案

**思路**

1. 业务依赖 `Embedder` Protocol，不依赖 `FakeEmbedder` 类名。
2. 换真模型只换实现；`MemoryVectorStore` / `search` 不动。
3. CI 默认 Fake；真模型可选、脱敏、可跳过。

**参考答案**

```python
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class FakeEmbedder:
    def __init__(self, dim: int = 32) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return fake_embed_batch(texts, dim=self.dim)


# 可选骨架：有 Key 再实现；无 Key 保持 NotImplemented 或整题跳过
class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("optional: wire real API when you have a key")


def build_store(
    texts: list[tuple[str, str]],
    embedder: Embedder,
) -> MemoryVectorStore:
    store = MemoryVectorStore()
    contents = [t for t, _ in texts]
    vectors = embedder.embed(contents)
    assert_dim(vectors, len(vectors[0]))
    for i, ((text, source), vec) in enumerate(zip(texts, vectors, strict=True)):
        store.add(
            Chunk(text=text, vector=vec, source=source, chunk_id=f"c{i}")
        )
    return store


emb = FakeEmbedder(dim=32)
store = build_store(
    [
        ("如何重置登录密码", "账号手册"),
        ("年假天数与司龄有关", "人事制度"),
    ],
    emb,
)
assert len(store) == 2
hits = store.search(emb.embed(["忘记密码"])[0], k=1)
assert len(hits) == 1
print("top1:", hits[0][0].text, "score=", round(hits[0][1], 4))
```

---

### 一页速查

```text
文本 → fake_embed → Chunk.vector
问题 → fake_embed → query_vec
     → MemoryVectorStore.search（余弦暴力 Top-K，可选 tenant 过滤）
     → [(chunk, score), ...]

同一 embedding 空间；入库校验维度；小数据 list 足够。
下一章：把 Top-K 拼进 Prompt → LLM（FakeLLM 返回 assistant dict）。
```
