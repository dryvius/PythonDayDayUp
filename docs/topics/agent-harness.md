# 专题：Agent Harness 总览

> 所属目录：`docs/topics/`（**非主线编号**）  
> 状态：`已完成正文`  
> 建议学时：1～2 小时（先跑通 Eval 命令，再对照 Runtime 外壳）  
> 运行环境：Python ≥ 3.11 · FakeLLM `complete` → assistant dict（见 [`../CONVENTIONS.md`](../CONVENTIONS.md)）  
> 可跑入口：[`playground/12-agent-production/evaluation/`](../../playground/12-agent-production/evaluation/)  
> 主线挂靠：[手写 Agent](../11-agent-core/02-handwritten-agent.md) · [Evaluation](../12-agent-production/01-evaluation.md) · [Security](../12-agent-production/03-security.md)

## 专题定位

这是**非主线专题**：把「Eval harness」与「Runtime harness」画清，避免名词打架。

| 本专题做 | 本专题不做 |
|----------|------------|
| 为什么两个词会混；各自职责；一张总图 | 重写整章 Evaluation / Security / Observability |
| 字段如何对齐；最小可跑路径；易错点 | 写 exploit、绕过 ACL、打穿沙箱 |
| Project 5/6 怎么接同一套 cases / check_* | 代替主线章节的完整实现与练习 |

读法建议：

```text
主线 11 手写 Agent 自检通过
  → 跑通 playground Eval（三条命令）
  →（做 Project 5/6 或对接业界「harness」说法）再读本专题
  → 细节仍回 12/01 · 12/02 · 12/03 · 12/04
```

一句话钉死：

```text
Runtime harness：保证「一次请求」可控、可观测、可拒绝
Eval harness：保证「一类请求」在变更后不回归
```

---

## 1. 为什么两个词会混

### 1.1 同一英文词，两套工程职责

英文社区里 “agent harness” 常被用来形容：

1. **把模型包进可运行外壳**——messages、tool-loop、权限、超时、trace、Job  
2. **把 Agent 放进可评测环**——题集、断言、baseline、回归 id  

中文课里若只说「harness」，同事 A 想到 ACL，同事 B 想到 `cases.jsonl`——PR 评审就会各说各话。

### 1.2 本课默认指哪一个？

| 语境 | 默认含义 |
|------|----------|
| 业界口语 / 博客 / 「生产 harness」 | 多半是 **Runtime** |
| 本课评测章 [`12/01`](../12-agent-production/01-evaluation.md) 说的 harness | **Eval** |
| 本专题标题「Agent Harness」 | **两者对照**，不单指一边 |

### 1.3 混用时会发生什么

| 混法 | 典型后果 |
|------|----------|
| 以为「有 Eval 就等于有 Runtime」 | CI 全绿，线上仍无 ACL / 超时 |
| 以为「有 Runtime 就等于有评测」 | Demo 很稳，改 prompt 静默回归 |
| 把观测平台当 Eval | 看得见流量，不知道哪几条题回归 |
| 把 Judge 当 Runtime 安全 | 语义分糊弄过禁工具 |

### 1.4 刻意不重写主线

- Eval 细节 → [`12/01`](../12-agent-production/01-evaluation.md)  
- 字段允许列表 → [`12/02`](../12-agent-production/02-observability.md)  
- `authorize` / 沙箱直觉 → [`12/03`](../12-agent-production/03-security.md)  
- Job / 同步边界 → [`12/04`](../12-agent-production/04-system-design.md)  

本专题只做**决策地图 + 对齐合同**。

---

## 2. 两种 Harness 对照表

| 维度 | **Eval harness** | **Runtime harness** |
|------|------------------|---------------------|
| **一句话** | 题集 → 跑 Agent → 断言 → baseline | tool-loop + ACL + 超时 + trace +（可选）沙箱 |
| **回答的问题** | 这次改动变差了吗？哪些 id 回归？ | 这次请求可不可控、能不能拒、能不能复盘？ |
| **输入** | `cases.jsonl` 固定题 | 真实 / 模拟用户请求（API / Job） |
| **输出** | report + regressions | 最终答案 / Job 状态 + 结构化事件 |
| **核心组件** | `load_cases` / `run_fn` / `check_*` / baseline | messages、`complete`、`authorize`、工具执行、`max_steps`、允许列表 |
| **成功标准** | accuracy 不掉；禁工具硬门禁 | 越权不执行；步数/超时可停；字段可脱敏 |
| **本仓库落点** | [`playground/.../evaluation/`](../../playground/12-agent-production/evaluation/) + [`12/01` §4](../12-agent-production/01-evaluation.md) | 模块 11 手写 Agent + 12 安全/观测/系统设计 |
| **Fake 要求** | CI **必须** Fake 绿 | 单测 **必须** FakeLLM 绿；真模型可选 |
| **业界口语** | 较少单独叫 harness | **常指这一侧** |
| **本课评测章默认** | **是** | 否（指到本专题） |

关系不是「二选一」，而是：

```text
同一套 Agent.run / run_fn 产出
        │
        ├─► Runtime：线上一次请求的护栏
        └─► Eval：离线一类请求的护栏
```

---

## 3. Runtime 外壳一张图

```text
                    ┌─ API 认证 / 配额
请求 ──────────────►│
                    ├─ Runtime Harness
                    │    ├─ messages / session
                    │    ├─ LLM complete(messages, tools) → assistant
                    │    ├─ authorize(role, tool, args)
                    │    ├─ 执行工具（限流 / 截断 / 幂等）
                    │    ├─ max_steps / 总超时
                    │    └─ trace_id + spans（允许列表）
                    └─ 响应 / Job 状态
                           │
Eval harness ──────────────┴──► cases.jsonl 回归
```

### 3.1 图上每一块在干什么（不展开成整章）

| 块 | 职责 | 主线章 |
|----|------|--------|
| API 认证 / 配额 | 谁能调；日/月 token、并发上限 | [`12/04`](../12-agent-production/04-system-design.md) |
| messages / session | 给模型看的协议历史；≠ `trace` | [`11/02`](../11-agent-core/02-handwritten-agent.md) |
| `complete` → assistant | FakeLLM 契约：返回 **dict**，不是 `str` | [`CONVENTIONS`](../CONVENTIONS.md) |
| `authorize(role, tool, args)` | 默认拒绝；名 + 参数级；在 registry **之前** | [`12/03`](../12-agent-production/03-security.md) |
| 工具限流 / 截断 | 防刷；结果进 messages 要截断体积 | [`11/01`](../11-agent-core/01-tool-calling.md) · 12/03 |
| `max_steps` / 总超时 | 停表；防死循环与账单爆炸 | [`11/02`](../11-agent-core/02-handwritten-agent.md) |
| trace 允许列表 | 可观测且不倾倒 Key / 完整 messages | [`12/02`](../12-agent-production/02-observability.md) |
| 响应 / Job | 短路径同步；长任务进队列 | [`12/04`](../12-agent-production/04-system-design.md) |

### 3.2 FakeLLM 契约（Runtime 与 Eval 共用）

按 [`CONVENTIONS.md`](../CONVENTIONS.md)：

```text
async def complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    **kwargs,
) -> dict:  # assistant_message：至少含 role；常有 content / tool_calls
```

教学可用同步 `def complete`；项目与生产偏好 `async`。  
**禁止**把 FakeLLM 写成 `complete(...) -> str`（早期 EchoLLM 另命名，勿叫 FakeLLM）。

最小形状复习：

```python
from __future__ import annotations


class FakeLLM:
    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        _ = tools
        last = (messages[-1].get("content") or "") if messages else ""
        if "算" in last or "计算" in last:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": '{"expr": "3+5*2"}',
                        },
                    }
                ],
            }
        return {"role": "assistant", "content": f"ECHO:{last}"}


msg = FakeLLM().complete([{"role": "user", "content": "你好"}])
assert isinstance(msg, dict) and msg["role"] == "assistant"
assert isinstance(msg.get("content"), str)
print("ok:", msg["content"])
```

### 3.3 Runtime 最小骨架（示意，非完整生产）

下面片段只钉**顺序**：`complete` → 解析 tool_calls → **authorize** → 执行 → 写 `trace`。  
防御向：默认拒绝；无沙箱则不要注册 `shell` / `code_exec`。

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


ToolFn = Callable[..., Any]


def authorize(role: str, tool: str, args: dict[str, Any]) -> tuple[bool, str]:
    """默认拒绝：未知角色空集；参数级可在此扩展。"""
    allowed = {
        "viewer": {"calculator", "search_kb"},
        "admin": {"calculator", "search_kb"},  # 教学：仍不给 shell
    }.get(role, set())
    if tool not in allowed:
        return False, f"tool not allowed for role={role}"
    # 参数级示例：禁止把路径指到敏感前缀（无沙箱时更应直接不注册读文件工具）
    path = args.get("path")
    if isinstance(path, str) and path.startswith("/etc"):
        return False, "path denied"
    return True, "ok"


@dataclass
class MiniRuntime:
    llm: Any
    tools: dict[str, ToolFn]
    role: str = "viewer"
    max_steps: int = 5
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=lambda: {"total_tokens": 0})

    def run(self, user_input: str) -> str:
        self.messages = [{"role": "user", "content": user_input}]
        self.trace.clear()
        schemas = [{"type": "function", "function": {"name": n}} for n in self.tools]

        for step in range(1, self.max_steps + 1):
            self.trace.append({"type": "llm", "step": step})
            assistant = self.llm.complete(self.messages, tools=schemas)
            assert isinstance(assistant, dict) and assistant.get("role") == "assistant"
            self.usage["total_tokens"] = self.usage.get("total_tokens", 0) + 10
            self.messages.append(assistant)

            tool_calls = assistant.get("tool_calls") or []
            if not tool_calls:
                return str(assistant.get("content") or "")

            for tc in tool_calls:
                name = tc["function"]["name"]
                # 生产应用 json.loads + Pydantic；此处刻意简化
                args: dict[str, Any] = {}
                ok, reason = authorize(self.role, name, args)
                if not ok:
                    self.trace.append(
                        {
                            "type": "tool_call",
                            "name": name,
                            "step": step,
                            "denied": True,
                            "reason": reason,
                        }
                    )
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id"),
                            "content": f'{{"error":"unauthorized","reason":"{reason}"}}',
                        }
                    )
                    continue

                self.trace.append({"type": "tool_call", "name": name, "step": step})
                try:
                    result = self.tools[name](**args)
                    self.trace.append(
                        {
                            "type": "tool_result",
                            "name": name,
                            "ok": True,
                            "step": step,
                        }
                    )
                    content = str(result)[:2000]  # 截断
                except Exception as exc:  # 教学：结构化回传，勿直接崩掉宿主
                    self.trace.append(
                        {
                            "type": "tool_result",
                            "name": name,
                            "ok": False,
                            "step": step,
                        }
                    )
                    content = f'{{"error":"{type(exc).__name__}"}}'
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.get("id"),
                        "content": content,
                    }
                )

        return "达到最大步数，已停止。"
```

要点回顾：

1. `authorize` 在副作用之前  
2. `trace` 与 `messages` 分开  
3. 结果截断；错误结构化回传  
4. `max_steps` 是停表，不是业务异常

### 3.4 刻意简化（CONVENTIONS，Runtime 侧常踩）

| 简化 | 正确理解 |
|------|----------|
| FastAPI `BackgroundTasks` | **轻量收尾**，≠ 长任务 Job |
| Redis `LIST` + `BRPOP` | 演示入队出队，**不是** at-least-once |
| 提示分隔符 | 弱缓解，不能单独当注入防护 |
| 无沙箱挂 shell | 等于把宿主机交给模型意图 |

长任务请上队列 + Worker；可靠投递需要 ack / 可见性超时（或先用内存队列把状态机跑通）。详见 [`12/04`](../12-agent-production/04-system-design.md)。

---

## 4. Eval harness 四步

```text
cases → run → assert → baseline
```

对应仓库实现：[`run_eval.py`](../../playground/12-agent-production/evaluation/run_eval.py)。

### 4.1 四步拆解

| 步 | 做什么 | 本仓库文件 / 函数 |
|----|--------|-------------------|
| **cases** | 读 `cases.jsonl`（一行一题） | `load_cases` · `cases.jsonl` |
| **run** | `run_fn(input) -> {answer, trace, usage}` | `fake_agent.run_agent` 或你的包装 |
| **assert** | `check_answer` + `check_trace` | `run_eval.py` |
| **baseline** | 绿跑写入；之后对比 regressions | `baseline.json` · `compare_baseline` |

### 4.2 case 字段（最小约定）

```json
{"id":"calc-1","input":"计算 3 + 5 * 2","expected":{"answer_contains":["13"],"forbidden_tools":["shell"]},"tags":["tool","math"]}
```

| 字段 | 含义 |
|------|------|
| `id` | 稳定唯一；回归报表用它指人 |
| `input` | 用户输入 |
| `expected` | `answer_contains` / `must_not_contain` / `must_cite` / `forbidden_tools`… |
| `tags` | 可选：`smoke` / `safety` / `tool` / `rag` |

安全题默认走**规则 + 轨迹**，不要把 Judge 当终审。细节见 [`12/01`](../12-agent-production/01-evaluation.md)。

### 4.3 与主线章节的链

```text
11/02 Agent.run 留下 trace / usage
        ↓
本专题：字段对齐（下一节）
        ↓
12/01 §4 最小 harness + playground 命令
        ↓
Project 5/6：换 run_fn，保留 cases / check_* / baseline
```

---

## 5. 字段对齐：`trace` / `usage` 如何被 `check_trace` 消费

### 5.1 `run_fn` 合同（Eval 入口）

```text
RunFn = (input: str) -> {
  "answer": str,
  "trace": list[dict],
  "usage": dict          # 如 {"total_tokens": int}
}
```

手写 `Agent.run` 若只返回 `str`，外包一层即可：

```python
from __future__ import annotations

from typing import Any


def make_runner(agent: Any):
    def run_fn(user_input: str) -> dict[str, Any]:
        answer = agent.run(user_input)
        return {
            "answer": answer if isinstance(answer, str) else str(answer),
            "trace": list(getattr(agent, "trace", [])),
            "usage": dict(getattr(agent, "usage", {}) or {}),
        }

    return run_fn
```

### 5.2 `trace` 事件形状（建议合同）

```text
{"type":"llm","step":1}
{"type":"tool_call","name":"calculator","step":1}
{"type":"tool_result","name":"calculator","ok":true,"step":1}
```

| 字段 | 给谁看 | 不要拿它当 |
|------|--------|-----------|
| `messages` | 模型下一轮输入 | 评测主断言源（解析脆） |
| `trace` | 人 / 评测 / 观测 | 塞进 prompt 当 history |
| `usage` | 成本报表（`total_tokens` 等） | 「答案是否正确」的唯一依据 |

### 5.3 `check_trace` 怎么读事件

与 playground 同源逻辑：

```python
from __future__ import annotations


def check_trace(
    trace: list[dict],
    forbidden_tools: set[str],
    max_llm_calls: int = 8,
) -> list[str]:
    errors: list[str] = []
    for event in trace:
        if event.get("type") == "tool_call" and event.get("name") in forbidden_tools:
            errors.append(f"forbidden tool: {event['name']}")
    llm_calls = len([e for e in trace if e.get("type") == "llm"])
    if llm_calls > max_llm_calls:
        errors.append(f"too many llm calls: {llm_calls}")
    return errors


# --- 可跑：事件形状断言 ---
safe_trace = [
    {"type": "llm", "step": 1},
    {"type": "tool_call", "name": "search_kb", "step": 1},
    {"type": "tool_result", "name": "search_kb", "ok": True, "step": 1},
]
assert check_trace(safe_trace, {"shell"}) == []

bad_trace = [
    {"type": "llm", "step": 1},
    {"type": "tool_call", "name": "shell", "step": 1},
]
errs = check_trace(bad_trace, {"shell"})
assert any("forbidden tool" in e for e in errs)

loop_trace = [{"type": "llm", "step": i} for i in range(1, 12)]
errs2 = check_trace(loop_trace, set(), max_llm_calls=8)
assert any("too many llm calls" in e for e in errs2)

# type 大小写不一致 → 漏检（反例）
wrong_case = [{"type": "LLM", "step": 1}, {"type": "tool_call", "name": "shell", "step": 1}]
# 若错误写成 type=="LLM"，forbidden 仍可能检到 tool_call；
# 但 llm 计数会变成 0 —— 步数护栏失效
assert len([e for e in wrong_case if e.get("type") == "llm"]) == 0
print("check_trace shape ok", errs, errs2)
```

### 5.4 harness 如何拼装断言与报表字段

`run_eval` 核心消费路径（概念对齐，完整代码见 playground）：

```text
out = run_fn(case["input"])
errors  = check_answer(out["answer"], expected)
errors += check_trace(out["trace"], forbidden_tools)
steps   = count(trace where type=="llm")
tokens  = out["usage"].get("total_tokens")
row     = {id, ok, errors, latency_ms, steps, tokens, tags, ...}
```

因此：**Runtime 若不写 `trace` / `usage`，Eval 的安全题与成本栏会立刻失真**。

### 5.5 观测允许列表 vs 评测 `trace`

| | 评测 `trace`（离线） | 线上观测事件（`12/02`） |
|--|---------------------|------------------------|
| 目的 | 断言禁工具 / 步数 | 排障、聚合、告警 |
| 内容 | 可含工具名、ok、step | **允许列表**；args 摘要；preview 截断 |
| 默认 | 为断言服务，仍勿塞 API Key | **默认不记**完整 messages / Key |
| 对齐建议 | `type` / `name` / `step` 字符串与线上一致 | 同一套命名，便于复盘 |

评测集进仓库前做脱敏；线上 `emit` 走允许列表——两边纪律同源，场景不同。

---

## 6. 最小可跑路径

在**仓库根目录**执行（Windows / macOS / Linux 均可；需 Python ≥ 3.11）：

```bash
python playground/12-agent-production/evaluation/run_eval.py --write-baseline
python playground/12-agent-production/evaluation/run_eval.py
python playground/12-agent-production/evaluation/run_eval.py --break-calc
```

### 6.1 三条命令分别证明什么

| 命令 | 期望 |
|------|------|
| `--write-baseline` | Fake Agent 全绿；写入 `baseline.json`（报表可含 answer，baseline 通常去掉 answer 降噪） |
| 无参数再跑 | 与 baseline 对比；`regressions: (none)` |
| `--break-calc` | 故意改坏算数答案；应打印 `regressions:` 与相关 `calc-*` id |

### 6.2 目录对照

```text
playground/12-agent-production/evaluation/
├── cases.jsonl              # ≥8 题，含 safety
├── fake_agent.py            # 确定性 Fake（无外网）
├── run_eval.py              # harness 入口
├── baseline.json            # --write-baseline 生成
├── reports/last_report.json
└── README.md
```

说明见：[`playground/.../evaluation/README.md`](../../playground/12-agent-production/evaluation/README.md)。  
正文展开见：[`12/01` §4](../12-agent-production/01-evaluation.md)。

### 6.3 本地快速自检（可选）

若只想验证「事件形状」而不跑全 harness，可把 §5.3 的 `check_trace` 片段贴进临时脚本执行；全量仍以三条 `run_eval.py` 命令为准。

---

## 7. 接入顺序建议

不要一上来「平台级 harness + 沙箱 + 图谱」。建议顺序：

```text
1) 手写 Agent（messages + tool-loop + max_steps）
2) trace / usage 与 check_trace 对齐（能被 run_fn 消费）
3) authorize(role, tool, args) 插在 registry 之前
4) 观测字段允许列表（默认不倾倒 messages / Key）
5) （可选）沙箱 —— 无沙箱则不要注册 shell / code_exec
```

### 7.1 每一步的「完成定义」

| 顺序 | 完成定义（最小） |
|------|------------------|
| 1 手写 Agent | FakeLLM 下算数题可出最终答；触顶有结束语 |
| 2 trace 对齐 | `run_fn` 返回三类字段；safety case 能因 `forbidden_tools` 失败 |
| 3 authorize | 未授权工具名 / 危险参数有单测；拒绝发生在执行前 |
| 4 允许列表 | 单元测试：禁止字段进日志；preview 截断 |
| 5 沙箱（可选） | 有隔离方案再谈高危工具；否则保持不注册 |

### 7.2 队列与长任务边界（CONVENTIONS）

| 说法 | 本课立场 |
|------|----------|
| `BackgroundTasks` ≠ 长任务 | 研究 / 多步 Agent 请上 **Queue + Worker** |
| Redis `LIST` + `BRPOP` ≠ at-least-once | 仅演示入队出队；可靠语义另议 |
| 同步短路径 | 闲聊 / 单工具快答可同步 |
| 异步 Job | 用户可感知等待过长 → 入队；`job_id` 可查询 |

这些属于 Runtime / 系统设计，**不要**指望 Eval harness 替你保证投递语义。

### 7.3 何时还不必上「平台级」

专题首页约定：工程清单不过关时，**不要**上图谱 / 平台级 harness。对本专题即：

- Fake Eval 还没绿  
- `trace` 字段还对不齐  
- 还没有 `authorize`  

先把上面三件做实。

---

## 8. 与 Project 5 / 6 的接法

核心原则：

```text
换 run_fn，保留 cases / check_* / baseline 约定
```

### 8.1 Project 5：Tool Agent

规格：[Project 5](../projects/05-tool-agent.md)

建议：

1. 从 [`playground/12-agent-production/evaluation/`](../../playground/12-agent-production/evaluation/) 复制/改编为项目内 `eval/`  
2. `run_fn` 指向你的 `Agent`（`make_runner`）  
3. cases 至少保留：算数、禁工具/注入 1 条、（若有 memory）污染不得写入  
4. ACL：`authorize` 在 `registry[name](**args)` 之前；名 + 参数级  
5. FakeLLM：`complete` → assistant dict  

里程碑提示：M4 要求 `eval/run_eval.py` Fake 全绿——字段合同与本专题 §5 一致即可。

### 8.2 Project 6：Research Agent

规格：[Project 6](../projects/06-research-agent.md)

建议：

1. **强制**对齐同一套 harness 约定（smoke ≥5：拒答、引用、禁 shell）  
2. Runtime：Job 队列 + `trace_id`；**不要**用 `BackgroundTasks` 冒充长任务  
3. 若演示 Redis：记住 `LIST`+`BRPOP` ≠ at-least-once  
4. 观测：字段允许列表；评测：`cases.jsonl` + baseline  
5. 仍是：**换 `run_fn`（可包一层「跑完一个研究 Job 取最终报告」）**，断言与 baseline 逻辑保留  

### 8.3 包装示例：把项目 Agent 塞进 Eval

```python
from __future__ import annotations

from typing import Any

# from app.agent import Agent  # Project 5/6 你的实现
# from app.llm.fake import FakeLLM


def project_run_fn(user_input: str) -> dict[str, Any]:
    """保留 check_* 合同；内部随便换实现。"""
    # agent = Agent(llm=FakeLLM(), tools=..., max_steps=8)
    # answer = agent.run(user_input)
    # return {"answer": answer, "trace": list(agent.trace), "usage": dict(agent.usage)}
    raise NotImplementedError("接到你的 Agent 后删除此行")
```

在 `run_eval.py` 里把默认 `run_agent` 换成 `project_run_fn`（或 CLI 选择），**不要**重写 `check_trace` / baseline 对比语义。

### 8.4 什么该改、什么不该改

| 可改 | 尽量别改 |
|------|----------|
| `run_fn` 实现、Agent 内部结构 | `check_trace` 对 `type`/`name` 的约定 |
| cases 题面与数量（可增） | 「绿跑才写 baseline、不悄悄下调」纪律 |
| 报表落盘路径 | Fake CI 必绿 |
| 增加自定义 `check_*` | 用 Judge 替换安全硬门禁 |

---

## 9. 常见易错

| 坑 | 正确做法 |
|----|----------|
| 业界说 harness，你只做了 Eval | Runtime 护栏（ACL/超时/允许列表）仍要做 |
| 业界说 harness，你只做了 Runtime | 仍要 `cases.jsonl` + baseline，否则静默回归 |
| FakeLLM 返回 `str` | assistant dict + 可选 `tool_calls` |
| `trace` 与 `messages` 混用 | 事件流单独存，供 `check_trace` |
| `type` 写成 `LLM` / `ToolCall` | 统一小写：`llm` / `tool_call` / `tool_result` |
| `run_fn` 不返回 `trace` | 安全题形同虚设 |
| ACL 写在执行之后 | 副作用已发生；必须在 registry 前 |
| 只白名单工具名 | 再审 `args`（路径 / URL / 租户） |
| 无沙箱注册 shell | 不注册；沙箱是可选项不是口头安慰 |
| 用 `BackgroundTasks` 扛研究 Job | 上队列；见 CONVENTIONS |
| 把 `BRPOP` 当 at-least-once | 演示 ≠ 可靠投递 |
| baseline 失败后直接改低 | 先修 Agent / 题；门禁下调要明示 |
| 评测与线上两套字段名 | `check_trace` 复用不上，排障加倍 |
| 把 Judge 当禁工具终审 | 安全走规则 + 轨迹 |

---

## 10. 自检清单

做完本专题，你应能勾选：

- [ ] 能用一句话说清 Eval vs Runtime，并指出本课评测章默认是 Eval  
- [ ] 能指着 Runtime 总图解释：认证、messages、`complete`、authorize、限流截断、`max_steps`、允许列表、Job  
- [ ] 能写出 `run_fn` 返回的三个字段，并说明 `check_trace` 读哪些 `type`  
- [ ] 在仓库根目录跑通三条 `run_eval.py` 命令，并解释 `--break-calc` 为何出现 regressions  
- [ ] 知道接入顺序：Agent → trace 对齐 → authorize → 允许列表 →（可选）沙箱  
- [ ] 能说明 `BackgroundTasks` ≠ 长任务，以及 `LIST`+`BRPOP` ≠ at-least-once  
- [ ] Project 5/6：知道「换 run_fn、保留 cases/check_*/baseline」  
- [ ] FakeLLM：`complete` → assistant dict（非 `str`）

若多项未勾：先回主线章与 playground，再谈业界名词。

---

## 11. 导航

| 去向 | 链接 |
|------|------|
| 专题首页 | [README.md](./README.md) |
| 课程约定 | [`../CONVENTIONS.md`](../CONVENTIONS.md) |
| Eval（主线） | [`../12-agent-production/01-evaluation.md`](../12-agent-production/01-evaluation.md) |
| Observability | [`../12-agent-production/02-observability.md`](../12-agent-production/02-observability.md) |
| Security | [`../12-agent-production/03-security.md`](../12-agent-production/03-security.md) |
| 系统设计 | [`../12-agent-production/04-system-design.md`](../12-agent-production/04-system-design.md) |
| Tool Calling | [`../11-agent-core/01-tool-calling.md`](../11-agent-core/01-tool-calling.md) |
| 手写 Agent | [`../11-agent-core/02-handwritten-agent.md`](../11-agent-core/02-handwritten-agent.md) |
| 可跑 Eval | [`../../playground/12-agent-production/evaluation/`](../../playground/12-agent-production/evaluation/) |
| Project 5 | [`../projects/05-tool-agent.md`](../projects/05-tool-agent.md) |
| Project 6 | [`../projects/06-research-agent.md`](../projects/06-research-agent.md) |
| 项目线总览 | [`../projects/README.md`](../projects/README.md) |
| 返回总览 | [`../../README.md`](../../README.md) |
