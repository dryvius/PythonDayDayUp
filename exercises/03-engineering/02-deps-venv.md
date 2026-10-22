# 练习：依赖与虚拟环境

> 对应文档：[`docs/03-engineering/02-deps-venv.md`](../../docs/03-engineering/02-deps-venv.md)  
> 状态：`已完成出题`  
> 建议用时：45～75 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：venv、pip/uv、`pyproject.toml`、环境变量。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录（可承接上一章 `my-agent/`，或新建）：

```text
playground/03-engineering/02-deps-venv/
```

4. 命令以你本机 Python ≥ 3.11 为准；可用 `venv` + `pip`，有条件可用 `uv`。
5. 先自己做完，再看文末「提示与参考答案」。**切勿把真实 API Key 写进代码或提交进 git。**

---

## 热身题（建议先做）

### W1. 确认 Python 版本

**要求**：运行：

```bash
python --version
```

**验收**：版本 ≥ 3.11；把输出贴进 `w1_notes.md`。

---

### W2. 全局 vs 项目：一句话

**要求**：用一句话解释：为什么 Agent 项目不该把 `httpx` / `openai` 直接装进「系统 Python」。

**验收**：能点到「多项目互相踩版本」或「不可复现」。

---

### W3. `.gitignore` 里应有 `.venv/`

**要求**：若练习目录会进 git，确认（或补上）忽略规则：

```gitignore
.venv/
```

**验收**：规则存在；不会打算提交整个虚拟环境目录。

---

## 基础题（必做）

### B1. 创建并验证 venv

1. 在项目根创建 `.venv`：

```bash
python -m venv .venv
```

2. 激活后运行：

```bash
python -c "import sys; print(sys.prefix)"
```

Windows PowerShell 激活示例：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
source .venv/bin/activate
```

3. 把输出贴进 `b1_notes.md`，并写一句：为什么这条路径应落在项目内的 `.venv`。

**验收**：有笔记；`sys.prefix` 指向本项目 `.venv`；`.venv/` 已在忽略列表（若该目录会提交）。

---

### B2. 安装一个依赖并导入

在已激活的 venv 内安装 `httpx`，写 `b2_check.py`：

```python
import httpx

print(httpx.__version__)
```

**验收**：`python b2_check.py` 打印出版本号；未激活 venv 时你应能意识到「可能装错位置」（笔记一句即可）。

---

### B3. 最小 `pyproject.toml`

创建含以下字段的 `pyproject.toml`（可手写）：

- `[project]` 下的 `name`
- `requires-python`（例如 `>=3.11`）
- `dependencies`（至少包含 B2 安装的库，版本约束写 `>=` 即可）

**验收**：文件可被打开阅读；上述字段齐全。

---

### B4. 环境变量读取

写 `b4_env.py`：

1. 读取 `APP_API_KEY`
2. 缺失则抛 `RuntimeError`（信息里说明缺哪个变量）
3. 存在则**只打印前 4 位 + `***`**，绝不打印完整密钥

**验收**：两种路径都演示过（PowerShell / bash 临时设置环境变量即可）。

---

## 进阶题（建议至少做 1 题）

### A1. 导出 / 锁定

任选其一：

- `pip freeze > requirements.txt`
- 或 `uv lock` / `uv sync`（若已使用 uv）

在 `a1_notes.md` 说明：「锁文件 / 冻结文件」解决什么问题（可复现安装）。

**验收**：生成了冻结或锁文件；笔记能说清「同一组版本」。

---

### A2. 尝试 ruff（可选安装）

若装得动：

```bash
pip install ruff
ruff check .
```

对上一章 `app/` 或本目录跑一次，记录 1 个发现或「无问题」到 `a2_notes.md`。

**验收**：有命令输出摘录或结论一句。

---

## 挑战题（可选）

### C1. `.env.example` + 本地加载方案说明

写 `c1_notes.md`，写清：

1. 开发期如何加载（例如手动 `export` / IDE env / 可选 `python-dotenv`——选一种说明即可）
2. 生产期为何通常**不**靠「把 `.env` 提交进镜像/仓库」
3. 给出一份 `.env.example` 示例内容（空值）

**验收**：三问都有完整段落，不是一句话打发。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W3
- [ ] **通过线**：B1～B4 完成
- [ ] 能口述：venv 隔离、依赖要声明、密钥走环境变量
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

> 每题先给思路，再给可照做的命令 / 文件全文 / 书面参考作答。

### W1 参考答案

```text
# 示例输出（以你机器为准）
Python 3.12.x
```

写入 `w1_notes.md`：

```markdown
python --version → Python 3.12.x（≥ 3.11，符合课程约定）
```

### W2 参考答案

全局乱装时，项目 A 需要 `requests==2.28`、项目 B 需要 `2.32`，会互相覆盖；「我电脑能跑」也无法在 CI / 同事机器复现。虚拟环境给每个项目独立的 site-packages。

### W3 参考答案

```gitignore
.venv/
__pycache__/
.env
```

`.venv/` 体积大、含平台相关二进制，不应进 git；`.env` 含密钥，更不能进。

---

### B1 思路 + 参考答案

**思路**

1. `python -m venv .venv`：用当前解释器创建隔离环境。
2. 激活后再看 `sys.prefix`，应指向项目内 `.venv`。
3. Windows / Unix 激活脚本路径不同，但验收标准相同。

**命令（Windows PowerShell）**

```powershell
cd playground/03-engineering/02-deps-venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.prefix)"
```

**命令（macOS / Linux）**

```bash
cd playground/03-engineering/02-deps-venv
python -m venv .venv
source .venv/bin/activate
python -c "import sys; print(sys.prefix)"
```

**`b1_notes.md` 示例**

```markdown
# B1

激活后 sys.prefix：
C:\...\02-deps-venv\.venv

结论：当前 python 已指向项目内虚拟环境，而不是系统全局前缀。
已在 .gitignore 加入 `.venv/`。
```

---

### B2 思路 + 参考答案

**思路**

先激活 venv，再 `pip install`，避免装到系统 Python。

**命令**

```bash
pip install "httpx>=0.27"
python b2_check.py
```

**`b2_check.py` 全文**

```python
import httpx

print(httpx.__version__)
```

**自检**

```python
import sys
import httpx

assert "site-packages" in httpx.__file__.replace("\\", "/")
print("ok", httpx.__version__, "python=", sys.executable)
```

---

### B3 思路 + 参考答案

**思路**

`pyproject.toml` 是现代 Python 项目的依赖声明入口；练习手写最小字段即可，不必上完整 build 后端也能先学会读/写。

**参考：`pyproject.toml`**

```toml
[project]
name = "deps-venv-lab"
version = "0.1.0"
description = "PythonDayDayUp deps/venv exercise"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "ruff>=0.6",
]
```

说明：`optional-dependencies.dev` 为建议项；B3 验收只要 `name` / `requires-python` / `dependencies` 齐全。

---

### B4 思路 + 参考答案

**思路**

1. 缺密钥要尽快失败（`RuntimeError`），避免带着空 Key 打到半路才崩。
2. 日志/打印必须脱敏：只露前缀。

**参考：`b4_env.py`**

```python
import os


def require_api_key() -> str:
    key = os.getenv("APP_API_KEY")
    if not key:
        raise RuntimeError("missing env var: APP_API_KEY")
    return key


def mask_secret(secret: str, visible: int = 4) -> str:
    if len(secret) <= visible:
        return "***"
    return secret[:visible] + "***"


def main() -> None:
    key = require_api_key()
    print("APP_API_KEY =", mask_secret(key))


if __name__ == "__main__":
    main()
```

**演示：缺失**

```powershell
# 确保未设置
Remove-Item Env:APP_API_KEY -ErrorAction SilentlyContinue
python b4_env.py
# 期望：RuntimeError: missing env var: APP_API_KEY
```

**演示：存在**

```powershell
$env:APP_API_KEY = "sk-demo-1234567890"
python b4_env.py
# 期望：APP_API_KEY = sk-d***
```

```bash
# bash
unset APP_API_KEY
python b4_env.py   # 应失败

export APP_API_KEY='sk-demo-1234567890'
python b4_env.py   # APP_API_KEY = sk-d***
```

**断言版自检**

```python
import os
from b4_env import mask_secret, require_api_key

assert mask_secret("sk-abcdefgh") == "sk-a***"

os.environ.pop("APP_API_KEY", None)
try:
    require_api_key()
    raise AssertionError("should have raised")
except RuntimeError as exc:
    assert "APP_API_KEY" in str(exc)

os.environ["APP_API_KEY"] = "sk-test-key"
assert require_api_key() == "sk-test-key"
```

---

### A1 思路 + 参考答案

**思路**

声明（`pyproject.toml`）描述「允许的范围」；锁/冻结固定「实际安装的精确版本」，避免「今天能装、明天解析到另一套」。

**pip 路线**

```bash
pip freeze > requirements.txt
```

**`a1_notes.md` 参考作答**

```markdown
# A1 锁文件 / 冻结文件解决什么？

1. **可复现**：同事与 CI 装到同一组精确版本，减少「我这边好好的」。
2. **排障**：线上行为异常时，能对照当时依赖树。
3. **与声明分工**：`pyproject.toml` 写意图（`httpx>=0.27`）；`requirements.txt` / `uv.lock` 写快照。

注意：冻结文件也会钉死传递依赖；升级时要有意识地重生成，而不是永远不更新。
```

**uv 路线（若使用）**

```bash
uv lock
uv sync
```

笔记同样强调：lock 让解析结果稳定。

---

### A2 思路 + 参考答案

**命令**

```bash
pip install ruff
ruff check .
```

**`a2_notes.md` 示例**

```markdown
# A2

命令：`ruff check app`（或 `.`）
结果：All checks passed!（或列出 1 条 F401 未使用导入并已顺手删掉）

结论：ruff 适合做「提交前快速静态检查」，与 pytest 互补。
```

---

### C1 思路 + 参考答案

**参考：`c1_notes.md`**

```markdown
# C1：`.env` 加载与生产边界

## 1. 开发期如何加载

常见三种（选一种坚持即可）：

1. **Shell 临时导出**：`export APP_API_KEY=...` / PowerShell `$env:APP_API_KEY=...`
2. **IDE Run Configuration**：在启动配置里填 Env
3. **可选库**：`python-dotenv` 在入口 `load_dotenv()` 读取本地 `.env`（仅开发便利；不要把库当成密钥管理系统）

无论哪种，代码里只 `os.getenv("APP_API_KEY")`，不写死密钥字符串。

## 2. 生产期为何不靠提交 `.env`

1. **泄露风险**：仓库、镜像层、构建日志都可能把密钥带走
2. **环境差异**：staging / prod 密钥不同，应在部署平台注入（K8s Secret、云厂商环境变量、CI secret）
3. **轮换**：密钥轮换时不应发版改文件，而应改运行时配置

生产镜像里可以有 `.env.example` 作文档，但真实密钥由编排系统注入进程环境。

## 3. `.env.example` 示例

```text
APP_API_KEY=
APP_MAX_STEPS=8
APP_ENV=dev
```

复制为 `.env` 后填写；确保 `.env` 在 `.gitignore`。
```

---

### 本章速查

| 主题 | 记住 |
|------|------|
| 隔离 | 每项目一个 `.venv` |
| 声明 | `pyproject.toml` 写 dependencies |
| 锁定 | freeze / lock 解决可复现 |
| 密钥 | 环境变量 + 脱敏打印；勿提交 `.env` |
