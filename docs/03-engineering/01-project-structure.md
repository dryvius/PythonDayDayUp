# 项目结构

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：2～4 小时  
> 对应练习：[`exercises/03-engineering/01-project-structure.md`](../../exercises/03-engineering/01-project-structure.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会用 Python 做项目」。
- **本章角色**：先把文件放对地方——包边界清晰、入口明确、配置可管。后面依赖、测试、日志都建立在这个骨架上。
- **前置**：模块与包（`01` 第三章）。

## 学习目标（学完应能做到）

1. 搭出适合 Agent/后端小项目的目录骨架（`app/` 或 `src/` 布局）。
2. 说清包边界：哪些是入口、哪些是库代码、哪些是测试。
3. 正确放置配置与入口（`main.py` / `__main__.py` / 环境变量）。
4. 知道何时从单文件演进到模块化，而不必一上来微服务。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | app/src 布局、包边界、配置与入口 | 能搭、能跑、能解释 |
| **建议掌握** | 单体到模块化演进 | 会拆分，不早拆 |
| **了解即可** | monorepo 多包 | 建立地图 |

---

## 1. 为什么要学

没有结构时，Agent 项目很容易变成：

```text
main.py（2000 行）
utils.py
test.py
new_test_final.py
```

有结构时：

```text
app/
  agents/   tools/   services/   models/
tests/
pyproject.toml
```

结构解决的是：**找得到、改得动、测得了、部署不慌**。

---

## 2. 必掌握：推荐布局（小中型 Agent 项目）

### 2.1 实用模板（本路线默认）

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
│   └── models/              # dataclass / schema
│       └── __init__.py
├── tests/
│   ├── __init__.py          # 可选
│   └── test_tools.py
├── .env.example
├── pyproject.toml
└── README.md
```

说明：

- **`app/`**：你的业务包（也可叫 `src/my_agent/`，见下）
- **`tests/`**：测试与业务分离
- **`pyproject.toml`**：项目元数据与依赖（下一章细讲）
- **`.env.example`**：告诉别人需要哪些环境变量（不要提交真密钥）

### 2.2 `app/` 布局 vs `src/` 布局

| 风格 | 例子 | 特点 |
|------|------|------|
| flat app | `app/` 直接在根下 | 简单，教程/小项目友好 |
| src layout | `src/my_agent/` | 更规范，减少「误导入仓库根目录脚本」 |

学习阶段用 `app/` 完全够；以后看开源项目看到 `src/` 不要慌，思想一样。

---

## 3. 必掌握：包边界

### 3.1 谁依赖谁（建议方向）

```text
main（组装）
  → agents（编排）
      → tools / services / models
tests → 任意公共模块（不要反向被业务依赖）
```

避免：

- `tools` 导入 `agents`（循环与层次混乱）
- 业务代码依赖 `tests`
- 到处 `from app.main import ...`

### 3.2 入口只做组装，不写业务细节

```python
# app/main.py
from app.config import Settings
from app.services.llm import EchoLLM
from app.tools.search import SearchTool
from app.agents.runner import AgentRunner


def main() -> None:
    settings = Settings.from_env()
    agent = AgentRunner(
        llm=EchoLLM(),
        tools=[SearchTool()],
        max_steps=settings.max_steps,
    )
    print(agent.run("what is RAG"))


if __name__ == "__main__":
    main()
```

---

## 4. 必掌握：配置与入口

### 4.1 配置放哪

推荐：

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

- **密钥走环境变量**，不写死在代码
- 提供 `.env.example`，真 `.env` 不进 git
- 配置集中读取，避免每个文件自己 `os.getenv`

### 4.2 怎么启动

```bash
# 在项目根目录
python -m app.main
# 或
python app/main.py   # 有时路径更脆，优先 -m
```

保证「当前工作目录 / 可导入路径」正确；依赖安装方式见下一章。

---

## 5. 建议掌握：从单文件演进

不要一上来过度设计。建议路径：

```text
1) 单文件原型跑通
2) 拆 tools / services
3) 加 config / tests
4) 再考虑多 agent 包、插件化
```

拆分信号：

- 单文件 > 300～400 行且多职责
- 测试无从下手
- 两人以上协作频繁冲突

---

## 6. 了解即可：monorepo 多包

一个仓库多个包（`packages/core`、`packages/web`）适合平台型团队。  
个人 Agent 学习项目不必上；见到即可。

---

## 7. 常见坑

1. 包名与第三方库撞名（`json.py`、`http.py`）
2. 在子目录里乱跑脚本导致 `ModuleNotFoundError`
3. 把虚拟环境、`__pycache__`、`.env` 提交进 git
4. 循环导入：用「依赖方向」和延迟导入救急，根本靠边界

---

## 8. 练习指引

[`exercises/03-engineering/01-project-structure.md`](../../exercises/03-engineering/01-project-structure.md)

建议目录：`playground/03-engineering/01-project-structure/`

---

## 9. 小结与下一站

### 自检

- [ ] 能画出 `app/agents|tools|services|models` 职责
- [ ] 入口只组装，配置集中
- [ ] 能用 `python -m` 跑起来

### 下一章

[`02-deps-venv.md`](./02-deps-venv.md) —— 虚拟环境、pip/uv、`pyproject.toml`、环境变量。

## 导航

- 返回模块：[README](./README.md)
- 上一模块：[类型系统](../02-advanced-python/07-typing-system.md)
- 下一章：[依赖与虚拟环境](./02-deps-venv.md)
