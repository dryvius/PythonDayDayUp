# SQL 基础

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/07-data-persistence/01-sql.md`](../../exercises/07-data-persistence/01-sql.md)

## 本章定位

- **模块目标**：掌握 SQL/ORM/缓存/队列的工程用法与取舍。
- **本章角色**：先会手写 SQL 核心操作——CRUD、JOIN、索引直觉、事务。ORM 再封装，不能替代理解。
- **和 Agent**：会话消息、用户、工具调用记录、知识库文档元数据，几乎都落在表里。

## 学习目标

1. 独立写出增删改查语句。
2. 用 JOIN 关联多表，理解主键/外键直觉。
3. 知道索引解决什么、不能解决什么。
4. 理解事务 ACID 中与工程最相关的部分（原子性与提交/回滚）。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | CRUD、JOIN、索引直觉、事务 | 能写、能读执行含义 |
| **建议掌握** | 聚合与子查询 | 会统计与嵌套查 |
| **了解即可** | 执行计划入门 | 会看 `EXPLAIN` 存在即可 |

---

## 1. 为什么要学

```text
users
sessions
messages
documents
tool_calls
```

Agent 平台少不了这些表。不会 SQL，排障时只能干瞪眼。

可用 SQLite 练习语法（文件型，零部署）；生产常见 PostgreSQL（下一章）。

---

## 2. 必掌握：CRUD

假设表：

```sql
CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

```sql
-- Create
INSERT INTO messages (id, session_id, role, content, created_at)
VALUES (1, 10, 'user', 'hello', '2026-01-01T00:00:00Z');

-- Read
SELECT id, role, content FROM messages WHERE session_id = 10 ORDER BY id;

-- Update
UPDATE messages SET content = 'hello!' WHERE id = 1;

-- Delete
DELETE FROM messages WHERE id = 1;
```

工程原则：

- 读生产数据先 `SELECT` 带 `WHERE`，别瞎 `UPDATE/DELETE` 全表
- 用户输入必须参数化（防 SQL 注入）；下一章/ORM 会强调

---

## 3. 必掌握：JOIN

```sql
SELECT s.id AS session_id, m.role, m.content
FROM sessions AS s
JOIN messages AS m ON m.session_id = s.id
WHERE s.user_id = 42;
```

| 类型 | 含义 |
|------|------|
| INNER JOIN | 两边都匹配才返回 |
| LEFT JOIN | 左表全保留，右无则 NULL |

Agent 例子：会话 left join 消息，即使暂无消息也列出会话。

---

## 4. 必掌握：索引直觉

索引 ≈ 书的目录：加速查找，写入时多维护成本。

```sql
CREATE INDEX idx_messages_session ON messages(session_id);
```

适合建索引：

- 高频 `WHERE` / `JOIN` 列（`session_id`、`user_id`）
- 唯一约束列

不适合盲目建：

- 极低区分度列乱建一堆
- 每次写入都很重的宽表上过量索引

没有索引时：大表按条件查可能变全表扫描 → 慢。

---

## 5. 必掌握：事务

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;   -- 成功提交
-- ROLLBACK; -- 出错回滚
```

对你最重要的两点：

1. **原子性**：一组改动要么全成，要么全不成  
2. Agent 写「消息 + 调用记录」时，常需同一事务，避免只写了一半

隔离级别、脏读等先建立「并发下事务会互相影响」的印象即可。

---

## 6. 建议掌握：聚合与子查询

```sql
SELECT role, COUNT(*) AS cnt
FROM messages
WHERE session_id = 10
GROUP BY role;

SELECT * FROM messages
WHERE session_id IN (SELECT id FROM sessions WHERE user_id = 42);
```

用于：统计某用户消息量、找出活跃会话等。

---

## 7. 了解即可：执行计划

```sql
EXPLAIN QUERY PLAN
SELECT * FROM messages WHERE session_id = 10;
```

（各数据库方言不同。）看到 “SCAN” vs “SEARCH/INDEX” 能猜是否走了索引。

---

## 8. 练习指引

[`exercises/07-data-persistence/01-sql.md`](../../exercises/07-data-persistence/01-sql.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能手写 CRUD + 条件查询
- [ ] 能写基础 JOIN
- [ ] 能解释索引与事务对 Agent 数据的意义

### 下一章

[`02-postgresql.md`](./02-postgresql.md) —— 把 SQL 落到真正常用的生产数据库。

## 导航

- 返回模块：[README](./README.md)
- 下一章：[PostgreSQL](./02-postgresql.md)
