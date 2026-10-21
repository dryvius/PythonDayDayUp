# 网络与 HTTP

> 所属模块：`04-systems-basics` · 计算机与服务端基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有前端 `fetch`/`axios` 经验可更快；超时/重试/幂等建议动手踩一遍）  
> 对应练习：[`exercises/04-systems-basics/02-network-http.md`](../../exercises/04-systems-basics/02-network-http.md)

## 本章定位

- **模块目标**：补齐前端背景下的系统直觉，避免一知半解。
- **本章角色**：搞清 Agent 调 LLM / 工具 API 时，网络栈与 HTTP 在干什么；学会用「超时、状态码、重试、幂等」排障与设计边界。
- **你的优势**：前端天天碰 HTTP；这里补服务端视角、Python 客户端写法，以及和 Agent 强相关的超时/重试决策。
- **目标不是**：背全协议细节或成为网络工程师；够用、能对话、能排障即可。

## 学习目标（学完应能做到）

1. 具备 TCP/IP 分层直觉（不背全协议细节），能用 RTT / 丢包 / 超时解释「偶发变慢」。
2. 熟练使用 HTTP 方法、状态码、常见头，见到 `401/429/5xx` 知道优先怀疑什么。
3. 能设计/调用 JSON API，解析成功与错误响应，并转成领域异常。
4. 理解 HTTPS、幂等与重试的基本边界；能为 LLM HTTP 调用设计超时与有限退避重试。
5. 对 HTTP/2、WebSocket / SSE 建立地图，知道流式输出常见路径。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | TCP/IP 直觉、HTTP 方法/状态码/头、JSON API | 能读文档、能排错、能写调用 |
| **建议掌握** | HTTPS、幂等与重试、LLM 超时重试 | 能安全地重试，不制造风暴 |
| **了解即可** | HTTP/2、WebSocket / SSE | 扫盲，后面流式章再深挖 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要网络与 HTTP？

Agent 运行时几乎全是「出网调用」：

```text
你的 Agent
  --HTTP JSON-->  LLM Provider（Chat Completions）
  --HTTP JSON-->  自建 Tool API（搜索、工单、内部服务）
  --HTTP JSON-->  向量库 / DB 网关 / 对象存储签名 URL
```

没有 HTTP 直觉时，你会反复踩这些坑：

```text
卡死了 → 其实没设 timeout
偶尔失败 → 其实是丢包/重传或上游 503
钱烧了 → 429 后仍疯狂重试
密钥泄漏 → 日志打印了 Authorization
解析炸了 → 把 HTML 错误页当 JSON 读
```

#### 本章要练的三种能力

1. **读懂现场**：状态码、头、超时异常分别在说什么
2. **写对调用**：JSON 请求体、鉴权头、timeout、错误转译
3. **设好边界**：哪些错可重试、重试几次、如何退避、何时必须幂等

可以先记一句：

> Agent 的「智能」建立在一次次可靠的 HTTP 往返之上；网络章学的是如何让这些往返可控。

#### 前端对照（先建立地图）

| 前端你已熟悉 | 本章 Python / 服务端视角 |
| --- | --- |
| `fetch(url, { method, headers, body })` | `httpx` / `requests` 发请求 |
| `axios.get/post` + 拦截器 | 客户端封装 + 统一错误转译 |
| `AbortController` / `timeout` | `timeout=`（连接超时 vs 读超时） |
| `response.json()` | `response.json()`（同样要防非 JSON） |
| `401` 跳登录 | `401` → 查 API Key / Bearer，**不要盲重试** |

---

## 2. 必掌握：TCP/IP 直觉

这一节会刻意写细——后面所有「超时、变慢、偶发失败」都建立在这套分层与连接直觉上。

### 2.1 极简分层：包是怎么走的

#### 为什么需要分层直觉？

你不需要背全协议，但要知道「卡在哪一层」：DNS 解析失败、TCP 连不上、TLS 握手失败、HTTP 拿到 502——排障用语完全不同。

#### 怎么理解

```text
应用层：HTTP / DNS / WebSocket
传输层：TCP（可靠字节流）/ UDP（尽最大努力）
网络层：IP（寻址与路由）
链路/物理：网卡与线缆 / Wi-Fi
```

对你有用的结论：

1. **HTTP 通常跑在 TCP 上**（还有 HTTP/3 / QUIC，了解即可）
2. 连接要建立（握手），有 **延迟 RTT**；跨洋调用更明显
3. 网络会丢包 / 重传 → 表现为偶发变慢，不是你代码「随机坏了」
4. **超时**是必须设置的：对方可能永远不回

心智图（一次 LLM 调用大致路径）：

```text
你的进程
  → DNS 查 api.example.com
  → TCP 三次握手（建连，耗 RTT）
  → TLS 握手（HTTPS，再耗若干 RTT）
  → 发送 HTTP 请求（方法、路径、头、JSON body）
  → 等待响应（可能很长：模型在生成）
  → 读完响应 / 流式读 chunk
  → 连接复用或关闭
```

#### 跑一下（感受「本机 vs 外网」延迟）

下面不依赖第三方库，用标准库测一次 DNS + TCP 建连耗时（需可访问外网；公司网络受限可改成本机地址或跳过）：

```python
import socket
import time

host = "httpbin.org"
port = 443

t0 = time.perf_counter()
infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
t1 = time.perf_counter()
print(f"DNS: {(t1 - t0) * 1000:.1f} ms → {infos[0][4]}")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5.0)
t2 = time.perf_counter()
sock.connect(infos[0][4])
t3 = time.perf_counter()
print(f"TCP connect: {(t3 - t2) * 1000:.1f} ms")
sock.close()
```

预期：DNS 与建连各几十毫秒到数百毫秒都正常；跨地区会更大。这只是「还没发 HTTP、还没等模型」的固定成本。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把「偶发变慢」全怪业务代码 | 可能是丢包重传、拥塞、对端排队 |
| 以为 HTTP 请求「发出去就瞬间有结果」 | 建连 + TLS + 服务端处理都要时间 |
| 不设 timeout | 对端挂起时，你的线程 / 协程一直等 |
| 把 UDP 和 TCP 混为一谈 | HTTP/1.1、HTTP/2 走 TCP；HTTP/3 另说 |

#### 前端 fetch/axios 对照

| 概念 | 浏览器 / 前端 | Python |
| --- | --- | --- |
| 建连与 TLS | 浏览器连接池代劳 | `httpx`/`requests` 也会复用连接 |
| 超时 | `AbortSignal` / axios `timeout` | `timeout=` 参数 |
| DNS 失败 | `TypeError: Failed to fetch` 一类 | `ConnectError` / `gaierror` |
| 「感觉慢」 | DevTools Network 看 Waiting / Content Download | 日志打阶段耗时（DNS/连接/首字节/读完） |

---

### 2.2 连接、RTT、丢包：为何 Agent「偶发慢」

#### 为什么要单独讲？

LLM 调用本身就慢（秒到几十秒）。再叠一层网络抖动，若你没有超时与重试边界，用户会感觉「Agent 随机卡死」。

#### 怎么理解

- **RTT（Round-Trip Time）**：一来一回的时间。握手、TLS、小请求都会吃若干个 RTT。
- **丢包与重传**：TCP 保证可靠，但可靠不等于「立刻到」——丢了要等超时再传，表现为尖刺延迟。
- **队头阻塞（粗理解）**：同一条 TCP 连接上，前面的数据卡住，后面也可能等（HTTP/2 多路复用缓解应用层排队，但 TCP 层仍有限制；HTTP/3 另说）。

对 Agent 的直接含义：

```text
同机房 / 同区域 API  → RTT 小，失败更少
跨洋 Provider        → 固定延迟更高，超时要留余量
高峰限流 429         → 不是网络坏了，是配额/并发打满
网关 502/503/504     → 上游或中间层出问题，常可有限重试
```

#### 示例：把「慢」拆开看

```python
# 概念伪代码：排障时分段计时
# t_dns, t_connect, t_ttfb(首字节), t_total
# LLM 场景里 t_ttfb 到 t_total 往往占大头（模型生成）
```

不必一上来就上完整 APM；先在自己的 `LLMClient` 里打：

```python
import time


def timed_call(fn):
    t0 = time.perf_counter()
    try:
        return fn()
    finally:
        ms = (time.perf_counter() - t0) * 1000
        print(f"call took {ms:.0f} ms")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 超时设得比「正常生成时间」还短 | 正常慢请求被误杀，重试反而加倍烧 token |
| 超时设成「永不」或极大 | 真挂起时占满 worker / 线程 |
| 用一次失败断定「网络全挂」 | 可能是瞬时 503 / 单次丢包 |

#### 前端对照

浏览器里你看 Network 面板的 **Waiting (TTFB)** 与 **Content Download**；Agent 里同理：首 token 前在等服务端，流式阶段在持续读。

---

### 2.3 超时：任何 HTTP 客户端都应设置

#### 为什么需要超时？

对方进程崩溃、防火墙黑洞、网关半开——都可能导致「请求发出去，响应永不来」。没有超时，同步代码会占死线程；异步代码会占死并发名额。

#### 怎么写（概念）

```python
# 概念：任何 HTTP 客户端都应设 timeout
# httpx.Client(timeout=30.0)
# 更细：连接超时短、读超时按场景加长（LLM 常需要）
# httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0)
```

两个必须分清的概念：

| 概念 | 含义 | Agent 侧 |
| --- | --- | --- |
| **连接超时（connect）** | 多久内建连成功 | 网络/DNS 问题，可较短（几秒） |
| **读超时（read）** | 两次读数据之间最多等多久 | LLM 生成慢，要更长；流式也要留余量 |
| **客户端库超时** | 本地抛异常（如 `TimeoutException`） | **不会**变成 HTTP 408 |
| **HTTP 408** | 服务端等请求体超时（较少见） | 和你在客户端设的 timeout **不是一回事** |
| **HTTP 504** | 网关等上游超时 | 对端/上游太慢；常可有限重试 |

#### 跑一下（用 httpx 感受超时）

需已安装 `httpx`（见工程化模块）。`httpbin.org/delay/10` 会故意晚 10 秒再响应：

```python
import httpx

try:
    # 读超时 2 秒：几乎必触发
    r = httpx.get("https://httpbin.org/delay/10", timeout=httpx.Timeout(2.0))
    print(r.status_code)
except httpx.TimeoutException as e:
    print("timeout as expected:", type(e).__name__)
```

公司网络受限时，可用本地慢函数代替「外网 delay」，重点是：**超时以异常形式出现在客户端**。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只设「总超时」却不理解 connect/read | LLM 流式中途长时间无 chunk 被误杀，或建连失败等太久 |
| 把库超时当成 HTTP 408 | 日志和告警对不上，排障跑偏 |
| 并发很多请求都不设超时 | 故障时连接与线程被拖死 |

#### 前端 fetch/axios 对照

```javascript
// fetch：用 AbortController 模拟超时
const controller = new AbortController()
const timer = setTimeout(() => controller.abort(), 2000)
try {
  const res = await fetch("https://httpbin.org/delay/10", {
    signal: controller.signal,
  })
  console.log(res.status)
} catch (e) {
  console.log("aborted/timeout", e.name) // AbortError
} finally {
  clearTimeout(timer)
}
```

```javascript
// axios
await axios.get("https://httpbin.org/delay/10", { timeout: 2000 })
// 超时 → AxiosError，code 常为 ECONNABORTED
```

| 前端 | Python（httpx） |
| --- | --- |
| `AbortController` + `signal` | `timeout=` / `httpx.Timeout(...)` |
| axios `timeout: 2000` | `timeout=2.0`（单位秒） |
| 超时抛 JS 异常 | 超时抛 `TimeoutException` |
| 不会 magically 变成 HTTP 408 | 同样不会 |

---

## 3. 必掌握：HTTP 方法 / 状态码 / 头

### 3.1 方法

#### 为什么方法重要？

方法表达「意图」：读、写、改、删、触发动作。REST 与网关限流、缓存、幂等假设都和它有关。Chat Completions **几乎总是 POST**。

#### 怎么理解

| 方法 | 含义 | 常见用途 | 相对幂等？ |
| --- | --- | --- | --- |
| GET | 读取 | 查资源、健康检查 | 通常是（不应有副作用） |
| POST | 提交 / 创建 / 动作 | **Chat Completions 常用 POST**；建工单 | **不一定**（最要小心） |
| PUT | 整体替换更新 | REST 资源按 id 更新 | 协议上**应**幂等 |
| PATCH | 部分更新 | REST 局部字段 | 视实现 |
| DELETE | 删除 | REST 资源 | 理想情况重复删同一资源结果一致 |

补充：

- 「幂等」≈ 同一请求做多次，效果与做一次相同（不是「只能发一次」）。
- LLM 的 POST：协议层不保证幂等；业务上常可重试，但可能**重复扣 token**、重复触发工具副作用。

#### 跑一下（看方法如何体现在请求里）

```python
import json

# 构造「假」Chat Completions 请求——方法是 POST，body 是 JSON
request = {
    "method": "POST",
    "url": "https://api.example.com/v1/chat/completions",
    "headers": {
        "Authorization": "Bearer sk-xxx",
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    "body": {
        "model": "gpt-x",
        "messages": [{"role": "user", "content": "hi"}],
    },
}

print(request["method"])
print(json.dumps(request["body"], ensure_ascii=False))
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用 GET 传超长 / 敏感 body | 长度受限、易进日志与代理缓存 |
| 以为 POST「不能重试」或「一定能重试」 | 要看副作用；见第 5 节 |
| 把「创建资源」的 POST 和「查询」的 GET 搞反 | 缓存与安全中间件行为不符预期 |

#### 前端 fetch/axios 对照

```javascript
// fetch
await fetch("/v1/chat/completions", {
  method: "POST",
  headers: {
    Authorization: "Bearer sk-xxx",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "gpt-x",
    messages: [{ role: "user", content: "hi" }],
  }),
})
```

```javascript
// axios
await axios.post(
  "/v1/chat/completions",
  { model: "gpt-x", messages: [{ role: "user", content: "hi" }] },
  { headers: { Authorization: "Bearer sk-xxx" } },
)
```

| 前端 | Python |
| --- | --- |
| `method: "POST"` | `client.post(...)` / `requests.post` |
| `JSON.stringify(obj)` | `json=` 参数（库帮你序列化）或手写 `json.dumps` |
| axios 自动把对象当 JSON | `httpx` 的 `json=` 同理 |

---

### 3.2 状态码（先记这些）

#### 为什么要熟状态码？

状态码是「服务端用数字说话」。Agent 里第一反应往往是：修配置、改请求、退避重试，还是直接失败告警。

#### 怎么理解

| 码 | 含义 | Agent 里第一反应 |
| --- | --- | --- |
| 200 | 成功 | 解析 JSON，走正常路径 |
| 201 | 已创建 | REST 创建成功 |
| 400 | 请求坏了 | **别盲重试**；查参数 / schema |
| 401 | 未认证 | API Key / Bearer 问题；**别重试** |
| 403 | 无权限 | 权限不足；**别重试**（换凭证除外） |
| 404 | 没有 | 路径 / 资源 id 错 |
| 408 | 服务端等请求体超时 | 较少见；**≠** 客户端 `timeout` |
| 429 | 太多了 | **限流**；退避，尊重 `Retry-After` |
| 500 | 服务端内部错误 | 可重试与否看场景；有限次 |
| 502/503 | 坏网关 / 不可用 | 瞬时故障时常可退避重试 |
| 504 | 网关上游超时 | 对端/上游太慢；常可有限重试 |

口诀分层：

```text
2xx  → 成功族
4xx  → 你的请求/凭证/配额有问题（429 特殊：可退避）
5xx  → 对端或中间层出问题（常可有限重试）
```

客户端 `httpx`/`requests` 超时：通常是**本地抛异常**（如 `TimeoutException`），不会变成 HTTP 408。排障时把「库超时」和「网关 504」分开看。

#### 跑一下（不联网：自己映射决策）

```python
def first_reaction(status_code: int) -> str:
    if status_code == 200:
        return "parse_json"
    if status_code in {401, 403}:
        return "fix_credentials_no_retry"
    if status_code == 400:
        return "fix_request_no_retry"
    if status_code == 404:
        return "fix_path_or_id"
    if status_code == 429:
        return "backoff_respect_retry_after"
    if status_code in {500, 502, 503, 504}:
        return "limited_backoff_retry"
    return "inspect_manually"


for code in (200, 401, 429, 503):
    print(code, "→", first_reaction(code))
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 401/400 仍自动重试 | 无效燃烧配额与日志噪声 |
| 429 立刻连打 | 重试风暴，限流更久 |
| 只看 status，不看 body | 错误信息在 JSON `error.message` 里 |
| 把超时异常当成 504 | 监控分类错乱 |

#### 前端对照

```javascript
const res = await fetch(url)
if (res.status === 401) {
  // 跳登录 / 刷 token——不要无脑 retry 同一坏请求
}
if (res.status === 429) {
  const retryAfter = res.headers.get("Retry-After")
  // 等待后再试
}
```

axios 里常见：`error.response.status`；无响应时可能是网络/超时（`error.request` 有、`error.response` 无）。

---

### 3.3 常见头

#### 为什么头重要？

头承载鉴权、内容类型、限流提示、客户端身份。流式时 `Content-Type` 还会变成 `text/event-stream`。

#### 怎么理解 / 怎么写

```text
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
Retry-After: 30
User-Agent: my-agent/0.1
```

| 头 | 作用 |
| --- | --- |
| `Authorization` | 身份；Agent 里常见 `Bearer sk-...` |
| `Content-Type` | 请求体格式；JSON 就是 `application/json` |
| `Accept` | 期望的响应格式 |
| `Retry-After` | 限流/维护时建议等待秒数或日期 |
| `User-Agent` | 标识客户端；排障与风控有时会看 |

流式输出时还常见 `text/event-stream`（SSE）。后面 LLM API 章会详解解析；本章先建立「这是另一种 Content-Type」的地图。

#### 示例

```python
headers = {
    "Authorization": "Bearer sk-xxx",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "my-agent/0.1",
}

# 收到 429 时
retry_after = "30"  # 来自响应头
wait_s = int(retry_after)
print(f"wait {wait_s}s then retry")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 日志打印完整 `Authorization` | 密钥进日志 / 工单 / 监控，等于泄漏 |
| 忘了 `Content-Type` | 有的服务端解析失败 → 400 |
| 忽略 `Retry-After` | 自己拍脑袋 sleep，或立刻重打触发更严限流 |
| 把 SSE 当普通 JSON 一次 `response.json()` | 解析失败或只吃到第一截 |

#### 前端 fetch/axios 对照

```javascript
fetch(url, {
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
})
```

```javascript
axios.post(url, data, {
  headers: { Authorization: `Bearer ${token}` },
})
```

注意：浏览器里 `Authorization` 出现在前端代码 = 暴露给用户；**LLM Provider 的 sk- 密钥应放服务端**。Agent / 后端同理：密钥进环境变量，不进仓库、不进前端包。

---

## 4. 必掌握：JSON API

### 4.1 一次典型的请求 / 响应

#### 为什么 JSON API 是 Agent 的通用语言？

LLM Provider、自建 Tool、向量网关，绝大多数约定：**HTTP + JSON body + JSON 错误**。你会读写 dict、序列化、解析、再转异常——这条链每天都在走。

#### 怎么理解

典型请求：

```http
POST /v1/chat/completions HTTP/1.1
Host: api.example.com
Authorization: Bearer sk-xxx
Content-Type: application/json

{"model":"gpt-x","messages":[{"role":"user","content":"hi"}]}
```

典型成功响应：

```json
{"id":"...","choices":[{"message":{"role":"assistant","content":"hello"}}]}
```

典型错误响应也常是 JSON：

```json
{"error":{"message":"Rate limit","type":"rate_limit","code":429}}
```

要解析并转成你的领域异常（回顾异常章的「边界转译」）。

#### 怎么写（Python 侧心智）

```python
import json

payload = {"model": "gpt-x", "messages": [{"role": "user", "content": "hi"}]}
body = json.dumps(payload).encode("utf-8")  # 手写序列化时
# 更常见：让 httpx/requests 用 json=payload 代劳
# data = response.json()
```

更干净的写法：

```python
import json
from pathlib import Path

payload = {
    "model": "gpt-x",
    "messages": [{"role": "user", "content": "hi"}],
}

path = Path("fake_chat_request.json")
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

loaded = json.loads(path.read_text(encoding="utf-8"))
assert loaded["model"] == "gpt-x"
assert loaded["messages"][0]["role"] == "user"
print("ok", loaded["messages"][0]["content"])
```

#### 跑一下：解析错误响应并映射异常

```python
class RateLimitError(Exception):
    def __init__(self, message: str, code: int = 429) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def parse_error_payload(data: dict) -> tuple[int, str]:
    err = data.get("error") or {}
    code = int(err.get("code") or 0)
    message = str(err.get("message") or "unknown")
    return code, message


def raise_for_api_error(data: dict) -> None:
    code, message = parse_error_payload(data)
    if code == 429 or "rate limit" in message.lower():
        raise RateLimitError(message, code=code or 429)
    raise RuntimeError(f"api error {code}: {message}")


fake = {"error": {"message": "Rate limit", "type": "rate_limit", "code": 429}}
try:
    raise_for_api_error(fake)
except RateLimitError as e:
    print("caught", e.code, e.message)
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 不看 `Content-Type` 就 `response.json()` | HTML 错误页 / 纯文本 → `JSONDecodeError` |
| 成功路径只取 `content`，忽略错误包形状 | 空指针 / KeyError，日志难读 |
| 手写拼接 JSON 字符串 | 转义错误；用 `json.dumps` / `json=` |
| 把 `complete` 直接设计成返回 `str` | 与仓库约定冲突（见 `CONVENTIONS.md`：返回 assistant 消息 dict） |

#### 前端 fetch/axios 对照

```javascript
const res = await fetch(url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
})
const ct = res.headers.get("content-type") || ""
if (!ct.includes("application/json")) {
  throw new Error(`unexpected content-type: ${ct}`)
}
const data = await res.json()
```

```javascript
// axios：通常已自动 parse JSON
const { data, status } = await axios.post(url, payload)
```

| 前端 | Python |
| --- | --- |
| `JSON.stringify` / `res.json()` | `json.dumps` / `response.json()` |
| 先检查 `ok` / `status` | 先看 `status_code`，再决定 parse |
| axios 抛出带 `response.data` 的错 | 自己封装：`raise_for_status` + 解析 body |

---

### 4.2 用 httpx / requests 发真实 GET（可选联网）

#### 为什么要亲手打一枪？

书面状态码表不够；至少打通一次「客户端 → 公网 → 读 status」。公司网络受限就改用 mock，并注明。

#### 怎么写

```python
import httpx

with httpx.Client(timeout=10.0) as client:
    r = client.get("https://httpbin.org/get")
    print(r.status_code)
    print(r.json()["url"])
```

`requests` 版本：

```python
import requests

r = requests.get("https://httpbin.org/get", timeout=10.0)
print(r.status_code)
print(r.json()["url"])
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 每次请求新建客户端又从不关闭 | 连接泄漏（回顾 OS 章的 fd） |
| 忽略代理 / 公司 MITM | TLS 校验失败；需按环境配置而不是关校验 |
| 把演示用的公网 URL 写进生产 | 应用自己的 base_url 与超时政策 |

#### 前端对照

```javascript
const res = await fetch("https://httpbin.org/get")
console.log(res.status, await res.json())
```

```javascript
const { status, data } = await axios.get("https://httpbin.org/get", { timeout: 10000 })
console.log(status, data.url)
```

---

## 5. 建议掌握：HTTPS 与重试

### 5.1 HTTPS

#### 为什么需要 HTTPS？

= HTTP + TLS 加密与证书校验。保护令牌与对话内容不被明文窃听；校验证书降低中间人风险。

#### 怎么理解

```text
明文 HTTP：  链路途经节点可能看见 Authorization 与 body
HTTPS：      先 TLS，再在加密通道里跑 HTTP
证书校验：   确认「对面大致是我以为的那个域名」
```

实践原则：

- 生产只用 HTTPS 调 LLM / 支付 / 用户数据相关 API
- 证书错误时**不要**随手关掉校验（`verify=False`），除非本地调试且清楚风险
- 公司代理会换证书：应安装企业根证书，而不是关校验

#### 示例

```python
import httpx

# 默认 verify=True，保持即可
# httpx.get("https://example.com", timeout=10.0)

# 本地调试自签证书时，优先把 CA 配进信任库
# 而不是长期 verify=False
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 生产关 `verify` | 中间人可窃 token |
| 密钥放前端或打进镜像层 | 泄露面巨大 |
| 混用 http:// 与 https:// | 重定向、cookie、HSTS 行为混乱 |

#### 前端对照

浏览器地址栏锁标志、混合内容拦截——同一思想：敏感请求必须 TLS。前端 axios/fetch 调自己的后端 HTTPS；**Provider 密钥仍只留在服务端**。

---

### 5.2 幂等与重试

#### 为什么重试危险又必要？

网络与上游会抖：超时、429、502 很常见。完全不重试 → 可用性差；无脑重试 → 重复下单、重复扣费、重试风暴、双倍烧 token。

#### 怎么理解

| 操作 | 是否相对安全重试 |
| --- | --- |
| GET 查询 | 通常是 |
| PUT 幂等更新 | 协议上**应**幂等（实现须守约） |
| POST 创建订单 / 扣费 | **小心**，可能重复副作用 |
| LLM POST | 常可重试，但可能重复扣 token、重复产生副作用工具调用 |

原则：

- 只对**瞬时错误**重试（超时、429、502/503/504…）
- 用**指数退避 + 抖动**（jitter），避免雷同客户端同一时刻打爆
- 尊重 `Retry-After`
- 工具调用要有**幂等键**或「先查后做」
- 有限次数（例如 2～5 次），然后失败上抛

#### 怎么写：重试决策函数

```python
def should_retry(status_code: int, method: str) -> bool:
    """教学用决策：可按业务收紧。

    - 429/502/503/504：可重试
    - 400/401/403/404：不重试
    - POST：仅对瞬时类状态重试；若副作用不可接受，调用方应配合幂等键
    """
    method = method.upper()
    if status_code in {400, 401, 403, 404}:
        return False
    if status_code == 429 or status_code in {502, 503, 504}:
        return True
    if status_code >= 500:
        # 500 是否重试看场景；这里允许有限次
        return True
    if method == "GET" and status_code in {408}:
        return True
    return False


def backoff_seconds(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    """指数退避（未含抖动）；attempt 从 0 起。"""
    delay = min(cap, base * (2**attempt))
    return delay
```

带抖动的直觉（不必背公式）：

```python
import random


def backoff_with_jitter(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    delay = min(cap, base * (2**attempt))
    return delay * (0.5 + random.random())  # 0.5x～1.5x
```

#### 跑一下

```python
cases = [
    (401, "POST"),
    (429, "POST"),
    (503, "GET"),
    (400, "POST"),
]
for code, method in cases:
    print(code, method, "→", should_retry(code, method))

for i in range(4):
    print(i, "→ wait", round(backoff_seconds(i), 2), "s")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 429 仍疯狂重试 | 重试风暴，配额更惨 |
| POST 创建工单无幂等键就重试 | 重复创建 |
| 无限重试 | 故障放大，拖垮自己 |
| 所有实例同一 sleep 节奏 | 惊群，下一秒一起打爆 |

#### 前端对照

axios 拦截器里做重试时，同样要：

- 区分 401（去刷新 token 或登出）与 503（退避）
- 给写操作带幂等键（如 `Idempotency-Key` 头）
- 绝不为「修不好的 400」自动循环

```javascript
// 概念：axios 响应拦截器伪代码
if (error.response?.status === 429) {
  const ra = Number(error.response.headers["retry-after"] || 1)
  await sleep(ra * 1000)
  return axios.request(error.config) // 还须限制次数！
}
```

---

### 5.3 对接 LLM：HTTP 调用与超时重试（重点）

#### 为什么单独开一节？

后面 [`09-ai-llm`](../09-ai-llm/02-llm-api.md) 会讲 SDK / SSE；本章先把**传输层与政策**钉死，避免「会调 API 但不会设边界」。

仓库约定（见 [`CONVENTIONS.md`](../CONVENTIONS.md)）：业务侧偏好

```text
async def complete(messages, tools=None, **kwargs) -> dict  # assistant 消息
```

无 Key 时用 FakeLLM；CI 必须可在 Fake 下绿。这里用同步伪客户端讲清超时与重试即可。

#### 怎么理解：一次 LLM HTTP 调用的失败谱

```text
建连失败 / DNS          → 可有限重试（网络瞬时）
客户端读超时            → 可有限重试（小心已部分计费）
401/403                 → 不重试，修 Key
400（参数/上下文超限）   → 不重试；截断/改请求后再说
429                     → 退避 + Retry-After
5xx / 502/503/504       → 有限退避重试
业务成功但工具副作用    → HTTP 成功 ≠ 可随意重放整个 Agent 步
```

超时起点（合理起点，不是真理）：

| 场景 | connect | read | 说明 |
| --- | --- | --- | --- |
| 健康检查 GET | 2～5s | 5～10s | 快速失败 |
| 非流式 Chat | 5s | 60～120s | 模型慢；按 Provider 调 |
| 流式 Chat | 5s | 更长或「空闲超时」 | 关注 chunk 间隔 |
| 本地 FakeLLM | 极短 | 极短 | 单测要快 |

#### 怎么写：最小 `LLMClient` 骨架（同步教学版）

```python
from __future__ import annotations

import time
from typing import Any

import httpx


class LLMError(Exception):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: httpx.Timeout | float = httpx.Timeout(5.0, read=60.0),
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        """同步教学版：返回 assistant 消息 dict（简化 choices[0].message）。"""
        payload = {"messages": messages, **kwargs}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/v1/chat/completions"

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    r = client.post(url, headers=headers, json=payload)
                if r.status_code == 401:
                    raise LLMError("unauthorized", retryable=False)
                if r.status_code == 429 or r.status_code in {502, 503, 504}:
                    if attempt >= self.max_retries:
                        raise LLMError(f"upstream {r.status_code}", retryable=False)
                    ra = r.headers.get("Retry-After")
                    delay = float(ra) if ra and ra.isdigit() else backoff_with_jitter(attempt)
                    time.sleep(delay)
                    continue
                if r.status_code >= 400:
                    # 尝试取出错误信息；非 JSON 也不要炸成二次异常淹没现场
                    try:
                        detail = r.json()
                    except ValueError:
                        detail = r.text[:200]
                    raise LLMError(f"bad response {r.status_code}: {detail}", retryable=False)

                data = r.json()
                return data["choices"][0]["message"]
            except httpx.TimeoutException as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise LLMError("timeout", retryable=False) from e
                time.sleep(backoff_with_jitter(attempt))
            except httpx.TransportError as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise LLMError("transport", retryable=False) from e
                time.sleep(backoff_with_jitter(attempt))

        raise LLMError("exhausted", retryable=False) from last_exc
```

说明（刻意简化，别当生产真理）：

- 生产更常见 **复用** `Client` / `AsyncClient`，而不是每次 `with Client`
- 异步章会用 `await` + `asyncio.sleep`；超时可用 `asyncio.wait_for`
- FakeLLM：单测不走真 HTTP，但仍可测「429 → 退避 → 成功」状态机
- 工具调用副作用：在**工具层**做幂等键，不要假设「重放 complete」安全

#### 跑一下（Fake 状态机，不烧钱）

```python
def fake_should_retry_demo() -> None:
    sequence = [503, 429, 200]
    for i, code in enumerate(sequence):
        ok = should_retry(code, "POST") if code != 200 else False
        print(f"attempt {i}: status={code}, retry={ok}")
        if code == 200:
            print("assistant:", {"role": "assistant", "content": "hello"})
            return
        print("  sleep", round(backoff_seconds(i), 2), "s (demo, not actually sleeping)")


fake_should_retry_demo()
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 超时过短 + 自动重试 | 正常慢请求被杀两次，双倍计费 |
| 429 不看 `Retry-After` | 固定 50ms 重打，一直限流 |
| 日志打印完整 messages + Authorization | 隐私与密钥双泄漏 |
| 把 HTML 网关错误页当 JSON | 异常信息变成 `JSONDecodeError` |
| CI 依赖真网络真 Key | 流水线不稳定；用 FakeLLM |

#### 前端 fetch/axios 对照

浏览器前端**不应当**直持 Provider `sk-`。正确形态：

```text
浏览器 axios/fetch → 你的后端 /api/chat → 后端 httpx → Provider
```

| 点 | 前端 | Agent 后端 |
| --- | --- | --- |
| 密钥 | 只带用户会话 cookie / JWT | 服务端持有 Provider Key |
| 超时 | axios `timeout`；UX 要 loading / 取消 | connect/read 分离；与产品 SLA 对齐 |
| 重试 | 用户可点「重试」；写操作谨慎 | 自动有限退避 + 幂等 |
| 流式 | 读 SSE / fetch stream | `text/event-stream` 或 SDK stream |

---

### 5.4 幂等键：给「创建类」工具用

#### 为什么需要？

`should_retry` 对 POST 返回 True 时，若工具是「创建工单」，重试可能创建两张单。幂等键让服务端识别「这是同一意图的重复提交」。

#### 怎么理解（10 行方案级）

```text
1. 客户端生成 Idempotency-Key（UUID）
2. 随 POST 头或 body 传给 Tool API
3. 服务端对同一 key：返回同一结果，不第二次执行副作用
4. 重试时复用同一 key（不要每次新生成）
5. key 与「用户 + 动作意图」绑定，设合理 TTL
```

#### 示例

```python
import uuid

def new_idempotency_key() -> str:
    return str(uuid.uuid4())


key = new_idempotency_key()
headers = {
    "Authorization": "Bearer tool-token",
    "Content-Type": "application/json",
    "Idempotency-Key": key,  # 重试必须带着同一个 key
}
# POST /tickets  {"title": "..."}
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 每次重试都 `uuid4()` 新 key | 幂等失效，仍重复创建 |
| 只在客户端去重、服务端无记录 | 并发双飞仍可能双写 |
| 把幂等当「永不失败」 | 仍要处理超时：不知对面是否已成功 → 靠 key 查询 |

#### 前端对照

支付 / 下单前端同样传 `Idempotency-Key`；axios 重试拦截器必须从原 `config.headers` 取出同一 key。

---

## 6. 了解即可：HTTP/2 与 WebSocket

#### 为什么扫盲即可？

多数时候客户端与网关已自动协商 HTTP/2；你业务代码仍像在写 HTTP/1.1 语义。WebSocket / SSE 在「流式推给前端」时出现频率更高，细节放到 Web / LLM 章。

#### 怎么理解

| 技术 | 一句话 | Agent 里 |
| --- | --- | --- |
| **HTTP/2** | 多路复用，减少连接数与队头等待（应用层） | 很多客户端自动支持；你无感受益 |
| **HTTP/3 / QUIC** | 建在 UDP 上，弱网更稳（了解） | Provider / CDN 侧逐渐多见 |
| **WebSocket** | 全双工长连接，适合双向推送 | 前后端实时通道；工具环未必需要 |
| **SSE** | 服务端单向事件流（`text/event-stream`） | LLM 流式输出常见形态 |

流式三条路（先认路）：

```text
1) 非流式：一次 JSON 响应（最简单，好测）
2) SSE / HTTP stream：服务端持续推 delta
3) WebSocket：双向；前端打字中途可取消/续传等
```

#### 示例（SSE 长什么样——认形状即可）

```text
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: {"choices":[{"delta":{"content":"Hel"}}]}

data: {"choices":[{"delta":{"content":"lo"}}]}

data: [DONE]
```

Python 侧以后会用 `httpx` stream 或 SDK；本章只需知道：**别对 SSE 做一次 `response.json()`**。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 为了「上 HTTP/2」改一堆业务代码 | 通常无必要；交给客户端与服务器 |
| 用 WebSocket 重写一切 API | REST/JSON 仍是工具与 LLM 的主流 |
| 代理/老旧中间盒缓冲 SSE | 流式变「一整坨最后才到」；需关掉缓冲 |

#### 前端对照

| 前端 | 说明 |
| --- | --- |
| `new EventSource(url)` | 浏览器 SSE（常见仅 GET） |
| `fetch` + `ReadableStream` | 更灵活的流式 POST |
| `new WebSocket(url)` | 双向通道 |
| axios | 传统请求为主；流式常用 fetch/XHR 或专用封装 |

---

## 7. 常见坑

1. **没设 timeout**，线程 / worker 挂死  
2. **429 仍疯狂重试**，变成重试风暴  
3. **把 HTML 错误页当 JSON 解析**  
4. **日志打印完整 Authorization** 或整段用户对话  
5. **忽略代理 / 公司网络对 TLS 的影响**（乱关 `verify`）  
6. **连接超时与读超时不分**，LLM 场景误杀或空等  
7. **库超时 vs HTTP 408 vs 网关 504** 三者混为一谈  
8. **POST 创建类工具无幂等键就自动重试**  
9. **CI / 单测依赖真网真 Key**（应 FakeLLM + mock）  
10. **前端直持 Provider 密钥**

对照自检时可把上表当成 code review checklist。

---

## 8. 练习指引

按练习文档完成：状态码表、假 Chat 请求体、错误响应解析、timeout 政策；进阶写 `should_retry`，可选打公网 GET；挑战题设计创建类工具的幂等策略。

[`exercises/04-systems-basics/02-network-http.md`](../../exercises/04-systems-basics/02-network-http.md)

建议本地目录：`playground/04-systems-basics/02-network-http/`。

---

## 9. 小结与下一站

### 自检

- [ ] 能用分层 / RTT / 丢包解释超时为何必要、为何偶发变慢
- [ ] 见到 401/429/5xx 知道优先怀疑什么，以及是否可重试
- [ ] 能描述一次 JSON API 请求/响应，并安全解析错误包
- [ ] 能区分 HTTPS 证书校验、幂等、指数退避的基本边界
- [ ] 能为 LLM HTTP 调用给出合理的 connect/read 超时与有限重试政策
- [ ] 知道 HTTP/2、WebSocket、SSE 各自解决什么问题

### 下一章

[`03-concurrency-models.md`](./03-concurrency-models.md) —— 并发模型：线程/进程/异步怎么选（和「很多 HTTP 同时在飞」直接相关）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[操作系统基础](./01-os-basics.md)
- 下一章：[并发模型](./03-concurrency-models.md)
