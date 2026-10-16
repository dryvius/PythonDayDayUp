# 练习：消息队列基础

> 对应文档：[`docs/07-data-persistence/05-message-queue.md`](../../docs/07-data-persistence/05-message-queue.md)  
> 状态：`已完成出题` · 建议用时：45～75 分钟

可用内存 `queue.Queue` 模拟 broker。

---

## 基础题（必做）

### B1. 同步痛点（书面）

列出同步跑 3 分钟 Agent 的 4 个问题。

### B2. 角色图

画出 Producer / Broker / Consumer，并标注 FastAPI 与 worker 各是谁。

### B3. 至少一次

解释：为什么消费者要幂等？举一个「重复扣费/重复发邮件」的 Agent 工具例子与对策。

### B4. Job 状态机

定义状态集合与允许迁移（例如不可从 succeeded → queued）；画出或列表说明。

---

## 进阶题（建议）

### A1. 内存队列 demo

API 线程 `put` job，worker 线程 `get` 并处理；主程序打印 job 状态变化。

### A2. Job API 草图

写清 `POST /v1/jobs` 与 `GET /v1/jobs/{id}` 的请求/响应 JSON 示例。

---

## 挑战题（可选）

### C1. BackgroundTasks vs Queue（书面）

对比适用边界，至少各 3 条。

---

## 模块 07 通关自检

- [ ] 会基础 SQL（CRUD/JOIN/事务/索引直觉）
- [ ] 理解 PG 类型/约束/连接配置
- [ ] 理解 ORM Session 与迁移价值
- [ ] 能设计缓存键与限流计数思路
- [ ] 能为长任务设计队列化方案

完成后进入模块 08《部署、运维与软件架构》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
