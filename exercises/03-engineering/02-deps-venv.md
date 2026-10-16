# 练习：依赖与虚拟环境

> 对应文档：[`docs/03-engineering/02-deps-venv.md`](../../docs/03-engineering/02-deps-venv.md)  
> 状态：`已完成出题`  
> 建议用时：45～75 分钟

## 练习说明

建议在 `playground/03-engineering/02-deps-venv/` 或承接上一章 `my-agent/` 进行。  
命令以你本机 Python 为准；可用 venv+pip，有条件可用 uv。

---

## 基础题（必做）

### B1. 创建并验证 venv

1. 创建 `.venv`
2. 激活后运行：`python -c "import sys; print(sys.prefix)"`
3. 把输出贴进 `b1_notes.md`（证明指向项目内虚拟环境）

**验收**：有笔记；`.venv` 已在 `.gitignore`（若该练习目录会提交）。

### B2. 安装一个依赖并导入

安装 `httpx`（或任意轻量库），写 `b2_check.py`：

```python
import httpx
print(httpx.__version__)
```

**验收**：在 venv 内可运行。

### B3. 最小 `pyproject.toml`

创建含 `name` / `requires-python` / `dependencies` 的文件（可手写）。  
依赖至少包含你在 B2 安装的库（版本约束写 `>=` 即可）。

**验收**：文件可被打开阅读；字段齐全。

### B4. 环境变量读取

写 `b4_env.py`：读取 `APP_API_KEY`，缺失则抛 `RuntimeError`；存在则只打印前 4 位 + `***`。

**验收**：两种路径都演示过（PowerShell 临时设置环境变量即可）。

---

## 进阶题（建议）

### A1. 导出/锁定

任选：`pip freeze > requirements.txt` 或 uv lock/sync。  
在笔记说明「锁文件/冻结文件」解决什么问题。

### A2. 尝试 ruff（可选安装）

对上一章 `app/` 跑一次 `ruff check`（装得动的话），记录 1 个发现或「无问题」。

---

## 挑战题（可选）

### C1. `.env.example` + 本地加载方案说明

写清：开发期如何加载、生产期为何通常不靠提交 `.env`。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1
