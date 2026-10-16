# 练习：装饰器

> 对应文档：[`docs/02-advanced-python/04-decorator.md`](../../docs/02-advanced-python/04-decorator.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/02-advanced-python/04-decorator/
```

4. 除题目明确要求外，装饰器请使用 `@functools.wraps`。

---

## 基础题（必做）

### B1. 无参装饰器：`logged`

实现 `@logged`：

- 调用前打印：`CALL <name> args=... kwargs=...`（可读即可，不必完美格式化）
- 调用后打印：`RET  <name> -> <result>`
- 正确返回原函数结果

用它装饰一个 `add(a, b)` 并调用验证。

**验收**：有前后日志；`add(2, 3) == 5`；`add.__name__ == "add"`。

---

### B2. 带参装饰器：`repeat`

实现：

```python
@repeat(n=3)
def ping():
    print("pong")
    return "ok"
```

要求：

1. 本体函数被调用 `n` 次
2. 返回**最后一次**的返回值
3. `n <= 0` 时抛 `ValueError`

**验收**：`ping()` 打印 3 次 `pong`，返回 `"ok"`。

---

### B3. `wraps` 对比实验

写两个装饰器：`plain`（不用 wraps）与 `nice`（用 wraps），都装饰同一函数：

```python
def create_message(role: str, content: str) -> dict:
    """创建消息。"""
    return {"role": role, "content": content}
```

打印对比：

- `__name__`
- `__doc__`

**验收**：能用输出说明 wraps 保留了什么；正文注释写一句结论。

---

### B4. `retry`（收窄异常）

实现：

```python
@retry(max_attempts=3, exceptions=(ValueError, ConnectionError))
def fetch():
    ...
```

要求：

1. 只重试指定异常类型；其它异常立刻抛出
2. 超过次数后抛 `RuntimeError`，并用 `from` 链接最后一次异常
3. 用「前两次 ValueError、第三次成功」验证
4. 另测：抛 `TypeError` 时不重试（attempts 计数可自行设计并说明）

**验收**：成功路径返回正确；类型不匹配时立即失败。

---

## 进阶题（建议至少做 1 题）

### A1. `timed` + 装饰器顺序

实现 `@timed`，打印毫秒耗时。  
然后对同一函数分别尝试：

```python
@timed
@retry(max_attempts=3, exceptions=(ConnectionError,))
def call_llm():
    ...

@retry(max_attempts=3, exceptions=(ConnectionError,))
@timed
def call_llm2():
    ...
```

让函数前两次失败、第三次成功。观察两次计时差异，并在 `notes_a1.md` 写 3～5 行：  
**外层 timed 与内层 timed 分别量的是什么。**

**验收**：有笔记；两种顺序都能最终成功。

---

### A2. 简易 `require_fields`

写带参装饰器，确保 kwargs 中包含必需字段：

```python
@require_fields("query", "top_k")
def search(**kwargs):
    return kwargs
```

缺字段时抛 `ValueError`，信息里带上缺失字段名。

**验收**：缺 `top_k` 时报错；字段齐全时正常返回。

---

## 挑战题（可选）

### C1. 类装饰器计数器

用类实现 `@count_calls`，使：

```python
@count_calls
def work():
    return "done"

work(); work()
print(work.calls)  # 2
```

**验收**：`calls` 可读取；`work.__name__` 尽量仍为 `work`（可用 `wraps` 或手动赋值）。

---

### C2. Agent 工具装饰器套装

为假工具函数加上：

1. `@require_fields(...)`
2. `@retry(...)`
3. `@timed`

模拟 `search(query: str, top_k: int = 3)`：偶发 `ConnectionError`，最终返回 list。  
写一段 demo 跑通，并打印工具的 `__name__`。

**验收**：缺参失败清晰；网络抖动可恢复；有耗时日志。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成
- [ ] 能口述：`@deco` 等价替换；有参装饰器三层结构；为何需要 wraps
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考思路（先做题再看）

<details>
<summary>B1 提示</summary>

`wrapper` 里先 log，再 `result = fn(*args, **kwargs)`，再 log，再 `return result`。

</details>

<details>
<summary>B2 提示</summary>

三层结构：`repeat(n)` → `decorator(fn)` → `wrapper`。循环 `n` 次保存 `result`。

</details>

<details>
<summary>B3 提示</summary>

分别装饰两个同名函数副本，或装饰后对比属性。重点看 `__name__` 是否变成 `wrapper`。

</details>

<details>
<summary>B4 提示</summary>

`except exceptions as exc:`（注意 `exceptions` 是 tuple）。其它异常不要 catch。

</details>

<details>
<summary>A1 思路</summary>

记住 `f = timed(retry(f))` 时，进入顺序是 timed → retry → f。外层计时包含所有重试等待。

</details>

<details>
<summary>C1 思路</summary>

类的 `__init__(self, fn)` 存函数；`__call__` 计数并调用。文档第 6 节有骨架。

</details>
