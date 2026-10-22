# 练习：SQL 基础

> 对应文档：[`docs/07-data-persistence/01-sql.md`](../../docs/07-data-persistence/01-sql.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 可用 **SQLite**（`sqlite3` CLI 或 Python 标准库）完成，降低环境门槛。
4. 建议目录：

```text
playground/07-data-persistence/01-sql/
  b1.sql
  b2.sql
  b4_tx.py
  notes.md
```

5. Python ≥ 3.11；SQL 文件应可直接执行或被脚本跑通。
6. 先自己做完，再看文末「提示与参考答案」。

---

## 热身题（建议先做）

### W1. SELECT 最小句

**要求**：写出查询 `messages` 表全部列的 SQL（表可尚不存在，先写对语法）。

**验收**：`SELECT * FROM messages;` 或显式列清单。

---

### W2. 过滤

**要求**：写出「`session_id = 1` 的消息」的 `WHERE` 查询。

**验收**：条件写在 `WHERE`，不是伪代码。

---

### W3. 排序

**要求**：按 `created_at` 升序返回某会话消息。

**验收**：出现 `ORDER BY created_at`。

---

### W4. 占位符直觉

**要求**：用一句话说明：为什么不要用 f-string 把用户输入拼进 SQL。

**验收**：提到 SQL 注入或「代码与数据未分离」。

---

## 基础题（必做）

### B1. 建表 + CRUD

建表 `messages`，字段至少：

| 列 | 说明 |
|----|------|
| `id` | 主键，自增 |
| `session_id` | 整数，非空 |
| `role` | 文本，非空 |
| `content` | 文本，非空 |
| `created_at` | 文本或时间，非空（SQLite 可用 `TEXT` 存 ISO 时间） |

完成：

1. 插入 3 行（至少两个不同 `session_id`）  
2. 按 `session_id` 查询  
3. 更新 1 行 `content`  
4. 删除 1 行  

把 SQL 存 `b1.sql`（可用多个语句）。

**验收**：从头执行脚本不报错；查询能看到更新后的内容；删除后行数减少。

---

### B2. JOIN

再建 `sessions(id, user_id, title)`，插入至少 2 个会话。  
写 **JOIN** 查出某 `user_id` 的全部消息（含 session 标题更佳）。

存 `b2.sql`。

**验收**：结果集能看出消息属于哪个 session；使用了 `JOIN`（不是两次手工过滤糊弄）。

---

### B3. 索引（SQL + 书面）

1. 为 `messages(session_id)` 创建索引  
2. 书面 **3 行内**说明：为什么对该列建索引（结合「按会话拉历史」的访问模式）

**验收**：有 `CREATE INDEX`；理由连到查询条件/高频过滤列。

---

### B4. 事务

用 Python `sqlite3` 或 SQL 脚本演示事务：

**成功路径**：插入两条消息 → `COMMIT` → 都能查到。  

**失败路径（演示）**：开启事务 → 插入一条 → 故意失败（错误 SQL 或 `raise`）→ `ROLLBACK` → 库中不应留下半成品。

把可运行脚本存 `b4_tx.py`，并在注释里写清 COMMIT/ROLLBACK 意图。

**验收**：失败路径后计数与开始时一致（或按你的断言说明）。

---

## 进阶题（建议至少做 1 题）

### A1. 聚合

统计每个 `role` 的消息数（`GROUP BY`）。

**验收**：输出含 role 与 count。

---

### A2. 子查询 / HAVING

列出「消息数 ≥ 2」的 `session_id`。

**验收**：结果与手工计数一致。

---

## 挑战题（可选）

### C1. SQL 注入认知（对比说明 + 安全写法）

写一段 Python：

1. **错误示范**（注释标明 DO NOT USE）：字符串拼接用户输入  
2. **正确写法**：`sqlite3` 占位符参数绑定  

**要求**：不要对任何真实系统做攻击；用本地库自证「绑定后特殊字符只是数据」。

**验收**：两段代码都有；结论写进 `notes.md`。

---

### C2. 分页直觉

写 `LIMIT/OFFSET`（或 keyset 思路书面）取某会话第 2 页（页大小 2）。

**验收**：SQL 可跑或书面步骤完整。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成（SQL/脚本可执行）
- [ ] 能口述：事务解决什么；索引不是免费的
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1～W3 参考答案

```sql
SELECT * FROM messages;
SELECT * FROM messages WHERE session_id = 1;
SELECT * FROM messages WHERE session_id = 1 ORDER BY created_at ASC;
```

### W4 参考答案

用户输入与 SQL 代码混在一起时，攻击者可能改写语句语义（注入）；应使用参数绑定让输入只作为数据。

---

### B1 思路 + 参考答案

**思路**：先 schema，再 insert，再 select/update/delete；脚本可重复执行时可先 `DROP`（仅练习库）。

**参考答案（`b1.sql`）**

```sql
DROP TABLE IF EXISTS messages;

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

INSERT INTO messages (session_id, role, content, created_at) VALUES
    (1, 'user', 'hello', '2026-01-01T10:00:00'),
    (1, 'assistant', 'hi there', '2026-01-01T10:00:01'),
    (2, 'user', 'another session', '2026-01-01T11:00:00');

-- 按 session 查询
SELECT id, role, content
FROM messages
WHERE session_id = 1
ORDER BY id;

-- 更新
UPDATE messages
SET content = 'hi there (edited)'
WHERE id = 2;

-- 删除
DELETE FROM messages WHERE id = 3;

SELECT * FROM messages ORDER BY id;
```

**Python 一键跑**（可选）：

```python
from __future__ import annotations

import sqlite3
from pathlib import Path

db_path = Path(__file__).with_name("practice.db")
sql = Path(__file__).with_name("b1.sql").read_text(encoding="utf-8")

with sqlite3.connect(db_path) as conn:
    conn.executescript(sql)
    rows = conn.execute("SELECT id, session_id, content FROM messages ORDER BY id").fetchall()
    print(rows)
```

---

### B2 思路 + 参考答案

**思路**：会话与消息 1:N；用 FK 列 `session_id` 连接。

**参考答案（`b2.sql`）**

```sql
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS sessions;

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

INSERT INTO sessions (id, user_id, title) VALUES
    (1, 'alice', 'rag chat'),
    (2, 'bob', 'ops');

INSERT INTO messages (session_id, role, content, created_at) VALUES
    (1, 'user', 'what is RAG?', '2026-01-01T10:00:00'),
    (1, 'assistant', 'retrieval + generation', '2026-01-01T10:00:01'),
    (2, 'user', 'restart api', '2026-01-01T12:00:00');

-- 查出 alice 的全部消息
SELECT
    s.user_id,
    s.title,
    m.id AS message_id,
    m.role,
    m.content
FROM messages AS m
JOIN sessions AS s ON s.id = m.session_id
WHERE s.user_id = 'alice'
ORDER BY m.id;
```

---

### B3 思路 + 参考答案

**思路**：WHERE/JOIN 高频列值得索引；写会变慢、占空间。

**参考答案**

```sql
CREATE INDEX idx_messages_session_id ON messages(session_id);
```

书面：Agent 拉历史几乎总是「给定 session_id 查 messages」。在该列建索引可减少全表扫描；代价是插入/更新时维护索引，以及额外存储——对读多写少的会话历史通常划算。

---

### B4 思路 + 参考答案

**思路**：原子性——要么一起成功，要么一起撤销。

**参考答案（`b4_tx.py`）**

```python
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("tx_demo.db")


def setup(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS messages;
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        );
        """
    )


def count_messages(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) FROM messages").fetchone()
    assert row is not None
    return int(row[0])


def commit_path(conn: sqlite3.Connection) -> None:
    # 成功路径：两条插入同一事务，一起提交
    try:
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (1, "user", "a"),
        )
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (1, "assistant", "b"),
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def rollback_path(conn: sqlite3.Connection) -> None:
    # 失败路径：第二条故意写坏，整笔回滚
    before = count_messages(conn)
    try:
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (1, "user", "will rollback"),
        )
        # 故意失败：无此列
        conn.execute(
            "INSERT INTO messages (session_id, role, content, missing) VALUES (?, ?, ?, ?)",
            (1, "assistant", "x", "y"),
        )
        conn.execute("COMMIT")
    except sqlite3.Error:
        conn.execute("ROLLBACK")
    after = count_messages(conn)
    assert after == before, (before, after)


if __name__ == "__main__":
    with sqlite3.connect(DB) as conn:
        setup(conn)
        commit_path(conn)
        assert count_messages(conn) == 2
        rollback_path(conn)
        assert count_messages(conn) == 2
        print("b4 ok")
```

---

### A1 思路 + 参考答案

```sql
SELECT role, COUNT(*) AS message_count
FROM messages
GROUP BY role
ORDER BY message_count DESC;
```

---

### A2 思路 + 参考答案

```sql
-- HAVING
SELECT session_id, COUNT(*) AS message_count
FROM messages
GROUP BY session_id
HAVING COUNT(*) >= 2;

-- 或子查询
SELECT session_id
FROM (
    SELECT session_id, COUNT(*) AS c
    FROM messages
    GROUP BY session_id
)
WHERE c >= 2;
```

---

### C1 思路 + 参考答案

**思路**：拼接改变语法树；绑定只传值。

**参考答案**

```python
from __future__ import annotations

import sqlite3


def unsafe_find(conn: sqlite3.Connection, role: str) -> list:
    # DO NOT USE：演示用拼接。用户输入可变成新的 SQL 子句。
    sql = f"SELECT id, content FROM messages WHERE role = '{role}'"
    return list(conn.execute(sql))


def safe_find(conn: sqlite3.Connection, role: str) -> list:
    sql = "SELECT id, content FROM messages WHERE role = ?"
    return list(conn.execute(sql, (role,)))


if __name__ == "__main__":
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE messages (id INTEGER PRIMARY KEY, role TEXT, content TEXT)"
    )
    conn.execute(
        "INSERT INTO messages (role, content) VALUES ('user', 'hello')"
    )
    # 绑定后，即便字符串含引号也只是数据
    evil = "user' OR '1'='1"
    print("safe:", safe_find(conn, evil))
```

`notes.md` 结论示例：永远不要把不可信输入拼进 SQL；使用 `?` / `:name` 占位符。ORM 也不能让你完全忘记注入（仍有原始 SQL 拼接风险）。

---

### C2 思路 + 参考答案

```sql
-- 页大小 2，第 2 页（OFFSET 2）
SELECT id, role, content
FROM messages
WHERE session_id = 1
ORDER BY id
LIMIT 2 OFFSET 2;
```

书面补充：深分页时 OFFSET 变贵，可改用「上一页最后 id」做 keyset：`WHERE id > :last_id ORDER BY id LIMIT 2`。
