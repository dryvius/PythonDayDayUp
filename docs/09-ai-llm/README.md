# 模块 09-ai-llm：AI / LLM 基础与认知地图

> 状态：`四章正文与练习已全部完成` · 预计周期：1～2 周

## 模块目标

对现阶段 AI 发展与常用名词建立较深入认知，并能调用 LLM。

## 为什么现在学

Agent 建立在 LLM 能力之上；先统一术语与心智模型，再进入 RAG / Tool / Agent，学习效率更高。

## 章节目录

1. [AI 发展脉络与名词词典](./01-ai-landscape-glossary.md) · [练习](../../exercises/09-ai-llm/01-ai-landscape-glossary.md)
2. [LLM API 实战](./02-llm-api.md) · [练习](../../exercises/09-ai-llm/02-llm-api.md)
3. [Prompt Engineering](./03-prompt-engineering.md) · [练习](../../exercises/09-ai-llm/03-prompt-engineering.md)
4. [Structured Output](./04-structured-output.md) · [练习](../../exercises/09-ai-llm/04-structured-output.md)

## 建议学习方式

1. 第一章先建立词典，避免后面被名词淹没
2. API 章用 FakeClient 也能完成主线；有 Key 再打真调用
3. 提示词请版本化进文件，不要只活在聊天记录里
4. 结构化输出是 Tool Calling 的桥，务必做通 Pydantic 校验

## 模块自检

- [ ] 能讲清 Token、上下文窗口、预训练/微调/推理
- [ ] 能封装 Chat 调用并处理重试边界
- [ ] 能写出可维护的 system/few-shot 模板
- [ ] 能把模型输出可靠解析为 Pydantic 模型

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[部署、运维与软件架构](../08-devops-architecture/README.md)
- 下一模块：[Embedding 与 RAG](../10-rag/README.md)
