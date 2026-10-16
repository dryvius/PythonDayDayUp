# Logging

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：2～4 小时  
> 对应练习：[`exercises/03-engineering/04-logging.md`](../../exercises/03-engineering/04-logging.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：用标准库 `logging` 建立可分级、可定向、可检索的日志；为 Agent 排障与后续可观测性打底。
- **对比**：`print` 适合临时调试；项目请用 logger。

## 学习目标（学完应能做到）

1. 配置并使用 logger：level / handler / formatter。
2. 按模块获取 logger，避免根 logger 乱用。
3. 建立结构化日志直觉（字段化，而不是一长串散文）。
4. 知道请求链路字段与可观测性平台的关系（地图级）。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 层级、handler/formatter、结构化直觉 | 能在项目里落地基础日志 |
| **建议掌握** | 请求/调用链路字段 | 能为一次 Agent run 打关键字段 |
| **了解即可** | 对接观测平台 | 知道方向 |

---

## 1. 为什么要学

Agent 出问题时你想立刻知道：

```text
哪一次 run_id？
调用了哪个工具？参数？耗时？
LLM 是否 429？重试了几次？
哪一步抛错？异常栈在哪？
```

`print` 很难分级、很难关、很难收集。logging 可以：

- 按级别过滤（DEBUG/INFO/WARNING/ERROR）
- 同时输出到控制台与文件
- 统一格式，便于检索

---

## 2. 必掌握：logger 层级与级别

### 2.1 获取 logger

```python
import logging

logger = logging.getLogger(__name__)
```

`__name__` 会让日志带上模块路径，如 `app.tools.search`，方便过滤。

### 2.2 级别（从低到高）

```text
DEBUG < INFO < WARNING < ERROR < CRITICAL
```

```python
logger.debug("score=%s", score)
logger.info("tool_start name=%s", name)
logger.warning("retry attempt=%s", i)
logger.error("tool_failed name=%s", name)
logger.exception("unexpected error")  # 附带 traceback，在 except 块内用
```

习惯：用 `%s` 延迟格式化（而非 f-string 抢先拼），失败路径再用 `exception`。

---

## 3. 必掌握：handler 与 formatter

### 3.1 一次基础配置

```python
import logging


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # 避免重复添加

    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(handler)
```

在入口调用：

```python
# app/main.py
setup_logging()
logger = logging.getLogger(__name__)
logger.info("app started")
```

### 3.2 handler 是什么

| Handler | 作用 |
|---------|------|
| `StreamHandler` | 输出到控制台 |
| `FileHandler` / `RotatingFileHandler` | 写文件并轮转 |

同一个 logger 可以挂多个 handler（控制台 + 文件）。

### 3.3 子 logger 传播

默认日志会向父 logger 传播（propagate）。一般：业务模块只 `getLogger(__name__).info(...)`，在入口统一配置 root/app logger。

---

## 4. 必掌握：结构化日志直觉

不要只写：

```python
logger.info(f"出错了 {e} 工具可能是 search 吧")
```

更好：

```python
logger.error(
    "tool_failed tool=%s retryable=%s error=%s",
    tool_name,
    retryable,
    exc,
)
```

再进一步（字段化，便于 JSON 采集）：

```python
logger.info(
    "llm_call",
    extra={
        "run_id": run_id,
        "model": model,
        "latency_ms": latency_ms,
        "tokens": tokens,
    },
)
```

注意：默认 `Formatter` **不会**自动打印 `extra` 里的自定义字段；要自定义 Formatter，或改用结构化/JSON 日志库。  
本章先养成 **「事件名 + 关键字段」** 的写法；**不要把 API Key 放进 `extra`**。

---

## 5. 建议掌握：请求 / Agent 链路字段

一次 Agent 运行建议贯穿：

| 字段 | 含义 |
|------|------|
| `run_id` | 一次用户请求/任务 |
| `step` | 当前第几步 |
| `tool` | 工具名 |
| `model` | 模型名 |
| `latency_ms` | 耗时 |
| `ok` | 是否成功 |

```python
logger.info(
    "agent_step run_id=%s step=%s tool=%s ok=%s latency_ms=%s",
    run_id, step, tool, ok, latency_ms,
)
```

后面做 Observability（Tracing）时，这些字段会自然映射到 span attributes。

---

## 6. 了解即可：对接可观测性平台

日志 → 文件/stdout → 采集器 → Loki/ELK/云日志  
链路追踪 → OpenTelemetry / 厂商 Tracing  
指标 → Prometheus 等

现在只需知道：先把日志写对，平台对接是工程下一阶段。

---

## 7. 常见坑

1. 在库模块里 `basicConfig` 乱配，导致应用入口难控
2. 每个文件重新加 Handler，日志重复打印
3. 日志泄漏 API Key / 用户隐私
4. 全部 DEBUG 打爆磁盘；生产默认 INFO/WARNING
5. 用 print 与 logger 混用，风格分裂

---

## 8. 综合小例子

```python
import logging
import time
import uuid

logger = logging.getLogger(__name__)


def run_tool(name: str, fn, **kwargs):
    run_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info("tool_start run_id=%s tool=%s", run_id, name)
    try:
        result = fn(**kwargs)
    except Exception:
        logger.exception("tool_error run_id=%s tool=%s", run_id, name)
        raise
    else:
        ms = (time.perf_counter() - start) * 1000
        logger.info(
            "tool_ok run_id=%s tool=%s latency_ms=%.1f",
            run_id,
            name,
            ms,
        )
        return result
```

---

## 9. 练习指引

[`exercises/03-engineering/04-logging.md`](../../exercises/03-engineering/04-logging.md)

---

## 10. 小结与下一站

### 自检

- [ ] 能在入口配置 logging，在模块里 `getLogger(__name__)`
- [ ] 知道级别与 handler/formatter 职责
- [ ] 能按「事件 + 字段」写 Agent 关键日志

### 模块 03 收官

工程化四件套已齐：

```text
结构 → 依赖/环境 → 测试 → 日志
```

下一模块：[`../04-systems-basics/README.md`](../04-systems-basics/README.md)  
计算机与服务端基础（OS / 网络 / 并发 / DSA 精要）。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[测试（pytest）](./03-testing.md)
- 下一模块：[计算机与服务端基础](../04-systems-basics/README.md)
