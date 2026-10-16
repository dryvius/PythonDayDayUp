# 练习：LLM API 实战

> 对应文档：[`docs/09-ai-llm/02-llm-api.md`](../../docs/09-ai-llm/02-llm-api.md)  
> 状态：`已完成出题` · 建议用时：70～110 分钟

无 Key 可接真 API；否则实现 `FakeLLM`，接口保持与 [`CONVENTIONS.md`](../../docs/CONVENTIONS.md) 一致：  
`complete(messages, tools=None) -> assistant_message(dict)`。

---

## 基础题（必做）

### B1. messages 构造

写函数 `build_chat(system: str, user: str) -> list[dict]`，并单元测试结构。

### B2. Client 封装

实现 `async def complete(messages, tools=None) -> dict`（真或假）。  
Fake 模式返回：`{"role": "assistant", "content": "ECHO: " + 最后一条 user content}`。  
另写 `text_of(message: dict) -> str`。

### B3. 参数实验（书面或代码）

对比 temperature=0 与 0.9 在「提取订单号」任务上的稳定性差异（可假想+论述；有 API 则实测 3 次）。  
说明输出上限字段为何要做成适配层的 `max_output_tokens`。

### B4. 重试策略函数

`should_retry(status_code: int | None, exc_type: str | None) -> bool`，覆盖 401/429/503/timeout。

---

## 进阶题（建议）

### A1. SSE 文本流式拼装

1. 实现 `parse_sse_data_line`  
2. 用异步生成器模拟若干 `data: {"choices":[{"delta":{"content":"..."}}]}` 行 + `[DONE]`  
3. 消费者拼出完整字符串并断言  

### A2. 流式 tool_calls 拼装

给定分片 delta（同一 `index` 上 `arguments` 拆成多段），用 `merge_tool_call_delta` 拼出完整 `tool_calls`，再 `json.loads(arguments)`。

### A3. Protocol 适配

定义 `LLMClient` Protocol（返回 dict），提供 `FakeLLM` 与另一种实现；业务函数只依赖 Protocol。

---

## 挑战题（可选）

### C1. 真实 httpx 调用

在有 Key 的前提下打一次 Chat Completions（非流式即可），打印 usage（若有）与耗时；注意脱敏。  
可选：再打一次 `stream=True`，验证与非流式 content 一致。

---

## 验收标准

- [ ] B1～B4 完成；`complete` 返回 dict 而非裸 str  
- [ ] （建议）A1 或 A2  
- [ ] （建议）A3
