# 课程约定（Conventions）

学习与写练习时默认遵守本页，避免版本/语义打架。

## 1. Python 版本

- **推荐：Python ≥ 3.11**（与 `pyproject` 示例、`TaskGroup`、`ExceptionGroup`、`TimeoutError` 别名一致）
- 可用 3.12（Dockerfile 示例用 `python:3.12-slim`）
- 注解写法默认 `list[str]`、`str | None`（勿再教 `List`/`Optional` 为唯一写法）

## 2. FakeLLM / LLMClient 约定

无 API Key 时：

- 用规则/关键词驱动的 FakeLLM 跑通工具环与评测
- **统一契约**（模块 09 起、项目线强制）：

```text
async def complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    **kwargs,
) -> dict:  # assistant_message：至少含 role；常有 content / tool_calls
```

- 纯文本场景取 `message["content"]`，不要让 `complete` 直接返回 `str`
- 早期语言章可用 `EchoLLM.complete(prompt) -> str` 教学，**勿命名为 FakeLLM**
- 手写 Agent 教学可用同步 `def complete`；项目与生产偏好 `async`
- 单测与 CI **必须**可在 FakeLLM 下绿；真模型作为可选升级

## 3. 重点分级

| 标记 | 含义 |
|------|------|
| **必掌握** | 写透、必练、模块自检要会 |
| **建议掌握** | 明显提升质量，时间紧可后补 |
| **了解即可** | 建立地图，防止过载 |

## 4. 已知刻意简化（别当生产真理）

- Redis `LIST`+`BRPOP`：演示入队出队，**不是** at-least-once
- 提示分隔符：弱缓解，**不能**单独当注入防护
- LangGraph 玩具执行器：需用 reducer/append 语义；勿与库 API 一一对应
- FastAPI `BackgroundTasks`：轻量收尾，长任务请上队列
- 教学用 API Key `!=` 比较：生产应考虑恒定时间比较

更完整的知识点勘误会随修订直接改正文；本页只列「刻意简化」。

## 5. 仓库布局提醒

| 路径 | 用途 |
|------|------|
| `docs/` | 正文 |
| `docs/topics/` | 非主线专题（记忆工程进阶、Harness 总览等） |
| `exercises/` | 练习与验收 |
| `docs/projects/` | 阶段性项目 |
| `playground/` | 实验与**可跑最小示例**（Memory Store、Eval harness 等） |

可跑入口：

- Memory：`playground/11-agent-core/memory/`
- Eval harness：`playground/12-agent-production/evaluation/`

## 导航

- 返回总览：[../README.md](../README.md)
- 项目线：[projects/README.md](./projects/README.md)
- 专题：[topics/README.md](./topics/README.md)
