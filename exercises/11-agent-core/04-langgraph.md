# 练习：LangGraph 与工作流

> 对应文档：[`docs/11-agent-core/04-langgraph.md`](../../docs/11-agent-core/04-langgraph.md)  
> 状态：`已完成出题` · 建议用时：60～100 分钟

可用微型图执行器，不必安装 LangGraph。

---

## 基础题（必做）

### B1. 建模

把「LLM ↔ Tools」画成节点和边，标出条件路由。

### B2. State

定义 state 字段至少含 messages/step/status。

### B3. 微型执行器

实现或改写文档 `run_graph`，跑通 llm→tools→llm→end（可用假节点）。

### B4. 防死循环

证明 max_visits / max_steps 生效（测超限抛错或强制 end）。

---

## 进阶题（建议）

### A1. 人工批准节点

加入 `approve`：默认拒绝某工具，状态进入 waiting；模拟批准后继续。

### A2. Checkpoint 草图

设计把每步 state 追加写入 JSONL 的接口。

---

## 挑战题（可选）

### C1. 对照真实库

安装并跑官方最小例子（可选），写差异笔记 8 行。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
