# 模块、包与导入系统

> 所属模块：`01-python-basics` · Python 语言基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/01-python-basics/03-modules-packages.md`](../../exercises/01-python-basics/03-modules-packages.md)

## 本章定位

- **模块目标**：能用 Python 写正常程序，而不是只会零散脚本。
- **本章角色**：学会把函数和数据拆进多个文件，并用 `import` 正确组装。这是从「单个 `.py`」迈向「真正项目」的关键一步。
- **你的优势**：前端里的 `import` / `export`、目录即模块的经验可直接类比；差异在于 Python 的包路径、`__init__.py`、以及「怎么启动」会强烈影响导入是否成功。

## 学习目标（学完应能做到）

1. 说清「模块 / 包 / 导入」分别是什么，并写出常见 `import` 写法。
2. 搭出一个最小可用的包目录，知道 `__init__.py` 的作用。
3. 分清绝对导入与相对导入，能排查常见 `ImportError` / `ModuleNotFoundError`。
4. 会用 `if __name__ == "__main__":` 区分「库代码」和「脚本入口」。
5. 完成课后练习，分清必掌握 / 建议掌握 / 了解即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | import 机制、包结构、`__init__.py`、绝对/相对导入 | 能搭、能导、能排错 |
| **建议掌握** | `__name__ == "__main__"`、常用标准库巡礼 | 会写入口、会查文档用库 |
| **了解即可** | `sys.path`、命名空间包 | 建立地图，工程化章再加深 |

---

## 1. 为什么要学（和 Agent 有什么关系）

真实 Agent 项目几乎不会是一个 `main.py` 塞全部逻辑，而更像：

```text
my_agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agents/
│   ├── tools/
│   ├── services/
│   └── models/
├── tests/
└── pyproject.toml
```

你会不断做这些事：

```text
from app.tools.search import search
from app.agents.react import run_agent
```

若导入体系不熟，后面会出现：

- 明明文件在，却 `ModuleNotFoundError`
- 相对导入在脚本直接运行时炸掉
- 循环导入把项目卡死
- 测试文件找不到包

本章目标：**先把「文件怎么变成可导入的能力」搞清楚**。更完整的项目布局会在「工程化」模块继续。

---

## 2. 必掌握：模块是什么，import 怎么工作

### 2.1 一个 `.py` 文件就是一个模块

例如文件 `greet.py`：

```python
# greet.py
DEFAULT_NAME = "world"


def hello(name: str = DEFAULT_NAME) -> str:
    return f"hello, {name}"
```

在同目录另一个文件里：

```python
import greet

print(greet.hello("Alice"))
print(greet.DEFAULT_NAME)
```

要点：

- `import greet` 会执行 `greet.py` 顶层代码一次
- 通过 `greet.xxx` 访问其中的函数/变量
- 模块名默认来自文件名（不含 `.py`）

### 2.2 常见导入写法

```python
import json                          # 导入整个模块
import json as js                    # 起别名
from pathlib import Path             # 从模块取某个名字
from pathlib import Path, PurePath   # 取多个
from datetime import datetime as dt  # 取出来再起别名
```

和 JS 的粗对照：

| JavaScript | Python |
|------------|--------|
| `import fs from "fs"` | `import fs`（更像命名空间导入） |
| `import { readFile } from "fs"` | `from fs import readFile`（概念近似） |
| `export function ...` | 模块顶层定义的名字默认可被导入 |

注意：Python **没有** JS 那种必须 `export` 才对外可见的语法；约定用 `_private` 下划线表示「内部实现，请别随便依赖」。

### 2.3 `from module import *` 不推荐

```python
from greet import *  # 不推荐：污染命名空间，可读性差
```

练习和工程代码里优先写明确导入。

### 2.4 导入会发生什么（心智模型）

```text
import app.tools.search
        ↓
1. 在模块搜索路径里找 app
2. 再找 app/tools
3. 加载 search.py（执行顶层代码）
4. 把结果缓存到 sys.modules
5. 之后再次 import 同一模块：直接复用缓存
```

所以：

- 模块顶层副作用（联网、读大文件、打印一堆东西）要谨慎
- 「改完代码但行为没变」有时是进程没重启，旧模块还在缓存里（开发时重跑脚本即可）

---

## 3. 必掌握：包结构

### 3.1 包 = 带组织结构的模块集合

最小包：

```text
echo_kit/
├── __init__.py
├── core.py
└── utils.py
```

- `echo_kit` 是**包名**（目录名）
- `echo_kit.core` 是包内模块
- 包用来分组相关能力，避免所有文件平铺在根目录

### 3.2 Agent 风格的小例子

```text
mini_agent/
├── __init__.py
├── messages.py
└── tools/
    ├── __init__.py
    ├── search.py
    └── calc.py
```

```python
# mini_agent/messages.py
def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}
```

```python
# mini_agent/tools/search.py
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"result:{query}:{i}" for i in range(top_k)]
```

使用：

```python
from mini_agent.messages import create_message
from mini_agent.tools.search import search

print(create_message("user", "你好"))
print(search("RAG", top_k=2))
```

### 3.3 目录边界怎么切（先够用）

| 目录直觉 | 放什么 |
|----------|--------|
| `tools/` | 可被 Agent 调用的工具函数 |
| `agents/` | 循环/策略/编排 |
| `services/` | 调 LLM、数据库等外部依赖 |
| `models/` | 数据结构 / schema |

现在不必一次做完美架构；先做到「按职责分文件 + 能稳定导入」。

---

## 4. 必掌握：`__init__.py`

### 4.1 它是干什么的？

传统上：目录里有 `__init__.py`，Python 才把该目录当作包。

它还可以：

1. 标记「这是一个包」
2. 在包被导入时执行初始化逻辑（尽量少做重活）
3. 向外暴露更短的公共 API

```python
# mini_agent/tools/__init__.py
from mini_agent.tools.search import search
from mini_agent.tools.calc import calc

__all__ = ["search", "calc"]
```

于是外部可以：

```python
from mini_agent.tools import search, calc
```

而不必每次写到具体文件。

### 4.2 `__all__` 是什么？

`__all__` 声明「`from package import *` 时导出哪些名字」。  
即使你不用 `import *`，它也常被当作**公共 API 清单**。

### 4.3 空的 `__init__.py` 可以吗？

可以，而且很常见：

```python
# 空文件也行
```

先保证包可导入，再决定要不要在 `__init__.py` 里做再导出。

> 现代 Python 也支持无 `__init__.py` 的命名空间包（PEP 420）。本章先按「有 `__init__.py`」的常规包来学，够用且最不容易踩坑。

---

## 5. 必掌握：绝对导入 vs 相对导入

### 5.1 绝对导入（推荐作为默认）

从包名完整写起：

```python
from mini_agent.messages import create_message
from mini_agent.tools.search import search
```

优点：路径清晰，适合大多数应用代码。

### 5.2 相对导入（包内部常用）

```python
# 在 mini_agent/tools/search.py 内部
from ..messages import create_message   # 上一级包中的 messages
from .calc import calc                  # 同级 calc
```

含义：

- `.` = 当前包
- `..` = 上一级包

### 5.3 最常见坑：把包内文件当脚本直接跑

假如你在 `mini_agent/tools/` 里执行：

```bash
python search.py
```

然后 `search.py` 里写了 `from ..messages import ...`，往往会报：

```text
ImportError: attempted relative import with no known parent package
```

原因：直接跑文件时，Python 不认为它处于包层级中。

**更稳妥的启动方式**（后文 `__main__` 也会强化）：

```bash
# 在项目根目录（包含 mini_agent 目录的那一层）
python -m mini_agent.tools.search
```

或提供一个包外的入口脚本，只使用绝对导入。

### 5.4 选择建议

| 场景 | 建议 |
|------|------|
| 应用代码、跨多层目录 | 优先绝对导入 |
| 包内部短距离引用 | 相对导入可以，保持克制 |
| 既当库又当脚本的文件 | 小心相对导入，准备 `python -m` 入口 |

---

## 6. 建议掌握：`if __name__ == "__main__":`

### 6.1 `__name__` 是什么？

- 模块被导入时：`__name__` 是模块名，如 `"mini_agent.messages"`
- 模块被直接运行时：`__name__` 是 `"__main__"`

所以这个套路：

```python
# mini_agent/messages.py
def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}


if __name__ == "__main__":
    print(create_message("user", "demo"))
```

效果：

- 别人 `import` 时，不会自动执行 demo
- 你直接运行该文件时，可以做快速手工测试

### 6.2 为什么 Agent 项目特别需要它？

工具文件里常会写几行本地试跑：

```python
def search(query: str) -> list[str]:
    ...


if __name__ == "__main__":
    print(search("langgraph memory"))
```

这样 `tools/search.py` 既是可导入模块，也是可临时调试的脚本。

---

## 7. 建议掌握：常用标准库巡礼

先混脸熟，用到再查文档。不必背。

| 模块 | 干什么 | Agent 里常见用法 |
|------|--------|------------------|
| `json` | JSON 序列化 | 消息、工具参数、评测集 |
| `pathlib` | 路径 | 读提示词模板、存会话 |
| `os` / `os.environ` | 环境变量 | API Key（后面工程化再规范） |
| `re` | 正则 | 简单解析、清洗文本 |
| `datetime` | 时间 | 日志时间戳、过期判断 |
| `logging` | 日志 | 比 print 更适合项目（后有专章） |
| `typing` | 类型注解 | Protocol / Generic 等（后有专章） |
| `asyncio` | 异步 | LLM/HTTP 并发（后有专章） |
| `http.client` / 第三方 `httpx` | HTTP | 调 API（实战中更常用 httpx/requests） |
| `unittest` / 第三方 `pytest` | 测试 | 后有专章 |

最小体验：

```python
import json
from datetime import datetime, timezone
from pathlib import Path

payload = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "messages": [{"role": "user", "content": "hi"}],
}
Path("out.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
```

---

## 8. 了解即可：`sys.path` 与命名空间包

### 8.1 `sys.path`

Python 找模块时会搜索一组路径（简化理解）：

```text
脚本目录 / 当前相关路径 / PYTHONPATH
→ 标准库相关路径
→ site-packages（含虚拟环境）
……
```

先匹配先生效：同名时靠前的路径会「盖住」靠后的。排查「装了包却导入了错误模块」时，先看 `sys.path` 顺序。

你可以用下面两行「看到」它（了解即可，不要在业务代码里乱改）：

```python
import sys
print(sys.path)
```

临时把路径塞进 `sys.path` 能“修好”导入，但那是急救，不是长期方案。  
长期方案是：正确的包布局 + 可安装项目（`pyproject.toml` / `uv`），工程化章会讲。

### 8.2 命名空间包

无 `__init__.py` 也可能组成包（命名空间包），用于大型库拆分发布。  
应用项目里继续用常规包（有 `__init__.py`）最省心。

---

## 9. 常见坑（建议收藏）

1. **文件/目录名别和标准库撞车**  
   自己建了 `json.py`，再 `import json` 可能导到自己，怪问题一堆。

2. **循环导入**  
   `a.py` 导入 `b.py`，`b.py` 又导入 `a.py`。  
   缓解：把共享结构抽到 `types.py` / `models.py`；或把导入移进函数内部（应急）；或重新划分边界。

3. **在错误的工作目录启动**  
   包找不到，常常是你在 nested 目录里运行，根路径不对。先确认「当前目录是谁」。

4. **混用绝对/相对导致风格混乱**  
   一个项目定一种主风格，团队协作更稳。

5. **在 `__init__.py` 里做重活**  
   一 `import package` 就联网/读超大文件，会让启动变慢且难测。

6. **`from x import y` 后改了 `x.y` 的绑定，你手里的 `y` 不一定变**  
   新手阶段记住：更偏向 `import module` 再 `module.func`，调试时心智更简单。

---

## 10. 综合小例子：搭一个可导入的 mini_agent

假设当前工作目录是 `playground/01-python-basics/03-modules-packages/`：

```text
03-modules-packages/
├── mini_agent/
│   ├── __init__.py
│   ├── messages.py
│   ├── runtime.py
│   └── tools/
│       ├── __init__.py
│       ├── search.py
│       └── calc.py
└── run_demo.py
```

```python
# mini_agent/__init__.py
"""A tiny agent-shaped package for learning imports."""

__version__ = "0.1.0"
```

```python
# mini_agent/tools/__init__.py
from .search import search
from .calc import calc

__all__ = ["search", "calc"]
```

```python
# mini_agent/runtime.py
from mini_agent.messages import create_message
from mini_agent.tools import search, calc


def run_once(query: str) -> list[dict]:
    messages = [create_message("user", query)]
    docs = search(query, top_k=2)
    total = calc("1+2")
    messages.append(
        create_message("assistant", f"docs={docs}, calc={total}")
    )
    return messages
```

```python
# run_demo.py
from mini_agent.runtime import run_once

if __name__ == "__main__":
    for msg in run_once("what is RAG"):
        print(msg)
```

在该目录执行：

```bash
python run_demo.py
```

若成功打印消息列表，说明你已经走通：**包结构 + 绝对导入 + 入口脚本**。

---

## 11. 练习指引

请打开并完成：

[`exercises/01-python-basics/03-modules-packages.md`](../../exercises/01-python-basics/03-modules-packages.md)

建议代码位置：

```text
playground/01-python-basics/03-modules-packages/
```

本章练习以「搭目录 + 跑通导入」为主，比纯算法题更接近真实项目。

---

## 12. 小结与下一站

### 你现在应该掌握的心智模型

```text
文件 → 模块
目录(+__init__.py) → 包
import → 按搜索路径加载并缓存
入口脚本 / python -m → 决定「以什么身份运行」
```

### 自检清单

- [ ] 能手写一个含 `tools/` 子包的最小项目并成功导入
- [ ] 能解释绝对导入与相对导入的差异与常见报错
- [ ] 知道为何需要 `if __name__ == "__main__":`
- [ ] 独立完成练习基础题

### 模块 01 收尾

恭喜，Python 语言基础三章（语法 → 函数 → 模块）完成后，你已经可以写「分文件的小项目」了。

下一模块：[`../02-advanced-python/README.md`](../02-advanced-python/README.md)  
从面向对象与类型系统开始，为阅读 Agent Framework 源码打内功。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[函数与作用域](./02-functions-scope.md)
- 下一模块：[高级特性与类型系统](../02-advanced-python/README.md)
