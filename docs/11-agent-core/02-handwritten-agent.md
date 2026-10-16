# 手写一个 Agent

> 所属模块：`11-agent-core` · Agent 核心开发  
> 状态：`已完成正文`  
> 建议学时：4～7 小时  
> 对应练习：[`exercises/11-agent-core/02-handwritten-agent.md`](../../exercises/11-agent-core/02-handwritten-agent.md)

## 本章定位

- **本章角色**：不靠重框架，手写 tool-loop Agent；建立状态机与错误恢复直觉。
- **价值**：框架换代你也不慌——循环本质相同。
- **产出**：可单测的 `Agent.run` + FakeLLM。

## 学习目标

1. 分清古典 ReAct 文本协议与现代 tool_calls 循环。
2. 用状态机描述 Agent 运行。
3. 实现可运行的最小 Agent（含轨迹）。
4. 加入错误恢复、重复调用熔断、max_steps。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | tool loop、状态机、最小实现、终止条件 | 能手写跑通并测 |
| **建议掌握** | 错误恢复、FakeLLM、轨迹 | 更稳、可测 |
| **了解即可** | 规划算法变体 | 扫盲 |

---

## 1. ReAct 思想 vs 现代 tool-loop

古典 ReAct：在**提示文本**里显式交替 `Thought / Action / Observation`。

```text
Thought → Action(tool) → Observation → … → Final Answer
```

本章及多数生产 API：实现的是 **tool-loop（工具环）**——模型返回结构化 `tool_calls`，服务端执行再回传。  
「Thought」常被协议吸收，不必强行输出 Thought 散文。思想同源，协议形态不同；下文「手写 Agent」默认指 **tool-loop**，不是古典文本协议。

---

## 2. 必掌握：状态机直觉

```text
IDLE → CALLING_LLM → (NEED_TOOLS → EXECUTING_TOOLS → CALLING_LLM)* → DONE
                                                      ↘ FAILED
```

状态里至少有：

```python
messages: list[dict]
step: int
status: str  # running | done | failed | max_steps
```

建议另存 `trace: list[dict]`（每步事件），便于评测与排障（模块 12）。

---

## 3. 必掌握：最小 Agent 实现

```python
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Agent:
    # 教学可用同步 complete；项目线偏好 async（见 CONVENTIONS）
    llm: Any  # complete(messages, tools=None) -> assistant_message(dict)
    tools: dict[str, Callable[..., Any]]
    max_steps: int = 5
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        tool_defs = build_tool_defs(self.tools)
        last_sig: str | None = None
        repeats = 0

        for step in range(1, self.max_steps + 1):
            self.trace.append({"type": "llm", "step": step})
            assistant = self.llm.complete(self.messages, tools=tool_defs)
            self.messages.append(assistant)

            tool_calls = assistant.get("tool_calls") or []
            if not tool_calls:
                return assistant.get("content") or ""

            # content 与 tool_calls 可同时存在：先执行工具，勿当最终答
            sig = str([(c.get("function", {}).get("name"), c.get("function", {}).get("arguments")) for c in tool_calls])
            if sig == last_sig:
                repeats += 1
                if repeats >= 2:
                    return "检测到重复工具调用，已停止"
            else:
                repeats = 0
                last_sig = sig

            for call in tool_calls:
                self.trace.append({"type": "tool_call", "name": call["function"]["name"], "step": step})
                tool_msg = run_tool_call(call, self.tools)  # 见上一章：校验 + 错误 JSON
                self.messages.append(tool_msg)

        return "达到最大步数，已停止"
```

依赖上一章的 `run_tool_call` / `build_tool_defs`；未知工具与非法 JSON 必须结构化回传。

---

## 4. 建议掌握：FakeLLM（可测）

```python
class FakeLLM:
    def complete(self, messages: list[dict], tools=None) -> dict:
        last = messages[-1]["content"] if messages else ""
        # 已有 tool 结果 → 给最终答
        if messages and messages[-1].get("role") == "tool":
            return {"role": "assistant", "content": f"根据工具结果：{messages[-1].get('content')}"}
        # 关键词触发工具
        if "计算" in last or "算" in last:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "calculator", "arguments": "{\"expr\": \"1+2\"}"},
                }],
            }
        return {"role": "assistant", "content": f"ECHO:{last}"}
```

原则：确定性、覆盖「要工具 / 不要工具 / 工具后收尾」三条路径。

---

## 5. 建议掌握：错误恢复

| 情况 | 策略 |
|------|------|
| 工具抛异常 | 错误 JSON 进 tool 消息，让模型改参或换工具 |
| 非法 arguments | 校验失败信息回传，计数；连续失败则 FAILED |
| LLM 超时 | 有限退避；超限 FAILED |
| 重复相同 tool_call | 熔断（见上） |
| 空 content 且无 tool_calls | 视为失败或重试一次 |

不要无限 extra 轮「再试一次」烧钱。

---

## 6. 常见坑

1. 把 `messages` 在每次 `run` 间不清空也不分 session → 串话  
2. 只测最终字符串，不测是否乱调工具  
3. FakeLLM 太聪明/太随机 → CI 红绿不定  
4. max_steps 很大却无超时 → 挂死  
5. 在 Agent 里直接执行未 ACL 的危险工具  

---

## 7. 了解即可：规划变体

Plan-and-Execute、Reflection、Tree-of-Thoughts……先把 tool loop 做稳，再在「计划节点」上扩展（下一章图编排更合适）。

---

## 8. 练习指引

[`exercises/11-agent-core/02-handwritten-agent.md`](../../exercises/11-agent-core/02-handwritten-agent.md)  
实战集成见 [Project 5：Tool Agent](../projects/05-tool-agent.md)。

---

## 9. 小结与下一站

### 自检

- [ ] 能画出状态机并指出终止边
- [ ] FakeLLM 下能测「算数走工具 / 闲聊不走工具」
- [ ] 触顶与重复调用有确定行为

### 下一章

[`03-agent-frameworks.md`](./03-agent-frameworks.md) —— 何时引入框架、如何读源码。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Tool Calling](./01-tool-calling.md)
- 下一章：[Agent Framework 概览](./03-agent-frameworks.md)
