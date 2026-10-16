# Project 2：FastAPI Todo

> 状态：`已完成实战说明`  
> 建议时机：完成模块 05～07 核心后（至少 FastAPI + SQL/ORM 入门）  
> 建议工时：10～18 小时  
> 推荐目录：`playground/projects/02-fastapi-todo/`

## 项目目标

实现带持久化的 Todo REST API：CRUD、校验、基础认证、测试，为后面 Agent API 打样。

## 你将练习到的能力

| 模块 | 知识点 |
|------|--------|
| 05 | 可选：`async` 路由；同步 ORM 亦可先跑通 |
| 06 | FastAPI、Pydantic、Depends、API Key、422/401 |
| 07 | SQL/ORM、Session、迁移意识；可选 Redis 缓存列表 |

工程实践：分层（router / service / repository）、结构化日志、`pytest` + `TestClient`、Docker Compose 起 Postgres（可选 SQLite 起步）。

## 需求概述

### 功能

1. `POST /v1/todos` 创建（title 必填、done 默认 false）  
2. `GET /v1/todos` 列表（可选 `?done=` 过滤）  
3. `GET /v1/todos/{id}`、`PATCH /v1/todos/{id}`、`DELETE /v1/todos/{id}`  
4. 全站（除 `/health`）需要 `X-API-Key`  
5. 404 / 422 / 401 行为正确  

### 非功能

- Pydantic v2 请求/响应模型  
- DB 为真源；重启不丢数据  
- 至少健康检查 + 创建/列表的自动化测试  
- 配置来自环境变量（`APP_API_KEY`、`DATABASE_URL`）  

## 建议目录

```text
playground/projects/02-fastapi-todo/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── deps.py              # get_db / require_api_key
│   ├── models.py            # SQLAlchemy
│   ├── schemas.py           # Pydantic
│   ├── routers/todos.py
│   └── services/todo_service.py
├── tests/
│   └── test_todos.py
├── alembic/                 # 可选；SQLite 可用 create_all 学习期
├── compose.yaml             # 可选 postgres
├── pyproject.toml
├── .env.example
└── README.md
```

## 里程碑

- [ ] **M1**：内存或 SQLite；无鉴权 CRUD 跑通 + `/docs`  
- [ ] **M2**：API Key；Pydantic；404；服务层抽离  
- [ ] **M3**：pytest ≥4；日志带 request_id；README 含 curl 示例  

## 验收标准

- [ ] OpenAPI 中模型字段清晰  
- [ ] 错误 Key → 401；缺 title → 422  
- [ ] 测试不依赖手工清库（用 fixture / 事务回滚或独立测试 DB）  
- [ ] 密钥仅环境变量  

## 延伸挑战

- 用户维度：Todo 归属 `user_id`（多 Key 映射）  
- Redis 缓存 `GET` 列表，写路径删缓存  
- 异步 SQLAlchemy + `AsyncSession`  

## 导航

- 返回项目列表：[./README.md](./README.md)
- 相关文档：[FastAPI](../06-web-backend/02-fastapi-pydantic.md) · [认证](../06-web-backend/03-auth.md) · [ORM](../07-data-persistence/03-orm.md)
- 返回总览：[../../README.md](../../README.md)
