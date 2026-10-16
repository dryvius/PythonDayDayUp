# 练习：Python ORM

> 对应文档：[`docs/07-data-persistence/03-orm.md`](../../docs/07-data-persistence/03-orm.md)  
> 状态：`已完成出题` · 建议用时：70～120 分钟

可用 SQLite + SQLAlchemy 完成（降低环境门槛）。目录：`playground/07-data-persistence/03-orm/`

---

## 基础题（必做）

### B1. 选型说明（书面）

为何本路线优先熟悉 SQLAlchemy 生态？列 3 条。

### B2. 模型

定义 `Message` 模型（字段至少 session_id/role/content），`create_all` 到 SQLite。

### B3. Session CRUD

插入 2 条、按 session_id 查询、更新 content、删除 1 条；注意 commit/rollback。

### B4. 迁移认知（书面）

解释：为何生产环境不能只靠 `create_all`？迁移工具解决什么？

---

## 进阶题（建议）

### A1. N+1 故事题

用伪代码展示 N+1，再写一种预加载/合并查询的伪代码修复。

### A2. Repository 草图

写一个 `MessageRepository` 类，封装 `add` / `list_by_session`，API 层不直接碰 Session 细节（可简化）。

---

## 挑战题（可选）

### C1. 与 FastAPI Depends 结合草图

画：请求 → Depends(get_db) → service → repo 的调用链（文字即可）。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
