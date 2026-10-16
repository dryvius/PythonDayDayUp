# 练习：缓存与 Redis

> 对应文档：[`docs/07-data-persistence/04-redis-cache.md`](../../docs/07-data-persistence/04-redis-cache.md)  
> 状态：`已完成出题` · 建议用时：45～75 分钟

无 Redis 可用内存 dict 模拟 TTL（学习用）；有 Docker 则真连 Redis。

---

## 基础题（必做）

### B1. 该不该缓存（书面）

各举 2 例：适合缓存 / 不适合缓存的 Agent 数据。

### B2. Key 设计

为「用户每日 LLM 调用次数」「会话热摘要」设计 key 名与 TTL，写进 `keys.md`。

### B3. 读穿流程

用伪代码写：`get_session_summary(session_id)` 的 cache-aside（读缓存 → DB → 回填）。

### B4. 一致性权衡（书面）

更新 DB 后你选择「删缓存」还是「更新缓存」？为什么？（说明一种即可，给风险）

---

## 进阶题（建议）

### A1. 限流计数器

实现（真 Redis 或模拟）：每用户每分钟最多 5 次，超限返回 False。

### A2. 会话热缓存

把最近 3 条消息 JSON 存缓存；进程重启后说明何者会丢、何者还在（对比 DB）。

---

## 挑战题（可选）

### C1. 缓存击穿脑暴

热点 key 过期瞬间大量请求打 DB，你会想到哪些缓解关键词？（不必实现）

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
