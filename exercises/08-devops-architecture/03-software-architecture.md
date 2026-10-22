# 练习：软件架构基础

> 对应文档：[`docs/08-devops-architecture/03-software-architecture.md`](../../docs/08-devops-architecture/03-software-architecture.md)  
> 状态：`已完成出题`  
> 建议用时：70～110 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 本章以**书面设计 + 轻量伪代码**为主；建议目录：

```text
playground/08-devops-architecture/03-software-architecture/
  layering.md
  dependency_review.md
  env.example.md
  refactor_todos.md
```

4. Python ≥ 3.11（若写接口草图）。
5. 目标：能画清 Agent API 的分层与依赖方向，而不是背名词。

---

## 热身题（建议先做）

### W1. 分层目的

**要求**：一句话说明「分层」想防止什么混乱。

**验收**：提到依赖失控 / 改一处炸一片 / 难测等。

---

### W2. 依赖方向

**要求**：内层（Domain）应不应该 import 具体 OpenAI SDK？为什么？

**验收**：不应该；应依赖抽象端口。

---

### W3. .env.example vs .env

**要求**：哪个可以进 git？哪个绝对不要？

**验收**：example 可以；真实 `.env` 不要。

---

### W4. 模块化单体

**要求**：用一句话定义「模块化单体」（本课语境）。

**验收**：单部署单元 + 内部按模块/边界拆分。

---

## 基础题（必做）

### B1. 分层图

为「带 Tool 与 LLM 的 Agent API」画出四层：

- API  
- Application  
- Domain  
- Infrastructure  

每层举 **2 个**文件/模块名示例。

**验收**：LLM SDK、DB driver 落在 Infrastructure；路由落在 API；纯规则/实体落在 Domain。

---

### B2. 依赖方向审查

判断对错并**改写**：

1. `domain/agent.py` import `openai`  
2. `api/routes.py` 直接拼 SQL  
3. `infrastructure/llm_openai.py` 实现 `domain/ports.py` 里的 `LLMClient`

**验收**：1 错、2 错、3 对；前两项给出正确依赖方向。

---

### B3. 密钥清单

1. 列 `.env.example` 应有的变量（至少 **5 个**）  
2. 列绝对不能提交的文件类型/模式（至少 **3 个**）

**验收**：含模型密钥、DB、API Key 等；含 `.env`、私钥、凭证 JSON 等。

---

### B4. 边界变更题

「把 OpenAI 换成另一家模型」应主要改哪些层？哪些层应基本不动？

**验收**：主要动 Infrastructure（+ 少量装配）；Domain/API 契约尽量不动。

---

## 进阶题（建议至少做 1 题）

### A1. 六边形一句话 + 草图

用自己的话解释端口/适配器；画一张：

- 输入适配器示例（如 FastAPI 路由）  
- 输出适配器示例（如 OpenAI LLM、Postgres）  

**验收**：应用核心不依赖适配器细节。

---

### A2. 模块化单体 vs 微服务（书面）

1. 给出你当前阶段选择**模块化单体**的 **4 个**理由  
2. 再给 **2 个**未来可能拆 worker 的触发条件  

**验收**：理由务实（认知负荷、事务、部署）；触发条件可观测（队列深度、发布节奏冲突等）。

---

## 挑战题（可选）

### C1. 重构清单

拿你现有 `playground` 里某个小项目，列 **5 条**「下一步架构改进」TODO（不必马上做完）。

**验收**：每条可执行（如「把 SQL 移出路由」），不是「写得更优雅」。

---

### C2. 端口接口草稿（代码）

用 Python Protocol 或 ABC 写一个 `LLMClient` 端口，并给一个 Fake 适配器（规则回复即可）。

**验收**：Domain/Application 只依赖端口；可单测。

---

## 模块 08 通关自检

- [ ] 会基础 Linux 排障命令
- [ ] 会 Dockerfile / compose 核心概念
- [ ] 能画清 Agent 分层与依赖方向
- [ ] 密钥管理原则清楚
- [ ] 记得：BackgroundTasks ≠ 长任务；教学 API Key `!=` ≠ 恒定时间比较；LIST+BRPOP ≠ at-least-once

完成后进入模块 09《AI / LLM 基础与认知地图》。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W4
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1 / C2

---

## 提示与参考答案（先做题再看）

### W1～W4 参考答案

- W1：防止业务、框架、IO 缠成一团导致难测难改。  
- W2：不应该；Domain 依赖 `LLMClient` 端口，由 Infrastructure 实现。  
- W3：`.env.example` 可提交；`.env` 不提交。  
- W4：一个可部署单元内部用模块边界隔离，先不分微服务。

---

### B1 思路 + 参考答案

```text
API
  - api/routes_agent.py
  - api/deps.py

Application
  - application/run_agent.py
  - application/dto.py

Domain
  - domain/agent.py
  - domain/ports.py          # LLMClient / ToolBus 接口

Infrastructure
  - infrastructure/llm_openai.py
  - infrastructure/db_pg.py
  - infrastructure/tool_http.py
```

ASCII：

```text
[API] → [Application] → [Domain]
                \           ^
                 \          | ports
                  v         |
              [Infrastructure adapters]
```

---

### B2 思路 + 参考答案

1. **错** → Domain 只依赖 `LLMClient` Protocol；`openai` 放到 `infrastructure/llm_openai.py`。  
2. **错** → 路由调 application/service；SQL 在 repository/infrastructure。  
3. **对** → 适配器实现端口，符合依赖倒置。

改写示意：

```python
# domain/ports.py
from typing import Protocol


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict: ...


# domain/agent.py
class Agent:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
```

---

### B3 思路 + 参考答案

`.env.example`：

```text
APP_ENV=dev
APP_API_KEY=
OPENAI_API_KEY=
DATABASE_URL=
REDIS_URL=
LOG_LEVEL=INFO
```

不可提交：

1. `.env` / `.env.local`  
2. `*.pem` / 私钥  
3. `credentials.json` / 云厂商密钥文件  
4. 含生产连接串的截图与笔记本附件（流程上也不要）  

---

### B4 思路 + 参考答案

主要改：

- `infrastructure/llm_*.py`（新适配器）  
- 装配/DI 处选择实现  
- （有时）配置项名字  

基本不动：

- Domain 规则、Agent 状态机  
- API 路由形状（除非供应商特性逼你改契约）  

---

### A1 思路 + 参考答案

**一句话**：端口是核心需要的能力接口；适配器是外部世界（HTTP、LLM、DB）对接端口的实现。

```text
          +------------------+
HTTP --> | Driving Adapter  |  (FastAPI routes)
          |   (inbound)      |
          +--------+---------+
                   v
          +------------------+
          | Application /    |
          | Domain (ports)   |
          +--------+---------+
                   v
          +------------------+
LLM/DB <--| Driven Adapters  |  (OpenAI, Postgres)
          |   (outbound)     |
          +------------------+
```

---

### A2 思路 + 参考答案

选模块化单体的理由：

1. 一人/小团队认知负担更低  
2. 本地调试简单，事务与一致性更容易  
3. 部署拓扑简单，先把产品跑通  
4. 过早拆微服务会引入分布式故障模式  

拆 worker 的触发条件示例：

1. Agent 长任务拖垮 API p99，需要独立扩缩 consumer  
2. 发布节奏冲突：API 日更 vs 推理 worker 周更，强绑同一进程代价过高  

---

### C1 思路 + 参考答案

示例 TODO：

1. 把 `routes.py` 里的 SQL 挪到 `repositories/message_repo.py`  
2. 为 LLM 引入 `LLMClient` Protocol + FakeLLM 测试  
3. Settings 统一从环境变量加载，消除硬编码 URL  
4. `/v1/agent/run` 长任务改为入队 + `job_id`  
5. 日志字段允许列表：禁止打印 API Key 与完整 messages  

---

### C2 思路 + 参考答案

```python
from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict: ...


class FakeLLM:
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        last = messages[-1].get("content", "") if messages else ""
        return {
            "role": "assistant",
            "content": f"fake:{last}",
            "tool_calls": [],
        }


async def run_once(llm: LLMClient, text: str) -> str:
    message = await llm.complete([{"role": "user", "content": text}])
    content = message.get("content")
    assert isinstance(content, str)
    return content


# 单测示意
# import asyncio
# assert asyncio.run(run_once(FakeLLM(), "hi")) == "fake:hi"
```

说明：这与课程 FakeLLM 契约对齐（返回 assistant message dict，而不是裸 `str`）。

---

## 附录：目录骨架示例（模块化单体）

可直接当作重构目标骨架（不必一次到位）：

```text
src/
  api/
    routes_health.py
    routes_agent.py
    deps.py
  application/
    run_agent.py
    jobs.py
  domain/
    agent.py
    ports.py
    errors.py
  infrastructure/
    llm_openai.py
    llm_fake.py
    db.py
    redis_cache.py
  main.py          # 装配：把适配器注入应用服务
```

装配示意：

```python
# main.py（示意）
from api.routes_agent import build_router
from application.run_agent import RunAgentService
from infrastructure.llm_fake import FakeLLM


def create_app():
    llm = FakeLLM()  # 生产换 OpenAIAdapter
    service = RunAgentService(llm=llm)
    app = ...
    app.include_router(build_router(service))
    return app
```

---

## 附录：依赖规则清单（可贴墙上）

1. Domain **不** import FastAPI / SQLAlchemy / OpenAI SDK  
2. API 层 **不** 直接写 SQL、不直接调 SDK（经 application）  
3. Infrastructure 可以实现端口，但不要反向被 Domain 依赖细节  
4. 配置从环境变量进入，经 Settings 注入，不在业务函数里 `os.getenv` 散落（逐步收敛即可）  
5. 长任务边界：API 入队；worker 在 application/infrastructure 执行——**不要**用 BackgroundTasks 假装架构  

与课程刻意简化对齐（复习）：

- 教学 API Key `!=` **≠** 恒定时间比较  
- Redis LIST+BRPOP **≠** at-least-once  
- BackgroundTasks **≠** 长任务  

---

## 附录：自检

- [ ] 能画出四层并举例文件  
- [ ] 能指出三道依赖题的对错  
- [ ] 能列出 `.env.example` 关键变量  
- [ ] 能说明换模型供应商时改哪些层


---

## 附录：评审用检查表（给自己 PR）

- [ ] 新依赖是进了 Infrastructure，而不是 Domain
- [ ] 路由文件没有出现 SQL 字符串
- [ ] LLM 调用经由端口，测试可注入 FakeLLM
- [ ] 配置来自环境变量 / Settings
- [ ] 长任务有 job 边界，而不是 BackgroundTasks 硬撑
- [ ] 日志不打印 API Key / 完整 messages

**口头题**：换模型供应商改哪些层？模块化单体现在为什么够用？

### 反例 → 正例（各一句）

1. 反例：`routes.py` 里 `openai.ChatCompletion` → 正例：`RunAgentService(llm: LLMClient)`
2. 反例：Domain import `sqlalchemy` → 正例：Repository 在 Infrastructure
3. 反例：同步跑 3 分钟 Agent → 正例：`POST /v1/jobs` + worker
