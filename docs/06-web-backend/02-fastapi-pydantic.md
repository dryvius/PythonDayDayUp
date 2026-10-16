# FastAPI + Pydantic

> 所属模块：`06-web-backend` · Web 后端  
> 状态：`已完成正文`  
> 建议学时：4～7 小时  
> 对应练习：[`exercises/06-web-backend/02-fastapi-pydantic.md`](../../exercises/06-web-backend/02-fastapi-pydantic.md)

## 本章定位

- **本章角色**：用 FastAPI 真正写出可用的 JSON API；用 Pydantic 做请求/响应校验——这也是 Agent 服务化的主工具链。
- **安装**：`pip install fastapi uvicorn pydantic`（或 uv add）。

## 学习目标

1. 定义路由、路径/查询参数、请求体。
2. 用 Pydantic 模型描述输入输出，并处理校验错误。
3. 使用依赖注入组织可复用逻辑（配置、鉴权前置）。
4. 会看 OpenAPI 文档，了解后台任务。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 路由与依赖注入、请求/响应模型、校验错误处理 | 能独立写 CRUD 风格 API |
| **建议掌握** | OpenAPI、后台任务 | 会用文档调试、会丢异步收尾任务 |
| **了解即可** | 自定义依赖进阶 | 地图 |

---

## 1. Hello API

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(title="agent-api", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

启动：

```bash
uvicorn app.main:app --reload --port 8000
```

访问：`http://127.0.0.1:8000/health`  
文档：`http://127.0.0.1:8000/docs`

---

## 2. 必掌握：路由与参数

```python
from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/items/{item_id}")
def get_item(item_id: int, q: str | None = Query(default=None, max_length=50)):
    return {"item_id": item_id, "q": q}


@app.post("/echo")
async def echo(payload: dict) -> dict:
    return {"you_sent": payload}
```

- 路径参数：`/items/{item_id}`
- 查询参数：`?q=...`
- `async def`：内部有 await I/O 时使用

---

## 3. 必掌握：Pydantic 请求/响应模型

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    temperature: float = Field(default=0.2, ge=0, le=2)


class ChatResponse(BaseModel):
    reply: str
    model: str


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    # 假装 LLM
    return ChatResponse(reply=f"ECHO: {body.message}", model="echo")
```

好处：

- 自动校验类型与边界
- 自动生成 OpenAPI schema
- 响应可裁剪多余字段（`response_model`）

Pydantic v2 是主流；看到 `model_validate` / `model_dump` 是 v2 API。

---

## 4. 必掌握：校验错误处理

非法请求会返回 **422**，body 类似：

```json
{"detail":[{"loc":["body","message"],"msg":"...","type":"..."}]}
```

自定义：

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"ok": False, "error": "validation_failed", "detail": exc.errors()},
    )
```

业务错误用 `HTTPException`：

```python
from fastapi import HTTPException


raise HTTPException(status_code=404, detail="session not found")
```

---

## 5. 必掌握：依赖注入（Depends）

```python
from fastapi import Depends
from dataclasses import dataclass


@dataclass
class Settings:
    model: str = "echo"


def get_settings() -> Settings:
    return Settings()


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    return ChatResponse(reply=f"ECHO: {body.message}", model=settings.model)
```

用途：

- 注入配置、DB session、当前用户
- 鉴权依赖（下一章）
- 测试时覆盖依赖

这和 OOP 章的「依赖注入直觉」同构。

---

## 6. 建议掌握：OpenAPI 与后台任务

### OpenAPI

`/docs`（Swagger UI）、`/redoc` 自动来自你的类型注解。  
前后端协作、Agent 工具自描述 API，都很有用。

### 后台任务

```python
from fastapi import BackgroundTasks


def write_log(message: str) -> None:
    ...


@app.post("/v1/chat")
async def chat(body: ChatRequest, tasks: BackgroundTasks) -> ChatResponse:
    tasks.add_task(write_log, body.message)
    return ChatResponse(reply="ok", model="echo")
```

适合：快速返回后写日志/轻量收尾。  
重任务仍应用队列（模块 07 消息队列直觉）。

---

## 7. 了解即可：自定义依赖进阶

可调用类依赖、带 yield 的依赖（类似上下文，做 setup/teardown）、多级依赖链。  
CRUD 做熟后再深挖。

---

## 8. 综合小例子：Agent Run API 骨架

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    query: str = Field(min_length=1)
    max_steps: int = Field(default=5, ge=1, le=20)


class AgentRunResponse(BaseModel):
    answer: str
    steps: int


app = FastAPI(title="mini-agent")


@app.post("/v1/agent/run", response_model=AgentRunResponse)
async def run_agent(body: AgentRunRequest) -> AgentRunResponse:
    if body.query.strip().lower() == "boom":
        raise HTTPException(status_code=400, detail="bad query")
    # 真实项目：await agent.arun(body.query)
    return AgentRunResponse(answer=f"done:{body.query}", steps=1)
```

---

## 9. 常见坑

1. 用可变对象当全局状态还不加锁
2. 在 async 路由里调用同步 HTTP 客户端
3. 返回任意 dict 却期望严格 schema——请用 `response_model`
4. 把密钥写进代码；应走环境变量 + Depends 配置

---

## 10. 练习指引

[`exercises/06-web-backend/02-fastapi-pydantic.md`](../../exercises/06-web-backend/02-fastapi-pydantic.md)

---

## 11. 小结与下一站

### 自检

- [ ] 能写 GET/POST + Pydantic 模型
- [ ] 能看懂 422 校验错误
- [ ] 会用 Depends 注入配置

### 下一章

[`03-auth.md`](./03-auth.md) —— 认证与授权：API Key / JWT / RBAC 地图。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Web 框架原理](./01-web-framework-principles.md)
- 下一章：[认证与授权](./03-auth.md)
