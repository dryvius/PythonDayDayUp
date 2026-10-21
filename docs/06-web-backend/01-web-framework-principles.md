# Web 框架原理

> 所属模块：`06-web-backend` · Web 后端  
> 状态：`已完成正文`  
> 建议学时：2～4 小时（有 Express/Koa 中间件经验可更快；请求生命周期与「async 里别阻塞」建议动手画一遍、踩一遍）  
> 对应练习：[`exercises/06-web-backend/01-web-framework-principles.md`](../../exercises/06-web-backend/01-web-framework-principles.md)

## 本章定位

- **模块目标**：能独立搭建并理解后端 API 服务。
- **本章角色**：先搞清「请求进来后发生了什么」，再学 FastAPI 才不会只停留在抄装饰器。
- **前置**：HTTP（模块 04）、asyncio（模块 05）。本章不再重讲状态码与事件循环细节，只把它们接到「Web 框架如何调度一次请求」上。
- **你的优势**：若写过 Express/Koa 的 `app.use` / `(req, res, next)`，路由与中间件心智几乎可直接迁移；差别在 Python 侧还有 WSGI/ASGI、以及 `def` / `async def` 对并发模型的影响。
- **刻意不做**：FastAPI 装饰器细节、Pydantic 校验字段、Depends 鉴权写法——留给下一章；本章只建立地图与选型肌肉。

## 学习目标（学完应能做到）

1. 描述一次 HTTP 请求的服务端生命周期（从连上 ASGI server 到发回响应），并标出鉴权 / 校验 / LLM 慢调用可能插在哪。
2. 理解路由与中间件各自解决什么问题，能判断「该放中间件还是放 endpoint / service」。
3. 分清同步处理与异步处理在 Web 里的含义，能判断 endpoint 该用 `def` 还是 `async def`，并解释「async 里同步阻塞」为何更危险。
4. 建立 WSGI/ASGI、框架 vs ASGI 服务器、网关/反向代理的地图，能解释 FastAPI 为何通常配 uvicorn。
5. 完成课后练习，并把「Agent 服务化」接到同一张请求路径上。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 请求生命周期、路由/中间件、同步与异步处理 | 能画流程、能选型、能解释阻塞事故 |
| **建议掌握** | WSGI/ASGI | 能解释 FastAPI 为何是 ASGI、uvicorn 扮演什么角色 |
| **了解即可** | 网关与反向代理 | 扫盲，部署章再深挖 |

---

## 1. 为什么要学（和 Agent 服务化有什么关系）

#### 为什么需要 Web 框架原理？

Agent 常以 API 形式对外，也常被别的服务调用：

```text
前端 / 其它服务 / 定时任务
    --HTTP JSON-->  你的 FastAPI（Agent 服务）
                       → 调 LLM
                       → 跑 Tool
                       → 读写 memory / DB
                       → 返回 JSON（或流式）
```

不懂框架原理时，你会反复踩这些坑：

```text
超时了     → 不知道慢在中间件、校验，还是 LLM
鉴权漏了   → 404 路径绕过了「以为会跑」的检查（或顺序反了）
全站卡死   → 有人在 async 路由里 requests.get / time.sleep
部署懵了   → 分不清 FastAPI、uvicorn、Nginx 谁干什么
测不动    → 业务全写在 endpoint，依赖框架才能跑
```

#### 怎么理解本章要解决的问题

模块 04 告诉你 HTTP 长什么样；模块 05 告诉你事件循环怎么让出。  
本章把两者接到「一次请求在服务端怎么走」：

1. **生命周期**：请求从进门到出门经过哪些层？
2. **路由 vs 中间件**：谁负责「匹配路径」，谁负责「统一横切」？
3. **sync vs async**：框架怎么调度工人线程 / 事件循环？
4. **部署地图**：框架、ASGI 服务器、网关各自边界在哪？

可以先记一句：

> Web 框架原理的核心不是背装饰器 API，而是**能画出请求路径，并知道在每一层该放什么、不该放什么**。

#### 跑一下（先建立「服务」心智，不必装 FastAPI）

下面用标准库起一个最小 HTTP 服务，感受「有人连进来 → 你的代码被调用 → 写回响应」——这就是框架要替你标准化的事：

```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps({"status": "ok"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # 安静一点
        return


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
```

另开终端：

```bash
curl http://127.0.0.1:8765/health
# {"status": "ok"}
```

真实项目不会手写 `BaseHTTPRequestHandler`，但你会看到框架做的事本质相同：**收字节 → 解析 HTTP → 找处理函数 → 序列化 → 写回**。后面各节只是把「找处理函数」「横切逻辑」「并发模型」拆开讲透。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为「会写 `@app.get` 就算懂框架」 | 出超时/鉴权/阻塞时不会定位层 |
| 把 Agent 当成「脚本跑完就退出」 | 服务化后进程常驻，一次坏请求可能拖垮整站 |
| 跳过原理直接抄 FastAPI 教程 | 中间件顺序、sync/async 选型会凭感觉猜 |

#### 前端 Express 对照（先建立地图）

| 你在 Express 里熟悉的 | 本章 Python / FastAPI 侧 |
| --- | --- |
| `app.get/post` 路由 | 路由表：方法 + 路径 → handler |
| `app.use(mw)` 中间件链 | Starlette/FastAPI middleware（洋葱模型） |
| `next()` | `await call_next(request)` |
| `express()` 应用对象 | `FastAPI()` / Starlette app |
| `node server` / `app.listen` | **ASGI 服务器**（uvicorn）跑 app |
| Nginx 反代到 Node | Nginx/Caddy 反代到 uvicorn workers |

---

## 2. 必掌握：请求生命周期

这一节会刻意写细——后面路由、中间件、sync/async、网关，都钉在这张路径上。

### 2.1 端到端：一次请求的 9 步

#### 为什么需要把步骤钉死？

排障时要回答：「卡在哪一层？鉴权跑了没有？404 有没有经过日志？」  
没有共享的步骤编号，团队沟通会变成「我觉得在框架里」。

#### 怎么理解（极简流程）

以 FastAPI + uvicorn 为默认语境（模块后两章同此）：

```text
1. 客户端发 HTTP 请求
2. 服务器接收连接（常由 uvicorn 等 ASGI server）
3. 应用级中间件入站（从前到后；后 add 的更靠外）
4. 框架匹配路由（路径 + 方法）——故 404 也会经过中间件
5. 依赖注入 / 解析参数 / 校验 body（Depends / Pydantic）
6. 执行 endpoint 函数
7. 序列化响应（JSON 等）
8. 中间件出站（从后到前）
9. 发回 HTTP 响应
```

心智图（Agent 服务常见路径）：

```text
Browser / 其它服务
    │  HTTP
    ▼
[网关/反代]  ← 了解即可，见第 6 节
    │
    ▼
uvicorn (ASGI server)  ← 管连接、协议、工人进程
    │
    ▼
中间件洋葱（入）──► Router 匹配 ──► Depends / Pydantic
                              │
                              ▼
                         endpoint（调 LLM / Tool）
                              │
                              ▼
中间件洋葱（出）◄──────── 序列化响应
    │
    ▼
HTTP 响应回客户端
```

#### 跑一下（示意：用日志「看见」顺序）

下一章才会完整跑 FastAPI；这里先用伪代码把顺序钉进肌肉记忆：

```python
# 示意，不是完整可运行 FastAPI 项目
async def logging_middleware(request, call_next):
    print("→ in  logging")
    response = await call_next(request)
    print("← out logging", response.status_code)
    return response


async def auth_middleware(request, call_next):
    print("→ in  auth")
    response = await call_next(request)
    print("← out auth")
    return response


async def run_agent(request):
    print("   * endpoint: call LLM")
    return {"ok": True}


# 若 auth 包在 logging 里面，一次成功请求打印顺序类似：
# → in  logging
# → in  auth
#    * endpoint: call LLM
# ← out auth
# ← out logging 200
```

这就是「洋葱」：先进的后出。Express 里多层 `app.use` 也是同一形状。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为 404「不进中间件」 | Starlette/FastAPI 里应用中间件在 Router **外**，404 通常仍经过中间件 |
| 在「匹配路由之前」的中间件里读 path params | `call_next` 之前通常还拿不到 |
| 把 ASGI server 和框架当成同一个东西 | uvicorn 负责协议与进程；FastAPI 负责应用逻辑 |

#### 前端 Express 对照

```text
Express 近似：
  req → mw1 → mw2 → route handler → mw2 → mw1 → res

FastAPI/Starlette 近似：
  request → mw1 → mw2 → routing → deps/validation → endpoint
         → mw2 → mw1 → response
```

细节命名不同（`next` vs `call_next`），**入站正向、出站反向**一致。

---

### 2.2 中间件包在 Router 外（别记反）

#### 为什么这一点要单独强调？

很多人从「先找路由再跑中间件」的想象出发，会误判：

- 「这个路径 404，鉴权中间件不会跑」→ 往往**会跑**
- 「中间件里能拿到 `{agent_id}`」→ 匹配前**通常不能**

#### 怎么理解

Starlette/FastAPI 的模型是：

```text
中间件（外层）
  └── 中间件（内层）
        └── Router（匹配路径 + 方法）
              └── endpoint + Depends
```

因此：

1. **未匹配的路由**仍可能走过应用中间件（适合统一日志、CORS、请求 ID）。
2. **粗粒度鉴权**可以放中间件；**需要路径参数 / 细粒度权限**的，更常放 Depends（下一章）。
3. 调试时先问：问题出在「进 Router 之前」还是「endpoint 之内」？

#### 示意（404 仍打日志）

```text
GET /no-such-path

→ logging in
→ （Router：无匹配 → 404 Response）
← logging out 404
```

业务 endpoint 没跑，但「请求存在过」已被中间件看见——这对可观测性很重要。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把「只有匹配成功才进中间件」当真理 | 漏日志、漏请求 ID、CORS 行为不符合预期 |
| 用中间件做「必须先有 path param」的逻辑 | 应下沉到路由级依赖或 endpoint |

#### 前端 Express 对照

Express 里全局 `app.use` 同样会碰到「最终 404」的请求；  
`app.get('/x', ...)` 匹配失败不等于全局中间件没跑。心智同构。

---

### 2.3 四个你要关心的插入点

#### 为什么需要「插入点」清单？

Agent 服务化时，同一条生命周期上要挂很多横切能力。  
先记住四个问题，写代码与排障都够用：

| 问题 | 常见落点 | Agent 例子 |
| --- | --- | --- |
| **哪一步做鉴权** | 中间件（粗）或 Depends（细） | 校验 `X-API-Key` / Bearer |
| **哪一步做校验** | Pydantic / 参数解析（进 endpoint 前） | `message` 长度、temperature 范围 |
| **哪一步最慢** | 常在 endpoint 内的 I/O | LLM 调用、工具 HTTP |
| **异常在哪变成 4xx/5xx** | 框架异常处理器 + 你的边界转译 | 校验失败 422；上游 502/504 |

#### 怎么理解（鉴权放哪？）

```text
适合中间件的鉴权：
  - 「几乎所有路径都要登录」
  - 只看 Header / Cookie，不依赖路径参数

适合 Depends / 路由级的鉴权：
  - 只要部分路由
  - 需要 path/query、或查 DB 判权限
  - 想在 OpenAPI 里体现安全方案（下一章）

不要：
  - 在中间件里写完整 Agent 编排
  - 在鉴权失败后还继续 call_next「碰运气」
```

#### 跑一下（书面标注，对接练习 B1）

把下面句子补全（答案见本节后文自检思路，先自己写）：

```text
客户端 POST /v1/agent/run
→ （？）加 request_id
→ （？）校验 API Key
→ Router 匹配到 run_agent
→ （？）Pydantic 校验 body
→ endpoint 内 await llm.complete(...)   ← 通常最慢
→ 若 LLM 超时：（？）变成哪类 HTTP 状态？
→ 中间件出站打耗时日志
→ 响应返回
```

参考填法：`请求 ID 中间件` → `鉴权中间件或 Depends` → `框架校验` → `504/502/你定义的错误体`（具体状态码策略在工程与下一章细化）。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 鉴权只写在「有业务的 endpoint」里 | 新路由忘贴，形成裸奔接口 |
| 校验靠手写 `if` 散落各处 | 错误形状不统一，OpenAPI 也对不上 |
| 把 LLM 超时当成「框架挂了」 | 其实卡在步骤 6；要看超时与上游，而不是先重装 uvicorn |

#### 前端对照

| 前端/Express | Python Web |
| --- | --- |
| 全局鉴权 middleware | 应用中间件或依赖 |
| `zod` / 手写校验 body | Pydantic（下一章） |
| 路由里 `await openai...` | endpoint 内 await LLM |
| `error-handling middleware` | 异常处理器 / HTTPException |

---

### 2.4 Agent 服务化：把「脚本」变成「常驻 API」

#### 为什么要单独说服务化？

本地 `python agent.py` 跑通 ≠ 可被前端/其它服务稳定调用。  
服务化多出来的是：**多请求并发、横切策略、进程模型、部署边界**。

#### 怎么理解

```text
脚本模式：
  一次输入 → 跑完 Agent → 进程结束

服务模式：
  进程常驻
  请求 A、B、C 交错到达
  共享：配置、连接池、限流器、假/真 LLM 客户端
  每个请求：自己的上下文（request_id、用户、超时预算）
```

本章原理直接服务这些决策：

1. 生命周期 → 请求 ID、耗时、鉴权挂哪  
2. 中间件 → CORS、日志、粗鉴权  
3. sync/async → LLM I/O 是否卡住整站  
4. ASGI + 网关 → 怎么部署、TLS 谁终结  

#### 示意（最小 Agent API 形状，细节下章写）

```text
GET  /health              → 探活（给网关/编排用）
POST /v1/chat             → 单轮对话
POST /v1/agent/run        → 跑工具环 / 多步 Agent
POST /v1/agent/run/stream → （了解）SSE/流式，后文再遇
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用模块级可变全局当「会话状态」 | 请求间串味、竞态 |
| health 里也去调 LLM | 探活变慢、被误杀下线 |
| 不设超时预算 | 一个慢 LLM 拖住工人/循环 |

#### 前端对照

浏览器调你的服务 ≈ 调任何 JSON API：`fetch` / `axios` + 超时 + 鉴权头。  
差别在服务端你要保证**并发下仍然正确**——这正是生命周期与 async 纪律的用武之地。

---

## 3. 必掌握：路由与中间件

### 3.1 路由：把「方法 + 路径」映射到处理函数

#### 为什么需要路由？

没有路由表，你就得在一个巨型 `if path == ...` 里分流（回想第 1 节的 `BaseHTTPRequestHandler`）。  
路由的价值：**声明式注册 + 参数抽取 + 与文档/校验集成**。

#### 怎么理解

```text
GET  /health        → health()
POST /v1/chat       → chat()
POST /v1/agent/run  → run_agent()
```

路由关心的三件事：

1. **方法**：`GET` / `POST` / …（错方法常是 405）
2. **路径**：静态段 + 路径参数（`/agents/{agent_id}`）
3. **处理函数**：sync 或 async endpoint

路径参数、查询参数、请求体的 FastAPI 写法在下一章细讲；本章先会「设计端点」与「和中间件分工」。

#### 跑一下（设计练习，对接 B2）

为迷你 Agent 服务草拟 4 个端点（先写文字，不必写代码）：

```text
方法  路径                 职责（一句话）
GET   /health              ...
POST  /v1/agent/run        ...
？    ？                   ...
？    ？                   ...
```

设计时问自己：

- 读操作是否用 GET？有副作用是否用 POST？
- 版本前缀 `/v1` 要不要从第一天就留？
- health 是否保持依赖最少？

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用 GET 触发「跑 Agent / 扣费」 | 缓存、重试、爬虫可能误触发 |
| 路径风格混乱（`/runAgent` 与 `/v1/agent/run` 混用） | 客户端与网关规则难统一 |
| 一个 endpoint 塞完所有产品功能 | 无法单独限流、鉴权、观测 |

#### 前端 Express 对照

```javascript
// Express
app.get("/health", (req, res) => res.json({ status: "ok" }))
app.post("/v1/agent/run", async (req, res) => { /* ... */ })
```

```python
# FastAPI（预告形状，下章展开）
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/agent/run")
async def run_agent(...):
    ...
```

---

### 3.2 中间件：环绕请求的统一逻辑

#### 为什么需要中间件？

日志、CORS、请求 ID、粗鉴权——若每个 endpoint 复制一份：

- 必然漏贴  
- 顺序无法保证  
- 测试与替换困难  

中间件把这些变成**默认外壳**。

#### 怎么理解

```text
请求 → 日志中间件 → 鉴权中间件 → 路由处理 → … → 响应
```

适合放中间件：

- 请求日志 / 耗时  
- CORS  
- 统一加请求 ID  
- 粗粒度鉴权（全站或大范围）  
- 统一安全头、简单限流（也常放网关，见第 6 节）  

不适合塞进中间件：

- 具体业务编排（选哪个 Tool、怎么拼 prompt）  
- 强依赖路径参数的领域规则  
- 大段 LLM 调用本身  

原则：

> **中间件管「每个请求都可能需要的外壳」；endpoint / service 管「这个接口独特的业务」。**

#### 怎么写（示意：纯 ASGI 风格的 call_next）

```python
# 示意结构（Starlette/FastAPI 中间件同构）
async def request_id_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID") or "generated-id"
    # 把 id 挂到 request.state，供日志与响应头使用
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

要点：

1. **入站**在 `call_next` 前  
2. **出站**在 `call_next` 后  
3. 不调用 `call_next` = 短路（可直接返回 401）

#### 跑一下（短路鉴权的形状）

```python
async def api_key_middleware(request, call_next):
    if request.url.path == "/health":
        return await call_next(request)  # 探活放行
    if request.headers.get("X-API-Key") != "secret":
        # 不 call_next：后面路由与 LLM 都不会跑
        from starlette.responses import JSONResponse
        return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return await call_next(request)
```

（完整挂载方式见下一章；此处只记「短路」语义。）

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 中间件里堆业务 | 难测、难复用，Router 变成空壳 |
| 鉴权中间件忘记放行 `/health` | 编排/K8s 探活失败，滚动发布被杀 |
| 出站逻辑写在 `call_next` 前 | 拿不到真实 status_code / 耗时不准 |

#### 前端 Express 对照

```javascript
// Express
app.use((req, res, next) => {
  const start = Date.now()
  res.on("finish", () => console.log(req.method, req.url, Date.now() - start))
  next()
})

app.use((req, res, next) => {
  if (req.path === "/health") return next()
  if (req.headers["x-api-key"] !== "secret") {
    return res.status(401).json({ detail: "unauthorized" })
  }
  next()
})
```

`next()` ↔ `await call_next(request)`；不调用就短路——一一对应。

---

### 3.3 中间件 vs 依赖注入（Depends）——先分清职责

#### 为什么现在就要分清？

下一章会大量用 `Depends`。若现在不分，你会把「能用中间件做的」和「该用依赖做的」搅在一起。

#### 怎么理解

| | 中间件 | Depends（路由/参数依赖） |
| --- | --- | --- |
| 作用域 | 常全局或大范围 | 可精确到某个路由/路由器 |
| 典型输入 | 原始 Request | 已解析的参数、子依赖、配置 |
| 短路 | 不 `call_next` | 抛 `HTTPException` 等 |
| 文档 | 不一定进 OpenAPI 安全方案 | 更容易体现在 OpenAPI |
| 适合 | 日志、CORS、请求 ID、粗鉴权 | 取配置、细鉴权、可复用「前置条件」 |

Agent 服务常见拆法：

```text
中间件：request_id、访问日志、CORS
Depends：get_settings、verify_api_key、get_llm_client
endpoint：只写编排（调用 service）
service：纯业务，可单测
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 全部用中间件「一刀切」 | 公开 webhook / 文档路由也被误伤 |
| 全部用 Depends、没有统一日志外壳 | 每个路由重复、404 路径无统一观测 |

#### 前端对照

- Express 全局 `app.use` ≈ 中间件  
- 路由级 `router.use` / 单个 handler 前的小函数 ≈ Depends 的「可插拔前置」  
- NestJS 的 Guard / Interceptor 分工，也接近「粗壳 vs 细依赖」

---

### 3.4 洋葱模型与注册顺序

#### 为什么顺序会变成生产事故？

「先日志还是先鉴权」「CORS 预检有没有被鉴权挡掉」——全是顺序问题。  
Starlette/FastAPI 还有一条反直觉：**后 `add_middleware` 的更靠外**。

#### 怎么理解

```text
# 伪代码顺序
app.add_middleware(Auth)
app.add_middleware(Logging)   # 后添加 → 更靠外

实际洋葱：
Logging（外）
  └── Auth（内）
        └── Router / endpoint
```

一次成功请求：

```text
→ Logging in
  → Auth in
    → endpoint
  ← Auth out
← Logging out
```

记忆口诀（FastAPI 语境）：

> **后添加的中间件更靠外**；出站顺序与入站相反。

#### 跑一下（用打印验证「外/内」）

把第 2.1 节的两层打印挂到真实 app 后（下章环境），交换 `add_middleware` 顺序，观察谁先打印 `→ in`。  
一次交换胜过背十次文档。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 假设「先写的一定先执行」 | 与 FastAPI 添加顺序语义相反，鉴权/日志错位 |
| CORS 中间件靠内、鉴权靠外且拦 OPTIONS | 浏览器预检失败，前端「跨域了」其实是预检被 401 |
| 多个中间件都改同一响应头 | 后出站的覆盖先出站的，结果难猜 |

#### 前端 Express 对照

Express 通常是**先 `use` 的先入站**（与 FastAPI `add_middleware` 的「后添加更靠外」不要混记）。  
迁移时：**画一张洋葱图，用日志验证**，不要假设两种框架顺序相同。

---

## 4. 必掌握：同步与异步处理

这一节与模块 05 是同一套肌肉，只是场景换成「Web endpoint」。

### 4.1 两种 endpoint，两种调度

#### 为什么 Web 里要再讲一遍 sync/async？

在脚本里 `time.sleep` 只卡住「当前这次运行」。  
在 ASGI 服务里，错误的阻塞可能卡住**事件循环上的所有请求**。

#### 怎么理解

| 类型 | 特征 | Web 含义（FastAPI） |
|------|------|---------------------|
| 同步 endpoint | 普通 `def` | 框架丢到**线程池**跑；阻塞占的是工人线程 |
| 异步 endpoint | `async def` | 在**事件循环**上跑；内部应 `await` I/O |

心智图：

```text
请求进来
  ├─ def endpoint     → 线程池工人执行（别耗尽池子）
  └─ async def endpoint → 事件循环调度（别用同步阻塞卡住 loop）
```

#### 跑一下（对照表，对接练习 B4）

先做判断，再对答案：

| 场景 | 更合理的选择 | 原因 |
| --- | --- | --- |
| 只返回固定 JSON 的 `/health` | `def` 或 `async def` 都行 | 几乎无 I/O；团队统一风格即可 |
| 内部 `await httpx` 调 LLM | `async def` | 等待时应让出循环 |
| 内部只能用同步 `requests` | `def`（线程池）或 `async`+`to_thread` | 勿在 async 里直接 `requests.get` |
| 重 CPU（本地大 JSON 变换） | `def` / `to_thread` / 进程池 | 避免占满事件循环 |

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 以为「写成 `async def` 就更快」 | 没有 await 让出时，只是换了调度入口 |
| 以为 `def` 不能用于 I/O | 可以，但占线程池；池耗尽后新请求排队 |
| 混用时从不测延迟 | 线上才发现「一个慢请求拖垮他人」 |

#### 前端对照

| JS/Express | Python/FastAPI |
| --- | --- |
| `async (req,res)` 里 `await fetch` | `async def` 里 `await httpx` |
| `async` 里同步重计算卡事件循环 | 同：卡 asyncio loop |
| CPU 重活丢 Worker 线程 | `def` 线程池或 `asyncio.to_thread` |

Node 与 asyncio 都是「一线程合作式调度」家族——**阻塞事件循环是同款事故**。

---

### 4.2 FastAPI 语境下的选型规则

#### 为什么要有规则，而不是「全部 async」？

Agent 依赖的库有的异步友好（httpx、许多官方 SDK），有的只有同步 API。  
规则帮你在「正确」与「现实」之间落地。

#### 怎么理解（规则清单）

1. **纯 I/O**（HTTP 调 LLM、异步 DB）→ 优先 `async def` + `await`  
2. **重 CPU 或只有同步库** → `def`（框架丢线程池）或在 `async def` 里 `await asyncio.to_thread(...)`  
3. **千万别在 `async def` 里同步 `requests.get` / `time.sleep`** → 卡住**事件循环**，比占满线程池更严重  
4. **`def` 里阻塞**主要耗线程池配额；池耗尽后新请求才会大面积排队  
5. **health / 极简探活**保持轻量：不要在探活路径上调 LLM  

这和模块 05 完全同一套纪律，只是受害者从「一个脚本」变成「整站租户」。

#### 怎么写（形状对比）

```python
import asyncio
import time

import httpx
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat-async")
async def chat_async(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 示意：假上游
        r = await client.post("https://httpbin.org/delay/1", json=payload)
        return {"upstream_status": r.status_code}


@app.post("/v1/cpu-bound")
def cpu_bound() -> dict[str, str]:
    # 同步 endpoint：阻塞落在线程池，不直接卡 loop
    time.sleep(0.05)  # 假装一点计算/同步库
    return {"ok": "true"}


@app.post("/v1/sync-lib-from-async")
async def sync_lib_from_async() -> dict[str, str]:
    def call_sync_lib() -> str:
        time.sleep(0.05)
        return "done"

    result = await asyncio.to_thread(call_sync_lib)
    return {"result": result}
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `async def` + `time.sleep` | 合作式调度被冻住，其它请求一起饿死 |
| `async def` + 同步 `requests` | 同上，且连接管理更差 |
| 无限放大线程池「先顶住」 | 掩藏设计问题，内存与切换成本上升 |

#### 前端 Express 对照

```javascript
// 错误：看起来 async，其实卡 loop
app.post("/bad", async (req, res) => {
  const buf = require("fs").readFileSync("/huge") // 同步 I/O
  res.send(buf)
})

// 正确方向：异步 I/O 或丢线程池/队列
app.post("/ok", async (req, res) => {
  const data = await fs.promises.readFile("/huge")
  res.send(data)
})
```

---

### 4.3 阻塞事故：用户会看见什么？

#### 为什么要做「事故复盘」？

练习 A2 就是这类题。能描述现象，才会在日志里找对层。

#### 怎么理解

假设：`async def` 路由里执行 `time.sleep(10)`（或同步 HTTP 10s）：

```text
现象（单 worker / 单事件循环视角）：
  - 该请求约 10s 后才返回（若没被网关先斩）
  - 同一进程上其它请求的延迟一起恶化（循环被占满）
  - CPU 可能不高（在睡），但吞吐掉崖
  - 多 worker 时：只有踩到该 worker 的请求遭殃，表现为「偶发极慢」
```

定位顺序：

1. 看路径：是否集中在某个 async 路由  
2. 看代码：`sleep` / `requests` / 同步 SDK / 重计算  
3. 看部署：几个 uvicorn worker？是否被网关 60s 超时斩断  
4. 修复：改 `await asyncio.sleep` / 异步客户端 / `to_thread` / 把重活丢队列  

#### 示意（错误 vs 正确）

```python
# 错误：卡 loop
@app.post("/v1/bad")
async def bad() -> dict[str, str]:
    time.sleep(10)
    return {"ok": "true"}


# 正确：让出
@app.post("/v1/good")
async def good() -> dict[str, str]:
    await asyncio.sleep(10)  # 演示用；真 LLM 应 await 客户端
    return {"ok": "true"}
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只看「本请求最终 200」 | 忽略了同进程邻居的尾延迟 |
| 把网关 504 当成「LLM 一定挂了」 | 也可能是你自己阻塞到被反代超时 |
| 用更多 async 路由「堆并发」却不改阻塞点 | 并发入口更多，事故半径更大 |

#### 前端对照

Chrome 里「一个慢 API」若卡的是浏览器主线程，页面会冻；  
在 Node/asyncio 服务端，冻的是**调度器**——其它连接一起遭殃。叙事同构。

---

## 5. 建议掌握：WSGI vs ASGI

### 5.1 一张表建立时代差

#### 为什么要分清 WSGI / ASGI？

否则你会把 FastAPI「当成会异步的 Flask」乱部署，或奇怪「为什么教程都在讲 uvicorn」。

#### 怎么理解

| | WSGI | ASGI |
|--|------|------|
| 时代 | 传统同步 Python Web | 异步友好（也可跑同步应用） |
| 代表应用 | Flask、传统 Django 部署 | FastAPI / Starlette / Django ASGI 模式 |
| 调用模型 | 同步可调用对象，一次请求一次调用 | `async` 可等待的应用接口；支持长连接等 |
| 并发常见手法 | 多进程 / 多线程工人 | 事件循环 + 多 worker 进程 |
| 典型服务器 | gunicorn+sync workers、uwsgi 等 | **uvicorn**、hypercorn、daphne 等 |

FastAPI 基于 Starlette，应用协议是 **ASGI**。  
本地开发最常见：

```bash
uvicorn app.main:app --reload
```

读法：

```text
uvicorn          → ASGI 服务器（进程、连接、HTTP/WS 协议）
app.main:app     → Python 路径：模块 app.main 里的 app 对象
--reload         → 开发热重载（生产勿当性能方案）
```

#### 怎么理解（三层别混）

```text
你写的路由代码     → 应用（FastAPI）
uvicorn/gunicorn   → 应用服务器（ASGI/WSGI server）
Nginx/Caddy/云 LB  → 反向代理 / 网关（第 6 节）
```

「框架」≠「服务器」。Flask 应用也要挂到 WSGI server 上；FastAPI 同理要挂到 ASGI server。

#### 跑一下（只要记住启动句，不必此刻写全项目）

```bash
# 下一章创建 app 后：
uvicorn app.main:app --reload --port 8000
# 浏览器打开 http://127.0.0.1:8000/docs
```

若你暂时只有第 1 节的标准库 server，也能体会「**服务器进程在前台常驻**」——uvicorn 只是把这件事做成了 ASGI 标准件。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用「跑 Flask 的方式」硬套 FastAPI | 选错服务器或失去异步能力 |
| 以为 `python app.py` 里 `uvicorn.run` 与「框架本身」是一回事 | 部署时仍要明确工人数、绑定、代理头 |
| 生产开 `--reload` | 多余父子进程与重载，行为与性能都不合适 |

#### 前端对照

| Node 世界 | Python 世界 |
| --- | --- |
| Express app | FastAPI app |
| `node` / `http.createServer` | uvicorn（ASGI server） |
| 旧时代部分 PHP-FPM 同步模型 | WSGI 同步工人模型 |
| 现代 Node 天然偏事件循环 | ASGI 把事件循环模型标准化 |

---

### 5.2 FastAPI 为什么通常用 uvicorn？

#### 为什么这个问题会出现在练习 A1？

因为「能跑」有很多方式，但**默认生态位**要清楚，避免错误类比。

#### 怎么理解（写给 A1 的 5 行答案骨架）

1. FastAPI/Starlette 暴露的是 **ASGI** 应用，不是经典 WSGI 可调用对象。  
2. **uvicorn** 是常用 ASGI 服务器，负责把 HTTP 连到 ASGI 接口，并驱动事件循环。  
3. 异步 endpoint、WebSocket、流式等能力，走 ASGI 更自然。  
4. 传统「只启同步 Flask + 同步工人」的心智，不能直接解释 FastAPI 的并发模型。  
5. 生产上仍常见「网关 + 多 uvicorn worker」；细节见了解节与部署章。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 「ASGI = 一定更快」 | 慢在 LLM 时，换协议层救不了；要优 I/O 与超时 |
| 「有了 ASGI 就不用多进程」 | 多核与隔离仍常靠多个 worker 进程 |

---

## 6. 了解即可：网关与反向代理

### 6.1 部署草图（先认边界）

#### 为什么现在要扫盲？

你本地 `uvicorn --reload` 就够学 API；但 Agent 一对外，TLS、限流、多实例会立刻出现。  
本章只建立地图，不要求会配 Nginx。

#### 怎么理解

```text
Internet
   → Nginx / Caddy / 云 Load Balancer（网关/反向代理）
        → uvicorn workers（ASGI server 进程）
             → FastAPI 应用（路由 / 中间件 / endpoint）
```

分工直觉：

| 层 | 常负责 | 不太负责 |
| --- | --- | --- |
| 网关 / 反代 | TLS 终止、限流、静态资源、负载均衡、缓冲、部分 WAF | 业务编排、Pydantic 校验细节 |
| uvicorn | HTTP→ASGI、工人进程、并发连接 | 产品业务规则 |
| FastAPI | 路由、中间件、校验、鉴权、调用 LLM/Tool | 对外证书与机房流量工程 |

TLS 终止常见在网关；应用看到的常是 HTTP（内网）。  
练习 C1 要你画的，就是这张图加上「证书在哪一层卸下」。

#### 示意（请求头与真实 IP——了解级）

```text
客户端 → 网关 → uvicorn
网关常加：
  X-Forwarded-For
  X-Forwarded-Proto
应用若要做审计/限流，需信任代理并正确解析（部署章再细）
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把 uvicorn 直接裸奔在 443 上当唯一方案 | 缺统一 TLS/限流/多服务入口时难运维 |
| 在应用里重复实现全部网关能力 | 职责膨胀，发布与语言绑定过死 |
| health 不区分「进程活着」与「依赖全好」 | 探活策略过严或过松（了解：liveness vs readiness） |

#### 前端对照

| 前端/站点常见 | 后端同学视角 |
| --- | --- |
| CDN / Nginx 托管静态资源 | 反代把 `/api` 转到 uvicorn |
| Vercel/Netlify 边缘到 Serverless | 云 LB → 容器里的 ASGI |
| 浏览器只认 HTTPS | 证书常在网关终结 |

---

### 6.2 和「应用内中间件」如何分工（地图）

#### 为什么要分工？

同一能力（限流、鉴权、日志）可以出现在网关或应用。  
了解级结论即可：

```text
网关更擅长：TLS、连接级限流、全局 WAF、多服务路由、静态资源
应用更擅长：业务鉴权、请求体校验、领域日志字段、Agent 编排超时
两者重叠时：网关做粗过滤，应用做细规则；避免两套互相打架的真相源
```

Agent 服务最低配对外形态：

```text
云 LB / Nginx
  → uvicorn
      → FastAPI
          → /health
          → /v1/agent/run（API Key + 超时 + FakeLLM/真模型）
```

---

## 7. 常见坑

把全章易错点收成排障清单（写下一章代码前扫一眼）：

1. **把业务逻辑全写在 endpoint** → 难单测、难复用；应下沉 service，endpoint 变薄  
2. **异步路由里同步阻塞**（`requests` / `time.sleep` / 重 CPU）→ 事件循环饥饿，同进程请求一起慢  
3. **中间件顺序不符合预期** → 鉴权/日志/CORS 错位；记住 FastAPI「后 add 更靠外」，并用日志验证  
4. **忘记区分「框架」与「ASGI 服务器」** → 部署与排障找错层（FastAPI vs uvicorn vs Nginx）  
5. **以为 404 不进应用中间件** → 漏请求 ID/访问日志；Starlette 模型是中间件包在 Router 外  
6. **在匹配路由前的中间件里读 path params** → 拿不到或行为未定义；细逻辑放 Depends/endpoint  
7. **health 过重或被鉴权误伤** → 发布与编排探活失败  
8. **用模块级可变全局保存「当前用户/会话」** → 并发下串味  
9. **把网关 504 只怪 LLM** → 也可能是自己阻塞或未设应用侧超时  
10. **Express 的 `use` 顺序经验直接套 `add_middleware`** → 两套默认顺序语义不同，先画洋葱再下结论  

---

## 8. 练习指引

[`exercises/06-web-backend/01-web-framework-principles.md`](../../exercises/06-web-backend/01-web-framework-principles.md)

建议路径：

1. **B1** 对照第 2 节画出 7～9 步，标注鉴权与 LLM 插入点  
2. **B2** 用第 3.1 节清单设计 4 个端点（含 health 与 run）  
3. **B3** 用第 3.2 / 3.3 节列出 3 件适合中间件、2 件不适合的事  
4. **B4** 用第 4 节判断 sync/async，并写出「只有同步库时」的改法  
5. （建议）**A1** 对照第 5 节写「为何 uvicorn + ASGI」  
6. （建议）**A2** 对照第 4.3 节做阻塞事故复盘  
7. （可选）**C1** 对照第 6 节画部署草图并标 TLS 终止  

playground 目录：`playground/06-web-backend/01-web-framework-principles/`

---

## 9. 小结与下一站

### 自检

- [ ] 能口述请求生命周期（含中间件在 Router 外、404 仍可能过中间件）  
- [ ] 知道中间件适合做什么、不适合做什么；能与 Depends 粗分职责  
- [ ] 能判断 endpoint 该 sync 还是 async，并能解释 async 内阻塞的事故形态  
- [ ] 能区分 FastAPI（框架）、uvicorn（ASGI server）、Nginx（网关/反代）  
- [ ] 能把 Agent 服务化（health / run / 鉴权 / 超时）接到同一张路径图上  

### 把地图带去下一章

```text
本章：请求怎么走、横切怎么挂、并发怎么选、部署三层是谁
下一章：FastAPI + Pydantic 具体怎么写
  - 路由与参数
  - 请求/响应模型与校验错误
  - Depends 组织配置与鉴权前置
  - /docs 调试与轻量 BackgroundTasks
```

### 下一章

[`02-fastapi-pydantic.md`](./02-fastapi-pydantic.md) —— 动手 FastAPI + Pydantic。

## 导航

- 返回模块：[README](./README.md)
- 下一章：[FastAPI + Pydantic](./02-fastapi-pydantic.md)
- 上一模块：[Python 异步编程](../05-async-python/README.md)
