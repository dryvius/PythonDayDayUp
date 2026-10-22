# 练习：Logging

> 对应文档：[`docs/03-engineering/04-logging.md`](../../docs/03-engineering/04-logging.md)  
> 状态：`已完成出题`  
> 建议用时：45～75 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：级别、`getLogger(__name__)`、handler/formatter、防重复配置、字段化直觉。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/03-engineering/04-logging/
├── app/
│   ├── __init__.py
│   ├── logging_config.py
│   ├── tools.py
│   ├── agent.py
│   └── runner.py
└── main.py
```

4. 观测约定对齐 `CONVENTIONS.md`：默认不要把完整 prompt / API Key 打进日志；`args` 用摘要。
5. Python ≥ 3.11；先做题再看文末答案。

---

## 热身题（建议先做）

### W1. `print` vs logger 一句话

**要求**：写一句：项目里为什么不能长期靠 `print` 排障 Agent。

**验收**：点到分级 / 关闭 / 收集中至少两点。

---

### W2. 级别排序

**要求**：按从低到高写出：DEBUG、INFO、WARNING、ERROR（可不写 CRITICAL）。

**验收**：顺序正确。

---

### W3. `__name__` 是什么

**要求**：在模块里 `logger = logging.getLogger(__name__)`，直接跑脚本与被 import 时 `logger.name` 可能有何不同（一句话）。

**验收**：能说到 `__main__` vs 包路径。

---

## 基础题（必做）

### B1. `setup_logging`

实现 `setup_logging(level: int = logging.INFO) -> None`：

- 配置 root：`StreamHandler` + Formatter（至少含时间、级别、`%(name)s`、消息）
- **重复调用不导致双份日志**（有 handler 则直接 return）

入口调用后：

```python
logging.getLogger(__name__).info("hello")
```

应能看到格式化输出。

**验收**：控制台有时间与级别；连续调用两次 `setup_logging()` 仍只有一份 handler 输出。

---

### B2. 模块 logger

两个模块 `app/tools.py` 与 `app/agent.py` 各自：

```python
logger = logging.getLogger(__name__)
```

分别打不同事件（如 `tool_start` / `agent_step`）。观察日志中的 `[name]` 是否不同。

**验收**：能区分来源模块（名字里能看出 `tools` vs `agent`）。

---

### B3. exception 日志

写一个会抛错的函数，在 `except` 里用 `logger.exception(...)`。  
确认输出含 traceback。

**验收**：堆栈可见；不要只用 `logger.error(str(e))` 交差。

---

### B4. 结构化字段风格

把一次假工具调用打成一行字段化日志，至少含：`run_id`、`tool`、`ok`、`latency_ms`。

推荐风格（标准库阶段完全合格）：

```text
tool_ok run_id=a3f2 tool=search ok=True latency_ms=12.3
```

**验收**：字段齐全可读；**不要**打印假 API Key 或完整 Authorization。

---

## 进阶题（建议至少做 1 题）

### A1. 文件 handler

在 `setup_logging` 中增加 `FileHandler` 或 `RotatingFileHandler`，同时输出到控制台与 `app.log`。

**验收**：跑一次后磁盘上有 `app.log`，内容与控制台关键事件一致。

---

### A2. 级别过滤

演示：

1. root 设 INFO 时 DEBUG 不可见
2. 临时调到 DEBUG 后可见

写进 `a2_notes.md`（含你看到的现象）。

**验收**：笔记描述两种现象；明白 logger 与 handler 两边级别都要够低。

---

## 挑战题（可选）

### C1. `run_tool` 包装器

实现文档综合例子风格的 `run_tool`：

- 成功：`tool_ok` + `latency_ms`
- 失败：`logger.exception` 的 `tool_error`，并继续抛出

写 2 个手工演示：一次成功、一次失败。

**验收**：两种路径日志都有；失败路径含 traceback。

---

## 模块 03 通关自检

- [ ] 能搭清爽的 `app/` 结构
- [ ] 会 venv / 依赖声明 / 环境变量
- [ ] 会为纯逻辑写 pytest
- [ ] 会配置 logging 并字段化记录 Agent 关键事件

全部完成后进入模块 04《计算机与服务端基础》。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W3
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

### W1 参考答案

`print` 不能按级别过滤、难统一收集到文件/平台、也无法在生产关掉噪音；Agent 排障需要 `run_id` / 工具名 / 耗时等可检索字段，这些靠 logging 更合适。

### W2 参考答案

`DEBUG < INFO < WARNING < ERROR`（再往上是 `CRITICAL`）。

### W3 参考答案

直接 `python main.py` 时该模块常为 `__main__`；被 `import app.tools` 时名字是包路径如 `app.tools`。所以业务库里用 `__name__` 才能按模块过滤。

---

### B1 思路 + 参考答案

**思路**

1. 配置权放入口；库模块只 `getLogger`。
2. `if root.handlers: return` 防重复。
3. Formatter 带 `asctime` / `levelname` / `name` / `message`。

**参考：`app/logging_config.py`**

```python
import logging


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:
        return

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

**演示**

```python
import logging
from app.logging_config import setup_logging

setup_logging()
setup_logging()  # 应被短路
logging.getLogger(__name__).info("hello")
```

期望：只有一行 INFO；没有双份。

---

### B2 思路 + 参考答案

```python
# app/tools.py
import logging

logger = logging.getLogger(__name__)


def search(query: str) -> list[str]:
    logger.info("tool_start tool=search query=%s", query[:40])
    hits = [f"doc:{query}:0"]
    logger.info("tool_ok tool=search hits=%s", len(hits))
    return hits
```

```python
# app/agent.py
import logging

logger = logging.getLogger(__name__)


def step(run_id: str, question: str) -> None:
    logger.info("agent_step run_id=%s question=%s", run_id, question[:40])
```

```python
# main.py
from app.agent import step
from app.logging_config import setup_logging
from app.tools import search


def main() -> None:
    setup_logging()
    step("demo001", "what is RAG")
    search("RAG")


if __name__ == "__main__":
    main()
```

期望日志名类似 `[app.agent]` 与 `[app.tools]` 可区分。

---

### B3 思路 + 参考答案

```python
import logging

from app.logging_config import setup_logging

logger = logging.getLogger(__name__)


def boom() -> None:
    return 1 / 0


def main() -> None:
    setup_logging()
    try:
        boom()
    except ZeroDivisionError:
        logger.exception("boom_failed op=%s", "divide")


if __name__ == "__main__":
    main()
```

期望：ERROR 行后跟 Traceback，含 `ZeroDivisionError`。

---

### B4 思路 + 参考答案

**思路**

标准库阶段用 `k=%s` 拼字段即可；不要把 Key 放进消息。观测字段允许列表：摘要、截断。

```python
import logging
import time
import uuid

from app.logging_config import setup_logging

logger = logging.getLogger(__name__)


def fake_tool_call() -> None:
    run_id = str(uuid.uuid4())[:8]
    tool = "search"
    t0 = time.perf_counter()
    # ... 假装干活
    time.sleep(0.01)
    ok = True
    latency_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "tool_ok run_id=%s tool=%s ok=%s latency_ms=%.1f",
        run_id,
        tool,
        ok,
        latency_ms,
    )
    # 错误示范（不要做）：
    # logger.info("key=%s", os.getenv("APP_API_KEY"))


if __name__ == "__main__":
    setup_logging()
    fake_tool_call()
```

---

### A1 思路 + 参考答案

```python
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(fmt)

    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    root.addHandler(console)
    root.addHandler(file_handler)
```

跑完后检查：

```bash
# PowerShell
Get-Content app.log -Tail 5
```

---

### A2 思路 + 参考答案

**演示脚本要点**

```python
import logging

root = logging.getLogger()
root.handlers.clear()  # 仅演示；正式代码用防重复 setup
root.setLevel(logging.INFO)
h = logging.StreamHandler()
h.setLevel(logging.INFO)
h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
root.addHandler(h)

log = logging.getLogger("demo")
log.debug("hidden")
log.info("visible")

root.setLevel(logging.DEBUG)
h.setLevel(logging.DEBUG)
log.debug("now-visible")
```

**`a2_notes.md` 参考作答**

```markdown
# A2 级别过滤

1. root+handler 都是 INFO 时：DEBUG 行不出现，INFO 出现。
2. 两边都降到 DEBUG 后：DEBUG 出现。

易错：只改 `root.setLevel(DEBUG)` 但 handler 仍是 INFO → DEBUG 依旧被挡。
结论：logger 与 handler 的 level 都要 ≤ 目标记录级别。
```

---

### C1 思路 + 参考答案

```python
# app/runner.py
from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def run_tool(
    name: str,
    fn: Callable[..., Any],
    *,
    run_id: str | None = None,
    **kwargs: Any,
) -> Any:
    """执行工具并打链路字段；失败记 exception 后原样抛出。"""
    rid = run_id or str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info("tool_start run_id=%s tool=%s", rid, name)
    try:
        result = fn(**kwargs)
    except Exception:
        logger.exception("tool_error run_id=%s tool=%s", rid, name)
        raise
    else:
        ms = (time.perf_counter() - start) * 1000
        logger.info(
            "tool_ok run_id=%s tool=%s ok=%s latency_ms=%.1f",
            rid,
            name,
            True,
            ms,
        )
        return result
```

```python
# main.py
from app.logging_config import setup_logging
from app.runner import run_tool


def search(query: str) -> list[str]:
    if not query.strip():
        raise ValueError("empty query")
    return [f"hit:{query}"]


def main() -> None:
    setup_logging()
    rid = "demo001"
    print(run_tool("search", search, run_id=rid, query="python logging"))
    try:
        run_tool("search", search, run_id=rid, query="   ")
    except ValueError:
        pass


if __name__ == "__main__":
    main()
```

期望：

1. 成功路径有 `tool_start` / `tool_ok` 与 `latency_ms`
2. 失败路径有 `tool_error` 与 traceback，进程可按你的 demo 继续结束

---

### 本章速查

| 主题 | 记住 |
|------|------|
| 配置 | 入口 `setup_logging`，防重复 handler |
| 获取 | 模块级 `getLogger(__name__)` |
| 异常 | `logger.exception` |
| 字段 | `run_id` / `tool` / `ok` / `latency_ms` |
| 安全 | 不打 API Key / 完整 prompt |
