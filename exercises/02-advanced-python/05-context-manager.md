# 练习：上下文管理器

> 对应文档：[`docs/02-advanced-python/05-context-manager.md`](../../docs/02-advanced-python/05-context-manager.md)  
> 状态：`已完成出题`  
> 建议用时：50～80 分钟

## 练习说明

1. 先读完文档「必掌握」再做题。
2. 题目分档：**基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议代码目录：

```text
playground/02-advanced-python/05-context-manager/
```

4. 验证「异常也会清理」时，可用 `try/except` 包住 `with` 观察副作用。

---

## 基础题（必做）

### B1. 文件 with 实操

1. 用 `with` + `pathlib` 写入 `hello.txt`
2. 再用 `with` 读回并断言内容
3. 在写入过程中故意 `raise RuntimeError("boom")`（写在 with 块内），确认：
   - 异常能被捕获/看到
   - 文件句柄不会一直占用（至少保证你使用了 with，而不是裸 open）

**验收**：正常读写通过；异常路径代码存在且仍使用 `with`。

---

### B2. `@contextmanager` 计时器

实现：

```python
@contextmanager
def timed(label: str):
    ...
```

要求：

1. 退出时打印 `label` 与毫秒耗时
2. 块内异常也必须打印耗时，然后异常继续抛出
3. 写两段 demo：正常结束 / 异常结束

**验收**：两段都能看到耗时日志；异常段外层能 catch 到原异常。

---

### B3. 临时改配置

实现 `temporary_set(mapping, key, value)`（文档同款语义）：

- 进入时设置新值
- 退出时恢复旧值；若原先没有该 key，则退出时删除该 key
- 异常退出也必须恢复

**验收**：

```python
cfg = {"temperature": 0.7}
with temporary_set(cfg, "temperature", 0):
    assert cfg["temperature"] == 0
assert cfg["temperature"] == 0.7

with temporary_set(cfg, "top_p", 0.9):
    assert cfg["top_p"] == 0.9
assert "top_p" not in cfg
```

再补一个「块内 raise 后仍恢复」的断言。

---

### B4. 协议默写（小问答 + 最小类）

1. 在 `b4_notes.md` 用自己的话写：`__enter__` / `__exit__` 何时调用
2. 手写一个类 `NullContext`，`with NullContext() as x:` 时 `x` 为 `"ok"`，退出无事发生

**验收**：笔记存在；`with NullContext() as x: assert x == "ok"` 通过。

---

## 进阶题（建议至少做 1 题）

### A1. 类版 Timer

把 B2 改成类 `Timer`：

- `__enter__` 返回 self
- 属性 `elapsed_ms` 在退出后可读取
- 不吞异常

**验收**：`with Timer("x") as t:` 结束后 `t.elapsed_ms > 0`。

---

### A2. 会话作用域 `agent_session`

实现文档综合例子风格的 `agent_session(name)`：

- yield 一个带 `log` 方法的 session 对象
- 成功 / 失败写不同事件
- finally 写结束事件（可含耗时）
- 异常必须重新抛出

**验收**：成功与失败两条路径的 `events` 列表符合预期。

---

## 挑战题（可选）

### C1. 简易「锁」（单线程模拟也行）

实现 `FakeLock` 上下文管理器：

- 进入时若已锁定则抛 `RuntimeError("locked")`
- 否则标记锁定，退出时解锁
- 用两个连续 `with` 证明可重入使用（先后，不是嵌套）
- 再写一个嵌套/并发模拟：第二次 acquire 失败

（单线程用布尔标记即可，目的是练习协议，不是真实现线程锁。）

**验收**：正常 with 两次成功；在已锁定状态下再次 enter 失败；异常退出后锁被释放。

---

### C2. 工具调用 span

实现 `tool_span(tool_name: str)`：

- 进入：记录 start
- 退出：向全局 list append 一条记录 `{tool, ok, ms}`
- 块内异常 → `ok=False`，但仍记录，再抛出

用它包两段假工具调用（成功/失败），最后打印 span 列表。

**验收**：两条记录都在；失败那条 `ok is False`。

---

## 验收标准（本章通过线）

- [ ] B1～B4 全部完成
- [ ] 能口述：为何 with 比手工 close 更安全；`@contextmanager` 的 yield/finally 结构
- [ ] （建议）A1 或 A2 至少 1 题
- [ ] （可选）C1 / C2

---

## 提示与参考思路（先做题再看）

<details>
<summary>B2 提示</summary>

```python
start = ...
try:
    yield
finally:
    print(...)
```

不要在 except 里吞掉异常（除非你再 raise）。

</details>

<details>
<summary>B3 提示</summary>

先记下 `missing = key not in mapping` 与 `old = mapping.get(key)`，finally 里分支恢复。

</details>

<details>
<summary>B4 提示</summary>

```python
def __enter__(self):
    return "ok"
def __exit__(self, exc_type, exc, tb):
    return None
```

</details>

<details>
<summary>A2 思路</summary>

`try: yield session; log success` / `except: log error; raise` / `finally: log end`。

</details>

<details>
<summary>C1 思路</summary>

实例属性 `self._locked`。`__enter__` 检查并设置；`__exit__` 清回 False。用嵌套 with 或手动先 `__enter__` 再二次进入测冲突。

</details>
