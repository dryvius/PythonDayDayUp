# 模块、包与导入系统

> 所属模块：`01-python-basics` · Python 语言基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有前端 `import` 经验可更快）  
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
| --- | --- | --- |
| **必掌握** | import 机制、包结构、`__init__.py`、绝对/相对导入 | 能搭、能导、能排错 |
| **建议掌握** | `__name__ == "__main__"`、常用标准库巡礼 | 会写入口、会查文档用库 |
| **了解即可** | `sys.path`、命名空间包 | 建立地图，工程化章再加深 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要模块与包？

真实 Agent 项目几乎不会是一个 `main.py` 塞全部逻辑。没有拆文件时，你会很快遇到：

```text
main.py（2000 行）
  ├── 消息结构
  ├── 工具函数
  ├── Agent 循环
  ├── 调 LLM
  └── 一堆临时调试代码
```

改一处怕牵全身；测试也难下手。

有了模块/包，同一件事通常长这样：

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

```python
from app.tools.search import search
from app.agents.react import run_agent
```

#### 导入不熟时会出现什么？

| 症状 | 常见原因 |
| --- | --- |
| 明明文件在，却 `ModuleNotFoundError` | 工作目录 / 包名 / 启动方式不对 |
| 相对导入一跑就炸 | 用 `python xxx.py` 直接跑了包内文件 |
| 循环导入把项目卡死 | A↔B 互相顶层 import |
| 测试文件找不到包 | 没从正确根目录启动，或包未安装到环境 |

#### 本章目标

> 先把「文件怎么变成可导入的能力」搞清楚。

更完整的项目布局会在「工程化」模块继续。现在先练稳导入。

---

## 2. 必掌握：模块是什么，import 怎么工作

这一节会刻意写细一点——`import` 是后面所有「多文件项目」的底座。

### 2.1 一个 `.py` 文件就是一个模块

#### 为什么需要模块？

前两章你已经会写函数了。但所有函数都挤在一个文件里时：

```python
# 一切都在一个文件……
def create_message(...): ...
def search(...): ...
def calc(...): ...
def run_agent(...): ...
# 文件越来越长，越来越难找
```

于是可以把**一组相关能力**单独开一个文件，再用名字引用它——这个文件就是**模块**。

#### 怎么写

例如文件 `greet.py`：

```python
# greet.py
DEFAULT_NAME = "world"


def hello(name: str = DEFAULT_NAME) -> str:
    return f"hello, {name}"
```

在同目录另一个文件里：

```python
# demo.py（和 greet.py 同目录）
import greet

print(greet.hello("Alice"))
print(greet.DEFAULT_NAME)
```

#### 跑一下

在该目录执行：

```bash
python demo.py
```

输出：

```text
hello, Alice
world
```

可以先建立三个直觉：

1. `import greet` 会执行 `greet.py` 顶层代码一次
2. 通过 `greet.xxx` 访问其中的函数/变量
3. 模块名默认来自文件名（不含 `.py`）

心智图：

```text
greet.py  ──import──▶  名字 greet
                          ├── greet.hello
                          └── greet.DEFAULT_NAME
```

和「把函数写在同一个文件里」相比，模块就是：

> 给一组相关能力单独开一个文件，再用名字引用它。

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 文件叫 `greet.py`，却写 `import greet.py` | `SyntaxError` / 找不到模块 |
| 文件名含连字符：`my-greet.py` | 无法用普通 `import`（标识符不能有 `-`） |
| 和标准库撞名：自己建了 `json.py` | 可能导到自己，怪问题一堆 |

#### JS 对照

| JavaScript | Python |
| --- | --- |
| 一个文件 ≈ 一个模块 | 一个 `.py` ≈ 一个模块 |
| 需要 `export` 才对外可见 | 顶层名字默认可被导入 |
| `import * as greet from "./greet.js"` | `import greet`（命名空间式） |

注意一个关键差异：

> Python **没有** JS 那种必须 `export` 才对外可见的语法。

约定用 `_private` 下划线表示「内部实现，请别随便依赖」。这是约定，不是语法强制。

---

### 2.2 常见导入写法

#### 为什么需要多种写法？

有时你要整个模块当命名空间（`json.dumps`）；有时只想拿一个名字（`Path`）；有时名字太长要起别名。Python 给了几套常用写法。

#### 怎么写

```python
import json                          # 导入整个模块
import json as js                    # 起别名
from pathlib import Path             # 从模块取某个名字
from pathlib import Path, PurePath   # 取多个
from datetime import datetime as dt  # 取出来再起别名
```

#### 跑一下

```python
import json
from pathlib import Path
from datetime import datetime as dt

print(json.dumps({"ok": True}))
print(Path("a.txt").suffix)   # .txt
print(dt(2026, 1, 1).year)    # 2026
```

对照表（先建立肌肉记忆）：

| 写法 | 之后怎么用 | 适合 |
| --- | --- | --- |
| `import m` | `m.xxx` | 模块本身有命名空间价值（如 `json`） |
| `import m as alias` | `alias.xxx` | 名字长或习惯简称 |
| `from m import name` | 直接用 `name` | 明确只要少数几个符号 |
| `from m import name as alias` | 用 `alias` | 避免和本地名字冲突 |

#### 易错点

```python
# ❌ 以为导入了模块，其实只导入了名字
from pathlib import Path
print(pathlib.Path("x"))  # NameError: name 'pathlib' is not defined

# ✅ 二选一
import pathlib
print(pathlib.Path("x"))

from pathlib import Path
print(Path("x"))
```

另一个常见混用错误：

```python
# ❌
from json import dumps
print(json.dumps({}))  # NameError: json 未定义

# ✅
print(dumps({}))
# 或
import json
print(json.dumps({}))
```

#### JS 对照

| JavaScript | Python |
| --- | --- |
| `import fs from "fs"` | `import fs`（更像命名空间导入） |
| `import { readFile } from "fs"` | `from fs import readFile`（概念近似） |
| `import { readFile as rf } from "fs"` | `from fs import readFile as rf` |
| `export function ...` | 模块顶层定义的名字默认可被导入 |

---

### 2.3 `from module import *` 不推荐

#### 为什么会有人写它？

图省事：一次把模块里「公开名字」全倒进当前命名空间。

```python
from greet import *  # 不推荐：污染命名空间，可读性差
print(hello("Bob"))  # 能跑，但读者不知道 hello 从哪来
```

#### 跑一下（看「污染」）

```python
# greet.py 里有 hello、DEFAULT_NAME
from greet import *

def hello():  # 不小心覆盖了导入来的 hello
    return "local"


print(hello())  # local —— 原来的 greet.hello 被盖掉了
```

#### 易错点 / 建议

别人读你的代码时会问：这个 `hello` 到底从哪来的？  
练习和工程代码里优先写明确导入：

```python
from greet import hello, DEFAULT_NAME
# 或
import greet
```

> `import *` 像把一抽屉零件全倒桌上——能找到，但以后很难收拾。

---

### 2.4 导入会发生什么（心智模型）

#### 为什么要懂这个？

不懂导入过程，后面排错全靠猜：「文件明明在，为什么找不到？」「改完代码怎么没生效？」

#### 怎么理解（步骤图）

```text
import app.tools.search
        ↓
1. 在模块搜索路径里找 app
2. 再找 app/tools
3. 加载 search.py（执行顶层代码）
4. 把结果缓存到 sys.modules
5. 之后再次 import 同一模块：直接复用缓存
```

#### 跑一下：顶层代码会执行

```python
# side_effect.py
print("side_effect loaded")  # 顶层副作用
VALUE = 1
```

```python
# demo.py
import side_effect
import side_effect  # 第二次：不会再打印
print(side_effect.VALUE)
```

输出：

```text
side_effect loaded
1
```

只打印一次——因为第二次命中了缓存。

#### 易错点（两个实际后果）

1. **模块顶层副作用要谨慎**  
   联网、读大文件、打印一堆东西——一 `import` 就会跑。库代码顶层尽量只做定义。

2. **「改完代码但行为没变」**  
   有时是进程没重启，旧模块还在 `sys.modules` 缓存里。开发时重跑脚本即可；交互环境才需要 `importlib.reload`（了解即可）。

反例：

```python
# ❌ 不推荐：一导入就干活
# tools/search.py
print("connecting to db...")  # 任何人 import 都会触发
RESULTS = fetch_all()         # 启动变慢、难测、难复用
```

```python
# ✅ 推荐：顶层只定义，调用时再干活
def search(query: str) -> list[str]:
    ...
```

---

## 3. 必掌握：包结构

### 3.1 包 = 带组织结构的模块集合

#### 为什么需要包？

模块解决了「拆文件」。文件一多，又会出现：

```text
项目根目录/
├── messages.py
├── search.py
├── calc.py
├── runtime.py
├── utils1.py
└── helpers_final_v2.py   ← 平铺灾难
```

于是用**目录**把相关模块编成一组——这就是**包（package）**。

#### 怎么写（最小包）

```text
echo_kit/
├── __init__.py
├── core.py
└── utils.py
```

含义：

- `echo_kit` 是**包名**（目录名）
- `echo_kit.core` 是包内模块
- `__init__.py` 标记「这是一个包」（下一节细讲）

导入时：

```python
from echo_kit.core import do_something
```

#### 跑一下（对照「文件 vs 包」）

```text
单文件模块：  greet.py          → import greet
包内模块：    echo_kit/core.py  → import echo_kit.core
```

可以想成前端项目里的「按功能拆目录」，只是 Python 额外要求你更在意「包名是不是能被找到」。

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 目录名是 `Echo-Kit` | 导入名必须是合法标识符，别用连字符 |
| 包名和某标准库同名 | 容易导错（如自己建了 `email/`） |
| 以为「有目录就能 import」 | 还要：工作目录对、启动方式对、通常有 `__init__.py` |

#### JS 对照

| 概念 | JavaScript | Python |
| --- | --- | --- |
| 单文件 | `./utils.js` | `utils.py` |
| 目录模块 | `./utils/index.js` | `utils/` + `__init__.py` |
| 深层路径 | `import x from "./a/b/c.js"` | `from a.b.c import x` |

---

### 3.2 Agent 风格的小例子

#### 为什么按这个形状拆？

Agent 代码天然有几块：消息结构、工具、运行时。先用最小目录练手。

#### 怎么写

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

#### 怎么用 / 跑一下

在**包含 `mini_agent` 目录的那一层**（项目根）启动 Python，然后：

```python
from mini_agent.messages import create_message
from mini_agent.tools.search import search

print(create_message("user", "你好"))
print(search("RAG", top_k=2))
```

可能输出：

```text
{'role': 'user', 'content': '你好'}
['result:RAG:0', 'result:RAG:1']
```

当你第一次写出这两行并成功跑通时，你就已经跨过「脚本」进入「小项目」了。

#### 易错点

```bash
# 若你当前目录不对，常见报错：
ModuleNotFoundError: No module named 'mini_agent'
```

优先检查：

1. 当前工作目录是不是「能看见 `mini_agent/`」的那一层  
2. 目录名是不是正好叫 `mini_agent`（和导入名一致）  
3. 有没有 `__init__.py`

---

### 3.3 目录边界怎么切（先够用）

#### 为什么要先有边界直觉？

不必一次做完美架构，但要避免「所有函数扔进 `utils.py`」。

| 目录直觉 | 放什么 | 例子 |
| --- | --- | --- |
| `tools/` | 可被 Agent 调用的工具函数 | `search` / `calc` / `read_file` |
| `agents/` | 循环/策略/编排 | ReAct 循环、路由 |
| `services/` | 调 LLM、数据库等外部依赖 | `llm_client.py` |
| `models/` | 数据结构 / schema | Message、ToolCall |

现在先做到：

> 按职责分文件 + 能稳定导入。

后面工程化章再谈「可安装包 / 测试布局 / 配置分层」。

---

## 4. 必掌握：`__init__.py`

### 4.1 它是干什么的？

#### 为什么需要 `__init__.py`？

传统上：目录里有 `__init__.py`，Python 才把该目录当作**常规包**。  
没有它时，老版本 Python 可能不认这个目录是包；即便现代 Python 有「命名空间包」，新手项目里**显式放一个**最省心。

它还可以做三件事：

1. 标记「这是一个包」
2. 在包被导入时执行初始化逻辑（尽量少做重活）
3. 向外暴露更短的公共 API（再导出）

#### 怎么写（再导出公共 API）

```python
# mini_agent/tools/__init__.py
from mini_agent.tools.search import search
from mini_agent.tools.calc import calc

__all__ = ["search", "calc"]
```

或在包内用相对导入（等价思路）：

```python
# mini_agent/tools/__init__.py
from .search import search
from .calc import calc

__all__ = ["search", "calc"]
```

于是外部可以：

```python
from mini_agent.tools import search, calc
```

而不必每次写到具体文件。  
这很像「做一个更干净的对外出口」。

#### 跑一下（对照「有无再导出」）

```text
没有再导出时：
  from mini_agent.tools.search import search

有再导出后：
  from mini_agent.tools import search
```

图示：

```text
外部用户
   │
   ▼
tools/__init__.py   ← 公共出口（search, calc）
   │
   ├── search.py
   └── calc.py      ← 内部实现细节
```

#### 易错点

```python
# ❌ 在 __init__.py 里做重活
from mini_agent.tools.search import search
connect_database()          # 一 import tools 就连库
preload_huge_model()        # 启动巨慢
```

```python
# ✅ 只做轻量再导出 / 版本号
from .search import search
from .calc import calc
__all__ = ["search", "calc"]
```

#### JS 对照

| Python | JavaScript（近似） |
| --- | --- |
| `tools/__init__.py` 再导出 | `tools/index.js` 里 `export * from "./search.js"` |
| `from pkg.tools import search` | `import { search } from "./tools"`（看打包/解析规则） |

---

### 4.2 `__all__` 是什么？

#### 为什么需要它？

`from package import *` 时，Python 需要知道「公开哪些名字」。  
即使你不用 `import *`，`__all__` 也常被当作**公共 API 清单**——告诉读者：这些才是建议对外使用的。

#### 怎么写

```python
# mini_agent/tools/__init__.py
from .search import search
from .calc import calc

__all__ = ["search", "calc"]
```

#### 跑一下

```python
from mini_agent.tools import *  # 仍不推荐日常使用
# 此时通常只有 __all__ 里的名字进入当前命名空间
```

没有 `__all__` 时，`import *` 的行为更「宽松」：会导出不以下划线开头的名字。  
新手阶段记住：

> `__all__` = 公共接口说明书；真正项目里仍优先写明确导入。

#### 易错点

```python
# ❌ 写了字符串但和真实名字不一致
__all__ = ["serach"]  # 拼错；import * 会出问题

# ✅ 名字必须对得上
__all__ = ["search", "calc"]
```

---

### 4.3 空的 `__init__.py` 可以吗？

#### 为什么常写空文件？

很多目录只需要「被识别为包」，暂时不需要再导出。

#### 怎么写

```python
# mini_agent/__init__.py
# 空文件也行
```

或只放一点元信息：

```python
# mini_agent/__init__.py
"""A tiny agent-shaped package for learning imports."""

__version__ = "0.1.0"
```

#### 易错点 / 建议

先保证包可导入，再决定要不要在 `__init__.py` 里做再导出。  
不要一上来就在 `__init__.py` 里堆业务逻辑。

> 现代 Python 也支持无 `__init__.py` 的命名空间包（PEP 420）。本章先按「有 `__init__.py`」的常规包来学，够用且最不容易踩坑。详见 §8.2。

---

## 5. 必掌握：绝对导入 vs 相对导入

### 5.1 绝对导入（推荐作为默认）

#### 为什么需要绝对导入？

路径从包名写起，读代码时一眼知道东西从哪来；也更不容易被「当前文件在哪」干扰。

#### 怎么写

```python
from mini_agent.messages import create_message
from mini_agent.tools.search import search
```

图示：

```text
项目根
└── mini_agent/          ← 包根（绝对导入从这里写起）
    ├── messages.py
    └── tools/
        └── search.py
```

#### 跑一下

在项目根：

```bash
python -c "from mini_agent.messages import create_message; print(create_message('user','hi'))"
```

成功则打印消息 dict。

#### 易错点

```python
# ❌ 把文件系统路径当成导入路径
from ./mini_agent/messages import create_message  # 语法都不对

# ✅ 用点号包路径
from mini_agent.messages import create_message
```

#### JS 对照

| JavaScript | Python 绝对导入 |
| --- | --- |
| `import x from "@/messages"`（别名） | `from mini_agent.messages import x`（包名起步） |
| 依赖打包器/路径别名配置 | 依赖包在搜索路径上可见 |

优点：路径清晰，适合大多数应用代码。

---

### 5.2 相对导入（包内部常用）

#### 为什么需要相对导入？

包内部短距离引用时，不想把完整包名写很长；重构包名时也少改几处。

#### 怎么写

```python
# 在 mini_agent/tools/search.py 内部
from ..messages import create_message   # 上一级包中的 messages
from .calc import calc                  # 同级 calc
```

含义：

| 写法 | 含义 |
| --- | --- |
| `.` | 当前包 |
| `..` | 上一级包 |
| `...` | 上两级（少见，谨慎） |

图示：

```text
mini_agent/
├── messages.py      ← from ..messages（在 tools/ 里）
└── tools/
    ├── calc.py      ← from .calc
    └── search.py    ← 当前文件
```

#### 跑一下（正确姿势）

相对导入依赖「你处于包层级中」。推荐：

```bash
# 在项目根
python -m mini_agent.tools.search
```

而不是直接 `python search.py`（见下一小节）。

#### 易错点

```python
# ❌ 相对导入不能用在「非包上下文」里乱写
# ❌ 层数写错：本该 .. 却写成 ...
from ...messages import create_message  # 可能超出顶层包 → ImportError
```

它短，但依赖「你当前处在包层级里」。一旦启动方式不对，就会炸。

#### JS 对照

| JavaScript | Python |
| --- | --- |
| `import x from "../messages.js"` | `from ..messages import x` |
| `import y from "./calc.js"` | `from .calc import y` |
| 相对路径主要看文件位置 | 相对导入还依赖「以包身份加载」 |

---

### 5.3 最常见坑：把包内文件当脚本直接跑

#### 为什么会炸？

假如你在 `mini_agent/tools/` 里执行：

```bash
python search.py
```

然后 `search.py` 里写了 `from ..messages import ...`，往往会报：

```text
ImportError: attempted relative import with no known parent package
```

原因很直接：

> 直接跑文件时，Python 不认为它处于包层级中——此时 `__name__` 是 `"__main__"`，也没有父包信息。

对照：

```text
python search.py
  → 把 search.py 当独立脚本
  → 没有「我是 mini_agent.tools.search」的身份
  → 相对导入失败

python -m mini_agent.tools.search
  → 以包模块身份运行
  → 知道父包是 mini_agent.tools
  → 相对导入可以工作
```

#### 更稳妥的启动方式

```bash
# 在项目根目录（包含 mini_agent 目录的那一层）
python -m mini_agent.tools.search
```

或提供一个包外的入口脚本，只使用绝对导入（见 §10 的 `run_demo.py`）。

#### 易错点口诀

这一条如果你只记住一件事，就记住它——后面排导入错，十有八九和「怎么启动」有关。

| 场景 | 建议 |
| --- | --- |
| 调试包内模块 | `python -m package.module` |
| 给用户/自己一个入口 | 包外 `run_demo.py` + 绝对导入 |
| 临时双击/在子目录里 `python xxx.py` | 容易踩相对导入坑 |

---

### 5.4 选择建议

| 场景 | 建议 |
| --- | --- |
| 应用代码、跨多层目录 | 优先绝对导入 |
| 包内部短距离引用 | 相对导入可以，保持克制 |
| 既当库又当脚本的文件 | 小心相对导入，准备 `python -m` 入口 |
| 团队协作 | 一个项目定一种主风格，少混用 |

反例纠错：

```python
# ❌ 同一文件风格混乱
from mini_agent.messages import create_message
from .calc import calc

# ✅ 同一层内选一种主风格（应用代码更常全程绝对）
from mini_agent.messages import create_message
from mini_agent.tools.calc import calc
```

---

## 6. 建议掌握：`if __name__ == "__main__":`

### 6.1 `__name__` 是什么？

#### 为什么需要它？

同一个文件常常有两种用法：

1. **当库**：被别人 `import`，只提供函数  
2. **当脚本**：你直接运行它，做几行演示 / 手工测试

如果演示代码写在顶层，别人一导入就会执行——这很讨厌。

#### 怎么理解

- 模块被导入时：`__name__` 是模块名，如 `"mini_agent.messages"`
- 模块被直接运行时：`__name__` 是 `"__main__"`

图示：

```text
import mini_agent.messages
  → __name__ == "mini_agent.messages"
  → 不跑「脚本区」

python messages.py
  → __name__ == "__main__"
  → 跑「脚本区」
```

#### 怎么写

```python
# mini_agent/messages.py
def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}


if __name__ == "__main__":
    print(create_message("user", "demo"))
```

#### 跑一下

```bash
# 当脚本跑：会打印
python messages.py

# 当库导入：不会打印 demo
python -c "from mini_agent.messages import create_message; print('imported ok')"
```

效果：

- 别人 `import` 时，不会自动执行 demo  
- 你直接运行该文件时，可以做快速手工测试

可以记成：

> 上面是库，下面是「只有我自己跑这个文件时才执行的小实验台」。

#### 易错点

```python
# ❌ 演示代码写在顶层
def create_message(...):
    ...


print(create_message("user", "demo"))  # 任何人 import 都会打印
```

```python
# ❌ 缩进写错，条件失去意义
if __name__ == "__main__":
print("demo")  # IndentationError
```

#### JS 对照

前端没有完全相同的内置机制，但概念近似：

| 意图 | Python | JavaScript（近似） |
| --- | --- | --- |
| 库代码 | 模块顶层函数定义 | `export function ...` |
| 仅直接运行时执行 | `if __name__ == "__main__":` | 常靠打包入口 / `import.meta.url` 判断（环境相关） |

---

### 6.2 为什么 Agent 项目特别需要它？

#### 为什么？

工具文件里常会写几行本地试跑：不想另开一堆临时文件，又不想污染导入。

#### 怎么写

```python
def search(query: str) -> list[str]:
    return [f"result:{query}"]


if __name__ == "__main__":
    print(search("langgraph memory"))
```

#### 跑一下

```bash
python -m mini_agent.tools.search
# 或在确认无相对导入问题时：
# python mini_agent/tools/search.py
```

这样 `tools/search.py` 既是可导入模块，也是可临时调试的脚本。  
这比「为了试一下就另开一个乱七八糟的临时文件」干净得多。

#### 易错点

若文件里用了相对导入，请优先：

```bash
python -m mini_agent.tools.search
```

而不是在子目录里直接 `python search.py`（回到 §5.3）。

---

## 7. 建议掌握：常用标准库巡礼

#### 为什么要先混脸熟？

Agent 日常会反复碰到：JSON、路径、时间、环境变量、日志。  
标准库的正确用法不是「背表」，而是：

> 遇到问题先问：Python 自带有没有现成模块？

不必背；用到再查文档。

#### 怎么选（速查表）

| 模块 | 干什么 | Agent 里常见用法 |
| --- | --- | --- |
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

#### 跑一下（把前两章能力接进来）

```python
import json
from datetime import datetime, timezone
from pathlib import Path

payload = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "messages": [{"role": "user", "content": "hi"}],
}
Path("out.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(Path("out.json").read_text(encoding="utf-8"))
```

可能输出片段：

```text
{
  "ts": "2026-...",
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ]
}
```

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 自己建了 `json.py` | 盖住标准库 `json` |
| 路径用纯字符串拼接 | 优先 `pathlib.Path` |
| 一上来就装一堆第三方库 | 先看标准库够不够 |

#### JS 对照（直觉）

| Python | JavaScript |
| --- | --- |
| `json.dumps` / `json.loads` | `JSON.stringify` / `JSON.parse` |
| `pathlib.Path` | `node:path` / `fs` |
| `os.environ["KEY"]` | `process.env.KEY` |
| `datetime` | `Date`（或 dayjs 等） |

---

## 8. 了解即可：`sys.path` 与命名空间包

### 8.1 `sys.path`

#### 为什么需要知道它？

当你「装了包却导入了错误模块」，或「文件明明在却找不到」时，最终都要回到：

> Python 到底在哪些目录里找模块？顺序是什么？

#### 怎么理解（简化）

Python 找模块时会搜索一组路径：

```text
脚本目录 / 当前相关路径 / PYTHONPATH
→ 标准库相关路径
→ site-packages（含虚拟环境）
……
```

先匹配先生效：同名时靠前的路径会「盖住」靠后的。

#### 怎么看（了解即可）

```python
import sys
print(sys.path)
```

你会看到一个字符串列表——这就是搜索顺序。

#### 易错点

```python
# ❌ 业务代码里靠改 sys.path「急救」
import sys
sys.path.append("/some/path")  # 能跑，但脆弱、难移植、难测
```

临时把路径塞进 `sys.path` 能“修好”导入，但那是急救，不是长期方案。  
长期方案是：正确的包布局 + 可安装项目（`pyproject.toml` / `uv`），工程化章会讲。

排查口诀：

1. 先看当前工作目录  
2. 再看启动方式（`python file.py` vs `python -m package`）  
3. 再看 `sys.path` 顺序是否被奇怪路径污染

---

### 8.2 命名空间包

#### 为什么存在？

大型库有时要拆成多个发行包，却共用一个顶层名字（例如不同团队维护 `company.foo` / `company.bar`）。这时会用到**命名空间包**（PEP 420）：目录可以没有 `__init__.py`。

#### 应用项目怎么选？

应用项目里继续用常规包（有 `__init__.py`）最省心。

| 类型 | `__init__.py` | 新手建议 |
| --- | --- | --- |
| 常规包 | 有（可空） | ✅ 默认用这个 |
| 命名空间包 | 可无 | 了解即可，真需要再查 |

---

## 9. 常见坑（建议收藏）

这一节把前面散落的坑收成一张清单。遇到报错时，按顺序自查。

### 9.1 文件/目录名别和标准库撞车

```python
# 自己建了 json.py 后
import json  # 可能导到「你自己」，而不是标准库
```

报错可能很奇怪（缺 `dumps`、行为不对）。  
解决：改名（如 `json_utils.py`），并删掉同目录残留的 `json.pyc` / `__pycache__`。

### 9.2 循环导入

```text
a.py ──import──▶ b.py
  ▲                │
  └────import──────┘
```

症状：`ImportError: cannot import name 'X' from partially initialized module ...`

缓解：

1. 把共享结构抽到 `types.py` / `models.py`  
2. 把导入移进函数内部（应急）  
3. 重新划分边界，避免双向依赖

### 9.3 在错误的工作目录启动

```bash
# 你在 nested 目录里
cd mini_agent/tools
python ../../run_demo.py  # 有时碰巧能跑，路径心智却乱了
```

包找不到时，先确认「当前目录是谁」：

```bash
# Windows PowerShell
Get-Location
# 或
pwd
```

应在「能看见包根目录」的那一层启动。

### 9.4 混用绝对/相对导致风格混乱

一个项目定一种主风格，团队协作更稳。应用代码优先绝对导入。

### 9.5 在 `__init__.py` 里做重活

一 `import package` 就联网/读超大文件，会让启动变慢且难测。

### 9.6 `from x import y` 的「绑定」直觉

```python
# m.py
def f():
    return 1


# demo.py
from m import f
# 之后即便 m.f 被重新绑定，你手里的 f 仍指向旧对象（多数新手场景）
```

新手阶段记住：更偏向 `import module` 再 `module.func`，调试时心智更简单。

### 9.7 相对导入 + `python xxx.py` 直接跑

报：

```text
ImportError: attempted relative import with no known parent package
```

优先改用：

```bash
python -m package.module
```

或包外入口脚本 + 绝对导入。

### 9.8 快速排错对照表

| 报错关键词 | 先查什么 |
| --- | --- |
| `ModuleNotFoundError: No module named 'xxx'` | 工作目录、包名、是否在正确根目录 |
| `attempted relative import with no known parent package` | 是否用了 `python -m` / 是否包外入口 |
| `cannot import name ... partially initialized` | 循环导入 |
| 行为像「导错模块」 | 是否文件名撞标准库、`sys.path` 顺序 |

---

## 10. 综合小例子：搭一个可导入的 mini_agent

把前面所有必掌握点串起来。假设当前工作目录是：

```text
playground/01-python-basics/03-modules-packages/
```

### 10.1 目标目录

```text
03-modules-packages/
├── mini_agent/
│   ├── __init__.py          # 包标记 + 版本信息
│   ├── messages.py          # 消息结构
│   ├── runtime.py           # 一次最小「运行」
│   └── tools/
│       ├── __init__.py      # 再导出 search / calc
│       ├── search.py
│       └── calc.py
└── run_demo.py              # 包外入口（绝对导入 + __main__）
```

对应关系：

```text
包结构
  → 绝对导入（runtime / run_demo）
  → __init__.py 再导出（tools）
  → 入口脚本（__main__）
```

### 10.2 关键文件

```python
# mini_agent/__init__.py
"""A tiny agent-shaped package for learning imports."""

__version__ = "0.1.0"
```

```python
# mini_agent/messages.py
def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}


if __name__ == "__main__":
    # 仅直接运行本文件时做手工检查
    print(create_message("user", "demo"))
```

```python
# mini_agent/tools/search.py
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"result:{query}:{i}" for i in range(top_k)]


if __name__ == "__main__":
    print(search("RAG", top_k=2))
```

```python
# mini_agent/tools/calc.py
def calc(expr: str) -> float:
    # 学习示例：切勿对不可信输入用 eval
    return float(eval(expr, {"__builtins__": {}}, {}))


if __name__ == "__main__":
    print(calc("1+2"))
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
    """跑一轮极简流程：用户消息 → 工具结果 → 助手消息。"""
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

### 10.3 怎么跑

在 `03-modules-packages/` 目录执行：

```bash
python run_demo.py
```

若成功，大致会打印类似：

```text
{'role': 'user', 'content': 'what is RAG'}
{'role': 'assistant', 'content': "docs=['result:what is RAG:0', 'result:what is RAG:1'], calc=3.0"}
```

说明你已经走通：

```text
包结构
  → 绝对导入
  → __init__.py 再导出
  → 入口脚本（__main__）
```

这已经是真实项目最小骨架了。

### 10.4 为什么这样拆？（加强解释）

| 文件 | 职责 | 导入角色 |
| --- | --- | --- |
| `messages.py` | 只负责消息结构 | 被 `runtime` 绝对导入 |
| `tools/search.py` / `calc.py` | 具体工具实现 | 被 `tools/__init__.py` 再导出 |
| `tools/__init__.py` | 公共出口 | 让外部写 `from mini_agent.tools import search` |
| `runtime.py` | 编排一次最小流程 | 组合 messages + tools |
| `run_demo.py` | 包外入口 | 避免「包内文件直接跑」的相对导入坑 |

常见失败路径与修复：

| 现象 | 修复 |
| --- | --- |
| `No module named 'mini_agent'` | 确认 cwd 是含 `mini_agent/` 的那一层 |
| 相对导入报错 | 别在 `tools/` 里直接 `python search.py`；用 `run_demo.py` 或 `python -m` |
| `calc` 导入不到 | 检查 `tools/__init__.py` 是否再导出、`__all__` 是否包含 |

---

## 11. 练习指引

请打开并完成：

[`exercises/01-python-basics/03-modules-packages.md`](../../exercises/01-python-basics/03-modules-packages.md)

建议代码位置：

```text
playground/01-python-basics/03-modules-packages/
```

本章练习以「搭目录 + 跑通导入」为主，比纯算法题更接近真实项目。  
导入报错时，优先检查：当前工作目录、启动方式、包名是否和目录名一致。

自检三问：

1. 我能画出自己的目录树吗？  
2. 我知道该用 `python run_xxx.py` 还是 `python -m ...` 吗？  
3. 报错信息里的模块名，和我的目录名一致吗？

---

## 12. 小结与下一站

### 你现在应该掌握的心智模型

```text
文件 → 模块
目录(+__init__.py) → 包
import → 按搜索路径加载并缓存
入口脚本 / python -m → 决定「以什么身份运行」
```

再压缩一句：

> **结构对 + 启动方式对，导入才稳。**

### 自检清单

- [ ] 能手写一个含 `tools/` 子包的最小项目并成功导入
- [ ] 能解释绝对导入与相对导入的差异与常见报错
- [ ] 知道为何需要 `if __name__ == "__main__":`
- [ ] 知道 `__init__.py` / `__all__` 各自解决什么问题
- [ ] 遇到 `ModuleNotFoundError` 时知道先查工作目录与启动方式
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
