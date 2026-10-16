# 网络与 HTTP

> 所属模块：`04-systems-basics` · 计算机与服务端基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/04-systems-basics/02-network-http.md`](../../exercises/04-systems-basics/02-network-http.md)

## 本章定位

- **本章角色**：搞清 Agent 调 LLM / 工具 API 时，网络栈与 HTTP 在干什么。
- **你的优势**：前端天天碰 HTTP；这里补服务端视角与排障用语。

## 学习目标

1. 具备 TCP/IP 分层直觉（不背全协议细节）。
2. 熟练使用 HTTP 方法、状态码、常见头。
3. 能设计/调用 JSON API，并处理超时与错误响应。
4. 理解 HTTPS、幂等与重试的基本边界。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | TCP/IP 直觉、HTTP 方法/状态码/头、JSON API | 能读文档、能排错 |
| **建议掌握** | HTTPS、幂等与重试 | 能安全地重试 |
| **了解即可** | HTTP/2、WebSocket | 扫盲 |

---

## 1. 为什么要学

```text
你的 Agent
  --HTTP JSON-->  LLM Provider
  --HTTP JSON-->  自建 Tool API
  --HTTP JSON-->  向量库 / DB 网关
```

几乎全是网络调用。不会 HTTP，就看不懂 401/429/502、超时、重试风暴。

---

## 2. 必掌握：TCP/IP 直觉

极简分层：

```text
应用层：HTTP / DNS
传输层：TCP（可靠字节流）/ UDP
网络层：IP（寻址与路由）
链路/物理：网卡与线缆/Wi-Fi
```

对你有用的结论：

1. **HTTP 通常跑在 TCP 上**（还有 HTTP/3/QUIC，了解即可）
2. 连接要建立（握手），有 **延迟 RTT**；跨洋调用更明显
3. 网络会丢包/重传 → 表现为偶发变慢，不是你代码“随机坏了”
4. **超时**是必须设置的：对方可能永远不回

```python
# 概念：任何 HTTP 客户端都应设 timeout
# httpx.Client(timeout=30.0)
```

---

## 3. 必掌握：HTTP 方法 / 状态码 / 头

### 3.1 方法

| 方法 | 含义 | 常见用途 |
|------|------|----------|
| GET | 读取 | 查资源 |
| POST | 提交/创建/动作 | **Chat Completions 常用 POST** |
| PUT/PATCH | 更新 | REST 资源 |
| DELETE | 删除 | REST 资源 |

### 3.2 状态码（先记这些）

| 码 | 含义 | Agent 里 |
|----|------|----------|
| 200 | 成功 | 正常 |
| 201 | 已创建 | REST |
| 400 | 请求坏了 | 参数错误 |
| 401 | 未认证 | API Key 问题 |
| 403 | 无权限 | 权限不足 |
| 404 | 没有 | 路径错 |
| 504 | 网关上游超时 | 对端/上游太慢；常可有限重试 |
| 502/503 | 坏网关 / 不可用 | 瞬时故障时常可退避重试 |
| 408 | 服务端等请求体超时 | 较少见；**≠** 你在客户端设的 `timeout` |
| 429 | 太多了 | **限流，常需退避重试** |
| 500 | 服务端内部错误 | 可重试与否看场景 |

客户端 `httpx`/`requests` 超时：通常是**本地抛异常**（如 `TimeoutException`），不会变成 HTTP 408。排障时把「库超时」和「网关 504」分开看。

### 3.3 常见头

```text
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
Retry-After: 30
User-Agent: my-agent/0.1
```

流式输出时还常见 `text/event-stream`（SSE）。

---

## 4. 必掌握：JSON API

典型请求：

```http
POST /v1/chat/completions HTTP/1.1
Host: api.example.com
Authorization: Bearer sk-xxx
Content-Type: application/json

{"model":"gpt-x","messages":[{"role":"user","content":"hi"}]}
```

典型响应：

```json
{"id":"...","choices":[{"message":{"role":"assistant","content":"hello"}}]}
```

Python 侧心智：

```python
import json

payload = {"model": "gpt-x", "messages": [{"role": "user", "content": "hi"}]}
body = json.dumps(payload).encode("utf-8")
# 用 httpx/requests 发送后：
# data = response.json()
```

错误响应也常是 JSON：`{"error":{"message":"...","type":"..."}}`  
要解析并转成你的领域异常（回顾异常章）。

---

## 5. 建议掌握：HTTPS 与重试

### 5.1 HTTPS

= HTTP + TLS 加密与证书校验。  
保护令牌不被明文窃听；证书错误时不要随手关掉校验（除非本地调试且清楚风险）。

### 5.2 幂等与重试

| 操作 | 是否相对安全重试 |
|------|------------------|
| GET 查询 | 通常是 |
| PUT 幂等更新 | 协议上**应**幂等（实现须守约） |
| POST 创建订单/扣费 | **小心**，可能重复副作用 |
| LLM POST | 常可重试，但可能重复扣 token、重复产生副作用工具调用 |

原则：

- 只对**瞬时错误**重试（超时、429、502…）
- 用指数退避 + 抖动
- 工具调用要有**幂等键**或“先查后做”

---

## 6. 了解即可：HTTP/2 与 WebSocket

- **HTTP/2**：多路复用，减少连接数；很多客户端自动支持
- **WebSocket**：全双工长连接，适合双向推送；Agent 流式也常用 SSE/HTTP stream

---

## 7. 常见坑

1. 没设 timeout，线程挂死
2. 429 仍疯狂重试，变成重试风暴
3. 把 HTML 错误页当 JSON 解析
4. 日志打印完整 Authorization
5. 忽略代理/公司网络对 TLS 的影响

---

## 8. 练习指引

[`exercises/04-systems-basics/02-network-http.md`](../../exercises/04-systems-basics/02-network-http.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能解释超时为何必要
- [ ] 见到 401/429/5xx 知道优先怀疑什么
- [ ] 能描述一次 JSON API 请求/响应

### 下一章

[`03-concurrency-models.md`](./03-concurrency-models.md) —— 并发模型：线程/进程/异步怎么选。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[操作系统基础](./01-os-basics.md)
- 下一章：[并发模型](./03-concurrency-models.md)
