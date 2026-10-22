# 练习：PostgreSQL

> 对应文档：[`docs/07-data-persistence/02-postgresql.md`](../../docs/07-data-persistence/02-postgresql.md)  
> 状态：`已完成出题`  
> 建议用时：60～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 有 Docker 时优先真开 Postgres；若环境受限：用**书面题 + SQLite 近似**完成，并在笔记标明与 PG 的差异。
4. 建议目录：

```text
playground/07-data-persistence/02-postgresql/
  schema.sql
  b4_notes.md
  a1_jsonb.sql
  .env.example
```

5. **禁止**把真实密码提交进 git；练习用假密码写在 `.env.example` 即可。
6. Python ≥ 3.11（本节以 SQL/配置为主）。

---

## 热身题（建议先做）

### W1. 为什么不只用 SQLite？

**要求**：列出至少 **2 条** Agent/后端场景下倾向 PostgreSQL 的理由。

**验收**：理由具体（并发、类型、JSONB、运维生态等），不是「比较牛」。

---

### W2. TIMESTAMPTZ 直觉

**要求**：一句话说明为何文档强调 `TIMESTAMPTZ` 而非「无时区 timestamp」。

**验收**：提到时区/UTC 存储或跨区展示问题。

---

### W3. 连接串里的主机名

**要求**：对比「本机进程连 DB」与「Compose 里 api 容器连 db 服务」时，`localhost` 是否总对？

**验收**：能说出容器内 localhost 是容器自己。

---

### W4. .env 习惯

**要求**：写出至少 3 个应出现在 `.env.example` 的变量名（不要填真实密钥）。

**验收**：含数据库相关变量。

---

## 基础题（必做）

### B1. 类型选择（书面）

为下列字段各选 **PostgreSQL 类型**，并各写一句理由：

1. 会话 id  
2. 用户 id  
3. 消息正文  
4. 创建时间  
5. 扩展元数据（如 model、tool 快照）

**验收**：时间倾向 `TIMESTAMPTZ`；元数据倾向 `JSONB`；正文倾向 `TEXT`。

---

### B2. 约束设计

写出 `chat_sessions` + `messages` 的建表 SQL，要求包含：

- 主键  
- 外键（messages → chat_sessions）  
- 至少 1 个 `CHECK`（例如 `role IN (...)`）  
- 合理的 `NOT NULL`  

存 `schema.sql`。

**验收**：SQL 语法按 PG 方言；约束可读。

---

### B3. 连接串与环境变量

1. 写出本地 `DATABASE_URL` **示例**（假密码）  
2. 区分（若文档提到）给 `psycopg`/`asyncpg` 的 URL 与给 SQLAlchemy 的方言 URL 时，注明你用的那一种  
3. 列出应放进 `.env` / `.env.example` 的变量名  

**验收**：示例可被辨认为 URL；说明「真实值不进 git」。

---

### B4. 启动记录

**若成功** `docker run`（或 compose）启动 Postgres：把命令、如何用 `psql`/GUI 连通的步骤写入 `b4_notes.md`。

**若失败**：写清失败原因、环境限制、以及你的替代练习方案（例如只完成 schema + 书面差异对照）。

**验收**：别人按你的笔记能复现或能理解你为何降级。

---

## 进阶题（建议至少做 1 题）

### A1. JSONB

给 `messages` 增加 `metadata JSONB`（或建表示例里直接带上）。

完成：

1. 插入含 `{"model":"echo"}` 的一行  
2. 按 `metadata->>'model' = 'echo'`（或等价）查询  

存 `a1_jsonb.sql`。无 PG 时可用书面写出 SQL，并注明 SQLite JSON1 差异。

**验收**：插入 + 查询语句完整。

---

### A2. 迁移思路（书面）

描述从「加一列」到「多环境应用」的 **5 步**流程；可点名 Alembic / 迁移工具。

**验收**：包含：写迁移、审阅、应用到开发库、验证、再应用到其它环境（或 CI）——不必与参考逐步同名，但顺序合理。

---

## 挑战题（可选）

### C1. UUID 主键策略

把会话 id 改成 UUID 策略（SQL 草图即可），说明优劣各 **2 点**。

**验收**：不是只写「更随机」；要提到索引局部性/可读性/分布式生成等至少两侧。

---

### C2. 外键删除策略（书面）

对「删除 session」比较 `ON DELETE CASCADE` vs `RESTRICT`：各适合什么？Agent 消息场景你倾向哪种（给理由）？

**验收**：两种都解释到。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1 思路 + 参考答案

**参考答案**：更强的并发与权限模型；`JSONB`/约束/扩展生态更适合会话元数据与后续检索类扩展；多人协作的后端服务更常以 PG 为系统记录。

---

### W2 思路 + 参考答案

**参考答案**：`TIMESTAMPTZ` 按绝对时间点存储（通常归一到 UTC），避免「无时区时间」在跨区部署/夏令时下被误解释。

---

### W3 思路 + 参考答案

**参考答案**：本机 Python 连本机容器映射端口时可用 `localhost`；在 Compose 网络里，api 容器应使用服务名（如 `db`）作主机名，容器内的 `localhost` 并不是兄弟容器。

---

### W4 思路 + 参考答案

```text
DATABASE_URL=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
```

---

### B1 思路 + 参考答案

| 字段 | 类型 | 理由 |
|------|------|------|
| 会话 id | `UUID` 或 `BIGSERIAL` | 分布式友好用 UUID；简单自增用 BIGSERIAL |
| 用户 id | `TEXT` 或 `UUID` | 对接外部 IdP 时常用 TEXT/UUID |
| 消息正文 | `TEXT` | 长度不确定，避免过紧 VARCHAR |
| 创建时间 | `TIMESTAMPTZ` | 保留时间点，避免无时区歧义 |
| 扩展元数据 | `JSONB` | 可索引/可查询的半结构化数据 |

---

### B2 思路 + 参考答案

**参考答案（`schema.sql`）**

```sql
-- PostgreSQL 方言示例
CREATE TABLE IF NOT EXISTS chat_sessions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    title           TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id              BIGSERIAL PRIMARY KEY,
    session_id      BIGINT NOT NULL REFERENCES chat_sessions(id),
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT messages_role_check
        CHECK (role IN ('system', 'user', 'assistant', 'tool'))
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
```

---

### B3 思路 + 参考答案

**参考答案**

```text
# 给常见客户端的示例（假密码）
DATABASE_URL=postgresql://agent:agent_dev_pwd@127.0.0.1:5432/agent_db

# 若使用 SQLAlchemy，常见写法：
# postgresql+psycopg://agent:agent_dev_pwd@127.0.0.1:5432/agent_db
```

`.env.example`：

```text
DATABASE_URL=postgresql://agent:agent_dev_pwd@127.0.0.1:5432/agent_db
POSTGRES_USER=agent
POSTGRES_PASSWORD=agent_dev_pwd
POSTGRES_DB=agent_db
```

真实密码只放本地 `.env`（gitignore），绝不提交。

---

### B4 思路 + 参考答案

**参考答案（成功时笔记模板）**

```bash
docker run --name pg-agent \
  -e POSTGRES_USER=agent \
  -e POSTGRES_PASSWORD=agent_dev_pwd \
  -e POSTGRES_DB=agent_db \
  -p 5432:5432 \
  -d postgres:16

docker exec -it pg-agent psql -U agent -d agent_db
# 然后: \dt   或  \i schema.sql
```

失败时示例：`Docker Desktop 未启动 / 公司机器禁容器` → 完成 B1/B2/B3 书面与 schema，A1 用 SQL 文本练习，并对照文档「SQLite vs PG」表。

---

### A1 思路 + 参考答案

```sql
ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

INSERT INTO chat_sessions (user_id, title)
VALUES ('alice', 'jsonb demo')
RETURNING id;
-- 假设返回 id=1

INSERT INTO messages (session_id, role, content, metadata)
VALUES (
    1,
    'assistant',
    'hello',
    '{"model":"echo"}'::jsonb
);

SELECT id, content, metadata
FROM messages
WHERE metadata->>'model' = 'echo';
```

SQLite 近似：用 `JSON` 文本 + `json_extract(metadata, '$.model')`；能力与索引与 PG 不同，需在笔记标明。

---

### A2 思路 + 参考答案

**五步示例**：

1. 在迁移工具中生成「加列」迁移脚本（Alembic revision）  
2. 人工审阅升级/降级是否可逆、默认值是否锁表过久  
3. 应用到本地/开发库并跑测试  
4. 在预发环境应用并观察  
5. 生产应用（窗口/权限/备份策略按团队规范）并记录版本  

不要在生产只靠 `create_all` 偷偷改表。

---

### C1 思路 + 参考答案

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- 或用应用侧生成 UUID

CREATE TABLE chat_sessions_uuid (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    TEXT NOT NULL,
    title      TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

优：客户端可预生成 id；合并多库冲突少；不暴露业务量。  
劣：索引局部性通常不如顺序 id；调试不如整数好记；占空间更大。

---

### C2 思路 + 参考答案

- `CASCADE`：删会话时自动删消息，省事，但误删代价大。  
- `RESTRICT`/`NO ACTION`：有消息时拒删，更安全，需先归档/显式删子行。  
- Agent 场景常倾向：软删除会话 + 限制硬删；若硬删，生产更慎用自动 CASCADE，或仅在明确「彻底销毁用户数据」流程里用。

---

## 附录：SQLite 近似对照（环境受限时）

当你无法启动 Postgres 时，可用下表完成「概念对齐」，并在 `b4_notes.md` 声明降级。

| 主题 | PostgreSQL | SQLite 近似 | 练习时注意 |
|------|------------|-------------|------------|
| 正文 | `TEXT` | `TEXT` | 基本可直接迁移心智 |
| 时间 | `TIMESTAMPTZ` | `TEXT` ISO8601 或 `DATETIME` | **无真正时区类型**，要自己约定存 UTC |
| 元数据 | `JSONB` | `TEXT` + JSON1 | 运算符与 GIN 索引不对等 |
| 自增 | `BIGSERIAL` | `INTEGER PRIMARY KEY AUTOINCREMENT` | 类型宽度语义不同 |
| UUID | `UUID` | `TEXT` | 应用侧生成即可 |
| 约束 | CHECK/FK 完善 | FK 需 `PRAGMA foreign_keys=ON` | 别假设默认开启 |

最小 SQLite schema 对照（仅帮助本地练手，**不是** PG 等价物）：

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id),
    role TEXT NOT NULL CHECK (role IN ('system','user','assistant','tool')),
    content TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
```

---

## 附录：连接与权限常见踩坑

1. **把生产密码写进 Dockerfile `ENV`**：密码进镜像层，镜像一推送即泄露。应运行时注入。  
2. **`trust` 认证对公网端口开放**：练习库可以偷懒，公网绝对不行。  
3. **只开 `5432` 到 0.0.0.0 却无防火墙**：本机 Docker 端口映射要意识到暴露面。  
4. **用超级用户跑应用**：应用账号应只有必要 DML/DDL；练习可单用户，生产要拆。  
5. **迁移与应用同用户乱改**：权限与审计会变糊；至少在笔记里区分「迁移角色 / 运行角色」。

**验收自问**：

- [ ] 我能否不看文档写出一份含 PK/FK/CHECK 的会话消息 schema？  
- [ ] 我能否解释为何 `TIMESTAMPTZ` 优于「无时区时间」？  
- [ ] 我能否说清 compose 里主机名该写服务名？


---

## 附录：练习日清单（建议按序勾）

1. 写完 B1 类型表（不查文档先盲写，再对照）
2. 落盘 `schema.sql` 并至少在一种引擎执行/审阅
3. 写好 `.env.example`（假密码）
4. 记录 Docker 成功或失败原因
5. 选做 JSONB 或迁移五步

**口头题（给同伴讲 2 分钟）**：

- 为什么消息正文用 TEXT，元数据用 JSONB？
- 外键能防止什么应用层漏网错误？
- 连接串里的主机名在「本机」和「compose」分别怎么写？

**扩展阅读对照（不必做）**：向量扩展、连接池、只读副本——放到「了解即可」，本练习不要求落地。

### 再练一遍：最小插入

```sql
INSERT INTO chat_sessions (user_id, title) VALUES ('alice', 'demo');
INSERT INTO messages (session_id, role, content)
VALUES (1, 'user', 'hello from practice');
SELECT m.id, m.role, m.content
FROM messages m
JOIN chat_sessions s ON s.id = m.session_id
WHERE s.user_id = 'alice';
```


---

## 附录：DATABASE_URL 拆解练习

把下面示例拆成字段（书面）：

```text
postgresql://agent:agent_dev_pwd@127.0.0.1:5432/agent_db
```

应能指出：

1. 协议 / 驱动提示  
2. 用户名  
3. 密码  
4. 主机  
5. 端口  
6. 数据库名  

SQLAlchemy 方言示例（了解）：

```text
postgresql+psycopg://agent:agent_dev_pwd@127.0.0.1:5432/agent_db
```

**不要**把含真实密码的 URL 贴进聊天记录或提交到 git。
