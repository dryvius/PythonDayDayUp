# 练习：认证与授权

> 对应文档：[`docs/06-web-backend/03-auth.md`](../../docs/06-web-backend/03-auth.md)  
> 状态：`已完成出题` · 建议用时：60～100 分钟

目录：`playground/06-web-backend/03-auth/`（可承接上一章项目）

---

## 基础题（必做）

### B1. 概念题（书面）

各举一例：认证失败、授权失败；对应你会返回 401 还是 403。

### B2. API Key 依赖

实现 `require_api_key`，保护 `POST /v1/agent/run`。  
无 Key / 错 Key → 401；正确 Key（环境变量）→ 200。

### B3. 日志安全

在代码注释或笔记中列出：哪些字段绝对不能打进日志（至少 3 项）。

### B4. JWT 直觉（书面）

解释：JWT payload 为什么不该放 `password` 或 `api_key`；`exp` 有何用。

---

## 进阶题（建议）

### A1. 多 Key 映射用户

内存 dict：`{"k1": "alice", "k2": "bob"}`，依赖返回 `user_id`；响应里带回 `user_id`（演示用）。

### A2. RBAC 雏形

`require_role("admin")`：alice 有 admin，bob 没有。  
`DELETE /admin/cache` 仅 admin 可访问；bob 得 403。

---

## 挑战题（可选）

### C1. 工具级授权

请求体含 `tools: list[str]`；若包含 `shell` 且用户无 `tool:shell` 权限 → 403。

### C2. 鉴权 + 限流草图（书面）

描述：按 `user_id` 每分钟最多 N 次 `/v1/agent/run` 的思路（不必完整实现）。

---

## 模块 06 通关自检

- [ ] 能讲清请求生命周期与中间件边界
- [ ] 能写 FastAPI + Pydantic 基础 API
- [ ] 能用 API Key 保护接口并区分 401/403
- [ ] 清楚 Agent 服务化最小安全底线

完成后进入模块 07《数据库与数据持久化》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
