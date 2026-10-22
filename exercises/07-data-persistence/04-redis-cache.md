# 练习：缓存与 Redis

> 对应文档：[`docs/07-data-persistence/04-redis-cache.md`](../../docs/07-data-persistence/04-redis-cache.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 无 Redis 时可用**内存 dict 模拟 TTL**（学习用）；有 Docker 则真连 Redis。
4. 建议目录：

```text
playground/07-data-persistence/04-redis-cache/
  keys.md
  cache_aside.py
  rate_limit.py
  notes.md
```

5. Python ≥ 3.11。
6. **刻意简化（必须记住）**——见 `docs/CONVENTIONS.md`：
   - Redis `LIST` + `BRPOP` 可演示入队出队
   - 它 **不是** at-least-once 投递语义
   - 真正的可靠队列还要考虑 ack、可见性超时、重试、死信等（下章消息队列继续）

---

## 热身题（建议先做）

### W1. 缓存一句话

**要求**：缓存解决的是什么问题？它通常**不能**单独当什么？

**验收**：加速/减负 vs 不能当唯一真相源（除非明确的纯缓存场景）。

---

### W2. TTL 直觉

**要求**：解释 TTL 到期后下一次读通常会发生什么（cache miss）。

**验收**：会回源或返回无数据，取决于策略。

---

### W3. Key 命名

**要求**：给「用户 42 的资料」起一个可读 key（含业务前缀）。

**验收**：形如 `user:42:profile` 这类，而不是 `data`。

---

### W4. LIST 演示 ≠ 可靠队列

**要求**：抄写并背下：

> Redis `LIST` + `BRPOP` 可用于教学演示队列，**≠ at-least-once**。

再用自己的话写一句「为什么还不够」。

**验收**：提到丢失/重复/无 ack 等之一。

---

## 基础题（必做）

### B1. 该不该缓存（书面）

各举 **2 例**（Agent 场景）：

1. 适合缓存  
2. 不适合缓存（或只适合极短 TTL）

**验收**：适合例偏「读多、可变可接受延迟」；不适合例偏「强一致金额/权限/一次性密钥」。

---

### B2. Key 设计

为下列两项设计 **key 名 + TTL**，写入 `keys.md`：

1. 用户每日 LLM 调用次数  
2. 会话热摘要  

**验收**：key 含 user/session/日期等维度；TTL 有理由（到自然日结束 / 数分钟等）。

---

### B3. 读穿（cache-aside）流程

实现或伪代码实现：

```python
def get_session_summary(session_id: str) -> str:
    ...
```

流程必须是：

1. 读缓存  
2. 命中则返回  
3. 未命中读 DB（可用假函数）  
4. 回填缓存（带 TTL）  
5. 返回  

**验收**：用注释标出 5 步；提供命中/未命中两条演示路径。

---

### B4. 一致性权衡（书面）

更新 DB 中的会话摘要后，你选择：

- **删缓存**，还是  
- **更新缓存**？

选一种，说明为什么，并写 **1 个主要风险**。

**验收**：有选择 + 风险（如并发下脏数据窗口）。

---

## 进阶题（建议至少做 1 题）

### A1. 限流计数器

实现（真 Redis 或内存模拟）：每用户每分钟最多 **5** 次，超限返回 `False`。

接口建议：

```python
def allow(user_id: str, *, limit: int = 5, window_seconds: int = 60) -> bool:
    ...
```

**验收**：第 6 次为 `False`；窗口逻辑有说明（固定窗口即可）。

---

### A2. 会话热缓存

把最近 3 条消息 JSON 存缓存；对比「进程重启后」：

- 缓存里的数据  
- DB 里的数据  

谁会丢、谁还在（书面 + 可选代码）。

**验收**：结论正确——默认缓存可丢，DB 仍在（除非你也没用持久化）。

---

## 挑战题（可选）

### C1. 缓存击穿脑暴（书面）

热点 key 过期瞬间大量请求打 DB，你会想到哪些缓解关键词？至少 4 个。

（不必实现。）

**验收**：如互斥重建、逻辑过期、永不过期+异步刷新、降级、限流等。

---

### C2. LIST + BRPOP 迷你 demo（并写清语义边界）

用 Redis（或 list 模拟）写：

- Producer：`LPUSH` 任务 JSON  
- Consumer：`BRPOP` 取出并处理  

**硬性要求**：在文件顶注释写明：

```text
# 演示用 LIST+BRPOP ≠ at-least-once。
# 进程在 BRPOP 之后、处理完成之前崩溃，可能导致消息丢失（已出队无人 ack）。
```

**验收**：能跑通一次生产消费；注释包含上述边界。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4（含 LIST≠at-least-once 默写）
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1～W4 参考答案

- W1：用空间换时间、降低源负载；通常不能替代权威存储。  
- W2：cache miss，按策略回源并可能回填。  
- W3：`user:42:profile`。  
- W4：`BRPOP` 取出即离开列表，没有「处理成功再 ack」；崩溃会丢；也不自带幂等与重试账本 → **≠ at-least-once**。

---

### B1 思路 + 参考答案

适合：

1. 会话热摘要 / 工具目录（变更不频繁）  
2. 模型名到上游配置的映射  

不适合：

1. 「是否已扣费」唯一状态（需强一致账本）  
2. 一次性 webhook 密钥或尚未轮转的 API Key  

---

### B2 思路 + 参考答案

```markdown
# keys.md

1) 用户每日 LLM 调用次数
- key: `llm:calls:{user_id}:{yyyy-mm-dd}`
- TTL: 到次日 02:00 左右（或 48h）——覆盖时区毛刺；计数也可用 INCR + EXPIRE

2) 会话热摘要
- key: `session:{session_id}:summary`
- TTL: 300s～1800s（摘要允许短暂旧数据；写路径删缓存）
```

---

### B3 思路 + 参考答案

```python
from __future__ import annotations

import time
from typing import Callable

# 极简内存缓存：value + expire_at
_STORE: dict[str, tuple[str, float]] = {}


def cache_get(key: str) -> str | None:
    item = _STORE.get(key)
    if item is None:
        return None
    value, expire_at = item
    if time.time() >= expire_at:
        _STORE.pop(key, None)
        return None
    return value


def cache_set(key: str, value: str, ttl_seconds: int) -> None:
    _STORE[key] = (value, time.time() + ttl_seconds)


def db_get_session_summary(session_id: str) -> str:
    return f"summary-for-{session_id}"


def get_session_summary(
    session_id: str,
    *,
    ttl_seconds: int = 300,
    db_get: Callable[[str], str] = db_get_session_summary,
) -> str:
    key = f"session:{session_id}:summary"

    # 1) 读缓存
    cached = cache_get(key)
    # 2) 命中
    if cached is not None:
        return cached

    # 3) 未命中读 DB
    value = db_get(session_id)
    # 4) 回填
    cache_set(key, value, ttl_seconds)
    # 5) 返回
    return value


if __name__ == "__main__":
    calls = {"n": 0}

    def counting_db(session_id: str) -> str:
        calls["n"] += 1
        return db_get_session_summary(session_id)

    a = get_session_summary("s1", db_get=counting_db)
    b = get_session_summary("s1", db_get=counting_db)
    assert a == b
    assert calls["n"] == 1  # 第二次命中缓存
    print("cache-aside ok")
```

---

### B4 思路 + 参考答案

**参考答案（选删缓存）**：更新 DB 后 `DEL` 缓存，下次读再回填。实现简单，避免「写缓存失败但 DB 已新」的分裂。  

风险：删缓存与写 DB 非原子，并发下可能出现短暂旧值回填（需要更复杂方案才能收敛）。  

若选更新缓存：读路径更快温热，但要用好「DB 与缓存双写顺序」，失败补偿更烦。

---

### A1 思路 + 参考答案

```python
from __future__ import annotations

import time

_HITS: dict[str, list[float]] = {}


def allow(user_id: str, *, limit: int = 5, window_seconds: int = 60) -> bool:
    now = time.time()
    window_key = f"{user_id}:{int(now // window_seconds)}"
    bucket = _HITS.setdefault(window_key, [])
    # 固定窗口：同一 window_key 内计数
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


if __name__ == "__main__":
    uid = "alice"
    assert [allow(uid) for _ in range(5)] == [True] * 5
    assert allow(uid) is False
    print("rate limit ok")
```

真 Redis 示意：`INCR key` + 首次 `EXPIRE 60`；超限返回 False。

---

### A2 思路 + 参考答案

热缓存：`session:{id}:recent_messages` → JSON 数组，TTL 600s。  
进程重启：内存模拟缓存必丢；Redis 若未持久化也可能丢；DB 仍在。  
结论：缓存加速，DB/权威存储保底。

---

### C1 思路 + 参考答案

关键词示例：单飞（mutex/lock）重建、逻辑过期、提前异步刷新、空值缓存防穿透、多级缓存、请求合并、降级默认值、限流、热点拆分。

---

### C2 思路 + 参考答案

```python
from __future__ import annotations

# 演示用 LIST+BRPOP ≠ at-least-once。
# 进程在 BRPOP 之后、处理完成之前崩溃，可能导致消息丢失（已出队无人 ack）。
# 需要可靠投递时请使用带 ack/可见性超时的队列语义，而不是裸 LIST。

from collections import deque

_QUEUE: deque[str] = deque()


def enqueue(job_json: str) -> None:
    _QUEUE.appendleft(job_json)  # 模拟 LPUSH


def brpop_timeout() -> str | None:
    if not _QUEUE:
        return None
    return _QUEUE.pop()  # 模拟 BRPOP（无超时等待）


def handle(job_json: str) -> None:
    print("handling", job_json)


if __name__ == "__main__":
    enqueue('{"job_id":"1","type":"agent_run"}')
    job = brpop_timeout()
    assert job is not None
    handle(job)
```

真 Redis 版可用 `redis.Redis` 的 `lpush` / `brpop`；注释边界同样必写。

```python
# 真 Redis 示意（需 redis 服务与 redis-py）
# import redis
# r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
# r.lpush("jobs", '{"job_id":"1"}')
# item = r.brpop("jobs", timeout=5)  # -> ("jobs", payload) 或 None
#
# 再次强调：这是演示入口，不是 at-least-once。
# 可靠语义需要 ack / 可见性超时 / 死信 / 幂等消费者（见消息队列章）。
```

---

## 附录：缓存与队列别混

| 能力 | 缓存（本章主线） | LIST+BRPOP 演示 | 可靠队列（下章） |
|------|------------------|-----------------|------------------|
| 主要目的 | 加速读、减负 | 教学入队出队 | 异步执行、削峰 |
| 丢了能否接受 | 通常可回源重建 | 演示可丢 | 业务常不可静默丢 |
| 重复 | 一般无所谓 | 可能重复或丢失 | 按至少一次设计 + 幂等 |
| TTL | 常见 | 不靠 TTL 表达完成 | 用 ack/重试表达完成 |

**自检**：

- [ ] 能设计带 TTL 的 key  
- [ ] 能写 cache-aside  
- [ ] 能默写：LIST+BRPOP ≠ at-least-once


---

## 附录：限流与缓存键命名规范（建议）

```text
{业务}:{实体}:{id}:{属性}[:{时间桶}]

示例：
llm:calls:alice:2026-10-22
session:s_123:summary
session:s_123:recent_messages
ratelimit:agent_run:alice:202610221530
```

原则：

1. 全小写 + 冒号分层，避免空格
2. 时间桶用 UTC 或明确时区
3. 密钥类数据不要当 key 后缀明文乱放
4. 写路径变更后优先删缓存，读路径负责回填

**口头题**：cache-aside 五步是什么？LIST+BRPOP 为什么不是 at-least-once？

### 再练一遍：TTL 过期手感

```python
import time
cache_set("k", "v", ttl_seconds=1)
assert cache_get("k") == "v"
time.sleep(1.05)
assert cache_get("k") is None
print("ttl ok")
```
