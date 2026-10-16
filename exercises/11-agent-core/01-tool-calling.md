# 练习：Tool Calling

> 对应文档：[`docs/11-agent-core/01-tool-calling.md`](../../docs/11-agent-core/01-tool-calling.md)  
> 状态：`已完成出题` · 建议用时：60～90 分钟

---

## 基础题（必做）

### B1. 定义工具 schema

为 `search` 与 `calc` 写 tools JSON（含 parameters）。

### B2. REGISTRY

实现两个函数并注册；用合法参数调用成功。

### B3. run_tool_call

解析 arguments 字符串，执行并返回 tool 消息；覆盖未知工具与异常路径。

### B4. 终止条件（书面）

列出你的 Agent 循环 4 条停止条件。

---

## 进阶题（建议）

### A1. Pydantic 校验参数

`SearchArgs` 校验失败时返回 ok=false 内容给模型侧消息。

### A2. 多步模拟

手写 messages 列表：user → assistant(tool_calls) → tool → assistant(final)。

---

## 挑战题（可选）

### C1. 并行 tool_calls

两个独立工具用 `asyncio.gather` 执行（可 sync 包 `to_thread`）。  
再造一条路径：其中一个失败 → 仍返回对应 tool 错误 JSON，另一个成功结果保留。

### C2. 结果截断

对超长工具返回做 `clip_tool_content`，断言 messages 里不会超过上限。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
