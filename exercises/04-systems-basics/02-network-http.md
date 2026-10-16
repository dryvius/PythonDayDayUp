# 练习：网络与 HTTP

> 对应文档：[`docs/04-systems-basics/02-network-http.md`](../../docs/04-systems-basics/02-network-http.md)  
> 状态：`已完成出题` · 建议用时：50～80 分钟

目录：`playground/04-systems-basics/02-network-http/`

---

## 基础题（必做）

### B1. 状态码速查表（书面）

自制表格：200/401/403/404/429/500/502/503 —— 含义 + Agent 侧第一反应。

### B2. 手写 JSON 请求体

构造一个「假 Chat Completions」请求 dict，含 `model` 与 `messages`，`json.dumps` 后写到文件，再读回断言。

### B3. 解析错误响应

给定假响应：

```python
{"error": {"message": "Rate limit", "type": "rate_limit", "code": 429}}
```

写函数返回 `(code, message)`；再映射成你自定义的 `RateLimitError`（可极简）。

### B4. Timeout 政策（书面）

写清：连接超时 vs 读取超时为什么都要关心；LLM 调用你会设大概多少秒（给一个合理起点即可）。

---

## 进阶题（建议）

### A1. 重试决策函数

`should_retry(status_code: int, method: str) -> bool`  
规则自定但要合理：例如 429/503 可重试；400/401 不重试；POST 是否重试要注释说明。

### A2. 用 httpx/requests 打一个公开 GET（可选联网）

如 `https://httpbin.org/get`，打印 status_code。公司网络受限则改用 mock 响应，并注明。

---

## 挑战题（可选）

### C1. 设计 Tool API 的幂等策略

为一个「创建工单」POST 工具写 10 行方案：幂等键怎么传、重试如何避免重复创建。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
