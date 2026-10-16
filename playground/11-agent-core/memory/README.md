# Memory Store 最小可跑示例

对应文档：[`docs/11-agent-core/05-agent-memory.md`](../../../docs/11-agent-core/05-agent-memory.md)

## 跑起来

```bash
# 演示写入/拒写/检索
python playground/11-agent-core/memory/demo.py

# 单测（含污染 case；无 pytest 时用 run_tests.py）
python playground/11-agent-core/memory/run_tests.py
python -m pytest playground/11-agent-core/memory/test_store.py -q
```

## 文件

| 文件 | 作用 |
|------|------|
| `store.py` | `MemoryStore` + `should_write_long_term` |
| `demo.py` | 手工演示 |
| `test_store.py` | pytest，含污染拒写 case |
| `data/` | demo 落盘（可删） |
