# 练习：Logging

> 对应文档：[`docs/03-engineering/04-logging.md`](../../docs/03-engineering/04-logging.md)  
> 状态：`已完成出题`  
> 建议用时：45～75 分钟

## 练习说明

目录：`playground/03-engineering/04-logging/`

---

## 基础题（必做）

### B1. setup_logging

实现 `setup_logging(level=logging.INFO)`：配置 root 的 StreamHandler + Formatter。  
入口调用后 `logging.getLogger(__name__).info("hello")` 能看到时间与级别。

**验收**：控制台有格式化输出；重复调用 setup 不导致双份日志（做防护）。

### B2. 模块 logger

两个模块 `app/tools.py` 与 `app/agent.py` 各自 `getLogger(__name__)`，打不同事件。  
观察日志中的 `[name]` 是否不同。

**验收**：能区分来源模块。

### B3. exception 日志

写一个会抛错的函数，在 `except` 里用 `logger.exception(...)`。  
确认输出含 traceback。

**验收**：有堆栈信息。

### B4. 结构化字段风格

把一次假工具调用打成一行字段化日志，至少含：`run_id`、`tool`、`ok`、`latency_ms`。

**验收**：日志可读且字段齐全；不要打印假 API Key。

---

## 进阶题（建议）

### A1. 文件 handler

增加 `RotatingFileHandler` 或普通 `FileHandler`，同时输出到控制台与 `app.log`。

### A2. 级别过滤

演示：root 设 INFO 时 DEBUG 不可见；临时调到 DEBUG 可见。写进 `a2_notes.md`。

---

## 挑战题（可选）

### C1. `run_tool` 包装器

实现文档综合例子的 `run_tool`，成功/失败路径都有对应日志，并写 2 个手工演示。

---

## 模块 03 通关自检

- [ ] 能搭清爽的 `app/` 结构
- [ ] 会 venv/依赖声明/环境变量
- [ ] 会为纯逻辑写 pytest
- [ ] 会配置 logging 并字段化记录 Agent 关键事件

全部完成后进入模块 04《计算机与服务端基础》。

---

## 验收标准

- [ ] B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1
