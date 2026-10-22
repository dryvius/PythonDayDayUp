# 练习：消息队列基础

> 对应文档：[`docs/07-data-persistence/05-message-queue.md`](../../docs/07-data-persistence/05-message-queue.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 可用内存 `queue.Queue` 模拟 broker；不必上真 Rabbit/SQS。
4. 建议目录：

```text
playground/07-data-persistence/05-message-queue/
  job_queue_demo.py
  job_api_sketch.md
  notes.md
```

5. Python ≥ 3.11。
6. **两处硬边界（写进笔记）**——见 `docs/CONVENTIONS.md`：
   - FastAPI `BackgroundTasks` **≠** 长任务方案；分钟级 Agent 请上队列 + worker
   - Redis `LIST`+`BRPOP` 演示 **≠** at-least-once（若你用它模拟 MQ，必须注明）

---

## 热身题（建议先做）

### W1. 为什么要排队？

**要求**：一句话说明同步 HTTP 里跑 3 分钟任务的核心矛盾。

**验收**：超时/占连接/失败难重试等至少点到一个。

---

### W2. 三角色

**要求**：默写 Producer / Broker / Consumer 各一句话。

**验收**：三者职责不混。

---

### W3. BackgroundTasks 边界

**要求**：抄写：

> `BackgroundTasks` 适合轻量收尾；长任务请上队列。

并各举 1 例「适合 / 不适合」。

**验收**：适合例像写日志；不适合例像多步 Agent。

---

### W4. 幂等一词

**要求**：用一句话解释「消费者幂等」。

**验收**：同一消息处理多次，业务效果与一次相同（或可安全去重）。

---

## 基础题（必做）

### B1. 同步痛点（书面）

列出同步跑 **3 分钟** Agent 的 **4 个问题**（网关超时、用户体验、扩缩容、失败重试、占用 worker 等任选）。

**验收**：恰好至少 4 条，互不重复。

---

### B2. 角色图

画出 Producer / Broker / Consumer，并标注：

- FastAPI 进程通常是谁  
- worker 进程通常是谁  

**验收**：图上能看出「API 快速入队，worker 慢慢跑」。

---

### B3. 至少一次与幂等

解释：为什么消费者要幂等？  

举一个 Agent 工具例子：重复执行会导致「重复扣费 / 重复发邮件 / 重复建单」——并给出对策（幂等键、去重表、上游唯一约束等任选）。

**验收**：问题 + 对策都有；不要只写「别重复投递」。

---

### B4. Job 状态机

定义状态集合（至少含：`queued` / `running` / `succeeded` / `failed`），并列出**允许的迁移**。

特别声明：不可从 `succeeded → queued`（除非你明确做「重跑」且用新状态机，需另写）。

**验收**：用列表或图表示；非法迁移写清楚。

---

## 进阶题（建议至少做 1 题）

### A1. 内存队列 demo

实现：

1. API 线程（或主线程）`put` job  
2. worker 线程 `get` 并处理（`sleep` 模拟）  
3. 主程序打印 job 状态变化：`queued → running → succeeded`

**验收**：可运行脚本；状态变化可见。

---

### A2. Job API 草图

写清 JSON 示例：

1. `POST /v1/jobs` 请求与 202 响应（含 `job_id`）  
2. `GET /v1/jobs/{id}` 响应（含 `status`）  

**验收**：字段自洽；POST 不阻塞等 3 分钟结果。

---

## 挑战题（可选）

### C1. BackgroundTasks vs Queue（书面）

对比适用边界，**至少各 3 条**。

**验收**：明确长任务归队列；BackgroundTasks 不提供跨进程持久化与可靠重试。

---

### C2. 失败重试策略草图

为 `failed` 任务设计：最大重试次数、退避、进入 dead-letter 的条件。书面即可。

**验收**：有上限，避免无限重试打爆下游。

---

## 模块 07 通关自检

- [ ] 会基础 SQL（CRUD/JOIN/事务/索引直觉）
- [ ] 理解 PG 类型/约束/连接配置
- [ ] 理解 ORM Session 与迁移价值
- [ ] 能设计缓存键与限流计数思路；知道 LIST+BRPOP ≠ at-least-once
- [ ] 能为长任务设计队列化方案；知道 BackgroundTasks ≠ 长任务

完成后进入模块 08《部署、运维与软件架构》。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1～W4 参考答案

- W1：HTTP 请求/网关有超时，长任务会占满 worker 且难重试。  
- W2：Producer 生产消息；Broker 存管用；Consumer 拉取处理。  
- W3：适合——响应后追加审计日志；不适合——同步 tool-loop 跑 LLM 三分钟。  
- W4：重复投递不导致重复副作用。

---

### B1 思路 + 参考答案

1. 反向代理/负载均衡先超时，客户端看到 502/504  
2. 用户刷新导致重复提交  
3. Web 进程被长任务占满，健康检查与其它 API 一起抖  
4. 中途失败难以从断点自动重试；扩缩容也不好只加 API 副本  

---

### B2 思路 + 参考答案

```text
[Client]
   | POST /v1/jobs
   v
[FastAPI = Producer] --enqueue--> [Broker: Queue/Redis/RQ...]
                                      |
                                      v
                               [Worker = Consumer]
                                      |
                                      v
                                 LLM / Tools
```

API：快速校验 + 入队 + 返回 `job_id`。  
Worker：执行 Agent。  

---

### B3 思路 + 参考答案

**为什么要幂等**：at-least-once 下，超时重投、worker 崩溃重启都可能导致同一逻辑消息被处理多次。

**例子**：工具 `charge_user(invoice_id)` 或 `send_email(campaign_id, user_id)`。  

**对策**：

- 传入幂等键 `Idempotency-Key` / `invoice_id`  
- DB 唯一约束：同一 `invoice_id` 只能成功扣费一次  
- 处理前查去重表，已成功则直接返回上次结果  

---

### B4 思路 + 参考答案

状态：`queued` / `running` / `succeeded` / `failed`（可选 `canceled`）。

允许迁移：

```text
queued    → running
running   → succeeded
running   → failed
queued    → canceled   (可选)
running   → canceled   (可选，需协作取消)
failed    → queued     (仅显式重试时；或用新状态 retried 更清晰)
```

非法：

```text
succeeded → queued     (禁止「悄悄改成功为排队」)
succeeded → failed
```

---

### A1 思路 + 参考答案

```python
from __future__ import annotations

import queue
import threading
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    payload: str
    status: str = "queued"
    result: str | None = None


JOBS: dict[str, Job] = {}
BROKER: queue.Queue[str] = queue.Queue()


def enqueue(payload: str) -> Job:
    job = Job(id=str(uuid.uuid4()), payload=payload, status="queued")
    JOBS[job.id] = job
    BROKER.put(job.id)
    print(f"{job.id} -> queued")
    return job


def worker_loop(stop_after: int) -> None:
    processed = 0
    while processed < stop_after:
        job_id = BROKER.get()
        job = JOBS[job_id]
        job.status = "running"
        print(f"{job.id} -> running")
        time.sleep(0.2)  # 模拟长任务片段
        job.result = f"done:{job.payload}"
        job.status = "succeeded"
        print(f"{job.id} -> succeeded")
        BROKER.task_done()
        processed += 1


if __name__ == "__main__":
    worker = threading.Thread(target=worker_loop, kwargs={"stop_after": 2}, daemon=True)
    worker.start()
    j1 = enqueue("alpha")
    j2 = enqueue("beta")
    BROKER.join()
    worker.join(timeout=2)
    assert JOBS[j1.id].status == "succeeded"
    assert JOBS[j2.id].status == "succeeded"
    print("a1 ok")
```

说明：此内存队列演示「异步化」；进程退出即丢，**不是**生产级 at-least-once。

---

### A2 思路 + 参考答案

```http
POST /v1/jobs
Content-Type: application/json

{"query": "summarize ticket 9", "max_steps": 5}
```

```json
{
  "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "queued"
}
```

（HTTP 202 Accepted）

```http
GET /v1/jobs/7c9e6679-7425-40de-944b-e07fc1f90ae7
```

```json
{
  "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "running",
  "result": null
}
```

成功后：

```json
{
  "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "succeeded",
  "result": {"answer": "...", "steps": 3}
}
```

---

### C1 思路 + 参考答案

**BackgroundTasks**：

1. 同进程、响应后执行  
2. 适合发短日志、清临时文件  
3. 无独立扩缩容；进程挂了任务一起没  

**Queue + Worker**：

1. 跨进程/跨机器  
2. 适合分钟级 Agent、可重试  
3. 可独立扩 worker；可落库状态  

边界：长任务、需可靠重试、需观测进度 → 队列；轻量收尾 → BackgroundTasks。

---

### C2 思路 + 参考答案

- `max_retries = 3`  
- 退避：`2^n` 秒（带抖动）  
- 超过次数或遇到不可重试错误（如 400 校验失败）→ `dead_letter`  
- 可重试错误：超时、429、5xx  
- dead-letter 需告警人工介入，避免沉默丢业务  

---

## 附录：三种「后台」对照（务必分清）

| 方案 | 同进程？ | 持久化 | 适合 |
|------|----------|--------|------|
| FastAPI `BackgroundTasks` | 是 | 否（随进程） | 轻量收尾：一行日志、清临时文件 |
| Redis `LIST`+`BRPOP` | 否（可跨进程） | 取决于 Redis 配置 | **演示**入队出队；**≠ at-least-once** |
| 正经队列 + worker（RQ/Celery/云队列等） | 否 | 通常有 | 分钟级 Agent、重试、独立扩缩 |

错误示范心智：

```text
POST /v1/agent/run
  → BackgroundTasks.add_task(run_agent_for_3_minutes)  # 不要这样当架构
```

正确方向：

```text
POST /v1/jobs  → 202 + job_id
worker        → 拉取 → 执行 → 更新状态
GET /v1/jobs/{id}
```

---

## 附录：幂等键示例（书面可粘贴）

```json
{
  "job_id": "…",
  "idempotency_key": "invoice:inv_123:charge",
  "tool": "charge_user",
  "args": {"invoice_id": "inv_123", "amount_cents": 990}
}
```

处理逻辑伪代码：

```python
def handle_charge(job: dict) -> dict:
    key = job["idempotency_key"]
    existing = db.find_result(key)
    if existing is not None:
        return existing  # 重复投递：直接返回上次结果
    result = payment_provider.charge(...)
    db.save_result(key, result)  # 唯一约束兜底
    return result
```

**自检**：

- [ ] 能画 Producer/Broker/Consumer  
- [ ] 能解释为何要幂等  
- [ ] 能对比 BackgroundTasks vs Queue


---

## 附录：Job 字段最小集（可当设计草稿）

```json
{
  "job_id": "uuid",
  "type": "agent_run",
  "status": "queued",
  "payload": {"query": "...", "max_steps": 5},
  "idempotency_key": "optional",
  "attempts": 0,
  "max_attempts": 3,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "error": null,
  "result": null
}
```

状态迁移测试用例（书面即可）：

1. queued → running → succeeded
2. queued → running → failed → queued（显式重试）
3. succeeded 后再次收到同一消息 → 幂等返回旧 result
4. attempts 耗尽 → dead_letter + 告警

**口头题**：为什么 API 要快速返回 202，而不是同步等 Agent 跑完？

### 再强调一次边界

- BackgroundTasks：轻量收尾
- LIST+BRPOP：演示 ≠ at-least-once
- Queue+Worker：长任务正道
