# Agent 系统设计

> 所属模块：`12-agent-production` · Agent 工程化与生产落地  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（以「可评审设计文档」为目标；代码示例多为边界与伪代码，全程可用 FakeLLM）  
> 对应练习：[`exercises/12-agent-production/04-system-design.md`](../../exercises/12-agent-production/04-system-design.md)  
> 运行环境：Python ≥ 3.11 · 教学可用同步边界示例；生产偏好 `async` + 队列（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）

## 本章定位

- **模块目标**：具备评测、可观测、安全与系统设计能力，接近生产级。
- **本章角色**：把 01～12 的积木装成「能上线讨论」的端到端架构——同步/异步边界、失败降级、成本控制、平台化演进。
- **产出形态**：可评审的设计检查清单 + 架构图 + 决策表；**不必一次写完全部代码**。
- **核心观点**：框架会变；能讲清边界、降级与成本的人，才能把 Agent 从 Demo 推到可运维系统。
- **前置**：本模块评测 / 观测 / 安全三章；模块 11 Runtime；模块 06 FastAPI；模块 07 队列；模块 10 RAG。
- **收官意义**：整门课从 Programming → Backend → System → AI Engineering 的汇合点。

## 学习目标（学完应能做到）

1. 画出生产级 Agent 端到端架构，并标注 Client / API / Job / Worker / Runtime / LLM / Tools / RAG / DB。
2. 划分同步短路径与异步 Job 边界；说明为何 `BackgroundTasks` ≠ 长任务。
3. 设计失败降级层级 1～5，并给出熔断/超时默认值思路。
4. 提出成本控制手段（路由、缓存、截断、`max_steps`、配额、评测防「更贵没更好」）。
5. 规划平台化演进路线；能扫一眼多租户地图。
6. 输出一份可评审的设计检查清单（本章以文档产出为目标）。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 端到端架构、同步/异步边界、降级 1～5、成本杠杆、设计检查清单 | 能做设计评审级输出 |
| **建议掌握** | 平台化演进、接口边界与决策表 | 能规划 3 个月路线 |
| **了解即可** | 多租户平台地图 | 企业阶段专项，先知道有哪些面 |

---

## 0. 设计课怎么学（先定产出）

这一章不是再教一个库，而是教你**怎么把已学模块讲成一张能评审的图**。

### 0.1 为什么「文档产出」比「堆代码」更重要？

上线前真正卡住团队的往往是：

| 卡住点 | 没写清时会发生什么 |
|--------|-------------------|
| 同步还是异步？ | API 被工具循环拖垮，超时雪崩 |
| 失败怎么降？ | 模型瞎编、用户看到 500 栈 |
| 钱怎么控？ | 账单先于产品炸 |
| 谁负责评测/观测？ | 改 prompt 静默变差，排障靠猜 |

所以练习目标是：一份同学能按图拆任务的设计文档（见练习 A～E）。

### 0.2 怎么写（本章交付物清单）

评审时至少交出这五件：

```text
1) 场景与非功能需求（用户 / SLA / 量级 / 是否允许异步）
2) 端到端架构图（同步路径 + 异步路径）
3) 关键决策表（超时 / 降级 / 鉴权 / 成本 / 评测 / 脱敏）
4) 失败剧本（≥5 个故障 → 应对层级）
5) 设计检查清单（本章 §8，打勾即评审议程）
```

### 0.3 对照：Demo 架构 vs 生产架构

| 维度 | Demo | 生产讨论应有的样子 |
|------|------|-------------------|
| 入口 | 一个脚本 `main.py` | FastAPI + Auth |
| 长任务 | 同步阻塞到结束 | Job + Queue + Worker |
| LLM | 直连 Key | Port + FakeLLM / 真模型可切换 |
| 失败 | `print` / 抛异常 | 降级层级 + 友好错误 |
| 成本 | 不看 | 路由 / 配额 / 评测护栏 |
| 观测 | 无 | `trace_id` 贯穿 + metrics |
| 安全 | 无 | ACL / 脱敏 / 注入边界 |

> 口令：**先能画边界，再谈拆服务。**

---

## 1. 端到端架构（必掌握）

把模块 01～12 的能力放进一张可白板讨论的图。

### 1.1 为什么要先画「一张总图」？

没有总图时，每个人脑中的「Agent 服务」不一样：

- 前端同学以为是「一个 chat HTTP」
- 后端同学以为是「再加几个工具函数」
- 算法同学以为是「换个更强模型」

总图强迫你们对齐：**请求从哪进、何时同步返回、何时进队列、Runtime 调谁、观测与评测挂在哪**。

### 1.2 怎么画（参考拓扑）

```text
Client (Web / App / 内部服务)
   │  HTTPS + Auth（API Key / JWT）
   ▼
API Gateway / FastAPI（接入层）
   │
   ├─ 同步短路径
   │    POST /v1/agent/ask  （< 数秒可完成）
   │         │
   │         ▼
   │    Application / Usecase
   │         │
   │         ▼
   │    Agent Runtime（图 / tool-loop）
   │         ├── LLM Adapter(s)  ← FakeLLM / 真模型
   │         ├── Tools（受 ACL）
   │         ├── RAG / Memory
   │         └── DB / Redis / Vector Store
   │         │
   │         ▼
   │    直接返回 Answer + run_id
   │
   └─ 异步 Job 路径
        POST /v1/jobs  → 入队 → 返回 job_id
               │
               ▼
            Queue（Redis/SQS/…）
               │
               ▼
            Worker（同仓或独立进程）
               │  复用同一 Runtime / Domain
               ▼
            写 Job 状态 → Client 轮询 / SSE / WS

外挂横切（贯穿每一跳，不画成「可选插件」）：
  Observability（logs / metrics / traces）
  Evaluation（offline suites / harness · CI 门禁）
  Security（鉴权、工具 ACL、脱敏）
```

四层分离（评审时用这四个词说话）：

| 层 | 职责 | 典型模块对照 |
|----|------|--------------|
| **接入层** | 鉴权、校验、路由同步/异步 | 模块 06 FastAPI + Auth |
| **编排层** | Usecase、Job 状态、调用 Runtime | 模块 08 架构 + 11 Runtime |
| **能力适配层** | LLM / Tools / RAG 端口实现 | 模块 10～11 + Provider SDK |
| **数据层** | DB / Redis / Vector | 模块 07 |

**Observability + Evaluation 是外挂横切**：不画进「业务主链」中心，但每条箭头都应能挂上 `trace_id` / 评测 case。

### 1.3 怎么写（接口边界草图）

先钉 4 个对外形状，实现可以后补：

```text
# 同步短问答
POST /v1/agent/ask
  Body: { "message": "...", "session_id?": "..." }
  → 200 { "answer": "...", "run_id": "...", "usage": {...} }
  → 504 / 503 按降级策略

# 异步长任务
POST /v1/jobs
  Body: { "type": "research", "payload": {...} }
  → 202 { "job_id": "...", "status": "queued" }

GET /v1/jobs/{job_id}
  → 200 { "status": "queued|running|succeeded|failed", "result?": ..., "error?": ... }

# 健康与就绪（运维）
GET /healthz  → 进程活着
GET /readyz   → 依赖（DB/队列/向量）可服务
```

端口（Domain）心智——与软件架构章一致：

```python
# 教学端口形状（Python ≥ 3.11）；实现可换 FakeLLM
from typing import Protocol, Any


class LLMPort(Protocol):
    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        """返回 message 形态，勿直接返回 str（见 CONVENTIONS）。"""
        ...


class JobPort(Protocol):
    async def enqueue(self, job_type: str, payload: dict[str, Any]) -> str: ...
    async def get(self, job_id: str) -> dict[str, Any]: ...
```

### 1.4 跑一下（离线：用 FakeLLM 证明「层可换」）

不必起真服务；用最小同步路径证明端口可测：

```python
from __future__ import annotations

from typing import Any


class FakeLLM:
    """离线可跑；CI 友好（CONVENTIONS）。"""

    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        last = messages[-1].get("content", "")
        return {"role": "assistant", "content": f"echo:{last}", "tool_calls": []}


async def run_short_ask(llm: FakeLLM, user_text: str) -> dict[str, Any]:
    """同步短路径：无工具、无队列——评审里的『绿色路径』。"""
    messages = [{"role": "user", "content": user_text}]
    msg = await llm.complete(messages)
    return {"answer": msg["content"], "run_id": "demo-run-1", "path": "sync"}


# 同步教学入口（生产路由里用 async def）
import asyncio

result = asyncio.run(run_short_ask(FakeLLM(), "健康检查问一句"))
assert result["path"] == "sync"
assert result["answer"].startswith("echo:")
print(result)
```

预期：无 API Key 也能绿——说明「接入层之下」可被 Fake 钉住。

### 1.5 易错点

| 错法 | 会发生什么 |
|------|------------|
| 把 Observability 画成可选插件 | 出事故才发现没有 `trace_id` |
| Client 直连向量库 / DB | 鉴权与 ACL 全丢 |
| Runtime 与 FastAPI 路由糊在一起 | 无法复用到 Worker |
| 架构图只有框没有箭头语义 | 评审不知道同步还是异步 |
| 一上来画微服务网状 | 分布式大泥球；先模块化单体 |

### 1.6 串联模块 01～12（积木对照表）

| 能力 | 主要落点 | 课程位置 |
|------|----------|----------|
| 语言与工程基础 | 类型、测试、日志字段习惯 | 模块 01～03 |
| HTTP 接入与鉴权 | FastAPI 路由、API Key/JWT | 模块 06 |
| 缓存 / 队列 | Redis、Job 入队出队 | 模块 07 |
| 模块化单体与端口 | api / application / domain / infra | 模块 08 |
| RAG | 检索、空命中降级 | 模块 10 |
| Tool / Runtime / Memory / Multi-Agent | 编排与护栏 | 模块 11 |
| 评测 harness | 发版门禁、防更贵没更好 | 模块 12-01 |
| 观测 | `trace_id`、token、工具轨迹 | 模块 12-02 |
| 安全 | 注入、ACL、脱敏 | 模块 12-03 |
| 系统设计（本章） | 边界、降级、成本、平台化 | 模块 12-04 |

---

## 2. 必掌握：同步 / 异步边界

这是本章最容易在评审上吵翻、也最值得吵清楚的一刀。

### 2.1 为什么边界错了会「全站抖」？

Agent 的「一次回答」可能是：

- 1 次 LLM（几百毫秒～数秒）
- 或 8 步工具 + 多次检索（数十秒～分钟）

若全部塞进同步 HTTP：

1. **网关/负载均衡超时**先于业务结束  
2. **worker 线程/协程被占满** → 健康的短请求也排队  
3. **客户端重试**放大流量 → 雪崩  
4. **进程重启**时进行中的请求直接消失（若还误用了进程内后台任务）

### 2.2 怎么划分（决策表）

| 维度 | 同步短路径 | 异步 Job |
|------|------------|----------|
| 完成时间 | 通常 < 数秒（团队自定 SLA） | 多步工具、深研究、批量 |
| API 返回 | 直接 `answer` | 先 `job_id`，再轮询/推送 |
| 超时 | 简单请求超时即可 | 任务级超时 + 可 checkpoint |
| 重试 | 谨慎（非幂等勿瞎重试） | 队列重试 + 幂等键 |
| 适用 | 短问答、分类、健康相关 | 研究报告、多工具调查、批量评测 |
| 失败可见性 | HTTP 状态 + 错误体 | Job `failed` + 可查询原因 |

经验口令（模块 07）：

> **用户可感知等待过长 → 上队列。**  
> 不是「技术上能不能同步跑完」，而是「产品上能不能让人干等」。

### 2.3 怎么写（同步 vs 异步伪代码边界）

```python
from __future__ import annotations

from dataclasses import dataclass
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
    """教学决策：把『感觉慢』变成可讨论的条件。"""
    if estimated_steps <= 2 and sla_seconds <= 8 and not (needs_tools and estimated_steps > 3):
        return RouteDecision(Path.SYNC, "short_path")
    if not user_allows_wait:
        # 产品不允许异步时：要么拒绝对超长任务，要么强制截断 max_steps
        return RouteDecision(Path.SYNC, "forced_sync_with_hard_cap")
    return RouteDecision(Path.ASYNC_JOB, "long_or_multi_step")


# —— 同步短路径（API 进程内跑完）——
async def handle_sync_ask(runtime: Any, message: str) -> dict[str, Any]:
    result = await runtime.run(message, max_steps=4)  # 短路径硬顶
    return {"answer": result.answer, "run_id": result.run_id, "path": "sync"}


# —— 异步：只入队，不在此跑长循环 ——
async def handle_create_job(jobs: Any, payload: dict[str, Any]) -> dict[str, Any]:
    job_id = await jobs.enqueue("agent_run", payload)
    return {"job_id": job_id, "status": "queued", "path": "async_job"}


# —— Worker：与 API 复用同一 runtime ——
async def worker_loop(jobs: Any, runtime: Any) -> None:
    job = await jobs.reserve()  # 伪代码：领取任务
    try:
        result = await runtime.run(job.payload["message"], max_steps=16)
        await jobs.complete(job.id, result)
    except Exception as exc:  # 生产应分类错误并计量
        await jobs.fail(job.id, error=str(exc))
```

### 2.4 跑一下（边界断言，不依赖真队列）

```python
d1 = decide_path(estimated_steps=1, needs_tools=False, user_allows_wait=True, sla_seconds=5)
assert d1.path == Path.SYNC

d2 = decide_path(estimated_steps=12, needs_tools=True, user_allows_wait=True, sla_seconds=5)
assert d2.path == Path.ASYNC_JOB

d3 = decide_path(estimated_steps=12, needs_tools=True, user_allows_wait=False, sla_seconds=5)
assert d3.reason == "forced_sync_with_hard_cap"
print("path decision OK")
```

### 2.5 刻意简化：`BackgroundTasks` ≠ 长任务

[`CONVENTIONS.md`](../CONVENTIONS.md) 写明：

> FastAPI `BackgroundTasks`：轻量收尾，**长任务请上队列**。

#### 为什么容易误用？

`BackgroundTasks` 看起来「请求先返回、后面再跑」，很像异步 Job。但它通常是：

- 挂在**同一个 API 进程**生命周期上  
- 进程崩溃 / 滚动发布 → **任务直接丢**  
- 没有标准的重试、可见性超时、死信、水平扩缩  

适合：写一条审计日志、清临时文件、发一个「尽量送达」的轻量通知。  
不适合：Agent 多步工具循环、长 RAG、批量报告。

#### 对照

| 机制 | 进程挂了会怎样 | 可重试 | 可扩缩 Worker | 适用 |
|------|----------------|--------|---------------|------|
| 同步 `await runtime.run` | 请求失败 | 客户端重试（慎） | 扩 API 副本 | 短路径 |
| FastAPI `BackgroundTasks` | **常丢** | 弱 | 弱 | 轻量收尾 |
| 队列 + Worker | 可重新投递（视语义） | 强 | 强 | **长任务** |

```python
# ❌ 反模式（教学标注，不要当生产方案）
# @app.post("/research")
# async def research(bg: BackgroundTasks):
#     bg.add_task(long_agent_run, ...)  # 进程一挂就没了
#     return {"ok": True}

# ✅ 正模式心智
# job_id = await queue.enqueue(...)
# return {"job_id": job_id}
```

### 2.6 易错点

| 错法 | 会发生什么 |
|------|------------|
| 「都能同步跑完」就全同步 | 高峰时 API 被长任务挤死 |
| 用 `BackgroundTasks` 冒充队列 | 发布即丢任务，难以排障 |
| 异步了但没有状态查询 API | 客户端只能干等或瞎轮询无协议 |
| Worker 复制一套 prompt/工具逻辑 | 双源真相（架构章已警告） |
| 同步路径不设 `max_steps` 硬顶 | 偶发多步把短路径拖成「伪异步」 |

### 2.7 对照：同一业务两种切法

```text
场景：内部知识库问答 Bot

切法 A（多数问答）：
  POST /ask → Runtime(max_steps=4) + RAG → 同步返回

切法 B（「汇总本周全部变更并写简报」）：
  POST /jobs → Worker Runtime(max_steps=20) → GET /jobs/{id}
```

评审问题一句话：

> **这条 API 在 P99 超过 SLA 时，是截断、拒绝，还是改异步？**

---

## 3. 必掌握：失败降级（层级 1～5）

没有降级的 Agent，不是「更智能」，只是「失败时更会一本正经胡说」。

### 3.1 为什么要分层，而不是一个巨大 `try/except`？

因为失败**类型不同，用户期望不同**：

| 失败 | 用户更想听到 |
|------|--------------|
| 某个工具 500 | 「这个来源暂时不可用，我改用…」或诚实说缺信息 |
| LLM 429 | 稍等 / 自动换备用，而不是立刻放弃 |
| RAG 空 | 「资料库没有」而不是编造条款 |
| 全链路挂 | 友好错误 + 工单入口 |
| 依赖大面积故障 | 只读/维护，而不是半残写入 |

分层让你在评审里能指着图说：「这一层归 Runtime，那一层归平台。」

### 3.2 怎么设计（降级层级 1～5）

```text
1) 单工具失败
      → 把错误以 tool 结果写回（ok=false）
      → 允许模型换工具 / 改问法
      → 同一工具连续失败 → 熔断该工具（本 run 或短 TTL）

2) LLM 429 / 短暂不可用
      → 指数退避（有上限）
      → 换备用模型 / 区域
      → 仍失败 → 升到第 4 层友好错误（勿死循环重试）

3) RAG 空命中 / 低相关
      → 明确「无资料 / 不足以下结论」
      → 禁止「自由发挥装成有引用」
      → 可选：放宽检索条件，但**不放宽权限**（安全章）

4) 全链路失败（Runtime 无法收束）
      → 对用户：友好错误 + run_id（便于工单）
      → 对内部：打 error 指标、保留脱敏轨迹
      → 可选：转人工 / 建单

5) 依赖大面积故障（LLM 厂商、向量集群、主库）
      → 只读降级 / 维护页 / 关闭写工具
      → 拒绝新的昂贵 Job 入队（保护预算与堆积）
```

### 3.3 怎么写（熔断 / 超时默认值思路）

教学默认值——**你们团队应在决策表里改成自己的数，但不能「没有数」**：

| 开关 | 建议默认（起点） | 说明 |
|------|------------------|------|
| HTTP 同步请求超时 | 8～15s | 短路径硬顶；超过应 504 或引导异步 |
| 单次 LLM 调用超时 | 30～60s | 按模型与地区调 |
| 单个工具超时 | 3～10s | 按工具；外部 HTTP 宜更短 |
| 工具连续失败熔断 | 同 run 内 2～3 次 | 避免死循环刷工具 |
| LLM 429 最大重试 | 2～3 次 | 带抖动退避；其后换模或失败 |
| Job 总时长 | 2～10 min | 视产品；超时写 `failed` |
| `max_steps`（同步） | 4～6 | 防止短路径失控 |
| `max_steps`（异步） | 12～20 | 仍要有顶 |
| 舱壁（bulkhead） | 按依赖限并发 | 向量慢时不要拖死全部 API |

伪代码：工具级熔断 + 超时心智：

```python
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ToolBreaker:
    fail_threshold: int = 3
    cooldown_s: float = 30.0
    fails: int = 0
    open_until: float = 0.0

    def allow(self) -> bool:
        return time.monotonic() >= self.open_until

    def record(self, ok: bool) -> None:
        if ok:
            self.fails = 0
            return
        self.fails += 1
        if self.fails >= self.fail_threshold:
            self.open_until = time.monotonic() + self.cooldown_s
            self.fails = 0


@dataclass
class DegenerateReply:
    level: int
    user_message: str
    run_id: str


def degrade_rag_empty(run_id: str) -> DegenerateReply:
    return DegenerateReply(
        level=3,
        user_message="资料库中未找到足够依据，无法给出可靠结论。",
        run_id=run_id,
    )


def degrade_total_failure(run_id: str) -> DegenerateReply:
    return DegenerateReply(
        level=4,
        user_message=f"服务暂时不可用。请稍后重试，或携带编号 {run_id} 联系支持。",
        run_id=run_id,
    )
```

### 3.4 跑一下（降级剧本桌面推演）

用表格走五条剧本（练习 D 同源）：

```text
剧本 A：search 工具 500
  → L1：tool 结果 ok=false → 模型改用 lookup_doc 或诚实说查不到

剧本 B：主模型 429
  → L2：退避 → 备用小模型 → 仍失败则 L4

剧本 C：向量库返回 0 hits
  → L3：无资料话术；禁止编造条款号

剧本 D：Runtime 触达 max_steps 仍无最终答
  → L4：友好收束 + run_id；指标 agent_max_steps_total++

剧本 E：LLM 厂商全面故障
  → L5：/readyz 失败或维护页；拒绝新 Job；只读 FAQ 静态页可选
```

最小可执行断言（离线）：

```python
b = ToolBreaker(fail_threshold=2, cooldown_s=60)
assert b.allow()
b.record(False)
b.record(False)
assert b.allow() is False  # 熔断打开
print("breaker OK")

r = degrade_rag_empty("run-9")
assert r.level == 3
assert "未找到" in r.user_message
```

### 3.5 易错点

| 错法 | 会发生什么 |
|------|------------|
| RAG 空仍让模型「自由答」 | 幻觉被当成有依据 |
| 429 无限重试 | 把自己打成 DDoS，账单双杀 |
| 降级只记日志不改用户文案 | 用户只看到转圈或 500 |
| 熔断后永不半开探测 | 依赖已恢复仍全拒绝 |
| L5 时仍接受昂贵 Job | 队列堆积，恢复后雪崩 |
| 错误里回传堆栈 / 内部 prompt | 安全与脱敏违规 |

### 3.6 对照：降级归属

| 层级 | 主要归属 | 观测信号 |
|------|----------|----------|
| L1 工具 | Runtime + Tool ACL | `tool_error_rate` |
| L2 LLM | LLM Adapter | `llm_429` / `llm_failover` |
| L3 RAG | RAG 用例 | `rag_empty_rate` |
| L4 全链路 | Application | `run_failed` |
| L5 大盘 | 平台 / SRE | `/readyz`、依赖探针 |

---

## 4. 必掌握：成本控制

Agent 系统的默认趋势是：**越用越贵，且不一定更好**。成本必须是一等设计约束。

### 4.1 为什么成本要进架构图？

因为每一跳都在烧钱与额度：

```text
路由分类 → 主模型 → 工具结果回灌 → 再推理 → RAG 大上下文 → …
```

没有预算与配额时，一次「友好的多 Agent 辩论」就能打穿月预算。

### 4.2 怎么设计（杠杆清单）

| 杠杆 | 做法 | 风险 / 注意 |
|------|------|-------------|
| **小模型路由** | 意图分类 / 是否需要工具用小模型 | 路由错 → 答非所问；要评测路由准确率 |
| **缓存** | 重复问题、相同检索 query | 时效与权限；缓存键必须含租户/ACL |
| **截断上下文** | 滑动窗口、工具结果摘要后再回灌 | 摘要丢关键约束 → 幻觉 |
| **`max_steps` / `max_tokens`** | 同步/异步分别设顶 | 顶太低损害任务成功率 |
| **工具结果摘要** | 长页面先 summary 再进 messages | 摘要模型本身也有成本 |
| **租户配额** | 日/月 token、并发 Job | 内部用户也会误用 |
| **预算告警** | 按模型 / 按租户烧到阈值页 | 只告警不限流仍会爆 |
| **评测护栏** | 成功率↑ 且成本不恶化才发版 | 防「更贵没更好」 |

### 4.3 怎么写（路由 + 硬顶伪代码）

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ModelKind = Literal["small", "large"]


@dataclass
class Budget:
    max_steps: int
    max_output_tokens: int
    daily_tokens_remaining: int


def pick_model(intent: str, complexity: str) -> ModelKind:
    """小模型做分流；难题再上大模型。"""
    if intent in {"chitchat", "classify", "route"}:
        return "small"
    if complexity == "hard":
        return "large"
    return "small"


def allow_spend(budget: Budget, estimated_tokens: int) -> bool:
    return estimated_tokens <= budget.daily_tokens_remaining


def clip_tool_result(text: str, max_chars: int = 2000) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + "\n...[truncated]..."
```

与评测章对齐的发版门禁心智：

```text
发版比较 baseline：
  ✅ task_success 不下降（或可解释的取舍）
  ✅ avg_tokens / avg_steps 不明显变差
  ❌ 「换更大模型，成功率持平但成本 +80%」→ 默认拒绝
```

### 4.4 跑一下（成本护栏离线断言）

```python
assert pick_model("classify", "easy") == "small"
assert pick_model("research", "hard") == "large"

b = Budget(max_steps=6, max_output_tokens=512, daily_tokens_remaining=1000)
assert allow_spend(b, 200) is True
assert allow_spend(b, 5000) is False

long = "x" * 5000
assert clip_tool_result(long, 100).endswith("[truncated]...")
print("cost guards OK")
```

### 4.5 易错点

| 错法 | 会发生什么 |
|------|------------|
| 只看成功率不看 tokens/steps | 静默变成土豪系统 |
| 缓存不带租户 / ACL | 串数据（安全事故） |
| 全链路永远最大模型 | 账单先于产品验证死亡 |
| 截断切掉系统安全约束 | 注入与越权风险上升 |
| 配额只做「提示」不做强制 | 等于没有配额 |
| 多 Agent 默认开辩论 | 费用与延迟倍增（模块 11 克制） |

### 4.6 对照：成本杠杆落点

配额拒绝 → 接入/应用；`max_steps` / 路由 → Runtime；缓存 / top_k → 数据与检索；「更贵没更好」门禁 → 评测发版。

---

## 5. 建议掌握：平台化演进

不要第一天就建「内部 Agent 平台」。要会讲**路线**，并知道每一步买到什么。

### 5.1 为什么要分阶段？

过早平台化的典型症状：

- 还没有稳定 Runtime 契约，就做「工具市场」  
- 还没有评测与观测，就做多租户计费  
- 三个业务三套 prompt 管理 UI，却共用混乱权限  

分阶段让组织能力与架构复杂度同速增长。

### 5.2 怎么规划（四段路线）

```text
阶段 A：单应用 Agent（模块化单体）
  - 一个 FastAPI +（可选）同仓 Worker
  - FakeLLM 单测 / CI 绿
  - 最小评测集 + trace_id
  - 目标：一个业务真的有人用

阶段 B：多业务复用同一 Runtime
  - Domain 端口稳定（LLM / Tool / Memory / Job）
  - 多套 Agent 配置（提示、工具 ACL、max_steps）
  - 共享观测字段与评测 harness
  - 目标：第二个业务「接配置」而不是「复制仓库」

阶段 C：工具市场 / 统一鉴权 / 统一观测
  - 工具注册、版本、ACL 模板
  - 统一身份与审计
  - 统一 dashboards（延迟、429、成本、空检索）
  - 目标：工具与安全策略可治理

阶段 D：内部 Agent 平台
  - 自助创建 Bot / 配额 / 管理面
  - 多租户隔离（见 §6）
  - 目标：平台团队 vs 业务团队分工清晰
```

口令（呼应架构章）：

> **先模块，后进程；先同仓 Worker，后微服务；先复用 Runtime，后平台 UI。**

### 5.3 怎么写（3 个月演进表示例）

| 时间 | 里程碑 | 可验证信号 |
|------|--------|------------|
| 月 1 MVP | 同步短路径 + FakeLLM CI + 基础 ACL | harness 绿；同步 SLA 有数 |
| 月 2 可运维 | 异步 Job + 观测三件套 + 降级 L1～L4 | 故障可按 `run_id` 复盘 |
| 月 3 雏形平台 | 第二业务复用 Runtime + 工具注册表 + 成本配额 | 第二业务不复制仓库 |

### 5.4 跑一下（演进自检问题）

连续问：第二业务是改配置还是复制代码？Worker 与 API 是否同一 Runtime？换供应商是否只动 Adapter？评测是否拦过「更贵没更好」？新工具是否过 ACL？——任一「否」却在谈平台 → 先退回阶段 B。

### 5.5 易错点

| 错法 | 会发生什么 |
|------|------------|
| 阶段 A 未稳就上多租户 | 隔离漏洞 + 产品复杂度爆炸 |
| 平台 UI 先于 Runtime 契约 | 界面漂亮、内核分叉 |
| 为「平台」拆 8 个微服务 | 团队被编排与部署拖死 |
| 工具市场无版本与 ACL | 任意业务可调用危险工具 |

### 5.6 对照：单体 → 平台，你真正复用的是什么？

| 复用物 | 价值 |
|--------|------|
| Runtime + 终止护栏 | 行为一致、评测可共享 |
| LLM/Tool 端口 | 可测、可换供应商 |
| 观测字段字典 | 排障话术统一 |
| 评测 harness | 发版标准统一 |
| 鉴权与 ACL 模板 | 安全基线统一 |

---

## 6. 了解即可：多租户地图

企业阶段才深挖；本章只要你知道**有哪些隔离面**，避免「一个 DB 前缀就算多租户」。

### 6.1 为什么是「地图」而不是「本周作业」？

多租户同时碰到：数据隔离、密钥、配额、工具策略、计费、管理面、合规审计。  
任一正面没设计，都会在第二个客户接入时爆雷。

### 6.2 怎么看地图（检查维度）

```text
租户 Tenant
  ├── 身份与成员（谁属于该租户）
  ├── 数据隔离（DB 行级 / schema / 实例；向量过滤强制租户条件）
  ├── 密钥与模型凭证（按租户或平台代持）
  ├── 配额与计费（token、Job 并发、存储）
  ├── 工具策略（允许列表、审批流）
  ├── 提示与配置（Bot 级配置隔离）
  ├── 观测与审计（按租户检索，防串视）
  └── 管理面（创建租户、轮换密钥、停用）
```

安全底线（与安全章一致）：

> **检索过滤、工具 ACL、日志脱敏——必须在服务端强制；不可信客户端传「我是租户 A」。**

### 6.3 对照：什么时候才值得上多租户？

| 信号 | 建议 |
|------|------|
| 仍只有一个内部业务 | 逻辑隔离（`tenant_id` 字段）即可，别上复杂计费 |
| 多个部门要硬隔离密钥与数据 | 认真做租户边界 |
| 要对外售卖 | 管理面 + 配额 + 审计必须进路线图 |
| 还不会做单租户评测/观测 | **先别上多租户** |

---

## 7. 建议掌握：把设计写成「可评审」文档

练习的本质是：**让没写过代码的评审者也能挑洞。**

### 7.1 为什么要有决策表，而不是只贴架构图？

图说明「有什么」；决策表说明「为什么选这个、放弃了什么、风险谁扛」。

模板：

| 决策点 | 选择 | 理由 | 风险 / 缓解 |
|--------|------|------|-------------|
| 长任务 | 队列 Job | P99 超 SLA；要重试 | 队列堆积 → 限流与 L5 |
| 同步超时 | 12s | 网关默认 15s 留余量 | 过短误杀 → 引导异步 |
| 鉴权 | API Key + 作用域 | 内部服务简单 | Key 泄漏 → 轮换与脱敏 |
| RAG 空 | L3 明确无资料 | 防幻觉 | 召回差 → 监控 empty_rate |
| 成本 | 小模型路由 + 日配额 | 控制账单 | 路由错 → 路由评测集 |
| 评测 | FakeLLM CI + 真模抽检 | 离线可绿 | Fake 盲区 → 小流量金标 |
| 日志 | 字段允许列表 | 合规 | 排障信息变少 → 受控 debug 通道 |

### 7.2 怎么写（场景假设最小字段）

```text
场景：带工具的内部客服辅助 Agent
用户：客服坐席（内部）
SLA：同步问答 P95 < 8s；复杂查单允许异步 2min
量级：约 5 万次/日（粗估）
允许异步：是（复杂工单）
数据：订单只读工具；禁止 shell / 任意 HTTP
成功标准：工单字段正确率；禁止编造订单状态
```

### 7.3 跑一下（用清单「扮演评审」）

拿 §8 清单问「证据在哪」：超时是否有数字、降级是否有 L1～L5 话术、成本是否有配额与评测门禁——口头保证一律退回补表。

### 7.4 易错点

| 错法 | 会发生什么 |
|------|------------|
| 决策表写「按需优化」 | 评审无法追责 |
| 架构图与决策表矛盾 | 实现时各做各的 |
| 只写开心路径 | 失败剧本空洞 |
| 抄本章参考图不改场景 | 数字与 SLA 对不上业务 |

---

## 8. 可评审设计检查清单（必掌握）

本章核心产出。复制到设计文档开头，评审逐项打勾。

### 8.1 总清单

#### 接入与安全

- [ ] 认证授权方式明确（API Key / JWT / SSO），作用域清楚  
- [ ] 工具 ACL：默认拒绝；危险工具单独审批  
- [ ] 提示注入与不可信工具结果边界有说明（安全章）  
- [ ] 密钥不进仓库；日志字段允许列表 + 脱敏  
- [ ] 多租户/多业务时，服务端强制隔离条件（若适用）  

#### 同步 / 异步

- [ ] 同步短路径与异步 Job 边界有表、有例子  
- [ ] 明确 **未** 用 `BackgroundTasks` 扛长任务  
- [ ] Job 状态模型（queued/running/succeeded/failed）与查询 API  
- [ ] Worker 与 API **复用**同一 Runtime / Domain  
- [ ] 同步路径有 `max_steps` / 超时硬顶  

#### 可靠性与降级

- [ ] 降级层级 1～5 有对应用户话术与归属  
- [ ] 熔断 / 超时 / 重试默认值已写入决策表  
- [ ] 幂等：入队与工具副作用策略已说明  
- [ ] RAG 空命中不编造；权限不因空结果而放宽  
- [ ] 人工兜底 / 工单入口（若产品需要）  

#### 观测与评测

- [ ] `trace_id` / `run_id` 从接入贯穿 Worker / LLM / Tool  
- [ ] 关键指标：成功率、延迟、429、工具失败、空检索、tokens  
- [ ] 离线评测集 + harness；CI 在 FakeLLM 下可绿  
- [ ] 发版对比 baseline：防「更贵没更好」  
- [ ] 轨迹可回答：调了哪些工具、是否超步  

#### 成本与演进

- [ ] 模型路由 / 缓存 / 截断 / 配额策略至少各有一项  
- [ ] 预算告警接收人明确  
- [ ] 平台化阶段与「现在不做什么」写清楚  
- [ ] 3 个月演进与验证信号可检查  

### 8.2 怎么用（评审 30 分钟议程）

```text
0～5 分   场景与 SLA
5～12 分  架构图：指着箭头讲同步/异步
12～20 分 失败剧本走两条（工具挂、RAG 空）
20～26 分 成本与评测门禁
26～30 分 检查清单残留项 → 记到行动项
```

### 8.3 对照：清单项 ↔ 课程章节

| 清单主题 | 回看 |
|----------|------|
| FastAPI 接入 / Auth | 模块 06 |
| 队列 / Job | 模块 07、架构章 Worker |
| Runtime / max_steps | 模块 11 |
| RAG 空降级 | 模块 10 |
| 评测 harness | 12-01 |
| trace 与脱敏 | 12-02 |
| ACL / 注入 | 12-03 |
| 总图与清单 | 本章 |

---

## 9. 把最小「同步 + 异步」边界示例拼起来

下面示例强调**边界**，不是完整生产服务。可离线用 FakeLLM 跑同步枝；异步枝用内存队列模拟。

### 9.1 为什么要有一个「可跑的骨架」？

纯 ASCII 图容易飘。一段能跑的边界代码应证明：短路径不进队列、长路径只返回 `job_id`、Worker 调同一 `runtime_run`。

### 9.2 怎么写

```python
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from typing import Any


class FakeLLM:
    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        content = messages[-1].get("content", "")
        return {"role": "assistant", "content": f"ok:{content}", "tool_calls": []}


@dataclass
class MemJobs:
    q: deque[dict[str, Any]] = field(default_factory=deque)
    store: dict[str, dict[str, Any]] = field(default_factory=dict)
    _n: int = 0

    async def enqueue(self, payload: dict[str, Any]) -> str:
        self._n += 1
        job_id = f"job-{self._n}"
        self.store[job_id] = {"status": "queued", "payload": payload, "result": None}
        self.q.append(job_id)
        return job_id

    async def reserve(self) -> str | None:
        if not self.q:
            return None
        job_id = self.q.popleft()
        self.store[job_id]["status"] = "running"
        return job_id

    async def complete(self, job_id: str, result: dict[str, Any]) -> None:
        self.store[job_id]["status"] = "succeeded"
        self.store[job_id]["result"] = result


async def runtime_run(llm: FakeLLM, message: str, *, max_steps: int) -> dict[str, Any]:
    # 教学：忽略真实 tool-loop；只证明调用点统一
    _ = max_steps
    msg = await llm.complete([{"role": "user", "content": message}])
    return {"answer": msg["content"], "run_id": "r-1"}


async def api_ask(llm: FakeLLM, message: str) -> dict[str, Any]:
    out = await runtime_run(llm, message, max_steps=4)
    return {"path": "sync", **out}


async def api_create_job(jobs: MemJobs, message: str) -> dict[str, Any]:
    job_id = await jobs.enqueue({"message": message})
    return {"path": "async_job", "job_id": job_id, "status": "queued"}


async def worker_once(jobs: MemJobs, llm: FakeLLM) -> None:
    job_id = await jobs.reserve()
    if job_id is None:
        return
    payload = jobs.store[job_id]["payload"]
    result = await runtime_run(llm, payload["message"], max_steps=16)
    await jobs.complete(job_id, result)


async def main() -> None:
    llm = FakeLLM()
    jobs = MemJobs()

    sync = await api_ask(llm, "短问")
    assert sync["path"] == "sync"

    created = await api_create_job(jobs, "长任务")
    await worker_once(jobs, llm)
    assert jobs.store[created["job_id"]]["status"] == "succeeded"
    print("sync+async boundary OK", sync["answer"], created["job_id"])


asyncio.run(main())
```

### 9.3 易错点

- 把 `MemJobs` 当成生产队列——它只演示形状；可靠投递见模块 07 与 CONVENTIONS。  
- 在 `api_create_job` 里直接 `await runtime_run`——异步边界名存实亡。  
- Worker 另写一套 prompt——双源真相。

---

## 10. 练习指引

按 [`exercises/12-agent-production/04-system-design.md`](../../exercises/12-agent-production/04-system-design.md) 完成：

| 题 | 对照本章 |
|----|----------|
| A 场景假设 | §0、§7.2 |
| B 架构图 | §1 |
| C 关键决策表 | §2、§3、§4、§7.1 |
| D 失败剧本 | §3.4 |
| E 演进路线 | §5 |

建议顺序：A（场景）→ B（总图）→ C（决策数字）→ D（降级剧本）→ §8 清单自审 → E（路线）。  

**先自己写完整页设计，再对照本文；本章以文档产出验收，不必先写全量代码。**

落地目录提示（练习约定）：

```text
playground/12-agent-production/system-design/architecture.md
```

---

## 11. 小结与自检

### 自检

- [ ] 能画出 Client→API→同步短路径 / 异步 Job→Worker→Runtime/LLM/Tools/RAG/DB，并标出 Observability / Evaluation 外挂  
- [ ] 能说明同步 vs 异步的判据，以及 `BackgroundTasks` 为何不能扛长任务  
- [ ] 能口述降级层级 1～5，并给出至少一组超时/熔断默认值  
- [ ] 能列出 ≥4 条成本杠杆，并说明评测如何防「更贵没更好」  
- [ ] 能描述单体 → 复用 Runtime → 工具市场 → 内部平台的演进  
- [ ] 能用 §8 清单主持一次 30 分钟设计评审  

### 模块 12 收官对照

| 章 | 你应带走的能力 |
|----|----------------|
| 01 评测 | harness、回归、轨迹断言 |
| 02 观测 | 三支柱、`trace_id`、脱敏 |
| 03 安全 | 注入、ACL、密钥与日志 |
| 04 系统设计（本章） | 边界、降级、成本、可评审文档 |

---

## 12. 课程收官寄语

你已从 Python 语法与工程基础，走过 Web、数据、架构、RAG、Agent Runtime，来到生产向的评测、观测、安全与系统设计。

请把最终能力记成这句话：

> **Programming + Backend + System + AI Engineering**

而不是绑定某个框架的 API 熟练度。

| 能力柱 | 含义 | 课程中的锚点 |
|--------|------|--------------|
| **Programming** | 抽象、测试、可读演进 | 模块 01～03、手写 Agent |
| **Backend** | HTTP、鉴权、数据、队列 | 模块 06～07 |
| **System** | 边界、降级、观测、演进 | 模块 08、本章 |
| **AI Engineering** | RAG、工具环、评测、成本与安全 | 模块 10～12 |

框架会换代，模型会改名；**端口、护栏、评测与降级**不会过期。

### 下一步建议

1. 完成 Project 5 / 6（带工具与研究链路的真实场景）  
2. 做一个**小**服务：同步短路径 +（可选）Job，挂上评测 harness 与 `trace_id`  
3. 持续维护：回归集、威胁清单、成本看板、设计检查清单  
4. 复利习惯：每次改 prompt / 模型 / 工具，先看评测与 tokens，再谈感觉  

当你能在白板上讲清「同步边界、降级第几层、钱从哪省、评测如何门禁」时——你已经具备把 Agent 带进生产讨论的资格。其余是迭代，不是从零开始。

---

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Agent Security](./03-security.md)
- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Agent 核心开发](../11-agent-core/README.md)
- 项目线：[../projects/README.md](../projects/README.md)
- 课程约定：[../CONVENTIONS.md](../CONVENTIONS.md)
