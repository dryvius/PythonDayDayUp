# 练习：软件架构基础

> 对应文档：[`docs/08-devops-architecture/03-software-architecture.md`](../../docs/08-devops-architecture/03-software-architecture.md)  
> 状态：`已完成出题` · 建议用时：50～90 分钟

---

## 基础题（必做）

### B1. 分层图

为「带 Tool 与 LLM 的 Agent API」画出 API / Application / Domain / Infrastructure 四层，并各举 2 个文件/模块名。

### B2. 依赖方向审查

判断对错并改写：

1. `domain/agent.py` import `openai`  
2. `api/routes.py` 直接拼 SQL  
3. `infrastructure/llm_openai.py` 实现 `domain/ports.py` 里的 `LLMClient`

### B3. 密钥清单

列 `.env.example` 应有的变量（至少 5 个）与绝对不能提交的文件类型。

### B4. 边界变更题

「把 OpenAI 换成另一家模型」应主要改哪些层？哪些层应基本不动？

---

## 进阶题（建议）

### A1. 六边形一句话 + 草图

用自己的话解释端口/适配器；画一张输入适配器与输出适配器示例。

### A2. 模块化单体 vs 微服务（书面）

给出你当前阶段选择模块化单体的 4 个理由；再给 2 个未来可能拆 worker 的触发条件。

---

## 挑战题（可选）

### C1. 重构清单

拿你现有 `playground` 里某个小项目，列 5 条「下一步架构改进」TODO（不必马上做完）。

---

## 模块 08 通关自检

- [ ] 会基础 Linux 排障命令
- [ ] 会 Dockerfile / compose 核心概念
- [ ] 能画清 Agent 分层与依赖方向
- [ ] 密钥管理原则清楚

完成后进入模块 09《AI / LLM 基础与认知地图》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
