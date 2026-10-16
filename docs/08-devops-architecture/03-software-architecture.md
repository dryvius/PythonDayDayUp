# 软件架构基础

> 所属模块：`08-devops-architecture` · 部署、运维与软件架构  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/08-devops-architecture/03-software-architecture.md`](../../exercises/08-devops-architecture/03-software-architecture.md)

## 本章定位

- **本章角色**：学会分层、模块边界、配置与密钥管理；对整洁/六边形架构建立直觉；知道微服务不该过早上。
- **和 Agent**：API、编排、工具、模型适配、持久化要分清，否则框架一换就全家重写。

## 学习目标

1. 画出 Agent 服务的分层结构。
2. 制定模块依赖方向规则。
3. 正确管理配置与密钥。
4. 理解端口/适配器直觉；知道何时不该拆微服务。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 分层架构、模块边界、配置与密钥 | 能落地小项目结构 |
| **建议掌握** | 六边形/整洁架构直觉 | 能听懂、能渐进采用 |
| **了解即可** | 微服务何时该拆 | 防过早拆分 |

---

## 1. 必掌握：分层架构（Agent 版）

推荐起点：

```text
API 层          FastAPI routes / schemas
Application 层  用例：run_agent / create_job
Domain 层       Agent/Tool 抽象、纯规则
Infrastructure  LLM SDK、DB、Redis、队列、搜索
```

依赖方向：

```text
API → Application → Domain
Infrastructure → 实现 Domain 端口（向内适配）
```

禁止：Domain 直接 import 某家 LLM SDK 细节（可放接口，实现放基础设施）。

---

## 2. 必掌握：模块边界

好边界的信号：

- 改模型供应商只动 `infrastructure/llm`
- 改表结构主要动 repository
- 工具可插拔注册，不改编排核心

目录可与工程化章呼应：

```text
app/
  api/
  application/
  domain/
  infrastructure/
```

小项目可先 `api / services / adapters`，但**依赖方向**要想清楚。

---

## 3. 必掌握：配置与密钥管理

| 该进仓库 | 不该进仓库 |
|----------|------------|
| `.env.example` | `.env` 真密钥 |
| 默认非秘密配置 | 生产连接串密码 |
| 架构文档 | 私钥、证书明文 |

做法：

- 12-factor：配置来自环境
- 本地 dotenv；生产用密钥管理（云 Secret / K8s Secret 等）
- 日志脱敏
- 轮换策略：泄露即作废

---

## 4. 建议掌握：六边形 / 整洁架构直觉

一句话：

> **业务核心不依赖框架与驱动；框架与驱动依赖业务定义的端口。**

```text
        ┌─────────────┐
HTTP ──►│  适配器入    │
        │   Domain    │
DB   ◄──│  适配器出    │
LLM  ◄──│             │
        └─────────────┘
```

你不需要一上来完整 Hexagonal；但要保留「可替换适配器」的缝。

---

## 5. 了解即可：微服务何时该拆

先别拆的信号：

- 团队 < 很小、一人项目
- 边界尚不清
- 没有独立扩展/发布需求

可以考虑拆的信号：

- 不同部分独立扩缩（例如重 embedding worker）
- 不同团队所有权清晰
- 故障隔离需求强

错误示范：把每个 Python 文件变成微服务。  
正确路径：**模块化单体 → 按需拆 worker/服务**。

---

## 6. Agent 参考架构草图

```text
Client
  → API Gateway / FastAPI
      → Agent Application (编排)
          → Tool ports
          → LLM port
          → Memory port
      → Infrastructure adapters
          → PG / Redis / Queue / Vector DB / Provider SDK
Worker（可选）
  → 消费长任务，复用同一 domain
```

---

## 7. 常见坑

1. 业务规则写进 route 函数
2. 到处直接 `os.getenv`，配置散落
3. 循环依赖（用分层与接口打断）
4. 过早微服务 + 分布式事务痛苦

---

## 8. 练习指引

[`exercises/08-devops-architecture/03-software-architecture.md`](../../exercises/08-devops-architecture/03-software-architecture.md)

---

## 9. 小结与下一站

### 自检

- [ ] 能画出 API/Application/Domain/Infra 分层
- [ ] 能说明密钥如何管理
- [ ] 能说出「模块化单体优先」的理由

### 模块 08 收官

下一模块：[`../09-ai-llm/README.md`](../09-ai-llm/README.md) —— AI/LLM 基础与认知地图（主线进入智能体核心前置知识）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Docker 与部署](./02-docker-deploy.md)
- 下一模块：[AI / LLM 基础](../09-ai-llm/README.md)
