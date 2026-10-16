# Agent Memory

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/11-agent-core/05-agent-memory.md`](../../exercises/11-agent-core/05-agent-memory.md)

## 本章定位

- **本章角色**：区分工作记忆 / 会话短期 / 长期记忆；管理会话状态；设计写入过滤与检索；防范记忆污染。
- **和持久化**：短期可在进程内；长期落 DB/向量库（模块 07/10）。

## 学习目标

1. 分清三层记忆及与 RAG 的边界。
2. 设计会话状态结构。
3. 实现带类型/拒写规则的写入与限量检索。
4. 跑通最小 `MemoryStore`（含污染拒写单测）。
5. 认识污染与遗忘问题。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 三层记忆、会话状态、写入过滤与检索、最小 Store | 能实现并跑通 |
| **建议掌握** | 污染与遗忘、命名空间隔离 | 能规避 |
| **了解即可** | 压缩/图谱等进阶 | 见专题 |

---

## 1. 三层记忆（必掌握）

| 层 | 内容 | 寿命 | 存储 |
|----|------|------|------|
| **工作记忆** | 本轮 tool scratchpad、中间结果 | 单次 `run` 内 | 进程内变量 / trace |
| **会话短期** | 当前 `messages`、会话摘要 | 一次会话 | 内存、Redis |
| **长期** | 用户偏好、跨会话事实 | 天～永久 | PG、向量库（**独立命名空间**） |

| | 短期会话 | 长期 |
|--|----------|------|
| 风险 | 爆上下文 | 脏数据、隐私、注入写入 |

### 与 RAG 的边界

| | Memory | RAG |
|--|--------|-----|
| 典型内容 | 关于**用户/会话**的状态与偏好 | 关于**知识库文档**的片段 |
| 写入 | 交互中产生，需防污染 | 离线/运营建库为主 |
| 检索 | 少而准，常按 `user_id` | Top-K 语义/关键词 |
| 库表/集合 | `memory:user:{id}:*` | `kb:tenant:{id}:*` |

可以都用向量库实现，但**产品语义别混**：别把「用户随口一句话」自动写进企业知识库。

---

## 2. 必掌握：会话状态

```python
from dataclasses import dataclass, field
from typing import Literal

MemoryType = Literal["pref", "fact", "episode"]


@dataclass
class SessionState:
    session_id: str
    user_id: str
    messages: list[dict] = field(default_factory=list)
    summary: str | None = None
    scratch: dict = field(default_factory=dict)  # 本轮工作记忆
    metadata: dict | None = None
```

策略：

- 最近 N 条原文 + 旧历史摘要  
- 系统提示固定，不塞进「可污染」记忆  
- `scratch` 在 `run` 结束可清空或择要写入长期层  

---

## 3. 必掌握：写入过滤与检索

### 3.1 写入时机与拒写

适合写：

- 用户**明确**偏好（「以后用中文」）
- 工具成功结果的**结构化摘要**（带来源）
- 经确认的稳定事实（项目代号等）

默认**拒写**：

```text
一次性错误结论、玩笑/反话、未确认的猜测
来自 RAG/网页的「指令口吻」内容（防间接注入进记忆）
密钥、证件号等敏感字段
```

```python
def should_write_long_term(item: dict) -> tuple[bool, str]:
    if item.get("source") in {"rag", "fetch_url", "user_raw"}:
        return False, "untrusted_source"
    if item.get("confidence", 0) < 0.8:
        return False, "low_confidence"
    if item.get("type") not in {"pref", "fact"}:
        return False, "type_not_allowed"
    return True, "ok"
```

重要事实可：人工审核 / 用户确认后再落库；一律带 `TTL` 与可撤销 id。

### 3.2 检索

- 按 `user_id`（+ 可选 `memory_type`）过滤  
- 注入 prompt 前**限量**（如最多 5 条）并标注来源标签  

```text
相关长期记忆：
- [pref] 偏好简洁回复
- [fact] 项目代号 Orion
```

记忆注入同样不可信当成系统指令；主控仍靠工具 ACL（模块 12）。

---

## 4. 必掌握：最小 MemoryStore（可跑）

仓库已提供可跑示例（纯标准库）：

[`playground/11-agent-core/memory/`](../../playground/11-agent-core/memory/)

```bash
python playground/11-agent-core/memory/demo.py
python playground/11-agent-core/memory/run_tests.py
# 或：python -m pytest playground/11-agent-core/memory/test_store.py -q
```

API 心智：

```text
add(user_id, type, text, source, confidence) -> (item|None, reason)
retrieve(user_id, limit=5) -> list[MemoryItem]
revoke(id) -> bool
format_for_prompt(items) -> str   # 带 [pref]/[fact] 标签
```

`add` **内部必须先** `should_write_long_term`；污染评测 case 见 `test_pollution_case_not_persisted`。  
落盘文件仅作学习；生产换 PG/Redis 时保持同一接口即可。

---

## 5. 建议掌握：污染与遗忘

污染例子：

- 把一次性错误结论当永久事实  
- 用户玩笑被当成偏好  
- 提示注入写入记忆  

缓解：写入过滤、TTL、可撤销、记忆与指令隔离、命名空间与 RAG 分开。

遗忘：

- 摘要压缩旧消息  
- 滑动窗口  
- 过期删除  

---

## 6. 了解即可：压缩策略与专题

分层摘要、记忆图谱、向量+结构化混合……有评测再上。  
进阶地图见专题：[记忆工程进阶](../topics/memory-engineering.md)。

---

## 7. 练习指引

[`exercises/11-agent-core/05-agent-memory.md`](../../exercises/11-agent-core/05-agent-memory.md)

---

## 8. 小结与下一站

### 自检

- [ ] 能画出工作 / 会话 / 长期三层
- [ ] 能写出 `should_write_long_term` 类拒写规则
- [ ] 本地跑通 Store demo + 污染单测
- [ ] 知道 Memory 与 RAG 命名空间为何要分开

### 下一章

[`06-multi-agent.md`](./06-multi-agent.md) —— 多 Agent 协作与何时不该用。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[LangGraph 与工作流](./04-langgraph.md)
- 下一章：[Multi-Agent](./06-multi-agent.md)
- 专题：[记忆工程进阶](../topics/memory-engineering.md)
