# 课后练习题

本目录**独立于** `docs/` 学习正文，专门存放每一小章节的练习。

## 怎么用

1. 先学 `docs/<模块>/<章节>.md`
2. 再做本目录下同名练习文件
3. 以练习文件中的验收标准为准，而不是“感觉学会了”
4. **先自己做完**，再看文末「提示与参考答案」（思路 + 可对照的正确答案）
5. 体例标杆：[函数与作用域](./01-python-basics/02-functions-scope.md)（热身 / 基础 / 进阶 / 挑战 + 详细答案）

约定见 [`../docs/CONVENTIONS.md`](../docs/CONVENTIONS.md)（Python ≥ 3.11、FakeLLM 等）。

## 目录

### 01-python-basics · Python 语言基础

- [语法与数据结构](./01-python-basics/01-syntax-basics.md)
- [函数与作用域](./01-python-basics/02-functions-scope.md)
- [模块、包与导入系统](./01-python-basics/03-modules-packages.md)

### 02-advanced-python · Python 高级特性与类型系统

- [面向对象编程](./02-advanced-python/01-oop.md)
- [Python 数据模型](./02-advanced-python/02-data-model.md)
- [Iterator / Generator](./02-advanced-python/03-iterator-generator.md)
- [装饰器](./02-advanced-python/04-decorator.md)
- [上下文管理器](./02-advanced-python/05-context-manager.md)
- [异常系统](./02-advanced-python/06-exception-system.md)
- [类型系统](./02-advanced-python/07-typing-system.md)

### 03-engineering · Python 工程化

- [项目结构](./03-engineering/01-project-structure.md)
- [依赖与虚拟环境](./03-engineering/02-deps-venv.md)
- [测试（pytest）](./03-engineering/03-testing.md)
- [Logging](./03-engineering/04-logging.md)

### 04-systems-basics · 计算机与服务端基础

- [操作系统基础](./04-systems-basics/01-os-basics.md)
- [网络与 HTTP](./04-systems-basics/02-network-http.md)
- [并发模型](./04-systems-basics/03-concurrency-models.md)
- [数据结构与算法精要](./04-systems-basics/04-dsa-essentials.md)

### 05-async-python · Python 异步编程

- [asyncio 基础](./05-async-python/01-asyncio-fundamentals.md)
- [asyncio 进阶实践](./05-async-python/02-asyncio-advanced.md)

### 06-web-backend · Web 后端

- [Web 框架原理](./06-web-backend/01-web-framework-principles.md)
- [FastAPI + Pydantic](./06-web-backend/02-fastapi-pydantic.md)
- [认证与授权](./06-web-backend/03-auth.md)

### 07-data-persistence · 数据库与数据持久化

- [SQL 基础](./07-data-persistence/01-sql.md)
- [PostgreSQL](./07-data-persistence/02-postgresql.md)
- [Python ORM](./07-data-persistence/03-orm.md)
- [缓存与 Redis](./07-data-persistence/04-redis-cache.md)
- [消息队列基础](./07-data-persistence/05-message-queue.md)

### 08-devops-architecture · 部署、运维与软件架构

- [Linux 基础](./08-devops-architecture/01-linux-basics.md)
- [Docker 与部署](./08-devops-architecture/02-docker-deploy.md)
- [软件架构基础](./08-devops-architecture/03-software-architecture.md)

### 09-ai-llm · AI / LLM 基础与认知地图

- [AI 发展脉络与名词词典](./09-ai-llm/01-ai-landscape-glossary.md)
- [LLM API 实战](./09-ai-llm/02-llm-api.md)
- [Prompt Engineering](./09-ai-llm/03-prompt-engineering.md)
- [Structured Output](./09-ai-llm/04-structured-output.md)

### 10-rag · Embedding 与 RAG

- [Embedding 与向量检索](./10-rag/01-embedding-vector-search.md)
- [RAG 架构](./10-rag/02-rag-architecture.md)
- [RAG 实战与调优](./10-rag/03-rag-practice.md)

### 11-agent-core · Agent 核心开发

- [Tool Calling](./11-agent-core/01-tool-calling.md)
- [手写一个 Agent](./11-agent-core/02-handwritten-agent.md)
- [Agent Framework 概览](./11-agent-core/03-agent-frameworks.md)
- [LangGraph 与工作流](./11-agent-core/04-langgraph.md)
- [Agent Memory](./11-agent-core/05-agent-memory.md)
- [Multi-Agent](./11-agent-core/06-multi-agent.md)

### 12-agent-production · Agent 工程化与生产落地

- [Agent Evaluation](./12-agent-production/01-evaluation.md)
- [Observability](./12-agent-production/02-observability.md)
- [Agent Security](./12-agent-production/03-security.md)
- [Agent 系统设计](./12-agent-production/04-system-design.md)
