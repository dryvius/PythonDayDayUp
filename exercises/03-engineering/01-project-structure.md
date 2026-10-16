# 练习：项目结构

> 对应文档：[`docs/03-engineering/01-project-structure.md`](../../docs/03-engineering/01-project-structure.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

在 `playground/03-engineering/01-project-structure/my-agent/` 下搭真实目录并跑通。

---

## 基础题（必做）

### B1. 搭骨架

创建：

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
│   └── models/
│       ├── __init__.py
│       └── message.py
├── tests/
│   └── test_smoke.py
├── .env.example
└── README.md
```

**验收**：目录存在；README 用 5 行说明如何运行。

### B2. 实现最小可运行链路

1. `models/message.py`：`create_message(role, content) -> dict`
2. `tools/search.py`：`search(query: str, top_k: int = 3) -> list[str]`
3. `services/llm.py`：`EchoLLM.complete(prompt: str) -> str`
4. `config.py`：`Settings.from_env()`（至少 `max_steps`）
5. `main.py`：组装并打印一次结果

**验收**：在 `my-agent/` 根执行 `python -m app.main` 成功。

### B3. 包边界检查（书面）

在 `b3_notes.md` 画出依赖方向（谁 import 谁），并指出你刻意避免的反向依赖。

**验收**：有笔记；`tools` 不 import `main`。

### B4. `.env.example`

写入至少：`APP_MAX_STEPS=`、`APP_API_KEY=`（空值），并在 README 说明不要提交真 `.env`。

**验收**：文件存在且无真实密钥。

---

## 进阶题（建议）

### A1. 增加 `agents/runner.py`

把「拼 prompt + 调 search + 调 llm」从 `main` 挪到 `AgentRunner`，`main` 只组装。

### A2. smoke test

`tests/test_smoke.py` 至少断言 `search("x")` 返回非空 list（下一章再系统学 pytest，这里先能 `pytest` 跑过更佳）。

---

## 挑战题（可选）

### C1. 按文档模板补全 `agents/` 空包与未来扩展注释

说明你准备把 memory / router 放哪，写在 README「扩展点」。

---

## 验收标准

- [ ] B1～B4 完成且 `python -m app.main` 可跑
- [ ] （建议）A1 或 A2
- [ ] （可选）C1
