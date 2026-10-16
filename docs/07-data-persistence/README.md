# 模块 07-data-persistence：数据库与数据持久化

> 状态：`五章正文与练习已全部完成` · 预计周期：2～3 周

## 模块目标

掌握 SQL/ORM/缓存/队列的工程用法与取舍。

## 为什么现在学

Memory、会话、任务状态、知识库元数据都依赖持久化。没有这一层，Agent 只能做「无状态 Demo」。

## 章节目录

1. [SQL 基础](./01-sql.md) · [练习](../../exercises/07-data-persistence/01-sql.md)
2. [PostgreSQL](./02-postgresql.md) · [练习](../../exercises/07-data-persistence/02-postgresql.md)
3. [Python ORM](./03-orm.md) · [练习](../../exercises/07-data-persistence/03-orm.md)
4. [缓存与 Redis](./04-redis-cache.md) · [练习](../../exercises/07-data-persistence/04-redis-cache.md)
5. [消息队列基础](./05-message-queue.md) · [练习](../../exercises/07-data-persistence/05-message-queue.md)

## 建议学习方式

1. SQL 先用 SQLite 动手，PG 概念同步建立
2. ORM 章节务必自己跑通一次 Session CRUD
3. Redis/队列若环境受限，可用内存模拟，但架构图要画清楚
4. 始终追问：数据真源在哪？缓存会不会读到陈旧数据？任务消息会不会丢或重复执行？

## 模块自检

- [ ] 能手写基础 SQL 并理解索引/事务
- [ ] 能设计会话/消息表与连接配置
- [ ] 理解 ORM 模型、Session、迁移
- [ ] 能设计缓存键/TTL 与简单限流
- [ ] 能为 Agent 长任务设计队列 + 状态查询

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Web 后端](../06-web-backend/README.md)
- 下一模块：[部署、运维与软件架构](../08-devops-architecture/README.md)
