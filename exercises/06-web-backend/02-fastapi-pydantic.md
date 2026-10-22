# 练习：FastAPI + Pydantic

> 对应文档：[`docs/06-web-backend/02-fastapi-pydantic.md`](../../docs/06-web-backend/02-fastapi-pydantic.md)  
> 状态：`已完成出题`  
> 建议用时：90～150 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/06-web-backend/02-fastapi-pydantic/
```

推荐最小布局：

```text
playground/06-web-backend/02-fastapi-pydantic/
  app/
    __init__.py
    main.py
    schemas.py
    settings.py
  test_api.py
```

4. 依赖：`fastapi`、`uvicorn`；测试用 `fastapi.testclient.TestClient`（无需真起端口）。
5. Python ≥ 3.11；先自己做完再看文末答案。
6. **刻意简化提醒**（见 `docs/CONVENTIONS.md`）：`BackgroundTasks` 只适合轻量收尾；**长任务请上队列**，不要把「跑 3 分钟 Agent」塞进 BackgroundTasks。

---

## 热身题（建议先做）

### W1. 安装与导入自检

**要求**：在 venv 中安装 `fastapi` 与 `uvicorn`，写 5 行脚本确认可以 `from fastapi import FastAPI`。

**验收**：导入无报错即可。

---

### W2. 最小 app 脑内编译

**给定**：

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/ping")
def ping() -> dict[str, str]:
    return {"pong": "ok"}
```

**要求**：用一句话说明：浏览器访问 `GET /ping` 时，框架如何知道该调用 `ping`。

**验收**：提到「路由表 / 装饰器注册 / 方法+路径匹配」即可。

---

### W3. 422 直觉

**要求**：说明为什么「缺字段的 JSON body」常常得到 **422** 而不是 500。

**验收**：能说到「请求体校验失败（Pydantic），尚未进入你的业务逻辑」。

---

### W4. Echo 契约

**要求**：手写（不必跑）一个响应 dict，字段至少含 `reply: str`、`model: str`，作为后面 `/v1/chat` 的目标形状。

**验收**：键名固定，便于前后端对齐。

---

## 基础题（必做）

### B1. Health

创建 `app/main.py`：

- `GET /health` 返回 `{"status": "ok"}`
- 可用 `uvicorn app.main:app --reload` 跑通，或直接用 TestClient

**验收**：

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
assert client.get("/health").status_code == 200
assert client.get("/health").json() == {"status": "ok"}
```

---

### B2. Chat 模型（Pydantic + Echo）

实现 `POST /v1/chat`：

**请求模型**（字段名固定）：

- `message: str` — 非空（strip 后也不能为空）
- `temperature: float = 0.2` — 范围 0～2

**响应模型**：

- `reply: str`
- `model: str`

**逻辑**：先做 Echo 即可，例如 `reply = f"echo: {message}"`；`model` 可先写死 `"echo-1"`（B4 再改为来自 Settings）。

**验收**：

1. 合法请求 → 200，字段齐全
2. 缺 `message` / `temperature=9` / `message="   "` → **422**（或你对空字符串用 422/400，但必须稳定可测；推荐用 Pydantic 校验得到 422）

---

### B3. 路径参数与 404

实现 `GET /sessions/{session_id}`：

- `session_id: int`
- 用模块级内存 `dict[int, dict]` 预置至少 1 个会话
- 存在 → 200 返回会话 dict
- 不存在 → `HTTPException(status_code=404, detail="session not found")`

**验收**：存在与不存在两条路径都有断言。

---

### B4. Depends 配置

实现：

```python
class Settings(BaseModel):
    app_name: str = "agent-api"
    model_name: str = "echo-1"


def get_settings() -> Settings:
    ...
```

在 `POST /v1/chat` 里通过 `Depends(get_settings)` 注入，响应里的 `model` **必须**来自 `settings.model_name`。

**验收**：改 Settings 默认 `model_name` 后，chat 响应跟着变（可用依赖覆盖测试）。

---

## 进阶题（建议至少做 1 题）

### A1. Agent Run API

实现 `POST /v1/agent/run`：

**请求**建议字段：

- `query: str`（非空）
- `max_steps: int = 3`（建议地理边界：1～10）

**行为**：

1. 正常：返回类似 `{"ok": true, "steps": [...], "answer": "..."}`（可用假步骤）
2. 若 `query == "boom"`：返回 **400**，`detail` 说明触发了演示错误
3. `max_steps` 越界：422（Pydantic）或 400（手写校验），二选一但要测到

**验收**：正常 / boom / 越界 三条路径可测。

---

### A2. 自定义校验异常格式

自定义 `RequestValidationError` 的 exception handler，使校验失败时响应形如：

```json
{
  "ok": false,
  "error": "validation_error",
  "details": [ ... ]
}
```

用故意非法的 `/v1/chat` 请求验证。

**验收**：不再是默认 FastAPI 的 `{"detail":[...]}` 顶层形状（或你明确包了一层）；`ok` 为 `false`。

---

## 挑战题（可选）

### C1. BackgroundTasks 写日志（轻量收尾）

在 `POST /v1/chat` **成功**后，用 `BackgroundTasks` 追加一行到 `requests.log`（内容含时间与 message 摘要即可）。

**硬性说明（写进代码注释）**：

- BackgroundTasks 适合「轻量收尾」（写一行日志、清理临时文件）
- **不等于**长任务执行器；跑数分钟的 Agent / 重试风暴请上消息队列

**验收**：请求返回后文件出现新行；注释里写明上述边界。

---

### C2. TestClient 烟雾测试集

用 `TestClient` 至少覆盖：

1. `GET /health` 200
2. `POST /v1/chat` 成功
3. `POST /v1/chat` 非法 body → 422（或你的自定义校验响应）
4. （若做了 A1）`query=boom` → 400

**验收**：`pytest test_api.py` 或 `python test_api.py` 可绿。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成，服务可启动或 TestClient 全绿
- [ ] 能口述：422 与 500 的差别；Depends 解决什么
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2；若做 C1，必须写明 BackgroundTasks ≠ 长任务

---

## 提示与参考答案（先做题再看）

> 下列参考实现可粘贴到 playground 后按需拆分文件。答案用 TestClient 自检。

### W1 思路 + 参考答案

**思路**：先保证环境，再写业务。

**参考答案**

```bash
pip install "fastapi>=0.110" "uvicorn[standard]>=0.27"
python -c "from fastapi import FastAPI; print(FastAPI)"
```

---

### W2 思路 + 参考答案

**思路**：装饰器在 import 时把函数挂到路由表。

**参考答案**：`@app.get("/ping")` 在加载模块时把 `(GET, /ping)` 注册到应用路由表；请求到来时 ASGI 服务器把调用交给 FastAPI，按方法+路径找到 `ping` 并执行。

---

### W3 思路 + 参考答案

**思路**：校验层 vs 业务层。

**参考答案**：请求体先经 Pydantic 校验；缺字段/类型错误会在进入 endpoint 前失败，FastAPI 默认转成 422 Unprocessable Entity。500 通常表示你的业务代码未捕获异常。

---

### W4 思路 + 参考答案

```python
{"reply": "echo: hi", "model": "echo-1"}
```

---

### B1～B4 + C2 综合参考答案

**思路**

1. 先 `health`，再 schema，再路由，再 Depends。
2. 空字符串用 `field_validator` 拒绝。
3. 测试全部走 TestClient，不依赖手工点 `/docs`。

**参考答案**（可按文件拆分；此处合并便于阅读）

```python
# app/settings.py
from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "agent-api"
    model_name: str = "echo-1"


def get_settings() -> Settings:
    return Settings()
```

```python
# app/schemas.py
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str
    temperature: float = Field(default=0.2, ge=0, le=2)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be blank")
        return cleaned


class ChatResponse(BaseModel):
    reply: str
    model: str


class AgentRunRequest(BaseModel):
    query: str = Field(min_length=1)
    max_steps: int = Field(default=3, ge=1, le=10)


class AgentRunResponse(BaseModel):
    ok: bool
    steps: list[str]
    answer: str
```

```python
# app/main.py
from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import (
    AgentRunRequest,
    AgentRunResponse,
    ChatRequest,
    ChatResponse,
)
from app.settings import Settings, get_settings

app = FastAPI(title="fastapi-pydantic-practice")

SESSIONS: dict[int, dict] = {
    1: {"id": 1, "title": "demo", "user_id": "alice"},
}

LOG_PATH = Path(__file__).resolve().parent.parent / "requests.log"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    # A2：统一校验错误外壳；不影响业务 404/400
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": "validation_error",
            "details": exc.errors(),
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _append_chat_log(message: str) -> None:
    # C1：轻量收尾。长任务（分钟级 Agent）请上队列，不要用 BackgroundTasks 硬扛。
    line = f"chat message={message[:80]!r}\n"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    reply = f"echo: {body.message}"
    background_tasks.add_task(_append_chat_log, body.message)
    return ChatResponse(reply=reply, model=settings.model_name)


@app.get("/sessions/{session_id}")
def get_session(session_id: int) -> dict:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


@app.post("/v1/agent/run", response_model=AgentRunResponse)
def agent_run(body: AgentRunRequest) -> AgentRunResponse:
    if body.query == "boom":
        raise HTTPException(status_code=400, detail="demo boom triggered")

    steps = [f"step-{i}" for i in range(1, body.max_steps + 1)]
    return AgentRunResponse(
        ok=True,
        steps=steps,
        answer=f"fake-answer:{body.query}",
    )
```

```python
# test_api.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.settings import Settings, get_settings

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_ok() -> None:
    response = client.post(
        "/v1/chat",
        json={"message": "hello", "temperature": 0.2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "echo: hello"
    assert data["model"] == "echo-1"


def test_chat_validation() -> None:
    response = client.post("/v1/chat", json={"temperature": 0.2})
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "validation_error"


def test_session_404() -> None:
    response = client.get("/sessions/999")
    assert response.status_code == 404


def test_session_ok() -> None:
    response = client.get("/sessions/1")
    assert response.status_code == 200
    assert response.json()["title"] == "demo"


def test_settings_dependency_override() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(model_name="override-1")
    try:
        response = client.post("/v1/chat", json={"message": "x"})
        assert response.status_code == 200
        assert response.json()["model"] == "override-1"
    finally:
        app.dependency_overrides.clear()


def test_agent_boom() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "boom", "max_steps": 2},
    )
    assert response.status_code == 400


def test_agent_ok() -> None:
    response = client.post(
        "/v1/agent/run",
        json={"query": "hi", "max_steps": 2},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert len(response.json()["steps"]) == 2


if __name__ == "__main__":
    test_health()
    test_chat_ok()
    test_chat_validation()
    test_session_404()
    test_session_ok()
    test_settings_dependency_override()
    test_agent_boom()
    test_agent_ok()
    print("all passed")
```

---

### A1 思路（单独强调）

**思路**：把「演示错误」与「校验错误」分开——`boom` 用 400；schema 越界用 422。

（实现已包含在上面的 `agent_run`。）

---

### A2 思路（单独强调）

**思路**：`@app.exception_handler(RequestValidationError)` 统一外壳，前端只依赖 `ok/error/details`。

注意：自定义后，测试里断言顶层键是 `ok` 而不是只断言 `detail`。

---

### C1 思路 + 补充说明

**思路**：`background_tasks.add_task(fn, *args)` 在响应返回后执行；失败默认不易被客户端感知，故只做最佳努力的轻量事。

**不要做的事**：

- 在 BackgroundTasks 里跑多步 Agent tool-loop
- 假设「任务一定完成 / 一定只执行一次」
- 用它替代 Redis/Rabbit/RQ/Celery 等队列

---

### 常见踩坑

1. **在路由里写 `async def` 却调用同步 `open().write` 长阻塞**：练习日志一行尚可；生产大量磁盘 I/O 仍要小心。
2. **把 `model` 写死在两处**：B4 要求单一来源 Settings。
3. **用 `dict` 当请求体不做校验**：丢失 422 福利，后面联调更痛。
4. **测试不清理 `dependency_overrides`**：会导致后续用例串味。
