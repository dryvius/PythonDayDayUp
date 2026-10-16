# PostgreSQL

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/07-data-persistence/02-postgresql.md`](../../exercises/07-data-persistence/02-postgresql.md)

## 本章定位

- **本章角色**：认识生产常见关系库 PostgreSQL：类型、约束、本地启动、连接配置；并为 JSON 业务字段与迁移建立直觉。
- **学习策略**：可用 Docker 启动；若环境受限，用 SQLite 练 SQL，但仍要读懂 PG 概念。

## 学习目标

1. 认识常用类型与约束。
2. 能在本地/容器启动 Postgres 并连接。
3. 会写基础连接配置（URL / 环境变量）。
4. 了解 JSONB 与迁移思路。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 常用类型、约束、本地/容器启动、连接配置 | 能连上并建表 |
| **建议掌握** | JSON/JSONB、迁移思路 | 能存半结构化数据 |
| **了解即可** | 扩展与性能调优 | 地图 |

---

## 1. 为什么选 PostgreSQL

- 可靠、SQL 标准好、生态强  
- JSONB、全文检索、扩展（含向量相关扩展生态）对 AI 应用友好  
- FastAPI / SQLAlchemy 教程大量以 PG 为例  

---

## 2. 必掌握：常用类型

| 类型 | 用途 |
|------|------|
| `BOOLEAN` | 开关 |
| `INTEGER` / `BIGINT` | 整数 id、计数 |
| `TEXT` / `VARCHAR` | 字符串 |
| `TIMESTAMPTZ` | 带时区时间（推荐） |
| `UUID` | 分布式 id |
| `JSONB` | 半结构化 JSON（建议掌握） |
| `NUMERIC` | 精确小数 |

Agent 表示例：

```sql
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 3. 必掌握：约束

```sql
CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES chat_sessions(id),
  role TEXT NOT NULL CHECK (role IN ('system','user','assistant','tool')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uniq_users_email ON users(email);
```

| 约束 | 作用 |
|------|------|
| PRIMARY KEY | 唯一标识 |
| FOREIGN KEY | 引用完整性 |
| UNIQUE | 唯一 |
| NOT NULL | 非空 |
| CHECK | 取值检查 |

---

## 4. 必掌握：本地 / 容器启动

Docker 示例：

```bash
docker run --name pg-agent -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=agent -p 5432:5432 -d postgres:16
```

连接串直觉：

```text
postgresql://postgres:postgres@localhost:5432/agent
```

客户端：`psql`、GUI（DBeaver 等）、或 Python 驱动。

---

## 5. 必掌握：连接配置

应用侧推荐环境变量：

```text
# SQLAlchemy 方言 URL（给 create_engine / create_async_engine 用）
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/agent

# 裸 psycopg / 多数 GUI 常用（无 +psycopg 后缀）
# postgresql://user:pass@localhost:5432/agent
```

原则：

- 密码不进仓库  
- 区分本地/预发/生产 URL  
- 连接池由 ORM/驱动管理（下一章）  
- `+psycopg` 是 **SQLAlchemy** 驱动标记，不要原样塞进 `psycopg.connect()`

---

## 6. 建议掌握：JSONB 与迁移

### JSONB

```sql
ALTER TABLE messages ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}'::jsonb;
SELECT * FROM messages WHERE metadata->>'model' = 'gpt-x';
```

适合：工具参数快照、模型返回的扩展字段。  
核心查询字段仍应用正式列 + 索引。

### 迁移思路

```text
改表不要只在生产手工点
→ 用迁移脚本（Alembic 等）版本化
→ 可上可回滚（尽量）
```

下一章 ORM 会接到 Alembic。

---

## 7. 了解即可：扩展与调优

`EXPLAIN ANALYZE`、连接数、vacuum、向量扩展……等有慢查询再深入。

---

## 8. 练习指引

[`exercises/07-data-persistence/02-postgresql.md`](../../exercises/07-data-persistence/02-postgresql.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能读懂建表与约束
- [ ] 知道如何用 Docker/本地启动并得到连接 URL
- [ ] 理解 JSONB 的适用边界

### 下一章

[`03-orm.md`](./03-orm.md) —— 用 SQLAlchemy 在 Python 里安全地操作库。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[SQL 基础](./01-sql.md)
- 下一章：[Python ORM](./03-orm.md)
