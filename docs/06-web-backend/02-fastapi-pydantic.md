# FastAPI + Pydantic

> 所属模块：`06-web-backend` · Web 后端  
> 状态：`已完成正文`  
> 建议学时：4～7 小时（有 Express / Nest / 前端 fetch 经验可更快；Depends 与 422 建议动手踩一遍）  
> 对应练习：[`exercises/06-web-backend/02-fastapi-pydantic.md`](../../exercises/06-web-backend/02-fastapi-pydantic.md)  
> 环境约定：Python ≥ 3.11；注解用 `list[str]`、`str | None`；Pydantic **v2**（`model_validate` / `model_dump`）

## 本章定位

- **模块目标**：能独立搭建并理解后端 API 服务。
- **本章角色**：用 FastAPI 真正写出可用的 JSON API；用 Pydantic 做请求/响应校验——这也是 Agent 服务化的主工具链。
- **前置**：上一章的请求生命周期、路由/中间件、同步 vs 异步处理；HTTP 基础（模块 04）、asyncio（模块 05）。
- **你的优势**：若写过 Express / Nest / 前端 `fetch` + TypeScript 类型，心智模型几乎一一对应；差异主要在「类型注解驱动路由与文档」。
- **安装**：`pip install fastapi uvicorn pydantic`（或 `uv add fastapi uvicorn`；`fastapi` 常会带上 pydantic）。

## 学习目标（学完应能做到）

1. 定义路由、路径/查询参数、请求体，并用 `uvicorn` 跑通。
2. 用 Pydantic v2 模型描述输入输出，并读懂 / 自定义校验错误（422）。
3. 使用 `Depends` 组织可复用逻辑（配置、鉴权前置、测试覆盖）。
4. 会看 OpenAPI（`/docs`），会用 `BackgroundTasks` 做轻量收尾，并知道长任务应上队列。
5. 能搭出最小的 Agent Run API 骨架，为下一章鉴权与项目线铺路。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 路由与参数、请求/响应模型、校验错误、Depends | 能独立写 CRUD 风格 JSON API |
| **建议掌握** | OpenAPI、BackgroundTasks | 会用文档调试、会丢轻量异步收尾 |
| **了解即可** | 自定义依赖进阶（可调用类、`yield` 依赖） | 建地图；CRUD 做熟后再深挖 |

---

## 1. 为什么要学（和 Agent 有什么关系）

Agent 很少永远只跑在 CLI 里。服务化之后常见形状是：

```text
前端 / 其它服务 / 定时任务
        --HTTP JSON-->  你的 FastAPI
                           → 校验入参（Pydantic）
                           → 注入配置 / 当前用户（Depends）
                           → 调 LLM / Tool / 检索
                           → 按 response_model 裁剪出参
                           → 返回 JSON + OpenAPI 文档
```

没有类型与校验时，你会反复踩：

- 客户端漏传字段 → 运行时 `KeyError`
- `temperature=999` → 模型行为诡异却难排查
- 响应多吐了内部字段 → 泄漏实现细节
- 前后端对「字段名 / 必填 / 默认值」各说各话

FastAPI + Pydantic 把「契约」写在 Python 类型里：运行时校验、文档自动生成、IDE 补全，一套注解多方受益。

可以先记一句：

> FastAPI 负责「HTTP 怎么进怎么出」；Pydantic 负责「数据长什么样、合不合法」。

---

## 2. 必掌握：Hello API

这一节会刻意写细——后面所有路由、模型、依赖，都站在「一个可启动的 `app`」之上。

### 2.1 最小应用

#### 为什么需要 Hello API？

先确认三件事能通，再堆业务：

1. 进程能起来（`uvicorn` 找到 `app`）
2. 路由能匹配（`GET /health`）
3. 文档能打开（`/docs`）——证明类型注解已被框架读到

Agent 服务里 `/health` 几乎是标配：编排、K8s、负载均衡都靠它判断「进程还活着」。

#### 怎么写

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(title="agent-api", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

要点：

| 片段 | 含义 |
| --- | --- |
| `FastAPI(...)` | 创建 ASGI 应用；`title`/`version` 会出现在 OpenAPI |
| `@app.get("/health")` | 把 `GET /health` 绑到函数 |
| `-> dict[str, str]` | 返回类型注解；帮助文档与序列化 |
| 普通 `def` | 无 `await` 时可用；框架会丢线程池执行（见上一章） |

项目布局建议（与练习一致）：

```text
app/
  __init__.py   # 可为空
  main.py       # 里面有 app = FastAPI(...)
```

`uvicorn` 的导入路径是 **`模块:变量`**：`app.main:app` = 文件 `app/main.py` 里的 `app` 对象。

#### 跑一下

在项目根目录（能 `import app` 的那一层）：

```bash
uvicorn app.main:app --reload --port 8000
```

| 地址 | 用途 |
| --- | --- |
| `http://127.0.0.1:8000/health` | 健康检查 JSON |
| `http://127.0.0.1:8000/docs` | Swagger UI（交互试接口） |
| `http://127.0.0.1:8000/redoc` | ReDoc（阅读型文档） |
| `http://127.0.0.1:8000/openapi.json` | 原始 OpenAPI schema |

用浏览器或 curl：

```bash
curl http://127.0.0.1:8000/health
```

期望：

```json
{"status":"ok"}
```

`--reload`：改代码自动重启，本地开发友好；生产部署不要开。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 在错误目录启动 | `ModuleNotFoundError: No module named 'app'` |
| 写成 `uvicorn main:app` 但文件在 `app/main.py` | 找不到模块或找到错误的 `main` |
| 端口被占用 | `Address already in use`；换 `--port` 或关掉旧进程 |
| 把 `app = FastAPI()` 写在 `if __name__` 里才创建 | `uvicorn` 导入时可能拿不到 `app` |
| 只访问 `/` 却没定义根路由 | 404；Hello 阶段先保证 `/health` |

#### 前端 / TS 对照

```typescript
// 前端：自己声明类型 + 手写 fetch
type Health = { status: string }

async function getHealth(): Promise<Health> {
  const res = await fetch("http://127.0.0.1:8000/health")
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<Health>
}
```

```python
# FastAPI：类型写在服务端，文档与校验跟着来
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

| 概念 | 前端 / Express 直觉 | FastAPI |
| --- | --- | --- |
| 应用实例 | `const app = express()` | `app = FastAPI()` |
| 注册路由 | `app.get("/health", handler)` | `@app.get("/health")` |
| 启动 | `app.listen(8000)` | `uvicorn app.main:app` |
| 健康检查 | 手写 JSON | 同上，但顺带进 OpenAPI |

---

### 2.2 `def` 还是 `async def`？（Hello 阶段先定规矩）

#### 为什么现在就要提？

上一章说过：在 `async def` 里同步阻塞会卡住事件循环。Hello 阶段养成习惯，后面接 LLM / DB 不会返工。

#### 怎么写（选型口诀）

| 场景 | 推荐 |
| --- | --- |
| 纯内存、无 I/O（如 `/health`、简单 echo） | `def` 或 `async def` 均可 |
| 内部有 `await`（httpx、异步 ORM、asyncio） | 必须 `async def` |
| 只有同步阻塞库（`requests`、重 CPU） | 用 `def`（线程池）或 `asyncio.to_thread` |

```python
# 可以：无 I/O
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# 可以：真有 await
@app.get("/health-async")
async def health_async() -> dict[str, str]:
    return {"status": "ok"}


# 千万别：async 里同步睡 / 同步 HTTP
@app.get("/bad")
async def bad() -> dict[str, str]:
    import time
    time.sleep(3)  # 卡住事件循环
    return {"status": "ok"}
```

#### 易错点

- 「全部写成 `async def` 就一定更快」——没有 await 的 async 函数没有魔法加速
- 把 `time.sleep` / `requests.get` 塞进 async 路由——上一章重点坑，这里再钉一次

---

## 3. 必掌握：路由与参数

路径参数、查询参数、请求体，是 API 契约的三块积木。Agent 的 `/v1/chat`、`/sessions/{id}` 全靠它们。

### 3.1 路径参数（Path）

#### 为什么需要路径参数？

标识「资源是哪一个」时，REST 习惯放在路径里：

```text
GET /sessions/42
GET /items/7
```

比 `GET /sessions?session_id=42` 更表达「这就是资源 ID」。

#### 怎么写

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
def get_item(item_id: int) -> dict[str, int]:
    return {"item_id": item_id}
```

- `{item_id}`：路径里的占位符
- `item_id: int`：FastAPI 按类型把字符串转成 `int`；转失败 → 校验错误（422）

多个路径参数同理：`/users/{user_id}/sessions/{session_id}`。

#### 跑一下

```bash
curl http://127.0.0.1:8000/items/42
# {"item_id":42}

curl http://127.0.0.1:8000/items/abc
# 422 —— 无法把 "abc" 解析成 int
```

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 函数参数名 ≠ 路径占位符名 | `{item_id}` 必须对应参数 `item_id` |
| 需要「不存在返回 404」却只靠类型 | 类型只保证是 int；业务上不存在要用 `HTTPException`（见 §5、§9） |
| 把可选资源 ID 放进路径又标成可选 | 路径段通常是必填；可选过滤条件用查询参数 |

#### 前端 / TS 对照

```typescript
// 前端拼 URL
const itemId = 42
await fetch(`/items/${itemId}`)
```

```python
# 后端声明「这一段必须是 int」
@app.get("/items/{item_id}")
def get_item(item_id: int) -> dict[str, int]:
    return {"item_id": item_id}
```

| | Express | FastAPI |
| --- | --- | --- |
| 声明 | `app.get("/items/:item_id", ...)` | `@app.get("/items/{item_id}")` |
| 取值 | `req.params.item_id`（字符串） | 注解为 `int` 则已转换 |
| 非法 ID | 自己 `parseInt` + 判错 | 自动 422 |

---

### 3.2 查询参数（Query）

#### 为什么需要查询参数？

过滤、分页、搜索词——**不是**资源身份本身，而是「怎么取这份资源」：

```text
GET /items/42?q=hello&limit=10
```

#### 怎么写

```python
from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/items/{item_id}")
def get_item(
    item_id: int,
    q: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=10, ge=1, le=100),
) -> dict[str, object]:
    return {"item_id": item_id, "q": q, "limit": limit}
```

规则直觉：

1. **简单类型 + 有默认值 / `None`** → 通常是查询参数
2. **路径里写了 `{name}`** → 路径参数
3. **Pydantic 模型类型** → 请求体（下一节）
4. 需要校验边界时，用 `Query(...)` / `Path(...)` / `Field(...)` 写约束

`Query` 常用参数（与 Pydantic `Field` 同类思路）：

| 参数 | 含义 |
| --- | --- |
| `default` | 默认值；`None` 表示可省略 |
| `max_length` / `min_length` | 字符串长度 |
| `ge` / `le` | 数值 ≥ / ≤（greater/less or equal） |
| `description` | 进 OpenAPI，给前端/同事看 |

#### 跑一下

```bash
curl "http://127.0.0.1:8000/items/1?q=hi&limit=5"
# {"item_id":1,"q":"hi","limit":5}

curl "http://127.0.0.1:8000/items/1?limit=999"
# 422 —— limit 超出 le=100
```

#### 易错点

- 忘记给「可选查询参数」默认值 → FastAPI 会当成**必填**查询参数
- 用可变默认值（如 `[]`）——和普通 Python 一样危险；查询参数场景用 `None` 再在函数里处理
- `bool` 查询参数：`?flag=true` / `1` / `yes` 等会被解析；别假设只有 `"true"`

#### 前端 / TS 对照

```typescript
const params = new URLSearchParams({ q: "hi", limit: "5" })
await fetch(`/items/1?${params}`)
```

```ts
// NestJS 风格直觉
// @Query('q') q?: string
```

| 需求 | 前端 | FastAPI |
| --- | --- | --- |
| 可选 q | `q?: string` | `q: str \| None = None` |
| limit 默认 10 | 自己 `?? 10` | `limit: int = 10` 或 `Query(default=10)` |
| 边界 | 运行时自己判 | `Query(ge=1, le=100)` |

---

### 3.3 请求体：先用 `dict`，马上换成模型

#### 为什么先写 `dict`？

看清「POST body → Python 对象」这一跳；下一节立刻换成 Pydantic，对比「无校验 vs 有校验」。

#### 怎么写

```python
from fastapi import FastAPI

app = FastAPI()


@app.post("/echo")
async def echo(payload: dict) -> dict:
    return {"you_sent": payload}
```

`payload: dict` 表示「JSON 对象当 body」。能跑，但**几乎不校验字段**。

#### 跑一下

```bash
curl -X POST http://127.0.0.1:8000/echo \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"hi\",\"extra\":true}"
```

```json
{"you_sent":{"message":"hi","extra":true}}
```

#### 易错点

- 忘了 `Content-Type: application/json` → 可能解析失败
- 生产 API 长期停留在 `dict` → 没有 schema、没有自动文档字段说明、没有边界校验
- GET 请求塞 body——能玩，但不推荐；过滤条件用 Query

#### 前端 / TS 对照

```typescript
await fetch("/echo", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "hi", extra: true }),
})
```

下一节的 `ChatRequest` ≈ 前端的 `type ChatRequest = { ... }`，但服务端还会**强制执行**。

---

### 3.4 参数来源速查（钉死心智模型）

```text
/items/{item_id}?q=hello          + JSON body
        ▲                ▲              ▲
     Path 参数        Query 参数     Body（模型 / dict）
```

| 你在函数里写 | FastAPI 通常从哪取 |
| --- | --- |
| `item_id` 且路径有 `{item_id}` | Path |
| `q: str \| None = None`（简单类型） | Query |
| `body: ChatRequest`（BaseModel） | JSON Body |
| `tasks: BackgroundTasks` | 框架注入 |
| `settings: Settings = Depends(...)` | 依赖注入 |

拿不准时：打开 `/docs`，看参数出现在 path / query / body 哪一栏。

---

## 4. 必掌握：Pydantic 请求 / 响应模型

Pydantic 是本章的「类型发动机」。v2 为主流；看到 `model_validate` / `model_dump` 就是 v2 API（v1 的 `parse_obj` / `dict()` 已过时，新代码不要写）。

### 4.1 定义模型与挂到路由

#### 为什么需要模型？

`dict` echo 无法保证：

- `message` 必填且非空
- `temperature` 在 0～2
- 响应只暴露 `reply` / `model`，不泄漏内部字段

模型 = **运行时校验 + OpenAPI schema + 编辑器补全** 的单一真相源。

#### 怎么写

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    temperature: float = Field(default=0.2, ge=0, le=2)


class ChatResponse(BaseModel):
    reply: str
    model: str


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    # 假装 LLM：真实项目里 await llm.complete(...)
    return ChatResponse(reply=f"ECHO: {body.message}", model="echo")
```

读注解的方式：

| 写法 | 含义 |
| --- | --- |
| `body: ChatRequest` | 请求体按该模型解析与校验 |
| `response_model=ChatResponse` | 输出按该模型序列化；多余字段会被裁掉 |
| `-> ChatResponse` | 给类型检查器与读者看；与 `response_model` 一起用更稳 |
| `Field(...)` | 默认值、边界、文档说明 |

#### 跑一下

合法请求：

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"你好\",\"temperature\":0.2}"
```

```json
{"reply":"ECHO: 你好","model":"echo"}
```

省略 `temperature`（走默认 0.2）：

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"你好\"}"
```

非法：空 message、超界 temperature → 422（下一节细拆）。

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 只用 `-> ChatResponse` 不写 `response_model` | 多数情况仍能序列化，但裁剪/文档行为以 `response_model` 更明确 |
| 返回裸 `dict` 却期望严格 schema | 请构造 `ChatResponse(...)` 或确保 dict 能通过模型 |
| 在模型里用可变默认值 `items: list = []` | 用 `Field(default_factory=list)` |
| 继续写 v1 API | 新代码用 `model_dump()`，不要 `dict()` |

#### 前端 / TS 对照

```typescript
// 前端类型（编译期）——运行时不会自动拦坏数据
type ChatRequest = {
  message: string
  temperature?: number // 默认 0.2 需自己处理
}

type ChatResponse = {
  reply: string
  model: string
}

async function chat(body: ChatRequest): Promise<ChatResponse> {
  const res = await fetch("/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<ChatResponse>
}
```

| | TypeScript `type` | Pydantic `BaseModel` |
| --- | --- | --- |
| 何时检查 | 主要是编译期 | **运行时**（每个请求） |
| 默认值 / 边界 | 手写逻辑或 zod 等 | `Field(default=..., ge=...)` |
| 文档 | 需另维护 | 自动进 OpenAPI |

有前端 zod / yup 经验的话：Pydantic ≈ **服务端的 zod**。

---

### 4.2 响应裁剪：`response_model` 的价值

#### 为什么要裁剪？

内部对象常带 `api_key`、`debug_trace`、ORM 懒加载字段。若直接 `return obj`，可能多吐字段。

#### 怎么写 / 跑一下

```python
class UserOut(BaseModel):
    id: int
    name: str


class UserInDb(BaseModel):
    id: int
    name: str
    hashed_password: str


@app.get("/users/me", response_model=UserOut)
def read_me() -> UserInDb:
    # 即使返回了带密码哈希的对象，响应也会被裁成 UserOut
    return UserInDb(id=1, name="ada", hashed_password="secret")
```

客户端只会看到：

```json
{"id":1,"name":"ada"}
```

#### 易错点

- 以为「不写进模型就一定不会泄漏」——若你返回的是未受 `response_model` 约束的结构，仍可能原样序列化
- 调试时在 `/docs` 里看到的 schema，以 `response_model` 为准

---

### 4.3 Pydantic v2 常用 API（建议掌握）

#### 为什么单独列？

业务层、测试、与非 FastAPI 代码交互时，你会直接操作模型，不只靠框架注入。

#### 怎么写

```python
from pydantic import BaseModel, Field, ValidationError


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    temperature: float = Field(default=0.2, ge=0, le=2)


# dict → 模型（校验）
req = ChatRequest.model_validate({"message": "hi", "temperature": 0.5})

# 模型 → dict（默认排除未设置的细节，按需调整）
data = req.model_dump()
# {'message': 'hi', 'temperature': 0.5}

# 模型 → JSON 字符串
raw = req.model_dump_json()

# 从 JSON 字符串来
req2 = ChatRequest.model_validate_json('{"message":"hi"}')
```

| v2 | 旧 v1（勿新写） |
| --- | --- |
| `model_validate` | `parse_obj` |
| `model_validate_json` | `parse_raw` |
| `model_dump` | `dict()` |
| `model_dump_json` | `json()` |

#### 易错点

- `ChatRequest(**data)` 与 `model_validate(data)` 在简单场景都可用；嵌套/宽松配置时优先熟悉 `model_validate`
- `model_dump()` 默认是 Python 对象（如 `datetime`）；要进纯 JSON 再考虑 `mode="json"`

---

### 4.4 嵌套模型与列表（Agent 里超常见）

#### 为什么需要？

消息历史、工具列表、多 step 轨迹，全是「模型里套模型 / 列表」。

#### 怎么写

```python
class Message(BaseModel):
    role: str
    content: str


class ChatRequestNested(BaseModel):
    messages: list[Message] = Field(min_length=1)
    temperature: float = Field(default=0.2, ge=0, le=2)
```

```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.2
}
```

#### 前端 / TS 对照

```typescript
type Message = { role: string; content: string }
type ChatRequestNested = {
  messages: Message[]
  temperature?: number
}
```

Python 3.11+ 直接写 `list[Message]`，不必再 `List[Message]`（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）。

---

## 5. 必掌握：校验错误处理

非法入参不是「程序崩了」，而是**可预期的 422**。前后端都要会读 `detail`。

### 5.1 默认 422 长什么样

#### 为什么先读懂默认格式？

`/docs` 里乱填、前端漏字段时，你第一眼看到的就是它。会读才能会改。

#### 跑一下

对 §4 的 `/v1/chat` 发送：

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"\",\"temperature\":9}"
```

响应状态码 **422**，body 类似：

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "message"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    },
    {
      "type": "less_than_equal",
      "loc": ["body", "temperature"],
      "msg": "Input should be less than or equal to 2",
      "input": 9,
      "ctx": {"le": 2}
    }
  ]
}
```

怎么读：

| 字段 | 含义 |
| --- | --- |
| `loc` | 错误位置：`body.message` / `query.limit` / `path.item_id` |
| `msg` | 人话说明 |
| `type` | 错误类型机读名 |
| `input` | 原始输入（调试有用；对外是否暴露看安全策略） |

#### 前端 / TS 对照

```typescript
type Violation = {
  loc: (string | number)[]
  msg: string
  type: string
}

type FastAPI422 = { detail: Violation[] }

// 前端可把 loc 拼成 "body.message" 展示在表单旁
```

这和 Nest 的 `ValidationPipe`、zod 的 `error.issues` 同一类信息，只是字段名不同。

---

### 5.2 自定义校验异常格式

#### 为什么要自定义？

统一成前端已有的错误包络，例如 `{ ok: false, error, detail }`，避免每个页面去适配 FastAPI 默认形状。

#### 怎么写

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": "validation_failed",
            "detail": exc.errors(),
        },
    )
```

#### 跑一下

再用空 `message` 打一次 `/v1/chat`，应看到：

```json
{
  "ok": false,
  "error": "validation_failed",
  "detail": [ ... ]
}
```

`exc.errors()` 在 v2 里返回可序列化的错误列表；需要时也可配合 `exc.body` 看原始 body。

#### 易错点

- 只自定义了 `RequestValidationError`，业务上的 `HTTPException` 仍走默认——这是正常分工
- handler 里再抛未捕获异常 → 变成 500；保持 handler 简单
- 把校验错误改成 400：可以，但要和前端约定；社区默认是 **422 Unprocessable Entity**

---

### 5.3 业务错误：`HTTPException`

#### 为什么和 422 分开？

| 类型 | 典型状态码 | 含义 |
| --- | --- | --- |
| 校验失败 | 422 | 「形状 / 类型 / 边界」不对 |
| 业务拒绝 | 400 / 401 / 403 / 404 / 409… | 「形状对，但业务不允许」 |

例如：`session_id` 已是合法 int，但内存里没有这条会话 → **404**，不是 422。

#### 怎么写

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

SESSIONS: dict[int, str] = {1: "demo-session"}


@app.get("/sessions/{session_id}")
def get_session(session_id: int) -> dict[str, object]:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    return {"session_id": session_id, "title": SESSIONS[session_id]}
```

#### 跑一下

```bash
curl http://127.0.0.1:8000/sessions/1
# {"session_id":1,"title":"demo-session"}

curl http://127.0.0.1:8000/sessions/99
# {"detail":"session not found"}  状态码 404
```

#### 易错点

- 用 `return {"error": "..."}` 却仍 `200`——客户端难写；请 `raise HTTPException`
- `detail` 可以是 str 或 dict；团队内统一一种
- 401/403 的细拆留给下一章认证；这里先会用 404/400

#### 前端 / TS 对照

```typescript
const res = await fetch(`/sessions/${id}`)
if (res.status === 404) {
  // 提示「会话不存在」
}
if (res.status === 422) {
  // 表单校验：读 detail 数组
}
```

---

## 6. 必掌握：依赖注入（Depends）

Depends 解决的是：**把「取配置 / 开连接 / 认当前用户」从每个 endpoint 里抽出去**，又可在测试时替换。

### 6.1 注入配置：最小例子

#### 为什么需要 Depends？

没有依赖时：

```python
# 每个路由自己读环境变量、自己 new 客户端 → 重复、难测、难换 FakeLLM
```

有依赖时：

```text
请求进入
  → 解析参数 / body
  → 执行 Depends 链（settings、db、user…）
  → 调用 endpoint(业务参数 + 注入值)
```

这和 OOP 章的「依赖注入直觉」同构：endpoint 不自己 `new`，而声明「我需要 Settings」。

#### 怎么写

```python
from dataclasses import dataclass

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


@dataclass
class Settings:
    model: str = "echo"


def get_settings() -> Settings:
    return Settings()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    temperature: float = Field(default=0.2, ge=0, le=2)


class ChatResponse(BaseModel):
    reply: str
    model: str


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    return ChatResponse(reply=f"ECHO: {body.message}", model=settings.model)
```

读这一行：

```python
settings: Settings = Depends(get_settings)
```

| 部分 | 含义 |
| --- | --- |
| `get_settings` | 依赖可调用对象；FastAPI 会调用它 |
| `Depends(...)` | 标记「这不是 Query/Body，请注入」 |
| `settings: Settings` | 注入值的类型，便于阅读与检查 |

#### 跑一下

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"hi\"}"
```

```json
{"reply":"ECHO: hi","model":"echo"}
```

把 `Settings.model` 改成 `"gpt-echo"` 再请求，响应里的 `model` 应跟着变——说明注入生效。

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 写成 `settings: Settings = get_settings()` | 只在**导入时**调用一次；不是每请求注入，测试也难覆盖 |
| 在 `get_settings` 里读密钥却打印到日志 | 配置可以注入，密钥不要进响应/日志 |
| 把重逻辑都塞进 Depends | 依赖宜「取资源」；业务仍放 service / endpoint |

#### 前端 / TS 对照

| 概念 | NestJS | FastAPI |
| --- | --- | --- |
| 注入 | 构造函数 `@Injectable()` | `Depends(get_xxx)` |
| 请求作用域服务 | 请求级 provider | 依赖函数每请求调用（默认可缓存，见下） |
| 测试替换 | testing module override | `app.dependency_overrides[get_settings] = fake` |

```typescript
// Nest 直觉：constructor(private readonly settings: Settings) {}
```

```python
# FastAPI：在参数列表里声明
async def chat(..., settings: Settings = Depends(get_settings)): ...
```

---

### 6.2 测试时覆盖依赖（强烈建议会）

#### 为什么重要？

CI 里不应真的读生产环境变量、打真实 LLM。覆盖 `get_settings` / `get_llm` 才能稳定绿。

#### 怎么写

```python
from fastapi.testclient import TestClient

def get_settings_override() -> Settings:
    return Settings(model="test-model")


app.dependency_overrides[get_settings] = get_settings_override

client = TestClient(app)
res = client.post("/v1/chat", json={"message": "hi"})
assert res.status_code == 200
assert res.json()["model"] == "test-model"

app.dependency_overrides.clear()
```

#### 易错点

- 测完不 `clear()` → 污染其它测试
- override 的 key 必须是**同一个函数对象** `get_settings`，不要复制粘贴一个同名函数

---

### 6.3 Depends 还能干什么（地图）

用途清单（下一章会落到鉴权）：

- 注入配置、DB session、Redis 客户端
- 鉴权前置：`current_user = Depends(get_current_user)`；失败直接 `HTTPException 401`
- 多层依赖：`get_db` ← `get_current_user` ← endpoint
- 与 Agent：`Depends(get_llm_client)`，测试时换成 FakeLLM（契约见 [`CONVENTIONS.md`](../CONVENTIONS.md)）

同一请求内，FastAPI 会对同一依赖函数做缓存：多个 endpoint 参数都 `Depends(get_settings)` 时，通常只跑一次——适合「取一次 DB session」。

---

## 7. 建议掌握：OpenAPI 与 BackgroundTasks

### 7.1 OpenAPI：`/docs` 不是装饰，是契约

#### 为什么要会看 OpenAPI？

1. **本地调试**：没写前端也能点试请求
2. **前后端协作**：schema 就是合同；可导出给代码生成器
3. **Agent 工具**：把 API 自描述给工具选择器 / 代码 Agent（字段、类型、必填一目了然）

类型注解、`Field(description=...)`、`response_model`、状态码——最终都汇进 `/openapi.json`。

#### 怎么写（让文档更好用）

```python
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="agent-api",
    version="0.1.0",
    description="Minimal Agent-facing HTTP API",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="用户输入")
    temperature: float = Field(default=0.2, ge=0, le=2, description="采样温度")


@app.get("/items/{item_id}", summary="获取条目", tags=["items"])
def get_item(
    item_id: int,
    q: str | None = Query(default=None, description="可选搜索词"),
) -> dict[str, object]:
    return {"item_id": item_id, "q": q}
```

| 装饰 | 作用 |
| --- | --- |
| `summary` / `description` | 接口短标题 / 长说明 |
| `tags=["items"]` | `/docs` 里分组 |
| `Field(description=...)` | 模型字段说明 |
| `response_model` | 响应 schema |

#### 跑一下

1. 启动服务，打开 `http://127.0.0.1:8000/docs`
2. 展开 `POST /v1/chat` → Try it out → Execute
3. 再打开 `/openapi.json`，搜索 `ChatRequest`，确认字段与约束在

#### 易错点

- 参数写成裸 `dict` → 文档里只显示「任意对象」，协作价值大减
- 改了模型却不刷新浏览器 → 旧 schema 缓存错觉；硬刷新即可
- 把 `/docs` 暴露到公网生产且无鉴权 → 信息泄漏面；生产常关闭或加保护

#### 前端 / TS 对照

| 前端做法 | FastAPI 侧 |
| --- | --- |
| 手写 `types.ts` + 同步落后 | 以 OpenAPI 为源生成客户端类型 |
| Postman 集合 | `/docs` 即互动集合 |
| `swagger-typescript-api` 等 | 吃 `/openapi.json` |

---

### 7.2 BackgroundTasks：轻量收尾，不是任务队列

#### 为什么需要它？

有时你想：**先把响应返回给客户端**，再做一点「最好完成、失败也不该拖垮请求」的事——写访问日志、轻量指标、清理临时文件。

#### 怎么写

```python
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

app = FastAPI()
LOG = Path("requests.log")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str
    model: str


def write_log(message: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    tasks: BackgroundTasks,
) -> ChatResponse:
    tasks.add_task(write_log, body.message)
    return ChatResponse(reply=f"ECHO: {body.message}", model="echo")
```

流程：

```text
endpoint 返回响应
    → 框架把响应发给客户端
    → 再依次执行 tasks 里的函数
```

#### 跑一下

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"log-me\"}"

# 然后查看 requests.log 是否多了一行 log-me
```

#### 关键：刻意简化（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）

> **FastAPI `BackgroundTasks`：轻量收尾，长任务请上队列。**

| 适合 BackgroundTasks | 应上队列（模块 07 消息队列直觉） |
| --- | --- |
| 写一行日志、打点 | 跑 Agent 多步、长 LLM 链 |
| 删除临时文件 | 需要重试、持久化、可观测的任务 |
| 请求内可接受「进程挂了就丢」 | 要 at-least-once / 死信 / 并发工人 |

`BackgroundTasks` 跑在**同一个进程**里：进程被杀、部署重启，未跑完的任务就没了；也不负责跨机器调度。长任务请用 Redis/RQ/Celery/云队列等，而不是把 `BackgroundTasks` 当万能后台。

#### 易错点

- 在 BackgroundTask 里跑 5 分钟 Agent → 占满 worker、难监控、难重试
- 以为 `add_task` 等于「另一台机器在跑」→ 不是
- 在 task 里用已关闭的 request/DB session → 只传普通数据（str、id），不要传请求对象
- `async def` 任务可以 `add_task`；同样避免内部同步阻塞

#### 前端 / TS 对照

前端的「先 `res.json()`，再 `beacon` 打点」≈ 轻量收尾直觉。  
前端**没有**服务端这种进程内 BackgroundTasks；若要可靠异步，两边最终都走向**队列 / worker**。

---

## 8. 了解即可：自定义依赖进阶

CRUD 与 Agent Run 做熟后再深挖；这里只建地图。

### 8.1 可调用类依赖

```python
class NeedHeader:
    def __init__(self, header_name: str = "x-request-id") -> None:
        self.header_name = header_name

    def __call__(self, request: Request) -> str | None:
        return request.headers.get(self.header_name)


require_request_id = NeedHeader()


@app.get("/ping")
def ping(rid: str | None = Depends(require_request_id)) -> dict[str, str | None]:
    return {"request_id": rid}
```

类可以带着配置（`header_name`），实例又可 `Depends(instance)`——适合可复用的鉴权/限流前置。

### 8.2 带 `yield` 的依赖（setup / teardown）

```python
def get_db():
    db = {"conn": "fake"}  # 真实项目：创建 session
    try:
        yield db
    finally:
        # 关闭 session / 归还连接池
        db.clear()


@app.get("/db-check")
def db_check(db: dict = Depends(get_db)) -> dict[str, str]:
    return {"conn": str(db.get("conn"))}
```

直觉对齐上下文管理器：进入时准备，离开时清理（含异常路径）。DB 章节会大量用这种模式。

### 8.3 多级依赖链

```text
get_settings → get_llm_client → get_agent → endpoint
```

每层只依赖上一层，endpoint 保持瘦。测试时可在任意层 override。

---

## 9. 综合小例子：Agent Run API 骨架

把路由、模型、校验、业务错误、Depends 收成一条「可继续长肉」的 Agent HTTP 入口。真实项目里 `await agent.arun(...)` 会替换 Echo。

### 9.1 为什么先做骨架？

服务化 Agent 的第一站通常不是完美编排，而是：

1. 稳定的 URL 与版本前缀（`/v1/...`）
2. 入参边界（`max_steps` 不能 9999）
3. 统一错误（坏 query → 400；非法 JSON → 422）
4. 可注入的模型名 / 客户端（便于 FakeLLM）

下一章会在这根骨架上挂 API Key；项目线会挂真实工具环。

### 9.2 怎么写

```python
from dataclasses import dataclass

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="mini-agent", version="0.1.0")


@dataclass
class Settings:
    model: str = "echo"


def get_settings() -> Settings:
    return Settings()


class AgentRunRequest(BaseModel):
    query: str = Field(min_length=1, description="用户问题")
    max_steps: int = Field(default=5, ge=1, le=20, description="最大步数")


class AgentRunResponse(BaseModel):
    answer: str
    steps: int
    model: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/agent/run", response_model=AgentRunResponse)
async def run_agent(
    body: AgentRunRequest,
    settings: Settings = Depends(get_settings),
) -> AgentRunResponse:
    if body.query.strip().lower() == "boom":
        raise HTTPException(status_code=400, detail="bad query")

    # 真实项目：
    # result = await agent.arun(body.query, max_steps=body.max_steps)
    # return AgentRunResponse(answer=result.answer, steps=result.steps, model=settings.model)

    return AgentRunResponse(
        answer=f"done:{body.query}",
        steps=min(1, body.max_steps),
        model=settings.model,
    )
```

### 9.3 跑一下

```bash
uvicorn app.main:app --reload --port 8000

# 健康检查
curl http://127.0.0.1:8000/health

# 成功
curl -X POST http://127.0.0.1:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"总结这段文本\",\"max_steps\":3}"

# 业务错误 400
curl -X POST http://127.0.0.1:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"boom\"}"

# 校验错误 422（max_steps 超界）
curl -X POST http://127.0.0.1:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"hi\",\"max_steps\":999}"
```

### 9.4 易错点

- 把「长时间 `arun`」塞进默认同步思维：入口可以是 `async`，但**超长任务**应考虑 202 + 队列，而不是让 HTTP 一直挂到跑完（与 BackgroundTasks 的边界一致）
- `max_steps` 只做 Field 校验还不够时，再在业务里限制工具调用次数
- 版本前缀 `/v1` 一旦对外发布，勿随意改语义；新行为加 `/v2` 或新字段要兼容

### 9.5 前端 / TS 对照

```typescript
type AgentRunRequest = {
  query: string
  max_steps?: number // 1～20，默认 5
}

type AgentRunResponse = {
  answer: string
  steps: number
  model: string
}

async function runAgent(body: AgentRunRequest): Promise<AgentRunResponse> {
  const res = await fetch("/v1/agent/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (res.status === 422) throw new Error("validation failed")
  if (res.status === 400) throw new Error("bad query")
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<AgentRunResponse>
}
```

---

## 10. 常见坑（建议收藏）

1. **用可变对象当全局状态还不加锁**  
   如模块级 `SESSIONS: dict = {}` 在多 worker / 多协程下会踩竞态；单机玩具可以，生产要 DB/Redis，或至少想清楚进程模型。

2. **在 `async` 路由里调用同步 HTTP 客户端**  
   `requests.get` / `time.sleep` 会堵事件循环；用 `httpx.AsyncClient` 或把同步调用放到 `def` / `to_thread`。

3. **返回任意 `dict` 却期望严格 schema**  
   请用 `response_model` + 构造模型实例；不要靠「我用心里保证字段对」。

4. **把密钥写进代码**  
   应走环境变量，经 `get_settings` / Depends 注入；下一章鉴权同理。

5. **把 `BackgroundTasks` 当长任务队列**  
   违反课程约定：轻量收尾可以，Agent 长跑请上队列（[`CONVENTIONS.md`](../CONVENTIONS.md)）。

6. **路径参数类型对了就以为业务对了**  
   `session_id: int` 只过 422；不存在仍要自己 `HTTPException(404)`。

7. **Pydantic v1 / v2 API 混用**  
   新代码统一 `model_validate` / `model_dump`；读旧博文时注意版本。

8. **依赖写成 `get_settings()` 直接调用**  
   失去每请求注入与 `dependency_overrides`；必须 `Depends(get_settings)`。

---

## 11. 练习指引

按文档顺序动手，不要只看：

[`exercises/06-web-backend/02-fastapi-pydantic.md`](../../exercises/06-web-backend/02-fastapi-pydantic.md)

建议路径：

1. B1 Health → 确认 `uvicorn` 与 `/docs`
2. B2 Chat 模型 → 故意打出 422
3. B3 路径参数 + 404
4. B4 Depends 配置
5. （建议）A1 Agent Run / A2 自定义校验格式
6. （可选）C1 BackgroundTasks 写日志；C2 `TestClient` 烟雾测试

playground 目录：`playground/06-web-backend/02-fastapi-pydantic/`。

---

## 12. 小结与下一站

### 你现在应该掌握的心智模型

```text
HTTP 请求
  → 路由匹配（方法 + 路径）
  → 路径/查询/Body 解析
  → Pydantic 校验（失败则 422）
  → Depends 注入（配置 / 用户 / 客户端）
  → endpoint 业务（失败则 HTTPException）
  → response_model 序列化
  → （可选）BackgroundTasks 轻量收尾
```

一句话：

> **用类型声明契约，用 Depends 组装边界，用 HTTPException / 422 区分业务错误与校验错误。**

### 自检清单

- [ ] 能写 `GET`/`POST` + 路径参数 + 查询参数
- [ ] 能用 Pydantic v2 模型做请求/响应，并说明 `response_model` 的裁剪作用
- [ ] 能看懂 422 的 `loc` / `msg`，会自定义 `RequestValidationError` handler
- [ ] 会用 `Depends` 注入配置，知道测试里如何 `dependency_overrides`
- [ ] 会打开 `/docs`，能说清 BackgroundTasks 与「上队列」的边界
- [ ] 能独立写出 `/v1/agent/run` 骨架

### 下一章

[`03-auth.md`](./03-auth.md) —— 认证与授权：API Key / JWT / RBAC 地图；把鉴权做成 Depends，挂到本章的 Agent Run 上。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Web 框架原理](./01-web-framework-principles.md)
- 下一章：[认证与授权](./03-auth.md)
- 课程约定：[CONVENTIONS.md](../CONVENTIONS.md)
