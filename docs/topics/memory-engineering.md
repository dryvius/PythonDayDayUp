# 专题：记忆工程进阶

> 非主线模块。先掌握 [`../11-agent-core/05-agent-memory.md`](../11-agent-core/05-agent-memory.md) 与可跑 Store。

## 你已经有的（主线）

- 工作 / 会话 / 长期三层  
- `should_write_long_term` 拒写  
- Memory ≠ RAG 命名空间  
- 可跑：`playground/11-agent-core/memory/`

## 进阶地图（了解即可，有评测再上）

| 方向 | 在解决什么 | 风险 |
|------|------------|------|
| 分层摘要 | 长会话压进摘要树 | 摘要丢失关键约束 |
| 记忆图谱 | 实体关系可查询 | 抽取噪声、运维重 |
| 向量长期记忆 | 语义召回偏好/事实 | 易与 RAG 库混用 |
| 操作系统式记忆（分页/swap） | 超长 Agent 轨迹 | 实现复杂，先评测收益 |

## 工程清单（进阶前必过）

1. 写入过滤单测（含污染 case）绿  
2. 与 RAG 集合/表前缀隔离  
3. TTL + revoke API  
4. 注入 prompt 限量 + 标签  
5. 评测：至少 1 条「注入不得写入记忆」  

## 导航

- 专题首页：[README.md](./README.md)
- 主线 Memory：[../11-agent-core/05-agent-memory.md](../11-agent-core/05-agent-memory.md)
