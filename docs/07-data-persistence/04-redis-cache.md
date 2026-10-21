# 缓存与 Redis

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：3～4 小时（有「读多写少 / 共享计数」经验可更快；TTL 与一致性建议动手踩一遍）  
> 对应练习：[`exercises/07-data-persistence/04-redis-cache.md`](../../exercises/07-data-persistence/04-redis-cache.md)

## 本章定位

- **本章角色**：理解缓存解决什么问题；掌握 Redis 常用结构与过期；建立一致性与限流直觉。
- **和 Agent**：热点 prompt 结果、会话热数据、限流计数、分布式锁雏形。
- **不是**：把 Redis 当唯一真源；也不是本章就把 Cluster / Streams 运维细节啃完。
- **刻意简化提醒**（见 [`CONVENTIONS`](../CONVENTIONS.md)）：文中若用 `LIST` + `BRPOP` 演示「入队/出队」，**只是**感受队列形状，**不是** at-least-once 可靠投递。

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

这一节会刻意写细——后面所有「键怎么起、TTL 怎么选、限流怎么计」都建立在「缓存到底替你挡什么」之上。

### 1.1 缓存在解决什么问题

#### 为什么需要缓存？

上一章你已经会把会话、消息落到 PostgreSQL。DB 是**真源**：可查询、可事务、可备份。但 Agent 场景里常出现：

```text
同一份「会话热摘要」被读几十次，写很少
同一段贵重计算结果（LLM 响应、重 SQL、重向量检索）反复被问
多个进程/容器要共享「当前分钟调用次数」
```

每次都打 DB / 再调一次 LLM，会慢、会贵、会把连接池打满。缓存的价值是：

> **把「贵且可短暂复用」的结果放到更快的一层，用空间与可接受的陈旧换延迟与成本。**

可以先记一句：

> 缓存不是第二数据库；它是**加速层**与**共享协调层**。核心业务仍以 DB 为准。

#### 怎么写（先建立职责边界）

| 层 | 职责 | 丢了会怎样 |
| --- | --- | --- |
| PostgreSQL 等 DB | 真源、事务、长期查询 | 业务数据丢 → 不可接受 |
| Redis 缓存 | 热数据、计数、短会话加速 | 可重建；最多短暂变慢或读到旧值 |
| 进程内 dict | 单进程极热路径 | 重启即空；多实例不共享 |

Agent 里常见落点：

```text
热点 prompt / 工具结果缓存（带业务键与 TTL）
session:{id}:hot          → 最近消息摘要（完整历史仍在 PG）
rate:user:{id}:{minute}   → 限流计数
lock:job:{id}             → 分布式锁雏形（本章只建立印象）
```

#### 跑一下（心智实验，不必真连）

假设 `get_session_summary(session_id)` 每次都查 PG 要 20ms，命中 Redis 约 1ms：

```text
100 次读、几乎无写：
  全打 DB  → 约 2000ms 量级 + 连接压力
  缓存命中 → 约 100ms 量级（首次 miss 仍打一次 DB）
```

再想贵计算：同 prompt 缓存命中一次，可能省掉一次完整 LLM 调用。这就是「该不该缓存」的体感来源。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把 Redis 当账本唯一真源 | 重启/淘汰/过期后业务数据对不上 |
| 「凡是读过的都缓存、永不过期」 | 内存涨爆；长期读到陈旧数据 |
| 多实例只靠进程内 dict 做限流 | 每个进程各计各的，限流形同虚设 |

#### 对照：DB vs 缓存

| 问题 | 找 DB | 找缓存 |
| --- | --- | --- |
| 「昨天那条消息原文是什么？」 | ✅ | ❌（除非你刻意镜像，且接受可能旧） |
| 「这一分钟还剩几次配额？」 | 可以，但偏慢 | ✅ 更合适 |
| 「跨容器共享当前会话热摘要」 | 能，但贵 | ✅ |
| 「扣款 / 库存 / 审计唯一真相」 | ✅ | ❌ |

---

### 1.2 适合 / 不适合

#### 为什么要先画这条线？

缓存用错比不用更危险：你会以为「已经更新了」，其实读的是旧值；或把不该丢的数据只放在可淘汰层。

#### 怎么写（决策清单）

**适合：**

- 读多写少
- 计算结果贵（LLM 响应、重查询）
- 需要跨进程共享的热数据/计数

**不适合：**

- 强一致账本唯一真源（仍以 DB 为准）
- 无过期策略的无限增长 key

再补两条 Agent 侧细化：

| 数据 | 倾向 | 原因 |
| --- | --- | --- |
| 用户每日 LLM 次数 | 适合缓存计数 | 高频增减、可丢后从 DB 校准或接受窗口误差 |
| 会话完整消息历史 | DB 为主 | 要查询、分页、审计；缓存最多放「最近 N 条摘要」 |
| 工具调用审计日志 | DB | 丢了说不清「调过没有」 |
| 同一 prompt 的短时结果 | 适合短 TTL 缓存 | 贵、可复用、过期可重算 |

#### 跑一下（书面对照练习）

对下面每条，先自己标「适合 / 不适合」，再对答案：

```text
1. agent:prompt_hash:{h} → LLM JSON 结果，TTL 10 分钟
2. 转账余额唯一字段，只写 Redis、不写 DB
3. session:{id}:recent3 → 最近 3 条消息 JSON，TTL 1 小时，完整历史在 PG
4. 无限 TTL 的「所有用户访问过的 URL 集合」，从不清理
```

参考：1 适合；2 不适合；3 适合；4 不适合（无过期无限增长）。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 「能缓存就缓存」 | 强一致字段被缓存拖成错误真相 |
| 只缓存、不设计 miss 回源 | Redis 空了服务直接 500 |
| 把「可重建」当成「可不要 TTL」 | 内存与陈旧同时失控 |

#### 对照：缓存 vs 本地变量

| | 进程内变量 / dict | Redis |
| --- | --- | --- |
| 速度 | 最快 | 很快（多一跳网络） |
| 多进程共享 | ❌ | ✅ |
| 重启 | 丢 | 视持久化；缓存语义下应能重建 |
| 适用 | 单进程极热、可丢 | 跨实例热数据 / 计数 / 协调 |

---

### 1.3 读写模式：Cache-Aside

#### 为什么先学 Cache-Aside？

这是 Web / Agent 最常见的「旁路缓存」：应用自己管缓存，DB 仍是真源。先把它写熟，再谈更花的 write-through 等变体。

#### 怎么写

模式：

```text
读：先查缓存 → 未命中查 DB → 回填缓存
写：更新 DB → 删除/更新缓存（注意顺序与失败）
```

读路径伪代码：

```python
def get_session_summary(session_id: str) -> str:
    key = f"agent:session:{session_id}:hot"
    cached = redis.get(key)
    if cached is not None:
        return cached  # 命中

    summary = db.query_summary(session_id)  # 未命中 → 真源
    redis.set(key, summary, ex=300)         # 回填，带 TTL
    return summary
```

写路径（更常见：**先写 DB，再删缓存**）：

```python
def update_session_summary(session_id: str, summary: str) -> None:
    db.save_summary(session_id, summary)  # 真源先成功
    redis.delete(f"agent:session:{session_id}:hot")
    # 下次读会 miss → 从 DB 回填新值
```

#### 跑一下

用「假 Redis」也能练流程（学习用；无 Docker 时练习题允许）：

```python
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class FakeRedis:
    store: dict[str, tuple[str, float | None]]

    def get(self, key: str) -> str | None:
        item = self.store.get(key)
        if item is None:
            return None
        value, expire_at = item
        if expire_at is not None and time.time() >= expire_at:
            del self.store[key]
            return None
        return value

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        expire_at = time.time() + ex if ex is not None else None
        self.store[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


db = {"s1": "旧摘要"}
r = FakeRedis(store={})


def get_summary(sid: str) -> str:
    key = f"agent:session:{sid}:hot"
    hit = r.get(key)
    if hit is not None:
        print("cache hit")
        return hit
    print("cache miss → db")
    value = db[sid]
    r.set(key, value, ex=300)
    return value


def update_summary(sid: str, text: str) -> None:
    db[sid] = text
    r.delete(f"agent:session:{sid}:hot")


print(get_summary("s1"))   # miss → 旧摘要
print(get_summary("s1"))   # hit  → 旧摘要
update_summary("s1", "新摘要")
print(get_summary("s1"))   # miss → 新摘要
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 先删缓存再写 DB，写 DB 失败 | 缓存空了，读到旧 DB；或并发下更容易脏回填 |
| 写完 DB 忘了删/改缓存 | 长时间读到**陈旧（stale）**数据 |
| 回填不设 TTL | key 常驻，内存与一致性都难控 |
| 把「删缓存失败」当成功 | DB 新、缓存旧，直到 TTL 或人工干预 |

写时「删缓存」vs「更新缓存」：

| 策略 | 优点 | 风险 |
| --- | --- | --- |
| 写 DB 后**删除**缓存 | 实现简单；下次读回填真源 | 删失败 → 短暂 stale；并发下仍有竞态 |
| 写 DB 后**更新**缓存 | 读路径少一次 miss | 更新失败或算错 → 缓存长期错；并发写更容易乱 |

本章默认：**写后删缓存** 更常见、更好讲清。进阶的锁/延迟双删等，知道名字即可。

#### 对照：扣费直觉（别混）

| | 缓存旁路 | 支付扣款 |
| --- | --- | --- |
| 真源 | DB | 账本 DB / 专门服务 |
| 失败可接受？ | 短暂旧数据通常可接受 | 少扣多扣通常不可接受 |
| Redis 角色 | 加速 | 至多做锁/限流，不做唯一余额 |

---

## 2. 必掌握：常用数据结构

Redis 不是「只能 SET 字符串」。选对结构，键更干净、操作更原子、限流/排行更好写。

### 2.1 结构地图（先建立选型表）

#### 为什么需要多结构？

全用 STRING 塞 JSON 也能跑，但：

- 改对象一个字段要整段读写
- 去重、排行、时间线要用客户端自己撸
- 限流滑动窗口等场景会别扭

#### 怎么写（选型总表）

| 结构 | 用途 | Agent 例子 |
|------|------|------------|
| STRING | 简单值/JSON | `session:{id}:summary` |
| HASH | 对象字段 | 用户配置 |
| LIST | 时间线；作队列仅演示 | 最近事件（可靠队列见下一章 / CONVENTIONS） |
| SET | 去重集合 | 在线设备 |
| ZSET | 排行/延时 | 优先级、滑动窗口计数辅助 |

口诀：

```text
一个值 / 一小段 JSON     → STRING
一个对象多个字段要局部改 → HASH
有序时间线 / 演示队列    → LIST（队列演示 ≠ 可靠投递）
只要唯一集合             → SET
要分数排序 / 范围         → ZSET
```

#### 跑一下（命令级直觉）

下面用 `redis-cli` 风格建立肌肉记忆；Python 客户端只是换皮。

```text
SET agent:session:s1:hot '{"summary":"..."}' EX 300
GET agent:session:s1:hot

HSET agent:user:u1:cfg theme dark locale zh
HGET agent:user:u1:cfg theme

LPUSH agent:session:s1:events '{"type":"tool_ok"}'
LRANGE agent:session:s1:events 0 9

SADD agent:user:u1:devices "phone-a" "laptop-b"
SISMEMBER agent:user:u1:devices "phone-a"

ZADD agent:leaderboard 98 "agent-a" 85 "agent-b"
ZREVRANGE agent:leaderboard 0 2 WITHSCORES
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 大 JSON 当 STRING，却频繁改一个字段 | 读写放大、易并发互相覆盖 |
| 把 LIST 当生产任务队列并默认「不丢」 | `BRPOP` 取出即删，worker 崩溃可能丢消息（见 2.4） |
| SET / LIST 分不清 | 要去重用 SET；要保留顺序与重复用 LIST |

#### 对照：Python 容器

| Python | Redis 近似 | 差异提醒 |
| --- | --- | --- |
| `str` / `bytes` | STRING | Redis 值本质是 bytes；客户端常帮你编解码 |
| `dict` 小对象 | HASH | HASH 字段级操作；大对象仍常整段 JSON STRING |
| `list` | LIST | 两端推弹；**不是**可靠 MQ |
| `set` | SET | 服务端去重与集合运算 |
| 无直接内置 | ZSET | 成员唯一 + score 排序 |

---

### 2.2 STRING：最常用的「一键一值」

#### 为什么需要 STRING？

会话摘要、prompt 缓存、开关标记——大量场景就是「一个 key 对应一段文本/JSON」。

#### 怎么写

```python
# redis-py 示意（API 以你安装的版本为准）
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

key = "agent:session:s1:hot"
r.set(key, '{"summary":"用户在问缓存"}', ex=300)
print(r.get(key))
print(r.ttl(key))  # 剩余秒数，约 ≤ 300
```

常用变体：

```text
SET key value EX 300      # 带过期
SET key value NX EX 300   # 不存在才设（分布式锁雏形常用）
INCR key                  # 整数计数（限流核心）
```

#### 跑一下

```python
r.set("agent:flag:feature_x", "1", ex=60)
assert r.get("agent:flag:feature_x") == "1"

r.set("agent:counter:demo", "0")
r.incr("agent:counter:demo")
print(r.get("agent:counter:demo"))  # 1
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 对非整数 STRING 做 `INCR` | 报错 |
| JSON 很大却当「临时小缓存」 | 内存与网络都被拖慢 |
| `decode_responses=True` 与手写 bytes 混用 | 类型对不上，调试痛苦 |

#### 对照

| 需求 | STRING 写法 |
| --- | --- |
| 缓存一段 JSON | `SET … EX …` |
| 计数 | `INCR` / `INCRBY` |
| 「占坑」锁雏形 | `SET key token NX EX 30` |

---

### 2.3 HASH：对象字段

#### 为什么需要 HASH？

用户配置、会话元数据常有多个字段。HASH 允许 `HSET` / `HGET` 局部更新，不必每次重写整段 JSON。

#### 怎么写 / 跑一下

```python
key = "agent:user:u1:cfg"
r.hset(key, mapping={"theme": "dark", "locale": "zh", "model": "fast"})
r.hset(key, "model", "quality")  # 只改一个字段
print(r.hget(key, "theme"))      # dark
print(r.hgetall(key))
r.expire(key, 3600)
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 字段极多、极大的「巨型 HASH」 | 难运维、难过期粒度（过期是整个 key） |
| 该整段版本化缓存却拆太碎 | 一致性与回源逻辑变复杂 |
| 忘记 `EXPIRE` | HASH 常驻内存 |

#### 对照：STRING JSON vs HASH

| | 整段 JSON STRING | HASH |
| --- | --- | --- |
| 局部改字段 | 读改写整段 | `HSET` 单字段 |
| 一次取全量 | `GET` | `HGETALL` |
| 嵌套结构 | JSON 更自然 | 扁平字段更合适 |

---

### 2.4 LIST：时间线；队列仅演示

#### 为什么需要 LIST？

最近事件、最近消息 ID、简单时间线——需要**有序、可重复、两端操作**时，LIST 很合适。

#### 怎么写（时间线）

```python
key = "agent:session:s1:events"
r.lpush(key, '{"type":"user"}', '{"type":"assistant"}')
r.ltrim(key, 0, 49)  # 只保留最近 50 条
print(r.lrange(key, 0, 9))
r.expire(key, 86400)
```

#### 跑一下（入队 / 出队演示）

> **刻意简化（必读）**：下面用 `LPUSH` + `BRPOP` 只演示「生产者塞进去、消费者拿出来」的形状。  
> 按 [`CONVENTIONS`](../CONVENTIONS.md)：这是**入队出队演示**，**不是** at-least-once。  
> `BRPOP` 取出即从 LIST 删除 ≈ **at-most-once**：worker 取出后崩溃，消息可能丢。  
> 可靠队列、ack、重试见下一章 [`05-message-queue.md`](./05-message-queue.md)。

```python
# 演示用：不要当成生产任务队列
QUEUE = "agent:jobs:demo"

r.lpush(QUEUE, '{"job_id":"j1"}')  # 入队
item = r.brpop(QUEUE, timeout=1)   # 出队；(queue_name, payload) 或 None
print(item)
```

命令对照：

```text
LPUSH jobs '{...}'     # 左进
BRPOP jobs 超时        # 右阻塞出；取出即删除
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把 LIST+BRPOP 当成「至少一次投递」 | worker 崩溃可能丢任务；与下一章语义冲突 |
| 时间线无限 `LPUSH` 不 `LTRIM` | 内存涨 | 
| 用 LIST 做去重 | LIST 允许重复；去请用 SET |

#### 对照：演示队列 vs 可靠队列

| 做法 | 实际语义 | 风险 |
|------|----------|------|
| `LIST` + `BRPOP` | 取出即删除 ≈ **at-most-once** | worker 取出后崩溃 → **丢消息** |
| Streams 消费组 + ACK / RabbitMQ ack 等 | 偏 **at-least-once** | 可能重复投递 → 要幂等 |

学习阶段：LIST 感受「有人生产、有人消费」。  
生产任务：带 **ack / 可见性超时** 的机制（Redis Streams、Celery/RQ/ARQ 等）——细节放到下一章。

---

### 2.5 SET 与 ZSET

#### 为什么需要它们？

- **SET**：在线设备、已授权 tool 名、去重 ID——只要「在不在集合里」。
- **ZSET**：排行榜、按分数取 TopN、延时/优先级队列的辅助结构、滑动窗口限流的辅助。

#### 怎么写 / 跑一下

```python
# SET
dev = "agent:user:u1:devices"
r.sadd(dev, "phone-a", "laptop-b")
print(r.sismember(dev, "phone-a"))  # True
print(r.smembers(dev))

# ZSET：score 越大越靠前（视你的业务）
board = "agent:tool:latency_ms"
r.zadd(board, {"search": 120, "calc": 5, "crawl": 800})
print(r.zrange(board, 0, 1, withscores=True))      # 最快的两个
print(r.zrevrange(board, 0, 1, withscores=True))   # 最慢的两个
```

滑动窗口计数的辅助直觉（了解即可，限流主路径见第 4 节时间桶）：

```text
ZADD rate:u1:window <timestamp> <unique_request_id>
ZREMRANGEBYSCORE rate:u1:window 0 <now-60>
ZCARD rate:u1:window  → 过去 60 秒请求数
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用 SET 保存「有序时间线」 | SET 无序（实现有序遍历也不当时间线用） |
| ZSET 成员重复插入 | 成员唯一；再 ZADD 是**更新 score** |
| 窗口 ZSET 不清理旧 member | 内存泄漏 |

#### 对照

| 需求 | 选 |
| --- | --- |
| 去重、成员测试 | SET |
| TopN / 按时间分排序 | ZSET |
| 严格时间线且可重复 | LIST |

---

### 2.6 键设计

#### 为什么键名值得单独练？

缓存出问题，十有八九先查 key：拼错、冲突、无法按业务批量清理、TTL 粒度不清。

#### 怎么写

推荐形态：

```text
agent:user:{user_id}:quota:2026-04-16
agent:session:{session_id}:hot
```

原则：

1. **带前缀**：`agent:` / 服务名，避免多项目共 Redis 撞车
2. **带业务**：`user` / `session` / `rate`
3. **带实体 ID**：可定位、可删除
4. **带时间粒度**（计数类）：日 / 分钟桶写进 key，过期边界清晰

```text
好：rate:user:123:2026-04-16T14:05
坏：rate:user:123:minute          # 所有分钟共用一个 key，过期语义糊
坏：s1                            # 看不出业务，极易冲突
```

#### 跑一下

```python
from datetime import datetime, timezone


def quota_key(user_id: str, day: str | None = None) -> str:
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"agent:user:{user_id}:quota:{day}"


def session_hot_key(session_id: str) -> str:
    return f"agent:session:{session_id}:hot"


print(quota_key("u42"))
print(session_hot_key("s9"))
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| key 含空格/难编码字符 | 运维与排查痛苦 |
| 把「用户输入原样」拼进 key 且不校验 | key 爆炸、注入式脏 key |
| 同一含义多种拼法 | 缓存命中率假低、删不干净 |

#### 对照：TTL 与 key 粒度

| key 设计 | TTL 建议（示例） |
| --- | --- |
| `…:quota:2026-04-16` | 到第二天多留一点缓冲，如 26h |
| `…:rate:…T14:05`（分钟桶） | 2～3 分钟即可 |
| `…:session:…:hot` | 数分钟～数小时，按「多重算成本」定 |

---

## 3. 必掌握：过期与一致性

缓存的核心矛盾：**快** 与 **新** 不可兼得时，你要显式做权衡。

### 3.1 TTL：让 key 自己死掉

#### 为什么需要过期？

没有 TTL：

- 内存只增不减
- 写后漏删时，陈旧数据可能「永远对」

TTL 是最便宜的安全网：即使删缓存失败，过期后也会回源。

#### 怎么写

```text
SET key value EX 300   # 5 分钟过期
```

Python：

```python
r.set("agent:session:s1:hot", "…", ex=300)
r.expire("agent:other", 120)   # 对已存在 key 设/刷新过期
print(r.ttl("agent:session:s1:hot"))
```

#### 跑一下

```python
r.set("tmp:demo", "1", ex=2)
print(r.get("tmp:demo"))  # 1
time.sleep(2.1)
print(r.get("tmp:demo"))  # None（已过期）
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只 `INCR` 从不 `EXPIRE` | 计数 key 永驻（限流节展开） |
| 每次读写都 `EXPIRE` 成「滑动永不过期」 | 热点 key 可能长期不淘汰（有时是特性，有时是坑） |
| TTL=0 / 负数语义没查文档 | 行为与预期不符 |

#### 对照：EX vs 写死永不过期

| | 短 TTL | 长 TTL / 永不过期 |
| --- | --- | --- |
| 新鲜度 | 更好 | 更易 stale |
| DB 压力 | 更容易打穿 | 更省 |
| 内存 | 更易回收 | 要强依赖删除策略 |

---

### 3.2 一致性权衡：短 TTL、长 TTL、写时删

#### 为什么不能「又强一致又永远命中」？

缓存与 DB 是两份拷贝。只要允许异步、允许失败、允许并发，就存在窗口：有人读到旧的。

工程上通常**接受短暂不一致**，并规定：

> 核心数据以 DB 为准；缓存允许短暂 **stale**。

#### 怎么写（策略表）

| 策略 | 结果 |
|------|------|
| 短 TTL | 更新鲜，更易打穿到 DB |
| 长 TTL | 更快，更易读到**陈旧（stale）**数据 |
| 写时删缓存 | 常见；并发下仍有竞态需进阶方案 |

读多写少的会话摘要：TTL 5～30 分钟 + 写后删，通常够用。  
配额看板要较新：TTL 更短，或写路径主动删。

#### 跑一下（stale 窗口体感）

```text
T0  读：缓存 miss → DB=旧 → 回填缓存=旧
T1  写：DB=新；删缓存失败（网络抖一下）
T2  读：仍命中缓存=旧   ← stale 窗口
T3  TTL 到期或删成功
T4  读：miss → DB=新 → 回填新
```

教学结论：缓存层要按「错一会儿可接受吗」设计，而不是按「绝对正确」设计。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 追求缓存与 DB 实时强一致却无协议 | 复杂度爆炸；事务跨 Redis+DB 更难 |
| 写后更新缓存算错字段 | 比「旧一点」更糟：错得像真的 |
| 并发：A 回填旧值盖过 B 的新值 | 经典竞态；短 TTL + 写删可缓解，彻底方案更进阶 |

#### 对照：三种「旧」别混

| 术语 | 含义 | 本章场景 |
| --- | --- | --- |
| **stale（陈旧）** | 读到过期未刷新的缓存拷贝 | ✅ 缓存一致性主术语 |
| **脏读（dirty read）** | SQL 隔离里读到**未提交**事务 | ❌ 不要和缓存 stale 混用 |
| 过期未命中 | key 没了，回源 | 正常路径 |

术语提醒：这里说的是 **stale（过期未刷新）**，不是 SQL 隔离级别里的 **脏读（读到未提交事务）**。两词不要混用。

---

### 3.3 穿透、击穿、雪崩（建立关键词）

#### 为什么要知道这三个词？

练习挑战题会问「热点 key 过期瞬间大量请求打 DB」。先把地图立住，不必本章实现完整防护。

#### 怎么写（地图）

| 现象 | 直觉 | 常见缓解关键词 |
| --- | --- | --- |
| **穿透** | 查根本不存在的数据，缓存不存 → 每次打 DB | 空值短 TTL；布隆过滤（了解） |
| **击穿** | 热点 key 过期瞬间，大量并发回源 | 互斥锁回源；逻辑过期；永不过期+异步刷新 |
| **雪崩** | 大量 key 同时过期 | TTL 加随机抖动；多级缓存；限流 |

#### 跑一下（TTL 抖动示意）

```python
import random


def ttl_with_jitter(base: int, spread: int = 30) -> int:
    return base + random.randint(0, spread)


print(ttl_with_jitter(300))  # 例如 312，避免整点一起死
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 不存在也「不缓存」 | 恶意/错误 ID 可打穿 DB |
| 所有 key 同一 TTL 且同一时刻写入 | 容易一起过期 → 雪崩味道 |
| 击穿时无互斥，全都查 DB | 热点把 DB 打挂 |

#### 对照：和限流的关系

限流保护的是「入口 QPS」；击穿防护保护的是「单个热点回源」。两者常一起用，但不是同一个开关。

---

## 4. 建议掌握：限流与会话

### 4.1 限流计数

#### 为什么需要限流？

Agent API 面对的是：

```text
用户脚本死循环刷接口
某个 token 被泄露后疯狂调 LLM
突发流量把下游（DB / 模型网关）打满
```

限流把「每用户 / 每 API Key / 每 IP」的速率关在预算内。Redis 适合做**跨进程共享**的计数器。

#### 怎么写（优先：时间桶写进 key）

优先把时间桶写进 key（自然过期边界清晰）：

```text
INCR rate:user:123:2026-04-16T14:05   # 按分钟桶
# 首次创建时设 TTL，或用原子脚本保证 INCR+EXPIRE
若 count > N → 429
```

Python 示意（注意：生产应把 INCR 与 EXPIRE 绑成原子操作，见易错点）：

```python
from datetime import datetime, timezone


def allow(user_id: str, limit: int = 5) -> bool:
    bucket = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    key = f"rate:user:{user_id}:{bucket}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, 120)  # 桶结束后多留一会，便于排查
    return count <= limit
```

更稳的方向（了解即可，知道名字）：

- **Lua / MULTI**：把计数与过期绑在一起
- 带时间桶的 key + 首次 `SET … EX … NX` / `EXPIRE` 保护
- 固定窗口简单；滑动窗口可用 ZSET（更准也更重）

#### 跑一下

```python
# 假想同一分钟内
assert allow("u1", limit=5) is True
assert allow("u1", limit=5) is True
# ... 第 6 次
# allow(...) is False → 对 API 层映射为 HTTP 429
```

真 Redis 时可用 `redis-cli MONITOR` 或自己打印 `GET rate:user:…` 看计数增长。

#### 易错点

反例（教学常见坑）：

```text
INCR rate:user:123:minute
EXPIRE rate:user:123:minute 60   # 两步非原子：中间崩溃可能永不 EXPIRE
```

| 错法 | 会发生什么 |
| --- | --- |
| `INCR` 与 `EXPIRE` 分两步且无保护 | 进程在中间挂了 → key 可能永不过期 |
| 所有分钟共用 `…:minute` 一个 key | 过期与桶边界纠缠，难推理 |
| 只在进程内计数 | 多副本部署后限流失效 |
| 超限仍继续打 LLM 再返回错误 | 钱已经花了；应在入口拒绝 |

落地时用 **Lua / MULTI** 把计数与过期绑在一起，或用带时间桶的 key + 首次 `SET … EX … NX` / `EXPIRE` 保护。

Lua 直觉（示意，不必本章背熟）：

```lua
-- 伪代码：INCR 后若无 TTL 则 EXPIRE
local c = redis.call('INCR', KEYS[1])
if c == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return c
```

#### 对照：固定窗口 vs 滑动窗口

| | 固定分钟桶（本章主推入门） | ZSET 滑动窗口 |
| --- | --- | --- |
| 实现 | `INCR` + key 含时间 | `ZADD` + 按 score 修剪 |
| 边界突刺 | 桶交界可能 2N 突发 | 更平滑 |
| 复杂度 | 低 | 较高 |
| 教学建议 | 先会这个 | 知道即可 |

HTTP 对照：超限 → **429 Too Many Requests**；可加 `Retry-After` 头（框架层后做）。

---

### 4.2 会话热缓存

#### 为什么需要「热缓存」而不是「只靠 DB」？

Agent 多轮对话里，网关/worker 可能频繁读「最近上下文摘要」。完整历史放 PG（可分页、可审计）；热路径放 Redis 加速。

职责拆分：

```text
PostgreSQL：完整消息历史、会话元数据真源
Redis：最近 N 条 / 摘要 / 当前 tool 状态等热数据
进程重启 → Redis 可空；下次读从 PG 回填
```

#### 怎么写

```python
import json

HOT_TTL = 3600


def cache_recent_messages(session_id: str, messages: list[dict]) -> None:
    key = f"agent:session:{session_id}:recent3"
    payload = json.dumps(messages[-3:], ensure_ascii=False)
    r.set(key, payload, ex=HOT_TTL)


def get_recent_messages(session_id: str) -> list[dict] | None:
    key = f"agent:session:{session_id}:recent3"
    raw = r.get(key)
    if raw is None:
        return None
    return json.loads(raw)
```

写消息时：

```text
1. 事务写入 PG（真源）
2. 删除或更新 Redis 热缓存
3. 读路径：Redis → miss 则查 PG → 回填
```

#### 跑一下

```python
msgs = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "嗨"},
    {"role": "user", "content": "缓存怎么用？"},
]
cache_recent_messages("s1", msgs)
print(get_recent_messages("s1"))

# 模拟「进程重启 / Redis flush」
r.delete("agent:session:s1:recent3")
print(get_recent_messages("s1"))  # None → 业务应回源 PG，再回填
```

思考题（练习 A2）：进程重启后，谁会丢、谁还在？

```text
Redis 热缓存：可能丢（可重建）
PG 完整历史：还在（真源）
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只写 Redis、不写 PG | 重启丢会话，客诉级事故 |
| 热缓存与 DB 长期不删不校验 | 摘要和真实最近消息不一致 |
| 把「全量历史」塞进一个 STRING | 大 key、慢网络、难 TTL 策略 |
| 多 worker 各写各的进程 dict | 用户打到另一实例就像「失忆」 |

#### 对照：会话三层

| 层 | 存什么 | 寿命 |
| --- | --- | --- |
| PG | 全量消息、审计 | 长期 |
| Redis | 最近 N 条 / 摘要 | TTL / 可删 |
| 请求内存 | 当前一次推理上下文 | 请求结束即无 |

Cookie / JWT 会话（模块 06）解决的是**认证身份**；这里的 Redis 会话缓存解决的是**对话热数据加速**。两者常一起出现，但不是同一个东西。

---

### 4.3 分布式锁雏形（了解接口即可）

#### 为什么会出现锁？

热点回源、定时任务「同一时刻只跑一个 worker」——需要互斥。Redis `SET key NX EX` 是常见雏形。

#### 怎么写 / 跑一下

```python
ok = r.set("lock:job:j1", "worker-a", nx=True, ex=30)
if ok:
    try:
        ...  # 做事
    finally:
        # 生产还应校验 value 再删，避免误删别人的锁
        r.delete("lock:job:j1")
else:
    print("someone else holds the lock")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 无 TTL 的锁 | 持有者崩溃 → 死锁 |
| 不校验 value 直接 DEL | 误删他人续约后的锁 |
| 当完整「红锁」理论方案 | 本章只建立雏形；生产要更严谨 |

#### 对照

限流是「大家都能进，但限速」；锁是「同一时刻只让一个进临界区」。别用错工具。

---

## 5. 了解即可：集群与持久化

开发阶段单机 Docker 足够；下面只建立**地图**，避免面试/排障时完全没听过名词。

### 5.1 本地先跑起来

#### 为什么先单机？

本章目标是键、TTL、结构、限流直觉。Cluster 拓扑会干扰注意力。

#### 怎么写 / 跑一下

```bash
docker run --name redis-agent -p 6379:6379 -d redis:7
```

验证：

```bash
docker exec -it redis-agent redis-cli PING
# PONG
```

Python：

```python
import redis

r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
print(r.ping())  # True
```

无 Docker 时：练习允许用内存 dict 模拟 TTL；架构图仍按「真 Redis」画。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 生产把 Redis 裸露在公网无密码 | 直接变成肉鸡/数据泄露 |
| 开发用 `FLUSHALL` 习惯带到共库环境 | 删光别人的 key |
| 以为「容器起了=数据永存」 | 默认没挂卷时删容器数据可能没了 |

#### 对照：缓存语义下的持久化

即使开了 RDB/AOF，**业务上仍应按可重建设计**。持久化是运维加分项，不是「可以把 Redis 当唯一账本」的许可证。

---

### 5.2 持久化预告：RDB / AOF

#### 为什么会听到这两个词？

进程挂了、机器重启了——Redis 能否把数据从磁盘捞回来，取决于持久化配置。

#### 怎么写（地图级）

| 机制 | 直觉 | 粗权衡 |
| --- | --- | --- |
| **RDB** | 周期性快照 | 恢复快；快照间隔内可能丢变更 |
| **AOF** | 近似写日志 | 更耐久；文件更大、重放更重 |
| 混合 | 现代版本常见组合 | 运维按合规与性能调 |

缓存场景：丢几分钟热数据通常可接受（回源 DB）。  
若误把「必须不丢」的状态只放 Redis，才需要认真做持久化 + 高可用——这时先问「为什么不放 DB」。

#### 跑一下（概念验证，不必调参）

```text
写 key → 可选触发 SAVE/BGSAVE（勿在生产随意乱来）
重启 redis → 看 key 是否还在
对照：缓存设计应假设「可能不在」
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 「开了 AOF = 永不丢」 | 仍有 fsync 策略与复制延迟窗口 |
| 缓存与「必须持久的状态」混库混 key | 运维策略互相打架 |

#### 对照

| 数据 | 更该放哪 |
| --- | --- |
| 可重建热摘要 | Redis（TTL） |
| 消息真源 | PostgreSQL |
| 两者都写 | 可以，但真源仍是 PG |

---

### 5.3 集群与高可用预告

#### 为什么以后会碰到 Cluster？

单机内存与 CPU 有上限；要水平扩展、要主从故障转移，会出现：

```text
Redis Cluster（分片）
主从复制 + 哨兵 / 托管故障转移
云厂商托管 Redis
```

#### 怎么写（先记约束，不记运维手册）

```text
Cluster：key 按槽分片；相关 key 若要同事务/同本地性，常要 hash tag
例如：{user:123}:quota 与 {user:123}:cfg 可落到同槽（语法以后查文档）
跨槽操作有限制 → 键设计阶段就要有「分片意识」
```

开发期：

```text
单机 Docker 足够练会本章全部必掌握内容
上线前再选：托管实例 / 主从 / Cluster
```

#### 跑一下（地图自问）

对每个 key 问三句：

```text
1. 丢了能否从 DB 重建？
2. 是否可能成为热点大 key？
3. 若上 Cluster，是否依赖「多 key 同槽」？
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 单机练会了就假设 Cluster 行为完全一样 | 跨槽、重定向、部分命令限制会咬人 |
| 大 key / 热 key 不治理 | 分片后仍可能打爆单个分片 |
| 用 Cluster 冒充「可靠任务队列」 | 队列语义仍要 ack；见下一章 |

#### 对照：本章边界

| 主题 | 本章 | 以后 |
| --- | --- | --- |
| STRING/HASH/LIST/SET/ZSET | ✅ 写细 | 更多命令 |
| TTL / cache-aside / 限流 | ✅ | 更复杂算法 |
| LIST+BRPOP | 仅演示 | 勿当 at-least-once |
| Cluster / RDB / AOF | 地图 | 部署与运维专项 |
| 可靠队列 | 指到下一章 | Streams / MQ |

Redis Cluster、RDB/AOF……部署期再学。开发用单机 Docker 足够。

---

## 6. 练习指引

[`exercises/07-data-persistence/04-redis-cache.md`](../../exercises/07-data-persistence/04-redis-cache.md)

建议顺序：

1. **B1～B2**：该不该缓存 + key/TTL（不动代码也能练）
2. **B3～B4**：cache-aside 与写后删
3. **A1**：分钟桶限流（真 Redis 或 FakeRedis）
4. **A2**：最近 3 条热缓存与重启语义
5. **C1**：击穿关键词脑暴（对照 3.3）

---

## 7. 小结与下一站

### 把全章收成一张图

```text
请求
  →（可选）限流：INCR 时间桶 → 超限 429
  → 读：Redis → miss → DB → 回填（EX TTL）
  → 写：DB 真源 → 删缓存
  → 会话：全量在 PG；热摘要在 Redis
  → LIST+BRPOP：只演示形状，不是可靠队列
  → Cluster/RDB/AOF：知道地图，开发先单机
```

### 自检

- [ ] 能设计合理 cache key + TTL
- [ ] 能说明缓存与 DB 的职责边界
- [ ] 能描述计数限流思路
- [ ] 能说出 stale 与脏读不是同一件事
- [ ] 能说明 LIST+BRPOP 为何不是 at-least-once

### 下一章

[`05-message-queue.md`](./05-message-queue.md) —— 长任务与异步解耦；在那里才认真讲至少一次投递与幂等。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Python ORM](./03-orm.md)
- 下一章：[消息队列基础](./05-message-queue.md)
