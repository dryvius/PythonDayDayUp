# 缓存与 Redis

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：3～4 小时  
> 对应练习：[`exercises/07-data-persistence/04-redis-cache.md`](../../exercises/07-data-persistence/04-redis-cache.md)

## 本章定位

- **本章角色**：理解缓存解决什么问题；掌握 Redis 常用结构与过期；建立一致性与限流直觉。
- **和 Agent**：热点 prompt 结果、会话热数据、限流计数、分布式锁雏形。

## 学习目标

1. 说清何时该用缓存、何时不该。
2. 认识 Redis 常用数据结构。
3. 理解 TTL 过期与一致性的基本权衡。
4. 会设计简单限流/会话缓存方案。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 缓存用途、常用结构、过期与一致性直觉 | 能设计简单缓存键 |
| **建议掌握** | 限流计数、会话缓存 | 能落地小方案 |
| **了解即可** | 集群与持久化 | 地图 |

---

## 1. 必掌握：缓存用途

适合：

- 读多写少
- 计算结果贵（LLM 响应、重查询）
- 需要跨进程共享的热数据/计数

不适合：

- 强一致账本唯一真源（仍以 DB 为准）
- 无过期策略的无限增长 key

模式：

```text
读：先查缓存 → 未命中查 DB → 回填缓存
写：更新 DB → 删除/更新缓存（注意顺序与失败）
```

---

## 2. 必掌握：常用数据结构

| 结构 | 用途 | Agent 例子 |
|------|------|------------|
| STRING | 简单值/JSON | `session:{id}:summary` |
| HASH | 对象字段 | 用户配置 |
| LIST | 时间线；作队列仅演示 | 最近事件（可靠队列见下一章 / CONVENTIONS） |
| SET | 去重集合 | 在线设备 |
| ZSET | 排行/延时 | 优先级、滑动窗口计数辅助 |

键设计：

```text
agent:user:{user_id}:quota:2026-04-16
agent:session:{session_id}:hot
```

带前缀、带业务、带时间粒度。

---

## 3. 必掌握：过期与一致性

```text
SET key value EX 300   # 5 分钟过期
```

权衡：

| 策略 | 结果 |
|------|------|
| 短 TTL | 更新鲜，更易打穿到 DB |
| 长 TTL | 更快，更易读到**陈旧（stale）**数据 |
| 写时删缓存 | 常见；并发下仍有竞态需进阶方案 |

接受「缓存允许短暂不一致」，核心数据以 DB 为准。

术语提醒：这里说的是 **stale（过期未刷新）**，不是 SQL 隔离级别里的 **脏读（读到未提交事务）**。两词不要混用。

---

## 4. 建议掌握：限流与会话

### 限流计数

优先把时间桶写进 key（自然过期边界清晰）：

```text
INCR rate:user:123:2026-04-16T14:05   # 按分钟桶
# 首次创建时设 TTL，或用原子脚本保证 INCR+EXPIRE
若 count > N → 429
```

反例（教学常见坑）：

```text
INCR rate:user:123:minute
EXPIRE rate:user:123:minute 60   # 两步非原子：中间崩溃可能永不 EXPIRE
```

落地时用 **Lua / MULTI** 把计数与过期绑在一起，或用带时间桶的 key + 首次 `SET … EX … NX` / `EXPIRE` 保护。

### 会话热缓存

把最近消息摘要放 Redis，完整历史仍在 PG。  
进程重启不丢真源；缓存只是加速。

---

## 5. 了解即可：集群与持久化

Redis Cluster、RDB/AOF……部署期再学。开发用单机 Docker 足够。

```bash
docker run --name redis-agent -p 6379:6379 -d redis:7
```

---

## 6. 练习指引

[`exercises/07-data-persistence/04-redis-cache.md`](../../exercises/07-data-persistence/04-redis-cache.md)

---

## 7. 小结与下一站

### 自检

- [ ] 能设计合理 cache key + TTL
- [ ] 能说明缓存与 DB 的职责边界
- [ ] 能描述计数限流思路

### 下一章

[`05-message-queue.md`](./05-message-queue.md) —— 长任务与异步解耦。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Python ORM](./03-orm.md)
- 下一章：[消息队列基础](./05-message-queue.md)
