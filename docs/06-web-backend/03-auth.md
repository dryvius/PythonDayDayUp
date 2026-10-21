# 认证与授权

> 所属模块：`06-web-backend` · Web 后端  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有前端登录/拦截器经验可更快；API Key + 401/403 + RBAC 建议动手踩一遍）  
> 对应练习：[`exercises/06-web-backend/03-auth.md`](../../exercises/06-web-backend/03-auth.md)

## 本章定位

- **模块目标**：能独立搭建并理解后端 API 服务。
- **本章角色**：让 API 知道「你是谁」以及「你能做什么」——Agent 服务上线最小安全底座。
- **原则**：先做对 API Key / 简单 Token；OAuth2 全流程先建立地图，不要一上来自己手写授权服务器。
- **你的优势**：前端天天碰「带 Token 调接口、401 跳登录」；这里补服务端如何验身份、如何裁权限，以及 Agent 工具场景下的最低安全清单。

## 学习目标（学完应能做到）

1. 严格区分认证（Authentication）与授权（Authorization），并正确使用 **401** / **403**。
2. 用 FastAPI `Depends` 实现基于 API Key 的接口保护；Key 来自环境变量，不进仓库。
3. 建立 Token / JWT 直觉：会用库签发与校验，懂载荷可见、必须过期、密钥强度等风险。
4. 了解 RBAC：用户 → 角色 → 权限；能设计角色权限表，并按权限码拦接口。
5. 对 OAuth2 建立「何时用、别手写」的地图；能背出 Agent 服务侧安全最低清单。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 认证 vs 授权、Token/JWT 直觉、API Key | 能保护自己的 API，分清 401/403 |
| **建议掌握** | RBAC 基础 | 能设计角色权限表，按权限码授权 |
| **了解即可** | OAuth2 完整流程 | 扫盲：知道场景与边界，不手写全套 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要认证与授权？

没有鉴权的 Agent API，等于把「会花钱、会改数据、能调工具」的能力挂在公网上：

```text
没有鉴权的 /v1/agent/run
  = 别人刷你的 LLM 额度
  = 会话 / 记忆 / 用户数据泄露
  = 工具被滥用（写文件、发邮件、调内部 API…）
```

Agent 比普通 CRUD 更危险：模型会「想」调工具，服务端若只认「有人能打到接口」而不认「这个人能不能用这个工具」，就会把高权限副作用暴露出去。

#### 本章要练的三种能力

1. **验身份**：请求里的 Key / Token 是否有效（认证）
2. **裁权限**：这个身份是否允许 `agent:run`、是否允许 `tool:shell`（授权）
3. **守底线**：密钥不进仓库、日志不泄密、危险工具默认关

可以先记一句：

> 先认证，再授权。登录成功 ≠ 什么都能干；Agent 工具尤其要按权限码单独放行。

#### 前端鉴权对照（先建立地图）

| 前端你已熟悉 | 本章 Python / 服务端视角 |
| --- | --- |
| 登录后把 Token 塞进 `localStorage` / Cookie | 签发 Token / 校验 Signature + `exp` |
| `axios` 拦截器加 `Authorization: Bearer ...` | 依赖注入读 Header，验 Key/JWT |
| 收到 `401` → 跳登录页 | `401` = 尚未建立有效身份 |
| 收到 `403` → 提示无权限 | `403` = 有身份但缺权限 |
| 路由守卫（有角色才进管理页） | RBAC：角色展开成权限集合再拦 |

---

## 2. 必掌握：认证 vs 授权

这一节会刻意写细——后面 API Key、JWT、RBAC 的所有状态码与依赖设计，都建立在这组区分上。

### 2.1 两个问题，不要混成一句「登录了」

#### 为什么要严格区分？

早期 demo 常写成「有 Token 就能调所有接口、用所有工具」。上线后你会发现：客服账号不该跑 `tool:shell`，只读账号不该 `agent:run`。若认证与授权糊成一团，改权限只能改「能不能登录」，无法按能力裁剪。

#### 怎么记（对照表）

| | 问题 | 英文 | 例子 |
|--|------|------|------|
| **认证** | 你是谁？ | Authentication | API Key 是否有效、用户名密码是否正确、JWT 签名与过期是否通过 |
| **授权** | 你能做什么？ | Authorization | 是否允许调用 `code_exec`、是否管理员、是否可读他人会话 |

顺序固定：

```text
请求进来
  → 认证：能否识别出「主体」（user / service / key）
       失败 → 401 Unauthorized
  → 授权：该主体是否拥有所需权限
       失败 → 403 Forbidden
  → 业务逻辑
```

口语里常把两者都叫「鉴权」；写代码与选状态码时，请拆开。

#### 跑一下（用状态码钉死直觉）

下面是「纯逻辑」小实验，不依赖 FastAPI，先把 401/403 的判定顺序跑通：

```python
def authenticate(api_key: str | None, expected: str) -> str | None:
    """成功返回 user_id；失败返回 None（对应 401）。"""
    if not api_key or api_key != expected:
        return None
    return "user_demo"


PERMISSIONS = {
    "user_demo": {"agent:read"},
    "user_admin": {"agent:read", "agent:run", "tool:shell"},
}


def authorize(user_id: str, needed: str) -> bool:
    """有身份后检查权限（失败对应 403）。"""
    return needed in PERMISSIONS.get(user_id, set())


def handle(api_key: str | None, needed: str, expected: str = "sk_demo") -> str:
    user_id = authenticate(api_key, expected)
    if user_id is None:
        return "401 Unauthorized"
    if not authorize(user_id, needed):
        return "403 Forbidden"
    return "200 OK"


print(handle(None, "agent:run"))              # 401
print(handle("wrong", "agent:run"))           # 401
print(handle("sk_demo", "agent:run"))         # 403（有身份，无权限）
print(handle("sk_demo", "agent:read"))        # 200
```

把 `PERMISSIONS["user_demo"]` 加上 `"agent:run"` 再跑一次，第三行应变 `200`——这就是「改授权、不改认证」。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 缺 Key 也返回 403 | 客户端误以为「已登录但没权限」，前端可能不跳登录 |
| 权限不足返回 401 | 前端清 Token 重登，用户被踢回登录页，其实只是缺权限 |
| 「登录了就能干所有事」 | Agent 工具面过大，一台服务被低权限账号打穿 |
| 把角色名当权限码硬编码进路由 | 角色一拆分就要改遍业务代码 |

#### 前端鉴权对照

| 场景 | 前端常见处理 | 后端应返回 |
| --- | --- | --- |
| 未带 Token / Token 无效 | 跳转登录、清本地凭证 | **401** |
| 已登录但不是管理员 | 提示「无权限」、隐藏按钮 | **403** |
| 路由 meta 要 `roles: ['admin']` | 导航守卫拦页面 | 接口侧仍要再验一遍（前端守卫可绕过） |

记住：前端隐藏按钮只是 UX；**真正的授权必须在服务端**。

### 2.2 401 与 403：和 Header 的关系

#### 为什么还要单独记状态码？

网关、监控、前端拦截器都按状态码分支。混用会导致「重登风暴」或「永远提示无权限」。

#### 怎么选

| 状态码 | 含义 | 典型原因 |
|--------|------|----------|
| **401** | 未认证 / 认证失败 | 缺 `X-API-Key`、Key 错、JWT 过期或签名失败 |
| **403** | 已认证但禁止 | 角色不够、权限码缺失、IP/租户策略拒绝 |
| **404** | 有时故意代替 403 | 隐藏资源是否存在（进阶；本章先分清 401/403） |

Bearer 场景下，401 响应常可带：

```http
WWW-Authenticate: Bearer
```

教学阶段可不强制；生产对接规范客户端时再补。

#### 跑一下（FastAPI 里抛错长什么样）

```python
from fastapi import FastAPI, Depends, Header, HTTPException, status

app = FastAPI()

EXPECTED = "sk_demo"
ALLOWED_RUN = {"admin"}


def get_user(x_api_key: str | None = Header(default=None)) -> dict:
    if not x_api_key or x_api_key != EXPECTED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key",
        )
    # 教学：用固定映射；真实项目查 DB
    return {"id": "u1", "role": "viewer"}


@app.post("/v1/agent/run")
def run_agent(user: dict = Depends(get_user)) -> dict:
    if user["role"] not in ALLOWED_RUN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="missing permission: agent:run",
        )
    return {"ok": True, "user": user["id"]}
```

用错误 Key 打 → 401；正确 Key 但 role 是 `viewer` → 403。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 业务里到处 `if not key: return {"error": ...}` 且仍 200 | 客户端当成功解析，排障极难 |
| 用 400 表达「没登录」 | 和参数校验混淆 |
| 只在网关验一次、业务服务互信后不再验 | 内网被打穿时无第二道门 |

#### 前端鉴权对照

```javascript
// axios 响应拦截器（概念）
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status
    if (status === 401) {
      // 清 Token，跳登录
    } else if (status === 403) {
      // 提示无权限，不要清 Token
    }
    return Promise.reject(err)
  },
)
```

后端把 401/403 用对，前端才能分支正确。

---

## 3. 必掌握：API Key（最实用起步）

Agent 服务、内部工具 API、服务间调用，最常见的第一道门就是 API Key。比完整登录链路简单，足够保护「别让陌生人刷你的 LLM」。

### 3.1 约定：客户端怎么带 Key

#### 为什么需要约定 Header？

没有统一位置，网关、日志脱敏、SDK 都会各写各的。业界常见两种：

```http
X-API-Key: sk_live_xxx
```

或：

```http
Authorization: Bearer sk_live_xxx
```

教学与内部服务任选一种并文档写死；对外 SDK 时优先跟生态习惯（很多 LLM Provider 用 `Authorization: Bearer`）。

#### 怎么写（服务端读取）

要点：

- Key **放环境变量**（如 `APP_API_KEY`），**不要**写进源码、**不要**提交进 Git
- 缺失或无效 → **401**
- **日志不要打印完整 Key**（最多前后各留几位做排障）

多用户时：维护 Key → `user_id`（或租户）映射表，而不是全局一个 Key（仍可比 OAuth 简单）。

本地开发示例（PowerShell）：

```powershell
$env:APP_API_KEY = "sk_dev_local_only"
# 然后启动 uvicorn；勿把真实生产 Key 写进 .env 再 git add
```

`.env` 若使用，确保已在 `.gitignore`；仓库里最多放 `.env.example`（只有变量名，无真实值）。

#### 跑一下（用 curl 感受「有/无 Key」）

假设服务已监听 `8000`，依赖要求 `X-API-Key`：

```bash
# 无 Key → 预期 401
curl -i -X POST http://127.0.0.1:8000/v1/agent/run ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"hi\"}"

# 有 Key → 进入业务（或后续 403）
curl -i -X POST http://127.0.0.1:8000/v1/agent/run ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: sk_dev_local_only" ^
  -d "{\"message\":\"hi\"}"
```

（Linux/macOS 把 `^` 换成 `\`。）

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把 Key 写进前端公开仓库 / 移动端包 | 任何人反编译或翻 Git 历史即可盗用 |
| 用「隐藏的 URL」当安全 | URL 会进日志、Referer、浏览器历史 |
| 日志打印完整 `Authorization` / `X-API-Key` | 日志系统变成密钥副本 |
| Key 提交进仓库后「改一版代码删掉」 | Git 历史仍在，必须轮换作废旧 Key |

#### 前端鉴权对照

| 场景 | 能不能把 API Key 放前端？ |
|------|---------------------------|
| 浏览器公开站点直接调你的付费 Agent API | **不能**——Key 会被看光 |
| 你的后端 BFF 再转发到 Agent 服务 | 可以：Key 只留在服务端环境变量 |
| 内部脚本 / CI / 服务间 | 可以：用环境变量或密钥管理，不进仓库 |

前端熟悉的「用户登录 Token」可以短时放浏览器（仍有 XSS 风险）；**服务级 API Key** 不要下发到公开前端。

### 3.2 FastAPI 依赖实现

#### 为什么用 `Depends`？

鉴权是横切逻辑：每个受保护路由都要验。写进每个函数会复制粘贴；做成依赖后，路由签名一眼能看出「需要 Key」，测试也可覆盖依赖。

#### 怎么写

```python
import os
from fastapi import Depends, Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    expected = os.getenv("APP_API_KEY")
    # 教学简化：用 != 比较（见下方「刻意简化」说明）
    if not expected or not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key",
        )
    return x_api_key


@app.post("/v1/agent/run")
async def run_agent(
    body: AgentRunRequest,
    _: str = Depends(require_api_key),
) -> AgentRunResponse:
    ...
```

也可读 `Authorization`：

```python
def require_bearer(authorization: str | None = Header(default=None)) -> str:
    expected = os.getenv("APP_API_KEY")
    if not expected or not authorization:
        raise HTTPException(status_code=401, detail="invalid api key")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != expected:
        raise HTTPException(status_code=401, detail="invalid api key")
    return token
```

#### 刻意简化：比较方式（务必读）

教学代码里 `x_api_key != expected` 足够建立流程直觉。

生产环境应考虑**恒定时间比较**，降低（在特定条件下）通过耗时侧信道猜 Key 的风险。见课程约定 [`CONVENTIONS.md`](../CONVENTIONS.md)「已知刻意简化」。

概念写法（了解即可，本章练习不强制）：

```python
import hmac


def api_key_equals(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided, expected)
```

注意：`compare_digest` 要求两边都是 `str`/`bytes` 且通常等长策略要一起设计；先把「Key 在环境变量 + 401 + 不进仓库」做对，再升级比较方式。

#### 跑一下（最小可运行片断）

把下面存成单文件（或放进你的 `app/main.py`），先 `set APP_API_KEY=sk_demo` 再启动：

```python
import os
from fastapi import Depends, FastAPI, Header, HTTPException, status

app = FastAPI(title="auth-demo")


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    expected = os.getenv("APP_API_KEY")
    if not expected or not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key",
        )
    return x_api_key


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}  # 健康检查通常不鉴权


@app.get("/v1/me")
def me(_: str = Depends(require_api_key)) -> dict[str, str]:
    return {"ok": "authenticated"}
```

```bash
uvicorn app.main:app --reload --port 8000
# 浏览器打开 /docs，对 /v1/me 点 Try it out，填 X-API-Key
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| `expected` 未配置时静默放行 | 生产忘配环境变量 = 裸奔 |
| 健康检查也强制 Key，却忘了给探针配 Key | K8s/负载均衡误杀实例 |
| 依赖里 `print(x_api_key)` | Key 进标准输出/日志聚合 |
| 全局一个 Key 却当「多租户隔离」 | 无法按用户审计与吊销 |

#### 前端鉴权对照

```javascript
// 浏览器：用户 Token（登录态）——可以走前端
await fetch("/v1/me", {
  headers: { Authorization: `Bearer ${userAccessToken}` },
})

// 浏览器：服务级 API Key——不要这样写进公开前端
// await fetch("/v1/agent/run", {
//   headers: { "X-API-Key": "sk_live_xxx" }, // 错误示范
// })
```

公开前端应调**你自己的后端**；由后端用环境变量里的 Key 再调 Agent / LLM。

### 3.3 多 Key / 查表（服务起步形态）

#### 为什么全局一个 Key 不够？

要吊销某个合作方、按用户限流、审计「谁在调」，就需要 Key → 主体 映射。

#### 怎么写（朴素版）

```python
# 教学：内存表。生产用 DB，且应存哈希而非明文 Key。
API_KEYS: dict[str, dict] = {
    "sk_alice": {"user_id": "alice", "roles": {"operator"}},
    "sk_bob": {"user_id": "bob", "roles": {"viewer"}},
}


def require_user(x_api_key: str | None = Header(default=None)) -> dict:
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="invalid api key")
    return API_KEYS[x_api_key]
```

生产要点（地图级，不必本章全实现）：

- 库里存 **Key 的哈希**（类似密码），请求来时哈希再比对
- 支持吊销、过期、按租户限流
- 轮换：先发新 Key，再作废旧 Key

#### 跑一下

```python
print(API_KEYS.get("sk_alice"))  # {'user_id': 'alice', 'roles': {'operator'}}
print(API_KEYS.get("sk_missing"))  # None → 业务里转 401
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 明文 Key 进数据库备份 | 备份泄露 = 全员失守 |
| 吊销只改文档不改校验表 | 「已作废」的 Key 仍能用 |
| 把这张表提交进仓库当「配置」 | 等同提交密钥 |

#### 前端鉴权对照

多租户 SaaS 前端通常只有**用户登录态**；服务级 Key 给合作方后端或 CLI，不进浏览器。管理页上的「创建/吊销 API Key」是管理员功能，对应后面的 `admin:keys` 权限。

---

## 4. 必掌握：Token / JWT 直觉

API Key 适合服务间与「一把钥匙开门」。面向终端用户时，更常见的是：登录一次，拿到 Token，之后请求带 Token。

### 4.1 Token 是什么

#### 为什么需要 Token？

总不能每个请求都传密码。登录成功后发一串令牌；之后请求带令牌证明「我仍是那个已认证主体」。

两种主流形态：

| 形态 | 直觉 | 优缺点（极简） |
|------|------|----------------|
| **服务端会话** | 服务端存 `session_id → user`，客户端只持 id | 易注销；要共享存储（多实例） |
| **自包含令牌（JWT）** | 令牌里带声明 + 签名，服务端可本地校验 | 易扩展；注销/强制下线不直观 |

本章建立 JWT 直觉；会话方案在持久化模块有存储后再深化。

#### 怎么写（概念）

```text
登录成功
  → 签发 token（含 sub、exp 等）
  → 客户端保存
后续请求
  → Authorization: Bearer <token>
  → 服务端验签 + 查过期 → 得到 user_id
  → 再做授权
```

#### 跑一下（不引入库的「会话版」对照）

```python
import secrets

SESSIONS: dict[str, str] = {}


def login(username: str, password: str) -> str:
    if username != "alice" or password != "correct":
        raise PermissionError("401")
    token = secrets.token_urlsafe(16)
    SESSIONS[token] = username
    return token


def current_user(token: str | None) -> str:
    if not token or token not in SESSIONS:
        raise PermissionError("401")
    return SESSIONS[token]


t = login("alice", "correct")
print(current_user(t))  # alice
SESSIONS.pop(t)         # 注销
try:
    current_user(t)
except PermissionError as e:
    print(e)  # 401
```

JWT 把「查 SESSIONS」换成「验签 + 读载荷」；注销就要另想办法（见下节）。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| Token 永不过期 | 泄露后长期可冒用 |
| 把密码放进 Token | 载荷可被看见或落日志 |
| 只靠前端「有 Token 就当已登录」 | 伪造字符串也能骗过纯前端守卫 |

#### 前端鉴权对照

| 前端 | 后端 |
|------|------|
| 登录接口拿 `access_token` | 校验账号密码后签发 |
| `Authorization: Bearer ...` | 解析并验签 |
| 401 → 清本地 Token | 过期/无效时返回 401 |
| 刷新令牌轮换（进阶） | 短 `access` + 长 `refresh`（地图） |

### 4.2 JWT 结构直觉

#### 为什么要懂三段式？

不会「拆开看」时，容易误以为 JWT 是加密的，把秘密塞进载荷。

结构：

```text
header.payload.signature
  ↑       ↑        ↑
 JSON    JSON    用密钥对前两段签名
 Base64URL 编码（可解码，不是保密）
```

常见载荷字段：

| 字段 | 含义 |
|------|------|
| `sub` | subject，通常是用户 id |
| `exp` | 过期时间（Unix 时间戳）——**一定要有** |
| `iat` | 签发时间 |
| `roles` / `permissions` | 可选；太大或变更频繁时不如服务端再查 |

#### 怎么写（概念示意）

学习阶段：会用库签发/校验即可（如 `PyJWT`），理解字段含义。下面是概念示意，**非完整生产代码**：

```python
# 概念示意，非完整生产代码
# import jwt
# from datetime import datetime, timedelta, timezone
#
# SECRET = os.environ["JWT_SECRET"]  # 够长、够随机；勿提交仓库
# payload = {
#     "sub": "user_1",
#     "exp": datetime.now(timezone.utc) + timedelta(hours=1),
# }
# token = jwt.encode(payload, SECRET, algorithm="HS256")
# decoded = jwt.decode(token, SECRET, algorithms=["HS256"])
```

校验时务必：

- 显式传入允许的 `algorithms`（不要随意接受 `none`）
- 检查 `exp`（库通常默认检查，别关掉）
- 密钥够强，并有轮换策略

#### 跑一下（不装库也能「看见」载荷）

JWT 载荷默认可被解码看见——用标准库拆一段教学用假 Token 的中间段（无需验签）：

```python
import base64
import json


def b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad)


# 仅演示「中间段可解码」；这不是合法可验签的生产 Token
fake_payload = base64.urlsafe_b64encode(
    json.dumps({"sub": "user_1", "exp": 1900000000}).encode()
).decode().rstrip("=")
print(json.loads(b64url_decode(fake_payload)))
# {'sub': 'user_1', 'exp': 1900000000}
```

结论：**JWT 不是加密**。别塞密码、API Key、身份证号等敏感明文。

#### 风险与注意（必掌握）

- 一定要 `exp`
- 密钥要够强、要轮换策略；密钥进仓库 = 任何人可伪造 Token
- 注销 / 强制下线对纯 JWT 不直观（常需黑名单，或短有效期 + 刷新令牌）
- 算法不要随意接受 `none`；校验时白名单算法
- 载荷可见 ≠ 可篡改：改完载荷后签名对不上，校验应失败

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| JWT 永不过期 | 泄露窗口无限大 |
| 用弱密钥或默认 `secret` | 暴力/猜测后可伪造任意用户 |
| 把 JWT 当加密通道 | 隐私进载荷被解码 |
| 「退出登录」只清前端 | 旧 JWT 在过期前仍可用（除非黑名单/短 TTL） |

#### 前端鉴权对照

```javascript
// 前端常把 access_token 放内存或会话存储；注意 XSS
// 解码 payload（仅调试用，不能当验签）
function peekJwtPayload(token) {
  const mid = token.split(".")[1]
  const json = atob(mid.replace(/-/g, "+").replace(/_/g, "/"))
  return JSON.parse(json)
}
```

前端 `peek` 只能做 UX（如显示用户名、临过期提示）；**是否放行接口由后端验签决定**。

### 4.3 和 API Key 怎么选（决策地图）

| 场景 | 更合适 |
|------|--------|
| 服务间调用、CI、内部 Worker | API Key |
| 终端用户登录、多人多角色 | Token / JWT（或会话） |
| 第三方「代用户访问」 | OAuth2（见第 6 节） |
| 本地脚本调自己的 Agent API | API Key 最省事 |

可以并存：用户用 JWT 调你的 API；你的 API 再用 API Key 调上游 LLM。

---

## 5. 建议掌握：RBAC 基础

Role-Based Access Control：用「角色」给权限分组，避免给每个用户逐条堆权限。

### 5.1 模型：用户 → 角色 → 权限

#### 为什么需要 RBAC？

Agent 场景权限膨胀很快：`agent:run`、`agent:read`、`tool:search`、`tool:shell`、`admin:keys`…  
若每个用户直接绑几十个权限码，运营与审计都会崩。角色是中间层：

```text
用户 → 角色 → 权限
alice → admin → agent:run, tool:* , admin:keys
bob   → viewer → agent:read
```

#### 怎么记（权限表示例）

| 权限码 | 含义 |
|--------|------|
| `agent:run` | 可调用运行接口 |
| `agent:read` | 可读会话/结果 |
| `tool:search` | 可使用搜索工具 |
| `tool:shell` | 高风险，**默认不给** |
| `admin:keys` | 管理 API Key |

实现可以很朴素：先有角色，再展开成权限集合。

重要区分：

> **角色名 ≠ 权限码**。  
> 检查「能不能跑 Agent」应看 `agent:run`，而不是只看字符串 `"admin"`（除非你明确写的是 `require_role`）。

#### 怎么写

```python
ROLE_PERMISSIONS = {
    "admin": {"agent:run", "agent:read", "tool:*", "admin:keys"},
    "operator": {"agent:run", "agent:read", "tool:search"},
    "viewer": {"agent:read"},
}


class User:
    def __init__(self, id: str, roles: set[str]):
        self.id = id
        self.roles = roles

    @property
    def permissions(self) -> set[str]:
        perms: set[str] = set()
        for role in self.roles:
            perms |= ROLE_PERMISSIONS.get(role, set())
        return perms


def get_current_user() -> User:
    # 真实项目：从 API Key / JWT 解析后查库
    return User(id="bob", roles={"viewer"})


def has_permission(user: User, needed: str) -> bool:
    perms = user.permissions
    if needed in perms:
        return True
    # 示例：tool:* 覆盖 tool:search / tool:shell（生产可换成更严的匹配）
    category, _, _ = needed.partition(":")
    return f"{category}:*" in perms


def require_permission(perm: str):
    def dep(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user, perm):
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return dep


# 若只检查角色名，应写成 require_role("admin")
# 不要把 "agent:run" 当角色名去比
```

#### 跑一下

```python
alice = User("alice", {"admin"})
bob = User("bob", {"viewer"})

print("alice agent:run", "agent:run" in alice.permissions)  # True
print("bob agent:run", "agent:run" in bob.permissions)      # False
print("bob agent:read", "agent:read" in bob.permissions)    # True
```

把 bob 的角色改成 `{"operator"}`，再看 `agent:run` 与 `tool:shell`：前者应 True，后者仍 False——这就是「按权限码裁剪工具面」。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 认证通过就授权所有工具 | `tool:shell` 被低权限用户触发 |
| 只在前端按角色隐藏菜单 | 直接调 API 仍能打穿 |
| 角色名与权限码混用 | `require_permission("admin")` 永远对不上表 |
| 权限数据只活在 JWT 里且长期不失效 | 降权后旧 Token 仍带着高权限声明 |

#### 前端鉴权对照

| 前端 | 后端 |
|------|------|
| 按钮 `v-if="can('agent:run')"` | 接口 `Depends(require_permission("agent:run"))` |
| 路由 `meta.roles = ['admin']` | 仍以权限码或服务端角色二次校验为准 |
| 从 `/v1/me` 拉 `permissions[]` 渲染菜单 | `/v1/me` 本身也要认证 |

前端 `can()` 只影响展示；后端 `require_permission` 才是执法点。

### 5.2 Agent 工具授权（和模块 12 的衔接）

#### 为什么接口级 RBAC 还不够？

即使用户有 `agent:run`，也不自动等于能跑所有工具。模型可能发起 `tool:shell`；服务端要在**执行工具前**再检一次权限（模块 12 会系统讲参数级 ACL）。

#### 怎么写（最小形状）

```python
TOOL_PERMISSION = {
    "search": "tool:search",
    "shell": "tool:shell",
}


def authorize_tool(user: User, tool_name: str) -> None:
    needed = TOOL_PERMISSION.get(tool_name)
    if needed is None:
        raise HTTPException(status_code=403, detail=f"unknown tool: {tool_name}")
    if not has_permission(user, needed):
        raise HTTPException(status_code=403, detail=f"missing {needed}")
```

#### 跑一下

```python
bob = User("bob", {"viewer"})
try:
    authorize_tool(bob, "shell")
except HTTPException as e:
    print(e.status_code, e.detail)  # 403 missing tool:shell
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 只校验「能否打 `/v1/agent/run`」 | 运行后工具面无二次门禁 |
| 信任模型「自己不会乱调」 | 提示注入可诱导调危险工具 |

#### 前端鉴权对照

管理控制台可以展示「当前角色可用工具」；真正拦截发生在 Agent 运行时后端，而不是前端表单。

---

## 6. 了解即可：OAuth2 预告

用于「让用户用 Google/GitHub 登录」或「第三方应用代用户访问资源」。完整流程含授权码、刷新令牌、scopes 等——本章只建立地图，**不要一上来自己手写全套 OAuth 服务器**。

### 6.1 什么时候会碰到 OAuth2

#### 为什么现在只扫盲？

Agent 产品后期常见需求：

- 「用公司 Google 账号登录控制台」
- 「让 Slack/飞书应用代用户读日历」
- 「第三方插件以有限 scope 调你的 API」

这些正是 OAuth2 / OIDC 的主场。自己从零实现授权服务器成本高、易踩坑；优先用成熟托管或框架集成。

#### 怎么记（和 API Key 对照）

| | API Key | OAuth2 |
|--|---------|--------|
| 典型主体 | 服务 / 脚本 / 合作方系统 | 终端用户 + 第三方应用 |
| 用户体验 | 复制一串 Key | 「用 Google 登录」跳转同意页 |
| 权限表达 | 自建权限码 / 角色 | scope（如 `read:email`） |
| 本章要求 | **必掌握实现** | **了解场景与边界** |

本阶段只需记住：

- **API Key** 适合服务间调用
- **OAuth2** 适合面向终端用户的委托授权
- 不要一上来自己手写全套 OAuth 服务器

#### 跑一下（只跑「脑内流程」，不写代码）

授权码模式（最常见）心智图：

```text
浏览器 → 你的前端
  → 跳转授权服务器（Google 等）登录并同意 scopes
  → 带回 authorization code（短时、一次性）
  → 你的后端用 code + client_secret 换 token
  → 之后用 access_token 调资源服务器
```

`client_secret` **只放后端**，与「API Key 不放公开前端」是同一条纪律。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 在公开前端写死 `client_secret` | 任何人都能冒充你的应用 |
| 以为「接了 OAuth 就不用自己的授权」 | OAuth 解决的是身份/委托；业务权限仍要 RBAC |
| 课程阶段就自建完整授权服务器 | 时间全耗在协议边角，Agent 主线停滞 |

#### 前端鉴权对照

| 前端常见 | 含义 |
|----------|------|
| 跳转 `/oauth/authorize?...` | 用户去 IdP 登录 |
| 回调页带 `?code=` | 交给**后端**换 token，前端尽量不碰 secret |
| 之后仍是 `Authorization: Bearer <access_token>` | 与 JWT/会话在传输层长得像 |

OIDC 在 OAuth2 之上多了「身份层」（`id_token`）；听到「Google 登录」时，多半是 OIDC。了解即可。

---

## 7. Agent 安全最低清单（本章视角）

模块 12 会系统化讲提示注入、沙箱与参数级 ACL。本章先落下「服务一对外就能检查」的最低清单。

### 7.1 五条底线

#### 为什么是「最低」而不是「完整安全」？

没有认证的 Agent API 会先死在刷额度和工具滥用上；先把门安上，再谈注入与沙箱。

#### 怎么执行（清单）

1. **所有会花钱 / 会改数据的接口要认证**  
   `/v1/agent/run`、写会话、管理 Key——至少 API Key 或用户 Token。
2. **危险工具默认关闭或强授权**  
   `shell` / `code_exec` / 发信 / 付款：默认拒绝；显式权限 + 审计。
3. **按用户做配额与限流（可后置，但要进地图）**  
   防止单一 Key 把预算打爆；可先做简单位窗计数。
4. **密钥轮换与泄露应急**  
   怀疑泄露 → 立刻作废旧 Key / 轮换 JWT 密钥；检查 Git 历史与日志。
5. **提示注入与工具滥用**  
   → 模块 12 安全章再系统化；本章至少做到「工具执行前查权限码」。

#### 跑一下（把清单变成自检表）

对着你正在写的服务逐项打勾：

```text
[ ] /v1/agent/run 有 Depends 鉴权
[ ] 无 Key 时返回 401（不是 200 + error 字符串）
[ ] APP_API_KEY / JWT_SECRET 只在环境变量
[ ] 仓库里没有 sk_live_ / 真实密码
[ ] tool:shell 默认不在 viewer/operator 权限里
[ ] 日志脱敏：不打印完整 Token / Key
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 「内网就不用鉴权」 | 内网横向移动后直接打到 Agent |
| 只认证网关，工具执行路径信任模型输出 | 注入成功即高权限副作用 |
| 泄露后只删代码不轮换 Key | 旧 Key 仍可用 |

#### 前端鉴权对照

| 清单项 | 前端侧配合 |
|--------|------------|
| 接口要认证 | 请求带用户 Token；服务 Key 走 BFF |
| 危险工具 | UI 可二次确认，但以后端拒绝为准 |
| 泄露应急 | 清本地存储、强制重新登录 |

### 7.2 和「常见坑」的衔接

下一节把清单展开成具体坑位；自检时两节一起扫。

---

## 8. 常见坑

把全章易错点收成排障清单（写代码前扫一眼）：

1. **前端把 Key 写进公开仓库 / 移动端包**  
   服务级密钥只留服务端；仓库用 `.env.example` 占位，真实值本地或密钥管理注入。
2. **只用「隐藏 URL」当安全**  
   安全靠认证与授权，不靠路径冷门。
3. **CORS 配错**  
   浏览器不允许 `Allow-Origin: *` 与 `Allow-Credentials: true` 同用；真坑是**反射任意 Origin + 带凭证**（等于谁都能带着 Cookie 打你的 API）。
4. **JWT 永不过期**  
   必有 `exp`；敏感操作配短 TTL。
5. **认证通过就授权所有工具**  
   分权限码；危险工具默认关。
6. **401 / 403 用反**  
   没身份 → 401；有身份没权限 → 403。
7. **教学用 `!=` 比较直接搬进生产**  
   见 [`CONVENTIONS.md`](../CONVENTIONS.md)：生产宜考虑恒定时间比较（如 `hmac.compare_digest`）。
8. **密钥进 Git 后以为「删文件就安全」**  
   必须轮换；历史里仍有旧值。

---

## 9. 练习指引

按练习文档动手，优先顺序：

1. 给 `/v1/agent/run`（或等价接口）加上 API Key 依赖  
2. 用错误 Key / 正确 Key 分别打出 401 与 200  
3. 再加一层权限：viewer 读、operator 跑；打出 403  
4. （可选）签发一枚带 `exp` 的 JWT 并校验  

练习入口：[`exercises/06-web-backend/03-auth.md`](../../exercises/06-web-backend/03-auth.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能区分认证与授权，以及 **401** 与 **403**
- [ ] 能给 FastAPI 加上 API Key 依赖；Key 来自环境变量且不进仓库
- [ ] 知道教学用 `!=` 与生产恒定时间比较的差别（见约定）
- [ ] 知道 JWT 装什么、不装什么；必有 `exp`
- [ ] 能画出用户 → 角色 → 权限，并按权限码拦接口 / 工具
- [ ] 知道 OAuth2 用在什么场景，以及为何现阶段不手写全套
- [ ] 能背出 Agent 安全最低清单五条

### 可以带走的句子

> 认证回答「你是谁」，授权回答「你能做什么」。  
> API Key 先把门关上；RBAC 再把工具面裁小。  
> JWT 可被看见、必须能过期；密钥永不进仓库。

### 模块 06 收官

下一模块：[`../07-data-persistence/README.md`](../07-data-persistence/README.md) —— 数据库与持久化（会话、记忆、任务状态、以及「Key/用户/角色」真表都靠它）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[FastAPI + Pydantic](./02-fastapi-pydantic.md)
- 下一模块：[数据库与数据持久化](../07-data-persistence/README.md)
