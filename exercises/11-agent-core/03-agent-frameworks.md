# 练习：Agent Framework 概览

> 对应文档：[`docs/11-agent-core/03-agent-frameworks.md`](../../docs/11-agent-core/03-agent-frameworks.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟  
> 运行环境：Python ≥ 3.11  
> 前置：[`02-handwritten-agent.md`](./02-handwritten-agent.md) 的状态机、`Agent.run`、FakeLLM、`authorize`

## 练习说明

1. 本章重**决策与映射**，不是安装全家桶。必做题用**表格 + 小代码 / 伪代码 / 接口对照**即可验收。
2. **不要**为完成 B/A 题安装 LangChain / LangGraph 等重型框架；可选 C 题才读一小段开源（可浏览器打开源码，不必 `pip install`）。
3. 题目分档：**热身 / 基础（必做） / 进阶（建议） / 挑战（可选）**。
4. 建议产出目录（Markdown / Python 笔记均可）：

```text
playground/11-agent-core/03-agent-frameworks/
  notes.md          # 表与决策清单
  adapter_sketch.py # 最小适配层骨架（可跑或仅类型检查）
```

5. 原则（贯穿全章）：**框架是加速器，不是理解的替代品**；说不清状态机就还不到上框架的时候。

---

## 热身题（建议先做）

### W1. 两张责任表（填空）

对照文档 §1，各写 **≥4 条**：

| 框架通常封装（省样板） | 你仍要负责（省不掉） |
|------------------------|----------------------|
| … | … |

**验收**：权限 / 评测 / 成本 / 失败策略至少出现在「你仍要负责」侧。

---

### W2. 等价物速配

把左手写概念连到框架常见角色（名称会变，抓角色即可）：

| 手写 | 框架常见名字（任写合理即可） |
|------|------------------------------|
| `messages: list[dict]` | |
| `for step in range(max_steps)` | |
| `run_tool_call(...)` | |
| `trace.append(...)` | |
| 会话存盘（若有） | |

**验收**：5 行都填了「角色级」对应，不是空着抄品牌口号。

---

## 基础题（必做）

### B1. 框架价值清单（可验收表）

完成一张「能力块 → 没有它时你要手写什么 → 它真正省下的」表，至少覆盖文档中的 **5 块**（消息适配、运行循环/图、记忆/checkpoint、tracing、RAG 或 多 Agent 任选）。

额外用 **3～5 句话**回答：为什么「上了框架」不等于「Agent 更准」？

**验收**：表完整；短文提到工具设计 / 提示 / 评测至少之一。

---

### B2. 用 / 不用决策（三场景）

对下列场景各给出：**建议（不用 / 薄封装 / 上编排框架）+ ≥2 条理由**。理由须触及「控制流复杂度 / 团队熟悉度 / 绑定容忍度」中至少一轴。

| # | 场景 |
|---|------|
| 1 | 内部小工具：查天气 + 算数，日调用量低 |
| 2 | 客服助手：检索知识库 → 可能转人工审批退款 |
| 3 | 强合规交易指令：每一步工具调用要过 ACL 与双人复核 |

**验收**：场景 1 倾向不用重框架；场景 3 强调可控 / 自管状态机或可插拔执行器——若你结论不同，须写出可辩护的反方理由。

---

### B3. 源码阅读清单（五层问题卡）

不写安装步骤。做一张「读任意 Agent 框架时带着的问题卡」，按五层列出 **每层 ≥2 个问题** + **≥1 个搜索关键词**：

1. 消息与 Tool 数据结构  
2. Agent / Executor 主循环或 Graph compile  
3. Model adapter  
4. Memory / Checkpointer  
5. Callback / Tracing  

再抄到便签上的总问题（文档原句可改写）：

> 工具结果怎样写回 messages？最大步数在哪强制停止？失败工具会不会静默吞掉？

**验收**：五层齐全；总问题三句都在你的 `notes.md` 里。

---

### B4. 绑定风险与中间态

1. 用三级（弱 / 中 / 强）描述「绑定成本」：各举一个**行为特征**（不必点名具体库）。
2. 写出一种 **中间态**：自研 `Agent.run` + 只借用一层（消息类型 / tracing / retriever / graph 执行器 四选一），说明动机与风险。
3. 决策句填空：若你说不清框架替你管了哪段 ______，就还不到上框架的时候。

**验收**：中间态写清「借用哪一层、状态机 source of truth 在哪」。

---

## 进阶题（建议至少做 1 题）

### A1. 选型维度对照表（纸上选型）

场景（固定）：「检索 → 起草工单 → 人工确认 → 执行变更」，模型可能换供应商。

完成维度表（弱/中/强或文字需求均可）：

| 维度 | 本场景需求 | 对方向的含义 |
|------|------------|--------------|
| 编排模型 | | |
| 可控性 | | |
| 可观测 | | |
| 模型适配 | | |
| 数据/RAG | | |
| 绑定成本 | | |
| 团队 | | |

最后用 **一句话结论形态**：「选 X 方向，因为…；避开 Y，因为…」——允许 X/Y 为「自研图执行器 / 轻量 SDK / 某类图框架」等**方向**，不要求锁定品牌。

**验收**：结论不是「选最火的」；可控性与人机节点被提及。

---

### A2. 手写 → 框架：迁移六步清单

对照文档 §5.5，把迁移六步写成**可勾选清单**，并在每步加一句「本仓库已有锚点」（例如 FakeLLM 用例、状态机图、`authorize`、trace 字段）。

六步骨架：

1. 冻结行为  
2. 画出状态机  
3. 映射等价物  
4. 先迁适配层  
5. 再迁编排  
6. 最后接记忆/观测插件  

**验收**：每步有 □ 勾选位 + 锚点；顺序不能改成「先改提示词再迁框架」。

---

### A3. 最小适配层（可跑小代码）

在**不引入重框架**的前提下，实现一个教学用适配层骨架，证明「业务只认统一契约」：

```python
# playground/.../adapter_sketch.py
from typing import Any, Protocol


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...
```

要求：

1. `FakeVendorA.complete` / `FakeVendorB.complete` 内部消息字段故意略有不同（如工具结果键名不同），经 `normalize_assistant` 后变成统一 assistant dict
2. 业务函数 `run_one_turn(client: LLMClient, messages, tools) -> dict` **只调用** `client.complete`
3. `authorize` 仍在工具执行前（可只留调用点 + 默认拒绝未知工具的注释或实现）
4. **禁止** `complete` 返回 `str`

**验收**：对 A/B 两个假厂商各跑一轮，业务侧断言形状一致。

---

## 挑战题（可选）

### C1. 开源执行器「寻宝」笔记（无需安装）

任选一个公开 Agent / 图执行相关仓库（文档中的方向即可），用浏览器或本地已有 clone：

1. 找到与手写 `max_steps` / `run_tool_call` / messages append **至少 2 处**等价物（文件路径 + 符号名）
2. 回答：工具失败是抛出、写入状态，还是回调吞掉？
3. 笔记控制在约 10～20 行

**验收**：有路径/符号；能回答失败语义；未要求 `pip install` 重型栈。

---

### C2. 「何时不上框架」决策清单（可打印）

做一张给自己用的 checklist（≥8 条），例如：

- [ ] 我能画出与手写 Agent 同构的状态图  
- [ ] 我能指出 max 步数硬停位置  
- [ ] …  

当未勾选项 ≥3 时，清单应建议「先不用 / 先薄封装」。

**验收**：清单可独立使用；与 B2 结论不自相矛盾。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W2
- [ ] **通过线**：B1～B4 表格/清单齐全，可在 `notes.md` 中复查
- [ ] （建议）A1 或 A2 或 A3 至少 1 题
- [ ] （可选）C1 / C2
- [ ] 能口述：框架省样板；产品逻辑、权限、评测、成本、失败策略仍是你的
- [ ] 必做题**未**依赖必须安装重型框架

---

## 提示与参考答案（先做题再看）

> 书面题给**示例答法**；代码题给完整骨架。你的理由只要自洽、可验收即可。

---

### W1 思路 + 参考答案

**思路**：分清「胶水」与「责任」；别把第 5 层产品策略塞进框架配置。

**参考答案**

| 框架通常封装（省样板） | 你仍要负责（省不掉） |
|------------------------|----------------------|
| 多厂商消息 / tool schema 适配 | 产品逻辑与提示纪律 |
| 运行循环 / 图编排样板 | 权限 / ACL / 租户隔离 |
| 记忆与 checkpoint 存取 | 评测集与回归 |
| tracing / 回调挂钩 | 成本与限流 |
| RAG 组件拼装 | 失败策略与降级 |
| 多 Agent 通讯模式 | 业务状态语义（「订单已确认」） |

---

### W2 思路 + 参考答案

**参考答案**

| 手写 | 框架常见名字（角色） |
|------|----------------------|
| `messages: list[dict]` | ChatMessage / state["messages"] |
| `for step in range(max_steps)` | AgentExecutor / graph invoke + recursion_limit |
| `run_tool_call(...)` | ToolNode / tool runtime |
| `trace.append(...)` | CallbackHandler / tracer / run tree |
| 会话存盘 | Checkpointer / MemorySaver / session store |

---

### B1 思路 + 参考答案

**思路**：框架不替你想业务；准确度来自工具、检索、提示与评测。

**参考答案（表摘录）**

| 能力块 | 没有它时你要手写什么 | 它真正省下的 |
|--------|----------------------|--------------|
| 消息 / Tool 适配 | 各厂商字段、流式拼装 | 换模型少改业务 |
| 运行循环 / 图 | `for`+路由+人机节点 | 复杂控制流显式化 |
| 记忆 / checkpoint | 截断、快照、恢复 | 长任务可暂停重放 |
| tracing | 逐步打点、run_id | 可观测与评测挂钩 |
| RAG 拼装 | loader→chunk→retrieve | 数据侧可插拔 |

短文示例：框架只加速胶水与编排；回答是否正确仍取决于工具边界、检索质量、提示纪律和你是否有评测回归。上框架却不画状态机，只会把 bug 藏进抽象层。

---

### B2 思路 + 参考答案

**思路**：用复杂度**现状**决策；预留接口比预装全家桶便宜。

**参考答案**

| 场景 | 建议 | 理由要点 |
|------|------|----------|
| 1 天气+算数 | **不用**重框架 | 线性 tool-loop；控制流简单；手写+日志足够；绑定成本不值得 |
| 2 客服+人工退款 | **考虑**图/工作流（框架或自研微型图） | 有分支与人机；需要可暂停/审批；编排价值出现 |
| 3 强合规交易 | **自研薄封装**或框架但**自管状态机** | 可控性优先；每跳 ACL+双人复核必须可审计；勿让魔法路由绕过 |

决策轴提醒：控制流复杂度 × 团队熟悉度 × 绑定容忍度。

---

### B3 思路 + 参考答案

**思路**：答案在数据结构与执行器里，不在 Quickstart 幸福路径里。

**参考答案（问题卡摘录）**

**1) 消息与 Tool**

- `role` 有哪些？tool 结果挂哪些字段？  
- `arguments` 是 str 还是 dict？谁校验？  
- 关键词：`ToolMessage` / `tool_calls` / `tool_call_id`

**2) 循环 / Graph**

- `max_iterations` / `recursion_limit` 是否硬停？  
- 无 tool_calls 如何 DONE？异常抛出还是写入状态？  
- 关键词：`AgentExecutor` / `should_continue` / `invoke`

**3) Model adapter**

- 流式 tool_calls 如何拼完整？换厂商是否改业务节点？  
- 关键词：`bind_tools` / `_convert_` / `to_openai`

**4) Memory / Checkpointer**

- 存消息全文还是状态快照？恢复后副作用是否幂等？  
- 关键词：`checkpointer` / `thread_id` / `MemorySaver`

**5) Callback / Tracing**

- 不改业务能否挂钩子？默认是否外泄完整 prompt？  
- 关键词：`CallbackManager` / `on_tool_start` / `run_id`

总问题三句：工具结果怎样写回 messages？最大步数在哪强制停止？失败工具会不会静默吞掉？

---

### B4 思路 + 参考答案

**参考答案**

1. **绑定成本**  
   - 弱：核心是你的状态机；框架可替换  
   - 中：用了其 State/Message 类型，迁移要写转换层  
   - 强：业务散落在特有 DSL / 云端专有运行时  

2. **中间态示例**：自研 `Agent.run` + 只借用 tracing callback——动机是统一观测出口；风险是 SaaS 泄密与采样要自管；**source of truth 仍是你的 `messages`/`status`**。  

3. 填空：**状态机**。

---

### A1 思路 + 参考答案

**参考答案（示例）**

| 维度 | 本场景需求 | 对方向的含义 |
|------|------------|--------------|
| 编排模型 | 人机 + 多阶段 | 偏向图/工作流，而非纯 chat SDK |
| 可控性 | 执行变更前必须 ACL | 工具执行器最好可替换 |
| 可观测 | 审批与执行可审计 | 需要清晰 span / 业务事件 |
| 模型适配 | 可能换供应商 | 业务节点勿绑死一家 request 形状 |
| 数据/RAG | 中等 | 检索可独立服务，不必全家桶 |
| 绑定成本 | 希望可迁移 | 避免强绑云端专有运行时 |
| 团队 | 假设 2 人后端 | 选能读源码的薄层或一人已熟的图库 |

结论形态示例：选「图编排 + 可替换 tool runner」方向，因为需要人机与 ACL；避开「强绑单一云 Agent 运行时」方向，因为换厂商与审计成本高。

---

### A2 思路 + 参考答案

**参考答案（可勾选）**

- [ ] **1. 冻结行为** — 锚点：FakeLLM「闲聊不调工具 / 算数走工具 / 触顶停止」用例  
- [ ] **2. 画出状态机** — 锚点：上一章 B1 图（DONE / FAILED / 人机等待）  
- [ ] **3. 映射等价物** — 锚点：messages / `run_tool_call` / `max_steps` / `trace`  
- [ ] **4. 先迁适配层** — 锚点：`LLMClient.complete -> dict`；业务工具函数先不动  
- [ ] **5. 再迁编排** — 锚点：loop → executor/graph；同一套评测必须绿  
- [ ] **6. 最后接记忆/观测** — 锚点：脱敏与字段允许列表（CONVENTIONS / 模块 12）  

纪律：先锁评测与状态机，再换执行器；ACL 保持在工具执行前。

---

### A3 思路 + 参考答案

**思路**：适配层消化厂商差异；业务与授权仍在你侧。

**参考答案**

```python
from __future__ import annotations

from typing import Any, Protocol


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """统一契约：返回 assistant dict，禁止 str。"""
        ...


def normalize_assistant(raw: dict[str, Any]) -> dict[str, Any]:
    """把不同假厂商的字段收成统一形状。"""
    role = raw.get("role") or raw.get("speaker") or "assistant"
    content = raw.get("content")
    if content is None:
        content = raw.get("text")
    tool_calls = raw.get("tool_calls")
    if tool_calls is None and "functions" in raw:
        # VendorB：用 functions 表示工具提议
        tool_calls = []
        for i, fn in enumerate(raw["functions"]):
            tool_calls.append(
                {
                    "id": fn.get("id") or f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": fn.get("name"),
                        "arguments": fn.get("arguments")
                        if isinstance(fn.get("arguments"), str)
                        else __import__("json").dumps(fn.get("arguments") or {}),
                    },
                }
            )
    out: dict[str, Any] = {"role": role, "content": content}
    if tool_calls:
        out["tool_calls"] = tool_calls
    return out


class FakeVendorA:
    """字段接近 OpenAI 兼容形。"""

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = tools, kwargs
        last = str(messages[-1].get("content") or "")
        if "算" in last:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "a1",
                        "type": "function",
                        "function": {
                            "name": "calc",
                            "arguments": '{"expr":"1+1"}',
                        },
                    }
                ],
            }
        return {"role": "assistant", "content": f"A:{last}"}


class FakeVendorB:
    """故意用 speaker/text/functions 异形字段。"""

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = tools, kwargs
        last = str(messages[-1].get("content") or "")
        if "算" in last:
            return {
                "speaker": "assistant",
                "text": None,
                "functions": [
                    {"id": "b1", "name": "calc", "arguments": {"expr": "1+1"}},
                ],
            }
        return {"speaker": "assistant", "text": f"B:{last}"}


class AdaptedClient:
    def __init__(self, vendor: Any) -> None:
        self._vendor = vendor

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        raw = self._vendor.complete(messages, tools=tools, **kwargs)
        if isinstance(raw, str):
            raise TypeError("vendor returned str; adapter refuses")
        return normalize_assistant(raw)


def authorize(role: str, tool: str, args: dict[str, Any]) -> bool:
    _ = args
    return tool in {"calc", "search"} and role in {"user", "admin"}


def run_one_turn(
    client: LLMClient,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    assistant = client.complete(messages, tools=tools)
    assert isinstance(assistant, dict) and assistant.get("role") == "assistant"
    # 若有 tool_calls：authorize → 再执行 registry（此处仅演示授权点）
    for call in assistant.get("tool_calls") or []:
        name = call["function"]["name"]
        args_raw = call["function"].get("arguments")
        import json

        args = json.loads(args_raw) if isinstance(args_raw, str) else dict(args_raw or {})
        if not authorize("user", name, args):
            raise PermissionError(f"unauthorized: {name}")
        # registry[name](**args)  ← 真正执行留在业务侧
    return assistant


def demo() -> None:
    msgs = [{"role": "user", "content": "请算 1+1"}]
    for label, vendor in ("A", FakeVendorA()), ("B", FakeVendorB()):
        client = AdaptedClient(vendor)
        out = run_one_turn(client, msgs, tools=[])
        assert out["role"] == "assistant"
        assert out.get("tool_calls")
        assert out["tool_calls"][0]["function"]["name"] == "calc"
        assert isinstance(out["tool_calls"][0]["function"]["arguments"], str)
        print(label, "ok", out["tool_calls"][0]["id"])


if __name__ == "__main__":
    demo()
```

---

### C1 思路 + 参考答案

**思路**：按 B3 五层搜符号；先看失败与停机分支。

**参考答案（笔记模板）**

```text
仓库：<name> @ <commit/日期>
1) max_steps 等价物：path/to/file.py :: recursion_limit / max_iterations
2) tool 执行等价物：path/to/tool_node.py :: ToolNode / execute_tools
失败语义：工具异常被写成 ToolMessage / 或向上抛 → <你的观察>
写回：state reducer 追加 messages / 显式 append
结论：与手写 Agent 同构处在于 loop+tool+stop；差异在 checkpoint/人机
```

---

### C2 思路 + 参考答案

**参考答案（清单示例）**

- [ ] 能画出与手写 Agent 同构的状态图  
- [ ] 能指出无 tool_calls 时的 DONE 条件  
- [ ] 能指出 max 步数硬停位置  
- [ ] 知道工具失败是否结构化写回  
- [ ] `authorize` 在执行前，而非只靠提示词  
- [ ] FakeLLM / 契约测试仍可离线绿  
- [ ] 团队有人能 debug 框架内部一层  
- [ ] 接受该层的绑定与升级成本  
- [ ] 控制流已出现图状分支 / 人机 / 长暂停（否则倾向不用）  
- [ ] 未出现「为迁就框架 API 而扭曲领域模型」

规则：未勾选 ≥3 → **先不用或只做薄封装**。

---

### 本章对照总表（复习用）

| 思想层（应掌握） | 品牌层（会变） |
|------------------|----------------|
| loop / graph / workflow | 具体库名与装饰器 |
| messages + tool_calls 协议 | 某云「Agents」产品名 |
| checkpoint / 人机节点 | 某框架类名 |
| callback / trace 字段纪律 | 某 SaaS 控制台 |
| authorize 在工具前 | 「自动安全」营销话术 |

### 五层栈（选型时拆开买、拆开弃）

```text
5) 产品与策略层     —— 业务规则、ACL、评测、预算     ← 几乎总是自研
4) 编排层           —— loop / graph / 人机
3) 能力拼装层       —— tools、memory、RAG、多 Agent
2) 模型适配层       —— messages / tool_calls 转换
1) 运行时与观测层   —— 执行、重试、trace export
```

口诀：**借用你愿意被绑的那一层；核心状态机尽量留在自己仓库语义清晰的模块里。**
