# Python ORM

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/07-data-persistence/03-orm.md`](../../exercises/07-data-persistence/03-orm.md)

## 本章定位

- **本章角色**：用 ORM（以 SQLAlchemy 2.x 思维为主）把表映射成 Python 类；掌握 Session、迁移与 N+1 意识。
- **原则**：ORM 是工具，不是免除 SQL；复杂报表仍可能手写 SQL。

## 学习目标

1. 说清 ORM 选型关注点（SQLAlchemy / 其它）。
2. 定义模型并用 Session 完成读写。
3. 理解迁移为何必要。
4. 能识别 N+1，知道仓储模式直觉。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 选型、模型与会话、迁移 | 能做基础 CRUD |
| **建议掌握** | N+1、仓储模式 | 能避免低级性能坑 |
| **了解即可** | 复杂查询优化 | 地图 |

---

## 1. ORM 是什么 / 如何选型

ORM = Object-Relational Mapping：类 ↔ 表，实例 ↔ 行。

| 工具 | 备注 |
|------|------|
| **SQLAlchemy** | Python 事实标准，灵活 |
| SQLModel | 偏 FastAPI/Pydantic 风格，底层仍常靠 SQLAlchemy |
| Django ORM | 绑 Django 生态 |
| Tortoise / others | 异步生态选项 |

本路线以 **SQLAlchemy 概念**为准；具体 API 以你安装的大版本文档为准。

---

## 2. 必掌握：模型与会话

概念模型（示意）：

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
```

Session 直觉：

```text
打开 Session
  → 查询/修改对象
  → commit 提交
  → 出错 rollback
  → close
```

FastAPI 中常用依赖 `yield` Session，请求结束关闭。

参数化/绑定由 ORM 处理，降低 SQL 注入风险（仍不要拼字符串 SQL）。

### 异步路由注意（与模块 05/06 对齐）

同步 `session.execute(...)` **会阻塞事件循环**。二选一：

| 做法 | 适用 |
|------|------|
| `AsyncSession` + `await session.execute(...)` | `async def` 路由（推荐与 FastAPI 异步主线一致） |
| 同步 Session + 普通 `def` 路由（框架丢线程池）或 `asyncio.to_thread` | 暂时只有同步 ORM 代码 |

**不要**在 `async def` 里直接跑同步 Session。

AsyncSession 读写直觉（API 以你安装的 SQLAlchemy 版本文档为准）：

```python
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(os.environ["DATABASE_URL"])  # 例：postgresql+asyncpg://...
Session = async_sessionmaker(engine, expire_on_commit=False)


async def list_messages(session_id: str) -> list[Message]:
    async with Session() as session:
        result = await session.execute(
            select(Message).where(Message.session_id == session_id).order_by(Message.id)
        )
        return list(result.scalars())
```

最小 Alembic 心智（命令以你项目配置为准）：

```bash
alembic revision --autogenerate -m "add messages"
# 审查生成的 upgrade/downgrade SQL
alembic upgrade head
```

---

## 3. 必掌握：迁移

```text
模型变更 → 生成迁移脚本 → 审查 SQL → 应用到数据库
```

常见工具：**Alembic**。

为什么不要只靠 `create_all`：

- 生产数据要保留
- 变更需要历史与协作
- 回滚/多环境一致

---

## 4. 建议掌握：N+1 与仓储

### N+1

```text
查 100 个 session
再循环每个 session 查 messages
→ 1 + 100 次查询
```

缓解：joinedload / selectinload 等预加载；或一次查齐再组装。

### 仓储模式直觉

```text
API 层 → Service → Repository(封装查询) → ORM
```

避免 endpoint 里堆满细节查询，方便测试与替换。

---

## 5. 了解即可：复杂查询优化

窗口函数、CTE、批量插入策略……有慢查询再专项学。

---

## 6. 综合心智：Agent 写入

```text
同一事务内：
  保存 user message
  保存 tool_call 记录
  更新 session 时间戳
成功 commit；失败 rollback
```

---

## 7. 练习指引

[`exercises/07-data-persistence/03-orm.md`](../../exercises/07-data-persistence/03-orm.md)

---

## 8. 小结与下一站

### 自检

- [ ] 能解释模型/表/Session/commit
- [ ] 知道迁移的价值
- [ ] 能描述 N+1 现象

### 下一章

[`04-redis-cache.md`](./04-redis-cache.md) —— 缓存加速与限流计数。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[PostgreSQL](./02-postgresql.md)
- 下一章：[缓存与 Redis](./04-redis-cache.md)
