# 认证与授权

> 所属模块：`06-web-backend` · Web 后端  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/06-web-backend/03-auth.md`](../../exercises/06-web-backend/03-auth.md)

## 本章定位

- **本章角色**：让 API 知道「你是谁」以及「你能做什么」——Agent 服务上线最小安全底座。
- **原则**：先做对 API Key / 简单 Token；OAuth2 全流程先建立地图。

## 学习目标

1. 严格区分认证（Authentication）与授权（Authorization）。
2. 实现基于 API Key 的接口保护。
3. 建立 Token / JWT 直觉（会用、懂风险）。
4. 了解 RBAC；OAuth2 知道用在什么场景。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 认证 vs 授权、Token/JWT 直觉、API Key | 能保护自己的 API |
| **建议掌握** | RBAC 基础 | 能设计角色权限表 |
| **了解即可** | OAuth2 完整流程 | 扫盲 |

---

## 1. 为什么要学

```text
没有鉴权的 /v1/agent/run
  = 别人刷你的 LLM 额度
  = 数据泄露
  = 工具被滥用（写文件、发邮件…）
```

Agent 工具权限尤其危险：等于把能力接口暴露在公网。

---

## 2. 必掌握：认证 vs 授权

| | 问题 | 例子 |
|--|------|------|
| **认证 Authentication** | 你是谁？ | API Key 是否有效、用户登录是否成功 |
| **授权 Authorization** | 你能做什么？ | 是否允许调用 `code_exec` 工具、是否管理员 |

先认证，再授权。不要混成一个模糊的“登录了就能干所有事”（早期 demo 可以，生产不行）。

---

## 3. 必掌握：API Key（最实用起步）

### 3.1 约定

客户端带：

```http
X-API-Key: sk_live_xxx
```

或：

```http
Authorization: Bearer sk_live_xxx
```

### 3.2 FastAPI 依赖实现

```python
import os
from fastapi import Depends, Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    expected = os.getenv("APP_API_KEY")
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

要点：

- Key 放环境变量
- 缺失/无效 Key → **401**（尚未建立有效身份）；有身份但缺权限 → **403**
- **日志不要打印完整 Key**

多用户时：Key → user_id 映射表，而不是全局一个 Key（仍可比 OAuth 简单）。

---

## 4. 必掌握：Token / JWT 直觉

### 4.1 Token

登录成功后发一串令牌；之后请求带令牌证明身份。  
服务端可存会话（server-side session）或用自包含令牌（JWT）。

### 4.2 JWT（JSON Web Token）

结构直觉：`header.payload.signature`

- 载荷里可有 `sub`（用户 id）、`exp`（过期）
- 用密钥签名，服务端可校验未被篡改
- **JWT 不是加密**：载荷默认可被解码看见 → 别塞密码/密钥

风险与注意：

- 一定要 `exp`
- 密钥要够强、要轮换策略
- 注销/强制下线对纯 JWT 不直观（常需黑名单或短有效期+刷新令牌）
- 算法不要随意接受 `none`

学习阶段：会用库签发/校验即可（如 `PyJWT`），理解字段含义。

```python
# 概念示意，非完整生产代码
# payload = {"sub": "user_1", "exp": ...}
# token = jwt.encode(payload, SECRET, algorithm="HS256")
```

---

## 5. 建议掌握：RBAC 基础

Role-Based Access Control：

```text
用户 → 角色 → 权限
alice → admin → agent:run, tool:* 
bob   → viewer → agent:read
```

Agent 场景权限例子：

| 权限 | 含义 |
|------|------|
| `agent:run` | 可调用运行接口 |
| `tool:search` | 可使用搜索工具 |
| `tool:shell` | 高风险，默认不给 |
| `admin:keys` | 管理 API Key |

实现可以很朴素：先有角色，再展开成权限集合（**角色名 ≠ 权限码**）。

```python
ROLE_PERMISSIONS = {
    "admin": {"agent:run", "tool:*", "admin:keys"},
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


def require_permission(perm: str):
    def dep(user: User = Depends(get_current_user)) -> User:
        if perm not in user.permissions:
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return dep


# 若只检查角色名，应写成 require_role("admin")，不要把 "agent:run" 当角色
```

401 = 没身份；403 = 有身份但没权限。  
API Key 用 `!=` 比较见 [`CONVENTIONS.md`](../CONVENTIONS.md) 刻意简化（生产宜恒定时间比较）。

---

## 6. 了解即可：OAuth2

用于「让用户用 Google/GitHub 登录」或「第三方应用代用户访问资源」。  
完整流程含授权码、刷新令牌、scopes 等。

Agent 产品后期常会碰到；本阶段：

- 知道 **API Key** 适合服务间调用
- 知道 **OAuth2** 适合面向终端用户的委托授权
- 不要一上来自己手写全套 OAuth 服务器

---

## 7. Agent 安全最低清单（本章视角）

1. 所有会花钱/会改数据的接口要认证  
2. 危险工具默认关闭或强授权  
3. 按用户做配额与限流（可后置）  
4. 密钥轮换与泄露应急（作废旧 Key）  
5. 提示注入与工具滥用 → 模块 12 安全章再系统化  

---

## 8. 常见坑

1. 前端把 Key 写进公开仓库 / 移动端包  
2. 只用「隐藏 URL」当安全  
3. CORS：浏览器不允许 `Allow-Origin: *` 与 `Allow-Credentials: true` 同用；真坑是**反射任意 Origin + 带凭证**  
4. JWT 永不过期  
5. 认证通过就授权所有工具  

---

## 9. 练习指引

[`exercises/06-web-backend/03-auth.md`](../../exercises/06-web-backend/03-auth.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能区分 401 与 403、认证与授权
- [ ] 能给 FastAPI 加上 API Key 依赖
- [ ] 知道 JWT 装什么、不装什么

### 模块 06 收官

下一模块：[`../07-data-persistence/README.md`](../07-data-persistence/README.md) —— 数据库与持久化（会话、记忆、任务状态都靠它）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[FastAPI + Pydantic](./02-fastapi-pydantic.md)
- 下一模块：[数据库与数据持久化](../07-data-persistence/README.md)
