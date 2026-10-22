# 练习：Web 框架原理

> 对应文档：[`docs/06-web-backend/01-web-framework-principles.md`](../../docs/06-web-backend/01-web-framework-principles.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 本章偏**概念与设计**，很多题是书面 + 小段 Python；不要求立刻起完整 FastAPI 项目（下章再写）。
4. 建议代码目录：

```text
playground/06-web-backend/01-web-framework-principles/
```

5. 先自己做完，再看文末「提示与参考答案」。书面题用自己的话写清即可，不必与参考答案逐字相同。
6. Python ≥ 3.11；注解用 `list[str]`、`str | None`。

---

## 热身题（建议先做）

> 每题几分钟。把「请求 / 路由 / 阻塞」心智先踩一遍。

### W1. 一句话：框架在干什么？

**要求**：用一两句话说明 Web 框架帮你做了哪些「脏活」（至少提路由、请求解析、响应序列化中的两项）。

**验收**：能说清「框架不是业务本身，而是把 HTTP 接到你的函数」。

---

### W2. 方法 + 路径

**给定**：下列需求。

**要求**：为每条写出「HTTP 方法 + 路径」建议（一句话即可）：

1. 探活（不查 DB）
2. 提交一次 Agent 运行
3. 按 id 查询会话

**验收**：方法语义合理（探活多用 GET；提交多用 POST）。

---

### W3. 同步阻塞直觉

**给定**：`time.sleep(2)` 与 `await asyncio.sleep(2)`。

**要求**：各用一句话说明它们在「单进程 async 服务」里对**其它请求**的影响差异。

**验收**：能说出 sleep 会占住事件循环线程 vs await sleep 会让出。

---

### W4. 中间件 vs endpoint

**要求**：判断对错并改一句：

> 「把业务校验、写库、调 LLM 全塞进中间件，endpoint 留空最干净。」

**验收**：能指出中间件适合横切关注点，业务应在 endpoint/service。

---

## 基础题（必做）

### B1. 画生命周期（含鉴权与 LLM）

用文字或 ASCII 画出：一次请求从客户端到 endpoint 再返回的 **7～9 步**。

**强制标注**：

1. 「鉴权（如校验 API Key）」可能插在哪一步附近
2. 「LLM 调用」通常落在哪一层（endpoint / service）
3. 中间件「进」与「出」各至少标一次

**期望结构示例（可改写成自己的）**：

```text
Client
  → 1) TCP/TLS
  → 2) 反向代理（可选）
  → 3) ASGI 服务器接收
  → 4) 外层中间件 in
  → 5) 路由匹配
  → 6) 依赖 / 鉴权
  → 7) endpoint → service → LLM
  → 8) 中间件 out（状态码、耗时）
  → 9) 响应回客户端
```

**验收**：步骤完整；鉴权不画在「已经调完 LLM 之后才第一次检查」这种明显反模式上（除非你明确写「错误示范」）。

---

### B2. 迷你 Agent 服务路由设计

为「可分享的迷你 Agent API」设计 **至少 4 个端点**。

每个端点写清：

| 字段 | 内容 |
|------|------|
| 方法 | GET / POST / … |
| 路径 | 如 `/v1/agent/run` |
| 职责 | 一句话 |
| 是否会调 LLM | 是 / 否 |

**硬性要求**：

1. 必须含 **health**（探活）
2. 必须含 **run**（触发一次 Agent）
3. 另外至少 2 个（例如会话查询、取消、简易 job 状态等，自定）

**验收**：health 不应绑定 LLM；run 的路径与方法语义合理。

---

### B3. 中间件职责清单

列出：

1. **3 件适合**放中间件的事（横切、与具体业务弱耦合）
2. **2 件不适合**放中间件的事（应下沉到 Depends / service / endpoint）

每条加半句理由。

**验收**：适合类里至少覆盖「日志 / 请求 ID / CORS / 统一计时」中的两类；不适合类里至少提到「调 LLM」或「写业务表」之一。

---

### B4. sync vs async 三问

判断并简述（每题 2～4 句）：

1. endpoint **只返回固定 JSON**，要不要写成 `async def`？可以，但关键点是什么？
2. endpoint 内 `await httpx.AsyncClient...` 调 LLM —— 这样写的意图是什么？
3. endpoint 内用同步 `requests.get(...)` 调 LLM —— 用户可能观察到什么？你该怎么改（至少给一种正确方向）？

**验收**：第 3 问不能只写「无所谓」；必须点出阻塞事件循环或改用异步客户端 / 线程池等对策之一。

---

## 进阶题（建议至少做 1 题）

### A1. WSGI / ASGI 对照（书面）

写一段 **约 5～8 行** 说明：

1. WSGI 与 ASGI 各解决什么时代的问题（极简）
2. FastAPI 为什么通常用 **uvicorn（ASGI）**，而不是「像旧 Flask 同步模型那样想当然」
3. 和 Agent（大量等待 LLM/HTTP）有什么关系

**验收**：能把「异步 I/O 等待」和 ASGI 选型连上，而不是只背名词。

---

### A2. 阻塞事故复盘（书面）

假设有人在 `async def` 路由里写了 `time.sleep(10)`（不是 `await asyncio.sleep`）。

请回答：

1. 单 worker、多并发用户时，**其它请求**可能观察到什么？
2. 你如何定位（日志字段、耗时、线程/事件循环线索，列 3 步即可）？
3. 最小修复是什么？若必须跑 CPU 重活，方向是什么？

**验收**：明确「async 函数里同步 sleep 仍会堵住事件循环」。

---

## 挑战题（可选）

### C1. 部署草图 + TLS

画出：

```text
Internet → 反向代理 → uvicorn → FastAPI(app)
```

并标注：

1. **TLS 终止**常见落在哪一层（可写「多数在反向代理」）
2. 健康检查探针更适合打哪一层的哪个路径
3. 应用日志里 request_id 理想从哪一层注入

**验收**：图上能看出「外网不直连业务进程」的一种常见形态即可。

---

### C2. 迷你「洋葱顺序」实验（代码）

用纯 Python（不必 FastAPI）模拟两层中间件 + endpoint，打印进入/离开顺序。

约定接口可自定，例如：

```python
def run_pipeline(middlewares: list, endpoint, request: dict) -> dict:
    ...
```

**期望输出顺序类似**：

```text
→ mw_logging
→ mw_auth
* endpoint
← mw_auth
← mw_logging
```

**验收**：顺序符合洋葱模型；auth 失败时可短路且仍能演示 logging 的 out（或明确你的短路策略）。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W4 先做完
- [ ] **通过线**：B1～B4 全部完成（书面可写在同目录 `.md`）
- [ ] 能口述：中间件适合什么、不适合什么；async 路由里同步阻塞的危害
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1 或 C2

---

## 提示与参考答案（先做题再看）

> 每题先给**思路**，再给**参考作答 / 参考实现**。书面题表述可以不同，要点对齐即可。

### W1 思路 + 参考答案

**思路**：框架 = HTTP 适配层；业务函数只关心「入参结构 / 返回结构」。

**参考答案**：Web 框架负责把 HTTP 方法与路径映射到处理函数，解析 query/body/header，并把返回值序列化成响应；鉴权、日志等还可通过中间件/依赖横切注入。业务代码不应手写裸 socket 协议细节。

---

### W2 思路 + 参考答案

**思路**：读操作用 GET；提交副作用用 POST；资源用路径参数。

**参考答案**：

1. `GET /health` — 探活
2. `POST /v1/agent/run` — 提交一次运行
3. `GET /v1/sessions/{session_id}` — 查询会话

---

### W3 思路 + 参考答案

**思路**：事件循环线程被同步占用 vs await 让出。

**参考答案**：`time.sleep(2)` 在 async 服务里会卡住当前事件循环线程，其它协程请求也可能一起卡住；`await asyncio.sleep(2)` 会挂起当前协程并让出循环，其它请求仍可被调度。

---

### W4 思路 + 参考答案

**思路**：中间件太厚 = 无法复用、难测、难读。

**参考答案**：该说法错误。中间件适合日志、CORS、请求 ID、统一计时等横切逻辑；写库、调 LLM、业务校验应放在 endpoint / service / Depends，便于单测与复用。

---

### B1 思路 + 参考答案

**思路**：按「进站 → 横切 → 路由 → 鉴权 → 业务 → 出站」画；LLM 在业务层。

**参考答案（ASCII）**：

```text
Client
  → 1) 建立连接 / TLS（常在反向代理终止）
  → 2) 反向代理转发到 uvicorn
  → 3) ASGI 接收 scope/receive/send
  → 4) 外层中间件 in（logging / request_id）
  → 5) 路由匹配到 handler
  → 6) Depends：校验 API Key（鉴权插入点）
  → 7) endpoint → application service → 调用 LLM（业务插入点）
  → 8) 中间件 out（写耗时、状态码）
  → 9) 响应返回 Client
```

说明：鉴权应在昂贵的 LLM 调用之前；中间件包在路由外，404 也可能打到外层日志中间件。

---

### B2 思路 + 参考答案

**思路**：先保证可运维（health），再暴露能力（run），再补查询类只读接口。

**参考答案**：

| 方法 | 路径 | 职责 | 调 LLM |
|------|------|------|--------|
| GET | `/health` | 进程存活探活 | 否 |
| POST | `/v1/agent/run` | 同步触发一次 Agent | 是 |
| GET | `/v1/sessions/{session_id}` | 查询会话元数据/摘要 | 否 |
| GET | `/v1/jobs/{job_id}` | 查询异步任务状态（为以后队列化预留） | 否 |

---

### B3 思路 + 参考答案

**思路**：横切 → 中间件；业务决策 → 下层。

**参考答案**：

适合中间件：

1. 访问日志 / 结构化请求日志（所有路由统一）
2. 注入/传递 `request_id`（链路关联）
3. CORS 或统一安全响应头

不适合中间件：

1. 调用 LLM 拼 prompt（业务核心，难测）
2. 按业务规则写多表事务（应在 service；中间件无业务上下文时更糟）

---

### B4 思路 + 参考答案

**思路**：`async def` 不是装饰品；关键是函数体是否真的 await 非阻塞 I/O。

**参考答案**：

1. 只返回固定 JSON 时，`def` 或 `async def` 都可以；若写成 `async def` 却内部同步阻塞，反而有害。关键点是「不要假装异步」。
2. `await httpx` 的意图：在等待 LLM/HTTP 时让出事件循环，提高并发承载。
3. `requests` 是同步阻塞调用，会卡住事件循环，表现为延迟尖刺、其它请求一起变慢。改法：换 `httpx.AsyncClient` 并 `await`；或把同步调用丢到 `asyncio.to_thread` / 线程池（权宜）；长任务则应上队列（见模块 07）。

---

### A1 思路 + 参考答案

**思路**：WSGI 同步请求-响应；ASGI 原生支持 async 与长连接类协议。

**参考答案**：

1. WSGI 面向传统同步 Web（一请求一处理模型的经典适配）；ASGI 面向异步应用与更多协议形态。
2. FastAPI/Starlette 是 ASGI 应用，需 ASGI 服务器（如 uvicorn）加载；硬套「旧同步 WSGI 心智」会丢掉 await 并发模型的收益。
3. Agent 服务大量时间花在等待 LLM/HTTP，ASGI + async 更匹配「等待型」负载；但这不意味着可以在 async 路由里随便 `time.sleep` 或同步 `requests`。

---

### A2 思路 + 参考答案

**思路**：症状 → 假设阻塞 → 用耗时与代码审查定位 → 修复。

**参考答案**：

1. 其它请求可能一起变慢或超时，即使它们自己的 handler 很轻；健康检查也可能抖动。
2. 定位三步：看 p99 延迟是否集体上升；对可疑路由打入口/出口耗时日志；在代码里搜 `time.sleep` / 同步 HTTP / 重 CPU，确认发生在 `async def` 路径上。
3. 最小修复：改成 `await asyncio.sleep(10)`（若仅为演示等待）。若是 CPU 重活：放到进程池/独立 worker；若是长任务：不要卡在请求内，改用消息队列（`BackgroundTasks` 也不适合真正的长任务）。

---

### C1 思路 + 参考答案

**思路**：TLS 与公网暴露面尽量停在边缘；应用只听内网端口。

**参考答案**：

```text
Internet
  → Reverse Proxy (Nginx/Caddy)  ← 常见 TLS 终止点；可做 /health 探活
  → uvicorn (:8000, 内网)
  → FastAPI app
       └─ middleware: request_id 注入（也可由代理传入 X-Request-ID）
```

- TLS：多数在反向代理终止，再到 uvicorn 走明文 HTTP（内网）。
- 探针：优先打代理或应用的 `GET /health`（不要打会触发 LLM 的路径）。
- request_id：代理生成并传入，或最外层中间件生成。

---

### C2 思路 + 参考答案

**思路**：中间件包装 `call_next`；先注册的外层后进入、先离开。

**参考答案**

```python
from __future__ import annotations

from collections.abc import Callable

Handler = Callable[[dict], dict]
Middleware = Callable[[Handler], Handler]


def mw_logging(next_handler: Handler) -> Handler:
    def wrapper(request: dict) -> dict:
        print("→ mw_logging")
        response = next_handler(request)
        print(f"← mw_logging {response.get('status', '?')}")
        return response

    return wrapper


def mw_auth(next_handler: Handler) -> Handler:
    def wrapper(request: dict) -> dict:
        print("→ mw_auth")
        if request.get("api_key") != "secret":
            print("← mw_auth 401")
            return {"status": 401, "body": {"detail": "unauthorized"}}
        response = next_handler(request)
        print("← mw_auth")
        return response

    return wrapper


def endpoint(request: dict) -> dict:
    print("* endpoint")
    return {"status": 200, "body": {"echo": request.get("path")}}


def run_pipeline(
    middlewares: list[Middleware],
    endpoint_handler: Handler,
    request: dict,
) -> dict:
    handler = endpoint_handler
    # 与常见框架类似：先包装的更靠内；列表从外到内注册时用反转
    for middleware in reversed(middlewares):
        handler = middleware(handler)
    return handler(request)


if __name__ == "__main__":
    # 注册顺序：logging 在外，auth 在内
    run_pipeline([mw_logging, mw_auth], endpoint, {"path": "/v1/run", "api_key": "secret"})
    print("---")
    run_pipeline([mw_logging, mw_auth], endpoint, {"path": "/v1/run", "api_key": "bad"})
```

期望成功路径打印顺序：

```text
→ mw_logging
→ mw_auth
* endpoint
← mw_auth
← mw_logging 200
```
