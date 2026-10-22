# 练习：认证与授权

> 对应文档：[`docs/06-web-backend/03-auth.md`](../../docs/06-web-backend/03-auth.md)  
> 状态：`已完成出题`  
> 建议用时：70～110 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录（可承接上一章 FastAPI 项目）：

```text
playground/06-web-backend/03-auth/
```

4. Python ≥ 3.11；测试优先 `TestClient`。
5. **刻意简化（必须写进笔记/注释）**——见 `docs/CONVENTIONS.md`：
   - 教学用 API Key 的 `!=` / `==` 比较 **≠** 生产级做法
   - 生产应考虑**恒定时间比较**（如 `hmac.compare_digest`），降低粗粒度计时侧信道风险
   - 本课为可读性可用 `!=`，但必须能口述差异

---

## 热身题（建议先做）

### W1. 认证 vs 授权（一句话）

**要求**：各用一句话定义「认证」「授权」。

**验收**：认证 ≈ 你是谁；授权 ≈ 你能做什么。

---

### W2. 401 / 403 填空

**要求**：下列场景选 401 或 403：

1. 没带 API Key  
2. Key 正确但角色不是 admin，却打了删除缓存接口  
3. Key 格式对但值错误  

**验收**：1→401；2→403；3→401。

---

### W3. Header 名称

**要求**：写出本课示例将使用的请求头名称（推荐 `X-API-Key`），并说明为何不要把 Key 放进 URL query。

**验收**：提到日志、浏览器历史、分享链接泄露风险之一。

---

### W4. 环境变量读取

**要求**：写 3 行代码：从环境变量 `APP_API_KEY` 读取密钥；未设置时得到 `None` 或抛明确错误（二选一，需注释说明）。

**验收**：不把真实密钥写进源码。

---

## 基础题（必做）

### B1. 概念题（书面）

各举 **一例**（结合 Agent API 场景）：

1. 认证失败 → 你返回 **401**  
2. 授权失败 → 你返回 **403**

每例写：请求大概长什么样、服务端拒绝原因一句话。

**验收**：两例不能都写成「没登录」。

---

### B2. API Key 依赖保护 `/v1/agent/run`

实现：

```python
async def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    ...
```

保护 `POST /v1/agent/run`（可用 Echo/假 Agent）。

规则：

1. 无 Header / 空字符串 → 401  
2. 与环境变量 `APP_API_KEY`（或 Settings）不一致 → 401  
3. 一致 → 进入业务，200  

**教学比较写法**（允许）：

```python
if x_api_key != expected:
    raise HTTPException(status_code=401, detail="invalid api key")
```

**必须在代码注释写明**：

```text
# 教学简化：!= 比较。生产应考虑 hmac.compare_digest 等恒定时间比较。
```

**验收**：TestClient 覆盖无 Key / 错 Key / 对 Key 三条路径。

---

### B3. 日志安全清单（书面）

列出至少 **3 类**绝对不该打进普通应用日志的字段/内容，并各给一句理由。

提示方向：API Key、Authorization、Cookie、完整 prompt/messages、用户隐私字段等。

**验收**：至少 3 项；理由能连到「泄露面 / 合规 / 密钥轮转」之一。

---

### B4. JWT 直觉（书面）

回答：

1. JWT payload 为什么不该放 `password` 或长期 `api_key`？  
2. `exp` 字段有何用？没有 `exp` 的风险是什么？  
3. 「JWT 已签名」是否等于「payload 内容保密」？为什么？

**验收**：第 3 问必须点出「默认可被解码阅读；签名防篡改 ≠ 加密保密」。

---

## 进阶题（建议至少做 1 题）

### A1. 多 Key 映射用户

内存表：

```python
API_KEYS: dict[str, str] = {
    "k-alice": "alice",
    "k-bob": "bob",
}
```

`require_api_key`（或改名 `require_user`）校验通过后返回 `user_id: str`。  
`POST /v1/agent/run` 响应中带回 `user_id`（演示用）。

**验收**：alice/bob 的 Key 各跑通；未知 Key → 401。

---

### A2. RBAC 雏形

在 A1 基础上增加角色：

```python
ROLES: dict[str, set[str]] = {
    "alice": {"admin", "user"},
    "bob": {"user"},
}
```

实现：

```python
def require_role(role: str):
    ...
```

保护 `DELETE /admin/cache`：仅 `admin` 可访问。

**验收**：

- alice → 204/200  
- bob（合法 Key）→ **403**（不是 401）  
- 无 Key → 401  

---

## 挑战题（可选）

### C1. 工具级授权

请求体增加 `tools: list[str]`。  
若包含 `"shell"`，则用户必须拥有权限标记 `tool:shell`，否则 **403**。

可用结构：

```python
PERMISSIONS: dict[str, set[str]] = {
    "alice": {"tool:shell", "tool:search"},
    "bob": {"tool:search"},
}
```

**验收**：bob 请求 `tools=["shell"]` → 403；仅 `search` → 200。

---

### C2. 鉴权 + 限流草图（书面）

描述：按 `user_id` 对 `POST /v1/agent/run` 做「每分钟最多 N 次」的思路。

至少写清：

1. 计数键怎么设计  
2. 鉴权与限流的先后顺序（先认出是谁，再计数）  
3. 超限返回码（建议 429）  
4. 为何限流不能替代鉴权  

**验收**：不是空话「加个中间件」；有键与顺序。

---

## 模块 06 通关自检

- [ ] 能讲清请求生命周期与中间件边界
- [ ] 能写 FastAPI + Pydantic 基础 API
- [ ] 能用 API Key 保护接口并区分 401/403
- [ ] 清楚：教学 `!=` ≠ 恒定时间比较；Agent 服务化最小安全底线

完成后进入模块 07《数据库与数据持久化》。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成；B2 有可跑代码 + 注释说明恒定时间比较
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1 思路 + 参考答案

**思路**：身份 vs 权限。

**参考答案**：认证确认调用方身份（例如出示有效 API Key）；授权在已认证前提下判断是否允许某操作（例如是否 admin、是否能调 shell 工具）。

---

### W2 思路 + 参考答案

1. 401  
2. 403  
3. 401  

---

### W3 思路 + 参考答案

**参考答案**：使用请求头 `X-API-Key`。Key 放进 query 易进访问日志、代理日志、浏览器历史与截图分享，泄露面更大。

---

### W4 思路 + 参考答案

```python
import os

api_key = os.getenv("APP_API_KEY")  # 未设置则为 None
if not api_key:
    raise RuntimeError("APP_API_KEY is required")
```

---

### B1 思路 + 参考答案

**思路**：401 = 没证明身份；403 = 证明了但不够格。

**参考答案**：

1. 认证失败：`POST /v1/agent/run` 未带 `X-API-Key` → 401 unauthorized  
2. 授权失败：bob 的合法 Key 调用 `DELETE /admin/cache` → 403 forbidden（身份已知，角色不足）

---

### B2 思路 + 参考答案

**思路**：Depends 里统一鉴权；业务路由只声明依赖。

**参考答案**

```python
from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI(title="auth-practice")


class RunRequest(BaseModel):
    query: str = Field(min_length=1)


class RunResponse(BaseModel):
    ok: bool
    answer: str


def get_expected_api_key() -> str:
    key = os.getenv("APP_API_KEY", "dev-secret")
    return key


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    expected = get_expected_api_key()
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing api key")

    # 教学简化：!= 比较。
    # 生产应考虑 hmac.compare_digest(x_api_key, expected) 等恒定时间比较，
    # 降低（粗粒度）计时侧信道风险；且密钥管理、轮转、存储哈希另议。
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid api key")

    return x_api_key


@app.post("/v1/agent/run", response_model=RunResponse)
def agent_run(
    body: RunRequest,
    _: str = Depends(require_api_key),
) -> RunResponse:
    return RunResponse(ok=True, answer=f"echo:{body.query}")


# ---- TestClient 验收 ----
client = TestClient(app)


def test_missing_key() -> None:
    response = client.post("/v1/agent/run", json={"query": "hi"})
    assert response.status_code == 401


def test_wrong_key() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "hi"},
        headers={"X-API-Key": "wrong"},
    )
    assert response.status_code == 401


def test_ok_key() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "hi"},
        headers={"X-API-Key": "dev-secret"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


if __name__ == "__main__":
    test_missing_key()
    test_wrong_key()
    test_ok_key()
    print("b2 passed")
```

**恒定时间比较示例（了解，生产方向）**：

```python
import hmac

def api_key_equals(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided, expected)
```

---

### B3 思路 + 参考答案

**参考答案（示例 4 项）**：

1. **API Key / Bearer Token** — 日志外泄等于账号被盗  
2. **完整 `messages` / system prompt** — 可能含用户隐私与内部策略  
3. **Cookie / Session 标识** — 可被用于会话劫持  
4. **数据库连接串** — 常含密码  

观测字段应走允许列表与截断（模块 12 会再强调）。

---

### B4 思路 + 参考答案

**参考答案**：

1. payload 默认只是 Base64URL 编码，谁拿到 token 谁就能读；放 password/长期 api_key 等于把秘密印在可转发的证件上。  
2. `exp` 控制过期；没有过期则令牌泄露后攻击窗口无限延长，吊销也更难。  
3. 签名用于防篡改与校验发行方；**不等于加密**。机密数据需要加密通道（HTTPS）以及避免把机密放进 JWT；若必须放敏感声明，应另有加密方案（本课了解即可）。

---

### A1 思路 + 参考答案

**思路**：Key → user_id 映射；未知 Key 仍是 401。

**参考答案**

```python
from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI()

API_KEYS: dict[str, str] = {
    "k-alice": "alice",
    "k-bob": "bob",
}


class RunRequest(BaseModel):
    query: str = Field(min_length=1)


def require_user(x_api_key: str | None = Header(default=None)) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing api key")
    # 教学简化：dict 查找前可用 !=/not in；多密钥场景同样建议生产侧做安全比较与安全存储。
    user_id = API_KEYS.get(x_api_key)
    if user_id is None:
        raise HTTPException(status_code=401, detail="invalid api key")
    return user_id


@app.post("/v1/agent/run")
def agent_run(
    body: RunRequest,
    user_id: str = Depends(require_user),
) -> dict:
    return {"ok": True, "user_id": user_id, "answer": f"echo:{body.query}"}


client = TestClient(app)


def test_alice() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "hi"},
        headers={"X-API-Key": "k-alice"},
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == "alice"


def test_unknown() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "hi"},
        headers={"X-API-Key": "k-nobody"},
    )
    assert response.status_code == 401


if __name__ == "__main__":
    test_alice()
    test_unknown()
    print("a1 passed")
```

---

### A2 思路 + 参考答案

**思路**：先认证拿到 user，再检查 role；失败码是 403。

**参考答案**

```python
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()

API_KEYS = {"k-alice": "alice", "k-bob": "bob"}
ROLES: dict[str, set[str]] = {
    "alice": {"admin", "user"},
    "bob": {"user"},
}


def require_user(x_api_key: str | None = Header(default=None)) -> str:
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="unauthorized")
    return API_KEYS[x_api_key]


def require_role(role: str) -> Callable[[str], str]:
    def dependency(user_id: str = Depends(require_user)) -> str:
        if role not in ROLES.get(user_id, set()):
            raise HTTPException(status_code=403, detail="forbidden")
        return user_id

    return dependency


@app.delete("/admin/cache")
def clear_cache(user_id: str = Depends(require_role("admin"))) -> dict:
    return {"ok": True, "cleared_by": user_id}


client = TestClient(app)


def test_admin_ok() -> None:
    response = client.delete("/admin/cache", headers={"X-API-Key": "k-alice"})
    assert response.status_code == 200


def test_user_forbidden() -> None:
    response = client.delete("/admin/cache", headers={"X-API-Key": "k-bob"})
    assert response.status_code == 403


def test_missing_unauthorized() -> None:
    response = client.delete("/admin/cache")
    assert response.status_code == 401


if __name__ == "__main__":
    test_admin_ok()
    test_user_forbidden()
    test_missing_unauthorized()
    print("a2 passed")
```

---

### C1 思路 + 参考答案

**思路**：工具名是权限对象；想调用 ≠ 允许执行（与后续 Agent ACL 同构）。

**参考答案**

```python
from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI()

API_KEYS = {"k-alice": "alice", "k-bob": "bob"}
PERMISSIONS: dict[str, set[str]] = {
    "alice": {"tool:shell", "tool:search"},
    "bob": {"tool:search"},
}


class RunRequest(BaseModel):
    query: str = Field(min_length=1)
    tools: list[str] = Field(default_factory=list)


def require_user(x_api_key: str | None = Header(default=None)) -> str:
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="unauthorized")
    return API_KEYS[x_api_key]


@app.post("/v1/agent/run")
def agent_run(
    body: RunRequest,
    user_id: str = Depends(require_user),
) -> dict:
    allowed = PERMISSIONS.get(user_id, set())
    for tool in body.tools:
        perm = f"tool:{tool}"
        if perm not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"missing permission {perm}",
            )
    return {"ok": True, "user_id": user_id, "tools": body.tools}


client = TestClient(app)


def test_bob_shell_forbidden() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "x", "tools": ["shell"]},
        headers={"X-API-Key": "k-bob"},
    )
    assert response.status_code == 403


def test_bob_search_ok() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "x", "tools": ["search"]},
        headers={"X-API-Key": "k-bob"},
    )
    assert response.status_code == 200


if __name__ == "__main__":
    test_bob_shell_forbidden()
    test_bob_search_ok()
    print("c1 passed")
```

---

### C2 思路 + 参考答案

**参考答案要点**：

1. 键示例：`ratelimit:agent_run:{user_id}:{YYYYMMDDHHMM}`，TTL 略大于 60s；或 Redis `INCR` + `EXPIRE`。  
2. 顺序：先鉴权得到 `user_id`，再计数；否则攻击者可用随机 Key 打满「匿名桶」或绕过用户级配额语义。  
3. 超限返回 **429**，可带 `Retry-After`。  
4. 限流只抑制滥用与费用爆炸，**不能**证明身份，也不能代替授权检查。
