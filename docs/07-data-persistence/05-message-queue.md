# 消息队列基础

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（建议先完成 FastAPI 章的 BackgroundTasks 小节，再对照本章）  
> 对应练习：[`exercises/07-data-persistence/05-message-queue.md`](../../exercises/07-data-persistence/05-message-queue.md)

## 本章定位

- **模块目标**：掌握 SQL/ORM/缓存/队列的工程用法与取舍。
- **本章角色**：理解为何需要队列；生产者/消费者；至少一次投递；Agent 长任务如何异步化。
- **不是**：深挖 Kafka 内核、ZooKeeper、分区再均衡细节；先建立正确架构直觉，能画图、能选型、能避开常见坑。
- **和 Agent**：多步工具调用、长 LLM 链、批量索引、定时评测——这些往往超过 HTTP 请求的合理时长，必须「入队 + 查状态」。

## 学习目标

1. 能判断「该同步返回」还是「丢队列后台跑」。
2. 描述生产者、消费者、broker 角色，并标出 FastAPI 与 worker 各是谁。
3. 理解至少一次投递与幂等消费，能举一个重复执行的反例与对策。
4. 能设计 Agent 长任务状态机草图与 `POST/GET /jobs` API。
5. 说清 FastAPI `BackgroundTasks` 与真队列的边界（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 为何需要队列、生产/消费、至少一次投递与幂等 | 能画架构、能讲清丢消息/重复的风险 |
| **建议掌握** | Agent 长任务场景、状态机与 Job API | 能设计 job API 与 worker 职责 |
| **了解即可** | Kafka/RabbitMQ/云队列对比 | 地图；知道先选团队会运维的 |

---

## 1. 必掌握：为什么需要队列

这一节会刻意写细——后面所有「ack / 幂等 / 状态机」都建立在「先认清同步 API 扛不住长任务」之上。

### 1.1 同步跑长任务会发生什么

#### 为什么这一步必须先想清楚？

很多人第一次接 Agent API 会这样写：

```text
POST /v1/agent/run
  → 在同一个请求里跑完：拼 prompt → 调 LLM → 工具 → 再调 LLM …
  → 最后把完整答案 JSON 返回
```

当任务只要几百毫秒，这样最简单。一旦变成 **3 分钟**（多轮工具、检索、长上下文），同步路径会同时踩中多个坑：

```text
网关超时 / 用户刷新 / 连接断开 / 占满 worker
```

逐条展开：

| 现象 | 发生了什么 | 用户/系统感受 |
|------|------------|----------------|
| 网关超时 | Nginx / 云 LB / API Gateway 常有 60s～120s 上限 | 客户端收到 502/504，任务其实可能还在跑或已半死 |
| 用户刷新 | 浏览器重发请求，或前端取消后重试 | 同一任务跑两份，账单与副作用翻倍 |
| 连接断开 | 手机切网、笔记本休眠、反向代理掐连接 | 服务端还在算，客户端已当失败 |
| 占满 worker | Uvicorn/Gunicorn worker 被长请求占住 | 健康检查变慢，短请求也被拖死 |

#### 先自己想

若你只有一台机器、两个 worker，同时来 3 个「各跑 3 分钟」的 Agent 请求——短请求（健康检查、查会话）还能不能及时响应？

#### 对照（想完再看）

多数情况下：**不能稳定响应**。长请求占满并发槽位后，短请求只能排队；再叠加超时与重试，系统会进入「越重试越堵」的恶性循环。

### 1.2 队列化之后长什么样

#### 为什么要改成「先入队、马上返回」？

HTTP 请求的职责应收缩为：

1. 校验输入  
2. 创建任务记录（落库）  
3. 把消息丢进 broker  
4. **立刻**返回 `job_id`（常用 HTTP 202）

真正烧时间的工作交给独立的 worker 进程/容器去消费。

#### 怎么写（流程骨架）

```text
客户端
  │
  │ POST /v1/jobs  {payload}
  ▼
API（Producer）
  │ 写 jobs 表：status=queued
  │ 消息入队：{job_id, payload}
  │ 立即返回 {job_id, status:"queued"}
  │
  ▼
Broker（Redis Streams / RabbitMQ / SQS / Kafka …）
  │
  ▼
Worker（Consumer）
  │ 取消息 → status=running → 执行 Agent
  │ 成功 → succeeded + 结果
  │ 失败 → failed / 重试 / 进 DLQ
  │
客户端轮询 GET /v1/jobs/{id} 或等回调/WebSocket
```

口诀：

> **同步路径只负责「接单」；异步路径才负责「干活」。**

#### 跑一下（心智实验，不依赖真实 broker）

用语言走一遍时间线：

```text
T+0s    客户端 POST /v1/jobs
T+50ms  API 返回 {"job_id":"j_01","status":"queued"}   ← 连接已结束
T+200ms worker 取到消息，更新 status=running
T+180s  Agent 跑完，status=succeeded，result 可查
T+181s  客户端 GET /v1/jobs/j_01 拿到结果
```

注意：客户端在 `T+50ms` 就可以去忙别的事；不必挂着一条 HTTP 连线等三分钟。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 入队成功但忘了写 `jobs` 表 | 有消息、无可查询状态；运维两眼一抹黑 |
| 写了表但入队失败且未回滚 | DB 里永远 `queued`，没人消费 |
| 把「返回 job_id」做成同步等跑完 | 又退化成同步长请求 |
| 前端只 `await` 一次 POST，不轮询 | 永远拿不到结果 |

#### 和「同步 API」对照

| 维度 | 同步跑完再返回 | 队列化 |
|------|----------------|--------|
| HTTP 时长 | ≈ 任务时长 | 毫秒级接单 |
| 超时风险 | 高 | 低（查询接口短） |
| 扩展 | 加 API 副本仍扛长任务 | 单独加 worker |
| 复杂度 | 低 | 要状态机、幂等、监控 |

### 1.3 队列的其它收益（不只为长任务）

#### 为什么还要削峰、解耦、重试？

即使任务只有几秒，队列仍常有价值：

| 收益 | 含义 | Agent 例子 |
|------|------|------------|
| **削峰** | 突发流量先进队列，worker 按能力消化 | 活动日突然涌入大批「总结文档」任务 |
| **解耦** | API 不依赖 worker 实现细节 | 换 Celery → ARQ，API 契约可不变 |
| **重试** | 短暂失败自动再投 | LLM 临时 429 / 网络抖动 |
| **多消费者扩展** | 水平加 worker | 夜间批量建索引 |
| **隔离故障** | worker 挂了不影响接单（消息仍在 broker） | 部署滚动时仍可入队 |

#### 易错点

- 以为「上了队列就一定可靠」→ 取决于 ack / 持久化 / 幂等，见第 3 节  
- 为了「架构好看」给 50ms 的小逻辑也上重型 Kafka → 过度设计  
- 削峰只加队列不加容量上限 → 队列无限堆积，最终内存/磁盘爆

#### 先自己想再对照

问自己：这个操作失败了用户能否接受「稍后查结果」？需要重试吗？峰值是否远高于稳态？

- 三者多为「是」→ 倾向队列  
- 必须在同一次请求里拿到强一致结果，且极短 → 可同步

---

## 2. 必掌握：生产者 / 消费者

### 2.1 三个角色

#### 为什么要拆成 Producer / Broker / Consumer？

同步代码里「生产」和「消费」是同一个人：接收请求的进程既接单又干活。拆开之后：

```text
Producer（API） → Broker（Redis Streams / RabbitMQ / SQS / Kafka …）
                         → Consumer（worker）
```

| 角色 | 职责 | 在 Agent 平台里常见是谁 |
|------|------|-------------------------|
| **Producer** | 校验、落库、投递消息 | FastAPI / 网关后的 API 服务 |
| **Broker** | 暂存消息、投递给消费者、（常）负责重投 | Redis / RabbitMQ / SQS / Kafka… |
| **Consumer** | 取出消息、执行业务、ack/nack | 独立 worker 进程或消费组 |

#### 怎么写（角色标注）

练习里常要求你画图并标注——建议直接按下面标：

```text
[浏览器/前端]
      │  HTTP
      ▼
[FastAPI = Producer] ----publish----> [Broker]
                                            │
                                            │ deliver
                                            ▼
                                      [Worker = Consumer]
                                            │
                                            ▼
                                      [PostgreSQL：jobs 状态/结果]
```

FastAPI **不是**消费者（除非你把消费循环错误地塞进 API 进程——不推荐作为生产默认）。

#### 跑一下（内存模拟，感受三角色）

环境受限时，可用标准库 `queue.Queue` 当「玩具 broker」（**仅演示时序，不是生产语义**）：

```python
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue


class Status(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


@dataclass
class Job:
    job_id: str
    payload: dict
    status: Status = Status.queued
    result: str | None = None


JOBS: dict[str, Job] = {}
BROKER: Queue[str] = Queue()  # 只传 job_id


def produce(job_id: str, payload: dict) -> Job:
    job = Job(job_id=job_id, payload=payload)
    JOBS[job_id] = job
    BROKER.put(job_id)  # Producer → Broker
    return job


def consume_once() -> None:
    job_id = BROKER.get()  # Consumer ← Broker
    job = JOBS[job_id]
    job.status = Status.running
    print(f"running {job_id}")
    time.sleep(0.2)  # 假装跑 Agent
    job.result = f"echo:{job.payload.get('prompt')}"
    job.status = Status.succeeded
    BROKER.task_done()
    print(f"succeeded {job_id} -> {job.result}")


if __name__ == "__main__":
    worker = threading.Thread(target=consume_once, daemon=True)
    worker.start()

    j = produce("j_01", {"prompt": "hello"})
    print("accepted", j.job_id, j.status)  # 立即返回 queued
    worker.join()
    print("final", JOBS["j_01"].status, JOBS["j_01"].result)
```

预期输出类似：

```text
accepted j_01 queued
running j_01
succeeded j_01 -> echo:hello
final succeeded echo:hello
```

#### 易错点

| 错法 | 说明 |
|------|------|
| 把完整巨大 payload 塞进消息，DB 不存 | 消息体膨胀；重试/审计困难；优先消息里放 `job_id`，细节查库 |
| API 进程里 `while True: BRPOP` | API 与 worker 生命周期缠在一起，扩缩容困难 |
| 多个消费者抢同一「无 ack」列表 | 语义混乱；见下一小节 LIST 陷阱 |
| 用全局内存 `dict` 当跨机器状态 | 多副本 API 看不到彼此的 job |

#### 对照：同步函数调用 vs 队列

| | 函数调用 | 消息队列 |
|--|----------|----------|
| 耦合 | 调用方必须同时在线 | 可时间解耦 |
| 失败 | 异常立刻抛回 | 可重投、进 DLQ |
| 扩展 | 加线程/进程仍绑在一起 | Producer / Consumer 独立扩 |

### 2.2 Redis LIST 直觉（教学用，不是可靠队列）

#### 为什么先讲 LIST + BRPOP？

因为它最容易建立「入队 / 出队」直觉：一边 `LPUSH`，一边阻塞 `BRPOP`。  
但请记住课程约定（[`CONVENTIONS.md`](../CONVENTIONS.md)）：

> Redis `LIST` + `BRPOP`：演示入队出队，**不是** at-least-once。

#### 怎么写（命令级直觉）

```text
# Producer
LPUSH jobs '{"job_id":"j_01","type":"agent_run"}'

# Consumer（阻塞最多 5 秒）
BRPOP jobs 5
```

`BRPOP` 成功时：元素已经从列表**移除**并返回给客户端。

#### 跑一下（若本机有 Redis）

```bash
# 终端 A：假装 worker
redis-cli BRPOP jobs 0

# 终端 B：假装 API
redis-cli LPUSH jobs '{"job_id":"j_01"}'
```

终端 A 应立刻打印出那条 JSON。

#### 易错点：LIST 的真实语义

| 做法 | 实际语义 | 风险 |
|------|----------|------|
| `LIST` + `BRPOP` | 取出即删除 ≈ **at-most-once** | worker 取出后崩溃 → **丢消息** |
| Streams 消费组 + ACK / RabbitMQ ack 等 | 偏 **at-least-once** | 可能重复投递 → 要幂等 |

崩溃时间线：

```text
1. BRPOP 成功，消息已从 LIST 消失
2. worker 开始跑 Agent
3. 进程被 kill / OOM
4. 消息不在队列里，也没人重新投递 → 任务蒸发
```

#### 对照：学习用 vs 生产用

| 阶段 | 可用方案 | 你要学到什么 |
|------|----------|--------------|
| 学习时序 | `queue.Queue` / Redis LIST | Producer/Consumer 是谁 |
| 生产任务 | Redis Streams(+ACK)、RabbitMQ、SQS、Celery/RQ/ARQ/Dramatiq 等 | **可见性超时 / ack**、重试、监控 |

学习阶段可用 LIST 感受「生产者/消费者」；生产请用带 **ack / 可见性超时** 的机制。

### 2.3 带 ack 的消费长什么样（概念）

#### 为什么需要 ack？

Broker 需要知道：「这条消息是不是已经安全处理完了？」

- **未 ack**：超时后可重新投递给自己或其他消费者  
- **已 ack**：认为处理完成，不再投递  

#### 怎么写（伪代码级，不绑死某一框架）

```text
msg = broker.receive()          # 消息变为「不可见」或「未确认」
try:
    handle(msg)
    broker.ack(msg)             # 成功才确认
except TemporaryError:
    broker.nack(msg) / 等可见性超时  # 稍后重投
except PoisonError:
    broker.ack(msg) + 写入 DLQ  # 避免毒消息无限循环（策略因系统而异）
```

#### 易错点

- 处理成功但忘了 ack → 超时后重复投递（偏至少一次）  
- 一拿到消息就 ack，再处理 → 崩了就丢（退化成至少/至多之间的最差组合）  
- 把「我代码里 try/except 了」当成「broker 会自动 ack」→ 两套机制要分开看  

#### 对照

| | LIST+BRPOP | Streams/Rabbit/SQS 类 |
|--|------------|------------------------|
| 取出后消息还在吗？ | 不在 | 通常仍在，直到 ack/删除 |
| worker 崩溃 | 易丢 | 可再投（于是可能重复） |
| 你要写的防护 | 基本无法恢复 | **幂等** |

---

## 3. 必掌握：至少一次投递与幂等

### 3.1 投递语义地图

#### 为什么不能幻想「正好一次」免费午餐？

多数**可靠**队列保证倾向：

> **At-least-once（至少一次）**：可能重复投递；很少承诺「正好一次（exactly-once）」且无需你做任何事。

三种常见说法：

| 语义 | 含义 | 典型代价 |
|------|------|----------|
| **at-most-once** | 最多一次，可能丢 | 实现简单（如 LIST+BRPOP） |
| **at-least-once** | 至少一次，可能重复 | 要幂等 |
| **exactly-once** | 正好一次 | 昂贵/有前提；常是「至少一次 + 幂等副作用」的效果 |

#### 先自己想

worker 在「业务已成功写库」和「向 broker ack」之间崩溃——broker 会认为没处理完而重投。你的业务会跑第二遍。怎么办？

#### 对照

正确方向不是「禁止重投」（你通常禁止不了），而是：

> **让第二遍执行变得无害或直接短路** → 这就是幂等消费。

### 3.2 消费者为什么必须尽量幂等

#### 为什么？

因为至少一次意味着：

```text
同一 job_id / 同一消息，handle() 可能被调用 2 次、3 次…
```

若 `handle` 里有副作用：

- 扣费 / 发邮件 / 调会写库的工具  
- 向外部 CRM 创建工单  
- 给用户推送「已完成」通知  

重复执行就会变成事故。

#### 怎么写（幂等手段清单）

| 手段 | 做法 | Agent 例子 |
|------|------|------------|
| **业务键去重** | 以 `job_id` 为唯一键；已 `succeeded` 则直接返回 | 重投时发现已完成，跳过 LLM |
| **唯一约束** | DB `UNIQUE(job_id)` / `UNIQUE(idempotency_key)` | 插入结果行冲突即视为已处理 |
| **工具幂等键** | 工具调用带稳定 `idempotency_key` | `charge(user, amount, key=job_id)` |
| **状态机守卫** | 非法迁移直接拒绝 | `succeeded → running` 禁止 |
| **自然幂等** | 操作本身可重复 | `SET` 缓存、写同一对象终态 |

伪代码：

```python
def handle(job_id: str) -> None:
    job = load_job(job_id)
    if job.status in {"succeeded", "canceled"}:
        return  # 短路：重复投递无害

    if not mark_running_if_queued(job_id):
        return  # 别人正在跑或状态不允许

    try:
        result = run_agent(job.payload, idempotency_key=job_id)
        save_success(job_id, result)
    except Exception:
        save_failure_or_retry(job_id)
        raise
```

#### 跑一下（重复投递演练）

在内存 demo 上故意调用两次 `handle`：

```python
def handle_idempotent(job_id: str, jobs: dict[str, Job]) -> str:
    job = jobs[job_id]
    if job.status == Status.succeeded:
        return "skip-duplicate"
    job.status = Status.running
    job.result = "done"
    job.status = Status.succeeded
    return "processed"


jobs = {"j_01": Job(job_id="j_01", payload={})}
print(handle_idempotent("j_01", jobs))  # processed
print(handle_idempotent("j_01", jobs))  # skip-duplicate
```

#### 易错点

| 错法 | 后果 |
|------|------|
| 只在日志里「尽量别重复」 | 重投时仍双扣费 |
| 用随机 UUID 当幂等键 | 每次重试都是新键，等于没有幂等 |
| 幂等键粒度太大 | 不同业务误伤成「同一个」 |
| 幂等键粒度太小 | 同一次业务拆成多个键，仍重复 |
| 只幂等「写结果」，不幂等「调工具」 | DB 看起来成功一次，外部副作用两次 |

#### 对照：至少一次 vs LIST 演示

| | LIST+BRPOP 演示 | 可靠队列 + 幂等 |
|--|-----------------|-----------------|
| 主要风险 | **丢** | **重复** |
| 你的对策 | 基本靠别用它做关键任务 | job_id 去重 / 唯一约束 / 工具幂等键 |
| 课程提醒 | 不要和「至少一次」混为一谈 | 第 2 节对照表 |

上一节的 `BRPOP` 示例**不**提供至少一次；不要把「列表队列」和「至少一次」混为一谈。

### 3.3 失败、重试与死信（DLQ）

#### 为什么需要 DLQ？

有些消息怎么重试都会失败（毒消息）：

- payload 缺字段、无法反序列化  
- 业务上永久非法的输入  
- 下游持续 4xx（不是 429）  

若无限重试，会堵死消费者、刷爆日志与账单。

#### 怎么写（策略骨架）

```text
失败
  ├─ 可重试（超时、429、5xx）→ 延迟重投，次数 +1
  │     └─ 超过 max_retries → 进 DLQ，job=failed
  └─ 不可重试（校验失败）→ 直接 failed / DLQ，不占重试预算
```

Worker 内还建议：

- 每次尝试打结构化日志：`job_id`、`attempt`、`error_type`  
- 对 LLM/工具设**超时**，避免永久挂起占着消费者  

#### 易错点

- 所有异常一律重试 100 次 → 账单与噪声爆炸  
- 进了 DLQ 无人看 → 等于静默丢业务  
- 重试不带抖动（jitter）→ 惊群打爆下游  

#### 对照

| | 同步 API 内 try/except | 队列重试 |
|--|------------------------|----------|
| 失败可见性 | 立刻返回 5xx | job 状态 / DLQ / 告警 |
| 对用户 | 需当场决策 | 可「稍后自动恢复」 |
| 毒消息 | 一次请求结束 | 必须显式隔离 |

---

## 4. 建议掌握：Agent 长任务

### 4.1 状态机

#### 为什么要先定状态，而不是只存一段日志？

客户端、客服、排障、计费都要问同一句话：**这个任务现在到哪了？**  
没有显式状态机，你会在日志里用字符串正则「猜」。

#### 怎么写（推荐状态集合）

```text
queued → running → succeeded
                 → failed
                 → canceled
```

允许的迁移（示例）：

| 从 | 到 | 谁触发 |
|----|----|--------|
| `queued` | `running` | worker 开始执行 |
| `running` | `succeeded` | worker 成功结束 |
| `running` | `failed` | 超过重试 / 不可恢复错误 |
| `queued` / `running` | `canceled` | 用户或管理员取消 |
| `succeeded` / `failed` / `canceled` | （终态） | 不再迁回 `queued` |

非法示例：`succeeded → queued`（除非你做「显式重跑」并生成**新** `job_id`）。

#### 跑一下（迁移守卫）

```python
ALLOWED = {
    ("queued", "running"),
    ("running", "succeeded"),
    ("running", "failed"),
    ("queued", "canceled"),
    ("running", "canceled"),
}


def transition(job: Job, new: Status) -> None:
    if (job.status.value, new.value) not in ALLOWED:
        raise ValueError(f"illegal: {job.status} → {new}")
    job.status = new
```

#### 易错点

- 只有 `pending/done` 两态 → 无法区分「排队」与「正在跑」，取消与超时难做  
- 终态仍可被旧消息改写 → 重复投递把 `succeeded` 打回 `running`  
- 取消只改 DB、不通知 worker → worker 仍跑完并覆盖状态（需协作取消令牌/周期检查）  

#### 对照：进程内 Future vs Job 状态

| | `asyncio.Task` / 线程 Future | 持久化 Job |
|--|------------------------------|------------|
| 进程重启 | 丢失 | 仍可查询（若落库） |
| 跨实例 | 难 | 天然按 `job_id` |
| 适合 | 单进程内编排 | 用户可见的长任务 |

### 4.2 Job API 草图

#### 为什么是「创建 + 查询」而不是一个超长 POST？

因为 HTTP 适合做短事务；长任务适合：

```text
POST /v1/jobs        创建（入队）
GET  /v1/jobs/{id}   查状态与结果
```

可选扩展（了解即可）：`POST /v1/jobs/{id}/cancel`、WebSocket/SSE 推送进度。

#### 怎么写（JSON 契约示例）

创建：

```http
POST /v1/jobs
Content-Type: application/json

{
  "type": "agent_run",
  "payload": {
    "session_id": "s_123",
    "prompt": "总结这三篇文档"
  }
}
```

响应（202）：

```json
{
  "job_id": "j_01",
  "status": "queued"
}
```

查询：

```http
GET /v1/jobs/j_01
```

```json
{
  "job_id": "j_01",
  "status": "succeeded",
  "result": {
    "answer": "……",
    "usage": {"input_tokens": 1200, "output_tokens": 400}
  },
  "error": null
}
```

失败时：

```json
{
  "job_id": "j_01",
  "status": "failed",
  "result": null,
  "error": {"code": "TOOL_TIMEOUT", "message": "search exceeded 30s"}
}
```

#### 跑一下（调用方伪代码）

```python
# 客户端侧时序（示意）
job = post_json("/v1/jobs", body)
job_id = job["job_id"]

while True:
    info = get_json(f"/v1/jobs/{job_id}")
    if info["status"] in {"succeeded", "failed", "canceled"}:
        break
    sleep(1.0)
```

生产中应加：最大轮询时长、退避、超时后展示「仍在处理」。

#### 易错点

- 把大结果只放在消息队列里、不落库 → 查询 API 无权威数据源  
- `GET` 在 `queued` 时 404 → 客户端以为创建失败；创建后即应可查  
- 响应里泄露其他用户的 `job_id` 可被遍历 → 要鉴权（job 归属用户）  

### 4.3 Worker 内工程要点

#### 为什么 worker 不是「while True: 调一下 Agent」就结束？

长任务还要可观测、可停止、可追责。

#### 怎么写（清单）

| 要点 | 做法 |
|------|------|
| 超时 | 整 job 与单步工具都设 timeout |
| 心跳/进度 | 可选字段 `progress`、`heartbeat_at`，避免「假死」误判 |
| 结构化日志 | 每行带 `job_id`（及 `trace_id`） |
| 取消 | 循环检查 `canceled` 或取消令牌 |
| 资源 | 限制并发（每个 worker 同时跑几个 Agent） |

#### 易错点

- 无超时的 LLM 调用 → 一个挂起占死消费者  
- 日志只有「error」字符串、无 `job_id` → 无法在海量日志里定位  
- 无限并发 `asyncio.create_task` → 内存与费率失控  

### 4.4 FastAPI `BackgroundTasks` 不够用时：上队列

#### 为什么本章要单独钉死这条边界？

模块 06 已约定（并写入 [`CONVENTIONS.md`](../CONVENTIONS.md)）：

> **FastAPI `BackgroundTasks`：轻量收尾，长任务请上队列。**

`BackgroundTasks` 解决的是：「响应先返回，再在**同一进程**里做一点最好完成的事」。  
它**不是**分布式任务系统。

#### 怎么写（对照决策表）

| 适合 `BackgroundTasks` | 应上队列 |
|------------------------|----------|
| 写一行访问日志、打点 | 跑 Agent 多步、长 LLM 链 |
| 删除临时文件 | 需要重试、持久化、可观测的任务 |
| 可接受「进程挂了就丢」 | 要至少一次 / 死信 / 多机工人 |
| 毫秒～少量秒、失败可忽略 | 分钟级、失败要可查可恢复 |
| 与请求同生命周期即可 | 要跨部署、滚动发布仍继续跑 |

决策口诀：

```text
轻量收尾、丢了可接受？ → BackgroundTasks
用户要查进度 / 要重试 / 要多 worker？ → 消息队列 + jobs 表
```

#### 跑一下（把错误用法改成正确用法）

错误（长任务塞进 BackgroundTasks）：

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()


def run_long_agent(prompt: str) -> None:
    # 假装 180s；还占着 API 进程
    ...


@app.post("/v1/agent/run")
async def agent_run(prompt: str, tasks: BackgroundTasks) -> dict:
    tasks.add_task(run_long_agent, prompt)
    return {"ok": True}  # 无 job_id、无状态、无重试
```

正确方向（示意）：

```python
@app.post("/v1/jobs", status_code=202)
async def create_job(prompt: str) -> dict:
    job_id = create_job_row(prompt)       # 落库 queued
    enqueue({"job_id": job_id})         # 真队列
    return {"job_id": job_id, "status": "queued"}
```

#### 易错点（BackgroundTasks 专项）

| 错法 | 真相 |
|------|------|
| 以为 `add_task` = 另一台机器在跑 | 仍在**本进程** |
| 部署 kill 进程时以为任务会迁移 | 未跑完即丢 |
| 用它做「生产级 Agent 平台」 | 缺 ack、DLQ、水平扩展消费者 |
| 在 task 里使用已关闭的 Request/Session | 只传 `job_id` 等普通数据 |

#### 对照：三条路径

| 路径 | 进程模型 | 可靠投递 | 典型用途 |
|------|----------|----------|----------|
| 同步跑完 | API 内 | 无（请求级） | 超短、强一致要当场结果 |
| `BackgroundTasks` | 同 API 进程 | 弱（进程没了就没了） | 日志、轻量收尾 |
| 真队列 + worker | 独立消费者 | 可做成至少一次 | Agent 长任务 |

---

## 5. 了解即可：选型对比

### 5.1 粗地图

#### 为什么先要地图，而不是先背品牌？

品牌很多，问题只有几类：任务队列、事件流、托管省运维。先对号入座，再谈参数调优。

| 系统 | 粗印象 | 更适合 | 不太适合当第一站 |
|------|--------|--------|------------------|
| **Redis Streams（+ ACK）** / 常见任务库 | 简单任务够用；运维面相对小 | 中小型 Agent job、已有 Redis | 超大规模事件总线 |
| **Redis LIST** | 仅演示入队出队 | 教学、可丢的信号 | 可靠任务（见约定） |
| **RabbitMQ** | 传统任务队列很强 | 路由、ack、多种消息模式 | 超高吞吐日志流（也能做，但不是主叙事） |
| **Kafka** | 日志/事件流、高吞吐、可重放 | 事件溯源、大数据管道 | 「我就想跑几个后台 job」的起步 |
| **云 SQS 等** | 托管省运维 | 云上快速落地 | 本地/离线复杂拓扑（视厂商而定） |
| **Celery / RQ / ARQ / Dramatiq** | Python 侧任务框架（底下接 Redis/Rabbit 等） | 快速给 FastAPI 挂 worker | 把框架当 broker 本身 |

#### 怎么写（选型问题清单）

按顺序问：

1. 消息丢了能否接受？不能 → 排除「纯 LIST 演示风」  
2. 要不要重放历史事件？要 → 更偏 Kafka 一类日志系统  
3. 团队会不会运维这套组件？不会 → 优先托管或已有的 Redis  
4. 只要「job 异步执行」还是「全域事件总线」？前者别一上来 Kafka  

#### 易错点

- 「大厂用 Kafka，所以我的 Demo 也要用」→ 运维与心智成本可能高于业务本身  
- 选了强力 broker 却不做幂等 → 重复执行照样出事  
- 多套队列并存无规范 → 同一平台三种任务语义，排障地狱  

#### 对照：任务队列 vs 事件流（极简）

| | 任务队列思维 | 事件流思维 |
|--|--------------|------------|
| 消息含义 | 「请执行这个 job」 | 「发生了这件事」 |
| 消费后 | 常删除/ack 掉 | 常保留一段时间可重放 |
| Agent 起步 | 更贴近 Job API | 进阶：多服务联动、审计 |

口诀：

> **先选团队会运维的；正确的幂等与状态机比品牌更重要。**

### 5.2 和本章其它知识点如何拼起来

```text
API 接单（Producer）
  → jobs 表（状态真源，常在 PostgreSQL）
  → Broker（可靠投递）
  → Worker（幂等消费 + 超时 + 日志）
  → GET /jobs/{id}（用户可见）
```

缓存章的 Redis 可以同时充当：

- 热数据缓存（上一章）  
- Streams/broker 或任务后端（本章）  

但**不要**把「缓存 key」和「任务消息」混在一个无文档的结构里糊弄——职责写清楚。

---

## 6. 练习指引

按练习册完成书面题与（建议）内存队列 demo：

[`exercises/07-data-persistence/05-message-queue.md`](../../exercises/07-data-persistence/05-message-queue.md)

建议顺序：

1. B1 同步痛点 → 对照本章 §1  
2. B2 角色图 → 对照 §2  
3. B3 至少一次与幂等 → 对照 §3  
4. B4 状态机 → 对照 §4.1  
5. A1/A2 → 自己跑通最小闭环  
6. C1 BackgroundTasks vs Queue → 对照 §4.4  

---

## 7. 小结与下一站

### 知识地图（骨架回顾）

```text
为什么需要队列
  → 同步长任务：超时 / 刷新 / 断连 / 占满 worker
  → 队列化：接单返回 job_id，worker 异步跑

生产者 / 消费者
  → Producer / Broker / Consumer
  → LIST+BRPOP 仅演示（非至少一次）
  → 生产用 ack / 可见性超时

至少一次与幂等
  → 可能重复 → job_id / 唯一约束 / 工具幂等键
  → 重试 + DLQ 隔离毒消息

Agent 长任务
  → 状态机 queued/running/succeeded/failed/canceled
  → POST+GET Job API
  → BackgroundTasks 轻量收尾；长任务上队列

选型
  → Redis Streams / Rabbit / Kafka / 云队列 / Python 任务框架
  → 幂等与状态机 > 品牌
```

### 自检

- [ ] 能画 job 入队与查询状态流程  
- [ ] 能标出 FastAPI=Producer、worker=Consumer  
- [ ] 理解至少一次 ⇒ 要幂等，并能举副作用反例  
- [ ] 知道 LIST+BRPOP 与至少一次不是同一回事  
- [ ] 知道 BackgroundTasks 与真队列边界  

### 模块 07 收官

下一模块：[`../08-devops-architecture/README.md`](../08-devops-architecture/README.md) —— Linux / Docker / 软件架构。

队列化的 worker、多副本 API、broker 本身如何部署与观测，会在运维与架构模块继续碰到——那时你已有「为什么必须拆进程」的直觉。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[缓存与 Redis](./04-redis-cache.md)
- 下一模块：[部署、运维与软件架构](../08-devops-architecture/README.md)
