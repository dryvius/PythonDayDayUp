# Agent 系统设计

> 所属模块：`12-agent-production` · Agent 工程化与生产落地  
> 状态：`已完成正文`  
> 建议学时：4～6 小时  
> 对应练习：[`exercises/12-agent-production/04-system-design.md`](../../exercises/12-agent-production/04-system-design.md)

## 本章定位

- **本章角色**：汇总端到端架构、同步/异步边界、失败降级、成本控制；展望平台化。
- **收官意义**：把 01～11 的积木装成「能上线讨论」的系统设计。

## 学习目标

1. 画出生产级 Agent 端到端架构。
2. 划分同步 API 与异步 Job 边界。
3. 设计失败降级路径。
4. 提出成本控制手段。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 架构图、同步异步边界、降级、成本 | 能做设计评审级输出 |
| **建议掌握** | 平台化演进 | 能规划路线 |
| **了解即可** | 多租户平台 | 地图 |

---

## 1. 端到端架构图（参考）

```text
Client (Web/App)
   │ HTTPS + Auth
   ▼
API Gateway / FastAPI
   ├─ 同步：短问答 / 健康检查
   └─ 异步：POST /jobs → Queue
               ▼
            Worker
               ├─ Agent Runtime (图/循环)
               ├─ LLM Adapter(s)
               ├─ Tools (受 ACL)
               ├─ RAG / Memory
               └─ DB / Redis / Vector Store
   │
   ▼
Observability (logs/metrics/traces)
Evaluation (offline suites)
```

关键分离：

- **接入层** vs **编排层** vs **能力适配层** vs **数据层**

---

## 2. 必掌握：同步 / 异步边界

| 同步 | 异步 Job |
|------|----------|
| < 数秒可完成 | 多步工具、深研究、批量 |
| 直接返回答案 | 返回 job_id，轮询/推送 |
| 简单超时 | 可 checkpoint、可重试 |

经验：用户可感知等待过长 → 上队列（模块 07）。

---

## 3. 必掌握：失败降级

层级：

```text
1) 单工具失败 → 告诉模型/换工具
2) LLM 429 → 退避/换模型
3) RAG 空 → 明确「无资料」而非瞎编
4) 全链路失败 → 友好错误 + 工单/人工
5) 依赖大面积故障 → 只读降级或维护页
```

熔断、舱壁、超时处处设默认值。

---

## 4. 必掌握：成本控制

杠杆：

- 小模型做路由/分类，大模型做难题
- 缓存重复问题（注意时效）
- 截断上下文、限制 max_steps / max_tokens
- 工具结果摘要后再回灌
- 预算告警与按租户配额
- 评测防止「更贵但没更好」

---

## 5. 建议掌握：平台化演进

```text
单应用 Agent
  → 多业务复用同一 Runtime
  → 工具市场 / 统一鉴权 / 统一观测
  → 内部 Agent 平台
```

先模块化单体，再抽 worker 与平台服务。

---

## 6. 了解即可：多租户平台

租户隔离（数据、密钥、配额、工具策略）、计费、管理面……企业阶段专项设计。

---

## 7. 设计检查清单

- [ ] 认证授权与工具 ACL  
- [ ] 超时/重试/幂等  
- [ ] 评测回归集  
- [ ] trace_id 贯穿  
- [ ] 密钥与日志脱敏  
- [ ] 同步/异步边界清晰  
- [ ] 成本与配额  
- [ ] 降级与人工兜底  

---

## 8. 练习指引

[`exercises/12-agent-production/04-system-design.md`](../../exercises/12-agent-production/04-system-design.md)

---

## 9. 课程收官寄语

你已从 Python 基础走到 Agent 生产视角。  
最终能力应是：

> **Programming + Backend + System + AI Engineering**

而不是绑定某个框架的 API。框架会变，这些能力不会。

下一步建议：

1. 完成 Project 5/6  
2. 用真实场景做一个带评测与追踪的小服务  
3. 持续维护回归集与威胁清单  

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Agent Security](./03-security.md)
- 返回总览：[../../README.md](../../README.md)
- 项目线：[../projects/README.md](../projects/README.md)
