# Logging

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：2～4 小时  
> 对应练习：[`exercises/03-engineering/04-logging.md`](../../exercises/03-engineering/04-logging.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：用标准库 `logging` 建立可分级、可定向、可检索的日志；为 Agent 排障与后续可观测性打底。
- **对比**：`print` 适合临时调试；项目请用 logger。
- **你的优势**：前端里的 `console.log` / `console.warn` / `console.error` 已经给了「分级输出」直觉；本章要把直觉升级成「可配置、可过滤、可收集」的工程日志。

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

#### 为什么 `print` 不够？

Agent 出问题时你想立刻知道：

```text
哪一次 run_id？
调用了哪个工具？参数？耗时？
LLM 是否 429？重试了几次？
哪一步抛错？异常栈在哪？
```

`print` 很难分级、很难关、很难收集。本地调试时它很爽；一旦项目变大，你会遇到：

| `print` 的痛点 | logging 怎么解 |
|----------------|----------------|
| 全是「噪音」，关不掉 | 按级别过滤（DEBUG/INFO/WARNING/ERROR） |
| 只能看终端 | 同时输出到控制台与文件 |
| 格式随手写，检索困难 | 统一 Formatter，字段可检索 |
| 库里 `print` 污染应用输出 | 库只打 logger，由入口统一配置 |

#### 和 Agent 有什么关系

一次 Agent 循环往往是：

```text
用户请求 → 选工具 → 调工具 → 调 LLM → 再工具 → … → 返回
```

任何一步失败，没有日志你只能猜。有日志，你至少能回答：

> 「这次 `run_id=a3f2` 在第 3 步 `tool=search` 超时了，重试了 2 次。」

#### 本章要练的三种能力

1. **分级**：DEBUG 开发用，生产默认 INFO/WARNING
2. **定向**：控制台给人看，文件/采集器给机器看
3. **字段化**：事件名 + 关键字段，方便检索与后续 Tracing

可以先记一句：

> 日志不是「把 print 换个名字」，而是给系统装上可开关、可过滤、可检索的黑匣子。

---

## 2. 必掌握：logger 层级与级别

这一节会刻意写细——后面 handler、结构化日志、Agent 链路字段，全建立在「谁在打日志、打到什么级别」上。

### 2.1 获取 logger

#### 为什么需要 `getLogger(__name__)`？

如果你到处写：

```python
logging.info("something")  # 打到根 logger
```

所有模块的日志混在一起，想只开 `app.tools` 的 DEBUG、关掉别处噪音，几乎做不到。

按模块拿 logger，名字会变成模块路径（如 `app.tools.search`），过滤与排障都轻松很多。

#### 怎么写

```python
import logging

logger = logging.getLogger(__name__)
```

习惯放在模块顶部，和 `logger = ...` 只写一次；函数里直接 `logger.info(...)`。

#### 跑一下

把下面保存为 `demo_name.py` 并运行（先别纠结格式，默认可能很简陋）：

```python
import logging

logging.basicConfig(level=logging.INFO)  # 仅演示；正式入口见 §3
logger = logging.getLogger(__name__)

logger.info("hello from this module")
print("logger.name =", logger.name)
```

你会看到 `logger.name` 是 `__main__`（直接跑脚本时）或包路径（被 import 时）。  
业务代码里 `__name__` 通常是 `app.tools.search` 这类路径。

#### 易错点

1. **库代码里不要 `basicConfig`**：配置权留给应用入口（`main.py` / ASGI lifespan）
2. 不要每个函数里再 `getLogger(...)` 一遍（可以，但没必要；模块级一次即可）
3. 名字写死字符串也可以，但 `__name__` 更不容易拼错、跟文件同步

#### 前端 / console 对照

| Python | 前端直觉 |
|--------|----------|
| `logging.getLogger(__name__)` | 按文件/模块建「有名字的 logger」 |
| `logging.info(...)`（无名字） | 有点像直接 `console.log`，全局一锅粥 |
| logger 名 `app.tools.search` | 类似带 namespace 的日志前缀：`[tools/search]` |

Node 生态里常见 `debug('app:tools')` 或 pino/winston 的 `child({ module: 'tools' })`——思路一致：**日志要能按来源过滤**。

---

### 2.2 级别（从低到高）

#### 为什么需要级别？

不是每条信息都同等重要：

- 开发时你想看「进了哪个分支、score 算出来多少」→ DEBUG
- 正常业务事件「工具开始/结束」→ INFO
- 可恢复异常「重试第 2 次」→ WARNING
- 失败但进程还活着 → ERROR
- 进程级灾难 → CRITICAL

没有级别，要么全开吵死，要么全关瞎眼。

#### 怎么写

级别从低到高：

```text
DEBUG < INFO < WARNING < ERROR < CRITICAL
```

```python
import logging

logger = logging.getLogger(__name__)

score = 0.87
name = "search"
i = 2

logger.debug("score=%s", score)           # 细节，开发排障
logger.info("tool_start name=%s", name)   # 正常关键路径
logger.warning("retry attempt=%s", i)     # 异常但可继续
logger.error("tool_failed name=%s", name) # 失败
# 在 except 块内：
# logger.exception("unexpected error")   # ERROR + 自动附带 traceback
```

口诀：

| 级别 | 什么时候用 | Agent 例子 |
|------|------------|------------|
| DEBUG | 开发细节 | prompt 片段长度、候选工具列表 |
| INFO | 正常业务事件 | `tool_start` / `tool_ok` / `llm_call` |
| WARNING | 可恢复异常 | 429 后重试、降级到备用模型 |
| ERROR | 本次操作失败 | 工具抛错、解析 JSON 失败 |
| CRITICAL | 进程难以继续 | 配置缺失导致无法启动（少用） |

#### 跑一下

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("demo.levels")

logger.debug("you should NOT see this at INFO")
logger.info("visible info")
logger.warning("visible warning")
logger.error("visible error")
```

预期：看不到 DEBUG；后三条都能看到。  
把 `level=logging.INFO` 改成 `logging.DEBUG` 再跑，DEBUG 会出现——这就是「过滤」的体感。

#### 易错点

1. **生产默认别开 DEBUG**：Agent 项目 DEBUG 很容易把 prompt / 检索片段打爆磁盘
2. `logger.error("...", exc_info=True)` 可以带栈；但在 `except` 里更推荐 `logger.exception(...)`（见下节）
3. 级别是「阈值」：业务模块 logger 设 DEBUG、handler 设 INFO 时，DEBUG 仍会被 handler 挡掉（§3 会展开）

#### 前端 / console 对照

```javascript
console.debug("score=", score);   // 类似 DEBUG（浏览器可过滤）
console.log("tool_start", name);  // 接近 INFO（习惯上当普通日志）
console.warn("retry", i);         // WARNING
console.error("tool_failed", name); // ERROR
```

差别在于：浏览器 DevTools 可以按级别过滤，但**默认不会**帮你写文件、轮转、统一格式。Python `logging` 把这些做成了标准库能力。

---

### 2.3 `exception`：失败路径带栈

#### 为什么需要 `logger.exception`？

只打 `logger.error("failed: %s", e)`，往往只剩一句异常消息，**没有调用栈**。Agent 排障最需要的是「在哪一层炸的」。

#### 怎么写

```python
import logging

logger = logging.getLogger(__name__)


def risky_parse(raw: str) -> dict:
    import json
    try:
        return json.loads(raw)
    except Exception:
        logger.exception("parse_failed raw_len=%s", len(raw))
        raise
```

`logger.exception(...)` **必须在 except 块内使用**（或确保当前有异常上下文）；它等价于 ERROR 级别并自动带上 traceback。

#### 跑一下

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo.exc")

try:
    1 / 0
except ZeroDivisionError:
    logger.exception("boom")
```

输出里应能看到 `Traceback (most recent call last):` 和 `ZeroDivisionError`。

#### 易错点

1. 在没有异常的普通路径调用 `exception`，栈信息可能是「空的/莫名其妙的」——失败路径用 `exception`，普通失败描述用 `error`
2. 不要把完整用户输入 / API Key 拼进异常日志；最多打长度、类型、脱敏摘要
3. 捕获后若还要向上抛，先 `exception` 再 `raise`（保留现场）

---

### 2.4 logger 树与传播（propagate）

#### 为什么要懂「层级」？

`logging` 的 logger 按名字形成树：

```text
root
 └── app
      ├── app.agent
      └── app.tools
           └── app.tools.search
```

子 logger 默认会把记录**传播（propagate）**给父 logger。所以常见做法是：

> 业务模块只负责 `getLogger(__name__).info(...)`；在入口统一配置 root（或 `app`）的 handler。

这样你不用在每个文件里加 Handler。

#### 怎么写（心智模型）

```python
import logging

# 模块 A
log_tools = logging.getLogger("app.tools")
# 模块 B
log_search = logging.getLogger("app.tools.search")

# 名字是层级关系：search 是 tools 的子 logger
assert log_search.parent == log_tools  # 概念上成立（具体 parent 指向父节点）
```

实际项目里你很少手动碰 `parent`；记住两件事即可：

1. `__name__` → 自然形成树
2. 入口配置一次，子模块坐享其成

#### 跑一下（看名字）

```python
import logging

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

logging.getLogger("app.agent").info("step=1")
logging.getLogger("app.tools.search").info("query=hello")
```

输出里的 `[name]` 不同——练习 B2 就是在练这个体感。

#### 易错点

1. 在子 logger **和** root 都加了会打印的 Handler，又保持 `propagate=True` → **一条日志打两遍**
2. 有人图省事 `logger.propagate = False` 又忘记给这个 logger 加 Handler → **日志消失**
3. 库代码里 `getLogger("root")` 或乱改 root level，会坑到整个应用

#### 前端 / console 对照

可以把它想成「带命名空间的日志通道」：

```text
app.tools.search  ≈  debug('app:tools:search')
```

父级开了、子级消息能冒泡——和前端日志 namespace 过滤是同一类问题。

---

## 3. 必掌握：handler 与 formatter

### 3.1 一次基础配置

#### 为什么要在入口统一 `setup_logging`？

如果每个模块自己 `basicConfig` / `addHandler`：

- 导入顺序不同，结果不同
- 重复添加 Handler → 双份日志
- 测试与 CLI 入口行为不一致

正确姿势：**应用入口调用一次** `setup_logging()`，其余模块只 `getLogger(__name__)`。

#### 怎么写

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
import logging
from app.logging_config import setup_logging  # 路径按你的项目结构调整

setup_logging()
logger = logging.getLogger(__name__)
logger.info("app started")
```

#### 跑一下

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


setup_logging()
setup_logging()  # 第二次应被短路
logger = logging.getLogger("app.demo")
logger.info("hello")
logger.debug("hidden at INFO")
```

预期：只有一行格式化 INFO；没有双份；没有 DEBUG。

#### 易错点

1. **忘记防重复**：测试里多次 import / 多次调用 setup → 双份日志（练习 B1 的验收点）
2. 只设了 `root.setLevel(DEBUG)`，handler 仍是 WARNING → DEBUG 还是出不来（两边都要够低）
3. 在库模块调用 `logging.basicConfig()`：它「仅在 root 无 handler 时生效」，行为容易和入口打架——项目里优先自己写 `setup_logging`

#### 前端 / console 对照

| Python | 前端 / Node 直觉 |
|--------|------------------|
| `setup_logging()` 在入口 | 应用启动时配置一次 winston/pino |
| `StreamHandler` | 输出到 stdout（像终端里的 console） |
| `Formatter` | 统一前缀：时间、级别、模块名 |
| 模块内只 `getLogger` | 业务文件里不要重新 `createLogger` 一遍全局配置 |

---

### 3.2 handler 是什么

#### 为什么需要 handler？

logger 负责「产生日志记录」；**handler 负责「送到哪里」**。  
同一条 `logger.info(...)` 可以同时：

- 打到控制台（给人看）
- 写到文件（给排障 / 采集器用）

#### 怎么写

| Handler | 作用 |
|---------|------|
| `StreamHandler` | 输出到控制台（默认 `sys.stderr`） |
| `FileHandler` | 写到指定文件 |
| `RotatingFileHandler` | 按大小轮转，避免单文件无限长大 |
| `TimedRotatingFileHandler` | 按时间轮转（了解即可） |

同一个 logger（通常是 root）可以挂多个 handler：

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

#### 跑一下

跑完上面的 `setup_logging()` 后：

```python
logger = logging.getLogger("app.tools")
logger.info("tool_start tool=%s", "search")
```

你应同时在终端和 `app.log` 里看到同一条（练习 A1）。

#### 易错点

1. 文件路径写相对路径时，取决于**进程 cwd**——容器 / systemd 下容易写到意外目录；项目里常用相对项目根或显式配置
2. Windows 下注意 `encoding="utf-8"`，避免中文乱码
3. 多进程写同一文件可能交错；入门阶段先单进程，生产再用集中采集

#### 前端 / console 对照

- 只有 `console.log` ≈ 只有 `StreamHandler`
- 「既要看控制台，又要落盘」≈ 控制台 handler + 文件 handler  
Node 里 winston 的 `transports: [Console, File]` 就是同一模型。

---

### 3.3 formatter：把记录变成字符串

#### 为什么需要 formatter？

没有统一格式时，日志长这样：

```text
start
ERROR something
tool ok 12ms
```

有 Formatter 后：

```text
14:22:01 INFO [app.tools] tool_ok tool=search latency_ms=12.3
```

人读得快，机器也更好用正则 / 采集器切开字段。

#### 怎么写

常用占位符：

| 字段 | 含义 |
|------|------|
| `%(asctime)s` | 时间 |
| `%(levelname)s` | 级别名 |
| `%(name)s` | logger 名 |
| `%(message)s` | 消息正文 |
| `%(filename)s` / `%(lineno)d` | 源文件与行号（调试有用，生产慎用噪音） |

```python
logging.Formatter(
    fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
```

#### 跑一下

改 `fmt`，观察输出变化——亲手改一次比背表格记得牢。

#### 易错点

1. 默认 Formatter **不会**打印 `extra={...}` 里的自定义键（§4 展开）
2. 格式字符串写错键名会在输出时出问题；改完用真实 `logger.info` 验一次
3. 时间格式太长会占屏；本地开发 `%H:%M:%S` 通常够用

---

### 3.4 级别在两层上生效

#### 为什么容易「DEBUG 设了但看不见」？

一条日志要被输出，通常要同时通过：

```text
logger 的 level  ≤  记录级别
        ↓
handler 的 level ≤  记录级别
```

任一环太高，记录都会被丢掉。

#### 怎么写 / 跑一下

```python
import logging

root = logging.getLogger()
root.handlers.clear()  # 演示用；正式代码用 §3.1 的防重复逻辑
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)  # handler 比 logger 更严
handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
root.addHandler(handler)

log = logging.getLogger("demo.filter")
log.setLevel(logging.DEBUG)

log.debug("blocked by handler")  # 看不到
log.info("ok")                   # 看得到
```

#### 易错点

- 调级别时只改了一处  
- 子 logger 单独 `setLevel(WARNING)`，把父级 DEBUG 策略「局部关掉」——有时是刻意的，有时是误伤

---

### 3.5 子 logger 传播（复习落地）

默认日志会向父 logger 传播（`propagate=True`）。一般：

> 业务模块只 `getLogger(__name__).info(...)`，在入口统一配置 root/app logger。

需要「这个库完全静音」时，再针对该 logger 调 level 或（谨慎地）关 propagate——入门阶段优先调 level，少动 propagate。

---

## 4. 必掌握：结构化日志直觉

### 4.1 从散文到字段

#### 为什么不能写散文式日志？

不要只写：

```python
logger.info(f"出错了 {e} 工具可能是 search 吧")
```

问题：

- 检索困难（「工具可能是」这种自然语言搜不到稳定字段）
- 格式不统一（有时中文有时英文）
- 后续做指标 / 告警时，解析成本极高

#### 怎么写（字段化）

更好：

```python
logger.error(
    "tool_failed tool=%s retryable=%s error=%s",
    tool_name,
    retryable,
    exc,
)
```

约定：

1. **事件名在前**：`tool_failed` / `llm_call` / `agent_step`
2. **关键字段用 `k=%s`**：稳定、可 grep
3. **用 `%s` 延迟格式化**：别先用 f-string 拼好再传入（见下节）

#### 跑一下

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("demo.struct")

tool_name = "search"
retryable = True
exc = "timeout"

logger.error(
    "tool_failed tool=%s retryable=%s error=%s",
    tool_name,
    retryable,
    exc,
)
# tool_failed tool=search retryable=True error=timeout
```

#### 易错点

1. 事件名今天 `tool failed`、明天 `ToolFailed`、后天中文——检索直接废；**统一 snake_case 事件名**
2. 把整段 prompt 塞进 INFO——磁盘与合规双炸；大对象只打长度 / hash / 截断预览
3. 布尔、耗时、id 类型不稳定（有时 str 有时 int）会让后续解析痛苦——尽量类型稳定

---

### 4.2 为什么优先 `%s` 而不是 f-string？

#### 为什么？

```python
logger.debug(f"payload={huge_dict}")  # 即使 DEBUG 被过滤，f-string 也可能已经拼完了
logger.debug("payload=%s", huge_dict)  # 被过滤时通常不执行格式化
```

延迟格式化：级别不够时，少做无用功；也是 logging 的惯用风格。

#### 怎么写 / 跑一下

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("demo.fmt")

user = "alice"
logger.info("user_login user=%s", user)  # 推荐
# logger.info(f"user_login user={user}")  # 能跑，但不推荐当习惯
```

#### 易错点

- 混用：`"user=%s" % user` 先算好再传给 logger——同样失去延迟格式化
- 需要很多字段时，宁可多几个 `%s`，也不要拼成一篇短文

#### 前端 / console 对照

```javascript
console.log("user_login user=%s", user); // 某些环境支持类 printf
console.log("user_login", { user });     // 更常见：对象字段化
```

前端更常传对象；Python 标准库 logging 更常「事件名 + `%s` 字段」。后面 JSON 日志库会更接近前端对象风格。

---

### 4.3 `extra`：字段化的下一步

#### 为什么还要 `extra`？

字符串里写 `k=%s` 对人友好；对采集器来说，**真正的字段**更香：

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

#### 怎么写（先建立直觉）

注意：默认 `Formatter` **不会**自动打印 `extra` 里的自定义字段。要看到它们，需要：

- 自定义 Formatter（把 `run_id` 等写进 fmt），或
- 使用结构化 / JSON 日志库（如 `python-json-logger`、loguru 的序列化方案等——本章不绑死某一库）

本章先养成 **「事件名 + 关键字段」** 的写法；标准库阶段用 `k=%s` 完全合格。

#### 跑一下（证明默认 Formatter 不打印 extra）

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo.extra")

logger.info("llm_call", extra={"run_id": "a1b2", "latency_ms": 12})
# 通常只看到：INFO llm_call
# 看不到 run_id——这是正常的，不是你写错了
```

若要用标准库把字段打出来，最小自定义示例：

```python
import logging


class ExtraFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        run_id = getattr(record, "run_id", "-")
        latency_ms = getattr(record, "latency_ms", "-")
        return f"{base} run_id={run_id} latency_ms={latency_ms}"


root = logging.getLogger()
root.handlers.clear()
handler = logging.StreamHandler()
handler.setFormatter(ExtraFormatter("%(levelname)s %(message)s"))
root.addHandler(handler)
root.setLevel(logging.INFO)

logging.getLogger("demo.extra2").info(
    "llm_call",
    extra={"run_id": "a1b2", "latency_ms": 12},
)
```

#### 易错点

1. **不要把 API Key / Cookie / 用户隐私放进 `extra`**
2. `extra` 的键不要和 LogRecord 内置属性冲突（如 `name`、`message`、`levelname`）——冲突可能抛错或覆盖
3. 本章目标是直觉与纪律；上生产 JSON 日志时再系统选型即可

#### 前端 / console 对照

```javascript
console.log("llm_call", { run_id, model, latency_ms, tokens });
// Chrome 里对象可展开——这就是「结构化」的体感
```

Python 标准库默认更偏文本行；要对象/JSON，靠 Formatter 或专用库。

---

## 5. 建议掌握：请求 / Agent 链路字段

### 5.1 一次 run 贯穿哪些字段？

#### 为什么需要「链路字段」？

没有 `run_id` 时，日志是一锅粥：

```text
tool_start tool=search
tool_ok tool=search
tool_start tool=calc
ERROR parse failed
```

有 `run_id` 后，你可以过滤「只看这一次用户请求」：

```text
agent_step run_id=a3f2 step=1 tool=search ok=True latency_ms=120.5
agent_step run_id=a3f2 step=2 tool=calc ok=False latency_ms=3.2
```

后面做 Observability（Tracing）时，这些字段会自然映射到 span attributes。

#### 怎么写（建议字段表）

一次 Agent 运行建议贯穿：

| 字段 | 含义 | 备注 |
|------|------|------|
| `run_id` | 一次用户请求/任务 | 短 uuid 即可 |
| `step` | 当前第几步 | Agent 循环计数 |
| `tool` | 工具名 | 无工具时可省略或 `tool=-` |
| `model` | 模型名 | LLM 调用时打 |
| `latency_ms` | 耗时 | 统一毫秒，便于对比 |
| `ok` | 是否成功 | `True`/`False`，别用「成功/失败」散文 |

可选增强（了解即可）：`user_id`（脱敏）、`request_id`（网关）、`tokens`、`retry`、`error_type`。

#### 怎么写 / 跑一下

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("demo.agent")

run_id = "a3f2c9b1"
step = 1
tool = "search"
ok = True
latency_ms = 120.5

logger.info(
    "agent_step run_id=%s step=%s tool=%s ok=%s latency_ms=%s",
    run_id, step, tool, ok, latency_ms,
)
```

#### 易错点

1. 每一步重新 `uuid4()` 当 `run_id`——链路断了；**一次用户请求共用一个 run_id**
2. 成功打 INFO、失败只 `print`——风格分裂，检索不全
3. 字段名漂变：`latency` / `latencyMs` / `cost_ms` 混用——选一个坚持住（本章推荐 `latency_ms`）

#### 前端 / console 对照

前端排查一次页面请求，常会带 `requestId` / `traceId`：

```javascript
console.info("agent_step", { run_id, step, tool, ok, latency_ms });
```

和后端链路字段是同一思想：先能「串起来」，再谈平台。

---

### 5.2 和 Tracing 的地图关系

现在先建立映射直觉即可（细节留给可观测性专题）：

| 日志字段 | Tracing 侧常见对应 |
|----------|-------------------|
| `run_id` | trace / 业务 correlation id |
| `step` + `tool` | span name / attributes |
| `latency_ms` | span duration |
| `ok` / `error_type` | span status |

你不需要现在上 OpenTelemetry；但字段从一开始就打对，以后迁移成本极低。

---

## 6. 了解即可：对接可观测性平台

日志写对之后，常见链路是：

```text
日志 → 文件/stdout → 采集器 → Loki/ELK/云日志
链路追踪 → OpenTelemetry / 厂商 Tracing
指标 → Prometheus 等
```

现在只需知道：

1. **先把日志写对**（级别、事件名、链路字段、不泄密）
2. 容器环境优先打 stdout，由平台采集——不一定先上复杂文件轮转
3. 平台对接是工程下一阶段；本章不要求会配 Grafana

地图级就够，防止一上来被全家桶淹没。

---

## 7. 常见坑

集中再记一版（前面各节易错点的总复盘）：

1. 在库模块里 `basicConfig` 乱配，导致应用入口难控
2. 每个文件重新加 Handler，日志重复打印
3. 日志泄漏 API Key / 用户隐私 / 完整 prompt
4. 全部 DEBUG 打爆磁盘；生产默认 INFO/WARNING
5. 用 `print` 与 logger 混用，风格分裂
6. 只改 logger level 或只改 handler level，DEBUG「设了却看不见」
7. `extra` 字段以为会自动出现在默认 Formatter 里
8. 失败路径用 `error(str(e))` 却不用 `exception`，丢掉 traceback

---

## 8. 综合小例子

把本章必掌握点串起来：入口配置 + 模块 logger + 成功/失败路径 + 链路字段。

#### 为什么要有 `run_tool` 这种包装？

Agent 里「调工具」会发生很多次。若每次手写起止日志，字段容易丢、成功失败不一致。抽一个薄包装，保证：

- 开始有 `tool_start`
- 成功有 `tool_ok` + `latency_ms`
- 失败有 `tool_error` + traceback，并继续抛出

#### 怎么写

```python
# app/logging_config.py
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

```python
# app/tools/runner.py
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
# app/main.py（演示入口）
from app.logging_config import setup_logging
from app.tools.runner import run_tool


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
        pass  # 演示失败路径日志；真实 Agent 会按策略处理


if __name__ == "__main__":
    main()
```

#### 跑一下（最小可粘贴版）

若你暂时不想搭包结构，用单文件也能感受：

```python
import logging
import time
import uuid


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(handler)


logger = logging.getLogger("app.tools.runner")


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


setup_logging()


def ok_fn(x: int) -> int:
    return x + 1


def bad_fn() -> None:
    raise RuntimeError("boom")


print(run_tool("add", ok_fn, x=1))
try:
    run_tool("boom", bad_fn)
except RuntimeError:
    pass
```

成功路径应看到 `tool_start` → `tool_ok`；失败路径应看到 `tool_error` 与 traceback。

#### 易错点

1. 包装器里吞掉异常只打日志、不 `raise`——调用方以为成功了
2. `run_id` 在包装器内每次新建，却还想串多步 Agent——应允许外部传入同一 `run_id`
3. 在 `run_tool` 里再 `setup_logging()`——配置职责又散了

#### 前端 / console 对照

类似前端给 API 客户端包一层：

```javascript
async function runTool(name, fn, args, runId) {
  console.info("tool_start", { run_id: runId, tool: name });
  const t0 = performance.now();
  try {
    const result = await fn(args);
    console.info("tool_ok", {
      run_id: runId,
      tool: name,
      latency_ms: performance.now() - t0,
    });
    return result;
  } catch (e) {
    console.error("tool_error", { run_id: runId, tool: name, error: e });
    throw e;
  }
}
```

思想相同：统一埋点，业务函数保持干净。

---

## 9. 练习指引

按文档动手：[`exercises/03-engineering/04-logging.md`](../../exercises/03-engineering/04-logging.md)

建议顺序：

1. **B1** `setup_logging` + 防重复 Handler  
2. **B2** 两模块 `getLogger(__name__)` 看 `[name]`  
3. **B3** `logger.exception` 看 traceback  
4. **B4** 字段化一行：`run_id` / `tool` / `ok` / `latency_ms`  
5. （建议）**A1** 文件 handler；**A2** 级别过滤体感  
6. （可选）**C1** 实现本节 `run_tool`

目录：`playground/03-engineering/04-logging/`

---

## 10. 小结与下一站

### 自检

- [ ] 能在入口配置 logging，在模块里 `getLogger(__name__)`
- [ ] 知道级别与 handler/formatter 职责（含「两层 level」）
- [ ] 能按「事件 + 字段」写 Agent 关键日志
- [ ] 失败路径会用 `exception`；知道别把密钥打进日志
- [ ] （建议）能为一次 run 贯穿 `run_id` / `step` / `tool` / `latency_ms` / `ok`

### 一张图记住职责

```text
logger   ：谁在说话、级别够不够
handler  ：送到哪（控制台 / 文件）
formatter：长什么样（时间、级别、模块、消息）
字段     ：事件名 + run_id/tool/latency…（可检索）
```

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
