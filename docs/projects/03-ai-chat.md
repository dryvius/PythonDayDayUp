# Project 3：AI Chat

> 状态：`已完成实战说明`  
> 建议时机：完成模块 09 后  
> 建议工时：8～14 小时  
> 推荐目录：`playground/projects/03-ai-chat/`  
> 运行环境：Python ≥ 3.11 · FakeLLM 契约见 [`../CONVENTIONS.md`](../CONVENTIONS.md)

## 项目目标

做一个最小「多轮聊天」服务：Chat API 适配层、会话历史、流式可选、结构化日志；无 Key 时 FakeLLM 可演示。

## 你将练习到的能力

| 模块 | 知识点 |
|------|--------|
| 06 | FastAPI 入参/出参、依赖注入 |
| 09 | Chat messages、token/上下文、Prompt、超时重试、Structured Output（可选） |
| 03/05 | logging、asyncio HTTP |

工程实践：**LLM 适配层**（真客户端与 Fake 可切换）、历史截断、不把密钥打进日志。

## 需求概述

### 功能

1. `POST /v1/chat`：`{session_id?, message}` → `{reply, model, usage?}`  
2. 同 `session_id` 多轮能带上历史（服务端存内存或 SQLite）  
3. 系统提示可配置；支持「材料不足就说不知道」类约束  
4. `GET /health`；缺 Key 时自动 FakeLLM（或显式 `LLM_MODE=fake`）  

### 非功能

- 上下文超长时截断（保留 system + 最近 N 轮）  
- LLM 调用设 timeout；429/5xx 有限退避  
- FakeLLM：关键词规则足够演示多轮；**`complete` 返回 assistant dict**（含 `role` / `content`），不要直接返回 `str`  
- 日志：`session_id`、latency_ms、model；**禁止**完整 API Key 与默认倾倒完整 messages  

## 建议目录

```text
playground/projects/03-ai-chat/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── llm/
│   │   ├── base.py          # Protocol
│   │   ├── fake.py
│   │   └── openai_compatible.py
│   ├── services/chat.py
│   └── schemas.py
├── prompts/system.md
├── tests/test_chat.py
├── .env.example
└── README.md
```

## 起步建议（第一天）

1. 定 `LLMClient` Protocol：`async def complete(messages, ...) -> dict`  
2. 实现 FakeLLM（关键词回显即可）+ 单轮 `/v1/chat`  
3. 再加 `session_id` 历史与截断；最后接真 API 适配层  

必读章节：

- [LLM API](../09-ai-llm/02-llm-api.md)  
- [Prompt](../09-ai-llm/03-prompt-engineering.md)  
- [CONVENTIONS · FakeLLM](../CONVENTIONS.md)  

## 里程碑

- [ ] **M1**：FakeLLM + 单轮 `/v1/chat`  
- [ ] **M2**：会话历史 + 截断；可切换真 API（OpenAI 兼容即可）  
- [ ] **M3**：超时/重试；测试覆盖 Fake 路径；可选 SSE 流式（拼装逻辑见模块 09）  

## 验收标准

- [ ] `LLM_MODE=fake` 下测试全绿  
- [ ] Fake / 真客户端都返回 **assistant dict**，业务层统一取 `content`  
- [ ] 换真模型只改适配层与配置，不改路由业务翻天  
- [ ] 超长历史不会无脑塞爆（有截断策略与单测）  
- [ ] README 写清环境变量；日志无密钥  

## 常见易错

| 坑 | 正确做法 |
|----|----------|
| `complete` 直接返回 `str` | 统一 assistant dict（CONVENTIONS） |
| 路由里写死 OpenAI SDK 调用 | 经适配层；Fake / 真可切换 |
| 历史无限追加 | 保留 system + 最近 N 轮；单测超长历史 |
| 日志打印完整 messages / Header | 字段允许列表；密钥脱敏 |
| 无 timeout | 所有外呼 LLM 设超时 + 有限退避 |

## 延伸挑战

- `response_format` / Pydantic 结构化意图分类前置路由  
- 会话落 Postgres  
- 简单前端（非必须）  

## 导航

- 返回项目列表：[./README.md](./README.md)
- 相关文档：[LLM API](../09-ai-llm/02-llm-api.md) · [Prompt](../09-ai-llm/03-prompt-engineering.md) · [FastAPI](../06-web-backend/02-fastapi-pydantic.md)
- 下一项目：[RAG 知识库](./04-rag-kb.md)
- 返回总览：[../../README.md](../../README.md)
