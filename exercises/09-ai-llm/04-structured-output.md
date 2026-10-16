# 练习：Structured Output

> 对应文档：[`docs/09-ai-llm/04-structured-output.md`](../../docs/09-ai-llm/04-structured-output.md)  
> 状态：`已完成出题` · 建议用时：60～90 分钟

---

## 基础题（必做）

### B1. Pydantic 模型

定义 `IntentResult(intent: Literal[...], confidence: float)`，对合法/非法 dict 做 validate 测试。

### B2. strip_fences

实现去掉 Markdown 代码围栏的函数，覆盖有无围栏两种输入。

### B3. parse 管线

`text -> strip -> json.loads -> Pydantic`；非法 JSON 抛明确错误。

### B4. 修复重试伪代码

写 `parse_with_repair(call_llm, raw_prompt, n=2)` 伪代码：失败则追加修复说明再调用。

---

## 进阶题（建议）

### A1. ToolArgs

用 Pydantic 定义 `SearchArgs`，再 `model_dump` 成 tool arguments；故意越界 `top_k` 验证失败。

### A2. 端到端 Fake

FakeLLM 固定返回 JSON 字符串；业务侧解析成模型并断言字段。

---

## 挑战题（可选）

### C1. 严格模式

讨论：是否 `extra='forbid'`；对 LLM 多余字段你选择丢弃还是失败？写 5 行权衡。

---

## 模块 09 通关自检

- [ ] 术语地图清楚（Token/上下文/RAG/Agent…）
- [ ] 能封装 Chat 调用（真或假）
- [ ] 会写可维护提示模板
- [ ] 会结构化解析 + Pydantic 校验

完成后进入模块 10《Embedding 与 RAG》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
