# 练习：RAG 实战与调优

> 对应文档：[`docs/10-rag/03-rag-practice.md`](../../docs/10-rag/03-rag-practice.md)  
> 状态：`已完成出题`  
> 建议用时：90～140 分钟（含热身）  
> Python：≥ 3.11

## 练习说明

1. 先读完文档「必掌握」：最小知识库、Hit@K、失败模式、chunk 实验纪律。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **实践约定**：全程 Fake embedding + 内存暴力 Top-K + FakeLLM（`complete -> dict`）。检索账与生成账**分开记账**。
4. 建议代码目录：

```text
playground/10-rag/03-rag-practice/
  ├── mini_rag.py          # 可复用上一章 MiniRAG
  ├── cases.jsonl          # 小题集
  ├── experiment.md        # chunk_size 对照
  ├── failure-notes.md     # 排障笔记
  └── eval_report.md       # 端到端评测报告（挑战题）
```

5. Fake embedding 语义弱：题集优先选「问句与文档字面接近」的 case，否则 Hit@K 接近随机，无法指导切分。
6. 先自己做完，再看文末「提示与参考答案」。

---

## 热身题（建议先做）

### W1. Hit@K 直觉

**给定**：检索结果 sources `["a.md", "b.md", "c.md"]`，期望 `{"b.md"}`，`k=2`。

**要求**：口头或纸上判断：Top-2 是否命中？Top-1 是否命中？

**验收**：Hit@2 = True（`b.md` 在第 2 位）；Hit@1 = False。

---

### W2. jsonl 一行长什么样

**给定**：评测题一条。

**要求**：写出一行合法 JSON（一行一个对象），字段至少含 `id` / `question` / `expected_sources`。

**验收**：能被 `json.loads` 解析；`expected_sources` 为数组。

---

### W3. 单变量实验纪律

**给定**：要调 `chunk_size`。

**要求**：用一句话写下「哪些量必须固定」。

**验收**：至少提到固定题集、固定 embedder、固定 K（或同时报告多个 K 但归因时只改一个旋钮）。

---

## 基础题（必做）

### B1. `hit_at_k` / `mrr`：检索侧指标

实现：

```python
def hit_at_k(
    retrieved_sources: list[str],
    expected: set[str],
    k: int,
) -> bool:
    """Top-K 是否命中任一期望 source。期望为空时返回 False（拒答题勿走此函数）。"""
    ...


def mrr(retrieved_sources: list[str], expected: set[str]) -> float:
    """Mean Reciprocal Rank：首个命中位次的倒数；未命中为 0.0。"""
    ...
```

**要求**：

1. 只看 `retrieved_sources[:k]`。
2. `expected` 为空 → `hit_at_k` 返回 `False`（拒答题留给生成侧）。
3. 自造 3 组用例写 `assert`。

**验收**：

```python
assert hit_at_k(["a.md", "b.md", "c.md"], {"b.md"}, k=2) is True
assert hit_at_k(["a.md", "b.md", "c.md"], {"b.md"}, k=1) is False
assert hit_at_k(["a.md"], {"z.md"}, k=3) is False
assert hit_at_k([], {"a.md"}, k=3) is False
assert hit_at_k(["a.md"], set(), k=3) is False

assert mrr(["a.md", "b.md"], {"b.md"}) == 0.5
assert mrr(["b.md", "a.md"], {"b.md"}) == 1.0
assert mrr(["a.md", "c.md"], {"b.md"}) == 0.0
```

---

### B2. 小题集 `cases.jsonl`（≥5，含拒答）

**要求**：在 playground 准备题集文件，至少 5 条，其中至少 1 条拒答：

```json
{"id": "q1", "question": "怎么重置密码？", "expected_sources": ["faq.md"], "expect_refuse": false}
{"id": "q2", "question": "客服电话多少？", "expected_sources": ["faq.md"], "expect_refuse": false}
{"id": "q3", "question": "试用期多久？", "expected_sources": ["hr.md"], "expect_refuse": false}
{"id": "q4", "question": "年假怎么算？", "expected_sources": ["hr.md"], "expect_refuse": false}
{"id": "q5", "question": "今天月球几点关门？", "expected_sources": [], "expect_refuse": true}
```

另准备两篇短文供 ingest（字面接近问句）：

```text
faq.md  — 重置密码步骤、客服电话
hr.md   — 试用期、年假规则
```

实现加载函数：

```python
def load_cases(path: str) -> list[dict]:
    """逐行 json.loads；跳过空行。"""
    ...
```

**验收**：

```python
cases = load_cases("cases.jsonl")  # 相对你的 playground 路径
assert len(cases) >= 5
assert any(c.get("expect_refuse") for c in cases)
assert all("question" in c for c in cases)
for c in cases:
    if not c.get("expect_refuse"):
        assert c.get("expected_sources")
```

路径建议：`playground/10-rag/03-rag-practice/cases.jsonl`。

---

### B3. 跑 Hit@K：对接 `retrieve`

实现：

```python
def evaluate_retrieval(
    cases: list[dict],
    retrieve_fn,
    *,
    k: int = 3,
) -> dict:
    """
    retrieve_fn(question, k) -> list[dict]，元素含 "source"。
    返回 {
      "k": k,
      "n": 参与检索评测的题数（排除 expect_refuse）,
      "hit_rate": float,
      "mrr": float,
      "per_case": [{"id", "hit", "mrr", "sources"}, ...],
    }
    """
    ...
```

**要求**：

1. `expect_refuse=True` 的题**不计入** Hit@K 平均（可单独记录）。
2. 固定 K；打印 `hit_rate` / `mrr`。
3. 使用上一章 `MiniRAG`（或等价实现）ingest 两篇短文后再评测。

**验收**：

```python
# rag 已 ingest faq.md / hr.md；cases 已 load
def retrieve_fn(question: str, k: int = 3) -> list[dict]:
    return rag.retrieve(question, k=k)

report = evaluate_retrieval(cases, retrieve_fn, k=3)
assert report["n"] >= 4
assert 0.0 <= report["hit_rate"] <= 1.0
assert 0.0 <= report["mrr"] <= 1.0
assert len(report["per_case"]) == report["n"]
print(report["hit_rate"], report["mrr"])
```

说明：Fake 下 Hit@K 绝对值勿过度解读；流程与报表对即可。

---

### B4. 调 `chunk_size` 对比（单变量）

**要求**：

1. 固定题集、固定 FakeEmbedder、固定 `k=3`、固定 `overlap` 比例或固定 overlap 值。
2. 至少对比两组 `chunk_size`（例如 40 vs 80，或 64 vs 128）。
3. 每组重新 ingest → `evaluate_retrieval`。
4. 把结果写入 `experiment.md`（表格：条件 / Hit@K / MRR / 备注）。

实现辅助函数（可选但推荐）：

```python
def run_chunk_size_experiment(
    texts: dict[str, str],
    cases: list[dict],
    sizes: list[int],
    *,
    overlap: int = 8,
    k: int = 3,
) -> list[dict]:
    """
    返回 [{"chunk_size", "hit_rate", "mrr", "n"}, ...]
    """
    ...
```

**验收**：

```python
texts = {
    "faq.md": "重置密码：进入设置 → 安全 → 重置密码。客服电话 400-800-1234。",
    "hr.md": "试用期为 3 个月。年假天数与司龄有关，满一年起算。",
}
rows = run_chunk_size_experiment(texts, cases, sizes=[40, 80], overlap=8, k=3)
assert len(rows) == 2
assert {r["chunk_size"] for r in rows} == {40, 80}
# experiment.md 存在且含 Hit 字样（人工检查）
```

---

## 进阶题（建议）

### A1. 失败排障笔记模板

**要求**：在 `failure-notes.md` 按模板记录至少 **2** 个故意制造的失败，每个含：

```markdown
## Case: <短标题>

- 症状：
- 复现步骤：
- 检查顺序（勾选）：
  - [ ] `len(index)` / ingest 返回值（是否空索引）
  - [ ] query/doc 是否同一 embedder
  - [ ] 维度是否一致
  - [ ] 过滤是否过严（tenant / min_score）
  - [ ] Top-K 是否过大导致噪声
  - [ ] 是否缺少拒答纪律
- 根因归类：空索引 / 模型不一致 / 切分 / 过滤 / Prompt / 其他
- 修复：
- 修复后验证：（Hit@K 或 ask 断言）
```

故意失败示例（任选 2）：

1. ingest 时吞掉异常 → 空索引  
2. 查询用另一套随机向量  
3. `min_score` 过高 → 全拒答  
4. 提示允许瞎编（对比有拒答纪律的版本）

**验收**：文件存在；至少 2 个 Case；每个有「症状 / 根因 / 修复」。

---

### A2. 简单 rerank 假实现

在检索后、进 Prompt 前插入精排（教学占位）：

```python
def fake_rerank(
    query: str,
    candidates: list[dict],
    *,
    top_n: int = 5,
) -> list[dict]:
    """
    假精排：按「查询词与 text 的重叠 token 数」降序，取 top_n。
    不调用外部模型；确定性。
    candidates 元素至少含 "text"；可含 "source" / "score"。
    """
    ...
```

**要求**：

1. 第一阶段可多取（如 k=8），rerank 后再取 `top_n=3` 进 Prompt。
2. 用构造数据断言：更相关（词重叠多）的排前面。
3. 书面 3 行：延迟 / 成本 / 为何「先多召回再精排」。

**验收**：

```python
query = "reset email password"
candidates = [
    {"chunk_id": "1", "text": "reset wifi password on router", "source": "net.md"},
    {"chunk_id": "2", "text": "reset email password in security settings", "source": "mail.md"},
    {"chunk_id": "3", "text": "change mailbox password via SSO", "source": "sso.md"},
]
out = fake_rerank(query, candidates, top_n=2)
assert out[0]["chunk_id"] == "2"
assert len(out) == 2
```

---

## 挑战题（可选）

### C1. 端到端评测报告：accuracy + 失败 case

在 FakeLLM 路径上做**生成侧**最小评测，并与检索侧分账：

```python
def evaluate_e2e(
    rag: MiniRAG,
    cases: list[dict],
    *,
    k: int = 3,
) -> dict:
    """
    返回 {
      "retrieval": { hit_rate, mrr, n },
      "generation": {
        "n": int,
        "accuracy": float,   # 见下方判定规则
        "fail_cases": [{"id", "question", "reason", "answer", "citations"}, ...]
      },
    }
    """
    ...
```

**生成侧判定规则（Fake 可测、须写进报告）**：

| 题型 | 判对条件 |
| --- | --- |
| `expect_refuse=True` | `refused is True` 且答案含「不知道」 |
| 普通题 | `refused is False`；且 `citations` 的 source 与 `expected_sources` 有交集；答案非空 |

（不要用真模型主观分充当 CI；有 Key 时可另附「人工抽检」小节。）

**要求**：

1. 产出 `eval_report.md`，含：题集规模、Hit@K、生成 accuracy、失败 case 列表（id + reason）。
2. `fail_cases` 至少能在「空库」或「故意坏 prompt」场景被测到非空（可另跑一条破坏性用例写入报告「已知失败演练」）。
3. FakeLLM 仍返回 dict。

**验收**：

```python
rag = MiniRAG(chunk_size=48, overlap=8, top_k=3)
for source, text in texts.items():
    rag.ingest(source, text, doc_id=source.replace(".md", ""))

e2e = evaluate_e2e(rag, cases, k=3)
assert "retrieval" in e2e and "generation" in e2e
assert 0.0 <= e2e["generation"]["accuracy"] <= 1.0
assert isinstance(e2e["generation"]["fail_cases"], list)

# 空库应拒答正确 → accuracy 贡献来自 refuse case
empty = MiniRAG()
e2e_empty = evaluate_e2e(empty, cases, k=3)
# 拒答题应判对；普通题应进 fail_cases
refuse_ids = {c["id"] for c in cases if c.get("expect_refuse")}
failed_ids = {f["id"] for f in e2e_empty["generation"]["fail_cases"]}
assert refuse_ids.isdisjoint(failed_ids) or e2e_empty["generation"]["accuracy"] >= 0.0

print("hit_rate", e2e["retrieval"]["hit_rate"])
print("gen_acc", e2e["generation"]["accuracy"])
print("fails", e2e["generation"]["fail_cases"])
```

把同一份数字写进 `eval_report.md`。

---

## 验收标准

- [ ] 热身 W1～W3 建议完成
- [ ] **必做** B1～B4：`hit_at_k`、`cases.jsonl`、评测跑通、chunk_size 对照表
- [ ] （建议）A1 排障笔记 ≥2 case；A2 `fake_rerank` 带 assert
- [ ] （可选）C1 端到端报告：accuracy + 失败 case；检索账与生成账分离
- [ ] Fake 路径离线可绿；`FakeLLM.complete` 返回 dict 而非 str

### 模块 10 通关自检

- [ ] 理解 embedding / 相似度 / 内存向量库
- [ ] 能实现 ingest → retrieve → prompt → ask
- [ ] 有题集与 Hit@K，会做单变量 chunk 实验
- [ ] 会按失败模式排障（先查空索引）

完成后进入模块 11《Agent 核心开发》。

---

## 提示与参考答案

> 先自己做。评测题优先保证「流程可复现」，再谈分数高低。

### W1 参考答案

```text
sources = [a, b, c]
expected = {b}
Hit@2: True（b 在第 2 位）
Hit@1: False（第 1 位是 a）
```

### W2 参考答案

```python
import json

line = (
    '{"id":"q1","question":"怎么重置密码？",'
    '"expected_sources":["faq.md"],"expect_refuse":false}'
)
obj = json.loads(line)
assert obj["expected_sources"] == ["faq.md"]
```

### W3 参考答案

```text
固定：题集、embedder（含 dim）、K、overlap（或明确只改 size）、评测脚本。
只改 chunk_size 一个旋钮，否则无法归因。
```

### B1 思路 + 参考答案

**思路**

1. Hit@K：截断到 K，看是否与期望集合有交。
2. MRR：找第一个命中的 1-based 位次，取倒数。
3. 拒答题期望为空：不要塞进 Hit@K 平均。

**参考答案**

```python
def hit_at_k(
    retrieved_sources: list[str],
    expected: set[str],
    k: int,
) -> bool:
    if not expected or k <= 0:
        return False
    return any(s in expected for s in retrieved_sources[:k])


def mrr(retrieved_sources: list[str], expected: set[str]) -> float:
    if not expected:
        return 0.0
    for i, s in enumerate(retrieved_sources, start=1):
        if s in expected:
            return 1.0 / i
    return 0.0


assert hit_at_k(["a.md", "b.md", "c.md"], {"b.md"}, k=2) is True
assert hit_at_k(["a.md", "b.md", "c.md"], {"b.md"}, k=1) is False
assert hit_at_k(["a.md"], {"z.md"}, k=3) is False
assert hit_at_k([], {"a.md"}, k=3) is False
assert hit_at_k(["a.md"], set(), k=3) is False

assert mrr(["a.md", "b.md"], {"b.md"}) == 0.5
assert mrr(["b.md", "a.md"], {"b.md"}) == 1.0
assert mrr(["a.md", "c.md"], {"b.md"}) == 0.0
```

### B2 思路 + 参考答案

**思路**

1. jsonl = 一行一个 JSON，便于追加题。
2. 拒答题用 `expect_refuse` + 空 `expected_sources`。
3. Fake 下问句尽量含文档关键词。

**参考答案**

`cases.jsonl` 示例：

```json
{"id": "q1", "question": "怎么重置密码？", "expected_sources": ["faq.md"], "expect_refuse": false}
{"id": "q2", "question": "客服电话多少？", "expected_sources": ["faq.md"], "expect_refuse": false}
{"id": "q3", "question": "试用期多久？", "expected_sources": ["hr.md"], "expect_refuse": false}
{"id": "q4", "question": "年假怎么算？", "expected_sources": ["hr.md"], "expect_refuse": false}
{"id": "q5", "question": "今天月球几点关门？", "expected_sources": [], "expect_refuse": true}
```

```python
import json
from pathlib import Path


def load_cases(path: str) -> list[dict]:
    rows: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


# 验收时把 path 换成你的实际路径
# cases = load_cases("playground/10-rag/03-rag-practice/cases.jsonl")
```

### B3 思路 + 参考答案

**思路**

1. 只评测非拒答题的检索。
2. `per_case` 留下 sources，方便看「偏题还是空」。
3. `retrieve` 与 `ask` 分离，避免评测被迫走生成。

**参考答案**

```python
def evaluate_retrieval(
    cases: list[dict],
    retrieve_fn,
    *,
    k: int = 3,
) -> dict:
    per_case: list[dict] = []
    hits = 0
    rr_sum = 0.0
    for case in cases:
        if case.get("expect_refuse"):
            continue
        expected = set(case.get("expected_sources") or [])
        chunks = retrieve_fn(case["question"], k)
        sources = [c["source"] for c in chunks]
        hit = hit_at_k(sources, expected, k)
        rr = mrr(sources, expected)
        hits += int(hit)
        rr_sum += rr
        per_case.append(
            {
                "id": case.get("id"),
                "hit": hit,
                "mrr": rr,
                "sources": sources,
            }
        )
    n = len(per_case)
    return {
        "k": k,
        "n": n,
        "hit_rate": (hits / n) if n else 0.0,
        "mrr": (rr_sum / n) if n else 0.0,
        "per_case": per_case,
    }


# 对接 MiniRAG（复用上一章实现）
# rag = MiniRAG(...)
# rag.ingest(...)
# report = evaluate_retrieval(cases, lambda q, k=3: rag.retrieve(q, k=k), k=3)
```

### B4 思路 + 参考答案

**思路**

1. 每个 size 新建 `MiniRAG`，避免旧 chunk 残留。
2. 只改 `chunk_size`；overlap / k / 题集固定。
3. 报表重过程与纪律；Fake 下绝对值供练习。

**参考答案**

```python
def run_chunk_size_experiment(
    texts: dict[str, str],
    cases: list[dict],
    sizes: list[int],
    *,
    overlap: int = 8,
    k: int = 3,
) -> list[dict]:
    rows: list[dict] = []
    for size in sizes:
        rag = MiniRAG(chunk_size=size, overlap=overlap, top_k=k)
        for source, text in texts.items():
            rag.ingest(source, text, doc_id=source.replace(".md", ""))
        report = evaluate_retrieval(
            cases,
            lambda q, k=k, rag=rag: rag.retrieve(q, k=k),
            k=k,
        )
        rows.append(
            {
                "chunk_size": size,
                "hit_rate": report["hit_rate"],
                "mrr": report["mrr"],
                "n": report["n"],
            }
        )
    return rows


texts = {
    "faq.md": "重置密码：进入设置 → 安全 → 重置密码。客服电话 400-800-1234。",
    "hr.md": "试用期为 3 个月。年假天数与司龄有关，满一年起算。",
}
# cases = load_cases(...)
# rows = run_chunk_size_experiment(texts, cases, sizes=[40, 80], overlap=8, k=3)
```

`experiment.md` 表示例：

```markdown
# chunk_size 对照实验

固定：题集 cases.jsonl、FakeEmbedder dim=32、k=3、overlap=8

| chunk_size | Hit@3 | MRR | n | 备注 |
| --- | --- | --- | --- | --- |
| 40 | 0.xx | 0.xx | 4 | |
| 80 | 0.xx | 0.xx | 4 | |

结论：……（Fake 下勿过度外推；有真 embedding 后用同一题集重跑）
```

### A1 参考答案（模板填写示例）

```markdown
## Case: 静默空索引

- 症状：任意问题 Top-K 空或只能拒答；`len(store)==0`
- 复现步骤：让 embed 抛错且 ingest 用 broad except 吞掉；再 ask
- 检查顺序：
  - [x] `len(index)` / ingest 返回值
  - [ ] query/doc 是否同一 embedder
  - [ ] 维度是否一致
  - [ ] 过滤是否过严
  - [ ] Top-K 噪声
  - [ ] 拒答纪律
- 根因归类：空索引
- 修复：ingest 不要吞异常；返回 chunk 数；启动时断言 `len(store)>0`
- 修复后验证：ingest 返回 >0；Hit@K 脚本能跑出 per_case

## Case: min_score 过高导致全拒答

- 症状：明明库里有字面相近文档，ask 全是「不知道」
- 复现步骤：`MiniRAG(min_score=0.99)` + Fake 向量
- 检查顺序：勾选过滤 / 拒答
- 根因归类：过滤
- 修复：降低阈值或 Fake 下先不用 min_score；阈值要在真模型分数分布上标定
- 修复后验证：普通题 `refused is False`；拒答题仍拒
```

### A2 思路 + 参考答案

**思路**

1. 多召回保证精排有挑选空间；再截断进 Prompt 控噪声与长度。
2. 教学用词重叠打分即可；生产换 cross-encoder。
3. 权衡：多一次打分延迟/成本，换更高精度 Top-N。

**书面 3 行（示例）**

```text
1. 延迟：多一阶段打分，P95 上升，但通常远小于「把 50 段全塞进 LLM」。
2. 成本：精排模型/API 有费用；比盲目加大 context 往往更省。
3. 先多后精：第一阶段召回覆盖金标，第二阶段去掉噪声，避免 K 太小漏召回。
```

**参考答案**

```python
import re


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"\w+", s.lower()))


def fake_rerank(
    query: str,
    candidates: list[dict],
    *,
    top_n: int = 5,
) -> list[dict]:
    q = _tokens(query)
    scored: list[tuple[int, dict]] = []
    for c in candidates:
        overlap = len(q & _tokens(c.get("text") or ""))
        scored.append((overlap, c))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in scored[:top_n]]


query = "reset email password"
candidates = [
    {"chunk_id": "1", "text": "reset wifi password on router", "source": "net.md"},
    {"chunk_id": "2", "text": "reset email password in security settings", "source": "mail.md"},
    {"chunk_id": "3", "text": "change mailbox password via SSO", "source": "sso.md"},
]
out = fake_rerank(query, candidates, top_n=2)
assert out[0]["chunk_id"] == "2"
assert len(out) == 2

# 接入 ask 前：
# hits = rag.retrieve(q, k=8)
# hits = fake_rerank(q, hits, top_n=3)
# messages = build_rag_prompt(q, hits)
```

### C1 思路 + 参考答案

**思路**

1. 检索报表复用 `evaluate_retrieval`。
2. 生成 accuracy：按题型规则二元判对；失败写入 `fail_cases`。
3. 报告里分两栏，避免「生成胡编却去狂调 chunk」。

**参考答案**

```python
def evaluate_e2e(
    rag: MiniRAG,
    cases: list[dict],
    *,
    k: int = 3,
) -> dict:
    retrieval = evaluate_retrieval(
        cases,
        lambda q, k=k: rag.retrieve(q, k=k),
        k=k,
    )

    fail_cases: list[dict] = []
    ok = 0
    n = 0
    for case in cases:
        n += 1
        out = rag.ask(case["question"])
        expect_refuse = bool(case.get("expect_refuse"))
        expected = set(case.get("expected_sources") or [])
        cit_sources = set()
        for c in out.get("citations") or []:
            # citations 形如 "[1] faq.md"
            parts = str(c).split(maxsplit=1)
            if len(parts) == 2:
                cit_sources.add(parts[1].strip())

        if expect_refuse:
            good = bool(out.get("refused")) and ("不知道" in (out.get("answer") or ""))
            reason = "refuse_ok" if good else "should_refuse"
        else:
            overlap = bool(cit_sources & expected) if expected else False
            good = (
                (not out.get("refused"))
                and bool(out.get("answer"))
                and overlap
            )
            reason = "ok" if good else "bad_answer_or_citation"

        if good:
            ok += 1
        else:
            fail_cases.append(
                {
                    "id": case.get("id"),
                    "question": case.get("question"),
                    "reason": reason,
                    "answer": out.get("answer"),
                    "citations": out.get("citations"),
                }
            )

    return {
        "retrieval": {
            "hit_rate": retrieval["hit_rate"],
            "mrr": retrieval["mrr"],
            "n": retrieval["n"],
        },
        "generation": {
            "n": n,
            "accuracy": (ok / n) if n else 0.0,
            "fail_cases": fail_cases,
        },
    }


# ---- 验收骨架 ----
# rag = MiniRAG(chunk_size=48, overlap=8, top_k=3)
# for source, text in texts.items():
#     rag.ingest(source, text, doc_id=source.replace(".md", ""))
# e2e = evaluate_e2e(rag, cases, k=3)
# assert 0.0 <= e2e["generation"]["accuracy"] <= 1.0
```

`eval_report.md` 表示例：

```markdown
# MiniRAG 端到端评测报告

- 路径：Fake embedding + MemoryVectorStore + FakeLLM（complete→dict）
- 题集：cases.jsonl（N=5，含 1 拒答）

## 检索侧

| 指标 | 值 |
| --- | --- |
| Hit@3 | 0.xx |
| MRR | 0.xx |
| n（非拒答题） | 4 |

## 生成侧

| 指标 | 值 |
| --- | --- |
| accuracy | 0.xx |
| n | 5 |

## 失败 case

| id | reason | 备注 |
| --- | --- | --- |
| q4 | bad_answer_or_citation | … |

## 已知失败演练（空库）

空库时普通题应失败、拒答题应成功——用于验证拒答短路。
```

---

### 一页速查

```text
题集 jsonl → retrieve → Hit@K / MRR（检索账）
         → ask → accuracy / fail_cases（生成账）
调参：一次只拧一个旋钮；先查空索引，再谈 chunk_size。
Fake 练流程；有真 embedding 后同一题集重跑再选型。
```
