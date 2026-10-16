# 练习：Prompt Engineering

> 对应文档：[`docs/09-ai-llm/03-prompt-engineering.md`](../../docs/09-ai-llm/03-prompt-engineering.md)  
> 状态：`已完成出题` · 建议用时：50～80 分钟

---

## 基础题（必做）

### B1. System 模板

写一个可复用 system prompt：中文助手 + 3 条硬规则 + 输出语言约束；保存 `prompts/system_v1.md`。

### B2. Few-shot 分类

为工单分类（billing/tech/other）写带 3 个示例的 user 模板函数 `render(question)`。

### B3. 约束清单

给「基于资料回答」任务列 5 条可检查约束（含材料不足时的行为）。

### B4. 注入防护分隔

写一段把用户输入包进 `USER DATA` 分隔区的模板，并说明为何不要让用户内容直接改写系统规则。

---

## 进阶题（建议）

### A1. CoT 决策

列出 3 个该用 / 3 个不该用思维链的任务类型。

### A2. 提示版本化

为同一任务写 v1/v2 两版提示，记录你改了什么、期望改善什么。

---

## 挑战题（可选）

### C1. 迷你评测集

准备 10 条输入 + 期望标签；用 Fake 规则或真模型跑，算准确率（可手工）。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
