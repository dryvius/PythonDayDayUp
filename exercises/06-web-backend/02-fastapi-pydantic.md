# 练习：FastAPI + Pydantic

> 对应文档：[`docs/06-web-backend/02-fastapi-pydantic.md`](../../docs/06-web-backend/02-fastapi-pydantic.md)  
> 状态：`已完成出题` · 建议用时：90～150 分钟

目录：`playground/06-web-backend/02-fastapi-pydantic/`  
依赖：`fastapi`、`uvicorn`；测试可用 `httpx` 的 ASGITransport 或手动点 `/docs`。

---

## 基础题（必做）

### B1. Health

创建 `app/main.py`：`GET /health` 返回 `{"status":"ok"}`。  
`uvicorn app.main:app --reload` 跑通。

### B2. Chat 模型

实现 `POST /v1/chat`：

- 请求：`message`（非空）、`temperature`（0～2，默认 0.2）
- 响应：`reply`、`model`
- 逻辑可先 Echo

非法 body 应得到 422。

### B3. 路径参数

`GET /sessions/{session_id}`：`session_id` 为 int；不存在时 `HTTPException 404`（可用内存 dict 模拟）。

### B4. Depends 配置

`Settings` + `get_settings`，在 `/v1/chat` 响应的 `model` 字段取自 settings。

---

## 进阶题（建议）

### A1. Agent Run API

实现文档综合例子 `/v1/agent/run`，含 `max_steps` 边界校验；`query=boom` 返回 400。

### A2. 自定义校验异常格式

自定义 `RequestValidationError` handler，返回 `{"ok":false,...}`；用故意非法请求验证。

---

## 挑战题（可选）

### C1. BackgroundTasks

在 chat 成功后后台追加一行到 `requests.log`（注意并发下简单 append 即可，学习用）。

### C2. TestClient 烟雾测试

用 `fastapi.testclient.TestClient` 写 2 个测试：health 与 chat 成功路径。

---

## 验收标准

- [ ] B1～B4 完成且服务可启动
- [ ] （建议）A1 或 A2
