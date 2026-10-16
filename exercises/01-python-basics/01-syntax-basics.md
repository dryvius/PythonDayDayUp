# 练习：语法与数据结构

> 对应文档：[`docs/01-python-basics/01-syntax-basics.md`](../../docs/01-python-basics/01-syntax-basics.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

1. 先读完文档「必掌握」再做题；「建议掌握」做进阶题时用得到。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议把代码放在：

```text
playground/01-python-basics/01-syntax-basics/
```

每题一个 `.py` 文件亦可，例如 `ex1_types.py`、`ex2_containers.py`。

4. 先自己做完，再看文末「提示与参考思路」。不要一上来对答案。

---

## 基础题（必做）

### B1. 变量、类型与真假值

给定：

```python
values = [0, 1, "", "hello", None, [], [1], {}, {"a": 1}, False, True]
```

请编写程序，输出每一项的：

1. 原始值的 `repr`
2. `type(...).__name__`
3. 在 `if` 意义下是真还是假（打印 `truthy` / `falsy`）

**验收**：能正确标出所有 falsy 项（应包含 `0`、`""`、`None`、`[]`、`{}`、`False`）。

---

### B2. 四大容器实操

有如下原始数据：

```python
raw_tools = ["search", "calc", "search", "browse", "calc", "code_exec"]
```

完成：

1. 用 `set` 得到去重后的工具名集合 `unique_tools`
2. 再转回**按字母排序**的 `list`，赋给 `sorted_tools`
3. 建一个 `dict`：`tool_enabled`，每个工具默认 `True`；把 `"code_exec"` 设为 `False`
4. 用 tuple 保存「当前允许调用的工具名列表」快照：`enabled_snapshot`  
   （只包含 enabled 为 True 的名字，顺序与 `sorted_tools` 一致）

最后打印这四个变量。

**验收**：

- `unique_tools` 长度为 4
- `tool_enabled["code_exec"] is False`
- `enabled_snapshot` 是 `tuple`，且不含 `"code_exec"`

---

### B3. 控制流：消息清洗

给定消息历史：

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

规则：

1. 丢掉 `content` 为 `None`、空字符串、或只有空白的消息
2. 对保留消息的 `content` 做 `.strip()`
3. `system` 消息始终保留在最前（若有多条 system，只保留第一条）
4. 除 system 外，只保留**最近 3 条**消息

打印最终 `messages`。

**验收**：最终列表长度应为 `1（system） + 最多 3 条`；不应出现空 content。

---

### B4. 推导式 + 文件读写

给定：

```python
chunks = [
    {"id": 1, "text": "Agent 能调用工具", "score": 0.88},
    {"id": 2, "text": "普通聊天模型只生成文本", "score": 0.42},
    {"id": 3, "text": "RAG 先检索再生成", "score": 0.79},
    {"id": 4, "text": "向量库存储 embedding", "score": 0.65},
]
```

要求：

1. 用**列表推导式**选出 `score >= 0.6` 的 chunk，按分数降序
2. 再用推导式得到纯文本列表 `texts`
3. 写入 `playground/.../selected.json`（路径可自定），格式为 JSON 数组，`ensure_ascii=False`，`indent=2`
4. 再读回文件，断言读回后的第一条 `score` 仍是最高分

**验收**：文件存在且可被 `json` 正确解析；最高分 chunk 排第一。

---

## 进阶题（建议至少做 1 题）

### A1. 切片与上下文窗口模拟

```python
history = [f"msg-{i}" for i in range(1, 21)]  # msg-1 ... msg-20
```

实现函数（可先写成脚本步骤）：

1. 永远保留第一条（假装它是 system）
2. 其余只保留最后 `n` 条（`n=5`）
3. 返回新列表，不修改原 `history`

示例：结果应类似 `["msg-1", "msg-16", "msg-17", "msg-18", "msg-19", "msg-20"]`

**验收**：原列表长度仍为 20；新列表长度为 `1 + n`。

---

### A2. 统计工具调用

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

输出一个摘要 dict，例如：

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

综合本章所有必掌握点，写一个脚本：

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

- [ ] B1～B4 全部完成，运行无报错
- [ ] 能不看文档讲清：何时用 list/dict/set，以及 `is None` 和 `== None` 为何不推荐混用
- [ ] （建议）A1 或 A2 至少完成 1 题
- [ ] （可选）完成 C1

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

用 `for v in values:`，真假判断直接 `bool(v)` 或 `if v else ...`。注意 `bool([]) is False`。

</details>

<details>
<summary>B2 提示</summary>

- 去重：`set(raw_tools)`
- 排序：`sorted(...)` 得到 list
- 字典推导式很适合建 `tool_enabled`
- 过滤 enabled 后再 `tuple(...)`

</details>

<details>
<summary>B3 提示</summary>

先拆出 system 与非 system；非 system 做清洗后用切片 `[-3:]`；最后拼接。注意 `content` 可能是 `None`，不能先 `.strip()`。

</details>

<details>
<summary>B4 提示</summary>

```python
selected = sorted(
    [c for c in chunks if c["score"] >= 0.6],
    key=lambda c: c["score"],
    reverse=True,
)
```

写入用 `json.dumps(..., ensure_ascii=False, indent=2)` + `Path.write_text`。

</details>

<details>
<summary>A1 思路</summary>

`[history[0]] + history[1:][-n:]`，注意 `history[0]` 与后面片段不要重复（本题第一条不在最后 5 条里）。更稳妥：`[history[0]] + history[-n:]` 前要确认 system 不在尾部窗口中，或先分离再拼。

本题数据下：`[history[0]] + history[-5:]` 若 `msg-1` 不在最后 5 条，结果正确。

</details>

<details>
<summary>A2 思路</summary>

准备计数器变量，遍历 `trace`，按 `type` 分支更新。`by_name` 用 `dict`，不存在则初始化为 0 再累加。

</details>

<details>
<summary>C1 思路</summary>

去重时可用 `dict` 以 `text` 为 key，只在新 score 更高时覆盖；最后 `sorted(..., reverse=True)[:K]`。文档第 11 节综合例子几乎就是标准答案骨架。

</details>
