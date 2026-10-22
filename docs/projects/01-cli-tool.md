# Project 1：Python CLI 工具

> 状态：`已完成实战说明`  
> 建议时机：完成模块 01～03 后  
> 建议工时：6～12 小时  
> 推荐目录：`playground/projects/01-cli-tool/`  
> 运行环境：Python ≥ 3.11（见 [`../CONVENTIONS.md`](../CONVENTIONS.md)）

## 项目目标

做一个可安装、可测试的命令行工具：解析参数、读文件/目录、输出结构化结果，并带基础日志。

建议选题（三选一或自拟等价难度）：

1. **文档扫描器**：统计目录下 `.md`/`.py` 行数、空行、按扩展名汇总  
2. **消息历史截断器**：读 JSONL 对话，按策略截断后写出  
3. **简单待办 CLI**：本地 JSON 文件增删改查

下文以「文档扫描器」为主线描述；换选题时对照同一里程碑即可。

## 你将练习到的能力

| 模块 | 知识点 |
|------|--------|
| 01 | 函数、模块、包、`if __name__` |
| 02 | 异常、类型注解、可选：生成器扫大目录 |
| 03 | `pyproject.toml`、venv、pytest、logging、项目结构 |

工程实践：包布局、入口脚本、`.env` 不进仓库、测试与实现分离。

## 需求概述

### 功能

1. 子命令或参数：`scan <path> [--ext md,py] [--json]`  
2. 递归遍历目录，跳过 `.venv` / `__pycache__` / `.git`  
3. 输出：人类可读表，或 `--json` 结构化结果  
4. 路径不存在 / 无权限 → 非 0 退出码 + 清晰错误信息  

### 非功能

- Python ≥ 3.11  
- 核心逻辑可单测（不依赖真实巨大目录，可用 `tmp_path`）  
- 有 `README`：安装与示例命令  
- 日志：默认 WARNING，`-v` 升到 INFO  

## 建议目录

```text
playground/projects/01-cli-tool/
├── app/
│   ├── __init__.py
│   ├── __main__.py          # python -m app
│   ├── cli.py               # argparse / typer
│   ├── scanner.py           # 纯逻辑
│   └── logging_setup.py
├── tests/
│   └── test_scanner.py
├── pyproject.toml
├── README.md
└── .gitignore
```

## 起步建议（第一天）

1. 建目录 + `pyproject.toml`（包名 `app`，脚本入口可选）  
2. 先写 `scanner.scan_path(path) -> dict`，用 `pytest` + `tmp_path` 造 2～3 个文件跑绿  
3. 再挂 `cli.py` / `__main__.py`；最后才加 `-v` 与 `pip install -e .`  

必读章节（细则回文档，不在这里重讲）：

- [项目结构](../03-engineering/01-project-structure.md)  
- [测试](../03-engineering/03-testing.md)  
- [Logging](../03-engineering/04-logging.md)  

## 里程碑

- [ ] **M1**：`scanner.scan_path` 对临时目录返回正确计数；`pytest` 绿  
- [ ] **M2**：CLI 可跑；`--json`；错误路径退出码 ≠ 0  
- [ ] **M3**：`pyproject` 可 `pip install -e .`；`-v` 日志；README 三节（安装/用法/开发）  

## 验收标准

- [ ] 他人按 README 能在干净 venv 安装并跑通一条示例  
- [ ] 至少 3 个 pytest（正常扫描、空目录、缺失路径）  
- [ ] 业务逻辑不写在 `cli.py` 里堆成一团  
- [ ] 无密钥；无提交 `.venv`  

## 常见易错

| 坑 | 正确做法 |
|----|----------|
| 逻辑全塞在 `cli.py` | 纯函数进 `scanner.py`，CLI 只负责解析与退出码 |
| 测试扫真实家目录 | 用 `tmp_path` 造最小夹具 |
| 缺路径仍 `exit 0` | 约定：错误 → 非 0；成功 → 0 |
| 默认 INFO 刷屏 | 默认 WARNING，`-v` 再升 INFO |
| 跳过规则漏 `.venv` | 显式跳过列表，单测里造一个假 `.venv` |

## 延伸挑战

- 用 `rich` 表格扩展输出  
- 并行扫描大目录（`ProcessPoolExecutor`，注意模块 04 GIL 边界）  
- 打包发布到 TestPyPI（了解即可）  

## 导航

- 返回项目列表：[./README.md](./README.md)
- 相关文档：[模块 03 工程化](../03-engineering/README.md) · [语法基础](../01-python-basics/01-syntax-basics.md)
- 返回总览：[../../README.md](../../README.md)
