# 练习：SQL 基础

> 对应文档：[`docs/07-data-persistence/01-sql.md`](../../docs/07-data-persistence/01-sql.md)  
> 状态：`已完成出题` · 建议用时：60～90 分钟

可用 SQLite（`sqlite3` CLI 或 Python）完成。目录：`playground/07-data-persistence/01-sql/`

---

## 基础题（必做）

### B1. 建表 + CRUD

建 `messages(id, session_id, role, content, created_at)`，完成插入 3 行、按 session 查询、更新 1 行、删除 1 行。把 SQL 存 `b1.sql`。

### B2. JOIN

再建 `sessions(id, user_id, title)`，插入数据，写 JOIN 查出某 `user_id` 的全部消息。

### B3. 索引

为 `messages(session_id)` 建索引；书面 3 行说明为何对该列建索引。

### B4. 事务

写一个事务脚本：插入两条消息，中间故意失败（可用错误 SQL 或注释模拟），演示需要 ROLLBACK 的场景说明（成功路径 COMMIT）。

---

## 进阶题（建议）

### A1. 聚合

统计每个 `role` 的消息数。

### A2. 子查询

列出「消息数 ≥ 2」的 `session_id`。

---

## 挑战题（可选）

### C1. SQL 注入认知

写错误拼接 vs 参数绑定的对比说明（Python `sqlite3` 占位符），不要真去攻击任何系统。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
