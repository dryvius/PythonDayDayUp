# 练习：Python ORM

> 对应文档：[`docs/07-data-persistence/03-orm.md`](../../docs/07-data-persistence/03-orm.md)  
> 状态：`已完成出题`  
> 建议用时：80～120 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 可用 **SQLite + SQLAlchemy 2.x** 完成（降低环境门槛）。
4. 建议目录：

```text
playground/07-data-persistence/03-orm/
  models.py
  db.py
  crud_demo.py
  notes.md
```

5. Python ≥ 3.11；类型注解使用现代写法。
6. 先自己做完再看文末答案。

---

## 热身题（建议先做）

### W1. ORM 一句话

**要求**：用一句话说明 ORM 帮你把什么映射到什么。

**验收**：对象/类 ↔ 表/行。

---

### W2. Session 不是 HTTP Session

**要求**：用两句话区分：SQLAlchemy `Session` vs Web「登录会话」。

**验收**：前者是工作单元/DB 会话；后者是用户状态。

---

### W3. commit 直觉

**要求**：插入对象后若忘记 `commit`，通常会发生什么？

**验收**：事务未持久化（连接关闭可能回滚）。

---

### W4. 依赖版本

**要求**：写出你将安装的包名（如 `sqlalchemy`），并用命令确认版本。

**验收**：环境可 import。

---

## 基础题（必做）

### B1. 选型说明（书面）

为何本路线优先熟悉 **SQLAlchemy** 生态？列 **3 条**（可结合 FastAPI、迁移、异步驱动、社区等）。

**验收**：3 条具体，不重复吹「流行」。

---

### B2. 模型 + create_all

定义 `Message` 模型，字段至少：

- `id`
- `session_id`
- `role`
- `content`
- （建议）`created_at`

使用 SQLAlchemy 2.x 风格（`DeclarativeBase` / `Mapped` 优先）。  
`create_all` 到 SQLite 文件。

**验收**：运行后出现表；`PRAGMA table_info` 或检查器能看到列。

---

### B3. Session CRUD

在脚本中完成：

1. 插入 2 条消息  
2. 按 `session_id` 查询  
3. 更新一条 `content`  
4. 删除 1 条  

注意：`commit` / 异常时 `rollback`。

**验收**：每一步有打印或 assert；异常路径至少在注释里说明如何 rollback。

---

### B4. 迁移认知（书面）

解释：

1. 为何生产环境不能只靠 `create_all`？  
2. 迁移工具（如 Alembic）主要解决什么问题？

**验收**：提到已有数据表结构演进、可重复/可审阅的变更脚本。

---

## 进阶题（建议至少做 1 题）

### A1. N+1 故事题

用**伪代码或可运行小例子**展示 N+1：

- 先查 sessions 列表  
- 循环中再查每个 session 的 messages  

再写一种修复：预加载 / join / 合并查询（任选其一直方）。

**验收**：前后对比能看出「1+N 次查询」vs「更少往返」。

---

### A2. Repository 草图

实现 `MessageRepository`，封装：

- `add(...)`
- `list_by_session(session_id: int) -> list[Message]`

约定：API 层（可写假函数）不直接拼 SQL / 不直接操作 Session 细节（Session 由 repo 或调用方注入，二选一但要一致）。

**验收**：有类；演示调用 2～3 行。

---

## 挑战题（可选）

### C1. 与 FastAPI Depends 结合草图

用文字或伪代码画出：

```text
请求 → Depends(get_db) → service → repo → DB
```

写清：`get_db` 如何 yield Session，以及请求结束时关闭/回收。

**验收**：生命周期说清；不要在全局单例 Session 上胡写并发。

---

### C2. 约束下沉

在模型或表上体现 `role` 合法值约束（DB `CHECK` 或校验层），并演示非法 role 失败。

**验收**：失败发生在 DB 或 Pydantic/校验层，有明确错误。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1～W3 参考答案

- W1：把 Python 类/实例映射到数据库表/行，并用 API 表达查询与持久化。  
- W2：SQLAlchemy Session 管理一组对象与事务；HTTP session 是用户浏览器会话状态，二者同名不同物。  
- W3：变更停在事务中，未 commit 则其它连接看不到，连接结束常回滚。

### W4 参考答案

```bash
pip install "sqlalchemy>=2.0"
python -c "import sqlalchemy as sa; print(sa.__version__)"
```

---

### B1 思路 + 参考答案

**参考答案**：

1. 与 FastAPI 文档/社区示例高度同路，Depends + Session 模式成熟  
2. Alembic 迁移是 Python Web 常见标配，利于 schema 演进  
3. 同步/异步（如 `asyncpg`）扩展路径清晰，从 SQLite 练习可平滑迁到 PG  

---

### B2 / B3 思路 + 参考答案

**思路**：2.x 用 `Mapped`/`mapped_column`；CRUD 包在 `with Session` 里。

**参考答案**

```python
# models.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
```

```python
# db.py
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base

ENGINE = create_engine("sqlite:///orm_practice.db", echo=False)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=ENGINE)


def get_session() -> Session:
    return SessionLocal()
```

```python
# crud_demo.py
from __future__ import annotations

from sqlalchemy import select

from db import get_session, init_db
from models import Message


def main() -> None:
    init_db()
    session = get_session()
    try:
        # create
        session.add_all(
            [
                Message(session_id=1, role="user", content="hi"),
                Message(session_id=1, role="assistant", content="hello"),
            ]
        )
        session.commit()

        # read
        rows = session.scalars(
            select(Message).where(Message.session_id == 1).order_by(Message.id)
        ).all()
        assert len(rows) >= 2

        # update
        rows[0].content = "hi (edited)"
        session.commit()

        # delete
        session.delete(rows[1])
        session.commit()

        left = session.scalars(select(Message).where(Message.session_id == 1)).all()
        print("left:", [(m.id, m.content) for m in left])
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
```

---

### B4 思路 + 参考答案

**参考答案**：

1. `create_all` 主要「没有则创建」，不会安全地处理「改列/删列/改约束/数据回填」；生产库有数据，硬改会丢数据或不一致。  
2. 迁移工具把 schema 变更做成可版本化、可审查、可重复执行的脚本，支持升级/（部分）降级与多环境对齐。

---

### A1 思路 + 参考答案

**思路**：循环里查询 = N+1；一次取出关联数据。

**参考答案（伪代码）**

```python
# 坏：N+1
sessions = db.query(SessionModel).all()  # 1 次
for s in sessions:
    msgs = db.query(Message).filter_by(session_id=s.id).all()  # N 次
    print(s.id, len(msgs))

# 好：预加载（示意）
from sqlalchemy.orm import selectinload

sessions = db.scalars(
    select(SessionModel).options(selectinload(SessionModel.messages))
).all()  # 通常 1～2 次 SQL，而不是 1+N
for s in sessions:
    print(s.id, len(s.messages))
```

若尚未建 relationship，也可用一次 `SELECT * FROM messages WHERE session_id IN (...)` 在内存分组。

---

### A2 思路 + 参考答案

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Message


class MessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, session_id: int, role: str, content: str) -> Message:
        message = Message(session_id=session_id, role=role, content=content)
        self._session.add(message)
        self._session.commit()
        self._session.refresh(message)
        return message

    def list_by_session(self, session_id: int) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.id)
        )
        return list(self._session.scalars(stmt))


# API 层示意
def api_list_messages(session_id: int, db: Session) -> list[dict]:
    repo = MessageRepository(db)
    return [
        {"id": m.id, "role": m.role, "content": m.content}
        for m in repo.list_by_session(session_id)
    ]
```

---

### C1 思路 + 参考答案

```python
from collections.abc import Generator

from sqlalchemy.orm import Session

from db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 路由示意
# def list_messages(session_id: int, db: Session = Depends(get_db)) -> list[dict]:
#     return api_list_messages(session_id, db)
```

调用链：请求进入 → Depends 打开 Session → service/repo 用同一 Session → 响应结束 `close`。不要用全局共享可变 Session 服务并发请求。

---

### C2 思路 + 参考答案

```python
from sqlalchemy import CheckConstraint

class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('system','user','assistant','tool')",
            name="ck_messages_role",
        ),
    )
    # ... 字段同 B2
```

非法 role insert 时应失败；应用层也可用 Pydantic 先拦一层。

---

## 附录：Session 生命周期速查

```text
打开 Session
  → add / execute / scalars
  → flush（可选，SQL 先发但未提交）
  → commit（持久化）或 rollback（撤销）
关闭 Session
```

易错点：

1. **长时间挂着 Session 当缓存**：对象过期、连接占满。  
2. **commit 后继续用过期对象不 refresh**：读到旧状态。  
3. **在 API 全局单例 Session**：并发请求互相踩。  
4. **捕获异常后不 rollback**：同一 Session 后续语句继续失败。  

推荐请求级：

```python
db = SessionLocal()
try:
    ...
    db.commit()
except Exception:
    db.rollback()
    raise
finally:
    db.close()
```

---

## 附录：自检问题

- [ ] 能否口述 ORM 与「手写 SQL」各自适合什么？  
- [ ] 能否解释 N+1 的形状与一种修复？  
- [ ] 能否说明为何生产要用迁移而不是只靠 `create_all`？  
