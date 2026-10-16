# 练习：Agent Memory

> 对应文档：[`docs/11-agent-core/05-agent-memory.md`](../../docs/11-agent-core/05-agent-memory.md)  
> 状态：`已完成出题` · 建议用时：60～90 分钟

可先跑通参考实现：[`playground/11-agent-core/memory/`](../../playground/11-agent-core/memory/)

---

## 基础题（必做）

### B1. 对照表

工作记忆 / 会话短期 / 长期：内容、寿命、存储、风险各写一行。

### B2. SessionState

实现 dataclass + `add_message` + `last_n` + `scratch` 字段。

### B3. 拒写规则

实现或直接使用 `should_write_long_term`；覆盖：`rag` / 低置信度 / 非 pref|fact / 注入口吻。

### B4. MemoryStore

实现 `add` / `retrieve` / `format_for_prompt`（可基于 playground 改）；`add` 必须先过 B3。

---

## 进阶题（建议）

### A1. 污染单测

写 pytest：`source=fetch_url` 的「忽略指令…」不得出现在 `retrieve` 结果中。

### A2. Prompt 隔离模板

把长期记忆块与用户输入分区拼接（带 `UNTRUSTED` / `[pref]` 标签）。

---

## 挑战题（可选）

### C1. TTL + revoke

过期条目不返回；`revoke(id)` 后检索为空。

### C2. 读专题

浏览 [`docs/topics/memory-engineering.md`](../../docs/topics/memory-engineering.md)，用 5 句话说明「主线已够用、进阶何时上」。

---

## 验收标准

- [ ] B1～B4 完成  
- [ ] （建议）A1 绿  
- [ ] 本地能跑 `demo.py` 或自写等价脚本  
