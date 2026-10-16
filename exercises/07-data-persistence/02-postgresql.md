# 练习：PostgreSQL

> 对应文档：[`docs/07-data-persistence/02-postgresql.md`](../../docs/07-data-persistence/02-postgresql.md)  
> 状态：`已完成出题` · 建议用时：45～80 分钟

若无法启动 Docker/PG：用书面题 + SQLite 近似类型完成，并在笔记标明差异。

---

## 基础题（必做）

### B1. 类型选择（书面）

为「会话 id / 用户 id / 消息正文 / 创建时间 / 扩展元数据」各选 PG 类型并一句理由。

### B2. 约束设计

写出 `chat_sessions` + `messages` 的建表 SQL（含 PK/FK/CHECK）。存 `schema.sql`。

### B3. 连接串

写出本地 `DATABASE_URL` 示例，并列出应放进 `.env` 的变量名（不要写真实密码进 git）。

### B4. 启动记录

若成功 `docker run` Postgres：把命令与如何用 `psql`/`GUI` 连通的步骤写入 `b4_notes.md`。  
若失败：写清失败原因与你的替代练习方案。

---

## 进阶题（建议）

### A1. JSONB

给 messages 增加 `metadata JSONB`，插入含 `{"model":"echo"}` 的一行，并按 `model` 查询。

### A2. 迁移思路（书面）

描述从「加一列」到「多环境应用」的 5 步流程（可点名 Alembic）。

---

## 挑战题（可选）

### C1. UUID 主键

把会话 id 改成 UUID 策略，说明优劣各 2 点。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
