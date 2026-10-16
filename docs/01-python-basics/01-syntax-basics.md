# 语法与数据结构

> 所属模块：`01-python-basics` · Python 语言基础  
> 状态：`已完成正文`  
> 建议学时：3～6 小时（有 JS/TS 基础可更快）  
> 对应练习：`[exercises/01-python-basics/01-syntax-basics.md](../../exercises/01-python-basics/01-syntax-basics.md)`

## 本章定位

- **模块目标**：能用 Python 写正常程序，而不是只会零散脚本。
- **本章角色**：搭好 Python 的「砖块」——变量、容器、分支循环、读写文件。后面所有 Agent / 后端代码都建立在这些砖块上。
- **你的优势**：若你熟悉 JS/TS，本章多数概念可「对照迁移」；重点盯住差异，而不是把语法书从头背完。

## 学习目标（学完应能做到）

1. 说清 Python 常见类型，并正确做类型转换与真假判断。
2. 熟练使用 `list` / `tuple` / `dict` / `set`，知道各自适合什么场景。
3. 用 `if` / `for` / `while` 写出可读的控制流，并会用推导式简化「过滤 + 映射」。
4. 用 `pathlib` 或基础 `open` 完成文本文件读写。
5. 完成课后练习，并分清哪些是「必掌握」、哪些可以先跳过。



## 重点分级


| 级别       | 内容                      | 学习要求         |
| -------- | ----------------------- | ------------ |
| **必掌握**  | 变量与类型、四大容器、控制流、推导式、文件读写 | 能写、能讲、能做题    |
| **建议掌握** | 切片技巧、常用内置函数             | 会用即可，不必背全表   |
| **了解即可** | bytes 与编码细节             | 建立地图，遇到乱码再深挖 |


---



## 1. 为什么要学（和 Agent 有什么关系）

Agent 开发里，你几乎每天都在处理这些东西：

```text
LLM 返回一段 JSON 字符串
    → 解析成 dict / list
    → 过滤工具调用、拼消息历史
    → 写入日志文件或本地缓存
```

所以本章不是「背语法」，而是练三种肌肉：

1. **把数据装进合适的容器**（list / dict 用错，后面全乱）
2. **用控制流表达业务逻辑**（分支、循环、提前返回）
3. **和文件系统打交道**（读配置、写结果、存会话）

先把这些做扎实，后面学 FastAPI、RAG、Tool Calling 时才不会在「基础语法」上卡壳。

---



## 2. 必掌握：变量与类型



### 2.1 动态类型，但类型仍然重要

Python 变量不需要先声明类型，但**值是有类型的**：

```python
name = "Alice"          # str
age = 20                # int
score = 95.5            # float
is_active = True        # bool
nothing = None          # NoneType，表示「没有值」
```

查看类型：

```python
print(type(name))       # <class 'str'>
print(isinstance(age, int))  # True
```

和 JS 对照：


| 概念  | JavaScript            | Python                              |
| --- | --------------------- | ----------------------------------- |
| 空值  | `null` / `undefined`  | 基本只用 `None`                         |
| 布尔  | `true` / `false`      | `True` / `False`（首字母大写）             |
| 字符串 | `'a'` / `"a"` / ``a`` | `'a'` / `"a"`，无模板字符串字面量（用 f-string） |
| 整数  | `Number`（易混浮点）        | `int` 任意精度，和 `float` 分开             |




### 2.2 f-string：拼字符串的首选方式

```python
user = "Bob"
tokens = 1280
print(f"{user} used {tokens} tokens")
# Bob used 1280 tokens
```

Agent 场景里拼 prompt、打日志，几乎都会用到 f-string。

### 2.3 真假值（Truthy / Falsy）——必掌握且易踩坑

在 `if` 里，下列值被视为「假」：

```python
False, None, 0, 0.0, "", [], {}, set()
```

其余多为「真」：

```python
messages = []
if messages:
    print("有消息")
else:
    print("无消息")  # 会走这里
```

**坑**：不要用 `if messages == []` 这种写法做「是否为空」的主判断；直接 `if messages:` / `if not messages:` 更地道。但若你要区分 `None` 和空列表，必须显式判断：

```python
# history 可能是 None（未初始化）或 []（已初始化但为空）
if history is None:
    history = []
```

判断是否为 `None`，用 `is` / `is not`，不要用 `==`。

### 2.4 类型转换

```python
int("42")        # 42
float("3.14")    # 3.14
str(42)          # "42"
bool(1)          # True
bool("")         # False

# 常见失败：
# int("3.14")   → ValueError
# int("abc")    → ValueError
```

从 LLM / HTTP 拿到的常常是字符串，**先转换再运算**。

---



## 3. 必掌握：四大容器

把容器想成「数据的收纳盒」。Agent 代码里 90% 的数据结构都落在它们上面。

### 3.1 list：有序、可变、可重复

```python
tools = ["search", "calc", "read_file"]
tools.append("write_file")
tools[0]                       # "search"
tools[-1]                      # "write_file"（倒数第一个）
len(tools)                     # 4
"calc" in tools                # True
```

适合：消息历史、工具列表、检索到的文档片段。

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你好"},
]
messages.append({"role": "assistant", "content": "你好！有什么可以帮你？"})
```



### 3.2 tuple：有序、不可变

```python
point = (10, 20)
# point[0] = 1  → TypeError，不能改「槽位」本身

# 注意：tuple 不可变 ≠ 里面的对象也不能变
# t = ([],); t[0].append(1)  # 合法：改的是 list，不是重绑 t[0]

# 常见用途：函数返回多个值、做 dict 的 key、表示固定结构
width, height = (1920, 1080)   # 解包
```

和 list 怎么选：

- 要改内容、要增删 → `list`
- 表示「一组固定字段」、不想被误改槽位 → `tuple`



### 3.3 dict：键值映射（你最该练熟的）

```python
user = {
    "name": "Alice",
    "age": 20,
    "roles": ["admin", "editor"],
}

user["name"]                   # "Alice"
user.get("email")              # None（不会抛错）
user.get("email", "N/A")       # "N/A"
user["email"] = "a@example.com"
"age" in user                  # True（查的是 key）
```

适合：JSON 对象、配置、一条 tool call、一条 HTTP 响应体。

```python
tool_call = {
    "name": "search",
    "arguments": {"query": "langgraph memory", "top_k": 5},
}
```

**坑 1**：访问不存在的 key 用 `[]` 会 `KeyError`，不确定时用 `.get()`。  
**坑 2**：遍历时默认遍历的是 key：

```python
for key in user:
    print(key, user[key])

for key, value in user.items():
    print(key, value)
```



### 3.4 set：去重、成员检测快

```python
tags = {"python", "agent", "rag", "python"}
print(tags)                    # 重复的 python 只保留一份

"agent" in tags                # True，平均 O(1)
tags.add("llm")
```

集合运算：

```python
a = {"search", "calc"}
b = {"calc", "browse"}
a | b                          # 并集
a & b                          # 交集 {"calc"}
a - b                          # 差集 {"search"}
```

适合：已调用过的工具名去重、权限集合、停用词表。

### 3.5 怎么选容器（速查）


| 需求            | 用什么     |
| ------------- | ------- |
| 有序列表、要改       | `list`  |
| 固定一组值、不改      | `tuple` |
| 按名字取值（JSON 味） | `dict`  |
| 去重 / 快速判断在不在  | `set`   |


---



## 4. 必掌握：控制流



### 4.1 if / elif / else

```python
status = "error"

if status == "ok":
    print("继续")
elif status == "retry":
    print("重试")
else:
    print("失败，记录日志")
```

Python 用**缩进**表示代码块（通常 4 个空格），没有 `{}`。缩进错了就是语法错误或逻辑错误。

### 4.2 for：遍历的主力

```python
tools = ["search", "calc", "read_file"]

for tool in tools:
    print(tool)

# 需要下标时
for i, tool in enumerate(tools):
    print(i, tool)

# 遍历 dict
for name, args in tool_call["arguments"].items():
    print(name, args)
```



### 4.3 while：少用，但要会

```python
retries = 3
while retries > 0:
    print("尝试调用 API")
    retries -= 1
```

Agent 的「最多循环 N 轮 tool calling」常用 `for _ in range(max_steps):`，比裸 `while True` 更安全。

### 4.4 break / continue / 提前返回思维

```python
docs = ["a", "", "b", None, "c"]
cleaned = []

for doc in docs:
    if doc is None:
        continue          # 跳过本次
    if doc == "":
        continue
    cleaned.append(doc)
    if len(cleaned) >= 2:
        break             # 够了就停
```

写复杂逻辑时，优先「不满足条件就 skip / return」，而不是层层嵌套 `if`。

### 4.5 range

```python
for i in range(3):         # 0, 1, 2
    print(i)

for i in range(1, 4):      # 1, 2, 3
    print(i)
```

---



## 5. 必掌握：推导式（List / Dict Comprehension）

推导式用来把「循环 + 过滤 + 转换」写成更短、更清晰的表达。  
有 JS 经验可以把它想成更强的 `map` + `filter`。

### 5.1 列表推导式

```python
users = [
    {"name": "Alice", "age": 20},
    {"name": "Bob", "age": 15},
    {"name": "Carol", "age": 25},
]

adult_names = [u["name"] for u in users if u["age"] >= 18]
# ["Alice", "Carol"]
```

等价于：

```python
adult_names = []
for u in users:
    if u["age"] >= 18:
        adult_names.append(u["name"])
```

Agent 场景例：从检索结果里抽出正文：

```python
chunks = [
    {"text": "hello", "score": 0.9},
    {"text": "world", "score": 0.4},
]
high = [c["text"] for c in chunks if c["score"] >= 0.5]
```



### 5.2 字典推导式

```python
names = ["search", "calc"]
tool_map = {name: {"enabled": True} for name in names}
# {"search": {"enabled": True}, "calc": {"enabled": True}}
```



### 5.3 什么时候不要用推导式

- 逻辑超过两行条件、嵌套很深 → 写回普通 `for`，可读性优先
- 有副作用（打印、写文件、发请求）→ 不要塞进推导式

---



## 6. 必掌握：文件读写



### 6.1 用 `with open`（推荐起点）

```python
# 写文本
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("first line\n")
    f.write("second line\n")

# 读全部
with open("notes.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 按行读
with open("notes.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
```

`with` 会在结束时自动关闭文件，避免资源泄漏。后面「上下文管理器」章会展开原理，这里先当成固定写法记住。

### 6.2 更现代：`pathlib`

```python
from pathlib import Path

path = Path("notes.txt")
path.write_text("hello\n", encoding="utf-8")
text = path.read_text(encoding="utf-8")

# 路径拼接
data_dir = Path("data")
file_path = data_dir / "messages.json"
```

工程代码里更推荐 `pathlib`，路径在 Windows / macOS 上更省心。

### 6.3 读写 JSON（超高频）

```python
import json
from pathlib import Path

messages = [
    {"role": "user", "content": "你好"},
]

path = Path("messages.json")
path.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")

loaded = json.loads(path.read_text(encoding="utf-8"))
print(loaded[0]["role"])
```

Agent 的会话历史、工具定义、评测数据集，大量都是 JSON 文件。

**记住**：始终显式写 `encoding="utf-8"`，减少跨平台乱码。

---



## 7. 建议掌握：切片技巧

切片语法：`seq[start:stop:step]`（`stop` 不含）

```python
nums = [0, 1, 2, 3, 4, 5]

nums[1:4]      # [1, 2, 3]
nums[:3]       # [0, 1, 2]
nums[3:]       # [3, 4, 5]
nums[-2:]      # [4, 5]
nums[::-1]     # 反转 [5, 4, 3, 2, 1, 0]
```

实用场景：

```python
# 只保留最近 10 条消息，防止 prompt 爆掉
history = history[-10:]

# 复制一份 list（浅拷贝）
copy = history[:]
```

字符串同样支持切片：`"hello"[1:4]` → `"ell"`。

---



## 8. 建议掌握：常用内置函数（先够用）

不必背手册，先把这几个用熟：

```python
len(x)                 # 长度
sum([1, 2, 3])         # 6
min(1, 2, 3)           # 1
max(1, 2, 3)           # 3
sorted([3, 1, 2])      # [1, 2, 3]
any([False, True])     # True
all([True, True])      # True
zip(names, scores)     # 配对迭代
enumerate(items)       # 带下标迭代
isinstance(x, list)    # 类型判断
```

排序字典列表（很常见）：

```python
chunks = [
    {"text": "b", "score": 0.2},
    {"text": "a", "score": 0.9},
]
chunks_sorted = sorted(chunks, key=lambda c: c["score"], reverse=True)
```

`lambda` 下一章函数篇会细讲；这里先当作「一次性小函数」即可。

---



## 9. 了解即可：bytes 与编码

你现在只需建立这张地图：

```text
str   = 人类可读的文本（Unicode 字符）
bytes = 磁盘/网络上的原始字节
编码 encode：str  → bytes   （如 UTF-8）
解码 decode：bytes → str
```

```python
s = "你好"
b = s.encode("utf-8")     # b'\xe4\xbd\xa0\xe5\xa5\xbd'
s2 = b.decode("utf-8")    # "你好"
```

何时再深挖：

- 读写非文本文件
- 处理 HTTP 原始 body
- 遇到 `UnicodeDecodeError` / 乱码

本章练习**不要求**你精通 bytes；文本场景统一 `utf-8` 即可。

---



## 10. 常见坑（建议收藏）

1. **可变默认值陷阱**（下章函数会详讲，先混个脸熟）
  不要写 `def f(items=[])`，列表会被多次调用共享。
2. `dict` **的 key 必须可哈希**
  list 不能当 key；tuple 可以（若元素也可哈希）。
3. **浅拷贝 vs 引用**
  ```python
   a = [1, 2, 3]
   b = a          # b 和 a 是同一个 list
   b.append(4)    # a 也变了
   c = a[:]       # 浅拷贝，一层独立
  ```
4. **在遍历 list 时删元素**
  容易漏删或抛错；更稳妥是建新列表，或先收集再删。
5. **Windows 路径**
  优先 `pathlib`，少手写 `"C:\\foo\\bar"` 拼接。
6. **把 JS 的** `===` **惯性带过来**
  Python 用 `==` 比内容，`is` 比身份（几乎只用于 `None`）。

---



## 11. 综合小例子：整理「假想的检索结果」

把本章知识点串起来。假设你拿到一批检索片段，要清洗、过滤、排序并写入文件：

```python
import json
from pathlib import Path

raw_chunks = [
    {"text": "  LangGraph 适合做有状态工作流  ", "score": 0.82, "source": "doc1"},
    {"text": "", "score": 0.91, "source": "doc2"},
    {"text": "RAG = 检索 + 生成", "score": 0.76, "source": "doc1"},
    {"text": "重复内容", "score": 0.55, "source": "doc3"},
    {"text": "重复内容", "score": 0.40, "source": "doc4"},
]

# 1) 清洗 + 过滤空文本 + 分数阈值
cleaned = []
seen_texts = set()

for chunk in raw_chunks:
    text = chunk["text"].strip()
    if not text:
        continue
    if chunk["score"] < 0.5:
        continue
    if text in seen_texts:      # 用 set 去重
        continue
    seen_texts.add(text)
    cleaned.append({"text": text, "score": chunk["score"], "source": chunk["source"]})

# 2) 排序并截断 Top-3（切片）
top_chunks = sorted(cleaned, key=lambda c: c["score"], reverse=True)[:3]

# 3) 推导式抽出文本，拼进 prompt
context = "\n".join(f"- {c['text']}" for c in top_chunks)
prompt = f"基于以下资料回答问题：\n{context}"

# 4) 落盘
out = Path("top_chunks.json")
out.write_text(json.dumps(top_chunks, ensure_ascii=False, indent=2), encoding="utf-8")

print(prompt)
print(f"saved {len(top_chunks)} chunks to {out}")
```

这已经很接近真实 RAG 流水线里「检索后处理」的一小段了。

---



## 12. 练习指引

请打开并完成：

`[exercises/01-python-basics/01-syntax-basics.md](../../exercises/01-python-basics/01-syntax-basics.md)`

建议代码位置（可自建）：

```text
playground/01-python-basics/01-syntax-basics/
```

完成标准以练习文档中的验收清单为准。

---



## 13. 小结与下一站



### 你现在应该掌握的心智模型

```text
值有类型 → 放进合适容器 → 用控制流处理 → 必要时读写文件
```



### 自检清单

- [ ] 能说明 `None` / 空列表 / 空字符串在 `if` 中的表现
- [ ] 能按场景选择 list / tuple / dict / set
- [ ] 能手写列表推导式完成「过滤 + 映射」
- [ ] 能用 `pathlib` 或 `open` 读写 UTF-8 文本 / JSON
- [ ] 独立完成练习基础题



### 下一章

`[02-functions-scope.md](./02-functions-scope.md)` —— 函数、作用域、`*args/**kwargs`、闭包。  
把「一段脚本」升级成「可复用的能力单元」，这是写 Agent 工具函数的起点。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 下一章：[函数与作用域](./02-functions-scope.md)

