# Python ORM

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：4～6 小时（有 SQL / FastAPI 经验可更快；Session 生命周期、迁移审查、N+1 建议动手踩一遍）  
> 对应练习：[`exercises/07-data-persistence/03-orm.md`](../../exercises/07-data-persistence/03-orm.md)  
> 环境约定：Python ≥ 3.11；注解用 `list[str]`、`str | None`；SQLAlchemy **2.x**（`select()` / `Mapped` / `mapped_column`）；异步路径用 `AsyncSession`

## 本章定位

- **模块目标**：掌握 SQL/ORM/缓存/队列的工程用法与取舍。
- **本章角色**：用 ORM（以 SQLAlchemy 2.x 思维为主）把表映射成 Python 类；掌握 Session、迁移与 N+1 意识。
- **原则**：ORM 是工具，不是免除 SQL；复杂报表仍可能手写 SQL。
- **前置**：上一章的 PostgreSQL 类型/约束/连接 URL；模块 01 的 SQL CRUD/事务；模块 05/06 的 asyncio 与 FastAPI `Depends`。
- **你的优势**：若写过 Prisma / TypeORM / Django ORM / Sequelize，心智几乎一一对应；差异主要在「Session 边界」与「2.x 的 `select()` 写法」。
- **安装（最小）**：
  - 同步 + SQLite：`pip install "sqlalchemy>=2.0"`
  - 异步 + SQLite：再加 `aiosqlite`（URL：`sqlite+aiosqlite:///./agent.db`）
  - 异步 + Postgres：`asyncpg`（URL：`postgresql+asyncpg://...`）
  - 迁移：`alembic`

## 学习目标（学完应能做到）

1. 说清 ORM 选型关注点（SQLAlchemy / SQLModel / Django ORM / 其它），以及本路线为何以 SQLAlchemy 概念为准。
2. 用 2.x 声明式模型定义表，并用 Session / AsyncSession 完成读写（含 commit / rollback）。
3. 理解迁移为何必要；能描述 Alembic「改模型 → 生成 → 审查 → 升级」链路。
4. 能识别 N+1，知道 `joinedload` / `selectinload` 与仓储模式直觉。
5. 能画出 Agent「同一事务写多条记录」的提交/回滚心智。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 选型、模型与会话、迁移 | 能做基础 CRUD；敢在生产思路里拒绝裸 `create_all` |
| **建议掌握** | N+1、仓储模式 | 能避免低级性能坑；endpoint 不堆查询细节 |
| **了解即可** | 复杂查询优化 | 地图：窗口函数、CTE、批量插入等，有慢查询再专项学 |

---

## 1. ORM 是什么 / 如何选型

这一节会刻意写细——后面所有模型、Session、迁移，都站在「你选对了工具层级」之上。

### 1.1 ORM 在解决什么

#### 为什么需要 ORM？

手写 SQL 很重要（上一章），但每个接口都拼字符串会很快失控：

```text
字段改名 → 几十处 SQL 跟着改
参数化遗漏 → SQL 注入
对象字段 ↔ 行字典手工搬运 → 易漏、难测
事务边界散落在业务函数里 → 半成功半失败
```

ORM（Object-Relational Mapping）做的事：

```text
Python 类  ↔  表
实例        ↔  行
属性        ↔  列
Session     ↔  一组工作的单元（读写 + 事务）
```

可以先记一句：

> ORM 把「怎么跟库说话」收成 Python API；**不等于**你可以不会 SQL。慢查询、JOIN、索引、事务语义，排障时仍要回到 SQL。

#### 怎么写（概念对照，先建立地图）

| SQL 世界 | ORM 世界（直觉） |
| --- | --- |
| `CREATE TABLE messages (...)` | `class Message(Base): __tablename__ = "messages"` |
| `INSERT INTO messages ...` | `session.add(Message(...)); await session.commit()` |
| `SELECT ... WHERE session_id = ?` | `select(Message).where(Message.session_id == sid)` |
| `UPDATE ...` | 改对象属性后 `commit`（或显式 `update()`） |
| `DELETE ...` | `await session.delete(obj)` 后 `commit` |
| `BEGIN / COMMIT / ROLLBACK` | Session 的事务边界 |

#### 跑一下（心智，不要求此刻装库）

想象一行消息：

```text
messages 表的一行：
  id=1, session_id="s1", role="user", content="hello"

对应 Python：
  msg = Message(session_id="s1", role="user", content="hello")
  # commit 后 msg.id 往往会被回填
```

你操作的是对象；库里落的是行。Session 负责「何时真正发 SQL、何时提交」。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为用了 ORM 就不用懂 SQL | 生产慢查询、错误的 JOIN、错误的事务隔离，最终仍要读 SQL / `EXPLAIN` |
| 把「模型类」当成「永远同步的实时库」 | 改了属性没 `commit`，库里没变；别的进程更看不到 |
| 在业务里拼 f-string SQL | ORM 也防不住你手写注入；参数化/绑定才是底线 |

#### SQL / 手写驱动对照

| 做法 | 优点 | 代价 |
| --- | --- | --- |
| 裸 SQL + 驱动 | 最透明 | 样板多、易漏参数化 |
| ORM | CRUD / 关系 / 迁移生态成熟 | 抽象泄漏时要会「下潜」到 SQL |
| 查询构建器（偏 Core） | 灵活、接近 SQL | 仍要自己管映射与生命周期 |

本路线：**2.x ORM 为主，复杂报表可退回 Core / 手写 SQL**。

---

### 1.2 选型：SQLAlchemy / SQLModel / Django ORM / 其它

#### 为什么要先选型，而不是「哪个火用哪个」？

Agent / FastAPI 项目常见四条约束：

1. **异步主线**：路由是 `async def`，DB 访问不能堵事件循环（见模块 05/06）
2. **不绑死单体框架**：希望服务可拆、可换 Web 层
3. **迁移可协作**：多人改表要有版本化脚本
4. **类型友好**：Python ≥ 3.11 注解能进模型与 IDE

选型是在这些约束下找「默认答案」，不是宗教战争。

#### 怎么选（对照表）

| 工具 | 备注 | 何时优先考虑 |
| --- | --- | --- |
| **SQLAlchemy** | Python 事实标准；Core + ORM；2.x API 统一；`AsyncSession` 成熟 | FastAPI / 独立服务 / 本路线默认 |
| **SQLModel** | 偏 FastAPI/Pydantic 风格，底层仍常靠 SQLAlchemy | 想少写一点样板、且接受其抽象层 |
| **Django ORM** | 绑 Django 生态（admin、迁移、惯例） | 你已在 Django 单体里 |
| **Tortoise / others** | 异步生态选项 | 小项目尝鲜；团队要评估生态与迁移工具成熟度 |

本路线以 **SQLAlchemy 2.x 概念**为准；具体 API 以你安装的大版本文档为准。SQLModel 会了 SQLAlchemy，迁移成本通常更低。

#### 跑一下（选型决策树，口头过一遍）

```text
是否已在 Django 项目里？
  ├─ 是 → Django ORM（跟生态走）
  └─ 否 → 是否 FastAPI / 异步服务为主？
            ├─ 是 → SQLAlchemy 2.x + AsyncSession（本路线）
            │         └─ 想更 Pydantic 一体？可评估 SQLModel（仍要懂 SA）
            └─ 否 → 同步 SQLAlchemy Session 也够用；别为了「潮」硬上异步
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 同项目混用两套 ORM「各管一张表」 | 事务边界、连接池、迁移工具分裂，排障成本暴涨 |
| 以为 SQLModel「不是 SQLAlchemy」 | 底层问题（Session、lazy load、N+1）仍是 SA 问题 |
| 只看星标、不看异步与迁移 | Demo 能跑，协作与生产翻车 |

#### 和 Agent 栈对照

| 层 | 常见选择 |
| --- | --- |
| HTTP | FastAPI |
| 校验 | Pydantic v2 |
| ORM | SQLAlchemy 2.x |
| 迁移 | Alembic |
| 库 | PostgreSQL（开发可用 SQLite） |

---

### 1.3 本路线默认约定（写代码前钉死）

#### 为什么要先钉约定？

同一章里若同步/异步、1.x/2.x 写法混着抄，练习会绿、项目会炸。先约定，后面所有示例都服从它。

#### 怎么写（约定清单）

1. **Python ≥ 3.11**；用 `list[Message]`、`str | None`
2. **SQLAlchemy 2.x**：`DeclarativeBase` + `Mapped` + `mapped_column`；查询用 `select(...)`，少用遗留的 `session.query(...)` 作为新代码默认
3. **FastAPI 异步主线**：优先 `AsyncSession` + `await session.execute(...)`
4. **连接串来自环境变量**（上一章 `DATABASE_URL`）；密码不进仓库
5. **生产表结构靠 Alembic**；`create_all` 仅本地玩具/测试可接受

#### 跑一下（依赖直觉）

```bash
# 玩具：同步 SQLite
pip install "sqlalchemy>=2.0"

# 与 FastAPI 异步主线对齐（推荐练习这条）
pip install "sqlalchemy>=2.0" aiosqlite alembic
```

#### 易错点

- 文档/博客仍大量是 1.x 的 `Query` API——能读，但**新代码按 2.x 写**
- `postgresql://` 与 `postgresql+asyncpg://` 不是同一回事（方言/驱动后缀必须匹配用法）

#### 对照：同步 vs 异步（先记结论）

| 场景 | 推荐 |
| --- | --- |
| `async def` 路由 | `AsyncSession` |
| 普通 `def` 路由 / 脚本 | 同步 `Session` 可以 |
| 在 `async def` 里直接 `session.execute`（同步） | **禁止**（堵事件循环） |

---

## 2. 必掌握：模型与会话

这一节会刻意写细——模型定义、Session CRUD、异步 Session，是后面迁移与仓储的底座。

### 2.1 声明式模型（SQLAlchemy 2.x）

#### 为什么要用 `Mapped` / `mapped_column`？

2.x 把「类型注解」和「列定义」绑在一起：IDE / 类型检查更友好，也和 Python ≥ 3.11 的注解习惯一致。旧式 `__table__` / 纯 `Column` 仍能读，但新代码优先新写法。

#### 怎么写

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
```

要点：

| 片段 | 含义 |
| --- | --- |
| `DeclarativeBase` | 所有模型的共同基类；元数据挂在这里 |
| `__tablename__` | 表名 |
| `Mapped[int]` | 注解：属性在 Python 侧的类型 |
| `mapped_column(...)` | 列选项：主键、索引、长度、可空等 |
| `index=True` | 为高频过滤列建索引（Agent 里常见 `session_id`） |

#### 跑一下（同步 SQLite 建表）

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, Text, select


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)


engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
Base.metadata.create_all(engine)  # 玩具/测试可以；生产请用迁移（§3）

with Session(engine) as session:
    session.add(Message(session_id="s1", role="user", content="hello"))
    session.commit()

    rows = session.scalars(
        select(Message).where(Message.session_id == "s1")
    ).all()
    print(rows[0].content)  # hello
```

`echo=True` 会打印 SQL——初学强烈建议打开一段时间，建立「对象操作 ↔ SQL」对照。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 忘写 `__tablename__` | 启动/建表时报错或行为不符合预期 |
| 把可空列写成 `Mapped[str]` 却不配 `nullable` | 注解与库约束不一致；用 `Mapped[str \| None]` 表达可空更清晰 |
| 生产长期只靠 `create_all` | 改列时无法安全演进已有数据（见 §3） |
| 字符串主键/外键不设长度（部分库） | Postgres 可用 `TEXT`；可移植性与索引策略要心里有数 |

#### SQL 对照

```sql
CREATE TABLE messages (
  id INTEGER NOT NULL PRIMARY KEY,  -- SQLite 示意；PG 常用 BIGSERIAL/IDENTITY
  session_id VARCHAR(64) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content TEXT NOT NULL
);
CREATE INDEX ix_messages_session_id ON messages (session_id);
```

---

### 2.2 Session 生命周期：打开 → 用 → commit/rollback → close

#### 为什么 Session 比「连上数据库」更重要？

引擎（Engine）管**连接池**；Session 管**这一次工作单元**：

```text
打开 Session
  → 查询/修改对象（可能先待在内存 identity map）
  → commit 提交
  → 出错 rollback
  → close
```

搞不清边界，典型事故是：

- 改了对象以为「已经进库」——其实没 `commit`
- 异常后继续用同一 Session——状态脏了
- Session 活得太长——连接占着、对象过期语义混乱

#### 怎么写（同步最小形状）

```python
from sqlalchemy.orm import Session

with Session(engine) as session:
    try:
        session.add(Message(session_id="s1", role="user", content="hi"))
        session.commit()
    except Exception:
        session.rollback()
        raise
```

FastAPI 中常用依赖 `yield` Session，请求结束关闭（异步版见 §2.4）。

参数化/绑定由 ORM 处理，降低 SQL 注入风险（**仍不要**拼字符串 SQL）。

#### 跑一下（CRUD 一条龙）

```python
from sqlalchemy import select
from sqlalchemy.orm import Session


def crud_demo(engine) -> None:
    with Session(engine) as session:
        # Create
        m1 = Message(session_id="s1", role="user", content="hello")
        m2 = Message(session_id="s1", role="assistant", content="hi!")
        session.add_all([m1, m2])
        session.commit()

        # Read
        msgs = session.scalars(
            select(Message)
            .where(Message.session_id == "s1")
            .order_by(Message.id)
        ).all()
        assert len(msgs) == 2

        # Update
        msgs[0].content = "hello!"
        session.commit()

        # Delete
        session.delete(msgs[1])
        session.commit()
```

心智图：

```text
session.add(obj)     → 纳入 Session 管理（未必立刻 INSERT）
修改 obj.attr        → 脏检查；commit 时发 UPDATE
session.delete(obj)  → 标记删除；commit 时发 DELETE
session.commit()     → 把待发 SQL 刷进事务并提交
session.rollback()   → 丢弃未提交变更
session.close()      → 结束工作单元（with 会帮你做）
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `add` 后不 `commit` | 库里没有；进程退出后「数据消失」 |
| 异常后不 `rollback` 继续用 | 后续操作可能怪报错或脏状态 |
| 把 Session 做成全局单例长期复用 | 线程/协程间串状态；连接生命周期失控 |
| `commit` 后还假设所有属性一定新鲜 | 默认可能 `expire`；异步下常用 `expire_on_commit=False`（见下节） |

#### 对照：引擎 vs Session

| 对象 | 职责 |
| --- | --- |
| `Engine` / `AsyncEngine` | 方言、连接池、与 DB 的通道 |
| `Session` / `AsyncSession` | 一次业务工作的对象身份映射 + 事务 |
| `select()` 语句 | 要执行的查询描述；需 `session.execute` / `scalars` 才真正跑 |

---

### 2.3 查询写法（2.x：`select` + `execute` / `scalars`）

#### 为什么不把 `session.query` 当新默认？

1.x 的 `session.query(Message).filter(...)` 还能见到；2.x 推荐统一用 Core 风格的 `select()`，同步/异步同一套语句对象，心智更干净。

#### 怎么写

```python
from sqlalchemy import select

stmt = (
    select(Message)
    .where(Message.session_id == "s1")
    .order_by(Message.id)
)

# 同步
rows = session.scalars(stmt).all()

# 异步（下节）
# result = await session.execute(stmt)
# rows = list(result.scalars())
```

按主键取一条（直觉）：

```python
msg = session.get(Message, 1)  # 没有则 None
```

#### 跑一下

```python
stmt = select(Message).where(Message.role == "user")
for m in session.scalars(stmt):
    print(m.id, m.content)
```

打开 `echo=True` 时，对照控制台里的 `SELECT ... WHERE messages.role = ?`。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 写了 `select(...)` 却忘记 `execute`/`scalars` | 只得到语句对象，没有数据 |
| `where(Message.session_id == sid)` 写成 `==` 以外的 Python 布尔运算链不当 | 复杂条件用 `and_()` / `or_()`，别把 Python `and` 当成 SQL AND |
| 把用户输入拼进 `text(f"...")` | 绕过 ORM 保护，回到注入风险 |

#### SQL 对照

```python
select(Message).where(Message.session_id == "s1").order_by(Message.id)
```

≈

```sql
SELECT messages.id, messages.session_id, messages.role, messages.content
FROM messages
WHERE messages.session_id = 's1'
ORDER BY messages.id;
```

---

### 2.4 异步路由注意：`AsyncSession`（与模块 05/06 对齐）

#### 为什么异步章要单独钉死？

同步 `session.execute(...)` **会阻塞事件循环**。FastAPI 里大量 `async def` 路由若直接跑同步 Session，并发能力会被「一个慢查询」拖垮。

二选一：

| 做法 | 适用 |
|------|------|
| `AsyncSession` + `await session.execute(...)` | `async def` 路由（推荐与 FastAPI 异步主线一致） |
| 同步 Session + 普通 `def` 路由（框架丢线程池）或 `asyncio.to_thread` | 暂时只有同步 ORM 代码 |

**不要**在 `async def` 里直接跑同步 Session。

#### 怎么写

```python
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# 例：postgresql+asyncpg://user:pass@localhost:5432/agent
# 玩具：sqlite+aiosqlite:///./agent.db
engine = create_async_engine(os.environ["DATABASE_URL"], echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def list_messages(session_id: str) -> list[Message]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.id)
        )
        return list(result.scalars())
```

`expire_on_commit=False` 的常见原因：`commit` 后还要读对象属性返回给 API，避免额外 refresh；**仍要清楚**对象可能相对库已过期——别跨请求缓存同一实例当真理。

#### 跑一下（异步 CRUD 最小脚本）

```python
import asyncio
import os

from sqlalchemy import select, String, Text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    engine = create_async_engine(url, echo=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # 玩具；生产用 Alembic

    async with Session() as session:
        session.add(Message(session_id="s1", role="user", content="hello"))
        await session.commit()

        result = await session.execute(
            select(Message).where(Message.session_id == "s1")
        )
        msg = result.scalars().one()
        print(msg.content)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `async def` 里用同步 `Session` | 事件循环被堵；延迟抖动、吞吐崩 |
| URL 写成 `postgresql://` 却 `create_async_engine` | 驱动不匹配，启动即失败 |
| 忘记 `await session.commit()` | 异步下同样「内存有、库没有」 |
| `create_all` 用同步 API 直接打在 async engine 上 | 需要 `run_sync` 或改用迁移 |

#### FastAPI `Depends` 对照（草图）

```python
from collections.abc import AsyncIterator
from fastapi import Depends, FastAPI

app = FastAPI()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@app.get("/sessions/{session_id}/messages")
async def api_list_messages(
    session_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int]]:
    result = await session.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.id)
    )
    rows = list(result.scalars())
    return [
        {"id": m.id, "role": m.role, "content": m.content}
        for m in rows
    ]
```

请求结束 → `yield` 之后的清理关掉 Session。练习挑战题 C1 就是这条链。

---

### 2.5 关系字段直觉（为 N+1 做铺垫）

#### 为什么现在就要碰「关系」？

Agent 几乎总是：

```text
Session（会话）1 —— N Message（消息）
Session 1 —— N ToolCall（工具调用）
```

不会关系，后面 N+1 只能背名词；会一点 `relationship`，预加载才有落点。

#### 怎么写（示意）

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)

    messages: Mapped[list["Message"]] = relationship(back_populates="session")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
```

#### 跑一下（读关系时要想「会不会偷偷再查一次」）

```python
# 伪代码心智：
chat = await session.get(ChatSession, "s1")
for m in chat.messages:  # 若未预加载，这里可能触发额外 SELECT
    print(m.content)
```

默认惰性加载在异步场景更麻烦——**异步下更要显式加载策略**（§4）。这不是细枝末节，是生产常见坑。

#### 易错点

- 循环导入：`ChatSession` / `Message` 互相引用时用字符串注解 `"Message"`，或调整模块结构
- 只建 `relationship` 不建 `ForeignKey`：关系缺少数据库层约束
- 在异步代码里触发隐式 IO（lazy load）→ 直接异常或难查的性能问题

#### 对照

| 概念 | SQL | ORM |
| --- | --- | --- |
| 外键 | `REFERENCES chat_sessions(id)` | `ForeignKey("chat_sessions.id")` |
| 导航 | `JOIN` | `relationship` + 预加载 |

---

## 3. 必掌握：迁移

### 3.1 为什么不要只靠 `create_all`

#### 为什么迁移是「必掌握」而不是「运维细节」？

```text
模型变更 → 生成迁移脚本 → 审查 SQL → 应用到数据库
```

`Base.metadata.create_all(engine)` 适合：

- 内存库单测
- 从零玩具 Demo
- 「表还不存在就创建」的最简路径

它**不适合**当生产演进手段：

| 现实 | `create_all` 做不到的 |
| --- | --- |
| 生产已有数据要保留 | 改列/加非空列需要数据回填策略 |
| 变更需要历史与协作 | 没有版本号，队友不知道库结构走到哪 |
| 回滚 / 多环境一致 | 缺少 upgrade/downgrade 叙事 |
| CI / 预发 / 生产对齐 | 无法可靠复放同一套 DDL |

常见工具：**Alembic**（SQLAlchemy 官方迁移伴侣）。

#### 怎么写（最小心智，命令以你项目配置为准）

```bash
# 一次性：alembic init migrations（目录名按团队约定）
# 配置 sqlalchemy.url 或 env.py 读 DATABASE_URL
# 让 env.py 能 import 到 Base.metadata

alembic revision --autogenerate -m "add messages"
# 审查生成的 upgrade/downgrade SQL —— 这一步不可省
alembic upgrade head
```

链路：

```text
改 models.py
  → alembic revision --autogenerate
  → 人肉审查 upgrade()/downgrade()
  → alembic upgrade head
  → 应用代码依赖新列/新表
```

#### 跑一下（审查时要看什么）

打开生成的迁移文件，确认类似意图（示意）：

```python
def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_messages_session_id", "messages", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_session_id", table_name="messages")
    op.drop_table("messages")
```

问自己：

1. 有没有丢掉列/索引？
2. 加 `NOT NULL` 时旧数据怎么办？
3. `downgrade` 是否可接受（有时生产只保证 forward）？

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| autogenerate 完不审查就 upgrade | 漏检重命名（常被当成 drop+create）、误删 |
| 手工改生产表却不写迁移 | 环境漂移：本地绿、预发红 |
| 迁移里跑难逆的数据删除又无备份 | 回滚叙事破裂 |
| 多个 head 不合并 | 协作时分支迁移冲突 |

#### 对照：`create_all` vs Alembic

| | `create_all` | Alembic |
| --- | --- | --- |
| 从零建表 | 方便 | 也可以，但用迁移更一致 |
| 改已有表 | 基本不管 | 正职 |
| 团队协作 | 弱 | 强（版本表 + 脚本） |
| 教学玩具 | ✅ | 可稍后 |
| 生产 | ❌ 当演进手段 | ✅ |

最小 Alembic 心智再记一句：

> **生成是辅助，审查是责任。**

---

### 3.2 迁移与部署顺序（工程直觉）

#### 为什么「先发代码还是先跑迁移」要有意识？

不兼容变更（删列、改类型）若顺序错了：

```text
新代码读新列，库还是旧结构 → 线上报错
或
库已删列，旧代码仍在写 → 线上报错
```

#### 怎么写（保守策略直觉）

```text
可兼容变更（加可空列 / 加表）：
  先 migrate → 再部署读新列的代码

破坏性变更：
  多步走（expand / migrate / contract）：
  先加新列并双写 → 切读 → 再删旧列
```

本章不要求你成为 DBA；要求你**拒绝**「改完模型直接对生产 create/drop」。

#### 易错点

- 把「我本地 upgrade 过了」当成「所有环境都 upgrade 了」
- CI 不跑迁移、只跑单测内存库——集成环境首次才爆

#### 对照（和上一章衔接）

上一章 PostgreSQL 已埋钩子：「改表不要只在生产手工点」。本章把钩子接到 Alembic 命令与审查习惯上。

---

## 4. 建议掌握：N+1 与仓储

### 4.1 N+1：是什么、为何在 Agent 里高发

#### 为什么 N+1 值得单独练？

列表页 + 关系加载是 ORM 经典雷区。Agent 控制台常见：

```text
查 100 个 session
再循环每个 session 查 messages
→ 1 + 100 次查询
```

会话一多，API 从「几十毫秒」变成「数秒」，而代码看起来只是两层 `for`。

#### 怎么写（坏的形状 vs 好的形状）

坏的形状（逻辑正确、性能错误）：

```python
# 伪代码
sessions = await session.scalars(select(ChatSession).limit(100))
for s in sessions:
    # 每次循环可能再打一条 SELECT messages WHERE session_id = ?
    _ = list(s.messages)
```

缓解思路（记两条就够开始）：

1. **预加载**：`selectinload` / `joinedload` 等  
2. **一次查齐再组装**：先查 sessions，再 `WHERE session_id IN (...)` 查 messages，Python 侧分组

#### 跑一下（用 SQL 次数对照理解）

```python
from sqlalchemy.orm import selectinload
from sqlalchemy import select

# 预加载示意（同步/异步都是「语句上挂 options」）
stmt = (
    select(ChatSession)
    .options(selectinload(ChatSession.messages))
    .limit(100)
)
# result = await session.execute(stmt)
# sessions = list(result.scalars())
# 此后访问 s.messages 不应再爆出 N 次查询
```

心智对比：

```text
N+1:
  SELECT * FROM chat_sessions LIMIT 100;          -- 1
  SELECT * FROM messages WHERE session_id = ?;    -- ×100

selectinload 直觉:
  SELECT * FROM chat_sessions LIMIT 100;          -- 1
  SELECT * FROM messages WHERE session_id IN (...); -- 1（或按批次）
```

`joinedload` 用 JOIN 一次取回；可能放大行数，列表+大集合时要掂量。`selectinload` 常更适合「一对多列表」。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只在开发库用 3 条数据「感觉挺快」 | 上线几百会话后才爆 |
| 异步里依赖隐式 lazy load | 运行期错误或被迫改同步 |
| 无脑全局 `joinedload` 所有关系 | 一次查出巨型图，内存与 SQL 更差 |
| 修了 N+1 却不看 `echo`/`EXPLAIN` | 可能只是换成另一种慢 |

#### 对照：ORM 预加载 vs 手写 SQL

| 做法 | 表达 |
| --- | --- |
| 手写 SQL | `JOIN` 或两个 `IN` 查询 + 应用层组装 |
| ORM | `options(selectinload(...))` / `joinedload(...)` |
| 报表/复杂聚合 | 常直接 SQL/Core 更清晰 |

---

### 4.2 仓储模式直觉

#### 为什么 endpoint 里不该堆满 `select(...)`？

可以跑，但几个月后：

- 同一查询复制到三个路由
- 单测要起 FastAPI 才能测「按 session 列消息」
- 想换数据源/加缓存时，改动面铺满 Web 层

仓储（Repository）把「怎么查库」关进一扇门：

```text
API 层 → Service → Repository(封装查询) → ORM
```

避免 endpoint 里堆满细节查询，方便测试与替换。

#### 怎么写（最小草图）

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session_id: str, role: str, content: str) -> Message:
        msg = Message(session_id=session_id, role=role, content=content)
        self._session.add(msg)
        await self._session.flush()  # 拿到 DB 生成的 id；是否 commit 交给上层事务
        return msg

    async def list_by_session(self, session_id: str) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.id)
        )
        return list(result.scalars())
```

Service 决定「要不要 commit / 和哪些写入同一事务」；Repository 不擅自开闭事务边界（团队约定一致即可）。

#### 跑一下（调用链口述）

```text
POST /messages
  → api_create_message(...)
  → MessageService.append_user_message(...)
  → MessageRepository.add(...)
  → await session.commit()   # 通常在 service 或 unit-of-work 末尾
```

单测可以给 Repository 塞一个真实 AsyncSession（SQLite 内存）或替身，而不必先编 HTTP。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| Repository 里 `commit`，Service 里再 `commit` | 事务边界碎裂，Agent 多表写入难原子 |
| 为「纯净架构」建 mid 层却无行为 | 空包装，读起来更累；有重复查询再抽 |
| API 层仍 `session.execute`「只此一次」 | 一次变十次；防线要一致 |

#### 对照：三层各自问什么

| 层 | 问的问题 |
| --- | --- |
| API | HTTP 状态码、状态校验、鉴权 |
| Service | 业务规则、事务边界、调用 LLM 前后写什么 |
| Repository | 这条 `select` / `insert` 怎么写得对、可测 |

练习 A2 就是逼你画出这扇门。

---

## 5. 了解即可：复杂查询优化

### 5.1 地图：何时离开「日常 ORM CRUD」

#### 为什么这一节只建地图？

窗口函数、CTE、批量插入策略、读写拆分……每个都能开专题。本章目标是：**知道它们存在，慢查询到来时有搜索词**。

#### 怎么用（触发条件）

| 信号 | 可能方向 |
| --- | --- |
| 列表接口随数据量线性变慢 | 索引、N+1、分页 |
| 报表要「每个 session 最后一条消息」 | 窗口函数 / 子查询；可 SQL 或 Core |
| 一次导入十万行 | bulk insert / `COPY`；慎用逐条 `add`+`commit` |
| 多步过滤+聚合难读 | CTE 提升可读性 |

#### 跑一下（保留好奇心即可）

```sql
-- 地图级示例：每个 session 最新一条消息（窗口函数思路）
SELECT session_id, content
FROM (
  SELECT session_id, content,
         ROW_NUMBER() OVER (
           PARTITION BY session_id ORDER BY id DESC
         ) AS rn
  FROM messages
) t
WHERE rn = 1;
```

ORM 也能表达部分窗口函数；**可读性差时允许手写 SQL**——记得参数化。

#### 易错点

- 过早优化：CRUD 都未稳就上分库分表
- 把「了解即可」当成「永远不学」——有 `EXPLAIN ANALYZE` 证据再深入

#### 对照

| 层级 | 工具 |
| --- | --- |
| 日常 CRUD / 关系 | ORM Session |
| 复杂 SQL | `text()` / Core / 视图 |
| 计划与索引 | `EXPLAIN ANALYZE`（上一章地图） |

---

## 6. 综合心智：Agent 写入

### 6.1 同一事务：消息 + 工具记录 + 会话时间戳

#### 为什么 Agent 写入特别怕「写了一半」？

一次用户回合常见要落多处：

```text
同一事务内：
  保存 user message
  保存 tool_call 记录
  更新 session 时间戳
成功 commit；失败 rollback
```

若 user message 进了库、tool_call 失败、session 时间戳没更新：

- 前端时间线错乱
- 计费/审计对不上
- 重试时可能重复插入

事务把这些绑定成原子单元——和模块 01 SQL 章的 `BEGIN/COMMIT` 是同一故事，只是 API 换成了 Session。

#### 怎么写（AsyncSession 示意）

```python
async def persist_turn(
    session: AsyncSession,
    *,
    session_id: str,
    user_text: str,
    tool_name: str,
    tool_payload: str,
) -> None:
    session.add(
        Message(session_id=session_id, role="user", content=user_text)
    )
    session.add(
        ToolCall(
            session_id=session_id,
            name=tool_name,
            payload=tool_payload,
        )
    )
    chat = await session.get(ChatSession, session_id)
    if chat is None:
        raise ValueError("unknown session")
    chat.updated_at = datetime.now(UTC)  # 字段名按你的模型

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise
```

`ToolCall` / `updated_at` 按你表结构替换；重点是**边界**，不是字段表。

#### 跑一下（失败注入心智）

```text
正常：
  add message, add tool_call, touch session → commit → 三处都可见

中途抛错（校验失败 / DB 约束）：
  rollback → 三处都不可见
  API 返回 4xx/5xx，客户端可安全重试（注意幂等，见队列章）
```

自己用测试故意 `raise` 在 `commit` 前，查库确认「没有半套数据」。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 每条 `add` 都立刻 `commit` | 失去原子性 |
| LLM 调用包在超长 DB 事务里 | 连接被占满；应「短事务」：先提交需要的、或事务外调 LLM 再写结果 |
| 重试无幂等键 | 网络重试导致重复 message |
| Session 跨请求传递 | 状态与连接泄漏 |

#### 对照：和「纯 SQL 事务」同一张图

```text
SQL:     BEGIN → INSERT → INSERT → UPDATE → COMMIT|ROLLBACK
ORM:     async with Session → add/add/modify → await commit()|rollback()
```

仓储负责「单次读写怎么写」；Service / 用例负责「哪些读写同一事务」。Agent 写入心智落在**后者**。

---

### 6.2 和 FastAPI / 队列的边界（避免反模式）

#### 为什么要提边界？

ORM Session ≠ 任务队列；也 ≠ HTTP 请求本身。

| 场景 | 建议 |
| --- | --- |
| 请求内短 CRUD | 请求级 Session + 事务 |
| 长 LLM 调用 | 事务外调用；需要落库的状态分段提交 |
| 后台 worker | worker 内自管 Session；别共用请求 Session |

#### 易错点

- 把 `BackgroundTasks` 当成「一定可靠的写入」（不可靠边界见 Web 章刻意简化）
- 在已关闭的 Session 上懒加载消息列表

#### 对照（模块航线）

```text
06 Web：Depends(yield Session)
07 本章：模型 / 事务 / N+1 / 迁移
07 后章：缓存与队列 —— 真源仍在 DB，缓存是加速，队列是异步边界
```

---

## 7. 练习指引

[`exercises/07-data-persistence/03-orm.md`](../../exercises/07-data-persistence/03-orm.md)

建议路径：

1. **B1** 用自己的话写清「为何 SQLAlchemy 生态」——对照 §1.2  
2. **B2～B3** 在 `playground/07-data-persistence/03-orm/` 用 SQLite 跑通模型 + Session CRUD；有余力改异步  
3. **B4** 解释 `create_all` 与迁移——对照 §3  
4. **A1 / A2** 选一：N+1 伪代码或 `MessageRepository`  
5. **C1** 画 Depends → service → repo 链

---

## 8. 小结与下一站

### 自检

- [ ] 能解释模型/表/Session/commit，并说出 2.x `select()` 基本读法
- [ ] 知道异步路由为何优先 `AsyncSession`，以及禁止在 `async def` 里跑同步 Session
- [ ] 知道迁移的价值，能描述 Alembic「生成 → 审查 → upgrade」
- [ ] 能描述 N+1 现象，并说出至少一种缓解（预加载或 IN 查询组装）
- [ ] 能说出仓储分层直觉，以及 Agent 多表写入的同一事务心智

### 关键句（可默念）

> ORM 映射对象；Session 划定工作单元；迁移演进结构；预加载控制查询次数；Agent 多写必须同事务。

### 下一章

[`04-redis-cache.md`](./04-redis-cache.md) —— 缓存加速与限流计数。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[PostgreSQL](./02-postgresql.md)
- 下一章：[缓存与 Redis](./04-redis-cache.md)
