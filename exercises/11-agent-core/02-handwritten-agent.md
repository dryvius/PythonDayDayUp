# 练习：手写一个 Agent

> 对应文档：[`docs/11-agent-core/02-handwritten-agent.md`](../../docs/11-agent-core/02-handwritten-agent.md)  
> 状态：`已完成出题` · 建议用时：90～140 分钟

---

## 基础题（必做）

### B1. 状态机图

画出 IDLE/CALLING_LLM/EXECUTING_TOOLS/DONE/FAILED。

### B2. FakeLLM

规则：用户含「搜索」则返回 search tool_call，否则直接答。

### B3. Agent.run

实现文档骨架，跑通「搜索」与「普通问答」两路径。

### B4. max_steps

构造 FakeLLM 每次都要调工具，断言达到 max_steps 停止。

---

## 进阶题（建议）

### A1. 工具错误恢复

search 抛错时回传错误，下一步 FakeLLM 给出最终致歉/说明。

### A2. 轨迹打印

每步打印 role 与是否含 tool_calls，便于调试。

---

## 挑战题（可选）

### C1. 与真实 LLM 对接

有 Key 则换真模型；保留 Fake 作为测试双模式。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
