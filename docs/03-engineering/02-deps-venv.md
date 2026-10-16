# 依赖与虚拟环境

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/03-engineering/02-deps-venv.md`](../../exercises/03-engineering/02-deps-venv.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：把依赖隔离、声明、安装、锁定；并学会用环境变量管理密钥与配置。
- **建议工具**：尽早用 `uv`；同时理解 `venv` + `pip`（到处都能见到）。

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

全局乱装依赖的后果：

```text
项目 A 需要 requests==2.28
项目 B 需要 requests==2.32
同一台机器互相踩脚
```

虚拟环境 = **每个项目一套独立的 site-packages**。  
Agent 项目还会装 `httpx`、`openai`、向量库客户端等，没有隔离很快灾难。

---

## 2. 必掌握：venv

```bash
# 在项目根目录
python -m venv .venv
```

激活（Windows PowerShell）：

```powershell
.\.venv\Scripts\Activate.ps1
```

激活（macOS / Linux）：

```bash
source .venv/bin/activate
```

退出：`deactivate`

验证：

```bash
python -c "import sys; print(sys.prefix)"
```

应指向 `.venv`。把 `.venv/` 加入 `.gitignore`。

---

## 3. 必掌握：pip（仍要会）

```bash
python -m pip install -U pip
python -m pip install httpx
python -m pip freeze > requirements.txt    # 旧式导出
python -m pip install -r requirements.txt
```

注意：

- 优先 `python -m pip`，避免装到别的 Python
- 现代项目更推荐 `pyproject.toml`，`requirements.txt` 仍常见

---

## 4. 必掌握：uv（推荐主用）

[uv](https://github.com/astral-sh/uv) 是更快的 Python 包管理器/环境工具。

常见用法（安装方式以官网为准）：

```bash
uv venv                 # 创建 .venv
uv pip install httpx    # 往当前环境装
# 或更完整的项目管理：
uv init
uv add httpx
uv sync
uv run python -m app.main
```

学习策略：

- 会 `venv + pip` 保底
- 新项目优先尝试 `uv`（速度与体验通常更好）

---

## 5. 必掌握：`pyproject.toml`

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

（不同工具对「开发依赖」字段写法略有差异：`[project.optional-dependencies]`、`[dependency-groups]` 等，以你用的工具文档为准。）

它解决：

- 项目叫什么、要什么 Python
- 运行依赖声明在哪里
- 后续测试/打包/工具配置也能放一起

### 5.1 让 `import app` 稳定（测试章前置）

`tests/test_*.py` 里写 `from app.tools...` 时，需要把项目装成可导入包，或告诉 pytest 去哪找：

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

```bash
# 推荐：可编辑安装后，任意目录都能 import app
uv sync
uv pip install -e .
# 或：pip install -e .

uv run pytest
```

不要靠在测试文件里改 `sys.path`。下一章测试示例默认你已完成这一步。

---

## 6. 必掌握：环境变量与密钥

### 6.1 原则

```text
代码仓库：.env.example（无秘密）
本机私密：.env（不提交）
进程环境：APP_API_KEY=...
```

### 6.2 读取

```python
import os

api_key = os.getenv("APP_API_KEY")
if not api_key:
    raise RuntimeError("APP_API_KEY is required")
```

本地可用：

```powershell
$env:APP_API_KEY = "sk-xxx"
```

或 `.env` + 库（如 `python-dotenv`）在开发期加载——生产环境通常由平台注入环境变量。

### 6.3 别做的事

- 把 Key 写进源码、截图、聊天记录乱贴
- 把 `.env` 提交到 git
- 在日志里打印完整 Key

---

## 7. 建议掌握：锁文件与格式化/静态检查

### 7.1 锁文件

`uv.lock` / `poetry.lock` 等记录**精确版本图**，保证同事与 CI 安装一致。  
应用项目建议提交锁文件（库项目策略另说）。

### 7.2 ruff

```bash
uv add --dev ruff
uv run ruff check .
uv run ruff format .
```

一个工具覆盖大量 lint + format，现代 Python 很常见。

---

## 8. 了解即可：多环境发布

`dev` / `staging` / `prod` 不同配置、不同密钥、不同依赖可选组。  
先保证「本地可复现安装」，再谈多环境。

---

## 9. 常见坑

1. 装包时装进了系统 Python，运行却在 venv（或反过来）
2. 忘记激活环境
3. Windows 执行策略导致无法激活脚本（按公司策略调整，或用 `uv run`）
4. 把密钥写进 `pyproject.toml`

---

## 10. 练习指引

[`exercises/03-engineering/02-deps-venv.md`](../../exercises/03-engineering/02-deps-venv.md)

---

## 11. 小结与下一站

### 自检

- [ ] 能创建 venv 并确认 `sys.prefix`
- [ ] 能读/写最小 `pyproject.toml` 依赖
- [ ] 知道密钥如何通过环境变量注入

### 下一章

[`03-testing.md`](./03-testing.md) —— pytest：让重构与加功能不再靠「人肉点一点」。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[项目结构](./01-project-structure.md)
- 下一章：[测试（pytest）](./03-testing.md)
