# 练习：Multi-Agent

> 对应文档：[`docs/11-agent-core/06-multi-agent.md`](../../docs/11-agent-core/06-multi-agent.md)  
> 状态：`已完成出题` · 建议用时：50～80 分钟

---

## 基础题（必做）

### B1. 模式选择题

给 5 个任务，标成路由/流水线/辩论/单 Agent 即可。

### B2. Router

实现 `classify`（规则即可）+ `route` + `handle`，至少 2 个专家 FakeAgent。

### B3. 何时不用（书面）

列 4 条「不要上多 Agent」的信号。

### B4. 消息协议

设计一条 agent 间消息的 JSON schema（from/to/type/payload/trace_id）。

---

## 进阶题（建议）

### A1. 流水线

调研→写作两个 FakeAgent，串行传递中间产物。

### A2. 权限隔离

不同 Agent 绑定不同工具集；验证写作 Agent 调不到 shell。

---

## 挑战题（可选）

### C1. 批评循环

提案→批评→修改，最多 2 轮后结束。

---

## 模块 11 通关自检

- [ ] 会实现 tool calling 环
- [ ] 能手写最小 Agent
- [ ] 理解框架价值与边界
- [ ] 能用图建模工作流
- [ ] 会基础记忆策略
- [ ] 能判断是否真要多 Agent

完成后进入模块 12《Agent 工程化与生产落地》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
