# 练习：Web 框架原理

> 对应文档：[`docs/06-web-backend/01-web-framework-principles.md`](../../docs/06-web-backend/01-web-framework-principles.md)  
> 状态：`已完成出题` · 建议用时：40～70 分钟

目录：`playground/06-web-backend/01-web-framework-principles/`

---

## 基础题（必做）

### B1. 画生命周期

用文字或 ascii 画出：请求从客户端到 endpoint 再返回的 7～9 步，标注「鉴权」和「LLM 调用」可能插在哪。

### B2. 路由设计

为迷你 Agent 服务设计 4 个端点（方法+路径+一句话职责），至少含 health 与 run。

### B3. 中间件职责清单

列出 3 件适合中间件、2 件不适合放中间件的事。

### B4. sync vs async

判断并简述：

1. endpoint 只返回固定 JSON  
2. endpoint 内 `await httpx` 调 LLM  
3. endpoint 内用 `requests` 调 LLM（你该怎么改）

---

## 进阶题（建议）

### A1. WSGI/ASGI 对照表

写 5 行：FastAPI 为什么通常用 uvicorn，而不是「像旧 Flask 那样想当然」。

### A2. 阻塞事故复盘（书面）

假设有人在 async 路由里 `time.sleep(10)`，用户会观察到什么？如何定位？

---

## 挑战题（可选）

### C1. 画部署草图

Internet → 反向代理 → uvicorn → FastAPI，标注 TLS 终止可能在哪一层。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
