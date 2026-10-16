# Web 框架原理

> 所属模块：`06-web-backend` · Web 后端  
> 状态：`已完成正文`  
> 建议学时：2～4 小时  
> 对应练习：[`exercises/06-web-backend/01-web-framework-principles.md`](../../exercises/06-web-backend/01-web-framework-principles.md)

## 本章定位

- **模块目标**：能独立搭建并理解后端 API 服务。
- **本章角色**：先搞清「请求进来后发生了什么」，再学 FastAPI 才不会只停留在抄装饰器。
- **前置**：HTTP（模块 04）、asyncio（模块 05）。

## 学习目标

1. 描述一次 HTTP 请求的服务端生命周期。
2. 理解路由与中间件各自解决什么问题。
3. 分清同步处理与异步处理在 Web 里的含义。
4. 建立 WSGI/ASGI、网关/反向代理的地图。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 请求生命周期、路由/中间件、同步与异步处理 | 能画流程、能选型 |
| **建议掌握** | WSGI/ASGI | 能解释 FastAPI 为何是 ASGI |
| **了解即可** | 网关与反向代理 | 扫盲 |

---

## 1. 为什么要学

Agent 常以 API 形式对外：

```text
前端 / 其它服务
    --HTTP--> 你的 FastAPI
                 → 调 LLM
                 → 跑 Tool
                 → 返回 JSON
```

不懂框架原理时：超时、中间件鉴权、阻塞事件循环会反复踩坑。

---

## 2. 必掌握：请求生命周期

极简流程：

```text
1. 客户端发 HTTP 请求
2. 服务器接收连接（常由 uvicorn 等 ASGI server）
3. 应用级中间件入站（从前到后；后 add 的更靠外）
4. 框架匹配路由（路径 + 方法）——故 404 也会经过中间件
5. 依赖注入 / 解析参数 / 校验 body（Depends / Pydantic）
6. 执行 endpoint 函数
7. 序列化响应
8. 中间件出站（从后到前）
9. 发回 HTTP 响应
```

注意：Starlette/FastAPI 里**中间件包在 Router 外**，不是「先匹配路由再跑中间件」。  
`call_next` 之前通常还拿不到 path params。

你要关心的点：

- **哪一步做鉴权**（中间件或依赖）
- **哪一步做校验**（Pydantic）
- **哪一步最慢**（常是 LLM 调用）
- **异常在哪被捕获**成 4xx/5xx

---

## 3. 必掌握：路由与中间件

### 3.1 路由

把「方法 + 路径」映射到处理函数：

```text
GET  /health        → health()
POST /v1/chat       → chat()
POST /v1/agent/run  → run_agent()
```

路径参数、查询参数、请求体在下一章用 FastAPI 细讲。

### 3.2 中间件

环绕所有（或一批）请求的统一逻辑：

```text
请求 → 日志中间件 → 鉴权中间件 → 路由处理 → … → 响应
```

适合：

- 请求日志 / 耗时
- CORS
- 统一加请求 ID
- 粗粒度鉴权

不适合塞太多业务细节（业务放 endpoint / service）。

---

## 4. 必掌握：同步与异步处理

| 类型 | 特征 | Web 含义 |
|------|------|----------|
| 同步 endpoint | 普通 `def` | FastAPI 丢到**线程池**跑；阻塞占的是工人线程 |
| 异步 endpoint | `async def` | 在事件循环上跑；内部应 await I/O |

规则（FastAPI 语境）：

- 纯 I/O（HTTP 调 LLM、异步 DB）→ 优先 `async def`
- 重 CPU 或只提供同步库 → `def`（框架会丢线程池）或 `to_thread`
- **千万别在 `async def` 里同步 `requests.get` / `time.sleep`**（这会卡住**事件循环**，比占满线程池更严重）
- `def` 里阻塞主要耗线程池配额；池耗尽后新请求才会大面积排队

这和模块 05 完全同一套肌肉。

---

## 5. 建议掌握：WSGI vs ASGI

| | WSGI | ASGI |
|--|------|------|
| 时代 | 传统同步 Python Web | 异步友好 |
| 代表 | Flask/Django（传统部署） | FastAPI / Starlette / Django ASGI |
| 并发 | 多进程/多线程工人 | 事件循环 + 工人 |

FastAPI 基于 Starlette，走 **ASGI**；本地常用：

```bash
uvicorn app.main:app --reload
```

---

## 6. 了解即可：网关与反向代理

```text
Internet → Nginx/Caddy/云 LB → uvicorn workers → FastAPI
```

网关/反向代理负责：TLS、限流、静态资源、负载均衡、缓冲。  
应用只管业务。部署章会再遇。

---

## 7. 常见坑

1. 把业务逻辑全写在 endpoint，无法测试
2. 异步路由里阻塞
3. 中间件顺序导致鉴权/日志不符合预期
4. 忘记区分「框架」与「ASGI 服务器」

---

## 8. 练习指引

[`exercises/06-web-backend/01-web-framework-principles.md`](../../exercises/06-web-backend/01-web-framework-principles.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能口述请求生命周期
- [ ] 知道中间件适合做什么
- [ ] 能判断 endpoint 该 sync 还是 async

### 下一章

[`02-fastapi-pydantic.md`](./02-fastapi-pydantic.md) —— 动手 FastAPI + Pydantic。

## 导航

- 返回模块：[README](./README.md)
- 下一章：[FastAPI + Pydantic](./02-fastapi-pydantic.md)
