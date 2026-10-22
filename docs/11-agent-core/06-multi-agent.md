# Multi-Agent

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（建议先用 FakeAgent 证明「单 Agent 不够」，再拆路由/流水线；编排护栏务必动手写一遍）  
> 对应练习：[`exercises/11-agent-core/06-multi-agent.md`](../../exercises/11-agent-core/06-multi-agent.md)

## 本章定位

- **本章角色**：理解多 Agent 分工模式（路由 / 流水线 / 辩论）；明确何时不该上多 Agent；能设计共享状态、消息协议与终止护栏。
- **原则**：多 Agent 是**组织结构**，不是性能魔法；复杂度、延迟、费用、排障难度都会上升。
- **默认克制**：先证明「单 Agent + 少量工具」不够，再拆；拆了也要能画出责任人与终止条件。
- **你的优势**：若做过微服务 / 前端微前端 / 工作流编排，心智可对照迁移——关键差异是「参与者是带提示与工具集的 LLM Agent」，失败模式更模糊。

## 学习目标（学完应能做到）

1. 用自己的话说明：何时单 Agent 足够、何时才值得拆多 Agent。
2. 描述三种常见协作模式（路由 / 流水线 / 辩论）并各举一例。
3. 设计简单路由器（规则或 LLM 分类 + `route` + `handle`）。
4. 设计共享状态与消息协议字段；写出带 `max_handoffs` / 唯一责任人的编排伪代码。
5. 能判断 Critic 为何默认只读、权限为何按 Agent 单独配置。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | 为何多 Agent、分工模式、路由/辩论/流水线、何时不用 | 能决策、能画图 |
| **建议掌握** | 共享状态、消息协议、编排护栏与终止 | 能设计最小实现 |
| **了解即可** | 大规模组织 / 拍卖式分配 | 扫盲，业务先稳住 2～3 专家 |

---

## 1. 为什么要多 Agent（先证明单 Agent 不够）

这一节会刻意写细——多 Agent 的诱惑很强，但**默认答案应是「先别上」**。只有当你能指出单 Agent 的具体失败模式，拆分才有正当性。

### 1.1 默认立场：单 Agent + 多工具往往够用

#### 为什么要先立这条规矩？

多 Agent 看起来「专业」「架构高级」，实际代价是：

| 成本维度 | 单 Agent | 多 Agent |
|----------|----------|----------|
| 延迟 | 一轮 tool-loop | 多次 handoff + 多次 LLM |
| 费用 | 一份上下文 | 多份提示重复塞上下文 |
| 排障 | 一条 trace | 跨 Agent 责任归属、路由错 |
| 评测 | 端到端一条路径 | 还要测路由正确率、踢皮球 |
| 安全 | 一套工具 ACL | 每套权限都要单独收紧 |

所以课程口令是：

> **先证明单 Agent 不够，再拆。** 拆完还要能回答：责任人是谁？最多转发几次？超限怎么降级？

#### 怎么写（先用「单 Agent」建模）

多数业务可以先长这样（和手写 Agent 章同一骨架）：

```text
用户 → 一个 Agent（一个 system prompt + 2～3 个工具）→ 答案
```

```python
# 心智：一个 Agent，多工具，而不是多 Agent
AGENTS = {
    "general": Agent(
        llm=llm,
        tools={"search": search, "calc": calc, "lookup_order": lookup_order},
        max_steps=8,
    )
}
```

先问四件事，再决定拆不拆：

1. **提示是否互相打架？**（「要大胆创新」vs「必须合规只读」写在同一 system 里）
2. **工具权限是否必须隔离？**（写作不该碰 `shell`；查账不该发邮件）
3. **角色专业性是否真的不同？**（调研 / 写作 / 审查的成功标准不同）
4. **失败模式是否可观测？**（拆了之后你能不能测「路由错了」）

四条都「还不痛」→ **继续单 Agent**。

#### 跑一下（用失败故事建立体感）

下面用**假场景**演示「还没到多 Agent」：

```python
def single_agent_enough(task: str) -> bool:
    """教学用决策函数：返回 True 表示先别拆。"""
    needs = []
    if "查订单" in task or "账单" in task:
        needs.append("lookup_order")
    if "计算" in task or "算一下" in task:
        needs.append("calc")
    if "搜索" in task or "资料" in task:
        needs.append("search")
    # 工具种类少、无权限冲突、无阶段产物 → 单 Agent
    return len(set(needs)) <= 3 and "先审查再写" not in task


assert single_agent_enough("帮我查一下订单 #12 运费怎么算") is True
assert single_agent_enough("先调研竞品，再写文案，再严格审查合规") is False
print("单 Agent 决策直觉 OK")
```

预期：日常问答 / 查单 / 小计算 → 单 Agent；明确多阶段产物 + 审查角色 → 才进入「可考虑拆」。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 「工具多了就要多 Agent」 | 工具多 ≠ 角色多；先做工具路由 / 提示分区 |
| 「拆了就能更聪明」 | 往往只是更贵、更慢、更难测 |
| 先画 5 个 Agent 再补需求 | 反模式：架构驱动需求 |
| 用多 Agent 掩盖提示工程失败 | 应先收紧单 Agent 的提示与工具契约 |

#### 对照：单 Agent vs 多 Agent（决策速查）

| 信号 | 倾向 |
|------|------|
| 意图清晰、工具 ≤ 3、无权限隔离刚需 | **单 Agent** |
| 同一提示里角色目标冲突 | 可考虑拆（或至少拆 system 段落 + 阶段） |
| 写库 / shell / 发信必须与只读检查隔离 | **多 Agent（或同进程多「角色配置」）** |
| 阶段产物明确（调研稿 → 大纲 → 成稿） | 流水线（可为多 Agent 或单 Agent 多节点） |
| 需要挑剔检查且愿付双倍成本 | 辩论 / Critic |
| 还不会做评测与追踪 | **先别上多 Agent** |

---

### 1.2 单 Agent 开始「不够」的三种信号

#### 为什么要会识别「真不够」？

否则你会把「提示太长」「偶发答错」误判成「需要多 Agent」。真不够，通常落在下面三类。

#### 怎么写（把信号写成可检查条件）

```python
from dataclasses import dataclass


@dataclass
class SplitSignals:
    prompt_conflicts: bool      # 提示目标互相打架
    need_tool_isolation: bool   # 工具权限必须隔离
    role_specialty_gap: bool    # 角色成功标准明显不同
    clear_stage_artifacts: bool # 阶段产物可交接
    can_eval_routing: bool      # 团队能测路由/协作


def should_consider_multi_agent(s: SplitSignals) -> tuple[bool, str]:
    if not s.can_eval_routing:
        return False, "no_eval_yet"  # 不会测就别拆
    hard = s.prompt_conflicts or s.need_tool_isolation or s.role_specialty_gap
    if hard:
        return True, "hard_signal"
    if s.clear_stage_artifacts:
        return True, "pipeline_candidate"
    return False, "single_agent_first"
```

三类「真不够」对照正文开篇：

1. **全能提示过长、互相冲突**  
   例：既要「大胆生成营销文案」，又要「合规官只许挑错不许改库」。塞进同一 system，模型会摇摆。
2. **工具权限需要隔离**  
   例：Researcher 可 `fetch_url`；Writer 只写文件到沙箱；Critic **只读**，绝不能 `shell` / 发信 / 写生产库。
3. **角色专业性差异大**  
   例：研究要广搜与引用；写作要结构与语气；审查要找漏洞与违规——成功标准不同，共用一套温度/提示往往两头不讨好。

#### 跑一下（口头过一遍决策）

```text
任务 A：用户问「把 1+2 算一下」→ 单 Agent + calculator
任务 B：客服「查账单 / 查技术 FAQ / 闲聊」意图清晰 → 路由多 Agent（或单 Agent + 意图分支）
任务 C：调研 → 大纲 → 写作 → 校对，每步有产物 → 流水线
任务 D：生成敏感策略草案，必须挑剔检查 → 提案 + Critic
任务 E：团队还没有 trace / 评测 → 无论多炫，先单 Agent
```

#### 易错点

- 把「提示写得乱」当成「必须多 Agent」——先整理单 Agent 提示。
- 把「想要并行」当成充分条件——多数任务串行阶段产物更重要；并行是优化，不是起点。
- 忽略 `can_eval_routing`——拆了测不了，等于引入不可控系统。

#### 对照：拆分粒度

| 粒度 | 含义 | 何时用 |
|------|------|--------|
| 单 Agent + 多工具 | 一个 loop，工具集共享 | 默认 |
| 单 Agent + 图节点 | 控制流显式，仍一套权限 | 分支/循环复杂时（见 LangGraph 章） |
| 多 Agent（多配置） | 多套提示 + 多套工具 ACL | 权限/角色硬冲突 |
| 多进程/多服务 Agent | 部署与隔离更强 | 生产安全/规模需求 |

> 多 Agent ≠ 必须多进程。教学与多数业务里，「多个 `Agent` 配置 + 编排器」就够建立正确心智。

---

### 1.3 拆开之后你真正买到的是什么

#### 为什么要说清楚「买到的不是智商」？

避免神话：多 Agent **不会**自动提高推理能力；你买到的是：

1. **提示焦点**：每个角色 system 更短、目标更单一  
2. **权限边界**：工具 ACL 按角色收紧（安全章会强化）  
3. **可替换性**：换掉 Writer 不必动 Researcher  
4. **可评测切片**：可单独测「路由准确率」「Critic 召回问题率」

#### 怎么写（一句话产品定义）

```text
多 Agent = 多个（提示 + 工具集 + 终止策略）配置
         + 编排器（路由/串行/循环）
         + 共享状态与消息协议
         + 护栏（max_handoffs / 责任人 / 超时 / 费用）
```

#### 易错点

- 以为「Agent 数量」是 KPI——数量上升通常是风险上升。
- 没有编排器，只靠 Agent「自行商量」——极易互相踢皮球。

#### 工程对照

| 前端 / 后端经验 | 多 Agent 粗对照 |
|----------------|-----------------|
| 微服务按界上下文拆分 | 按角色/权限拆 Agent |
| API Gateway 路由 | Router Agent / 规则路由 |
| 流水线 CI stage | Pipeline 阶段产物交接 |
| Code Review | Critic / Debate |
| 分布式追踪 `trace_id` | 协作消息里的 `trace_id` |

---

## 2. 必掌握：协作模式

三种模式先建立地图，再逐个写细。不必一上来全上；业务上 **2～3 个专家 + 一种主模式** 就够。

### 2.0 总览对照

| 模式 | 拓扑 | 适合 | 主要风险 |
|------|------|------|----------|
| **路由 Router** | 请求 → 选一个专家 | 意图分类清晰 | 分错科、fallback 弱 |
| **流水线 Pipeline** | A → B → C 产物交接 | 阶段产物明确 | 上游垃圾进下游、无回退 |
| **辩论 / 评审 Debate·Critic** | 提案 ↔ 批评 → 合成 | 需要挑剔检查 | 成本高、轮次失控 |

```text
路由：     User → Router → Expert_* → Reply
流水线：   User → A → B → C → Reply
辩论：     User → Proposer ⇄ Critic → Synthesizer → Reply
```

---

### 2.1 路由（Router）

#### 为什么需要路由？

当用户意图落在**互斥领域**（账单 / 技术 / 闲聊），硬塞一个全能专家会导致：

- 提示里堆满各域细则 → 上下文噪声  
- 工具全集暴露 → 权限面过大  
- 评测无法回答「是不是进错科室」

路由把「分类」与「专业处理」拆开：Router 只负责**选人**，专家只负责**办事**。

#### 怎么写

最小形态（规则或 LLM 分类均可）：

```text
用户请求 → classify(intent) → route(intent) → 专家 Agent.run → 回复
```

```python
AGENTS = {
    "billing": FakeAgent(name="billing", specialty="账单/订单"),
    "tech": FakeAgent(name="tech", specialty="技术排障"),
    "general": FakeAgent(name="general", specialty="闲聊/兜底"),
}


def classify(user_text: str) -> str:
    t = user_text.lower()
    if any(k in t for k in ("账单", "发票", "订单", "退款", "billing")):
        return "billing"
    if any(k in t for k in ("报错", "api", "超时", "bug", "技术")):
        return "tech"
    return "general"


def route(intent: str) -> str:
    if intent == "billing":
        return "billing"
    if intent == "tech":
        return "tech"
    return "general"


def handle(user_text: str) -> str:
    intent = classify(user_text)
    agent_name = route(intent)
    return AGENTS[agent_name].run(user_text)
```

生产里 `classify` 可以是：规则 → 小模型分类 → 大模型 JSON 意图；**务必保留 `general` 兜底**。

#### 跑一下（FakeAgent 即可）

```python
class FakeAgent:
    def __init__(self, name: str, specialty: str) -> None:
        self.name = name
        self.specialty = specialty

    def run(self, user_text: str) -> str:
        return f"[{self.name}/{self.specialty}] 已处理：{user_text}"


# 接上上面的 AGENTS / classify / route / handle
print(handle("我想查一下上月账单"))
# [billing/账单/订单] 已处理：我想查一下上月账单

print(handle("API 总是超时怎么办"))
# [tech/技术排障] 已处理：API 总是超时怎么办

print(handle("今天天气怎么样"))
# [general/闲聊/兜底] 已处理：今天天气怎么样
```

练习 B2 就是把这条链写完整：`classify` + `route` + `handle` + ≥2 专家。

#### 易错点

| 错法 | 后果 |
|------|------|
| Router 自己也去调重工具 | Router 应轻量；重活交给专家 |
| 没有 `general` 兜底 | 未知意图硬塞某专家 → 胡说 |
| 分错了还在专家内部死磕 | 应允许「退回 Router / 转 general」并计入 handoff |
| 只测专家、不测路由 | 线上事故常是「进错科室」 |

#### 对照：路由 vs 单 Agent 内分支

| | 单 Agent 内 `if intent` | 多 Agent 路由 |
|--|-------------------------|---------------|
| 实现 | 同一进程、同一工具 ACL | 多配置、可多 ACL |
| 适合 | 分支少、权限相同 | 权限/提示硬隔离 |
| 评测 | 端到端 | 额外要路由准确率 |

---

### 2.2 流水线（Pipeline）

#### 为什么需要流水线？

当任务天然是**阶段产物**：

```text
调研笔记 → 大纲 → 正文 → 校对稿
```

硬用一个 Agent「一次生成终稿」，常见症状是：结构飘、引用丢、校对标准被生成目标吞掉。流水线让每阶段 **输入/输出契约** 变清楚。

#### 怎么写

```text
调研 Agent →（artifacts.research）→ 写作 Agent →（artifacts.draft）→ 校对 Agent
```

```python
from dataclasses import dataclass, field


@dataclass
class PipelineState:
    user_text: str
    artifacts: dict = field(default_factory=dict)
    trace: list[dict] = field(default_factory=list)


def run_pipeline(state: PipelineState) -> PipelineState:
    # 阶段 1：调研
    research = AGENTS["researcher"].run(state.user_text)
    state.artifacts["research"] = research
    state.trace.append({"stage": "research", "ok": True})

    # 阶段 2：写作（只吃调研产物 + 原问题）
    draft_input = {
        "question": state.user_text,
        "research": state.artifacts["research"],
    }
    draft = AGENTS["writer"].run(draft_input)
    state.artifacts["draft"] = draft
    state.trace.append({"stage": "write", "ok": True})

    # 阶段 3：校对（建议只读）
    review = AGENTS["critic"].run(state.artifacts["draft"])
    state.artifacts["review"] = review
    state.trace.append({"stage": "review", "ok": True})
    return state
```

关键设计点：

1. **交接的是产物，不是整段聊天口水**（至少要有结构化摘要）。  
2. **下游失败能否回到上游**要显式规定（默认教学：不自动无限回退）。  
3. Critic / 校对默认**只读**（见 §4）。

#### 跑一下（两段 Fake 串行，对接练习 A1）

```python
class StageAgent:
    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, payload) -> str:
        if self.name == "researcher":
            return f"NOTES: 关于「{payload}」的三点摘要"
        if self.name == "writer":
            return f"DRAFT: 基于 {payload['research']} 写成短文"
        return f"REVIEW: 通过；原文长度={len(str(payload))}"


AGENTS = {
    "researcher": StageAgent("researcher"),
    "writer": StageAgent("writer"),
    "critic": StageAgent("critic"),
}

final = run_pipeline(PipelineState(user_text="对比 A/B 两款产品"))
print(final.artifacts["draft"])
print(final.artifacts["review"])
print(final.trace)
```

#### 易错点

| 错法 | 后果 |
|------|------|
| 把完整 messages 原样扔给下一阶段 | 噪声爆炸、费用飙升 |
| 上游胡写，下游无拒收 | 垃圾进、垃圾出 |
| 阶段无限来回「再改一版」 | 无终止；必须 `max_rounds` |
| 校对 Agent 拥有写库/发信 | 审查角色越权（安全事故） |

#### 对照：流水线 vs LangGraph 节点

| | Pipeline 多 Agent | 图节点（上一章） |
|--|-------------------|------------------|
| 关注点 | 角色提示 + 工具 ACL | 控制流与状态合并 |
| 可组合 | 流水线也可用图表达 | 图里每个节点也可绑不同 Agent |
| 建议 | 先契约后框架 | 分支/人工批准时上图 |

---

### 2.3 辩论 / 评审（Debate / Critic）

#### 为什么需要 Critic？

生成模型倾向「圆场」。对合规、安全、逻辑漏洞，**单独的挑剔角色**比「请你再检查一下自己」更稳——自己改自己常会放过自己。

代价也很明确：**至少多一轮 LLM**，还可能多轮修改。

#### 怎么写

```text
提案 Agent → 批评 Agent →（可选）修改 → 合成 / 输出
```

```python
def debate_once(question: str, *, max_rounds: int = 2) -> str:
    draft = AGENTS["proposer"].run(question)
    for round_i in range(1, max_rounds + 1):
        critique = AGENTS["critic"].run({"draft": draft, "question": question})
        if critique.get("verdict") == "pass":
            return draft
        draft = AGENTS["proposer"].run(
            {"question": question, "draft": draft, "critique": critique}
        )
        # 最后一轮无论是否 pass 都收束，避免无限吵
    return draft  # 责任人：proposer（或单独 synthesizer）
```

Critic 返回建议结构（教学用）：

```python
{
    "verdict": "pass" | "revise",
    "issues": ["事实无来源", "承诺了退款权限"],
    "suggestions": ["删除未证实数据", "改成引导人工客服"],
}
```

#### 跑一下（最多 2 轮，对接练习 C1）

```python
class Proposer:
    def __init__(self) -> None:
        self.fixes = 0

    def run(self, payload) -> str:
        if isinstance(payload, str):
            return "草案：保证三天内无条件退款"  # 故意有问题
        self.fixes += 1
        return "草案：可申请退款，以人工审核结果为准"


class Critic:
    def run(self, payload: dict) -> dict:
        draft = payload["draft"]
        if "无条件退款" in draft:
            return {
                "verdict": "revise",
                "issues": ["过度承诺"],
                "suggestions": ["改为人工审核"],
            }
        return {"verdict": "pass", "issues": [], "suggestions": []}


AGENTS = {"proposer": Proposer(), "critic": Critic()}
print(debate_once("写一条退款政策"))
# 草案：可申请退款，以人工审核结果为准
```

#### 易错点

| 错法 | 后果 |
|------|------|
| Critic 拥有写工具 / shell | 审查者变成操作者 |
| `max_rounds` 很大或没有 | 费用与延迟失控 |
| 两方对称「互喷」无合成 | 没有唯一责任人对用户输出 |
| 用辩论代替检索事实 | 吵得再认真也变不成真 |

#### 对照：Critic vs 单 Agent 自检

| | 单 Agent「请自查」 | 独立 Critic |
|--|-------------------|-------------|
| 提示冲突 | 生成与挑剔挤在同一角色 | 目标分离 |
| 权限 | 常仍持有写工具 | **默认只读** |
| 成本 | 较低 | 更高 |
| 适用 | 低风险润色 | 合规/安全/关键逻辑 |

---

### 2.4 模式选择题怎么做（对接练习 B1）

给任务时，用三问：

1. **意图是否互斥可选？** → 路由  
2. **是否有可交接的阶段产物？** → 流水线  
3. **是否必须挑剔检查且愿付费？** → 辩论  
4. 以上都不强 → **单 Agent 即可**

```text
例：
- 「查发票」→ 路由（billing）或单 Agent+lookup
- 「调研后写博客」→ 流水线
- 「生成对外承诺文案并严格审查」→ 辩论/Critic
- 「把这段英文译成中文」→ 单 Agent
- 「既要改生产配置又要安全审查」→ 多 Agent + Critic 只读 + 人工批准
```

---

## 3. 必掌握：何时不该多 Agent

### 3.1 为什么「不该用」和「该用」同样重要？

因为多 Agent 失败时，症状不像单测红灯那样干净——表现为：更慢、更贵、互相转发、用户收到「正在转接」、责任无人认领。**克制是生产能力**。

### 3.2 怎么判断（四条硬信号 + 一条反模式）

**不要上多 Agent** 的信号（练习 B3 至少写出 4 条）：

1. **任务可用单 Agent + 2～3 工具解决**  
2. **团队还不会做评测与追踪**（没有 trace / 路由 case）  
3. **只是为了「架构好看」**  
4. **延迟 / 费用敏感且收益说不清**  

再加上正文原有反模式：

5. **五个 Agent 互相转发，没有终止与责任人**

#### 怎么写（门禁函数）

```python
@dataclass
class MultiAgentGate:
    tools_needed: int
    has_eval_and_trace: bool
    architecture_vanity: bool
    latency_or_cost_sensitive: bool
    benefit_clear: bool


def allow_multi_agent(g: MultiAgentGate) -> tuple[bool, str]:
    if g.architecture_vanity:
        return False, "vanity"
    if g.tools_needed <= 3 and not g.benefit_clear:
        return False, "single_agent_enough"
    if not g.has_eval_and_trace:
        return False, "no_eval"
    if g.latency_or_cost_sensitive and not g.benefit_clear:
        return False, "cost_unclear"
    return True, "ok"
```

#### 跑一下

```python
print(allow_multi_agent(MultiAgentGate(
    tools_needed=2,
    has_eval_and_trace=True,
    architecture_vanity=False,
    latency_or_cost_sensitive=True,
    benefit_clear=False,
)))
# (False, 'single_agent_enough')

print(allow_multi_agent(MultiAgentGate(
    tools_needed=5,
    has_eval_and_trace=False,
    architecture_vanity=False,
    latency_or_cost_sensitive=False,
    benefit_clear=True,
)))
# (False, 'no_eval')
```

#### 易错点

- 「先拆了再说，评测以后补」——以后通常不会补，只会在事故后补。  
- 用 Agent 数量向领导汇报进度——应汇报**可测的行为**（路由准确率、任务成功率）。  
- 把 LangGraph / 框架教程里的多 Agent demo 直接当业务默认——demo 为了展示能力，不是默认架构。

#### 对照：该用 / 不该用

| 场景 | 决策 |
|------|------|
| 翻译、摘要、单次查询 | 单 Agent |
| 意图清晰的多科室客服 | 路由（可多 Agent） |
| 无 trace 的周末原型 | 单 Agent |
| 要写生产库且要合规审查 | 多 Agent + Critic 只读 + 护栏 |
| 「听说 Multi-Agent 很强」 | **不该用**（动机非法） |

---

## 4. 建议掌握：共享状态、协议与终止

多 Agent 一旦开搞，**状态怎么共享、消息长什么样、何时停**比「再加一个专家」更重要。

### 4.1 共享状态：黑板 vs 消息总线

#### 为什么要先选共享模型？

选错共享模型，后面全是竞态与「谁改了字段」扯皮。

| 模型 | 直觉 | 适合 | 风险 |
|------|------|------|------|
| **黑板（共享 state dict）** | 大家读写同一块板 | 流水线、图编排 | 字段冲突、覆盖、难审计 |
| **消息总线（彼此发 message）** | 发信/收信 | 路由、松耦合专家 | 协议要严、易丢责任链 |

教学默认：**编排器持有一份 `OrchestrationState`（黑板）+ 每次 hop 追加一条 message（审计）**——两者并不互斥。

#### 怎么写

```python
from dataclasses import dataclass, field
from typing import Any
import time
import uuid


@dataclass
class AgentMessage:
    from_agent: str
    to_agent: str
    type: str  # request | result | critique | handoff | final
    payload: Any
    trace_id: str
    step: int
    idempotency_key: str


@dataclass
class OrchestrationState:
    trace_id: str
    user_text: str
    shared: dict = field(default_factory=dict)      # 黑板
    inbox: list[AgentMessage] = field(default_factory=list)
    handoffs: int = 0
    owner: str | None = None  # 最终对用户负责的 Agent
    status: str = "running"   # running | done | failed | limited
```

协议字段建议（练习 B4 要能写成 JSON schema 直觉）：

```text
from, to, type, payload, trace_id, step, idempotency_key
```

| 字段 | 作用 |
|------|------|
| `from` / `to` | 谁发给谁；排障第一眼 |
| `type` | 消息种类，避免都当 chat 散文 |
| `payload` | 结构化产物，不塞无关历史 |
| `trace_id` | 一次用户请求全链路同一 ID |
| `step` | 协作步序号 |
| `idempotency_key` | 防重复 handoff / 重试双执行 |

示例消息：

```python
def make_handoff(*, frm: str, to: str, payload: Any, trace_id: str, step: int) -> AgentMessage:
    return AgentMessage(
        from_agent=frm,
        to_agent=to,
        type="handoff",
        payload=payload,
        trace_id=trace_id,
        step=step,
        idempotency_key=f"{trace_id}:{step}:{frm}->{to}",
    )
```

#### 跑一下

```python
tid = str(uuid.uuid4())
st = OrchestrationState(trace_id=tid, user_text="查账单")
msg = make_handoff(frm="router", to="billing", payload={"intent": "billing"}, trace_id=tid, step=1)
st.inbox.append(msg)
st.shared["intent"] = "billing"
print(st.inbox[0].idempotency_key)
print(st.shared)
```

#### 易错点

- 黑板字段被后写覆盖、无版本——关键产物应不可变追加或写 `artifacts.stage`。  
- 消息只有 `content: str`——协作协议退化成群聊，无法做权限与终止。  
- 忘记 `trace_id`——模块 12 可观测性会非常痛。

#### 对照：黑板 vs 总线

```text
黑板： state["draft"] = "..."        # 大家看得见
总线： inbox.append(Message(...))  # 事件可审计

推荐：黑板存产物，总线存事件。
```

---

### 4.2 工具权限：按 Agent 单独配置

#### 为什么必须按 Agent 配工具？

多 Agent 的核心收益之一就是**缩小每个角色的爆炸半径**。若所有 Agent 共享全能工具表，拆分只剩「多付几次 LLM 钱」。

#### 怎么写

```python
TOOLSETS = {
    "researcher": {"fetch_url", "search"},
    "writer": {"write_sandbox_file"},          # 无 shell
    "critic": set(),                          # 只读：无工具或仅只读检索
    "billing": {"lookup_order"},
}


def bind_agent(name: str, llm) -> Agent:
    tools = {k: TOOLS[k] for k in TOOLSETS[name]}
    return Agent(llm=llm, tools=tools, max_steps=6)
```

硬规矩（与正文一致，安全章会再强化）：

> **Critic / 评审 Agent 默认只读**——检查与建议，不自动获得 `shell` / 写库 / 发信。

#### 跑一下（对接练习 A2）

```python
def can_call(agent_name: str, tool_name: str) -> bool:
    return tool_name in TOOLSETS.get(agent_name, set())


assert can_call("writer", "shell") is False
assert can_call("critic", "write_sandbox_file") is False
assert can_call("researcher", "search") is True
print("权限隔离 OK")
```

#### 易错点

- 「先共用工具表，上线前再拆」——上线前不会拆。  
- Critic 为了「帮忙改一下」拿到写权限——角色污染。  
- 只在 prompt 写「你不要调用 shell」——**提示不是 ACL**。

#### 对照

| 控制手段 | 强度 |
|----------|------|
| Prompt 约定 | 弱 |
| 工具表不挂载 | **强（推荐）** |
| 运行时 ACL / 人工批准 | 生产增强（模块 12） |

---

### 4.3 编排器级护栏与终止

#### 为什么终止比「再加专家」优先？

没有终止的多 Agent = 分布式死循环。用户侧表现是转圈；账单侧表现是 tokens 烧掉。

编排器级护栏（保留并写透）：

```text
max_handoffs：跨 Agent 转发次数上限（防互相踢皮球）
责任人：最终对用户输出的 Agent 必须唯一明确
超时：整次协作总墙钟预算
费用：累计 tokens / 步数触顶则降级单 Agent 直答
```

#### 怎么写（最小编排循环）

```python
AGENTS: dict[str, Any] = {}  # name -> agent


def orchestrate(user_text: str, *, max_handoffs: int = 3) -> str:
    handoffs = 0
    agent_name = "router"
    owner = "general"  # 默认责任人；路由后可改
    # 也可同时跟踪 deadline / token_budget
    while handoffs <= max_handoffs:
        agent = AGENTS[agent_name]
        result = agent.run(user_text)  # 约定返回 {reply, next?, done, owner?}
        if result.get("owner"):
            owner = result["owner"]
        if result.get("done"):
            return result["reply"]  # 责任人产出
        next_name = result.get("next")
        if not next_name or next_name == agent_name:
            return result.get("reply") or "stopped"
        agent_name = next_name
        handoffs += 1
    # 超限：降级策略示例——让责任人直接答，不再转发
    return AGENTS[owner].run(f"[协作步数超限，请直接回答] {user_text}")
```

更完整一点的状态机直觉：

```text
RUNNING → (handoff)* → DONE
        ↘ LIMITED（触顶降级）
        ↘ FAILED（超时/异常）
```

#### 跑一下（观察踢皮球被掐断）

```python
class PingPongAgent:
    def __init__(self, name: str, nxt: str) -> None:
        self.name = name
        self.nxt = nxt

    def run(self, user_text: str) -> dict:
        return {"reply": f"{self.name} 想转给 {self.nxt}", "next": self.nxt, "done": False}


AGENTS = {
    "router": PingPongAgent("router", "a"),
    "a": PingPongAgent("a", "b"),
    "b": PingPongAgent("b", "a"),
    "general": FakeAgent("general", "兜底"),
}

print(orchestrate("你好", max_handoffs=3))
# 协作步数超限后走 owner/general 降级（取决于你实现的 return 分支）
```

把 `max_handoffs=3` 改成很大，你会「看见」费用型事故的形状——这就是护栏存在的理由。

#### 易错点

| 错法 | 后果 |
|------|------|
| 只给每个 Agent `max_steps`，没有全局 `max_handoffs` | 本地都合规，全局仍死循环 |
| 责任人含糊（「最后说话的算」） | 用户投诉时无人认领 |
| 超限直接抛异常给用户 | 体验差；应降级直答或道歉收束 |
| 超时只套在单次 LLM | 协作总墙钟仍可能拖很久 |

#### 对照：Agent 内终止 vs 编排终止

| 层级 | 典型护栏 |
|------|----------|
| 单 Agent（手写章） | `max_steps`、重复 tool 熔断 |
| 编排器（本章） | `max_handoffs`、总超时、费用顶、唯一 `owner` |
| 生产（模块 12） | 鉴权、审计、人工批准、限流 |

---

### 4.4 错误归属与评测切片

#### 为什么要提前定归属？

多 Agent 出问题时，最常见扯皮是：「模型不行」vs「路由错」vs「专家工具挂了」。归属不清，评测集也建不起来。

#### 怎么写（简单规则）

```text
路由分错     → 记在 router（评测加「路由错误」case）
专家工具失败 → 记在该专家 + 编排器是否降级
Critic 误杀 → 记在 critic（可测误报率）
超限停止     → 记在 orchestrator（护栏是否过紧）
```

```python
def attribute_error(where: str, exc: Exception) -> dict:
    return {
        "bucket": where,  # router | expert:billing | orchestrator | critic
        "error_type": type(exc).__name__,
        "retryable": where.startswith("expert"),
    }
```

#### 易错点

- 只有端到端「对/错」，没有路由 case——优化时会改错旋钮。  
- 专家失败就自动转下一个专家，无审计——掩盖真实故障。

#### 对照：单测该补什么

| Case | 断言 |
|------|------|
| 账单话术进 billing | `route(classify(text)) == "billing"` |
| 未知意图进 general | 兜底 |
| writer 无 shell | `can_call("writer","shell") is False` |
| 踢皮球 | `orchestrate` 在 `max_handoffs` 内停止 |
| Critic 只读 | 工具集为空或仅只读 |

---

## 5. 了解即可：大规模

#### 为什么只扫盲？

上百 Agent、市场拍卖式任务分配、动态组织……属于研究 / 平台级话题。业务主线应先把 **2～3 个专家 + 一种协作模式 + 护栏** 做稳，再谈规模。

#### 对照地图（预告，不深挖）

| 形态 | 一句话 |
|------|--------|
| 静态专家组 | 预注册 billing/tech/writer……（本章主线） |
| 层级经理 Agent | Manager 拆任务给 Worker |
| 市场 / 拍卖 | 多个 Worker 竞价接任务（复杂） |
| Agent 即服务 | 远程 Agent 网络（协议与信任更难） |

#### 易错点（预告级）

- 用「大规模多 Agent」论文架构套 3 人小产品。  
- 还没稳住 `trace_id` 与 `max_handoffs`，就上动态发现与拍卖。

---

## 6. 最小路由伪代码（整章收束可跑版）

这一节把 §2.1 与编排护栏收成**可粘贴的最小完整版**，方便直接对着练习 B2。

### 6.1 为什么再写一版「最小完整」？

前面拆开讲了动机与模式；动手时你需要一份**从头到尾**的骨架：分类 → 路由 → 专家执行 →（可选）护栏。少任何一段，练习都容易写成「只有 if-else 没有 Agent 边界」。

### 6.2 怎么写

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class AgentLike(Protocol):
    def run(self, user_text: str) -> str: ...


@dataclass
class FakeExpert:
    name: str
    reply_prefix: str

    def run(self, user_text: str) -> str:
        return f"{self.reply_prefix}: {user_text}"


AGENTS: dict[str, AgentLike] = {
    "billing_agent": FakeExpert("billing_agent", "BILLING"),
    "tech_agent": FakeExpert("tech_agent", "TECH"),
    "general_agent": FakeExpert("general_agent", "GENERAL"),
}


def classify(user_text: str) -> str:
    """规则分类即可；真项目可换成 LLM JSON 意图。"""
    t = user_text.lower()
    if any(k in t for k in ("账单", "发票", "订单", "退款")):
        return "billing"
    if any(k in t for k in ("报错", "超时", "api", "bug")):
        return "tech"
    return "general"


def route(intent: str) -> str:
    if intent == "billing":
        return "billing_agent"
    if intent == "tech":
        return "tech_agent"
    return "general_agent"


def handle(user_text: str) -> str:
    intent = classify(user_text)  # LLM 或规则
    agent = AGENTS[route(intent)]
    return agent.run(user_text)


# —— 可选：带 handoff 上限的薄编排（责任人 = 路由选中的专家）——
def handle_with_guard(
    user_text: str,
    *,
    max_handoffs: int = 3,
    classify_fn: Callable[[str], str] = classify,
) -> str:
    handoffs = 0
    # 第一步：router → expert（计 1 次 handoff）
    intent = classify_fn(user_text)
    agent_name = route(intent)
    owner = agent_name
    handoffs += 1
    if handoffs > max_handoffs:
        return AGENTS["general_agent"].run(user_text)
    return AGENTS[owner].run(user_text)
```

### 6.3 跑一下

```python
assert "BILLING" in handle("请开一张发票")
assert "TECH" in handle("API 报错超时")
assert "GENERAL" in handle("讲个笑话")
print(handle("我想退款"))
print("router OK")
```

### 6.4 易错点

- `classify` 与 `route` 糊成一个巨型 if——以后换 LLM 分类会拆不动。  
- `handle` 里专家再手动 `if` 一遍意图——路由失去意义。  
- 专家返回散文里「请转技术」却没有结构化 `next`——编排器无法护栏。

### 6.5 对照：最小路由 vs 完整编排

| 能力 | `handle` | `orchestrate`（§4.3） |
|------|----------|----------------------|
| 选专家 | ✅ | ✅ |
| 多跳转发 | ❌ | ✅ |
| `max_handoffs` | 可选薄包一层 | ✅ |
| 辩论/流水线 | ❌ | 换成别的编排函数 |

学习顺序：先让 `handle` 绿 → 再加流水线/辩论 → 最后统一挂上编排护栏。

---

## 7. 练习指引

按 [`exercises/11-agent-core/06-multi-agent.md`](../../exercises/11-agent-core/06-multi-agent.md) 完成：

| 题 | 对照本章 |
|----|----------|
| B1 模式选择 | §2.0 / §2.4 |
| B2 Router | §2.1 / §6 |
| B3 何时不用 | §3 |
| B4 消息协议 | §4.1 |
| A1 流水线 | §2.2 |
| A2 权限隔离 | §4.2 |
| C1 批评循环 | §2.3 |

建议顺序：B3（克制）→ B2（路由）→ B4（协议）→ B1（模式）→ A1/A2 → C1。  
**先自己写，再对照本文代码。**

---

## 8. 小结与下一站

### 自检

- [ ] 能说明为何默认先单 Agent，以及「真不够」的三种信号  
- [ ] 能画出路由 / 流水线 / 辩论三种拓扑并举例  
- [ ] 能实现 `classify` + `route` + `handle`  
- [ ] 能说明 Critic 为何默认不给写工具  
- [ ] 能设计 `max_handoffs` 与唯一责任人  
- [ ] 能判断何时单 Agent 足够  

### 模块 11 收官

你已覆盖：Tool → 手写 Agent → 框架认知 → 图编排 → Memory → Multi-Agent。

下一模块：[`../12-agent-production/README.md`](../12-agent-production/README.md) —— 评测、可观测、安全、系统设计。

也可推进 Project 5/6（Tool Agent / Research Agent）——研究类项目若拆多 Agent，请带着本章护栏与克制清单上阵。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Agent Memory](./05-agent-memory.md)
- 下一模块：[Agent 工程化与生产落地](../12-agent-production/README.md)
