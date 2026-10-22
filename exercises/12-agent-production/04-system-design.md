# 练习：Agent 系统设计

> 对应文档：[`docs/12-agent-production/04-system-design.md`](../../docs/12-agent-production/04-system-design.md)  
> 状态：`已完成出题`  
> 建议用时：90～140 分钟（含热身；以可评审文档 + 边界骨架为主）  
> 运行环境：Python ≥ 3.11 · FakeLLM dict 契约 · 伪服务可离线跑

## 练习说明

1. 先读完文档「必掌握」：端到端架构、同步/异步边界、降级 1～5、成本杠杆、设计检查清单。
2. 题目分档：**热身 / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议产出目录：

```text
playground/12-agent-production/system-design/
├── architecture.md      # 图 + 场景
├── decisions.md         # 决策表 / 降级 / 成本
├── design_outline.md    # 可评审大纲（A 题）
└── mini_service.py      # C 题伪服务（可选）
```

4. FakeLLM / Runtime 返回形状：

```text
complete(...) -> assistant dict   # 含 role；常有 content / tool_calls
Agent / ask 汇总 -> {answer, trace, usage} 或含 run_id / path
```

5. 横切能力对齐前三章：Eval harness、观测字段允许列表、`authorize` 默认拒绝。评测命令可引用：

```bash
python playground/12-agent-production/evaluation/run_eval.py
python playground/12-agent-production/evaluation/run_eval.py --write-baseline
```

6. 本章允许大量「伪代码 / 内存队列」；**不必**起真 Redis / 真网关。先自己做完，再看文末答案。

---

## 热身题（建议先做）

### W1. 场景一句话

**要求**：选定一个场景（内部知识库 Bot / 客服辅助 / 只读代码问答等），用一句话写清：用户是谁 + 核心任务。

**验收**：同学能听懂「为谁解决什么」。

---

### W2. 同步还是异步？

**给定**：① 单次短问答预计 &lt; 3s；② 多步调研预计 2 分钟。

**要求**：各选路径（sync / async_job）并写一句理由。

**验收**：② 必须倾向异步或「强制截断 + 产品确认」。

---

### W3. FakeLLM 契约确认

**要求**：写一个同步或 async 的 `FakeLLM.complete`，返回 `{"role":"assistant","content":...}`，**不要**返回裸 `str`。

**验收**：`isinstance(msg, dict) and msg["role"] == "assistant"`。

---

### W4. 横切三件套

**要求**：列出评测 / 观测 / 安全在架构图上各挂在哪一层（一句话 × 3）。

**验收**：提到 harness 门禁、`trace_id`、工具 ACL/脱敏之一组关键词。

---

## 基础题（必做）

### B1. 端到端架构图

在 `architecture.md` 用 ASCII 或 Mermaid 画出生产级 Agent 拓扑，至少标注：

```text
Client → API（鉴权）→ 同步短路径 / 异步 Job
                      ↓
                 Agent Runtime → LLM Adapter（Fake/真）
                               → Tools（ACL）
                               → RAG / Memory / DB
外挂横切：Observability · Evaluation · Security
```

图下用表格说明四层：接入层 / 编排层 / 能力适配层 / 数据层。

附：**场景与非功能**（SLA、日请求量粗估、是否允许异步、数据敏感级别）。

**验收**：图含同步与异步两条箭头；横切不是「可选插件」口吻。

---

### B2. 同步 / 异步边界代码骨架（FakeLLM dict）

实现（可单文件）边界骨架，**不依赖真队列**：

```python
class Path(str, Enum):
    SYNC = "sync"
    ASYNC_JOB = "async_job"

def decide_path(...) -> RouteDecision: ...

class FakeLLM:
    async def complete(self, messages: list[dict], **kwargs) -> dict: ...

async def handle_sync_ask(...) -> dict:  # 含 answer / run_id / path / usage?
async def handle_create_job(...) -> dict:  # 202 语义：job_id + queued
async def worker_once(...) -> None:  # 从内存队列取任务，复用同一 runtime
```

要求：

1. `complete` 返回 assistant dict
2. 同步路径硬顶 `max_steps`（如 4）
3. 异步路径 **只入队**，不在 API 函数里跑长循环
4. Worker 与 API **复用**同一 `runtime.run`
5. 附断言：`decide_path` 对长短任务分支；`handle_create_job` 立即返回 `queued`

**验收**：`asyncio.run` 下短问同步绿；长任务拿到 `job_id` 后 worker 能把状态推到 `succeeded`。

---

### B3. 降级层级表

在 `decisions.md` 给出降级层级 **1～5** 表（可按正文调整命名，但层级清晰），例如：

| 层级 | 触发 | 用户可见行为 | 系统动作 |
|------|------|--------------|----------|
| L1 | 工具超时 | … | 跳过工具 / 重试一次 |
| L2 | LLM 5xx / 超时 | … | 切备份模型或 Fake 拒答模板 |
| … | … | … | … |
| L5 | 费用熔断 / 全局过载 | … | 拒绝新任务 / 仅健康检查 |

再列出 ≥5 个故障剧本：LLM 宕机、向量库慢、工具 500、注入/越权、费用突增——映射到层级。

**验收**：表可评审；每个故障有对应层级，不是全写「重试」。

---

### B4. 成本控制清单

列出可执行的成本控制清单（checkbox），至少覆盖：

- [ ] 模型路由（简单题小模型）
- [ ] 检索 / 上下文截断
- [ ] `max_steps` / max_tool_calls
- [ ] 缓存（语义或精确，注明失效）
- [ ] 用户 / 租户配额
- [ ] 评测门禁：防「更贵没更好」（对齐 Eval baseline）
- [ ] 观测：token / latency 进报表

每项用一句话写「怎么落到你的场景」。

**验收**：清单 ≥7 项；显式提到评测防回归变贵。

---

## 进阶题（建议至少做 1 题）

### A1. 可评审设计文档大纲填写

复制并填满下列大纲到 `design_outline.md`（每节不少于 3 条要点）：

```text
1. 场景与非功能需求
2. 端到端架构（附链接到 architecture.md）
3. 关键决策表（超时 / 降级 / 鉴权 / 成本 / 评测 / 脱敏）≥6 行
4. 失败剧本（≥5）
5. 接口草图（ask / jobs / healthz / readyz）
6. 安全与观测默认值（authorize、允许列表、分隔符弱缓解说明）
7. 发版门禁（Fake Eval 必绿 + baseline）
8. 开放问题与风险
```

**验收**：同学能按文档拆 1～2 周实现任务；决策表含理由与风险列。

---

### A2. 平台化演进阶段

画出 **3 个阶段**（约 3 个月节奏可自定）并说明每阶段「做 / 不做」：

| 阶段 | 目标 | 必交付 | 明确不做 |
|------|------|--------|----------|
| MVP | 可演示可测 | … | … |
| 可运维 | 观测+评测+ACL | … | … |
| 平台化雏形 | 多团队复用 | … | … |

点出：多租户、统一 Runtime SDK、自助配置工具白名单、评测即服务——哪些放到阶段 3。

**验收**：阶段边界清楚；避免 MVP 就上完整多租户平台。

---

## 挑战题（可选）

### C1. 把 API + Job + Runtime + Eval + Obs 边界拼成可跑伪服务

在 `mini_service.py`（或包）实现**完整可跑**的内存伪服务，模块边界清晰：

```text
API: ask(message) / create_job(payload) / get_job(job_id)
JobStore: 内存 dict + 队列
Runtime: FakeLLM + 可选假工具；输出 {answer, trace, usage}
Obs: RunContext / 计数；日志字段允许列表（无 messages 全文）
Eval: 对固定 2～3 条 case 调用同一 runtime，打印 passed/total
Security: authorize 在工具前；默认拒绝 shell
```

约束：

1. Python ≥ 3.11；同步教学可用 `asyncio.run` 包一层
2. FakeLLM 返回 dict；Agent 对外 `{answer, trace, usage}`
3. 不引入真实外网 / 真实密钥
4. `__main__` demo：同步 ask → 异步 job → 跑一小段 eval

**验收**：一键运行 demo 全绿；目录/函数名能看出边界。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4（架构图、同步异步骨架、降级表、成本清单）
- [ ] Fake 路径可离线；接口形状含 `run_id` / `job_id` 或等价
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 伪服务可跑

---

## 提示与参考答案（先做题再看）

W1 参考答案

```text
场景：面向内部员工的知识库问答 Bot——用公司文档回答「流程/配置」类问题，允许异步深挖。
```

W2 参考答案

```text
① sync：短 SLA，用户同步等待可接受
② async_job：多步调研超过产品可等待时间 → 入队返回 job_id；若产品禁止异步则强制 max_steps 截断并明示
```

W3 参考答案

```python
from __future__ import annotations

from typing import Any


class FakeLLM:
    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        last = messages[-1].get("content", "") if messages else ""
        return {"role": "assistant", "content": f"echo:{last}", "tool_calls": []}


import asyncio

msg = asyncio.run(FakeLLM().complete([{"role": "user", "content": "hi"}]))
assert isinstance(msg, dict) and msg["role"] == "assistant"
```

W4 参考答案

```text
Evaluation：CI / 发版门禁，挂在 Runtime 同契约的离线 harness（cases→baseline）
Observability：贯穿 API→Runtime→Worker 每跳的 trace_id / metrics
Security：接入鉴权 + Runtime 内 authorize/脱敏；分隔符仅弱缓解
```

B1 思路 + 参考答案

**思路**

先对齐「请求从哪进、何时同步、何时入队」；横切画在旁边但箭头要能挂 `trace_id`。

**参考答案（architecture.md 节选）**

```text
Client (Web)
   │ HTTPS + Auth
   ▼
FastAPI API
   ├─ SYNC:  POST /v1/agent/ask  → Runtime(max_steps=4) → Answer+run_id
   └─ ASYNC: POST /v1/jobs       → Queue → Worker → Runtime → JobStore
                                      ▲
                                      └── 与 API 复用同一 Runtime

Runtime → LLMPort(FakeLLM|Provider) / Tools(ACL) / RAG / DB

横切：Obs(logs/metrics/traces) · Eval(harness/baseline) · Security(authz/redact)
```

| 层 | 职责 |
|----|------|
| 接入层 | 鉴权、校验、路由 sync/async |
| 编排层 | Usecase、Job 状态、调 Runtime |
| 能力适配层 | LLM/Tools/RAG 端口 |
| 数据层 | DB/Redis/Vector |

非功能示例：p95 &lt; 5s（同步）；异步 2 分钟内完成；日 5 万请求；文档含中敏感，日志默认脱敏。

B2 思路 + 参考答案

**思路**

边界对了，Worker 才能复用 Runtime；API 进程内跑长循环是雪崩温床。`BackgroundTasks` ≠ 长任务队列。

**参考答案**

```python
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Path(str, Enum):
    SYNC = "sync"
    ASYNC_JOB = "async_job"


@dataclass
class RouteDecision:
    path: Path
    reason: str


def decide_path(
    *,
    estimated_steps: int,
    needs_tools: bool,
    user_allows_wait: bool,
    sla_seconds: float,
) -> RouteDecision:
    if estimated_steps <= 2 and sla_seconds <= 8 and not (needs_tools and estimated_steps > 3):
        return RouteDecision(Path.SYNC, "short_path")
    if not user_allows_wait:
        return RouteDecision(Path.SYNC, "forced_sync_with_hard_cap")
    return RouteDecision(Path.ASYNC_JOB, "long_or_multi_step")


class FakeLLM:
    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        last = messages[-1].get("content", "") if messages else ""
        return {"role": "assistant", "content": f"echo:{last}", "tool_calls": []}


@dataclass
class Runtime:
    llm: FakeLLM

    async def run(self, message: str, *, max_steps: int = 4) -> dict[str, Any]:
        _ = max_steps
        msg = await self.llm.complete([{"role": "user", "content": message}])
        return {
            "answer": msg.get("content") or "",
            "trace": [{"type": "llm", "step": 1}],
            "usage": {"total_tokens": 10},
            "run_id": uuid.uuid4().hex[:10],
        }


@dataclass
class JobStore:
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)

    async def enqueue(self, job_type: str, payload: dict[str, Any]) -> str:
        job_id = uuid.uuid4().hex[:10]
        self.jobs[job_id] = {
            "id": job_id,
            "type": job_type,
            "payload": payload,
            "status": "queued",
            "result": None,
            "error": None,
        }
        await self.queue.put(job_id)
        return job_id

    async def reserve(self) -> dict[str, Any]:
        job_id = await self.queue.get()
        job = self.jobs[job_id]
        job["status"] = "running"
        return job

    async def complete(self, job_id: str, result: dict[str, Any]) -> None:
        self.jobs[job_id]["status"] = "succeeded"
        self.jobs[job_id]["result"] = result

    async def fail(self, job_id: str, error: str) -> None:
        self.jobs[job_id]["status"] = "failed"
        self.jobs[job_id]["error"] = error


async def handle_sync_ask(runtime: Runtime, message: str) -> dict[str, Any]:
    result = await runtime.run(message, max_steps=4)
    return {
        "answer": result["answer"],
        "run_id": result["run_id"],
        "path": "sync",
        "usage": result["usage"],
        "trace": result["trace"],
    }


async def handle_create_job(jobs: JobStore, payload: dict[str, Any]) -> dict[str, Any]:
    job_id = await jobs.enqueue("agent_run", payload)
    return {"job_id": job_id, "status": "queued", "path": "async_job"}


async def worker_once(jobs: JobStore, runtime: Runtime) -> None:
    job = await jobs.reserve()
    try:
        result = await runtime.run(job["payload"]["message"], max_steps=16)
        await jobs.complete(job["id"], result)
    except Exception as exc:  # 教学简化
        await jobs.fail(job["id"], error=type(exc).__name__)


async def _demo() -> None:
    runtime = Runtime(FakeLLM())
    jobs = JobStore()

    d1 = decide_path(
        estimated_steps=1, needs_tools=False, user_allows_wait=True, sla_seconds=5
    )
    d2 = decide_path(
        estimated_steps=10, needs_tools=True, user_allows_wait=True, sla_seconds=5
    )
    assert d1.path is Path.SYNC and d2.path is Path.ASYNC_JOB

    sync_out = await handle_sync_ask(runtime, "健康检查")
    assert sync_out["path"] == "sync" and sync_out["answer"].startswith("echo:")

    created = await handle_create_job(jobs, {"message": "深度研究 Orion"})
    assert created["status"] == "queued"
    await worker_once(jobs, runtime)
    assert jobs.jobs[created["job_id"]]["status"] == "succeeded"
    print("B2 ok", sync_out["run_id"], created["job_id"])


# asyncio.run(_demo())
```

B3 思路 + 参考答案

**思路**

降级要「用户仍可能完成任务」或「明确失败」，避免超时后模型瞎编。

**参考答案（层级表）**

```markdown
| 层级 | 触发 | 用户可见 | 系统动作 |
|------|------|----------|----------|
| L1 局部重试 | 单工具超时/5xx | 略慢 | 重试 1 次或换镜像工具 |
| L2 功能降级 | 检索失败 | 「未引用资料的谨慎回答」或拒答 | 跳过 RAG，收紧 prompt |
| L3 模型降级 | 主模型不可用 | 可能变短/变弱 | 备份模型；同步路径降 max_steps |
| L4 只读安全模式 | 注入飙升/ACL 拒绝激增 | 拒绝写操作 | 禁用写工具；人审门全开 |
| L5 过载/费用熔断 | 预算或 p99 崩溃 | 503 / 排队提示 | 拒新任务；保 healthz |

故障映射：
- LLM 宕机 → L3
- 向量库慢 → L1 然后 L2
- 工具 500 → L1
- 注入/越权飙升 → L4
- 费用突增 → L5 + 配额
```

B4 思路 + 参考答案

**参考答案（成本清单）**

```markdown
- [x] 模型路由：FAQ 走小模型；复杂推理才升高配
- [x] 上下文截断：top_k 与 max_chars；超长对话摘要
- [x] max_steps=8（同步 4）；防止空转烧钱
- [x] 精确缓存：相同问题短 TTL；变更文档即失效
- [x] 租户日配额：token 与请求双上限
- [x] Eval 门禁：`run_eval.py` + baseline，拒绝「accuracy 持平但 avg_steps/tokens 暴涨」的发布
- [x] Obs：每 run 记 total_tokens / latency；周报看 p95 成本
- [x] 工具结果 preview 截断：降上下文再喂回模型的 token
```

A1 思路 + 参考答案

**参考答案（design_outline.md 填写示例节选）**

```markdown
# 设计大纲：内部知识库 Agent

## 1. 场景与非功能
- 用户：内部员工；任务：文档问答 + 少量只读检索工具
- SLA：同步 p95&lt;5s；异步研究 &lt;120s
- 量级：日 5 万；允许异步；中敏感文档

## 2. 架构
- 见 architecture.md；模块化单体起步

## 3. 决策表
| 决策点 | 选择 | 理由 | 风险 |
|--------|------|------|------|
| 长任务 | 队列 Job | 避免拖垮 API | 队列运维 |
| 超时 | sync 8s / tool 3s | 快速失败 | 误杀慢检索 |
| 降级 | L1～L5 | 可控体验 | 需演练 |
| 鉴权 | 网关 JWT + 角色 | 接公司 IdP | 角色映射错 |
| 成本 | 路由+配额+max_steps | 账单可控 | 配额过严伤体验 |
| 评测 | Fake harness+baseline | CI 必绿 | case 不足 |
| 脱敏 | 允许列表+redact | 防泄露 | 排障变难 |

## 4. 失败剧本
（略，映射 B3）

## 5. 接口草图
- POST /v1/agent/ask → {answer, run_id, usage}
- POST /v1/jobs → {job_id, status}
- GET /v1/jobs/{id}
- GET /healthz /readyz

## 6. 安全与观测默认
- authorize(role,tool,args) 在 registry 前；默认拒绝
- 日志允许列表；不记 messages/API Key
- 分隔符 UNTRUSTED_DOC = 弱缓解，须配合 ACL

## 7. 发版门禁
- python playground/12-agent-production/evaluation/run_eval.py
- 与 baseline 比：无 regressions；关注 avg_steps/tokens

## 8. 开放问题
- 是否要 SSE；多租户何时做；人审工作流谁承接
```

A2 思路 + 参考答案

**参考答案**

```markdown
| 阶段 | 目标 | 必交付 | 明确不做 |
|------|------|--------|----------|
| MVP（周 1～4） | 可演示可测 | sync ask + FakeLLM + 8 条 eval + 基础 ACL | 多租户计费、复杂工作流引擎 |
| 可运维（周 5～8） | 看得见管得住 | JSONL/metrics、baseline CI、降级 L1～L3、异步 Job | 完整 SSO 套件、跨区域合规平台 |
| 平台化雏形（周 9～12） | 多团队复用 | Runtime SDK、工具白名单配置化、评测即服务、租户配额 | 自研「万能 Agent 云」大而全 |

阶段 3 再碰：统一控制台、自助注册工具（仍默认拒绝）、多租户强隔离。
```

C1 思路 + 参考答案

**思路**

用内存拼齐边界，证明「层可换、Fake 可测」。Eval/Obs/Sec 不要糊进一个 200 行函数无缝。

**参考答案（mini_service.py 完整可跑）**

```python
from __future__ import annotations

import asyncio
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


# ---------- Security ----------
ALLOWED = {"viewer": {"search", "calculator"}, "operator": {"search", "calculator"}}


def authorize(role: str, tool: str, args: dict[str, Any]) -> tuple[bool, str]:
    _ = args
    if tool not in ALLOWED.get(role, set()):
        return False, f"tool not allowed: {tool}"
    return True, "ok"


def redact(text: str) -> str:
    text = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-[REDACTED]", text)
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[EMAIL]", text)
    return text


# ---------- Obs ----------
ALLOWED_LOG_KEYS = {"run_id", "type", "name", "ok", "step", "latency_ms", "status"}


def to_log(event: dict[str, Any]) -> dict[str, Any]:
    return {k: event[k] for k in ALLOWED_LOG_KEYS if k in event}


@dataclass
class Metrics:
    requests: int = 0
    tokens: int = 0

    def summary(self) -> dict[str, int]:
        return {"requests": self.requests, "tokens": self.tokens}


# ---------- Runtime ----------
class FakeLLM:
    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        last = messages[-1].get("content", "") if messages else ""
        if "搜索" in last:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {"name": "search", "arguments": '{"query":"RAG"}'},
                    }
                ],
            }
        return {"role": "assistant", "content": f"echo:{last}", "tool_calls": []}


def search(query: str) -> list[str]:
    return [f"doc:{query}:0"]


REGISTRY: dict[str, Callable[..., Any]] = {"search": search}


@dataclass
class Runtime:
    llm: FakeLLM
    role: str = "viewer"

    async def run(self, message: str, *, max_steps: int = 4) -> dict[str, Any]:
        import json

        run_id = uuid.uuid4().hex[:10]
        trace: list[dict[str, Any]] = []
        messages: list[dict[str, Any]] = [{"role": "user", "content": message}]
        tokens = 0

        for step in range(1, max_steps + 1):
            t0 = time.perf_counter()
            msg = await self.llm.complete(messages)
            latency = (time.perf_counter() - t0) * 1000
            tokens += 20
            trace.append(
                {
                    "type": "llm",
                    "step": step,
                    "latency_ms": round(latency, 2),
                    "run_id": run_id,
                }
            )
            calls = msg.get("tool_calls") or []
            if not calls:
                answer = redact(msg.get("content") or "")
                return {
                    "answer": answer,
                    "trace": trace,
                    "usage": {"total_tokens": tokens},
                    "run_id": run_id,
                }

            fn = calls[0]["function"]
            name = fn["name"]
            args = json.loads(fn.get("arguments") or "{}")
            ok, reason = authorize(self.role, name, args)
            if not ok:
                trace.append({"type": "acl_denied", "name": name, "step": step, "run_id": run_id})
                return {
                    "answer": redact(f"拒绝工具：{reason}"),
                    "trace": trace,
                    "usage": {"total_tokens": tokens},
                    "run_id": run_id,
                }
            trace.append({"type": "tool_call", "name": name, "step": step, "run_id": run_id})
            result = REGISTRY[name](**args)
            trace.append(
                {
                    "type": "tool_result",
                    "name": name,
                    "ok": True,
                    "step": step,
                    "run_id": run_id,
                }
            )
            messages.append(msg)
            messages.append(
                {"role": "tool", "name": name, "content": json.dumps(result, ensure_ascii=False)}
            )

        return {
            "answer": "max steps",
            "trace": trace,
            "usage": {"total_tokens": tokens},
            "run_id": run_id,
        }


# ---------- Job + API ----------
@dataclass
class JobStore:
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)

    async def enqueue(self, payload: dict[str, Any]) -> str:
        job_id = uuid.uuid4().hex[:8]
        self.jobs[job_id] = {"status": "queued", "payload": payload, "result": None}
        await self.queue.put(job_id)
        return job_id

    async def worker_once(self, runtime: Runtime) -> None:
        job_id = await self.queue.get()
        self.jobs[job_id]["status"] = "running"
        result = await runtime.run(self.jobs[job_id]["payload"]["message"], max_steps=8)
        self.jobs[job_id]["status"] = "succeeded"
        self.jobs[job_id]["result"] = result


@dataclass
class Api:
    runtime: Runtime
    jobs: JobStore
    metrics: Metrics = field(default_factory=Metrics)
    logs: list[dict[str, Any]] = field(default_factory=list)

    async def ask(self, message: str) -> dict[str, Any]:
        out = await self.runtime.run(message, max_steps=4)
        self.metrics.requests += 1
        self.metrics.tokens += int((out.get("usage") or {}).get("total_tokens") or 0)
        for ev in out.get("trace") or []:
            self.logs.append(to_log(ev))
        return {
            "answer": out["answer"],
            "run_id": out["run_id"],
            "path": "sync",
            "usage": out["usage"],
            "trace": out["trace"],
        }

    async def create_job(self, message: str) -> dict[str, Any]:
        job_id = await self.jobs.enqueue({"message": message})
        return {"job_id": job_id, "status": "queued", "path": "async_job"}

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self.jobs.jobs[job_id]


# ---------- Eval（迷你，对齐 check 语义） ----------
def check_answer(answer: str, expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for needle in expected.get("answer_contains") or []:
        if needle not in answer:
            errors.append(f"missing: {needle!r}")
    return errors


def check_trace(trace: list[dict], forbidden: set[str]) -> list[str]:
    return [
        f"forbidden tool: {e.get('name')}"
        for e in trace
        if e.get("type") == "tool_call" and e.get("name") in forbidden
    ]


async def run_mini_eval(runtime: Runtime) -> dict[str, Any]:
    cases = [
        {"id": "echo", "input": "你好", "expected": {"answer_contains": ["echo"], "forbidden_tools": ["shell"]}},
        {
            "id": "search",
            "input": "请搜索资料",
            "expected": {"answer_contains": ["echo"], "forbidden_tools": ["shell"]},
        },
    ]
    # 第二题：工具后下一轮 Fake 会 echo；放宽为不强制 echo 也行——此处再跑一步已在 runtime 循环内消化
    rows = []
    for case in cases:
        out = await runtime.run(case["input"])
        errs = check_answer(out["answer"], case["expected"])
        errs += check_trace(out["trace"], set(case["expected"].get("forbidden_tools") or []))
        rows.append({"id": case["id"], "ok": not errs, "errors": errs})
    passed = sum(1 for r in rows if r["ok"])
    return {"passed": passed, "total": len(rows), "rows": rows}


async def main() -> None:
    api = Api(runtime=Runtime(FakeLLM()), jobs=JobStore())
    sync_out = await api.ask("你好")
    assert sync_out["path"] == "sync"

    created = await api.create_job("异步研究")
    await api.jobs.worker_once(api.runtime)
    job = api.get_job(created["job_id"])
    assert job["status"] == "succeeded"

    report = await run_mini_eval(api.runtime)
    print("eval", report)
    print("metrics", api.metrics.summary())
    print("log_sample", api.logs[:2])
    assert "messages" not in str(api.logs)
    print("C1 mini_service ok", sync_out["run_id"], created["job_id"])


if __name__ == "__main__":
    asyncio.run(main())
```

说明：完整项目请把 Eval 换接  
`python playground/12-agent-production/evaluation/run_eval.py`  
同一 `RunFn` 契约即可。

---

## 导航

- 文档：[Agent 系统设计](../../docs/12-agent-production/04-system-design.md)
- 模块首页：[12-agent-production](../../docs/12-agent-production/README.md)
- 上一练习：[03-security](./03-security.md)
- Eval 入口：[evaluation](../../playground/12-agent-production/evaluation/)
