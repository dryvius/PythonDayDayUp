# 练习：语法与数据结构

> 对应文档：[`docs/01-python-basics/01-syntax-basics.md`](../../docs/01-python-basics/01-syntax-basics.md)  
> 状态：`已完成出题`  
> 建议用时：70～100 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」再做题；「建议掌握」做进阶题时用得到。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. **热身题建议先做**：把变量、真假值、list/dict/set、切片、推导式踩一遍；做完再上基础题会顺很多。
4. 建议代码目录：

```text
playground/01-python-basics/01-syntax-basics/
```

每题一个 `.py` 文件亦可，例如 `w1_types.py`、`b3_clean.py`。

5. 先自己做完，再看文末「提示与参考答案」。计算与清洗结果请用变量 / `return` 保存，不要只靠 `print` 交差。

---

## 热身题（建议先做）

> 每题控制在几分钟内。不必写成大项目；在 playground 里逐题跑通即可。

### W1. 变量与 `type`

**给定**：几个字面量。

**要求**：分别赋值 `n = 42`、`s = "Agent"`、`flag = True`，打印各自的 `type(...).__name__`。

**期望输出 / 验收**：

```python
assert type(n).__name__ == "int"
assert type(s).__name__ == "str"
assert type(flag).__name__ == "bool"
```

---

### W2. 真假值速查

**给定**：

```python
samples = [0, 1, "", "x", None, [], [0], {}, {"a": 1}]
```

**要求**：用循环标出每一项在 `if` 意义下是 `truthy` 还是 `falsy`（打印即可）。

**验收**：能正确指出 falsy 为 `0`、`""`、`None`、`[]`、`{}`（本题不含 `False`，后面 B1 会补全）。

---

### W3. list 追加与切片

**给定**：`roles = ["system", "user", "assistant"]`。

**要求**：

1. `append("tool")` 后长度为 4
2. 用切片取出「除第一条外」的列表赋给 `rest`

**验收**：

```python
assert roles == ["system", "user", "assistant", "tool"]
assert rest == ["user", "assistant", "tool"]
```

---

### W4. dict 读写

**给定**：空字典 `msg: dict = {}`。

**要求**：写入 `"role": "user"`、`"content": "hi"`；再读出 `content`。

**验收**：

```python
assert msg["role"] == "user"
assert msg.get("name") is None  # 缺键用 get 更安全
```

---

### W5. set 去重

**给定**：`names = ["search", "calc", "search", "browse"]`。

**要求**：得到去重后的集合，再转成按字母排序的 list。

**验收**：

```python
assert sorted(set(names)) == ["browse", "calc", "search"]
```

---

### W6. 列表推导式过滤

**给定**：`scores = [0.2, 0.7, 0.55, 0.9, 0.4]`。

**要求**：用推导式留下 `>= 0.5` 的分数。

**验收**：

```python
kept = [s for s in scores if s >= 0.5]
assert kept == [0.7, 0.55, 0.9]
```

---

## 基础题（必做）

### B1. 变量、类型与真假值

**给定**：

```python
values = [0, 1, "", "hello", None, [], [1], {}, {"a": 1}, False, True]
```

**要求**：编写程序，输出每一项的：

1. 原始值的 `repr`
2. `type(...).__name__`
3. 在 `if` 意义下是真还是假（打印 `truthy` / `falsy`）

**期望输出 / 验收**：能正确标出所有 falsy 项（应包含 `0`、`""`、`None`、`[]`、`{}`、`False`）。

---

### B2. 四大容器实操（贴近 Agent 工具名）

**给定**：

```python
raw_tools = ["search", "calc", "search", "browse", "calc", "code_exec"]
```

**要求**：

1. 用 `set` 得到去重后的工具名集合 `unique_tools`
2. 再转回**按字母排序**的 `list`，赋给 `sorted_tools`
3. 建一个 `dict`：`tool_enabled`，每个工具默认 `True`；把 `"code_exec"` 设为 `False`
4. 用 tuple 保存「当前允许调用的工具名列表」快照：`enabled_snapshot`  
   （只包含 enabled 为 True 的名字，顺序与 `sorted_tools` 一致）

最后打印这四个变量。

**验收**：

```python
assert len(unique_tools) == 4
assert tool_enabled["code_exec"] is False
assert isinstance(enabled_snapshot, tuple)
assert "code_exec" not in enabled_snapshot
```

---

### B3. 控制流：消息清洗

**给定**消息历史：

```python
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "  你好  "},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": "什么是 RAG？"},
    {"role": "assistant", "content": None},
    {"role": "user", "content": "再用一句话解释"},
]
```

**要求**：

1. 丢掉 `content` 为 `None`、空字符串、或只有空白的消息
2. 对保留消息的 `content` 做 `.strip()`
3. `system` 消息始终保留在最前（若有多条 system，只保留第一条）
4. 除 system 外，只保留**最近 3 条**消息

**验收**：最终列表长度应为 `1（system） + 最多 3 条`；不应出现空 content。

---

### B4. 推导式 + 文件读写

**给定**：

```python
chunks = [
    {"id": 1, "text": "Agent 能调用工具", "score": 0.88},
    {"id": 2, "text": "普通聊天模型只生成文本", "score": 0.42},
    {"id": 3, "text": "RAG 先检索再生成", "score": 0.79},
    {"id": 4, "text": "向量库存储 embedding", "score": 0.65},
]
```

**要求**：

1. 用**列表推导式**选出 `score >= 0.6` 的 chunk，按分数降序
2. 再用推导式得到纯文本列表 `texts`
3. 写入 `selected.json`（路径可自定，建议放在本章 playground），格式为 JSON 数组，`ensure_ascii=False`，`indent=2`
4. 再读回文件，断言读回后的第一条 `score` 仍是最高分

**验收**：文件存在且可被 `json` 正确解析；最高分 chunk 排第一。

---

## 进阶题（建议至少做 1 题）

### A1. 切片与上下文窗口模拟

**给定**：

```python
history = [f"msg-{i}" for i in range(1, 21)]  # msg-1 ... msg-20
```

**要求**：实现函数（可先写成脚本步骤）：

1. 永远保留第一条（假装它是 system）
2. 其余只保留最后 `n` 条（`n=5`）
3. 返回新列表，不修改原 `history`

示例：结果应类似 `["msg-1", "msg-16", "msg-17", "msg-18", "msg-19", "msg-20"]`

**验收**：原列表长度仍为 20；新列表长度为 `1 + n`。

---

### A2. 统计工具调用（trace 摘要）

**给定**：

```python
trace = [
    {"type": "thought", "content": "先搜索"},
    {"type": "tool_call", "name": "search"},
    {"type": "tool_result", "name": "search", "ok": True},
    {"type": "tool_call", "name": "browse"},
    {"type": "tool_result", "name": "browse", "ok": False},
    {"type": "tool_call", "name": "search"},
    {"type": "tool_result", "name": "search", "ok": True},
    {"type": "final", "content": "完成"},
]
```

**要求**：输出一个摘要 dict，例如：

```python
{
    "tool_calls": 3,
    "success": 2,
    "failed": 1,
    "by_name": {"search": 2, "browse": 1},
}
```

规则：

- `tool_calls` 统计 `type == "tool_call"`
- `success` / `failed` 看 `tool_result.ok`
- `by_name` 统计各工具被 call 的次数

**验收**：数字与示例一致（若你扩展了字段，核心四个键必须正确）。

---

## 挑战题（可选）

### C1. 迷你「检索后处理」脚本

综合本章必掌握点，写一个脚本（贴近 RAG / Agent 检索链路）：

**输入**（可写死在代码里）：若干 chunk，字段含 `text` / `score` / `source`

**处理**：

1. strip 文本，过滤空文本
2. `score < 0.5` 丢弃
3. 按文本去重（保留分数更高的那条）
4. 排序取 Top-K（`K=3`）
5. 生成 `prompt` 字符串（把 Top-K 文本拼进去）
6. 把 Top-K 与 prompt 一起保存为 JSON 文件

**加分项**：

- 用 `argparse` 读 `K`（不会可先写死，下章后再改）
- 打印处理前后数量对比

**验收**：换一组数据再跑一遍，逻辑仍正确；文件可读回。

---

## 验收标准（本章通过线）

- [ ] （建议）热身题 W1～W6 先做完，建立手感
- [ ] **通过线**：B1～B4 全部完成，运行无报错
- [ ] 能不看文档讲清：何时用 list/dict/set，以及 `is None` 和 `== None` 为何不推荐混用
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1

---

## 提示与参考答案（先做题再看）

> 热身题答案偏短；基础题及以后每题先给**思路**，再给带详细注释的**参考实现**。答案不是唯一写法，能通过验收、意图清晰即可。

### W1 参考答案

```python
n = 42
s = "Agent"
flag = True

assert type(n).__name__ == "int"
assert type(s).__name__ == "str"
assert type(flag).__name__ == "bool"
print(type(n).__name__, type(s).__name__, type(flag).__name__)
```

### W2 参考答案

```python
samples = [0, 1, "", "x", None, [], [0], {}, {"a": 1}]

for v in samples:
    kind = "truthy" if v else "falsy"
    print(repr(v), "->", kind)

# falsy: 0, "", None, [], {}
```

### W3 参考答案

```python
roles = ["system", "user", "assistant"]
roles.append("tool")
rest = roles[1:]

assert roles == ["system", "user", "assistant", "tool"]
assert rest == ["user", "assistant", "tool"]
```

### W4 参考答案

```python
msg: dict = {}
msg["role"] = "user"
msg["content"] = "hi"

assert msg["role"] == "user"
assert msg.get("name") is None
```

### W5 参考答案

```python
names = ["search", "calc", "search", "browse"]
assert sorted(set(names)) == ["browse", "calc", "search"]
```

### W6 参考答案

```python
scores = [0.2, 0.7, 0.55, 0.9, 0.4]
kept = [s for s in scores if s >= 0.5]
assert kept == [0.7, 0.55, 0.9]
```

### B1 思路 + 参考答案

**思路**

1. 遍历 `values`，对每一项打印 `repr`、类型名、真假标签。
2. 真假用 `bool(v)` 或 `if v else ...`；注意空容器与 `0` / `False` 都是 falsy。
3. 判断「是不是 None」业务里优先 `is None`，不要用 `== None` 当习惯。

**参考答案**

```python
values = [0, 1, "", "hello", None, [], [1], {}, {"a": 1}, False, True]

falsy_items: list = []
for v in values:
    kind = "truthy" if v else "falsy"
    print(f"{repr(v):20} {type(v).__name__:10} {kind}")
    if not v:
        falsy_items.append(v)

# 验收：这些值在 if 意义下都是假
expected_falsy = [0, "", None, [], {}, False]
assert falsy_items == expected_falsy
```

### B2 思路 + 参考答案

**思路**

1. 去重用 `set`；需要有序时再 `sorted(...)` 变回 list。
2. 字典推导式适合「每个名字 → 默认 True」。
3. 过滤 enabled 后再 `tuple(...)`，得到不可变快照（后续改 dict 不影响 snapshot）。

**参考答案**

```python
raw_tools = ["search", "calc", "search", "browse", "calc", "code_exec"]

# 1) 去重集合
unique_tools = set(raw_tools)
assert len(unique_tools) == 4

# 2) 按字母排序的 list
sorted_tools = sorted(unique_tools)
assert sorted_tools == ["browse", "calc", "code_exec", "search"]

# 3) 默认全部启用，再关掉 code_exec
tool_enabled = {name: True for name in sorted_tools}
tool_enabled["code_exec"] = False
assert tool_enabled["code_exec"] is False

# 4) 允许调用的工具名快照（顺序跟随 sorted_tools）
enabled_snapshot = tuple(
    name for name in sorted_tools if tool_enabled[name]
)
assert isinstance(enabled_snapshot, tuple)
assert "code_exec" not in enabled_snapshot
assert enabled_snapshot == ("browse", "calc", "search")

print(unique_tools)
print(sorted_tools)
print(tool_enabled)
print(enabled_snapshot)
```

### B3 思路 + 参考答案

**思路**

1. `content` 可能是 `None`，不能先 `.strip()`；先判 `None` / 非 str / 空白。
2. 拆出第一条有效 system，与其余非 system 消息。
3. 非 system 清洗后取 `[-3:]`，再与 system 拼接。

**参考答案**

```python
from typing import Any


def is_blank_content(content: Any) -> bool:
    """None / 非 str / 去空白后为空 → 视为无效内容。"""
    if content is None:
        return True
    if not isinstance(content, str):
        return True
    return content.strip() == ""


messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "  你好  "},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": "什么是 RAG？"},
    {"role": "assistant", "content": None},
    {"role": "user", "content": "再用一句话解释"},
]

cleaned: list[dict] = []
system_msg: dict | None = None

for m in messages:
    role = m.get("role")
    content = m.get("content")
    if is_blank_content(content):
        continue
    item = {"role": role, "content": str(content).strip()}
    if role == "system":
        # 只保留第一条 system
        if system_msg is None:
            system_msg = item
        continue
    cleaned.append(item)

# 除 system 外只留最近 3 条
recent = cleaned[-3:]
result = ([system_msg] if system_msg is not None else []) + recent

assert len(result) <= 4
assert result[0]["role"] == "system"
assert all(m["content"] for m in result)
# 本题数据下：system + 最近 3 条有效非 system
assert len(result) == 4
assert [m["content"] for m in result[1:]] == [
    "你好",
    "什么是 RAG？",
    "再用一句话解释",
]
print(result)
```

### B4 思路 + 参考答案

**思路**

1. 先过滤再 `sorted(..., reverse=True)`。
2. `texts` 用推导式从 selected 取 `"text"`。
3. 写入用 `json.dumps` + `Path.write_text`；读回用 `json.loads`。

**参考答案**

```python
import json
from pathlib import Path

chunks = [
    {"id": 1, "text": "Agent 能调用工具", "score": 0.88},
    {"id": 2, "text": "普通聊天模型只生成文本", "score": 0.42},
    {"id": 3, "text": "RAG 先检索再生成", "score": 0.79},
    {"id": 4, "text": "向量库存储 embedding", "score": 0.65},
]

selected = sorted(
    [c for c in chunks if c["score"] >= 0.6],
    key=lambda c: c["score"],
    reverse=True,
)
texts = [c["text"] for c in selected]

out = Path(__file__).resolve().parent / "selected.json"
out.write_text(
    json.dumps(selected, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

loaded = json.loads(out.read_text(encoding="utf-8"))
assert loaded[0]["score"] == max(c["score"] for c in selected)
assert loaded[0]["id"] == 1  # 0.88 最高
assert texts[0] == "Agent 能调用工具"
print("texts:", texts)
print("wrote:", out)
```

### A1 思路 + 参考答案

**思路**

1. 第一条当 system 永久保留；尾部窗口用 `history[-n:]`。
2. 若 system 不在尾部窗口中，直接 `[history[0]] + history[-n:]` 即可。
3. 必须返回新 list，不要 `history[:] = ...` 改原对象。

**参考答案**

```python
def window_history(history: list[str], n: int = 5) -> list[str]:
    """保留第一条 + 最后 n 条；不修改入参。"""
    if not history:
        return []
    if n < 0:
        raise ValueError("n must be >= 0")
    # 本题数据下 system 不在最后 n 条里，直接拼接即可
    return [history[0]] + history[-n:]


history = [f"msg-{i}" for i in range(1, 21)]
result = window_history(history, n=5)

assert len(history) == 20  # 原列表未变
assert result == [
    "msg-1",
    "msg-16",
    "msg-17",
    "msg-18",
    "msg-19",
    "msg-20",
]
assert len(result) == 1 + 5
assert history is not result
```

### A2 思路 + 参考答案

**思路**

1. 准备计数器与 `by_name` dict，遍历 `trace` 按 `type` 分支。
2. `tool_call` 累加总次数与按名次数；`tool_result` 看 `ok`。
3. 其它类型（thought / final）忽略即可。

**参考答案**

```python
trace = [
    {"type": "thought", "content": "先搜索"},
    {"type": "tool_call", "name": "search"},
    {"type": "tool_result", "name": "search", "ok": True},
    {"type": "tool_call", "name": "browse"},
    {"type": "tool_result", "name": "browse", "ok": False},
    {"type": "tool_call", "name": "search"},
    {"type": "tool_result", "name": "search", "ok": True},
    {"type": "final", "content": "完成"},
]


def summarize_trace(events: list[dict]) -> dict:
    tool_calls = 0
    success = 0
    failed = 0
    by_name: dict[str, int] = {}

    for ev in events:
        t = ev.get("type")
        if t == "tool_call":
            tool_calls += 1
            name = ev["name"]
            by_name[name] = by_name.get(name, 0) + 1
        elif t == "tool_result":
            if ev.get("ok"):
                success += 1
            else:
                failed += 1

    return {
        "tool_calls": tool_calls,
        "success": success,
        "failed": failed,
        "by_name": by_name,
    }


summary = summarize_trace(trace)
assert summary == {
    "tool_calls": 3,
    "success": 2,
    "failed": 1,
    "by_name": {"search": 2, "browse": 1},
}
print(summary)
```

### C1 思路 + 参考答案

**思路**

1. 清洗 → 阈值过滤 → 按 text 去重（dict 以 text 为 key，更高分覆盖）。
2. 按 score 降序取 Top-K，再拼 prompt。
3. 一次写入 JSON，便于 Agent / RAG 调试时复查中间结果。

**参考答案**

```python
import json
from pathlib import Path

raw_chunks = [
    {"text": "  Agent 能调用工具  ", "score": 0.88, "source": "a.md"},
    {"text": "噪音", "score": 0.3, "source": "b.md"},
    {"text": "RAG 先检索再生成", "score": 0.79, "source": "c.md"},
    {"text": "Agent 能调用工具", "score": 0.70, "source": "d.md"},  # 同文更低分
    {"text": "向量库存储 embedding", "score": 0.65, "source": "e.md"},
    {"text": "   ", "score": 0.99, "source": "f.md"},
    {"text": "工具结果要校验", "score": 0.91, "source": "g.md"},
]

K = 3
before = len(raw_chunks)

# 1) strip + 过滤空文本；2) 分数阈值
cleaned: list[dict] = []
for c in raw_chunks:
    text = (c.get("text") or "").strip()
    if not text:
        continue
    score = float(c["score"])
    if score < 0.5:
        continue
    cleaned.append({"text": text, "score": score, "source": c.get("source", "")})

# 3) 按文本去重：保留更高分
best: dict[str, dict] = {}
for c in cleaned:
    prev = best.get(c["text"])
    if prev is None or c["score"] > prev["score"]:
        best[c["text"]] = c

# 4) Top-K
top = sorted(best.values(), key=lambda x: x["score"], reverse=True)[:K]

# 5) 拼 prompt（模拟塞进上下文）
lines = [f"[{i+1}] {c['text']}" for i, c in enumerate(top)]
prompt = "根据以下资料回答：\n" + "\n".join(lines)

payload = {"top_k": top, "prompt": prompt, "stats": {"before": before, "after": len(top)}}
out = Path(__file__).resolve().parent / "rag_postprocess.json"
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

loaded = json.loads(out.read_text(encoding="utf-8"))
assert len(loaded["top_k"]) <= K
assert loaded["top_k"][0]["score"] >= loaded["top_k"][-1]["score"]
# 「Agent 能调用工具」应保留 0.88 那条，而不是 0.70
assert any(c["text"] == "Agent 能调用工具" and c["score"] == 0.88 for c in loaded["top_k"])
print("before/after:", before, len(top))
print("prompt:\n", prompt)
```
