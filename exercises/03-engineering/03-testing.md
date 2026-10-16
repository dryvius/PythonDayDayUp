# 练习：测试（pytest）

> 对应文档：[`docs/03-engineering/03-testing.md`](../../docs/03-engineering/03-testing.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

代码建议放在 `playground/03-engineering/03-testing/`（可含迷你 `app/` + `tests/`）。  
先 `pip install pytest` 或 `uv add --dev pytest`。

---

## 基础题（必做）

### B1. 第一个测试

实现 `app/textutil.py`：

- `normalize(text: str) -> str`：`strip` + 压缩空白
- `clip(text: str, max_len: int) -> str`

写 `tests/test_textutil.py` 至少 2 个测试。  
运行：`pytest -q`

**验收**：测试通过。

### B2. `pytest.raises`

为 `clip` 规定：`max_len < 3` 抛 `ValueError`。  
写测试断言该异常。

**验收**：有对应测试且通过。

### B3. fixture

写 fixture 提供样本 `messages` 列表，测试 `truncate_messages`（可自实现，逻辑同文档例子）。

**验收**：至少 1 个测试使用 fixture。

### B4. 测什么不测什么（书面）

在 `b4_notes.md` 列出：你的 Agent 项目里 3 件「优先单测」与 2 件「不该塞单测」的事，并简述原因。

**验收**：有笔记。

---

## 进阶题（建议）

### A1. 参数化

对 `normalize` 或 `clip` 用 `@pytest.mark.parametrize` 写 3 组以上用例。

### A2. FakeLLM 测试

写 `EchoLLM` + `ask(llm, prompt)`，测试 `ask(EchoLLM(), "hi")` 返回包含 `hi`。  
（不要打真实网络）

---

## 挑战题（可选）

### C1. mock 外部调用

函数内部调用 `http_post`（可假造模块），用 `unittest.mock.patch` 替换返回值并断言调用。

---

## 验收标准

- [ ] B1～B4 完成，`pytest` 绿
- [ ] （建议）A1 或 A2
- [ ] （可选）C1
