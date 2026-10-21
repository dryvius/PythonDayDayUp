# 软件架构基础

> 所属模块：`08-devops-architecture` · 部署、运维与软件架构  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有前端分层 / Nest 模块经验可更快；依赖方向与「模块化单体优先」建议动手画一遍）  
> 对应练习：[`exercises/08-devops-architecture/03-software-architecture.md`](../../exercises/08-devops-architecture/03-software-architecture.md)

## 本章定位

- **模块目标**：具备把服务跑起来、拆清楚边界的能力。
- **本章角色**：学会分层、模块边界、配置与密钥管理；对整洁/六边形架构建立直觉；知道微服务不该过早上。
- **和 Agent**：API、编排、工具、模型适配、持久化要分清，否则框架一换就全家重写。
- **你的优势**：前端里的「页面 / 组件 / API client / store」分层、Nest 的 module、或 Express「router 薄、service 厚」经验可以直接迁移；重点盯住 Python 侧的依赖方向与密钥边界。
- **前置**：模块 03 项目结构、模块 06 Web 后端。本章不重讲目录怎么搭、FastAPI 怎么写装饰器，只把它们接到「谁依赖谁、换什么时改哪里」。
- **刻意不做**：完整 DDD / CQRS / 事件溯源、服务网格、分布式事务框架——留给真有规模后再补；本章默认 **模块化单体优先**。

## 学习目标（学完应能做到）

1. 画出 Agent 服务的分层结构（API / Application / Domain / Infrastructure），并各举真实模块名。
2. 制定模块依赖方向规则；能审查「Domain 是否直接 import 厂商 SDK」。
3. 正确管理配置与密钥（`.env.example` vs 真密钥、集中读取、日志脱敏、轮换）。
4. 用自己的话解释端口/适配器直觉；知道何时不该拆微服务。
5. 能画一张「模块化单体 + 可选 Worker」参考草图，并说明拆分触发条件。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 分层架构、模块边界、配置与密钥 | 能落地小项目结构，能审查依赖方向 |
| **建议掌握** | 六边形/整洁架构直觉 | 能听懂、能渐进采用「可替换适配器」缝 |
| **了解即可** | 微服务何时该拆 | 防过早拆分；认同模块化单体优先 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要软件架构？

Agent 项目一旦超过「一个脚本调完 LLM」，会同时出现这些变化源：

```text
HTTP API 形状会变（路由、鉴权、流式）
编排策略会变（多步循环、重试、工具选择）
工具会增删（search / calc / browse）
模型供应商会换（OpenAI → 另一家 / 本地）
存储会换（SQLite → Postgres；加 Redis / 向量库）
部署形态会变（本机 → Docker → 多副本）
```

没有架构时，常见结局是：

| 症状 | 背后缺什么 |
| --- | --- |
| 换模型要改 route、改 prompt、改 DB 三处 | 没有分层 / 端口 |
| 改表结构拖垮编排单测 | Domain 绑死了 SQL |
| 密钥写进仓库、日志里打出 API Key | 配置与密钥无边界 |
| 一人项目先拆成 8 个微服务 | 把「进程边界」当成「模块边界」 |

有架构时，同一件事通常长这样：

```text
改模型供应商  →  只动 infrastructure/llm 适配器
加一个 Tool   →  注册新工具，编排核心不动
换 Postgres   →  换 repository 实现，用例签名不变
本地 / 生产   →  同一代码，不同环境变量与密钥源
```

#### 怎么理解本章要解决的问题

模块 03 告诉你文件放哪；模块 06 告诉你请求怎么进门。  
本章回答四句话：

1. **分层**：请求进门后，业务规则落在哪一层？
2. **边界**：改动应落在哪个目录，不该「涟漪」到哪？
3. **配置与密钥**：什么进仓库，什么绝不能进？
4. **演进**：先模块化单体，什么信号才值得拆进程/服务？

可以先记一句：

> 软件架构的核心不是画漂亮箱子，而是让「换供应商、加工具、改存储、换部署」的改动面可预期——**模块化单体优先，按需拆分**。

#### 示例：同一功能，两种放法

```python
# ❌ 全写在 route：换模型 / 换 DB / 加鉴权都会改同一文件
@app.post("/run")
async def run(body: dict):
    import openai
    client = openai.OpenAI(api_key="sk-...")  # 密钥还写死了
    text = client.chat.completions.create(...).choices[0].message.content
    conn.execute("INSERT INTO runs ...", text)
    return {"answer": text}
```

```python
# ✅ 分层后：route 只翻译 HTTP；用例编排；端口抽象 LLM/DB
@app.post("/run")
async def run(body: RunRequest, use_case: RunAgent = Depends(...)):
    result = await use_case.execute(body.question)
    return RunResponse(answer=result.answer)
```

第二种未必一开始就「完整六边形」，但已经留出了缝：HTTP、用例、适配器可以分开换。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把架构当成「目录改名仪式」 | 依赖方向仍乱，只是文件夹更多 |
| 一上来抄完整 Clean Architecture 样板 | 空接口满天飞，交付变慢 |
| 用微服务解决「代码乱」 | 乱被放大成网络与分布式一致性问题 |

#### 前端架构对照（先建立地图）

| 你在前端熟悉的 | 本章后端 / Agent 侧 |
| --- | --- |
| 页面薄、业务进 composable / store | route 薄、业务进 application / domain |
| `api/` client 可换 axios / fetch | `infrastructure/` 适配器可换 SDK |
| 组件不直接 `localStorage` 散落 | Domain 不直接 `os.getenv` / 厂商 SDK |
| 功能模块（`features/chat`） | 业务模块边界（agents / tools / memory） |
| 先 monorepo 包，再拆独立部署 | 先模块化单体，再拆 worker / 服务 |

---

## 2. 必掌握：分层架构（Agent 版）

这一节会刻意写细——分层是后面模块边界、六边形直觉、参考草图的共同底座。

### 2.1 四层地图（推荐起点）

#### 为什么需要分层？

同一请求里混着「HTTP 细节、用例步骤、业务规则、厂商 SDK」时，任何一处变化都会牵全身。  
分层把**变化速度不同**的东西分开：API 形状常变，领域规则相对稳，基础设施最爱换。

#### 怎么理解 / 怎么画

推荐起点（本路线 Agent 服务默认）：

```text
API 层            FastAPI routes / schemas / Depends
Application 层    用例：run_agent / create_job / cancel_job
Domain 层         Agent/Tool 抽象、纯规则、端口（接口）
Infrastructure 层 LLM SDK、DB、Redis、队列、搜索、对象存储
```

依赖方向（先背这个，再谈名词）：

```text
允许：
  API            → Application（偶尔 → Domain 的 DTO/类型）
  Application    → Domain（端口与纯规则）
  Infrastructure → 实现 Domain 端口（向内适配）

禁止：
  Domain         → FastAPI / SQLAlchemy / openai / redis 客户端细节
  Domain         → API schemas
  Application    → 某家 LLM SDK 的具体类（应通过端口）
```

心智图：

```text
        外
┌───────────────────┐
│  API（进来/出去）   │  翻译 HTTP ↔ 用例输入输出
├───────────────────┤
│  Application      │  编排步骤：校验 → 调端口 → 组结果
├───────────────────┤
│  Domain           │  规则 + 端口定义（“要什么能力”）
├───────────────────┤
│  Infrastructure   │  端口的真实实现（“怎么做到”）
└───────────────────┘
        内（更稳、更纯）
```

#### 示例：每层放什么（Agent 语境）

| 层 | 放什么 | 不放什么 | 文件名举例 |
| --- | --- | --- | --- |
| API | 路由、Pydantic 请求/响应、鉴权 Depends、状态码映射 | 长编排、拼 SQL、直接调 SDK | `api/routes/agent.py`、`api/schemas.py` |
| Application | 用例类/函数：一步步调用端口 | FastAPI 装饰器、厂商 SDK 细节 | `application/run_agent.py` |
| Domain | `AgentSession` 规则、Tool 协议、`LLMClient` 端口 | `import openai`、拼 HTTP | `domain/ports.py`、`domain/agent.py` |
| Infrastructure | OpenAI 适配、Postgres repository、Redis、队列生产者 | 业务 if/else 规则堆这里 | `infrastructure/llm_openai.py`、`infrastructure/db.py` |

最小端口形状（与仓库约定对齐，模块 09 起强制）：

```python
# domain/ports.py（示意）
from typing import Protocol


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:  # assistant_message
        ...


class Tool(Protocol):
    name: str

    async def run(self, arguments: dict) -> str:
        ...
```

```python
# application/run_agent.py（示意：编排，不碰 SDK）
class RunAgent:
    def __init__(self, llm: LLMClient, tools: list[Tool]) -> None:
        self._llm = llm
        self._tools = {t.name: t for t in tools}

    async def execute(self, question: str) -> str:
        messages = [{"role": "user", "content": question}]
        message = await self._llm.complete(messages, tools=None)
        return str(message.get("content") or "")
```

```python
# infrastructure/llm_fake.py（示意：可测、无 Key）
class FakeLLM:
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        last = messages[-1]["content"] if messages else ""
        return {"role": "assistant", "content": f"ECHO: {last}"}
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| Domain 直接 `import openai` | 换厂商 / 单测无 Key 时 Domain 全军覆没 |
| 业务规则写进 route 函数 | OpenAPI 一变，规则跟着搬家；单测要起 ASGI |
| Application 里到处 `os.getenv` | 配置散落，环境差异变玄学 |
| 以为「四层目录」= 架构完成 | 目录对了但依赖反了，等于没分层 |

#### 前端架构对照

| 前端分层直觉 | Agent 后端分层 |
| --- | --- |
| `pages` / `views`（路由出口） | API 层 |
| composable / use-case 服务 | Application 层 |
| 领域类型、校验、纯函数 | Domain 层 |
| `api/http.ts`、SDK、IndexedDB 封装 | Infrastructure 层 |
| UI 不直接 `fetch` 散落（理想态） | Domain 不直接碰框架与驱动 |

NestJS 里常见的 `Controller → Service → Repository`，和这里的 `API → Application → (Domain ports ← Infrastructure)` 同构；差别是我们把「端口」显式留在 Domain，方便换 FakeLLM。

---

### 2.2 依赖方向：向内稳定，向外可换

#### 为什么要把方向钉死？

分层失败 90% 不是「少写了一个文件夹」，而是**箭头反了**：

```text
domain/agent.py  →  import openai          # 内层依赖外层细节
api/routes.py    →  直接拼 SQL             # 入口穿透持久化
tools/search.py  →  import agents.runner   # 工具反绑编排 → 循环依赖
```

#### 怎么画（审查清单）

画依赖时只问一句：**这个模块换掉时，谁必须改？**

```text
换 FastAPI → 应主要动 API（+ 组装）
换 OpenAI  → 应主要动 infrastructure/llm_*
换 Postgres → 应主要动 infrastructure/repo_*
改「最多几步工具循环」规则 → 应主要动 Domain / Application
```

允许的箭头：

```text
API ──────────────► Application ──────► Domain
                         ▲                 ▲
                         │                 │
              Infrastructure 实现端口 ──────┘
```

组装点（`main` / DI 容器）可以同时看见各层，负责「接线」——这是例外，不是让业务到处 import `main`。

#### 示例：三种审查题（对接练习 B2）

```python
# 1) ❌ Domain 依赖厂商
# domain/agent.py
import openai  # 禁止

# ✅ Domain 只依赖端口；实现放 infra
# domain/ports.py 定义 LLMClient
# infrastructure/llm_openai.py 实现 complete(...)
```

```python
# 2) ❌ API 直接拼 SQL
# api/routes.py
conn.execute("SELECT ...")  # 禁止

# ✅ API → 用例 → repository 端口
result = await get_run_use_case.execute(run_id)
```

```python
# 3) ✅ Infra 实现 Domain 端口
# infrastructure/llm_openai.py
class OpenAILLM:
    async def complete(self, messages, tools=None, **kwargs) -> dict:
        ...
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用「延迟 import」长期掩盖循环依赖 | 能跑，但边界已烂；下次必炸 |
| 把 Domain 做成「只有 dataclass，没有规则」 | 规则仍堆在 route / infra，分层名存实亡 |
| 让 Application 返回 ORM 对象给 API | API 被 SQLAlchemy 会话生命周期绑死 |

#### 前端架构对照

前端 ESLint 的 `import/no-cycle`、`boundaries` 插件，和这里的依赖方向是同一问题：  
**features 不依赖 pages；shared 不依赖 features**。  
后端把同样的规则落到包导入上即可。

---

### 2.3 小项目可以少目录，但不能少方向

#### 为什么允许「简化版」？

三人以下、功能未稳时，硬上完整四层 + 端口接口，容易变成空壳。  
但「API 里直接 openai + SQL」也会很快还债。折中：**目录可简，箭头要想清**。

#### 怎么理解

| 阶段 | 可用布局 | 仍必须遵守 |
| --- | --- | --- |
| 玩具 / 练习 | 单文件或 `api / services` | LLM 调用别写死密钥；业务别全塞 route |
| 小项目 | `api / services / adapters` | services 编排；adapters 接 SDK/DB |
| 中型 Agent | 完整 `api / application / domain / infrastructure` | 端口 + FakeLLM 可测 |

```text
小项目简化版（方向仍对）：

api/          →  调 services
services/     →  编排；依赖 adapters 的接口或注入实例
adapters/     →  openai / db / redis
```

这和完整四层同构：`services ≈ application(+部分 domain)`，`adapters ≈ infrastructure`。

#### 示例

```python
# services/run_agent.py —— 接收已构造好的 llm，而不是内部 new OpenAI()
async def run_agent(question: str, llm, tools: list) -> str:
    message = await llm.complete([{"role": "user", "content": question}])
    return str(message.get("content") or "")
```

组装仍在入口：

```python
# main 或 api 依赖注入处
llm = FakeLLM()  # 或 OpenAILLM(settings)
answer = await run_agent(question, llm, tools)
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 「小项目所以到处 `os.getenv` + 直接 SDK」 | 小项目长成中项目时无缝可拆 |
| 过早建 20 个空接口 | 阅读成本高于收益 |

#### 前端架构对照

前端也常见：Demo 可以 `fetch` 写在组件里；上线前收敛到 `api/` + composable。  
**收敛时机看痛点，不是看日历**——但密钥与纯规则尽早别和 UI/route 焊死。

---

## 3. 必掌握：模块边界

分层是「纵向切」（技术角色）；模块边界是「横向切」（业务能力）。两者要一起用。

### 3.1 好边界的信号

#### 为什么需要模块边界？

只有分层时，仍可能出现「巨大的 application 上帝包」：所有用例、所有工具、所有记忆逻辑挤在一起。  
模块边界回答：**按业务能力切开后，改 A 不该读懂 B 的内脏**。

#### 怎么理解 / 怎么画

好边界的信号（可当验收句）：

```text
改模型供应商     → 只动 infrastructure/llm（或 adapters/llm）
改表结构         → 主要动 repository / migrations
工具可插拔注册   → 不改编排核心（runner 只认 Tool 端口）
加一种 Memory    → 新适配器 + 注册，不改 Domain 用例签名
```

坏边界的信号：

```text
改一个 Tool 要改 AgentRunner 内部 10 处 if
repository 被 6 个包直接 import 私有 SQL 细节
「工具」模块 import 「编排」模块，形成环
```

目录可与工程化章呼应：

```text
app/
  api/
  application/
  domain/
  infrastructure/
```

也可以按能力再切一刀（模块化单体常见）：

```text
app/
  api/
  agent_runtime/     # 编排用例 + domain
  tools/
  memory/
  infrastructure/    # 共享适配器（llm/db/queue）
```

关键不是名字，而是：**跨模块只走公开入口，不钻私有文件**。

#### 示例：工具可插拔

```python
# domain/ports.py
class Tool(Protocol):
    name: str

    async def run(self, arguments: dict) -> str: ...


# application/registry.py
def build_tool_map(tools: list[Tool]) -> dict[str, Tool]:
    return {t.name: t for t in tools}


# infrastructure/tools/echo.py
class EchoTool:
    name = "echo"

    async def run(self, arguments: dict) -> str:
        return str(arguments.get("text", ""))
```

编排只依赖 `Tool` 端口与注册表，不 `import` 某个工具的私有实现细节。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 按「文件类型」切（全是 utils/helpers） | 找不到业务归属，人人往 utils 扔 |
| 模块互相直读对方表/内部函数 | 边界是纸糊的 |
| 为每个 Python 文件建一个「模块」 | 粒度过碎，编排成本爆炸 |

#### 前端架构对照

| 前端 | 后端 Agent |
| --- | --- |
| `features/chat`、`features/settings` | `agent_runtime`、`tools`、`memory` |
| feature 对外导出 `index.ts` | 模块对外导出用例 / facade |
| 禁止跨 feature 深挖 `internal/` | 禁止跨包 import 私有 repository 细节 |
| 共享 UI 进 `shared/` | 共享 infra 进 `infrastructure/` |

---

### 3.2 变更风暴测试（用改动验证边界）

#### 为什么需要「变更风暴」？

边界好不好，不能只看目录树，要看**一次真实变更的涟漪半径**。

#### 怎么画

拿四类变更做桌面推演（纸上写「会改哪些文件」）：

| 变更 | 理想涟漪 | 若涟漪过大说明 |
| --- | --- | --- |
| 换 LLM 供应商 | infra + 组装 | Domain/API 被 SDK 污染 |
| 给 API 加字段 | API schemas + 少量用例 DTO | 表结构/SDK 被误伤 |
| 新增 Tool | 新工具文件 + 注册一行 | Runner 出现新 if 分支地狱 |
| 把同步改成队列异步 | application 入口 + worker 组装；Domain 复用 | Domain 写死了「必须在 HTTP 请求里跑完」 |

#### 示例：换模型供应商的正确涟漪

```text
应改：
  infrastructure/llm_openai.py → llm_other.py
  main / DI 组装处选择实现
  （可选）配置项 MODEL_PROVIDER

基本不动：
  domain/ports.py 的 LLMClient 形状
  application/run_agent.py 的步骤
  api/routes 的路径与鉴权
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用「复制一份 OpenAI 调用到新文件」假装可替换 | 两处逻辑漂移，端口形同虚设 |
| 在 Domain 里写 `if provider == "openai"` | 供应商判断进了核心，永远撕不掉 |

#### 前端架构对照

前端换图表库（ECharts → 另一家）时：理想是只换 `shared/charts` 适配层；若每个页面都直接 `import echarts`，就是边界失败——和 Domain 直接 import SDK 同一病。

---

### 3.3 打断循环依赖

#### 为什么循环依赖是架构报警灯？

```text
A import B
B import A
```

短期可用函数内 import「续命」，长期说明**职责黏在一起**：该抽端口、该下沉共享模型、或该合并模块。

#### 怎么理解

常见 Agent 环：

```text
agents.runner → tools.search → agents.runner   # 工具回调编排
domain.models → infrastructure.db → domain.models
api.schemas ←→ domain.entities（互相转换却双向 import）
```

打断手法（按优先级）：

1. **依赖倒置**：双方依赖端口/协议，而不是彼此具体类
2. **下沉共享**：把 Message / RunId 放到更稳的 `domain` / `models`
3. **合并**：若两个「模块」总是一起改，可能本就是一个模块
4. **组装上移**：创建顺序放到 `main`，不要在叶子模块互相 new

#### 示例

```python
# ❌ tools 为了「跑完通知 Agent」去 import runner
# ✅ tool 只返回字符串；由 application 决定下一步
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用 `TYPE_CHECKING` 长期掩盖设计问题 | 类型过了，运行时边界仍糊 |
| 把所有东西塞进一个 `types.py` 巨型文件 | 环是没了，内聚也没了 |

#### 前端架构对照

前端 `store` ↔ `api` ↔ `component` 循环，和这里同构：把「事件/回调」改成单向数据流，或把共享类型下沉到 `types/`。

---

## 4. 必掌握：配置与密钥管理

架构分层解决「代码依赖」；配置与密钥解决「环境与秘密依赖」。两者同等重要。

### 4.1 什么进仓库，什么绝不进

#### 为什么要分清？

密钥进 Git 的代价不是「尴尬」，而是：**泄露即资产失守**，且历史难擦干净（即使后来删除，clone 过的人仍可能有）。

#### 怎么理解

| 该进仓库 | 不该进仓库 |
|----------|------------|
| `.env.example`（变量名 + 假值/说明） | `.env` 真密钥 |
| 默认非秘密配置（超时、模型名默认值） | 生产连接串密码、API Key、Webhook Secret |
| 架构文档、compose 示意 | 私钥、证书明文、生产 dump |
| CI 用的「假密钥」说明 | 云账号长期凭证明文 |

12-factor 核心句（配置章反复出现）：

> **配置来自环境；同一镜像/同一构建，靠环境差异区分本地与生产。**

#### 示例：`.env.example`（对接练习 B3）

```text
# .env.example —— 可提交
APP_ENV=dev
APP_API_KEY=replace-me
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/agent
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY=replace-me
LLM_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

```text
# .env —— 不提交（进 .gitignore）
APP_API_KEY=真实值...
LLM_API_KEY=sk-真实值...
DATABASE_URL=postgresql+psycopg://user:真实密码@db:5432/agent
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把 `.env` 当「示例」提交 | 密钥进历史 |
| 只教 `.gitignore` 却不提供 `.env.example` | 别人不知道要配什么 |
| 在文档/截图里贴真实 Key | 和提交仓库一样危险 |

#### 前端架构对照

| 前端 | 后端 |
| --- | --- |
| `VITE_*` / `NEXT_PUBLIC_*` 可进浏览器 | 浏览器可见 ≠ 可当密钥 |
| 前端环境变量仍可能被打包进静态资源 | **LLM Key、DB 密码只放服务端** |
| `.env.local` 不提交 | `.env` 不提交 |
| 前端只拿「匿名可暴露」配置 | 后端用 Secret 源注入 |

Agent 场景特别危险：有人把 `LLM_API_KEY` 塞进前端 env「图省事」——等于把钱包挂在 CDN 上。

---

### 4.2 集中读取：一处 Settings，别处注入

#### 为什么不能到处 `os.getenv`？

散落读取会导致：

1. 默认值不一致（有的 `0`，有的 `None`）
2. 缺变量时有的启动炸、有的运行到半路才炸
3. 测试难以统一打桩
4. 日志/文档无法列出「完整配置面」

#### 怎么写

```python
# app/config.py（示意）
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_api_key: str
    database_url: str
    redis_url: str
    llm_api_key: str
    llm_model: str
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        def must(name: str) -> str:
            value = os.getenv(name)
            if not value:
                raise RuntimeError(f"missing env: {name}")
            return value

        return cls(
            app_env=os.getenv("APP_ENV", "dev"),
            app_api_key=must("APP_API_KEY"),
            database_url=must("DATABASE_URL"),
            redis_url=must("REDIS_URL"),
            llm_api_key=must("LLM_API_KEY"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
```

用法：

```text
main / lifespan / DI
  → settings = Settings.from_env()
  → 把 settings.llm_api_key 传给 OpenAILLM(...)
  → 业务函数接收 Settings 或更窄的依赖，而不是自己 getenv
```

本地可用 dotenv 在进程启动时加载；生产用平台注入（云 Secret / K8s Secret / CI variables）。

#### 示例：组装时注入，而不是业务里偷读

```python
# ✅
llm = OpenAILLM(api_key=settings.llm_api_key, model=settings.llm_model)

# ❌ 在 domain 或 tool 深处
api_key = os.getenv("LLM_API_KEY")
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| Domain 读取环境变量 | 核心规则绑死部署环境 |
| 配置类可变且全局单例乱改 | 测试互相污染 |
| 把「非秘密默认值」和「密钥」混在同一硬编码文件 | 人一复制给同事就泄密 |

#### 前端架构对照

前端也有「集中 config」：`import.meta.env` 读完放进 `config.ts`，业务引用 `config.apiBase`，而不是每个组件自己 `import.meta.env.VITE_API_BASE`。  
心智相同：**读环境一处化，使用注入化**。

---

### 4.3 日志脱敏、轮换与泄露应对

#### 为什么配置章必须谈日志？

Agent 最容易把密钥打进日志：请求头、异常 `repr`、把整个 `messages` 丢进 debug。  
架构上「密钥不进仓库」却在日志里明文，等于侧门打开。

#### 怎么理解（最小纪律）

```text
1. 永远不要 log settings 整个对象（可能含 key）
2. Authorization / api_key / password 字段脱敏：只留前后缀或哈希
3. 生产默认 INFO；DEBUG 慎开且勿持久化敏感对话到不安全位置
4. 泄露即作废：轮换 Key，撤销旧 Key，检查审计日志
5. 权限最小化：CI / 预发 / 生产用不同密钥
```

轮换策略（了解并做到「会执行」）：

```text
怀疑泄露 → 立即在供应商控制台作废
         → 生成新 Key 注入 Secret 源
         → 滚动重启服务
         → 复查 git 历史 / 日志 / 聊天记录是否残留
```

#### 示例：脱敏示意

```python
def redact_secret(value: str, keep: int = 3) -> str:
    if len(value) <= keep * 2:
        return "***"
    return f"{value[:keep]}***{value[-keep:]}"


# log: api_key=sk-***xyz
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 用「教学用恒定时间比较」那套不当真 | 生产鉴权仍应用安全比较（见 CONVENTIONS 刻意简化） |
| 密钥写进 Docker 镜像 `ENV` 层 | 镜像分发即泄露；应用运行时注入 |
| 多人共用一把长期生产 Key | 无法追责、轮换牵一发而动全身 |

#### 前端架构对照

浏览器会把前端 env 打进包；后端则要防日志与镜像层。  
共同原则：**秘密不进可分发产物**（静态资源、镜像层、公开仓库、错误页）。

---

## 5. 建议掌握：六边形 / 整洁架构直觉

不要求一上来完整 Hexagonal；但要留下「可替换适配器」的缝。

### 5.1 一句话与一张图

#### 为什么需要这套直觉？

分层告诉你「上下」；六边形告诉你「内外」：  
**业务核心不依赖框架与驱动；框架与驱动依赖业务定义的端口。**

整洁架构（Clean Architecture）与六边形在教学上可先当成同一家族：  
都强调依赖指向内层、外层可替换。

#### 怎么理解 / 怎么画

```text
              ┌─────────────────────────┐
  HTTP ──────►│  入站适配器（Driving）    │
  CLI  ──────►│                         │
  Worker ────►│        Domain           │
              │     （端口 + 规则）       │
  DB   ◄──────│  出站适配器（Driven）    │
  LLM  ◄──────│                         │
  Queue◄──────│                         │
              └─────────────────────────┘
```

名词对照（别被英文吓到）：

| 说法 | 含义 | Agent 例子 |
| --- | --- | --- |
| 端口 Port | 核心需要的能力契约 | `LLMClient.complete`、`MemoryStore.save` |
| 入站适配器 | 把外部请求翻译成用例调用 | FastAPI route、CLI、定时触发 |
| 出站适配器 | 把端口实现成真实 IO | OpenAI SDK、Postgres、Redis、搜索 HTTP |
| 依赖倒置 | 内层定义接口，外层实现 | Domain 定义端口，Infra 实现 |

#### 示例：同一用例，两种入站

```text
HTTP POST /v1/agent/run  ──►  RunAgent.execute(question)
CLI  `python -m app run "..."` ──►  RunAgent.execute(question)
Worker 消费 job 载荷      ──►  RunAgent.execute(question)
```

三种入站适配器，**复用同一 Domain / Application**——这就是六边形的获得感。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 为每个函数建接口「看起来很整洁」 | 过度抽象，改不动 |
| 只画六边形海报，依赖仍向外 | 名词正确，结构错误 |
| 把 Framework 当 Domain | 「我们的业务就是 FastAPI」——换框架即重写 |

#### 前端架构对照

| 六边形概念 | 前端近似 |
| --- | --- |
| 入站适配器 | 路由页面、用户事件处理 |
| 出站适配器 | `api/` HTTP client、本地缓存适配 |
| 端口 | `ChatRepository` 接口 / composable 依赖的抽象 |
| Domain | 纯函数校验、会话状态规则（不碰 Vue/React API） |

前端「可换 UI、可换请求库」与后端「可换 HTTP、可换 LLM」是同一肌肉。

---

### 5.2 渐进采用：先留缝，再补接口

#### 为什么不要第一天完整落地？

完整端口/适配器在大型系统有回报；在一周玩具项目里，空 `Protocol` 可能只是噪音。  
渐进策略：

```text
第 1 步：编排接收 llm/tools 注入（构造注入）——已有缝
第 2 步：单测用 FakeLLM ——逼你稳定 complete 契约
第 3 步：抽出 Protocol / ABC 放 domain/ports
第 4 步：多入站（HTTP + Worker）复用同一用例
```

#### 怎么理解「缝」长什么样

```python
# 有缝：可替换
class RunAgent:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

# 无缝：焊死
class RunAgent:
    def __init__(self) -> None:
        self._llm = OpenAI(...)  # 内部 new 具体类
```

#### 示例：FakeLLM 逼出端口形状

无 API Key 时用 FakeLLM 跑通工具环与评测（见 `docs/CONVENTIONS.md`）。  
当你能在 CI 里用 FakeLLM 绿时，端口形状就已经「被测试钉住」了——这比先画 UML 更实在。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 先写 15 个空适配器再写业务 | 交付延期，接口与真实需求脱节 |
| 测试也打真模型 | CI 不稳、费钱、无法复现 |

#### 前端架构对照

前端也是：先把 `fetch` 收进 `api/client.ts`（缝），再在需要时抽 `ChatApi` 接口给 mock——不必第一天上完整 clean architecture 文件夹宗教。

---

### 5.3 整洁架构同心圆（与分层对照）

#### 为什么还要提同心圆？

你会在文章里看到「Entities / Use Cases / Interface Adapters / Frameworks」。  
把它映射回本路线四层，避免学两套互相打架的词汇。

#### 怎么画（对照表）

| 整洁架构常见环 | 本路线四层 | Agent 落点 |
| --- | --- | --- |
| Entities | Domain 实体/规则 | Session、Tool 契约、限额规则 |
| Use Cases | Application | `RunAgent`、`CreateJob` |
| Interface Adapters | API schemas + 部分 infra 转换 | Pydantic ↔ 用例 DTO；ORM ↔ domain |
| Frameworks & Drivers | Infrastructure + FastAPI 本身 | uvicorn、SDK、DB 驱动 |

依赖规则同一句：**源码依赖只能指向内圆**。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把「目录名叫 usecases」当成已整洁 | 用例里仍直接 SQL/SDK |
| 强行翻译每一本架构书的术语 | 团队沟通成本上升；本路线认准四层 + 端口即可 |

#### 前端架构对照

前端的「domain → application → adapters → UI framework」讨论，和同心圆是同一张图；Vue/React 属于最外环，不应渗入纯规则。

---

## 6. 了解即可：微服务何时该拆

默认立场先写在前面：

> **模块化单体优先。**  
> 先把进程内的模块边界做对；只有证据充分时，再把某个模块拆成独立进程/服务。

### 6.1 先别拆的信号

#### 为什么默认不拆？

拆成微服务，你立刻买到这些账单：

```text
网络延迟与重试
子超时与级联失败
分布式追踪
跨服务数据一致性（别想着随手 join）
本地开发要起一堆依赖
版本兼容与发布编排
```

一人项目或边界尚不清时，这些成本通常高于收益。

#### 怎么理解

先别拆的信号：

- 团队很小、甚至一人项目
- 边界尚不清（说不清模块公开 API）
- 没有独立扩展 / 独立发布的真实需求
- 还在频繁改领域模型（拆了只会双倍重构）
- 运维与观测还没跟上（没有统一日志/指标/追踪）

错误示范：把每个 Python 文件变成微服务。  
正确路径：**模块化单体 → 按需拆 worker/服务**。

#### 示例：模块化单体里的「逻辑服务」

```text
同一仓库、同一部署单元（一个 API 进程 + 可选同仓 Worker）

app/
  agent_runtime/   # 逻辑模块 A
  tools/           # 逻辑模块 B
  memory/          # 逻辑模块 C
  infrastructure/

进程内函数调用 = 事务简单、调试简单、重构便宜
模块边界清晰后，未来拆进程只是「换运输方式」
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 「大厂都微服务，所以我也要」 | 小团队被分布式拖死 |
| 用微服务证明架构能力 | 能力应体现在边界与演进，不是进程数 |

#### 前端架构对照

前端「先拆 10 个微前端」和后端「先拆 10 个微服务」是双胞胎错误。  
常见正解：先 monorepo / 模块化前端，按团队与发布节奏再拆独立部署单元。

---

### 6.2 可以考虑拆的信号

#### 为什么有时又该拆？

当**独立性的价值**稳定地高于**分布式的成本**时：

- 不同部分独立扩缩（例如重 embedding / 文档解析 worker，CPU/GPU 与 API 不同）
- 不同团队所有权清晰，且需要独立发布节奏
- 故障隔离需求强（工具执行失控不能拖垮在线 API）
- 技术栈必须分家（极少见；先怀疑自己）

#### 怎么理解（优先拆 Worker，而不是拆「小 HTTP 服务蜘蛛网」）

Agent 常见演进：

```text
1) 同步 API 内跑完 Agent          （最简单）
2) API 入队 + 同仓 Worker 消费    （模块化单体的异步形态）
3) Worker 独立扩缩部署            （仍可同仓，进程分离）
4) 少数边界极稳的能力独立成服务    （真微服务）
```

多数团队长期停在 2）或 3）就够了。

#### 示例：该拆 Worker 的触发条件

```text
- LLM / 工具步骤经常 > HTTP 网关超时
- 需要重试、并发限流、优先级队列
- 高峰时只想扩「跑任务的进程」，不想盲扩 Web
```

```text
API 进程：收请求、鉴权、入队、查状态
Worker 进程：跑 RunAgent（复用同一 domain/application）
两者共享：domain、ports、大部分 infrastructure 客户端封装
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| API 与 Worker 复制两份编排代码 | 行为分叉；修 bug 只修一边 |
| 一拆就上分布式事务 / 两阶段提交 | 复杂度暴涨；先用「状态机 + 幂等 + 重试」 |
| 按技术层拆服务（auth 服务、db 服务） | 每次业务改动跨服务连环改 |

#### 前端架构对照

「BFF 单独部署」有时值得；「每个按钮一个微前端」不值得。  
用发布/扩缩/故障域说话，不用时髦词说话。

---

### 6.3 决策表（出门前看一眼）

| 问题 | 若答案偏「是」 | 倾向 |
| --- | --- | --- |
| 模块公开 API 稳定吗？ | 否 | 留在单体 |
| 是否真有独立扩缩指标？ | 否 | 留在单体 |
| 团队是否按边界所有权划分？ | 否 | 留在单体 |
| 是否已有观测与 on-call？ | 否 | 先补工程，再谈拆 |
| 是否只是「想异步」？ | 是 | 先同仓 Worker |
| 是否故障域必须隔离？ | 是 | 可拆进程/服务 |

口诀：

> **先模块，后进程；先同仓 Worker，后微服务。**

---

## 7. Agent 参考架构草图

把前面所有块拼成可画在白板上的一张图。

### 7.1 模块化单体（默认推荐）

#### 为什么这张图是默认？

它同时满足：本地好跑、边界清晰、测试可用 FakeLLM、未来能拆 Worker——而不强迫你一上来分布式。

#### 怎么画

```text
Client (Web / 其它服务)
  │  HTTP
  ▼
API Gateway / 反代（可选）
  │
  ▼
FastAPI（API 层）
  │  鉴权 / schemas
  ▼
Agent Application（用例编排）
  │
  ├── Tool ports ──────────────► Tool adapters（search/calc/...）
  ├── LLM port ────────────────► Provider SDK / FakeLLM
  ├── Memory port ─────────────► PG / Redis / Vector DB
  └── Job port（可选）──────────► Queue（Redis/SQS 等）
  │
  ▼
Infrastructure 实现以上端口
```

目录落位（一种常见画法）：

```text
app/
  api/                 # 入站适配器：HTTP
  application/         # 用例
  domain/              # 规则 + ports
  infrastructure/
    llm/
    db/
    redis/
    tools/
  main.py              # 组装
```

#### 示例：一次同步 `/run` 的调用链

```text
POST /v1/agent/run
 → api.routes 校验 + 鉴权
 → application.RunAgent.execute
 → domain 规则（步数/工具允许列表）
 → llm.complete（port）
 → （如有 tool_calls）tool.run（port）
 → memory.save（port，可选）
 → 返回 API schema
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把草图当成必须原样抄的目录宗教 | 小项目可用简化版，但箭头不能反 |
| Client 直连数据库「跳过 API」 | 边界与鉴权全丢 |

#### 前端架构对照

```text
Browser
  → BFF/API
      → application/usecase
          → ports
      → adapters

≈

Browser
  → pages
      → composables / stores
          → api client 端口
      → real HTTP / mock
```

---

### 7.2 可选 Worker：同仓异步，仍是模块化单体

#### 为什么 Worker 常常比「新微服务」更合适？

Agent 步骤慢、要重试——这是**执行模型**问题，不一定是**服务拆分**问题。  
同仓 Worker 复用同一 Domain，避免两套业务。

#### 怎么画

```text
Client
  → FastAPI
      → CreateJob（application）
          → 入队（Job port）
          → 立即返回 job_id

Worker（可选，同仓代码）
  → 消费队列
  → 调用同一个 RunAgent（domain/application 复用）
  → 写状态到 DB（Memory/Run repository）

Client 轮询或 WebSocket/SSE 取结果
```

```text
部署视图（仍可很简单）：

[ api 容器 ] ──队列──► [ worker 容器 ]
      │                     │
      └────── 同一镜像/同一包 ─┘
              不同 CMD
```

Docker 章的 compose 可以把 `api` 与 `worker` 写成两个 service、同一 build——这就是模块化单体的多进程形态。

#### 示例：职责切割

| 进程 | 负责 | 不负责 |
| --- | --- | --- |
| API | 鉴权、校验、入队、查状态 | 长时间工具循环 |
| Worker | 跑编排、重试、限流 | 对外暴露复杂业务路由（通常） |

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| Worker 里重新实现一套 prompt/工具逻辑 | 双源真相 |
| 用 FastAPI `BackgroundTasks` 扛长任务 | 进程一挂任务丢；长任务请上队列（见 CONVENTIONS） |

#### 前端架构对照

前端「点击后先返回任务 id，再轮询进度」，对应的就是 API+Worker；  
UI 不关心任务在哪个进程跑，只关心状态协议稳定。

---

### 7.3 以后真拆服务时，草图怎么变

#### 为什么先画「以后」，却不现在做？

为了证明：**现在的模块边界是为未来搬家服务的**；不是现在就搬家。

#### 怎么理解

```text
今天（模块化单体）：
  agent_runtime / tools / memory  同进程，函数调用

明天（证据充足时）：
  embedding-worker 独立扩缩
  或 tool-runner 独立故障域

搬家手法：
  把某个出站适配器后面的实现，换成「HTTP/gRPC 客户端适配器」
  Domain 端口签名尽量不动
```

这就是「先留缝」的长期回报。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 还没同仓模块化就先拆 | 分布式大泥球 |
| 拆完仍共享一个数据库强耦合表 | 微服务外壳、单体灵魂（还更脆） |

#### 前端架构对照

微前端拆分前，先把 `features/*` 边界做稳；拆分时把 feature 的对外 API 变成独立 deploy。  
后端同理：先模块，后服务。

---

## 8. 常见坑

把前面易错点收成一张「出门前核对」表：

| # | 坑 | 正确方向 |
| --- | --- | --- |
| 1 | 业务规则写进 route 函数 | route 只翻译 HTTP；规则在 Domain / 用例 |
| 2 | 到处直接 `os.getenv`，配置散落 | `Settings.from_env()` 集中读，注入使用 |
| 3 | 循环依赖 | 用分层、端口、下沉模型打断 |
| 4 | 过早微服务 + 分布式事务痛苦 | **模块化单体优先**；先同仓 Worker |
| 5 | Domain 直接 import 厂商 SDK | Domain 只认端口；SDK 在 Infrastructure |
| 6 | 密钥进仓库 / 进镜像层 / 进前端包 | 环境注入 + Secret 源；日志脱敏；泄露即轮换 |
| 7 | 目录齐全但箭头反了 | 用变更风暴测试涟漪半径 |
| 8 | API 与 Worker 复制两份编排 | 复用同一 application/domain |
| 9 | 用「空接口数量」衡量架构水平 | 用可替换性与测试稳定性衡量 |
| 10 | 把每个 `.py` 当微服务 | 逻辑模块 ≠ 部署单元 |

口诀复习：

```text
分层定上下，模块定左右
端口留缝，适配器可换
配置进环境，密钥不进库
单体模块化，进程按需拆
```

---

## 9. 练习指引

按练习文档完成（先自己画/写，再对照本章）：

[`exercises/08-devops-architecture/03-software-architecture.md`](../../exercises/08-devops-architecture/03-software-architecture.md)

建议顺序：

1. **B1** 分层图：四层各举 2 个模块名  
2. **B2** 依赖方向审查：三道对错改写  
3. **B3** 密钥清单：`.env.example` 至少 5 项 + 禁提交类型  
4. **B4** 换模型供应商的涟漪  
5. （建议）**A1** 六边形一句话 + 入站/出站草图  
6. （建议）**A2** 模块化单体四理由 + 两个拆 Worker 触发条件  
7. （可选）**C1** 对现有 playground 列 5 条架构改进 TODO  

自测时盯住一句：你画的箭头是否指向 Domain，而不是从 Domain 指向 SDK。

---

## 10. 小结与下一站

### 你现在应该掌握的心智模型

```text
请求从 API 进来
  → Application 编排用例
  → Domain 规则 + 端口
  → Infrastructure 适配器碰真实世界

配置与密钥：
  示例进仓库，真密钥进环境 / Secret 源

演进：
  模块化单体 →（可选）同仓 Worker →（证据足）再拆服务
```

### 自检

- [ ] 能画出 API / Application / Domain / Infra 分层，并说明依赖方向
- [ ] 能说明密钥如何管理（示例、注入、脱敏、轮换）
- [ ] 能说出「模块化单体优先」的理由，以及何时才考虑拆 Worker/服务
- [ ] 能用端口/适配器直觉解释「换 LLM 为什么不该动 Domain」

### 模块 08 收官

下一模块：[`../09-ai-llm/README.md`](../09-ai-llm/README.md) —— AI/LLM 基础与认知地图（主线进入智能体核心前置知识）。

学架构是为了让后面 Agent 核心代码「换得动、测得稳、部署不慌」；不是为了收集名词。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Docker 与部署](./02-docker-deploy.md)
- 下一模块：[AI / LLM 基础](../09-ai-llm/README.md)
