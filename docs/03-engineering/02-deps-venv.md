# 依赖与虚拟环境

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/03-engineering/02-deps-venv.md`](../../exercises/03-engineering/02-deps-venv.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：把依赖隔离、声明、安装、锁定；并学会用环境变量管理密钥与配置。
- **建议工具**：本仓库约定可用 `uv`；同时必须理解 `venv` + `pip`（到处都能见到）。
- **前置**：上一章项目结构；会在终端进到项目根目录。

## 学习目标（学完应能做到）

1. 创建并激活虚拟环境，解释为什么需要它。
2. 用 `pip` / `uv` 安装依赖，读懂 `pyproject.toml`。
3. 区分开发依赖与运行依赖；理解锁文件价值。
4. 用环境变量管理 API Key，不把密钥写进代码仓库。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | venv、pip、uv、pyproject.toml、环境变量 | 能独立建环境装依赖 |
| **建议掌握** | 锁文件、ruff/formatter | 会用、能解释为何需要 |
| **了解即可** | 多环境发布 | 建立地图 |

---

## 1. 为什么要学

#### 为什么全局乱装依赖会出事？

没有隔离时，所有项目共用「系统里那一套 site-packages」：

```text
项目 A 需要 requests==2.28
项目 B 需要 requests==2.32
同一台机器互相踩脚
```

表现往往是：

- A 昨天还能跑，今天装了 B 就挂了
- 「我电脑上能跑」——因为你本机装过一堆别人项目不需要的包
- Agent 项目还会装 `httpx`、`openai`、向量库客户端等，没有隔离很快灾难

#### 虚拟环境解决什么？

虚拟环境 = **每个项目一套独立的 site-packages**（再加一份独立的 `python`/`pip` 入口）。

心智图：

```text
系统 Python（别乱动）
   │
   ├─ 项目 A/.venv  → 只装 A 的依赖
   └─ 项目 B/.venv  → 只装 B 的依赖
```

可以先记一句：

> 依赖隔离不是「高级技巧」，而是让项目可复现、可协作、可部署的底线。

#### 和前端对照（先建立地图）

| 概念 | Python | Node / 前端 |
|------|--------|-------------|
| 项目本地依赖目录 | `.venv/`（解释器 + site-packages） | `node_modules/` |
| 依赖声明 | `pyproject.toml`（或 `requirements.txt`） | `package.json` |
| 锁文件 | `uv.lock` / `poetry.lock` 等 | `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` |
| 安装命令 | `uv sync` / `pip install -r ...` | `npm install` / `pnpm i` |
| 跑脚本 | `uv run ...` / 激活后再 `python ...` | `npm run ...` / `npx ...` |

差异要记住一点：Node 的 `node_modules` 主要是包；Python 的 `.venv` 还带着**一份隔离的解释器入口**。

---

## 2. 必掌握：venv

这一节写细——后面 pip / uv / 测试章都默认你已有 `.venv`。

### 2.1 创建虚拟环境

#### 为什么需要 `python -m venv`？

直接 `pip install` 到系统 Python，等于在「全家共用厨房」里乱放调料。  
`venv` 在项目里建一个独立目录（惯例名 `.venv`），把解释器与包隔开。

#### 怎么写

在**项目根目录**执行：

```bash
python -m venv .venv
```

说明：

1. `-m venv`：用当前 Python 跑标准库模块 `venv`（比直接敲某个 `virtualenv` 命令更稳）
2. `.venv`：目录名可改，但生态与文档几乎都用这个；点开头表示「本机生成、常忽略提交」
3. 创建后会出现 `.venv/Scripts/`（Windows）或 `.venv/bin/`（macOS / Linux）

#### 跑一下（含预期）

```bash
python -m venv .venv
```

预期：命令几乎无输出；项目根下多出 `.venv/` 目录。

Windows PowerShell 可再确认：

```powershell
Test-Path .\.venv\Scripts\python.exe
```

预期输出：

```text
True
```

macOS / Linux：

```bash
ls .venv/bin/python
```

预期：能看到该路径存在（不报 `No such file`）。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 不在项目根创建 | 环境散落各处，以后找不到该激活哪个 |
| 用错了系统里的另一个 `python` | 建出来的环境版本不是你以为的 3.11+ |
| 把 `.venv/` 提交进 git | 仓库暴涨、跨平台路径失效；应进 `.gitignore` |

把忽略写进 `.gitignore`（若还没有）：

```gitignore
.venv/
```

#### 前端 / Node 对照

| Python | Node |
|--------|------|
| `python -m venv .venv` | 通常不「创建解释器」，直接 `npm install` 生成 `node_modules` |
| `.venv/` 勿提交 | `node_modules/` 勿提交 |
| 环境与项目绑定 | 依赖目录与项目绑定 |

### 2.2 激活与退出

#### 为什么要「激活」？

激活会改当前 shell 的 `PATH`，让你敲 `python` / `pip` 时优先走到 `.venv` 里那一套，而不是系统全局。

#### 怎么写

**Windows PowerShell：**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux：**

```bash
source .venv/bin/activate
```

退出（两平台相同）：

```bash
deactivate
```

#### 跑一下（含预期）

激活成功后，提示符前通常会出现 `(.venv)`：

```text
(.venv) PS C:\...\my-agent>
```

然后验证解释器前缀：

```bash
python -c "import sys; print(sys.prefix)"
```

预期：路径里包含项目下的 `.venv`（Windows 示例形态）：

```text
C:\Users\...\my-agent\.venv
```

而不是只有系统安装目录。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 开了新终端却忘了再激活 | `pip install` 可能装进系统 Python |
| PowerShell 报「无法加载，因为在此系统上禁止运行脚本」 | 执行策略限制；按公司/本机策略调整，或改用下一节的 `uv run`（不必激活也能跑） |
| 以为「建了 `.venv` 就自动生效」 | 不激活 / 不用 `uv run` 时，默认仍可能是系统 Python |
| 用「开始菜单里的 Python」双击脚本 | 完全绕开 venv |

Windows 若暂时不能改执行策略，可先用**绝对路径**验证（不依赖激活）：

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.prefix)"
```

#### 前端 / Node 对照

| Python | Node |
|--------|------|
| `Activate.ps1` / `source .../activate` | 一般不激活「解释器」，靠 `npm`/`npx` 找本地二进制 |
| `deactivate` | 关掉终端或退出 shell 即可 |
| 激活后 `python` 指向本地 | `npx eslint` 优先用本地 `node_modules/.bin` |

### 2.3 确认「当前到底是谁」

#### 为什么要反复确认？

装包与运行必须是**同一套**解释器。装进 A、跑在 B，是本章第一大坑。

#### 怎么写 / 跑一下

```bash
python -c "import sys; print(sys.executable); print(sys.prefix)"
python -m pip -V
```

预期（激活后）：

- `sys.executable` / `sys.prefix` 指向 `.venv`
- `pip -V` 一行里的路径也落在 `.venv` 下

若看到系统路径（如 `C:\Python312\...` 或 `/usr/bin/python`）而你以为在 venv 里——停下来先激活或改用 `uv run`。

#### 易错点

> 口诀：**先看 `sys.prefix`，再装包。**

---

## 3. 必掌握：pip（仍要会）

即使主用 `uv`，也要会读别人仓库里的 `pip` 命令，并理解「装到哪个解释器」。

### 3.1 安装与升级 pip 自身

#### 为什么优先 `python -m pip`？

直接敲 `pip` 可能指向另一个 Python。  
`python -m pip` = **用当前这个 `python` 自带的 pip**，歧义更少。

#### 怎么写 / 跑一下

先确保已激活 venv（或明确用 `.venv` 里的 python），然后：

```bash
python -m pip install -U pip
```

预期：输出里出现 `Successfully installed pip-...` 或提示已是最新。

再装一个轻量库：

```bash
python -m pip install httpx
```

预期：末尾类似：

```text
Successfully installed httpx-... ...
```

验证导入：

```bash
python -c "import httpx; print(httpx.__version__)"
```

预期：打印一个版本号字符串（例如 `0.27.x`），无 `ModuleNotFoundError`。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 未激活就 `pip install` | 装进系统或别的环境，当前项目 `import` 仍失败 |
| 只敲 `pip` 不敲 `python -m pip` | Windows 上尤其容易指错 |
| 用管理员权限往系统目录装 | 权限与污染全局；教学与项目开发都应停在 venv |

#### 前端 / Node 对照

| Python | Node |
|--------|------|
| `python -m pip install httpx` | `npm install httpx`（举例）/ `pnpm add lodash` |
| 装进当前环境的 site-packages | 装进当前项目的 `node_modules` |
| `import httpx` | `import ...` / `require(...)` |

### 3.2 `requirements.txt`（旧式但仍常见）

#### 为什么还要会？

很多教程、旧项目、Docker 示例仍用「冻结文件」。现代项目更推荐 `pyproject.toml` + 锁文件，但你必须能读、能装。

#### 怎么写

导出当前环境已装包（含精确版本）：

```bash
python -m pip freeze > requirements.txt
```

按文件安装：

```bash
python -m pip install -r requirements.txt
```

#### 跑一下（含预期）

```bash
python -m pip freeze > requirements.txt
```

打开 `requirements.txt`，预期类似：

```text
httpx==0.27.2
anyio==4.x.x
...
```

（具体版本随时间变化；重点是「包名==精确版本」。）

再开一个干净 venv 演练「复现安装」时：

```bash
python -m pip install -r requirements.txt
```

预期：按列表装齐；最后无报错。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 把开发工具和运行依赖糊在一个巨大 freeze 里且从不整理 | 文件难读；生产镜像可能多装一堆 |
| 只提交 `requirements.txt` 却在另一台机器用不同 Python 小版本 | 偶发编译型依赖失败 |
| 以为 `freeze` 等于现代锁文件 | freeze 是「当前环境快照」；锁文件还有解析图与工具语义（见 §7） |

#### 前端 / Node 对照

| Python | Node |
|--------|------|
| `pip freeze > requirements.txt` | 近似「把当前 `node_modules` 版本写死」——Node 更常见的是锁文件自动维护 |
| `pip install -r requirements.txt` | `npm ci`（按锁文件干净装）更接近「可复现」 |

---

## 4. 必掌握：uv（推荐主用）

[uv](https://github.com/astral-sh/uv) 是更快的 Python 包管理器 / 环境工具。  
**本仓库约定：学习与练习可用 `uv`。** 安装方式以[官网文档](https://github.com/astral-sh/uv)为准（版本演进快，此处不写死安装脚本）。

### 4.1 两种用法：兼容 pip vs 项目管理

#### 为什么分两层？

1. **`uv pip ...`**：心智接近 pip，适合「已有 venv，只想快速装包」
2. **`uv add` / `uv sync` / `uv run`**：以 `pyproject.toml`（+ `uv.lock`）为中心，更像前端的 `pnpm`/`npm` 工作流

学习策略：

- 会 `venv + pip` 保底（读旧文档、救急）
- **新项目优先 `uv`**（速度与体验通常更好）

#### 怎么写（常用命令）

```bash
uv venv                 # 创建 .venv
uv pip install httpx    # 往当前环境装（pip 兼容层）

# 更完整的项目管理：
uv init                 # 初始化项目元数据（若还没有）
uv add httpx            # 写入 pyproject 依赖并安装
uv sync                 # 按声明与锁文件同步环境
uv run python -m app.main
```

#### 跑一下（含预期）

若项目已有 `pyproject.toml`：

```bash
uv sync
```

预期：创建/复用 `.venv`，安装依赖；若生成或更新了锁文件，会看到对 `uv.lock` 的写入提示。

不激活也能跑：

```bash
uv run python -c "import sys; print(sys.prefix)"
```

预期：`sys.prefix` 指向项目 `.venv`。

再跑业务入口（路径按你上一章骨架调整）：

```bash
uv run python -m app.main
```

预期：与「先激活再 `python -m app.main`」行为一致，但少一步激活。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 混用「系统 pip 装包」和「uv sync」 | 环境漂移，锁文件与真实安装不一致 |
| 装了全局工具却不用 `uv run` / 不激活 | 又跑回系统 Python |
| 把 `uv` 当成「可以跳过理解 venv」 | 出问题时你仍要会看 `sys.prefix` |
| 在未初始化项目里盲目 `uv add` | 先确认当前目录是否是你的项目根 |

#### 前端 / Node 对照

| uv / Python | Node 生态 |
|-------------|-----------|
| `uv add httpx` | `pnpm add httpx` / `npm install httpx` |
| `uv sync` | `pnpm install` / `npm ci`（按锁恢复） |
| `uv run pytest` | `pnpm exec pytest` 或 `npm run test` / `npx ...` |
| `uv.lock` | `pnpm-lock.yaml` / `package-lock.json` |
| `.venv` | `node_modules`（角色相近，机制不同） |

可以记：

> `uv run` ≈ 「用本项目环境执行」——有点像 `npx` / `pnpm exec`，但连 Python 解释器一起锁定在项目里。

---

## 5. 必掌握：`pyproject.toml`

`pyproject.toml` 是现代 Python 项目的「身份证 + 依赖声明 + 工具配置」汇合点。

### 5.1 最小可读模板

#### 为什么需要它？

它集中回答：

- 项目叫什么、要什么 Python
- **运行依赖**声明在哪里
- 测试 / 打包 / lint 等工具配置也能放一起

没有它时，依赖散落在口头约定、`requirements.txt`、README 里——协作成本高。

#### 怎么写

最小示意：

```toml
[project]
name = "my-agent"
version = "0.1.0"
description = "Learning agent project"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27",
]

[dependency-groups]
dev = [
  "pytest>=8.0",
  "ruff>=0.6",
]
```

字段怎么读：

| 字段 | 含义 |
|------|------|
| `name` / `version` | 项目标识（给打包与工具看） |
| `requires-python` | 允许的 Python 版本下限/范围 |
| `dependencies` | **运行依赖**（部署/运行时常需要） |
| `[dependency-groups] dev` | **开发依赖**（测试、lint；生产可不装） |

说明：不同工具对「开发依赖」字段写法略有差异——`[project.optional-dependencies]`、`[dependency-groups]` 等，以你用的工具文档为准。本路线示例偏向 uv 常见的 `dependency-groups`。

#### 跑一下（含预期）

用 uv 把声明同步进环境：

```bash
uv sync
```

预期：`.venv` 中可 `import httpx`；开发组是否默认装入取决于工具与命令参数——若你显式需要 dev 组，按 uv 文档使用包含 dev 的 sync（学习阶段 `uv add --dev ...` 后通常已写入并装好）。

检查声明是否被工具识别（示例）：

```bash
uv run python -c "import httpx; print('ok', httpx.__version__)"
```

预期：

```text
ok 0.27.x
```

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 把 API Key 写进 `pyproject.toml` | 密钥进仓库；**严禁**（见 §6） |
| 运行依赖与开发依赖不分 | 生产镜像臃肿；或同事装不全测不了 |
| 版本约束过宽又无锁文件 | 今天能装、明天解析到不兼容版本 |
| TOML 语法错（引号、逗号） | 工具直接解析失败 |

#### 前端 / Node 对照

| `pyproject.toml` | `package.json` |
|------------------|----------------|
| `[project] name/version` | `"name"` / `"version"` |
| `dependencies` | `"dependencies"` |
| `dependency-groups.dev` / optional | `"devDependencies"` |
| `requires-python` | `"engines.node"`（类似角色，严格程度因工具而异） |
| `[tool.ruff]` 等 | `"eslintConfig"` 或单独 `eslint.config.js` |

### 5.2 让 `import app` 稳定（测试章前置）

#### 为什么这一步必须提前做？

`tests/test_*.py` 里写 `from app.tools...` 时，Python 必须知道去哪找 `app` 包。  
常见正确做法：把项目做成可安装包（可编辑安装），或明确告诉 pytest 搜索路径。  
**不要**在每个测试文件里改 `sys.path`。

#### 怎么写

```toml
# pyproject.toml（示意，构建后端以你选的为准）
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

# 或者不装包，只给 pytest 路径：
[tool.pytest.ini_options]
pythonpath = ["."]
```

推荐学习路径：可编辑安装 + `uv sync`，这样任意工作目录都能 `import app`。

#### 跑一下（含预期）

```bash
uv sync
uv pip install -e .
# 或：pip install -e .

uv run pytest
```

预期：

- 可编辑安装成功（输出含 `Successfully installed ...` 或 uv 等价提示）
- `uv run python -c "import app; print(app.__file__)"` 能打印出项目内路径
- `uv run pytest` 能收集到测试（下一章细讲；此处先保证导入不炸）

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 测试里手动 `sys.path.insert(0, ...)` | 本地侥幸通过，CI/其他目录失败 |
| 包目录没有 `__init__.py`（按你布局需要时） | 导入行为怪异 |
| 只配置了 `pythonpath` 却从未在「非项目根」试过 | 误以为问题解决了 |

#### 前端 / Node 对照

| Python | Node |
|--------|------|
| `pip install -e .` / 包发现 | 本地 `npm link` 或 workspace 协议 |
| `pythonpath = ["."]` | 测试跑法里配置根目录 / 路径别名 |
| `from app.tools import x` | `import { x } from '../src/tools'` 或别名 `@/` |

下一章测试示例默认你已完成「可导入 `app`」这一步。

---

## 6. 必掌握：环境变量与密钥

Agent / 后端几乎都会碰到 API Key。规则只有一条核心：

> **密钥只存在于运行环境，不存在于仓库历史。**

### 6.1 分层原则

#### 为什么要分三层？

| 层 | 放什么 | 是否进 git |
|----|--------|------------|
| 代码仓库 | `.env.example`（变量名 + 假值/空值说明） | ✅ 提交 |
| 本机私密 | `.env`（真密钥） | ❌ 不提交 |
| 进程环境 | `APP_API_KEY=...`（OS / CI / 云平台注入） | 不适用 |

```text
代码仓库：.env.example（无秘密）
本机私密：.env（不提交）
进程环境：APP_API_KEY=...
```

#### 怎么写（示例文件）

`.env.example`（可提交）：

```dotenv
# 复制为 .env 后填写真实值；不要把 .env 提交进仓库
APP_API_KEY=
APP_BASE_URL=https://api.example.com
```

`.gitignore` 确保包含：

```gitignore
.env
.venv/
```

#### 跑一下（含预期）

确认 git 不会跟踪 `.env`（在项目根）：

```bash
git check-ignore -v .env
```

预期：有一行指出被某条 ignore 规则命中（若你已配置）。  
若无输出，说明**还没忽略**——立刻补上，再检查 `git status` 不应出现要提交的 `.env`。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 把真 Key 写进 `.env.example` | 等于公开密钥模板被污染 |
| 曾经提交过 `.env` 后又删除 | 历史里仍可能有密钥，需按平台做轮换 |
| 密钥写进 `pyproject.toml` / 源码常量 | 审查与日志一搜一个准 |

### 6.2 在代码里读取

#### 为什么用 `os.getenv`？

配置与密钥属于**部署环境**，不是业务逻辑常量。代码只声明「我需要这个名字的变量」。

#### 怎么写

```python
import os

api_key = os.getenv("APP_API_KEY")
if not api_key:
    raise RuntimeError("APP_API_KEY is required")
```

本地临时注入（Windows PowerShell）：

```powershell
$env:APP_API_KEY = "sk-xxx"   # 仅本机演示；勿提交、勿截图乱贴
python -c "import os; print(os.getenv('APP_API_KEY')[:4] + '***')"
```

macOS / Linux：

```bash
export APP_API_KEY="sk-xxx"
python -c "import os; print(os.getenv('APP_API_KEY')[:4] + '***')"
```

开发期也可用 `.env` + 库（如 `python-dotenv`）在启动时加载——**生产环境通常由平台直接注入环境变量**，不要假设服务器上有一份你提交的 `.env`。

#### 跑一下（含预期）

把读取逻辑放进脚本（与练习 B4 同思路），例如 `b4_env.py`：

```python
import os

api_key = os.getenv("APP_API_KEY")
if not api_key:
    raise RuntimeError("APP_API_KEY is required")
print(api_key[:4] + "***")
```

**缺失时**（PowerShell 先清掉再跑）：

```powershell
Remove-Item Env:APP_API_KEY -ErrorAction SilentlyContinue
uv run python b4_env.py
```

预期：进程以非零退出，并看到类似：

```text
RuntimeError: APP_API_KEY is required
```

**已设置时：**

```powershell
$env:APP_API_KEY = "sk-xxx"
uv run python b4_env.py
```

预期只打印脱敏前缀，例如：

```text
sk-x***
```

而不是完整 Key。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 默认值写死真 Key：`os.getenv("APP_API_KEY", "sk-live-...")` | 假「有默认」把密钥编进代码 |
| 日志 / 异常里打印完整 Key | 密钥进日志系统 |
| 在聊天、截图、PR 描述里贴 Key | 泄露面扩大；泄露后应轮换 |
| 以为「私有仓库就能写死密钥」 | 权限会变；历史会克隆；自动化会扫 |

#### 前端 / Node 对照

| Python | Node / 前端 |
|--------|-------------|
| `os.getenv("APP_API_KEY")` | `process.env.APP_API_KEY` |
| `.env` + dotenv（开发） | `dotenv` / Vite 等对 `VITE_` 前缀的约定 |
| 服务端持有密钥 | **浏览器前端不要放真正的私密 Key**（会进打包产物） |
| CI 注入 secrets | GitHub Actions `secrets.*` 等同理 |

前端特别提醒：若 Key 只能给后端用，就放在 Python 服务环境变量里，不要指望「藏在前端代码里没人看见」。

### 6.3 别做的事（清单）

- 把 Key 写进源码、截图、聊天记录乱贴
- 把 `.env` 提交到 git
- 在日志里打印完整 Key
- 把密钥写进 `pyproject.toml`、Docker 镜像层明文、测试快照

---

## 7. 建议掌握：锁文件与格式化 / 静态检查

### 7.1 锁文件

#### 为什么需要锁文件？

`pyproject.toml` 里常见 `httpx>=0.27`——这是**允许范围**。  
锁文件（如 `uv.lock`、`poetry.lock`）记录**精确版本图**（含传递依赖），保证：

- 你、同事、CI 装到同一套版本
- 「上个月能跑、这个月解析到坏版本」的概率下降

应用项目建议**提交锁文件**（库项目是否锁、如何锁，策略另说；先建立地图即可）。

#### 怎么写 / 跑一下

以 uv 为例：

```bash
uv lock          # 根据 pyproject 生成/更新 uv.lock
uv sync          # 按锁文件安装到 .venv
```

预期：

- 仓库中出现（或更新）`uv.lock`
- 另一台机器 `uv sync` 后，关键包版本与你本机一致

若你暂时用 pip 路线，至少保留一份可复现的冻结文件（`requirements.txt`），并在笔记里写清局限（见 §3.2）。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 改了 `pyproject.toml` 却不更新锁 | CI 与本地各装各的 |
| 应用项目不提交锁文件 | 「我这能跑」再度上演 |
| 手工改锁文件 | 易损坏；应让工具生成 |

#### 前端 / Node 对照

| Python | Node |
|--------|------|
| `uv.lock` | `package-lock.json` / `pnpm-lock.yaml` |
| `uv sync` | `npm ci` / `pnpm install --frozen-lockfile` |
| 范围写在 `pyproject.toml` | 范围写在 `package.json`，锁文件钉死解析结果 |

### 7.2 ruff：lint + format

#### 为什么建议用 ruff？

一个工具覆盖大量 lint + format，速度快，现代 Python 很常见。  
它不替代测试，但能在「跑业务前」挡住一批低级问题与风格漂移。

#### 怎么写

```bash
uv add --dev ruff
uv run ruff check .
uv run ruff format .
```

也可在 `pyproject.toml` 里放工具配置（示意）：

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

（具体 rule 集随团队约定；先会跑起来。）

#### 跑一下（含预期）

```bash
uv run ruff check .
```

预期之一：

```text
All checks passed!
```

或列出文件与规则代号（如 `F401` 未使用导入）。按提示改完再跑，直到通过。

格式化：

```bash
uv run ruff format .
```

预期：输出类似 `X files reformatted` 或 `X files left unchanged`。

#### 易错点

| 错法 | 会发生什么 |
|------|------------|
| 把 ruff 放进运行依赖 | 生产环境多装工具链 |
| 本地不跑、只靠 CI 骂 | 反馈环太长 |
| 与旧项目的 black/isort/flake8 混用且配置冲突 | 格式来回打；选一套并写进约定 |

#### 前端 / Node 对照

| Python | 前端 |
|--------|------|
| `ruff check` | `eslint` |
| `ruff format` | `prettier`（或 eslint 格式化规则） |
| `uv run ruff ...` | `pnpm exec eslint .` / `npm run lint` |

---

## 8. 了解即可：多环境发布

#### 为什么会有多环境？

`dev` / `staging` / `prod` 往往有：

- 不同配置（URL、日志级别、特性开关）
- 不同密钥（绝不复用生产 Key 到个人笔记本演示）
- 不同依赖可选组（例如生产不装测试工具）

#### 先掌握什么？

先保证「本地可复现安装」（venv/uv + 声明 + 锁），再谈多环境。  
多环境的本质仍是：**同一份代码，不同环境变量与发布流水线**——不是复制三份仓库。

#### 前端 / Node 对照

与前端 `development` / `production` 构建模式类似：构建产物或运行配置变，源码仓库尽量保持一份。

---

## 9. 常见坑

1. 装包时装进了系统 Python，运行却在 venv（或反过来）——先查 `sys.prefix` / `pip -V`
2. 忘记激活环境——或改用 `uv run` 固定到项目环境
3. Windows 执行策略导致无法激活脚本——按公司策略调整，或用 `uv run` / `.venv\Scripts\python.exe`
4. 把密钥写进 `pyproject.toml`、源码、测试数据、README
5. 只改依赖声明不更新锁文件，导致 CI 与本地不一致
6. 用改 `sys.path` 代替可编辑安装 / `pythonpath` 配置
7. 把 `.venv/` 或 `.env` 提交进 git

---

## 10. 练习指引

[`exercises/03-engineering/02-deps-venv.md`](../../exercises/03-engineering/02-deps-venv.md)

建议顺序：B1 建 venv → B2 装依赖 → B3 写 `pyproject.toml` → B4 环境变量；有余力再做锁文件与 ruff。

---

## 11. 小结与下一站

### 你现在应该掌握的心智模型

```text
隔离：.venv（每项目一套）
声明：pyproject.toml（要什么）
锁定：uv.lock 等（精确是什么）
执行：激活 或 uv run（用对解释器）
秘密：环境变量 / .env（不进仓库）
质量：ruff check/format（提交前先扫一眼）
```

### 自检

- [ ] 能创建 venv 并确认 `sys.prefix`
- [ ] 能读/写最小 `pyproject.toml` 依赖
- [ ] 知道密钥如何通过环境变量注入，且 `.env` 不进 git
- [ ] （建议）能解释锁文件与 `ruff check` / `ruff format` 解决什么问题

### 下一章

[`03-testing.md`](./03-testing.md) —— pytest：让重构与加功能不再靠「人肉点一点」。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[项目结构](./01-project-structure.md)
- 下一章：[测试（pytest）](./03-testing.md)
