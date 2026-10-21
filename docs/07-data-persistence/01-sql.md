# SQL 基础

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（有前端/本地存储经验可更快；CRUD + JOIN + 事务建议动手敲一遍）  
> 对应练习：[`exercises/07-data-persistence/01-sql.md`](../../exercises/07-data-persistence/01-sql.md)

## 本章定位

- **模块目标**：掌握 SQL/ORM/缓存/队列的工程用法与取舍。
- **本章角色**：先会手写 SQL 核心操作——CRUD、JOIN、索引直觉、事务。ORM 再封装，不能替代理解。
- **和 Agent**：会话、消息、用户、工具调用记录、知识库文档元数据，几乎都落在表里；排障时最终往往要落到「这条 SQL 查/写了什么」。
- **你的优势**：若熟悉前端的 `localStorage` / IndexedDB / REST 资源路径，可把「表 = 资源集合、行 = 一条记录、WHERE = 过滤条件」对照迁移；本章盯住差异与工程坑，而不是背方言手册。

## 学习目标（学完应能做到）

1. 独立写出增删改查语句，并知道生产环境里「先 SELECT、再改删」的纪律。
2. 用 JOIN 关联多表，说清主键 / 外键直觉，以及 INNER / LEFT 的结果差异。
3. 解释索引解决什么、不能解决什么；能给高频过滤列建索引。
4. 理解事务里与工程最相关的部分：原子性、COMMIT / ROLLBACK；能说明 Agent「消息 + 工具调用」为何常要同事务。
5. （建议）能写聚合与子查询做简单统计；知道 `EXPLAIN` 能帮你判断是否走了索引。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | CRUD、JOIN、索引直觉、事务 | 能写、能读执行含义、能做题 |
| **建议掌握** | 聚合与子查询 | 会统计与嵌套查，不必一次背全语法 |
| **了解即可** | 执行计划入门 | 会看 `EXPLAIN` 存在即可；方言差异下一章再补 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要 SQL？

Agent 平台少不了这些「真源」表：

```text
users          谁在用
sessions       一次对话会话
messages       会话里的每条消息（user / assistant / tool …）
documents      知识库文档元数据
tool_calls     工具调用记录（入参、出参、耗时、是否成功）
```

没有持久化时，进程一重启，会话历史、工具结果、用户偏好全没了——只能做「无状态 Demo」。

ORM（下一章之后会学）会帮你用 Python 对象操作表，但：

1. 排障日志里经常是**原始 SQL**
2. 慢查询要看**索引是否命中**
3. 复杂报表 / 迁移脚本仍要手写 SQL

所以本章不是「背关键字」，而是练三种肌肉：

1. **把业务数据装进表结构**（会话 / 消息怎么拆表）
2. **用 SQL 表达读改删**（带条件、带关联）
3. **用索引与事务保正确与性能**（别全表扫、别只写一半）

#### 本章用什么练？

**SQLite**：文件型数据库，零部署，适合练语法。

```text
Python 自带 sqlite3 模块
也可用 sqlite3 CLI：sqlite3 playground.db
```

生产常见 **PostgreSQL**（下一章）。语法主体互通；差异点（类型名、部分函数、`EXPLAIN` 形态）后面再对齐即可。

#### 应用层对照（先建立地图）

| 你在前端 / API 里做的事 | SQL 大致对应 |
| --- | --- |
| `GET /sessions/10/messages` | `SELECT … WHERE session_id = 10` |
| `POST` 一条消息 | `INSERT INTO messages …` |
| `PATCH` 改 content | `UPDATE … SET content = … WHERE id = ?` |
| `DELETE` 某条消息 | `DELETE … WHERE id = ?` |
| 列表页「用户 + 其会话」 | `JOIN` |
| 列表按时间排序 | `ORDER BY created_at` |
| 分页 `limit/offset` | `LIMIT / OFFSET`（方言细节略） |

可以先记一句：

> SQL 是声明「要什么数据」；应用层决定「何时发、参数从哪来、结果怎么展示」。

---

## 2. 必掌握：CRUD

这一节会刻意写细——增删改查是后面 JOIN、索引、事务、ORM 的共同底座。  
Agent 直觉：把 `messages` 想成「一条会话里的消息数组」，只是落在表里而不是 Python `list`。

### 2.1 先有一张表：CREATE TABLE

#### 为什么需要建表？

没有表结构，数据库不知道一行有哪些列、什么类型、谁是主键。建表 = 约定「消息长什么样」。

#### 怎么写

```sql
CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

列直觉：

| 列 | 含义 | Agent 侧 |
| --- | --- | --- |
| `id` | 主键，唯一标识一行 | 消息 ID |
| `session_id` | 属于哪次会话 | 对应 `sessions.id` |
| `role` | 说话角色 | `user` / `assistant` / `system` / `tool` |
| `content` | 正文 | 提示词或模型回复 |
| `created_at` | 创建时间 | 排序、审计 |

配套的会话表（后面 JOIN 会用到）：

```sql
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  title TEXT NOT NULL
);
```

#### 跑一下（SQLite）

用 CLI 或 Python 均可。Python 最小示例：

```python
import sqlite3
from pathlib import Path

db = Path("playground.db")
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.executescript(
    """
    DROP TABLE IF EXISTS messages;
    DROP TABLE IF EXISTS sessions;

    CREATE TABLE sessions (
      id INTEGER PRIMARY KEY,
      user_id INTEGER NOT NULL,
      title TEXT NOT NULL
    );

    CREATE TABLE messages (
      id INTEGER PRIMARY KEY,
      session_id INTEGER NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """
)
conn.commit()
conn.close()
print("tables ready")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 忘记主键 | 难唯一定位一行；UPDATE/DELETE 容易误伤 |
| `role` / `content` 允许 NULL 却不处理 | 应用层要处处判空；Agent 拼 prompt 时易炸 |
| 时间用随意字符串格式 | 排序与比较变脆；教学可用 ISO8601 文本，生产多用时间戳类型 |

#### 前端 / 应用层对照

```typescript
// 前端类型直觉 ≈ 表行
type Message = {
  id: number
  sessionId: number
  role: "user" | "assistant" | "system" | "tool"
  content: string
  createdAt: string
}
```

表是共享真源；TS 类型是应用侧的契约。两边字段要对齐，但**权威在数据库约束**（`NOT NULL`、主键），不是前端接口。

---

### 2.2 Create：INSERT

#### 为什么需要 INSERT？

用户发了一句「hello」，Agent 要把这条 `user` 消息落库；模型回复后再插一条 `assistant`。没有 INSERT，会话无法续聊。

#### 怎么写

```sql
INSERT INTO messages (id, session_id, role, content, created_at)
VALUES (1, 10, 'user', 'hello', '2026-01-01T00:00:00Z');
```

一次插多行：

```sql
INSERT INTO messages (id, session_id, role, content, created_at) VALUES
  (1, 10, 'user', 'hello', '2026-01-01T00:00:00Z'),
  (2, 10, 'assistant', 'Hi!', '2026-01-01T00:00:01Z'),
  (3, 10, 'user', '写个排序', '2026-01-01T00:00:02Z');
```

主键自增时（SQLite 的 `INTEGER PRIMARY KEY` 常可省略 `id`）：

```sql
INSERT INTO messages (session_id, role, content, created_at)
VALUES (10, 'user', 'hello', '2026-01-01T00:00:00Z');
```

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
cur = conn.cursor()

cur.execute(
    """
    INSERT INTO sessions (id, user_id, title)
    VALUES (10, 42, 'demo chat')
    """
)

cur.execute(
    """
    INSERT INTO messages (id, session_id, role, content, created_at)
    VALUES (?, ?, ?, ?, ?)
    """,
    (1, 10, "user", "hello", "2026-01-01T00:00:00Z"),
)
conn.commit()
conn.close()
```

注意：这里用了 `?` **参数占位**，而不是把用户输入拼进字符串——防 SQL 注入的第一步（练习 C1 会强化）。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 列数与 VALUES 个数不一致 | 语法错误 |
| 主键重复插入 | `UNIQUE` / 主键冲突 |
| 字符串拼接 SQL：`f"... '{user_input}'"` | SQL 注入风险；永远参数化 |
| 插完忘记 `commit`（Python sqlite3） | 重启后数据像「没写进去」 |

#### 前端 / 应用层对照

```text
POST /sessions/10/messages
Body: { "role": "user", "content": "hello" }

后端 → INSERT INTO messages (...) VALUES (...)
响应 → 返回新行 id / 整行 JSON
```

前端不写 SQL；但你要能读懂后端最终落的是哪条 INSERT。

---

### 2.3 Read：SELECT

#### 为什么需要 SELECT？

续聊时要把历史消息按顺序读出，拼进 prompt。列表页要展示某会话的全部消息。排障时你也会 `SELECT` 核对「库里到底有没有那条」。

#### 怎么写

查某会话全部消息（按 id 顺序，近似时间序）：

```sql
SELECT id, role, content
FROM messages
WHERE session_id = 10
ORDER BY id;
```

只取需要的列，而不是习惯性 `SELECT *`（宽表 / 大字段时尤其重要）：

```sql
SELECT id, role, content FROM messages WHERE session_id = 10;
```

常用子句直觉：

| 子句 | 作用 | Agent 例子 |
| --- | --- | --- |
| `WHERE` | 过滤行 | 只要 session 10 |
| `ORDER BY` | 排序 | 按时间 / id 拼历史 |
| `LIMIT` | 限制条数 | 只要最近 N 条 |
| `OFFSET` | 跳过前几条 | 简易分页 |

最近 20 条（教学写法）：

```sql
SELECT id, role, content
FROM messages
WHERE session_id = 10
ORDER BY id DESC
LIMIT 20;
```

（应用层若要「正序拼 prompt」，可在内存里再反转，或用子查询包一层。）

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
conn.row_factory = sqlite3.Row  # 可用列名取字段
cur = conn.cursor()

cur.execute(
    """
    SELECT id, role, content
    FROM messages
    WHERE session_id = ?
    ORDER BY id
    """,
    (10,),
)

for row in cur.fetchall():
    print(dict(row))

conn.close()
```

期望类似：

```text
{'id': 1, 'role': 'user', 'content': 'hello'}
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 忘记 `WHERE` 就查生产大表 | 扫全表、拖垮库、泄漏他人数据 |
| 字符串比较大小写 / 空格敏感未约定 | 「User」与「user」对不上 |
| `ORDER BY` 缺失却假设「插入顺序」 | 并发插入后顺序不稳定；要用明确排序键 |
| 把 `=` 写成赋值思维 | SQL 的 `=` 在 `WHERE` 里是比较 |

#### 前端 / 应用层对照

```text
GET /sessions/10/messages?limit=20

≈ SELECT … WHERE session_id = 10 ORDER BY id LIMIT 20
```

前端的 `messages.filter(m => m.sessionId === 10)` 是**内存过滤**；有持久化后，过滤应尽量下推到 SQL（数据量大时更明显）。

---

### 2.4 Update：UPDATE

#### 为什么需要 UPDATE？

用户编辑了未发送的草稿；或你要修正一条错误落库的 `content`；或给会话改 `title`。改已有行用 UPDATE，而不是再插一行冒充「同一条」。

#### 怎么写

```sql
UPDATE messages
SET content = 'hello!'
WHERE id = 1;
```

改多列：

```sql
UPDATE sessions
SET title = '排序问题讨论'
WHERE id = 10;
```

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
cur = conn.cursor()

cur.execute(
    "UPDATE messages SET content = ? WHERE id = ?",
    ("hello!", 1),
)
print("rows affected:", cur.rowcount)
conn.commit()
conn.close()
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| **忘记 WHERE** | 整表 content 全被改掉——灾难级误操作 |
| WHERE 条件太宽 | 误更新同 session 多行 |
| 不先 SELECT 确认目标行 | 改错 id；生产习惯：先查再改 |
| 用 UPDATE 表达「追加新消息」 | 语义错了；新消息应 INSERT |

工程纪律（务必记住）：

```text
1. SELECT … WHERE id = ?     -- 确认要改的就是它
2. UPDATE … WHERE id = ?     -- 带主键或足够窄的条件
3. 再 SELECT 核对（重要变更）
```

#### 前端 / 应用层对照

```text
PATCH /messages/1  { "content": "hello!" }
→ UPDATE messages SET content = ? WHERE id = ?
```

乐观锁、版本号等进阶手段本章不展开；先养成「条件必须够窄」。

---

### 2.5 Delete：DELETE

#### 为什么需要 DELETE？

用户撤回一条消息；清理测试数据；合规要求删除某会话下全部内容。DELETE 删的是行，不是「把 content 置空」（那是 UPDATE）。

#### 怎么写

```sql
DELETE FROM messages WHERE id = 1;
```

删某会话全部消息：

```sql
DELETE FROM messages WHERE session_id = 10;
```

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
cur = conn.cursor()

cur.execute("DELETE FROM messages WHERE id = ?", (1,))
print("rows affected:", cur.rowcount)
conn.commit()
conn.close()
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| **忘记 WHERE** | 清空整张表 |
| 只删 messages、忘关联数据 | sessions / tool_calls 变孤儿行（或外键阻止删除） |
| 硬删除 vs 软删除未约定 | 产品要「可恢复」时应用 `deleted_at`，而不是真 DELETE |

生产常见软删除直觉（了解形状即可）：

```sql
-- 概念示例：多一列 deleted_at，查询时过滤
UPDATE messages
SET deleted_at = '2026-01-01T12:00:00Z'
WHERE id = 1;

SELECT * FROM messages
WHERE session_id = 10 AND deleted_at IS NULL;
```

#### 前端 / 应用层对照

```text
DELETE /messages/1
→ DELETE FROM messages WHERE id = ?
```

和前端从数组 `splice` 掉一项不同：数据库删除是持久的，刷新后仍不在。

---

### 2.6 CRUD 合在一起：Agent 会话最小闭环

心智图：

```text
创建会话     → INSERT sessions
用户发言   → INSERT messages (role=user)
模型回复   → INSERT messages (role=assistant)
加载历史   → SELECT messages WHERE session_id = ? ORDER BY id
改标题     → UPDATE sessions SET title = ? WHERE id = ?
清空会话   → DELETE messages WHERE session_id = ?
```

这一节结束时，你应能不看笔记写出：`INSERT` / `SELECT … WHERE` / `UPDATE … WHERE` / `DELETE … WHERE`，并口头解释「为什么 WHERE 不能省」。

---

## 3. 必掌握：JOIN

单表 CRUD 够用「一个会话里的消息」；一旦要「某用户的所有消息」或「会话标题 + 最近一条」，就需要把表关联起来。

### 3.1 主键 / 外键直觉

#### 为什么需要关联键？

`messages.session_id` 指向 `sessions.id`：消息属于会话。这就是**外键直觉**（即使你暂时没写 `FOREIGN KEY` 约束，语义上也在关联）。

```text
sessions.id  ←──  messages.session_id
   (主键)              (外键侧)
```

| 概念 | 含义 | 例子 |
| --- | --- | --- |
| 主键 PRIMARY KEY | 表内唯一标识一行 | `sessions.id`、`messages.id` |
| 外键（逻辑/约束） | 引用另一表主键 | `messages.session_id → sessions.id` |

Agent 表还会出现：`tool_calls.message_id → messages.id`、`documents.user_id → users.id` 等。

#### 怎么写（先有数据）

```sql
INSERT INTO sessions (id, user_id, title) VALUES
  (10, 42, 'demo chat'),
  (11, 42, '另一会话'),
  (12, 7,  '别人的会话');

INSERT INTO messages (id, session_id, role, content, created_at) VALUES
  (1, 10, 'user', 'hello', '2026-01-01T00:00:00Z'),
  (2, 10, 'assistant', 'Hi!', '2026-01-01T00:00:01Z'),
  (3, 11, 'user', 'hi again', '2026-01-01T01:00:00Z');
```

### 3.2 INNER JOIN

#### 为什么需要 JOIN？

你要从「用户 id」查到「消息正文」。消息表没有 `user_id`，但会话表有——需要：

```text
users / sessions / messages 用键拼起来
```

#### 怎么写

```sql
SELECT
  s.id AS session_id,
  s.title,
  m.role,
  m.content
FROM sessions AS s
JOIN messages AS m
  ON m.session_id = s.id
WHERE s.user_id = 42
ORDER BY s.id, m.id;
```

`JOIN` 默认常指 **INNER JOIN**：两边都匹配才返回。

```text
sessions(10) ──匹配── messages(1,2)
sessions(11) ──匹配── messages(3)
sessions(12) 无 messages → INNER 时不会出现
```

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute(
    """
    SELECT s.id AS session_id, s.title, m.role, m.content
    FROM sessions AS s
    JOIN messages AS m ON m.session_id = s.id
    WHERE s.user_id = ?
    ORDER BY s.id, m.id
    """,
    (42,),
)

for row in cur.fetchall():
    print(dict(row))

conn.close()
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `ON` 条件写错列 | 笛卡尔积爆炸或结果为空 |
| 多表同名列不写别名 | `id` 歧义报错 |
| 用 WHERE 做过滤、却漏了 JOIN 条件 | 旧式写法易漏；推荐显式 `ON` |

### 3.3 LEFT JOIN

#### 为什么需要 LEFT JOIN？

「列出某用户全部会话，即使还没有消息」——INNER 会丢掉空会话；LEFT 保留左表。

#### 怎么写

```sql
SELECT
  s.id AS session_id,
  s.title,
  m.id AS message_id,
  m.content
FROM sessions AS s
LEFT JOIN messages AS m
  ON m.session_id = s.id
WHERE s.user_id = 42
ORDER BY s.id, m.id;
```

空会话时，`m.*` 列为 `NULL`。

#### 跑一下（构造空会话）

```sql
INSERT INTO sessions (id, user_id, title)
VALUES (13, 42, '还没说话');
```

再跑上面的 `LEFT JOIN`：应看到 `session_id = 13` 且 `message_id` / `content` 为 NULL。

#### INNER vs LEFT（务必能口述）

| 类型 | 含义 | Agent 例子 |
| --- | --- | --- |
| INNER JOIN | 两边都匹配才返回 | 只要「确实有消息」的会话内容 |
| LEFT JOIN | 左表全保留，右无则 NULL | 会话列表页：空会话也要显示 |

还有 RIGHT / FULL，教学阶段少用；把 INNER + LEFT 用稳即可。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 在 LEFT JOIN 后对右表列写 `WHERE m.role = 'user'` | 常把「右表为空」的行滤掉，效果退化成 INNER |
| 需要「左保留」却用了 INNER | 空会话从列表消失，产品表现为「丢会话」 |

过滤右表条件时，放进 `ON` 或先子查询，再决定是否 LEFT——先建立「WHERE 会杀掉 NULL 侧」的直觉。

#### 前端 / 应用层对照

```text
// 前端常做两步请求或聚合 DTO：
GET /users/42/sessions
GET /sessions/10/messages

// 一次 SQL JOIN 可在服务端拼成：
[{ sessionId, title, messages: [...] }]
```

API 可以拆请求；数据库侧仍要会 JOIN，便于报表、管理后台、批量导出。

---

## 4. 必掌握：索引直觉

### 4.1 索引是什么

#### 为什么需要索引？

`WHERE session_id = 10` 在小表上很快；消息上百万行后，没有索引就可能**全表扫描**——每一行都看一遍。

索引 ≈ 书的目录：按某列快速定位到行，代价是占用空间，且写入时要维护目录。

#### 怎么写

```sql
CREATE INDEX idx_messages_session ON messages(session_id);
```

常见命名：`idx_<表>_<列>`。

唯一约束也会带索引能力（概念上）：

```sql
-- 概念：邮箱唯一（具体语法随库略有差异）
-- CREATE UNIQUE INDEX idx_users_email ON users(email);
```

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
cur = conn.cursor()
cur.execute(
    "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)"
)
conn.commit()

# SQLite：看计划（详见第 7 节）
cur.execute(
    "EXPLAIN QUERY PLAN SELECT * FROM messages WHERE session_id = 10"
)
print(cur.fetchall())
conn.close()
```

有索引时，计划里更常看到对索引的 SEARCH；没有时可能是 SCAN（名称随版本略有差异）。

#### 适合建索引

- 高频 `WHERE` / `JOIN` 列：`session_id`、`user_id`、`message_id`
- 唯一业务键：邮箱、外部系统 id
- 排序+过滤常一起出现的列（进阶：联合索引，先建立「有这回事」）

#### 不适合盲目建

- 区分度极低的列（例如只有 `Y/N`）上堆很多索引
- 写多读少、且每次写入都很重的宽表上过量索引
- 「每一列都建一个」——写入变慢、占用膨胀，收益却小

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为有索引就一定快 | 条件函数包裹列、类型不匹配、选择性太差仍可能不走索引 |
| 只建索引从不看计划 | 慢查询依旧；要用 EXPLAIN 验证 |
| 忽略写入成本 | 每次 INSERT/UPDATE/DELETE 都要维护索引 |

#### Agent 对照

```text
高频路径：
  按 session_id 拉历史      → messages(session_id) 索引很值
  按 user_id 列会话          → sessions(user_id) 索引很值
  按 content 模糊搜全文      → 普通 BTree 索引不擅长；后面全文/向量另说
```

口诀：

> 先问「最热的过滤列是谁」，再决定索引；别先堆索引再猜。

#### 前端 / 应用层对照

前端给列表做 `Array.find` 不需要索引；数据库是磁盘上的大量行，索引是「服务端的加速目录」。把「前端 filter」和「SQL WHERE + 索引」分清层级。

---

## 5. 必掌握：事务

### 5.1 什么是事务

#### 为什么需要事务？

Agent 常要**连续写多行**，且必须一起成功或一起失败，例如：

```text
插入 assistant 消息
同时插入 tool_calls 记录
更新 session 的 updated_at
```

若插完消息后进程崩溃，工具记录没写上——状态会撕裂：UI 显示「已回复」，审计却找不到调用。

事务把多步改动绑成一体：**要么全成，要么全不成**。

#### 怎么写

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;     -- 成功提交
-- ROLLBACK; -- 出错则回滚
```

Agent 味道更浓的例子：

```sql
BEGIN;

INSERT INTO messages (id, session_id, role, content, created_at)
VALUES (100, 10, 'assistant', '调用搜索中…', '2026-01-01T00:00:10Z');

INSERT INTO tool_calls (id, message_id, tool_name, arguments, status)
VALUES (1, 100, 'search', '{"q":"sql index"}', 'running');

COMMIT;
```

任一步失败 → `ROLLBACK`，两条都不留下「成功提交」的半成品（具体可见性还受隔离级别影响；教学先抓原子性）。

#### 跑一下（Python sqlite3）

```python
import sqlite3

conn = sqlite3.connect("playground.db")
cur = conn.cursor()

try:
    cur.execute("BEGIN")
    cur.execute(
        """
        INSERT INTO messages (id, session_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (100, 10, "assistant", "调用搜索中…", "2026-01-01T00:00:10Z"),
    )
    # 模拟后半段失败：故意写一张不存在的表
    cur.execute(
        "INSERT INTO tool_calls (id, message_id) VALUES (1, 100)"
    )
    conn.commit()
except Exception as e:
    conn.rollback()
    print("rolled back because:", e)
finally:
    conn.close()
```

先建 `tool_calls` 再跑成功路径；或保留失败演示，确认 `messages` 里没有「半提交」的 100（在 SQLite 默认事务行为下理解 rollback）。

#### 对你最重要的两点

1. **原子性**：一组改动要么全成，要么全不成  
2. Agent 写「消息 + 调用记录 / 状态」时，常需同一事务，避免只写了一半

ACID 其余部分先建立地图即可：

| 字母 | 含义（极简） | 现在要记住的 |
| --- | --- | --- |
| A Atomicity | 原子性 | BEGIN/COMMIT/ROLLBACK |
| C Consistency | 一致性 | 约束不被破坏 |
| I Isolation | 隔离性 | 并发事务会互相影响；级别以后再挖 |
| D Durability | 持久性 | COMMIT 后崩溃也不该丢（引擎保证） |

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 多步写却不开事务 | 中途失败留下半成品 |
| 长事务里做 HTTP / LLM 调用 | 锁持有过久，拖垮并发 |
| 以为「每个 statement 自动提交」在所有驱动上行为一致 | 要查连接的 autocommit 设置 |
| 失败后继续用同一连接乱写 | 先 rollback，再决定重试 |

工程习惯：

```text
事务里：只做数据库读写
事务外：调 LLM、调 HTTP、读文件
需要「最终一致」时：事务写状态 + 队列异步（模块后章）
```

#### 前端 / 应用层对照

前端没有真正的多行 ACID；最多乐观 UI 回滚。  
服务端事务才是「扣库存 + 写订单」或「消息 + tool_call」的正确性边界。

```text
前端：点发送 → 乐观插入气泡
后端：BEGIN → INSERT message → INSERT tool_call → COMMIT
失败：ROLLBACK → API 4xx/5xx → 前端撤气泡或标错误
```

---

## 6. 建议掌握：聚合与子查询

统计与嵌套查询在管理后台、用量分析、评测集筛选里很常见；时间紧可先会读、会改模板。

### 6.1 聚合：COUNT / GROUP BY

#### 为什么需要聚合？

问题从「列出行」变成「数一数」：某会话里 user / assistant 各多少条？某用户总消息量？

#### 怎么写

```sql
SELECT role, COUNT(*) AS cnt
FROM messages
WHERE session_id = 10
GROUP BY role;
```

常用聚合：

| 函数 | 含义 |
| --- | --- |
| `COUNT(*)` | 行数 |
| `COUNT(col)` | 非 NULL 的 col 个数 |
| `SUM` / `AVG` / `MAX` / `MIN` | 求和 / 均 / 最大 / 最小 |

`WHERE` 在分组前过滤；`HAVING` 在分组后过滤（先混个脸熟）：

```sql
SELECT session_id, COUNT(*) AS cnt
FROM messages
GROUP BY session_id
HAVING COUNT(*) >= 2;
```

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
for row in conn.execute(
    """
    SELECT role, COUNT(*) AS cnt
    FROM messages
    WHERE session_id = 10
    GROUP BY role
    """
):
    print(row)
conn.close()
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `SELECT` 了非聚合列却没进 `GROUP BY` | 多数引擎报错或结果不确定 |
| 用 `WHERE cnt >= 2` 过滤聚合结果 | 应使用 `HAVING` |
| `COUNT` 错列导致 NULL 行被忽略 | 分清 `COUNT(*)` 与 `COUNT(col)` |

### 6.2 子查询

#### 为什么需要子查询？

「先找出某用户的全部 session id，再查这些会话的消息」——可以 JOIN，也可以先嵌一套查询。

#### 怎么写

```sql
SELECT *
FROM messages
WHERE session_id IN (
  SELECT id FROM sessions WHERE user_id = 42
);
```

找出「消息数 ≥ 2」的会话（和练习 A2 对齐）：

```sql
SELECT session_id
FROM messages
GROUP BY session_id
HAVING COUNT(*) >= 2;
```

或写成子查询嵌套：

```sql
SELECT *
FROM sessions
WHERE id IN (
  SELECT session_id
  FROM messages
  GROUP BY session_id
  HAVING COUNT(*) >= 2
);
```

很多子查询也能改写为 JOIN；先求**结果正确**，再谈哪种更好读、更好优化。

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
rows = conn.execute(
    """
    SELECT id, role, content
    FROM messages
    WHERE session_id IN (
      SELECT id FROM sessions WHERE user_id = ?
    )
    ORDER BY id
    """,
    (42,),
).fetchall()
print(rows)
conn.close()
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 子查询返回多列却用于 `IN` | 语法/语义错误；`IN` 侧通常一列 |
| 相关子查询写太重 | 大表上可能很慢；以后用 JOIN / 窗口函数优化 |
| 把「业务上的且」写成错误嵌套 | 先用自然语言写清集合，再落 SQL |

#### Agent / 应用层对照

```text
聚合：用量面板「今日消息数」「每角色占比」
子查询：评测集「只导出消息数 ≥ N 的会话」
前端：charts 吃的是聚合后的 JSON，不是原始百万行
```

---

## 7. 了解即可：执行计划入门

### 7.1 为什么要看 EXPLAIN？

你建了索引，但查询仍慢——可能根本没走索引。执行计划告诉你引擎**打算怎么跑**这条 SQL。

本章目标：知道有 `EXPLAIN` 这回事；能区分「像在扫全表」vs「像在用索引找」。方言细节放到 PostgreSQL 章加深。

#### 怎么写（SQLite）

```sql
EXPLAIN QUERY PLAN
SELECT * FROM messages WHERE session_id = 10;
```

#### 跑一下

```python
import sqlite3

conn = sqlite3.connect("playground.db")
cur = conn.cursor()
cur.execute(
    "EXPLAIN QUERY PLAN SELECT * FROM messages WHERE session_id = 10"
)
for row in cur.fetchall():
    print(row)
conn.close()
```

解读直觉（不要死记关键字，抓对比）：

| 计划里常看到的信号 | 粗直觉 |
| --- | --- |
| SCAN TABLE | 可能在扫表（大表上危险信号） |
| SEARCH / USING INDEX | 更像走了索引定位 |

各数据库输出格式不同：PostgreSQL 常用 `EXPLAIN` / `EXPLAIN ANALYZE`；MySQL 也有自己的 `EXPLAIN`。看见不同不要慌——**问题相同：有没有用上合适索引**。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只看感觉「应该走索引」 | 以计划为准 |
| 在空表 / 极小表上结论外推 | 优化器对小表可能直接扫；要用接近真实的数据量感受 |
| 把「了解 EXPLAIN」当成「会做 DBA」 | 本章只要会打开计划、建立 SCAN vs INDEX 对立 |

#### 和索引节的闭环

```text
慢查询
  → EXPLAIN 看是否 SCAN
  → 检查 WHERE/JOIN 列有无索引
  → CREATE INDEX
  → 再 EXPLAIN 对比
```

---

## 8. 常见坑（全章对照表）

把前面易错点收成一张「出门前核对」表：

| # | 坑 | 正确习惯 |
|---|----|----------|
| 1 | `UPDATE`/`DELETE` 漏 `WHERE` | 先 `SELECT` 确认；条件尽量落到主键 |
| 2 | 字符串拼接用户输入 | 永远参数化（`?` / `%s` 等占位） |
| 3 | 用 INNER 当会话列表 | 空会话要用 `LEFT JOIN`（或先查 sessions） |
| 4 | LEFT JOIN 后再 `WHERE` 右表列 | 可能退化成 INNER；条件放对位置 |
| 5 | 无索引却怪框架慢 | 给高频 `session_id`/`user_id` 建索引并 `EXPLAIN` |
| 6 | 多步写不加事务 | `BEGIN`…成功 `COMMIT` / 失败 `ROLLBACK` |
| 7 | 事务里调 LLM | 事务只包住 DB；长 I/O 放外面 |
| 8 | `SELECT *` 习惯性用在宽表 | 只取需要的列 |
| 9 | 假设行顺序等于插入顺序 | 明确 `ORDER BY` |
| 10 | 把 ORM 当可不学 SQL 的理由 | 排障与慢查询仍要读 SQL |

---

## 9. 综合小例子：会话 + 消息最小模型

下面把本章主线串成一段可跑脚本（SQLite）。建议保存在：

```text
playground/07-data-persistence/01-sql/
```

```python
"""最小 Agent 会话表：建表 → CRUD → JOIN → 索引 → 事务 → 聚合。"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "agent_demo.db"


def main() -> None:
    if DB.exists():
        DB.unlink()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE sessions (
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL,
          title TEXT NOT NULL
        );

        CREATE TABLE messages (
          id INTEGER PRIMARY KEY,
          session_id INTEGER NOT NULL,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TEXT NOT NULL
        );

        CREATE INDEX idx_messages_session ON messages(session_id);
        CREATE INDEX idx_sessions_user ON sessions(user_id);
        """
    )

    # CREATE
    cur.execute(
        "INSERT INTO sessions (id, user_id, title) VALUES (?, ?, ?)",
        (10, 42, "demo chat"),
    )
    cur.executemany(
        """
        INSERT INTO messages (id, session_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, 10, "user", "hello", "2026-01-01T00:00:00Z"),
            (2, 10, "assistant", "Hi!", "2026-01-01T00:00:01Z"),
        ],
    )
    conn.commit()

    # READ
    rows = cur.execute(
        """
        SELECT id, role, content FROM messages
        WHERE session_id = ? ORDER BY id
        """,
        (10,),
    ).fetchall()
    print("history:", [dict(r) for r in rows])

    # UPDATE
    cur.execute(
        "UPDATE messages SET content = ? WHERE id = ?",
        ("hello!", 1),
    )
    conn.commit()

    # JOIN
    joined = cur.execute(
        """
        SELECT s.title, m.role, m.content
        FROM sessions AS s
        JOIN messages AS m ON m.session_id = s.id
        WHERE s.user_id = ?
        ORDER BY m.id
        """,
        (42,),
    ).fetchall()
    print("join:", [dict(r) for r in joined])

    # 事务：消息 +（模拟）状态同进同退
    try:
        cur.execute("BEGIN")
        cur.execute(
            """
            INSERT INTO messages (id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (3, 10, "user", "再问一句", "2026-01-01T00:00:02Z"),
        )
        cur.execute(
            "UPDATE sessions SET title = ? WHERE id = ?",
            ("demo chat (active)", 10),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    # 聚合
    stats = cur.execute(
        """
        SELECT role, COUNT(*) AS cnt
        FROM messages
        WHERE session_id = ?
        GROUP BY role
        """,
        (10,),
    ).fetchall()
    print("stats:", [dict(r) for r in stats])

    # 执行计划预告
    plan = cur.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT * FROM messages WHERE session_id = 10
        """
    ).fetchall()
    print("plan:", plan)

    # DELETE（演示完再删一条）
    cur.execute("DELETE FROM messages WHERE id = ?", (3,))
    conn.commit()
    conn.close()
    print("done →", DB)


if __name__ == "__main__":
    main()
```

跑通后，对照练习 B1～B4 / A1～A2 自己改条件、加空会话、试 `LEFT JOIN`。

---

## 10. 练习指引

请打开并完成：

[`exercises/07-data-persistence/01-sql.md`](../../exercises/07-data-persistence/01-sql.md)

建议代码位置：

```text
playground/07-data-persistence/01-sql/
```

建议动手顺序：

1. 建 `sessions` / `messages`，完成 CRUD（B1）  
2. `JOIN` 查出某 `user_id` 的全部消息（B2）  
3. 为 `messages(session_id)` 建索引并写清理由（B3）  
4. 用 `BEGIN`/`COMMIT`/`ROLLBACK` 演示原子性（B4）  
5. 有余力：`GROUP BY` 与「消息数 ≥ 2」子查询（A1/A2）  
6. 选做：参数化 vs 字符串拼接的注入认知（C1，勿攻击真实系统）

---

## 11. 小结与下一站

### 心智模型

```text
表 = 一类实体的集合（sessions / messages）
行 = 一条记录
CRUD = 增删改查（WHERE 是安全带）
JOIN = 用键把多表拼成业务视图
索引 = 加速过滤/关联的目录（有写入成本）
事务 = 多步写的原子边界（消息 + tool_call）
聚合/子查询 = 从「列出行」到「算集合」
EXPLAIN = 问引擎「你怎么跑」
```

### 和前端 / API 的最终对照

| 你在应用层做的事 | SQL 对应 |
| --- | --- |
| REST 资源 CRUD | `INSERT` / `SELECT` / `UPDATE` / `DELETE` |
| 关联资源一次返回 | `JOIN` |
| 列表过滤字段建加速结构 | 索引 |
| 多步写要全成或全败 | 事务 |
| 管理后台统计图 | `GROUP BY` / 子查询 |
| 性能排障 | `EXPLAIN` |

### 自检清单

- [ ] 能手写 CRUD + 条件查询，并解释为何改删必须带窄 `WHERE`
- [ ] 能写基础 `JOIN`，说清 INNER 与 LEFT 对「空会话」的差异
- [ ] 能解释索引与事务对 Agent「会话/消息/工具记录」的意义
- [ ] （建议）能写 `COUNT` + `GROUP BY` 与简单 `IN (子查询)`
- [ ] （了解）会对一条查询跑 `EXPLAIN QUERY PLAN` 并粗读 SCAN vs INDEX
- [ ] 独立完成练习基础题 B1～B4

### 下一章

[`02-postgresql.md`](./02-postgresql.md) —— 把 SQL 落到真正常用的生产数据库：连接、类型、约束与工程配置。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Web 后端](../06-web-backend/README.md)
- 下一章：[PostgreSQL](./02-postgresql.md)
