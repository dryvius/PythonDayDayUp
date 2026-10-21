# 项目结构

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：2～4 小时（有前端工程 / Node monorepo 经验可更快；包边界与 `python -m` 建议动手踩一遍）  
> 对应练习：[`exercises/03-engineering/01-project-structure.md`](../../exercises/03-engineering/01-project-structure.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：先把文件放对地方——包边界清晰、入口明确、配置可管。后面依赖、测试、日志都建立在这个骨架上。
- **你的优势**：前端里的 `src/`、入口文件、`.env`、测试目录经验可以直接迁移；重点盯住 Python 的「包 vs 脚本」「`python -m`」「谁依赖谁不能反」。
- **前置**：模块与包（`01` 第三章）。若导入机制还不熟，先补那一章再回来。

## 学习目标（学完应能做到）

1. 搭出适合 Agent/后端小项目的目录骨架（`app/` 或 `src/` 布局）。
2. 说清包边界：哪些是入口、哪些是库代码、哪些是测试；画出依赖方向。
3. 正确放置配置与入口（`main.py` / `__main__.py` / 环境变量），能用 `python -m` 跑起来。
4. 知道何时从单文件演进到模块化，而不必一上来微服务或 monorepo。
5. 完成课后练习，分清必掌握 / 建议掌握 / 了解即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | app/src 布局、包边界、配置与入口 | 能搭、能跑、能解释 |
| **建议掌握** | 单体到模块化演进 | 会拆分，不早拆 |
| **了解即可** | monorepo 多包 | 建立地图 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要「项目结构」？

前面你已经会写函数、模块、class。但 Agent 项目一旦超过「演示脚本」，没有结构时很容易变成：

```text
main.py（2000 行）
utils.py
helpers.py
test.py
new_test_final.py
fix_main_v2.py
```

症状通常是：

| 症状 | 背后缺什么 |
| --- | --- |
| 改工具要翻半个仓库 | 没有按职责分目录 |
| 测试文件 import 业务代码乱炸 | 没分清「库」和「入口」 |
| 换机器跑不起来 | 配置散落、密钥写死、启动方式脆 |
| 两人改同一文件天天冲突 | 拆分太晚或拆错边界 |

有结构时，同一件事通常长这样：

```text
app/
  agents/    # 编排：怎么跑一轮 Agent
  tools/     # 工具：search / calc / browse
  services/  # 外部能力：LLM / HTTP / DB 封装
  models/    # 数据形状：Message / Settings 相关结构
  config.py  # 配置集中读取
  main.py    # 入口：只组装，少写业务细节
tests/
pyproject.toml
.env.example
```

#### 结构解决的四件事

```text
找得到  →  知道 search 在 tools/，不在 main 里
改得动  →  改 LLM 封装不必动 Agent 编排
测得了  →  tests 能独立 import 公共模块
部署不慌 →  入口明确，配置不靠「本机路径玄学」
```

#### 本章要练的四种能力

1. **放对地方**：业务包、测试、配置、入口各归其位
2. **画清边界**：依赖只允许「上层 → 下层」，禁止乱串
3. **集中配置**：密钥走环境变量，读取集中在一处
4. **渐进演进**：先跑通，再按信号拆，而不是先造空架子

可以先记一句：

> 项目结构不是目录美学，而是让「找文件、改逻辑、写测试、换环境」的成本可预期。

---

## 2. 必掌握：推荐布局（小中型 Agent 项目）

这一节会刻意写细——布局是后面包边界、配置入口、依赖安装的共同底座。  
本路线默认用 **`app/` 扁平布局**；开源项目里常见的 `src/` 布局思想相同。

### 2.1 实用模板（本路线默认）

#### 为什么需要一套默认模板？

没有默认时，每个人会发明一套目录名：`core/`、`lib/`、`src/`、`backend/`……协作和对齐文档都贵。  
小中型 Agent / 后端服务，下面这套够用，也和练习题一致。

#### 怎么搭

```text
my-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # 入口：组装依赖并启动
│   ├── config.py            # 配置读取
│   ├── agents/
│   │   └── __init__.py
│   ├── tools/
│   │   └── __init__.py
│   ├── services/            # LLM / 外部 API 封装
│   │   └── __init__.py
│   └── models/              # dataclass / schema / 消息结构
│       └── __init__.py
├── tests/
│   ├── __init__.py          # 可选
│   └── test_tools.py
├── .env.example
├── pyproject.toml
└── README.md
```

各层职责（先建立地图，后面各节再加深）：

| 路径 | 放什么 | 不放什么 |
| --- | --- | --- |
| `app/main.py` | 读配置、组装对象、启动 | 长业务细节、复杂 Agent 循环 |
| `app/config.py` | `Settings`、从环境变量读取 | 业务逻辑、调 LLM |
| `app/agents/` | 编排：runner、路由、多步循环 | 具体 HTTP / 厂商 SDK 细节 |
| `app/tools/` | 可调用工具（search、calc…） | Agent 主循环 |
| `app/services/` | LLM / 外部 API / 基础设施封装 | UI、测试夹具 |
| `app/models/` | Message、Chunk、纯数据结构 | 有副作用的 IO |
| `tests/` | 测试 | 被业务代码反向 import |
| `.env.example` | 需要哪些环境变量（示例） | 真实密钥 |
| `pyproject.toml` | 项目元数据与依赖 | （下一章细讲） |
| `README.md` | 如何安装、如何运行 | 把代码贴满当文档 |

#### 跑一下（先确认「包」存在）

在项目根（`my-agent/`）创建上述空包后，至少保证：

```bash
# 在 my-agent/ 根目录
python -c "import app; print(app.__file__)"
```

预期类似：

```text
.../my-agent/app/__init__.py
```

若报 `ModuleNotFoundError: No module named 'app'`，多半是：

1. 当前工作目录不是项目根
2. 包名不是 `app`（目录名写错）
3. 缺少 `app/__init__.py`（学习阶段建议先补上，减少歧义）

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把业务代码直接扔在仓库根目录一堆 `.py` | 导入路径混乱，测试和脚本抢同一命名空间 |
| 包名叫 `json` / `http` / `test` | 和标准库 / 测试工具撞名，排错极痛苦 |
| 只有 `app/tools/search.py` 却没有 `tools/__init__.py` | 在部分场景下导入行为变脆（学习阶段建议包内都放） |
| README 不写「从哪一层目录启动」 | 别人（和未来的你）永远踩 `ModuleNotFoundError` |

#### JS/Node 对照

| 前端 / Node 常见 | 本路线 Python 对应 |
| --- | --- |
| `src/` 下放业务 | `app/`（或 `src/my_agent/`） |
| `package.json` | `pyproject.toml`（下一章） |
| `.env.example` | 同名，原则相同 |
| `__tests__/` 或 `*.test.ts` | 顶层 `tests/`（pytest 惯例） |
| `src/index.ts` / `main.ts` | `app/main.py` 或 `python -m app` |

前端习惯「一切在 `src/`」；Python 社区两种都常见——先认准本路线的 `app/` 即可。

---

### 2.2 每个子包放什么：按 Agent 心智拆

#### 为什么要按 agents / tools / services / models 拆？

Agent 代码天然有几类「不同变化速度」的东西：

```text
models     → 数据结构变少、变稳
tools      → 工具可增删，接口相对稳定
services   → 厂商 SDK / HTTP 细节常换
agents     → 编排策略会迭代
main/config→ 组装与配置，应保持薄
```

把它们揉进一个文件，改「换一个 LLM 厂商」会碰到编排；改「加一个 tool」会碰到配置。分目录是为了**改动面可控**。

#### 怎么写（最小文件示意）

```python
# app/models/message.py
def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}
```

```python
# app/tools/search.py
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]
```

```python
# app/services/llm.py
class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"
```

```python
# app/agents/runner.py
from app.models.message import create_message


class AgentRunner:
    def __init__(self, llm, tools: list, max_steps: int = 8) -> None:
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def run(self, question: str) -> str:
        _ = create_message("user", question)
        # 教学简化：只演示「编排调用 tools + llm」
        search = self.tools[0]
        docs = search(question)
        return self.llm.complete(f"q={question}; docs={docs}")
```

#### 对照示例：目录与职责一张图

```text
用户问题
   ↓
main 组装 Settings + EchoLLM + SearchTool + AgentRunner
   ↓
agents/runner 编排
   ├── tools/search     （检索）
   ├── services/llm     （生成）
   └── models/message   （消息形状）
```

#### 易错点

- **`services` 不是「随便塞杂项」**：优先放「对接外部世界」的封装（LLM、HTTP、DB）
- **`utils.py` 大杂烩**很快会变成第二个 `main.py`；宁可按领域再拆，也不要无限膨胀万能工具箱
- **`models` 里写 IO**（读文件、打 API）会污染「纯数据」层，测试变难

#### JS/前端对照

| 前端常见分层 | Agent Python 对应直觉 |
| --- | --- |
| `types/` / `models/` | `app/models/` |
| `api/` / `services/` | `app/services/` |
| `components/`（可复用 UI 单元） | `app/tools/`（可复用能力单元） |
| `pages/` / `app/` 路由编排 | `app/agents/` |
| `main.ts` 挂载应用 | `app/main.py` |

名字不必一一对应，重要的是：**编排层不要直接堆厂商 SDK 细节**。

---

### 2.3 `app/` 布局 vs `src/` 布局

#### 为什么会有两种布局？

都是为了把「可安装的业务包」和「仓库里的脚本/测试/文档」分开。差别主要在：**业务包离仓库根有多远**，以及「误把仓库根当包」的概率。

#### 怎么对照

| 风格 | 例子 | 特点 | 适合 |
| --- | --- | --- | --- |
| flat app | 根下直接 `app/` | 简单，路径短，教程友好 | 本路线、小项目、练习 |
| src layout | `src/my_agent/` | 更规范；减少「误导入仓库根脚本」 | 要打包发布、多人库项目 |

`src/` 布局示意：

```text
my-agent/
├── src/
│   └── my_agent/          # 真正的业务包名
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── agents/
│       ├── tools/
│       ├── services/
│       └── models/
├── tests/
├── pyproject.toml
└── README.md
```

导入会变成：

```python
from my_agent.tools.search import search
# 而不是
from app.tools.search import search
```

#### 跑一下（心智对比即可）

学习阶段继续用：

```bash
python -m app.main
```

以后读开源看到：

```bash
python -m my_agent.main
# 或安装后
my-agent-cli
```

不要慌：把 `app` 换成包名即可，目录思想一样。

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 同时存在根目录 `app.py` 和包目录 `app/` | 导入时极易撞车 |
| 包名用 `src` | `src` 是布局文件夹，不是业务包名；业务包应是 `my_agent` 这种名字 |
| 学习阶段死磕 packaging 细节 | 先把 `app/` + `python -m` 跑通；可编辑安装下一章再讲 |

#### JS/Node 对照

| Node / 前端 | Python |
| --- | --- |
| `src/index.ts`，包名在 `package.json` 的 `name` | `src/my_agent/`，包名常与目录一致 |
| 直接 `node src/index.js` | 更推荐 `python -m my_agent.main`，而不是裸跑深层文件 |
| monorepo 里 `packages/foo/src` | 类似「多包 + src layout」，本章末了解即可 |

学习阶段用 `app/` 完全够；见到 `src/` 只换「包名路径」，不必重学一套哲学。

---

### 2.4 仓库根还该有什么（最小集）

#### 为什么根目录不能只塞 `app/`？

根目录是「人与工具的入口」：安装依赖、读说明、放环境变量模板、放测试。  
业务代码进包；**元数据与协作文件留在根**。

#### 怎么放

```text
my-agent/
├── app/                 # 业务包
├── tests/               # 测试
├── .env.example         # 环境变量清单（无密钥）
├── .gitignore           # 忽略 .venv、__pycache__、.env 等
├── pyproject.toml       # 项目与依赖（下一章）
└── README.md            # 如何运行
```

`.gitignore` 最低限度应覆盖（示例片段）：

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
.pytest_cache/
```

#### 易错点

- 提交 `.env`（真实密钥）——这是事故，不是风格问题
- 提交 `.venv/`——仓库会巨大且不可移植
- 根目录堆 `scratch.py`、`notebook_final.ipynb` 却不说明——可以本地玩，但别让「临时文件」变成正式入口

#### 前端对照

和前端仓库根放 `package.json`、`.env.example`、`README`、忽略 `node_modules` 是同一类纪律；Python 里忽略的是 `.venv` / `__pycache__` / `.env`。

---

## 3. 必掌握：包边界

布局解决「文件在哪」；边界解决「谁可以依赖谁」。  
边界一糊，目录再漂亮也会循环导入、测试牵一发而动全身。

### 3.1 谁依赖谁（建议方向）

#### 为什么需要依赖方向？

没有方向时，常见崩溃是：

```text
tools/search.py  import  agents/runner.py
agents/runner.py import  tools/search.py
→ 循环导入 / 层次消失
```

有了方向，每个文件都知道自己「可以看下层，不该看上层」。

#### 怎么画（本路线建议）

```text
main（组装）
  → agents（编排）
      → tools / services / models
tests → 任意公共模块（不要反向被业务依赖）
config ← 被 main / 少数组装点读取
```

更细一点：

```text
允许：
  main        → config, agents, services, tools, models
  agents      → tools, services, models, config（谨慎）
  tools       → models, services（若工具需要 IO 封装）
  services    → models（以及第三方库）
  models      →（尽量只依赖标准库 / typing）

禁止或强力避免：
  tools       → agents
  models      → agents / tools / services
  任意业务    → tests
  到处        → from app.main import ...
```

#### 对照示例

```python
# ✅ agents 依赖 tools —— 符合方向
# app/agents/runner.py
from app.tools.search import search


def run(question: str) -> list[str]:
    return search(question)
```

```python
# ❌ tools 依赖 agents —— 反向， entangle
# app/tools/search.py
from app.agents.runner import AgentRunner  # 别这样
```

#### 易错点

| 错法 | 后果 |
| --- | --- |
| `from app.main import settings` | 入口变成「全局大字典」，测试与复用困难 |
| `models` 为了方便去 import `services` | 数据层被 IO 绑死，单测要打真网 |
| 「先互相 import 再说」 | 循环导入；短期用延迟 import 救命，长期靠重画边界 |

#### JS/前端对照

| 前端常见规则 | Python 对应 |
| --- | --- |
| `components` 不依赖 `pages` | `tools` 不依赖 `agents` |
| `utils` 不依赖业务页面 | `models` 不依赖编排 |
| 测试文件不被 `src` 引用 | `tests` 不被 `app` 引用 |
| 避免 `import from '../app'` 穿透 | 避免业务去 import `main` |

前端 lint 里常见的 `import/no-cycle`、分层 ESLint 规则，和这里的「依赖方向」是同一问题。

---

### 3.2 入口只做组装，不写业务细节

#### 为什么入口要薄？

`main.py` 若既读配置、又写 Agent 循环、又拼 prompt、又解析工具结果：

1. **测不动**：要测编排必须启动整个入口
2. **换入口难**：明天加 CLI / FastAPI，只能复制粘贴
3. **边界消失**：所有人改需求都挤进 `main.py`

入口的工作应接近「接线板」：创建对象、注入依赖、调用一次 `run`。

#### 怎么写

```python
# app/main.py
from app.agents.runner import AgentRunner
from app.config import Settings
from app.services.llm import EchoLLM
from app.tools.search import search


def main() -> None:
    settings = Settings.from_env()
    agent = AgentRunner(
        llm=EchoLLM(),
        tools=[search],
        max_steps=settings.max_steps,
    )
    print(agent.run("what is RAG"))


if __name__ == "__main__":
    main()
```

拆开看：

1. **import 组装所需零件**——不在这里实现 `search` / `complete`
2. **`Settings.from_env()`**——配置集中入口
3. **构造 `AgentRunner(...)`**——依赖注入：llm / tools 从外面传进
4. **`if __name__ == "__main__"`**——既可 `python -m app.main`，也可被测试 import 而不立刻执行

#### 跑一下

在项目根：

```bash
python -m app.main
```

预期类似（取决于你的 `EchoLLM` / `search` 实现）：

```text
ECHO: q=what is RAG; docs=['doc:what is RAG:0', ...]
```

#### 易错点

- 在 `main` 里写 200 行 prompt 拼接——应下沉到 `agents/` 或 `services/`
- 在 `main` 里 `os.getenv` 散落多处——应进 `config.py`
- 把 `main` 当模块被到处 import 业务函数——入口模块应保持「很少被依赖」

#### JS/Node 对照

```text
// 类似前端
main.ts / index.ts
  → createApp()
  → 挂载 router / store / 根组件
  → 不在 main 里写某个页面的业务细节
```

```text
// 类似 Nest/Express
main.ts bootstrap
  → 创建 app、挂 middleware、listen
  → 业务在 module / controller / service
```

Python 的 `app/main.py` 就是 bootstrap，不是「整个后端」。

---

### 3.3 测试目录的边界

#### 为什么 `tests/` 必须在业务包之外？

测试是「使用你的包的客户」，不是包的一部分。  
业务代码一旦 `import tests.xxx`，等于生产依赖测试夹具——部署与打包都会变味。

#### 怎么放

```text
my-agent/
├── app/
│   └── tools/
│       └── search.py
└── tests/
    └── test_tools.py
```

```python
# tests/test_tools.py
from app.tools.search import search


def test_search_returns_items() -> None:
    assert search("rag")  # 非空即可（pytest 下一章系统讲）
```

#### 易错点

- 把测试写进 `app/tests/` 又被打包进发布物（以后 packaging 时更痛）
- 测试里靠「改 `sys.path` 鬼打墙」而不是从项目根 / 可编辑安装导入
- 为了方便，业务代码去读 `tests/fixtures`——应把共用夹具抽到 `app` 可测的公共模块，或测试专用目录且仅测试引用

#### 前端对照

和「`src` 不 import `__tests__`」同一纪律；Vitest/Jest 的测试文件是消费者，不是运行时依赖。

---

### 3.4 循环导入：边界出了问题的报警灯

#### 为什么它会出现？

顶层互相 import：

```python
# app/agents/runner.py
from app.tools.search import search  # 加载 tools

# app/tools/search.py
from app.agents.runner import AgentRunner  # 又加载 agents → 炸
```

#### 怎么处理（分层级）

1. **根本办法**：重画依赖方向（tools 不依赖 agents）
2. **权宜之计**：把 import 挪进函数内（延迟导入），先让程序跑起来
3. **结构办法**：把双方都依赖的「纯函数 / 纯模型」抽到 `models/` 或更中立的模块

```python
# 权宜：延迟导入（能跑，但不代替边界治理）
def run(question: str) -> str:
    from app.services.llm import EchoLLM
    return EchoLLM().complete(question)
```

#### 易错点

> 延迟导入是止痛药，不是架构。

若你发现「到处都要延迟导入」，说明包边界该重构了。

#### JS 对照

和 ESM/CJS 循环依赖类似：有时能得到 `undefined` 的部分导出。Python 更常直接 `ImportError` 或属性尚未绑定。治理手段一样——**减少环，而不是技巧压环**。

---

## 4. 必掌握：配置与入口

「代码放对」之后，还要解决两件实事：

1. **配置从哪来**（尤其是密钥）
2. **进程从哪启动**（导入路径才稳定）

### 4.1 配置放哪：集中读取

#### 为什么需要集中配置？

没有集中时：

```python
# tools/search.py
TOP_K = int(os.getenv("TOP_K", "3"))

# services/llm.py
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

# agents/runner.py
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))
```

问题：

- 变量名不统一（`TOP_K` vs `APP_TOP_K`）
- 默认值散落，改一处漏三处
- 测试想注入配置很麻烦
- 密钥更容易被不小心写进代码

#### 怎么写

```python
# app/config.py
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    model: str = "gpt-4.1-mini"
    max_steps: int = 8
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            model=os.getenv("APP_MODEL", "gpt-4.1-mini"),
            max_steps=int(os.getenv("APP_MAX_STEPS", "8")),
            api_key=os.getenv("APP_API_KEY"),
        )
```

原则：

1. **密钥走环境变量**，不写死在代码或仓库里
2. 提供 **`.env.example`**，真 `.env` 不进 git
3. **配置集中读取**，避免每个文件自己 `os.getenv`
4. 用 `frozen=True`（或习惯上只读）减少运行期被随便改掉

`.env.example` 示例：

```dotenv
APP_MODEL=gpt-4.1-mini
APP_MAX_STEPS=8
APP_API_KEY=
```

#### 跑一下

```python
import os
from app.config import Settings

os.environ["APP_MAX_STEPS"] = "3"
settings = Settings.from_env()
print(settings.max_steps)  # 3
print(settings.model)      # gpt-4.1-mini（未覆盖则默认）
```

在入口中：

```python
settings = Settings.from_env()
agent = AgentRunner(llm=EchoLLM(), tools=[search], max_steps=settings.max_steps)
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 把真 Key 写进 `config.py` 默认值 | 一 push 就泄露 |
| 提交 `.env` | 同上 |
| `max_steps=os.getenv(...)` 忘了 `int(...)` | 类型变成 `str`，比较/运算埋雷 |
| 每个模块私藏一份 Settings 单例并在 import 时读环境 | 测试里改环境变量顺序敏感，难控 |

学习阶段用 `os.getenv` + `dataclass` 足够。`pydantic-settings`、python-dotenv 自动加载等，等依赖章熟悉后再加，不妨碍先练集中读取。

#### JS/Node 对照

| Node / 前端 | Python |
| --- | --- |
| `process.env.APP_API_KEY` | `os.getenv("APP_API_KEY")` |
| `dotenv` + `.env` | 可加 `python-dotenv`；原则相同 |
| 不要把密钥打进前端包 | 不要把密钥写进仓库；后端同理 |
| `config/index.ts` 集中导出 | `app/config.py` 的 `Settings` |

Vite 里 `VITE_` 前缀暴露给浏览器——那是前端特有坑；Python Agent 默认全在服务端，仍必须把密钥当秘密。

---

### 4.2 怎么启动：优先 `python -m`

#### 为什么启动方式会影响「能不能 import」？

Python 的导入依赖「当前是谁当顶层包 / `sys.path` 里有什么」。  
用错方式启动时，常见现象是：文件明明在，却 `ModuleNotFoundError: No module named 'app'`。

#### 怎么写 / 怎么跑

推荐（在项目根 `my-agent/`）：

```bash
python -m app.main
```

含义直觉：

```text
把当前环境的「模块搜索」按包方式加载 app.main
→ 相对/绝对导入更符合包语义
→ 工作目录仍是你启动时所在目录（一般是项目根）
```

也可以：

```bash
python app/main.py
```

但这条路径更脆：有时 `app` 不被当成包、相对导入失败，或你在子目录里启动时路径全乱。

**学习阶段口诀**：

> 先回到项目根，再用 `python -m 包.模块`。

#### 跑一下（对照两种失败）

```bash
# 错误示范 1：站在错误目录
cd app
python -m app.main
# 常见：No module named 'app'

# 错误示范 2：把包内文件当孤立脚本乱跑，还用相对导入
cd app/agents
python runner.py
# 常见：ImportError / 相对导入失败
```

正确：

```bash
cd /path/to/my-agent
python -m app.main
```

#### 易错点

| 错法 | 说明 |
| --- | --- |
| 在 IDE 里「右键跑某个子文件」却没设工作目录 | 和命令行踩同一类坑 |
| 靠修改 `sys.path.insert(0, ...)` 救所有脚本 | 能跑一会儿，换机器/换入口就炸；优先修正启动方式与布局 |
| 把 `PYTHONPATH=.` 当唯一方案 | 可作权宜，长期仍应「根目录 + `-m`」或可编辑安装（下一章） |

#### JS/Node 对照

| Node | Python |
| --- | --- |
| 在包根执行 `node src/index.js` / `npm start` | 在项目根执行 `python -m app.main` |
| 深层文件里用相对路径 `require` 乱跳 | 深层 `python xxx.py` + 相对导入易炸 |
| `package.json` 的 `"main"` / `"bin"` | 以后可在 `pyproject.toml` 配脚本入口 |

前端很少「cd 进 components 再 node 某个文件当应用入口」；Python 也一样，**入口从项目根启动**。

---

### 4.3 `main.py` vs `__main__.py`

#### 为什么会有两个名字？

两者都能当入口，但触发方式略有不同：

| 文件 | 典型启动 | 含义 |
| --- | --- | --- |
| `app/main.py` | `python -m app.main` | 明确跑 `main` 模块 |
| `app/__main__.py` | `python -m app` | 「把整个包当脚本跑」时的入口 |

#### 怎么写

```python
# app/__main__.py
from app.main import main

if __name__ == "__main__":
    main()
```

这样：

```bash
python -m app        # 走 __main__.py → 调用真正的 main()
python -m app.main   # 直接走 main.py
```

#### 易错点

- 两处各写一套完整业务——必漂；应只在一处实现 `main()`，另一处调用
- 以为有了 `__main__.py` 就可以在任意目录乱启动——工作目录与包路径规则不变

#### Node 对照

类似 `package.json` 里 `"main"` 与 `"bin"` / `npm start` 脚本：可以有多个入口别名，但**实现应只有一份**。

---

### 4.4 `if __name__ == "__main__"` 为什么还要写

#### 为什么需要它？

同一个文件可能被：

1. **当入口执行** → 应该跑 `main()`
2. **当模块 import** → 只应提供函数/类，不应副作用启动

```python
def main() -> None:
    print("boot")


if __name__ == "__main__":
    main()
```

#### 跑一下（对照）

```bash
python -m app.main
# 会执行 main()

python -c "import app.main; print('imported only')"
# 不应自动 boot（若你正确使用了守卫）
```

#### 易错点

- 顶层直接 `Settings.from_env(); agent.run(...)` 无守卫——pytest 收集/导入时可能副作用连发
- 把大量逻辑塞进 `if __name__` 块而不是 `main()` 函数——不利于测试与复用

#### JS 对照

浏览器打包入口天然是「只启动一次」；Node 里也有类似：

```javascript
// 近似直觉
if (require.main === module) {
  main();
}
```

Python 用 `__name__ == "__main__"` 表达同一意图。

---

### 4.5 最小可运行链路（综合小例子）

把布局、边界、配置、入口串起来。可按此搭，再对照练习题加深。

#### 目录

```text
my-agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── llm.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── message.py
│   └── agents/
│       ├── __init__.py
│       └── runner.py
├── tests/
│   └── test_smoke.py
├── .env.example
└── README.md
```

#### 关键代码

```python
# app/config.py
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_steps: int = 8

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(max_steps=int(os.getenv("APP_MAX_STEPS", "8")))
```

```python
# app/models/message.py
def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}
```

```python
# app/tools/search.py
def search(query: str, top_k: int = 3) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]
```

```python
# app/services/llm.py
class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"
```

```python
# app/agents/runner.py
from collections.abc import Callable, Protocol

from app.models.message import create_message


class LLMLike(Protocol):
    def complete(self, prompt: str) -> str: ...


class AgentRunner:
    def __init__(
        self,
        llm: LLMLike,
        tools: list[Callable[..., list[str]]],
        max_steps: int = 8,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def run(self, question: str) -> str:
        _ = create_message("user", question)
        docs = self.tools[0](question)
        # max_steps 先占位，后续真 Agent 循环再用
        _ = self.max_steps
        return self.llm.complete(f"q={question}; docs={docs}")
```

`Protocol` 让 `agents` 依赖「能 complete 的对象」，而不 import 具体的 `EchoLLM`——这正是包边界想要的效果。若尚未接触 Protocol，写成无注解的 `llm` 参数也可以，先保证能跑。
```python
# app/main.py
from app.agents.runner import AgentRunner
from app.config import Settings
from app.services.llm import EchoLLM
from app.tools.search import search


def main() -> None:
    settings = Settings.from_env()
    agent = AgentRunner(
        llm=EchoLLM(),
        tools=[search],
        max_steps=settings.max_steps,
    )
    print(agent.run("what is RAG"))


if __name__ == "__main__":
    main()
```

#### 跑一下

```bash
cd my-agent
python -m app.main
```

预期类似：

```text
ECHO: q=what is RAG; docs=['doc:what is RAG:0', 'doc:what is RAG:1', 'doc:what is RAG:2']
```

#### 这里用到了什么？

```text
app/ 布局
  → 包边界：main 组装，agents 编排，tools/services/models 下沉
  → Settings.from_env 集中配置
  → python -m app.main 稳定启动
  → EchoLLM 无密钥可跑（符合课程 Fake/Echo 约定）
```

#### 你可以怎么改着玩？

1. 把 `search` 换成 class `SearchTool`，注入方式不变
2. 增加 `APP_MODEL` 并在打印里带上 `settings`
3. 写 `tests/test_smoke.py` 只测 `search("x")` 非空

---

## 5. 建议掌握：从单文件演进

不要一上来过度设计。很多好项目都是「先跑通，再按疼点拆」。

### 5.1 推荐演进路径

#### 为什么要「演进」而不是「首日完美架构」？

过早拆分的代价：

- 空目录、空 `__init__.py`、假接口比真实需求还多
- 你还不知道变化点在哪，边界会拆错
- 心理上「架构完成了」，实际上主流程还没跑通

过晚拆分的代价：

- 单文件上千行，测试无从下手
- 合并冲突频繁
- 想换 LLM / 加 tool 只能复制粘贴

#### 怎么走（四步）

```text
1) 单文件原型跑通
2) 拆 tools / services（变化快、可单测的部分先出去）
3) 加 config / tests（可配置、可回归）
4) 再考虑多 agent 包、插件化、更重的框架
```

#### 对照示例：从 1 个文件到骨架

**阶段 A — 单文件**

```python
# proto.py
def search(query: str) -> list[str]:
    return [f"doc:{query}:0"]


class EchoLLM:
    def complete(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


def main() -> None:
    q = "what is RAG"
    docs = search(q)
    print(EchoLLM().complete(f"q={q}; docs={docs}"))


if __name__ == "__main__":
    main()
```

**阶段 B — 拆 tools / services**

```text
app/
  tools/search.py
  services/llm.py
  main.py          # 仍可暂时承担编排
```

**阶段 C — 加 config / tests / agents**

```text
app/
  config.py
  agents/runner.py
  tools/ ...
  services/ ...
  models/ ...
  main.py          # 变薄
tests/
```

#### 易错点

- 阶段 A 都没跑通，就先建 monorepo——空转
- 阶段 B 把「所有函数」平均洒进 20 个文件——导航成本高于收益
- 为了「看起来像大厂」先上微服务——学习项目通常是负收益

#### 前端对照

和前端「先一个 `App.vue` / `App.tsx` 跑通，再拆 components、再抽 `api/`、再上状态库」同一节奏。  
**先垂直切片可演示，再横向分层。**

---

### 5.2 拆分信号：什么时候该动刀？

#### 为什么需要信号，而不是感觉？

「代码丑」太主观；下面信号更可操作：

| 信号 | 建议动作 |
| --- | --- |
| 单文件 > 300～400 行且多职责 | 按 tools/services/agents 切开 |
| 测试无从下手（必须启动全家桶） | 把纯函数/工具抽到可 import 模块 |
| 两人以上频繁改同一文件冲突 | 按变化点拆文件 |
| 同一段逻辑复制 3 次以上 | 抽模块，而不是再复制第 4 次 |
| 换 LLM / 加 tool 要改 10 处 | 引入 `services` / `tools` 边界 + 注入 |

#### 怎么拆（实操顺序）

1. **先找稳定接口**：`search(query) -> list[str]`、`complete(prompt) -> str`
2. **再搬实现**：把函数/类剪到新文件，旧处改 import
3. **跑通主路径**：`python -m app.main` 仍然绿
4. **最后补测试**：锁住刚抽出的纯逻辑

#### 易错点

> 拆分的第一天验收标准仍是：主路径能跑、导入不炸。

不要拆完只留下「目录很漂亮但 `main` 红着」。

#### JS 对照

React 里「组件超过一屏就拆」和这里「文件多职责就拆」类似；但也不要为了拆而拆出一百个只有三行的文件——**按职责与变化点拆**，不是按行数宗教。

---

### 5.3 不该过早做的事

#### 为什么要列「不要清单」？

工程化章节最容易焦虑性过度设计。先明确学习项目通常**不必**一上来就做的事：

| 先别急着做 | 原因 |
| --- | --- |
| 微服务拆多仓库 | 部署与调试成本暴涨，学习信号被淹没 |
| 完整插件系统 / 动态发现 | 有 2～3 个 tool 时，列表注入就够 |
| 自研框架层 | 先把业务跑通；框架感放到后面 Agent 模块 |
| monorepo 多包 | 个人小项目收益低（见下一节） |
| 为每个文件夹写「未来或许」的空抽象 | 抽象应来自重复，而不是想象 |

#### 口诀

```text
先能跑 → 再能测 → 再能配 → 最后才「平台化」
```

#### 前端对照

相当于：还没做出页面，就先上微前端 + 自建组件库 + 完整 design system。  
可以向往，但不是第一章的任务。

---

## 6. 了解即可：monorepo 多包

#### 为什么只需了解？

一个仓库多个包（例如 `packages/core`、`packages/web`、`packages/cli`）适合：

- 多团队共享库
- 多产物（SDK + API + Worker）强同步发版
- 平台型代码组织

个人 Agent 学习项目、单服务小后端，**单包 `app/` 足够**。见到开源 monorepo 时能认地图即可，不必照搬。

#### 长什么样（地图）

```text
repo/
├── packages/
│   ├── core/          # 共享领域库
│   ├── agent-api/     # 服务
│   └── agent-cli/     # 命令行
├── pyproject.toml     # 或每个包各自一份 + 工具链编排
└── README.md
```

#### 和单包的关系

```text
单包 app/     →  本路线默认
多包 monorepo →  边界从「目录」升级到「可独立版本的包」
```

多包会引入：包间依赖版本、构建顺序、统一 lint/test 工具链——收益与成本都明显上升。

#### 易错点（认知向）

- 把「多几个文件夹」误叫 monorepo——monorepo 通常指多包/多项目共存与工具链
- 还没共享代码需求就先拆 `packages/*`——多半是仪式感

#### JS 对照

和 pnpm workspace / Turborepo / Nx 的 `packages/*` 同一物种。  
前端同学若用过 workspace，迁移概念很快；Python 侧常见工具是 uv workspace、pants、bazel 等——知道存在即可，本路线不展开。

---

## 7. 常见坑

1. **包名与第三方库/标准库撞名**（`json.py`、`http.py`、`typing.py`）  
   → 导入到的可能不是你写的那个文件。

2. **在子目录里乱跑脚本**  
   → `ModuleNotFoundError`；先 `cd` 到项目根，用 `python -m app.main`。

3. **把虚拟环境、`__pycache__`、`.env` 提交进 git**  
   → 用 `.gitignore`；密钥按事故处理（轮换）。

4. **循环导入**  
   → 短期延迟导入，根本靠依赖方向；禁止 `tools → agents`、`业务 → tests`。

5. **入口太胖 / 到处 `from app.main import ...`**  
   → `main` 只组装；配置进 `config`；编排进 `agents`。

6. **配置散落 `os.getenv`**  
   → 统一 `Settings.from_env()`；示例进 `.env.example`。

7. **过早 monorepo / 微服务**  
   → 单包跑通并有测试后，再按真实共享需求升级。

8. **`app/` 与 `app.py` 并存**  
   → 导入歧义；删掉或改名其中一个。

---

## 8. 练习指引

请打开并完成：

[`exercises/03-engineering/01-project-structure.md`](../../exercises/03-engineering/01-project-structure.md)

建议代码位置：

```text
playground/03-engineering/01-project-structure/
```

建议路径：

1. 先按模板搭出 `app/` + `tests/` + `.env.example`
2. 实现最小链路：`models` / `tools` / `services` / `config` / `main`，保证 `python -m app.main` 可跑
3. 书面画出依赖方向（练习 B3），刻意避免反向依赖
4. 有余力：把编排挪进 `agents/runner.py`，让 `main` 只组装；再补一条 smoke 测试

先按自己的理解搭出来即可；尤其是「工作目录 + `python -m`」和「入口要薄」，踩一次比只看文档记得更牢。

---

## 9. 小结与下一站

### 你现在应该掌握的心智模型

```text
业务进 app/（或 src/包名）
测试进 tests/，永不被业务反向依赖
main 只组装；agents 编排；tools/services/models 下沉
配置集中 Settings.from_env；密钥不进仓库
从项目根 python -m 启动
先单文件跑通，再按信号拆分；别首日 monorepo
```

### 自检清单

- [ ] 能画出 `app/agents|tools|services|models` 各自职责
- [ ] 能说明依赖方向，并举一个「禁止的反向依赖」例子
- [ ] 入口只组装，配置集中在 `config.py`
- [ ] 能用 `python -m app.main`（或等价方式）跑起来
- [ ] 能说出至少 3 个「该从单文件拆出去」的信号
- [ ] 知道 monorepo 是什么，以及为什么学习项目不必上
- [ ] 独立完成练习基础题

### 下一章

[`02-deps-venv.md`](./02-deps-venv.md) —— 虚拟环境、pip/uv、`pyproject.toml`、环境变量与可编辑安装，让这个骨架真正「可安装、可复现」。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一模块：[类型系统](../02-advanced-python/07-typing-system.md)
- 下一章：[依赖与虚拟环境](./02-deps-venv.md)
