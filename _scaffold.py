# -*- coding: utf-8 -*-
"""Generate learning docs + exercises skeleton. Run once, then delete if desired."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 内容风格约定：重点优先的完整教程
STYLE_NOTE = (
    "写作风格：**重点优先的完整教程**。"
    "必掌握内容写透（概念 + 示例 + 踩坑）；建议掌握写清用法；了解即可只给认知地图。"
)

CURRICULUM: list[dict] = [
    {
        "id": "01-python-basics",
        "title": "Python 语言基础",
        "goal": "能用 Python 写正常程序，而不是只会零散脚本。",
        "why": "一切后续后端、异步、Agent 开发的语言底座。",
        "estimated": "1～2 周",
        "chapters": [
            {
                "file": "01-syntax-basics",
                "title": "语法与数据结构",
                "must": ["变量与类型", "list/tuple/dict/set", "控制流", "推导式", "文件读写"],
                "nice": ["切片技巧", "常用内置函数"],
                "optional": ["bytes 与编码细节"],
            },
            {
                "file": "02-functions-scope",
                "title": "函数与作用域",
                "must": ["函数定义与返回值", "*args/**kwargs", "作用域与闭包", "lambda"],
                "nice": ["高阶函数", "functools 入门"],
                "optional": ["递归与调用栈直觉"],
            },
            {
                "file": "03-modules-packages",
                "title": "模块、包与导入系统",
                "must": ["import 机制", "包结构", "__init__.py", "相对/绝对导入"],
                "nice": ["__name__ == '__main__'", "常用标准库巡礼"],
                "optional": ["sys.path 与命名空间包"],
            },
        ],
    },
    {
        "id": "02-advanced-python",
        "title": "Python 高级特性与类型系统",
        "goal": "建立 Python 内功，能读现代框架源码里的抽象。",
        "why": "Agent Framework 大量使用 Class / Protocol / Generic / DI。",
        "estimated": "2～3 周",
        "chapters": [
            {
                "file": "01-oop",
                "title": "面向对象编程",
                "must": ["class/继承/组合", "抽象基类", "dataclass", "property"],
                "nice": ["魔法方法常用子集", "依赖注入直觉"],
                "optional": ["元类概念扫盲"],
            },
            {
                "file": "02-data-model",
                "title": "Python 数据模型",
                "must": ["对象协议直觉", "常用 dunder 方法", "可调用对象"],
                "nice": ["描述符入门"],
                "optional": ["与 CPython 实现的关系"],
            },
            {
                "file": "03-iterator-generator",
                "title": "Iterator / Generator",
                "must": ["迭代协议", "生成器与 yield", "惰性求值"],
                "nice": ["生成器管道", "yield from"],
                "optional": ["异步生成器预告"],
            },
            {
                "file": "04-decorator",
                "title": "装饰器",
                "must": ["函数装饰器", "带参数装饰器", "保留元信息"],
                "nice": ["类装饰器", "实际场景：重试/计时/鉴权"],
                "optional": ["装饰器栈顺序细节"],
            },
            {
                "file": "05-context-manager",
                "title": "上下文管理器",
                "must": ["with 协议", "contextlib", "资源管理"],
                "nice": ["自定义上下文管理器"],
                "optional": ["异步上下文管理器预告"],
            },
            {
                "file": "06-exception-system",
                "title": "异常系统",
                "must": ["try/except/else/finally", "自定义异常", "异常链"],
                "nice": ["错误设计原则"],
                "optional": ["ExceptionGroup 概览"],
            },
            {
                "file": "07-typing-system",
                "title": "类型系统",
                "must": ["类型注解", "Optional/Union/Literal", "TypedDict", "Protocol", "Generic"],
                "nice": ["TypeVar", "pyright/mypy 基础"],
                "optional": ["类型体操进阶"],
            },
        ],
    },
    {
        "id": "03-engineering",
        "title": "Python 工程化",
        "goal": "从“会写 Python”进入“会用 Python 做项目”。",
        "why": "Agent 项目需要可维护结构、依赖管理、测试与日志。",
        "estimated": "1～2 周",
        "chapters": [
            {
                "file": "01-project-structure",
                "title": "项目结构",
                "must": ["src/app 布局", "包边界", "配置与入口"],
                "nice": ["单体到模块化演进"],
                "optional": ["单体仓库多包"],
            },
            {
                "file": "02-deps-venv",
                "title": "依赖与虚拟环境",
                "must": ["venv", "pip", "uv", "pyproject.toml", "环境变量"],
                "nice": ["锁文件", "ruff/formatter"],
                "optional": ["多环境发布流程"],
            },
            {
                "file": "03-testing",
                "title": "测试（pytest）",
                "must": ["pytest 基础", "断言与 fixture", "测什么不测什么"],
                "nice": ["参数化", "mock 基础"],
                "optional": ["覆盖率与 CI 预告"],
            },
            {
                "file": "04-logging",
                "title": "Logging",
                "must": ["logging 层级", "handler/formatter", "结构化日志直觉"],
                "nice": ["请求链路日志字段"],
                "optional": ["与可观测性平台对接"],
            },
        ],
    },
    {
        "id": "04-systems-basics",
        "title": "计算机与服务端基础",
        "goal": "补齐前端背景下的系统直觉，避免一知半解。",
        "why": "解释 Agent 超时、阻塞、网络失败、资源占用的“为什么”。",
        "estimated": "1～2 周",
        "chapters": [
            {
                "file": "01-os-basics",
                "title": "操作系统基础",
                "must": ["进程/线程", "内存与 I/O", "文件描述符直觉"],
                "nice": ["调度与阻塞"],
                "optional": ["内核细节"],
            },
            {
                "file": "02-network-http",
                "title": "网络与 HTTP",
                "must": ["TCP/IP 直觉", "HTTP 方法/状态码/头", "JSON API"],
                "nice": ["HTTPS 概念", "幂等与重试"],
                "optional": ["HTTP/2、WebSocket 扫盲"],
            },
            {
                "file": "03-concurrency-models",
                "title": "并发模型",
                "must": ["并行 vs 并发", "多线程/多进程/异步对比", "GIL 直觉"],
                "nice": ["何时选哪种模型"],
                "optional": ["无锁结构扫盲"],
            },
            {
                "file": "04-dsa-essentials",
                "title": "数据结构与算法精要",
                "must": ["复杂度直觉", "常用结构取舍", "与工程选型的关系"],
                "nice": ["哈希/堆/图的应用场景"],
                "optional": ["刷题路线（非主线）"],
            },
        ],
    },
    {
        "id": "05-async-python",
        "title": "Python 异步编程",
        "goal": "掌握 asyncio，跨过 Agent 开发分水岭。",
        "why": "LLM / Tool / DB / HTTP 全是 I/O，异步几乎是标配。",
        "estimated": "1～2 周",
        "chapters": [
            {
                "file": "01-asyncio-fundamentals",
                "title": "asyncio 基础",
                "must": ["async/await", "事件循环", "Coroutine/Task", "asyncio.gather"],
                "nice": ["超时与取消"],
                "optional": ["事件循环实现细节"],
            },
            {
                "file": "02-asyncio-advanced",
                "title": "asyncio 进阶实践",
                "must": ["Semaphore 限流", "并发控制模式", "异步 HTTP 客户端"],
                "nice": ["异步上下文/生成器", "常见死锁与坑"],
                "optional": ["trio/anyio 生态扫盲"],
            },
        ],
    },
    {
        "id": "06-web-backend",
        "title": "Web 后端",
        "goal": "能独立搭建并理解后端 API 服务。",
        "why": "Agent 常以服务形式对外提供能力，也要调用其他 API。",
        "estimated": "2 周",
        "chapters": [
            {
                "file": "01-web-framework-principles",
                "title": "Web 框架原理",
                "must": ["请求生命周期", "路由/中间件", "同步与异步处理"],
                "nice": ["WSGI/ASGI"],
                "optional": ["网关与反向代理角色"],
            },
            {
                "file": "02-fastapi-pydantic",
                "title": "FastAPI + Pydantic",
                "must": ["路由与依赖注入", "请求/响应模型", "校验错误处理"],
                "nice": ["OpenAPI 文档", "后台任务"],
                "optional": ["自定义依赖进阶"],
            },
            {
                "file": "03-auth",
                "title": "认证与授权",
                "must": ["认证 vs 授权", "Token/JWT 直觉", "API Key"],
                "nice": ["RBAC 基础"],
                "optional": ["OAuth2 完整流程"],
            },
        ],
    },
    {
        "id": "07-data-persistence",
        "title": "数据库与数据持久化",
        "goal": "掌握 SQL/ORM/缓存/队列的工程用法与取舍。",
        "why": "Memory、会话、任务状态、知识库元数据都依赖持久化。",
        "estimated": "2～3 周",
        "chapters": [
            {
                "file": "01-sql",
                "title": "SQL 基础",
                "must": ["CRUD", "JOIN", "索引直觉", "事务"],
                "nice": ["聚合与子查询"],
                "optional": ["执行计划入门"],
            },
            {
                "file": "02-postgresql",
                "title": "PostgreSQL",
                "must": ["常用类型", "约束", "本地/容器启动", "连接配置"],
                "nice": ["JSON/JSONB", "迁移思路"],
                "optional": ["扩展与性能调优"],
            },
            {
                "file": "03-orm",
                "title": "Python ORM",
                "must": ["SQLAlchemy/同类工具选型", "模型与会话", "迁移"],
                "nice": ["N+1 问题", "仓储模式直觉"],
                "optional": ["复杂查询优化"],
            },
            {
                "file": "04-redis-cache",
                "title": "缓存与 Redis",
                "must": ["缓存用途", "常用数据结构", "过期与一致性直觉"],
                "nice": ["限流计数", "会话缓存"],
                "optional": ["集群与持久化策略"],
            },
            {
                "file": "05-message-queue",
                "title": "消息队列基础",
                "must": ["为什么需要队列", "生产者/消费者", "至少一次投递直觉"],
                "nice": ["任务队列场景（Agent 长任务）"],
                "optional": ["Kafka/RabbitMQ 选型对比"],
            },
        ],
    },
    {
        "id": "08-devops-architecture",
        "title": "部署、运维与软件架构",
        "goal": "具备把服务跑起来、拆清楚边界的能力。",
        "why": "生产级 Agent 不只是脚本，还要部署、隔离与可演进架构。",
        "estimated": "1～2 周",
        "chapters": [
            {
                "file": "01-linux-basics",
                "title": "Linux 基础",
                "must": ["常用命令", "进程与日志查看", "权限与环境"],
                "nice": ["systemd 直觉"],
                "optional": ["性能排查工具链"],
            },
            {
                "file": "02-docker-deploy",
                "title": "Docker 与部署",
                "must": ["镜像/容器", "Dockerfile", "compose 本地编排"],
                "nice": ["多阶段构建", "环境隔离"],
                "optional": ["K8s 概念扫盲"],
            },
            {
                "file": "03-software-architecture",
                "title": "软件架构基础",
                "must": ["分层架构", "模块边界", "配置与密钥管理"],
                "nice": ["六边形/整洁架构直觉"],
                "optional": ["微服务何时该拆"],
            },
        ],
    },
    {
        "id": "09-ai-llm",
        "title": "AI / LLM 基础与认知地图",
        "goal": "对现阶段 AI 发展与常用名词建立较深入认知，并能调用 LLM。",
        "why": "Agent 建立在 LLM 能力之上；先统一术语与心智模型。",
        "estimated": "1～2 周",
        "chapters": [
            {
                "file": "01-ai-landscape-glossary",
                "title": "AI 发展脉络与名词词典",
                "must": ["LLM/Token/Context Window", "预训练/微调/推理", "Chat vs Completion"],
                "nice": ["RAG/Agent/Tool/Embedding 总览", "开源 vs 闭源模型格局"],
                "optional": ["训练细节与论文脉络"],
            },
            {
                "file": "02-llm-api",
                "title": "LLM API 实战",
                "must": ["Chat API", "温度等关键参数", "流式输出", "错误与重试"],
                "nice": ["多模型适配层设计"],
                "optional": ["本地推理部署扫盲"],
            },
            {
                "file": "03-prompt-engineering",
                "title": "Prompt Engineering",
                "must": ["系统提示与用户提示", "少样本", "角色与约束"],
                "nice": ["思维链适用边界"],
                "optional": ["自动提示优化工具"],
            },
            {
                "file": "04-structured-output",
                "title": "Structured Output",
                "must": ["JSON/Schema 约束输出", "校验与修复", "与 Pydantic 结合"],
                "nice": ["工具参数结构化"],
                "optional": ["各厂商结构化能力差异"],
            },
        ],
    },
    {
        "id": "10-rag",
        "title": "Embedding 与 RAG",
        "goal": "能构建可用的知识库问答系统，并理解失败原因。",
        "why": "企业 Agent 最常见落地形态之一。",
        "estimated": "2 周",
        "chapters": [
            {
                "file": "01-embedding-vector-search",
                "title": "Embedding 与向量检索",
                "must": ["Embedding 是什么", "相似度", "向量库角色"],
                "nice": ["常见向量库对比"],
                "optional": ["ANN 算法扫盲"],
            },
            {
                "file": "02-rag-architecture",
                "title": "RAG 架构",
                "must": ["切分/检索/生成流水线", "召回质量问题", "元数据过滤"],
                "nice": ["Hybrid Search", "Rerank"],
                "optional": ["GraphRAG 等变体扫盲"],
            },
            {
                "file": "03-rag-practice",
                "title": "RAG 实战与调优",
                "must": ["最小可用知识库", "评测召回", "常见失败模式"],
                "nice": ["chunk 策略实验"],
                "optional": ["多模态 RAG 扫盲"],
            },
        ],
    },
    {
        "id": "11-agent-core",
        "title": "Agent 核心开发",
        "goal": "理解 Agent 本质，能手写并使用框架构建 Agent。",
        "why": "本课程主线终点的核心能力区。",
        "estimated": "3～4 周",
        "chapters": [
            {
                "file": "01-tool-calling",
                "title": "Tool Calling",
                "must": ["工具定义", "模型选择工具", "执行与回传", "循环终止条件"],
                "nice": ["工具设计原则"],
                "optional": ["并行 tool calls"],
            },
            {
                "file": "02-handwritten-agent",
                "title": "手写一个 Agent",
                "must": ["ReAct 循环", "状态机直觉", "最小 Agent 实现"],
                "nice": ["错误恢复与重试"],
                "optional": ["规划算法变体"],
            },
            {
                "file": "03-agent-frameworks",
                "title": "Agent Framework 概览",
                "must": ["框架解决什么问题", "何时不用框架", "阅读源码的切入点"],
                "nice": ["主流框架对比（认知级）"],
                "optional": ["跟进最新生态"],
            },
            {
                "file": "04-langgraph",
                "title": "LangGraph 与工作流",
                "must": ["图/节点/边", "状态", "条件分支", "循环"],
                "nice": ["人机协同节点", "持久化 checkpoint"],
                "optional": ["与其他编排方案对比"],
            },
            {
                "file": "05-agent-memory",
                "title": "Agent Memory",
                "must": ["短期/长期记忆", "会话状态", "记忆写入与检索"],
                "nice": ["记忆污染与遗忘"],
                "optional": ["记忆压缩策略研究"],
            },
            {
                "file": "06-multi-agent",
                "title": "Multi-Agent",
                "must": ["分工与协作模式", "路由/辩论/流水线", "何时不该多 Agent"],
                "nice": ["共享状态与消息协议"],
                "optional": ["大规模 Agent 系统研究"],
            },
        ],
    },
    {
        "id": "12-agent-production",
        "title": "Agent 工程化与生产落地",
        "goal": "具备评测、可观测、安全与系统设计能力，接近生产级。",
        "why": "Demo 与生产的鸿沟主要在这里。",
        "estimated": "2～3 周",
        "chapters": [
            {
                "file": "01-evaluation",
                "title": "Agent Evaluation",
                "must": ["为什么要评测", "任务成功率", "轨迹评估", "回归集"],
                "nice": ["LLM-as-Judge 适用边界"],
                "optional": ["在线评测体系"],
            },
            {
                "file": "02-observability",
                "title": "Observability",
                "must": ["日志/指标/追踪", "Token 与延迟", "工具调用轨迹"],
                "nice": ["Tracing 平台直觉"],
                "optional": ["SLO 设计"],
            },
            {
                "file": "03-security",
                "title": "Agent Security",
                "must": ["提示注入", "工具权限", "数据泄露风险", "沙箱直觉"],
                "nice": ["最小权限原则落地"],
                "optional": ["合规与审计"],
            },
            {
                "file": "04-system-design",
                "title": "Agent 系统设计",
                "must": ["端到端架构图", "同步/异步边界", "失败降级", "成本控制"],
                "nice": ["平台化演进路径"],
                "optional": ["多租户 Agent 平台"],
            },
        ],
    },
]

PROJECTS: list[dict] = [
    {
        "file": "01-cli-tool",
        "title": "Project 1：Python CLI 工具",
        "stage": "完成模块 01～03 后",
        "outcome": "命令行工具、参数解析、打包运行。",
    },
    {
        "file": "02-fastapi-todo",
        "title": "Project 2：FastAPI Todo",
        "stage": "完成模块 05～07 核心后",
        "outcome": "CRUD API + 数据库 + 基础测试。",
    },
    {
        "file": "03-ai-chat",
        "title": "Project 3：AI Chat",
        "stage": "完成模块 09 后",
        "outcome": "流式对话、会话历史、结构化输出。",
    },
    {
        "file": "04-rag-kb",
        "title": "Project 4：RAG 知识库",
        "stage": "完成模块 10 后",
        "outcome": "文档入库、检索、问答与基础评测。",
    },
    {
        "file": "05-tool-agent",
        "title": "Project 5：Tool Agent",
        "stage": "完成模块 11 前半后",
        "outcome": "工具调用循环、可扩展工具集。",
    },
    {
        "file": "06-research-agent",
        "title": "Project 6：Research Agent",
        "stage": "完成模块 11～12 后",
        "outcome": "多步骤研究、记忆、可观测与评测。",
    },
]


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def chapter_doc(module: dict, chapter: dict, index: int, total: int) -> str:
    prev_hint = "上一章" if index > 1 else "本模块导读"
    next_hint = "下一章" if index < total else "本模块小结 / 下一模块"
    return f"""# {chapter['title']}

> 所属模块：`{module['id']}` · {module['title']}  
> 状态：`骨架`（待填充完整教程）  
> 对应练习：[`exercises/{module['id']}/{chapter['file']}.md`](../../exercises/{module['id']}/{chapter['file']}.md)

## 本章定位

- **模块目标**：{module['goal']}
- **本章在路线中的角色**：为后续 Agent / 后端能力提供可复用积木。
- **建议学时**：按个人节奏，以完成本章练习为准。

## 学习目标（学完应能做到）

{bullets([f"解释并使用：{x}" for x in chapter['must'][:3]])}
- 完成本章练习题，并知道哪些点属于「了解即可」。

## 重点分级（降低概念过载）

### 必掌握
{bullets(chapter['must'])}

### 建议掌握
{bullets(chapter['nice'])}

### 了解即可
{bullets(chapter['optional'])}

## 教程大纲（待填充）

1. **为什么要学**：与 Agent / 工程场景的连接
2. **核心概念**：用最少术语讲清本质
3. **动手示例**：可运行的最小代码
4. **常见坑**：初学者高频错误
5. **练习指引**：做什么、验收什么
6. **小结与下一站**：知识地图上的位置

## 内容占位

{STYLE_NOTE}

（完整正文将按上述大纲逐章补齐。）

## 自检清单

- [ ] 能不看笔记讲清「必掌握」每一项
- [ ] 能独立完成对应练习
- [ ] 知道本章哪些内容可以暂时跳过

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- {prev_hint} / {next_hint}：见模块 README 目录
"""


def chapter_exercise(module: dict, chapter: dict) -> str:
    return f"""# 练习：{chapter['title']}

> 对应文档：[`docs/{module['id']}/{chapter['file']}.md`](../../docs/{module['id']}/{chapter['file']}.md)  
> 状态：`骨架`（待填充题目）

## 练习说明

- 先完成文档中的「必掌握」再做题。
- 题目分档：**基础 / 进阶 / 挑战**（挑战可选）。
- 建议把代码写在本仓库外的练习目录或 `playground/`（后续可自行添加）。

## 基础题（必做）

1. （待填充）围绕：{chapter['must'][0]}
2. （待填充）围绕：{chapter['must'][1] if len(chapter['must']) > 1 else chapter['must'][0]}

## 进阶题（建议）

1. （待填充）综合运用：{', '.join(chapter['must'][:3])}

## 挑战题（可选）

1. （待填充）贴近后续 Agent / 工程场景的小任务

## 验收标准

- [ ] 基础题全部完成
- [ ] 能用自己的话解释关键代码
- [ ] （可选）进阶题至少完成 1 题

## 提示与参考

- （待填充）关键提示
- （待填充）参考答案思路（先不给完整答案，避免抄袭式学习）
"""


def module_readme(module: dict) -> str:
    lines = [
        f"# 模块 {module['id']}：{module['title']}",
        "",
        f"> 状态：`骨架已就绪` · 预计周期：{module['estimated']}",
        "",
        "## 模块目标",
        "",
        module["goal"],
        "",
        "## 为什么现在学",
        "",
        module["why"],
        "",
        "## 章节目录",
        "",
    ]
    for i, ch in enumerate(module["chapters"], 1):
        lines.append(
            f"{i}. [{ch['title']}](./{ch['file']}.md)"
            f" · [练习](../../exercises/{module['id']}/{ch['file']}.md)"
        )
    lines += [
        "",
        "## 建议学习方式",
        "",
        "1. 按章节顺序阅读文档",
        "2. 只把「必掌握」吃透，其余按兴趣加餐",
        "3. 立即做对应 `exercises/` 练习",
        "4. 用模块末尾的自检确认是否可进入下一模块",
        "",
        "## 模块自检",
        "",
        f"- [ ] 能用自己的话说明：{module['goal']}",
        "- [ ] 本模块所有章节基础练习已完成",
        "- [ ] 清楚本模块与 Agent 主线的连接点",
        "",
        "## 导航",
        "",
        "- 返回总览：[../../README.md](../../README.md)",
    ]
    return "\n".join(lines) + "\n"


def project_doc(project: dict) -> str:
    return f"""# {project['title']}

> 状态：`骨架`（待填充实战说明）  
> 建议时机：{project['stage']}

## 项目目标

{project['outcome']}

## 你将练习到的能力

- （待填充）对应模块知识点清单
- （待填充）工程实践点（结构、测试、日志等）

## 需求概述

1. （待填充）功能需求
2. （待填充）非功能需求（可读性、错误处理、基本测试）

## 里程碑

- [ ] M1：最小可运行版本
- [ ] M2：核心功能完整
- [ ] M3：测试 / 文档 / 基础可观测

## 验收标准

- （待填充）

## 延伸挑战

- （待填充）

## 导航

- 返回项目列表：[./README.md](./README.md)
- 返回总览：[../../README.md](../../README.md)
"""


def projects_readme() -> str:
    lines = [
        "# 实战项目线",
        "",
        "项目线与文档主线并行：学完相关模块后立刻做项目，用项目反哺“为什么要学”。",
        "",
        "## 项目列表",
        "",
    ]
    for i, p in enumerate(PROJECTS, 1):
        lines.append(f"{i}. [{p['title']}](./{p['file']}.md) — {p['stage']}")
    lines += [
        "",
        "## 建议节奏",
        "",
        "```",
        "文档小章节 → 练习题 →（阶段性）项目里程碑",
        "```",
        "",
        "不要等“全部学完”再做项目。",
        "",
    ]
    return "\n".join(lines)


def exercises_root_readme() -> str:
    lines = [
        "# 课后练习题",
        "",
        "本目录**独立于** `docs/` 学习正文，专门存放每一小章节的练习。",
        "",
        "## 怎么用",
        "",
        "1. 先学 `docs/<模块>/<章节>.md`",
        "2. 再做本目录下同名练习文件",
        "3. 以练习文件中的验收标准为准，而不是“感觉学会了”",
        "",
        "## 目录",
        "",
    ]
    for module in CURRICULUM:
        lines.append(f"### {module['id']} · {module['title']}")
        lines.append("")
        for ch in module["chapters"]:
            lines.append(f"- [{ch['title']}](./{module['id']}/{ch['file']}.md)")
        lines.append("")
    return "\n".join(lines)


def root_readme() -> str:
    module_toc_lines = []
    for module in CURRICULUM:
        module_toc_lines.append(f"### {module['id']} · {module['title']}")
        module_toc_lines.append("")
        module_toc_lines.append(f"- **目标**：{module['goal']}")
        module_toc_lines.append(f"- **周期**：{module['estimated']}")
        module_toc_lines.append(
            f"- **导读**：[`docs/{module['id']}/README.md`](docs/{module['id']}/README.md)"
        )
        module_toc_lines.append("- **章节**：")
        for ch in module["chapters"]:
            module_toc_lines.append(
                f"  - [{ch['title']}](docs/{module['id']}/{ch['file']}.md)"
                f" · [练习](exercises/{module['id']}/{ch['file']}.md)"
            )
        module_toc_lines.append("")
    module_toc = "\n".join(module_toc_lines)

    projects_toc = "\n".join(
        f"{i}. [{p['title']}](docs/projects/{p['file']}.md) — {p['stage']}"
        for i, p in enumerate(PROJECTS, 1)
    )

    return f"""# PythonDayDayUp

> 从 Python 扎实基本功，走到能独立开发 Agent，并对现阶段 AI 常用概念有较深入认知。

本仓库是一套**循序渐进的 Markdown 学习文档 + 独立练习题**，内容骨架基于
[Python → Agent 学习路线分享](https://chatgpt.com/share/6acf680e-f448-83ea-8d57-fd52d62e6aac)
整理与重组。

当前进度：**全部目录与章节骨架已就绪，正文与题目将逐章填充。**

---

## 这个文件夹是干什么的？

| 路径 | 用途 |
|------|------|
| `README.md`（本文件） | 总览：目标、用法、目录、学成标准 |
| `docs/` | 学习正文（大模块 → 小章节） |
| `docs/projects/` | 阶段性实战项目说明 |
| `exercises/` | 每章课后练习（与正文分离） |

---

## 最终学习成就

学完后，期望你具备的不是“会调某个框架 API”，而是：

```
Python                 ★★★★★
Software Engineering   ★★★★
Backend Engineering    ★★★★
Database               ★★★★
Network / OS           ★★★
LLM                    ★★★★
RAG                    ★★★★★
Agent                  ★★★★★
System Design          ★★★★
```

也就是说，你要成为：

> **具备完整服务端基础的 AI Full-Stack / Agent Engineer**

即使未来某个 Agent 框架消失，你仍然掌握：

> **Programming + Backend + System + AI Engineering**

---

## 学习目的（为什么这样设计）

1. **Python 精通**：语法 → 高级特性 → 工程化，而不是停留在脚本级。
2. **后端不再一知半解**：补齐异步、HTTP、数据库、缓存、部署与架构直觉。
3. **Agent 可独立开发**：Tool Calling → 手写 Agent → 工作流 → Multi-Agent → 生产化。
4. **AI 认知扎实**：对 Token、Context、RAG、Agent、Embedding 等名词有工程级理解。

刻意**不走**「NumPy → 深度学习 → 训练大模型」长线；主线是：

```
Python → 工程化 → 异步 → 后端 → 数据库
      → LLM API → RAG → Tool Calling → Agent → 生产化
```

---

## 怎么用（推荐节奏）

### 单章循环

```
读 docs 章节（先吃透「必掌握」）
        ↓
做 exercises 同名练习
        ↓
勾选自检清单
        ↓
进入下一章
```

### 三条并行线（很重要）

不要完全串行学完再做项目：

```
主线：工程开发（docs 01→12）
基础线：系统直觉（尤其模块 04、08）
项目线：实战（docs/projects）
```

- 文档解释项目里的「为什么」
- 项目解释文档里的「学了有什么用」

### 内容难度策略

本教程采用 **「重点优先的完整教程」**：

- **必掌握**：写透，必须练
- **建议掌握**：够用就学，能明显提升代码质量
- **了解即可**：建立地图，防止概念过载、影响兴趣

---

## 大模块总览

{module_toc}

---

## 实战项目线

{projects_toc}

项目导读：[`docs/projects/README.md`](docs/projects/README.md)

---

## 建议时间表（可按投入调整）

| 阶段 | 模块 | 大约时间 |
|------|------|----------|
| Python 语言 | 01 | 1～2 周 |
| 高级特性 + 类型 | 02 | 2～3 周 |
| 工程化 | 03 | 1～2 周 |
| 系统基础 | 04 | 1～2 周 |
| 异步 | 05 | 1～2 周 |
| Web 后端 | 06 | 2 周 |
| 数据持久化 | 07 | 2～3 周 |
| 部署与架构 | 08 | 1～2 周 |
| AI / LLM | 09 | 1～2 周 |
| RAG | 10 | 2 周 |
| Agent 核心 | 11 | 3～4 周 |
| 生产化 | 12 | 2～3 周 |

- 每天 1～2 小时：大约 **4～6 个月**
- 每天 3～4 小时：有机会压缩到 **2～3 个月**
- 若走更扎实的后端补强路线：可拉长到 **6～12 个月**

---

## 从哪里开始？

1. 打开 [`docs/01-python-basics/README.md`](docs/01-python-basics/README.md)
2. 学习第一章 [`docs/01-python-basics/01-syntax-basics.md`](docs/01-python-basics/01-syntax-basics.md)
3. 完成练习 [`exercises/01-python-basics/01-syntax-basics.md`](exercises/01-python-basics/01-syntax-basics.md)

---

## 当前仓库状态

- [x] 总览文档
- [x] 全部大模块目录
- [x] 全部小章节骨架
- [x] 全部练习题骨架
- [x] 项目线骨架
- [ ] 逐章填充完整教程正文
- [ ] 逐章填充练习题与验收细节

---

## 来源与说明

- 路线参考：[ChatGPT 分享 · Python 到 Agent 学习路线](https://chatgpt.com/share/6acf680e-f448-83ea-8d57-fd52d62e6aac)
- 文档会在骨架基础上持续补全，优先保证主线连贯与可练习性。
"""


def main() -> None:
    docs = ROOT / "docs"
    exercises = ROOT / "exercises"

    for module in CURRICULUM:
        mod_dir = docs / module["id"]
        ex_dir = exercises / module["id"]
        mod_dir.mkdir(parents=True, exist_ok=True)
        ex_dir.mkdir(parents=True, exist_ok=True)

        (mod_dir / "README.md").write_text(module_readme(module), encoding="utf-8")

        total = len(module["chapters"])
        for i, ch in enumerate(module["chapters"], 1):
            (mod_dir / f"{ch['file']}.md").write_text(
                chapter_doc(module, ch, i, total), encoding="utf-8"
            )
            (ex_dir / f"{ch['file']}.md").write_text(
                chapter_exercise(module, ch), encoding="utf-8"
            )

    proj_dir = docs / "projects"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "README.md").write_text(projects_readme(), encoding="utf-8")
    for p in PROJECTS:
        (proj_dir / f"{p['file']}.md").write_text(project_doc(p), encoding="utf-8")

    (exercises / "README.md").write_text(exercises_root_readme(), encoding="utf-8")
    (ROOT / "README.md").write_text(root_readme(), encoding="utf-8")

    chapter_count = sum(len(m["chapters"]) for m in CURRICULUM)
    print(f"OK: modules={len(CURRICULUM)}, chapters={chapter_count}, projects={len(PROJECTS)}")


if __name__ == "__main__":
    main()
