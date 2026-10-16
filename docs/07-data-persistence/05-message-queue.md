# 消息队列基础

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：2～4 小时  
> 对应练习：[`exercises/07-data-persistence/05-message-queue.md`](../../exercises/07-data-persistence/05-message-queue.md)

## 本章定位

- **本章角色**：理解为何需要队列；生产者/消费者；至少一次投递；Agent 长任务如何异步化。
- **不是**：深挖 Kafka 内核；先建立正确架构直觉。

## 学习目标

1. 能判断「该同步返回」还是「丢队列后台跑」。
2. 描述生产者、消费者、broker 角色。
3. 理解至少一次投递与幂等消费。
4. 能设计 Agent 长任务状态机草图。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 为何需要队列、生产/消费、至少一次投递 | 能画架构 |
| **建议掌握** | Agent 长任务场景 | 能设计 job API |
| **了解即可** | Kafka/RabbitMQ 对比 | 地图 |

---

## 1. 必掌握：为什么需要队列

同步 API 跑 3 分钟 Agent：

```text
网关超时 / 用户刷新 / 连接断开 / 占满 worker
```

队列化：

```text
POST /jobs → 入队 → 立即返回 job_id
worker 消费 → 更新状态 → 完成后可轮询/回调
```

其它收益：削峰、解耦、重试、多消费者扩展。

---

## 2. 必掌握：生产者 / 消费者

```text
Producer（API） → Broker（Redis Streams / RabbitMQ / SQS / Kafka …）
                         → Consumer（worker）
```

最小 Redis **列表**直觉（仅演示入队/出队，**不是**可靠队列）：

```text
LPUSH jobs '{...}'
BRPOP jobs 超时
```

注意语义：

| 做法 | 实际语义 | 风险 |
|------|----------|------|
| `LIST` + `BRPOP` | 取出即删除 ≈ **at-most-once** | worker 取出后崩溃 → **丢消息** |
| Streams 消费组 + ACK / RabbitMQ ack 等 | 偏 **at-least-once** | 可能重复投递 → 要幂等 |

学习阶段可用 LIST 感受「生产者/消费者」；生产请用带 **ack / 可见性超时** 的机制（Redis Streams、Celery/RQ/ARQ/Dramatiq + Redis/RabbitMQ 等）。

---

## 3. 必掌握：至少一次投递

多数**可靠**队列保证倾向：

> **At-least-once**：可能重复投递；很少承诺「正好一次」免费午餐。

因此消费者必须尽量 **幂等**：

- 用 `job_id` 去重
- 写库用唯一约束
- 工具调用带幂等键

失败：进入重试 / 死信队列（DLQ），避免毒消息卡死。

对照：上一节的 `BRPOP` 示例**不**提供至少一次；不要把「列表队列」和「至少一次」混为一谈。

---

## 4. 建议掌握：Agent 长任务

状态建议：

```text
queued → running → succeeded
                 → failed
                 → canceled
```

API：

```text
POST /v1/jobs        创建
GET  /v1/jobs/{id}   查状态与结果
```

Worker 内：

- 设超时
- 心跳/进度字段（可选）
- 结构化日志带 `job_id`

FastAPI `BackgroundTasks` 只适合轻量；真长任务请上队列。

---

## 5. 了解即可：选型对比

| 系统 | 粗印象 |
|------|--------|
| Redis Streams（+ ACK）/ 托管队列 | 简单任务够用；列表仅适合可丢任务 |
| RabbitMQ | 传统任务队列很强 |
| Kafka | 日志/事件流、高吞吐 |
| 云 SQS 等 | 托管省运维 |

先选团队会运维的；正确的幂等与状态机比品牌更重要。

---

## 6. 练习指引

[`exercises/07-data-persistence/05-message-queue.md`](../../exercises/07-data-persistence/05-message-queue.md)

---

## 7. 小结与下一站

### 自检

- [ ] 能画 job 入队与查询状态流程
- [ ] 理解至少一次 ⇒ 要幂等
- [ ] 知道 BackgroundTasks 与真队列边界

### 模块 07 收官

下一模块：[`../08-devops-architecture/README.md`](../08-devops-architecture/README.md) —— Linux / Docker / 软件架构。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[缓存与 Redis](./04-redis-cache.md)
- 下一模块：[部署、运维与软件架构](../08-devops-architecture/README.md)
