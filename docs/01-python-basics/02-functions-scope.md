# 函数与作用域

> 所属模块：`01-python-basics` · Python 语言基础  
> 状态：`已完成正文`  
> 建议学时：4～7 小时（有 JS/TS 基础可更快；闭包与可变默认参数建议动手踩一遍）  
> 对应练习：[`exercises/01-python-basics/02-functions-scope.md`](../../exercises/01-python-basics/02-functions-scope.md)

## 本章定位

- **模块目标**：能用 Python 写正常程序，而不是只会零散脚本。
- **本章角色**：把「一段能跑的代码」升级成「可复用、可组合的能力单元」。Agent 里的工具函数、消息清洗、重试封装，全是函数。
- **你的优势**：JS/TS 里的 `function` / 箭头函数 / 闭包经验可以直接迁移；重点盯住 Python 的默认参数坑、`*args/**kwargs`、以及 `global`/`nonlocal`。

## 学习目标（学完应能做到）

1. 正确定义函数、处理返回值，并养成「一个函数一件事」的习惯。
2. 熟练使用位置参数、关键字参数、默认参数，以及 `*args` / `**kwargs`。
3. 说清 LEGB 作用域规则，能写简单闭包，知道何时用 `nonlocal`。
4. 会用 `lambda` 处理排序等短小场景，知道什么时候不该用。
5. 完成课后练习，分清必掌握 / 建议掌握 / 了解即可。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | 函数定义与返回值、`*args/**kwargs`、作用域与闭包、lambda | 能写、能讲、能做题 |
| **建议掌握** | 高阶函数、functools 入门 | 会用 `map`/`filter`/`partial` 等常见模式 |
| **了解即可** | 递归与调用栈直觉 | 建立地图，算法题再深挖 |

---

## 1. 为什么要学（和 Agent 有什么关系）

#### 为什么需要函数？

没有函数时，你的代码往往是一条长脚本：

```text
读配置 → 拼 prompt → 调 LLM → 解析 JSON → 写日志 → 再调一次……
```

每一段都揉在一起：想复用「清洗消息」只能复制粘贴；想改「重试逻辑」要翻整份文件。

有了函数，Agent 代码通常长这样：

```text
build_prompt(messages) → call_llm(prompt) → parse_tool_calls(resp)
                                           → run_tool(name, args)
                                           → append_message(history, ...)
```

#### 本章要练的三种能力

1. **封装**：把重复逻辑收成函数（清洗、截断、重试）
2. **组合**：函数当参数传来传去（钩子、中间件、工具注册）
3. **边界清晰**：输入是什么、输出是什么、副作用是什么

可以先记一句：

> 函数不是「把代码缩进一下」，而是给一段能力起名字，并约定它的输入和输出。

---

## 2. 必掌握：函数定义与返回值

这一节会刻意写细——函数是后面闭包、装饰器、工具注册的共同底座。

### 2.1 最基本的形态

#### 为什么需要 `def`？

上一章你会写脚本步骤。但「两数相加」这种能力如果要在多处使用，就应该起个名字、规定输入输出——这就是函数。

#### 怎么写

```python
def add(a: int, b: int) -> int:
    """返回两数之和。"""
    return a + b
```

拆开看：

1. `def` 定义函数；名字用 `snake_case`
2. `a: int`、`-> int` 是类型注解——**现在先当文档用**，运行时默认不强制检查（后面类型系统章再系统讲）
3. `"""..."""` 是文档字符串，写在函数体第一行，养成习惯
4. `return` 把结果交给调用方

#### 跑一下

```python
print(add(2, 3))  # 5
result = add(10, 20)
print(result)     # 30
```

心智图：

```text
调用 add(2, 3)
    ↓
a=2, b=3 进入函数
    ↓
return 5
    ↓
调用方拿到 5
```

#### 易错点

| 错法 | 会发生什么 |
| --- | --- |
| 写了逻辑但忘了 `return` | 调用方拿到 `None`（见下一小节） |
| 函数名用了 `CamelCase` | 能跑，但不符合 Python 惯例 |
| 以为类型注解会拦错类型 | 默认不会；`add("a", "b")` 仍可能拼出 `"ab"` |

#### JS 对照

| JavaScript | Python |
| --- | --- |
| `function add(a, b) { return a + b }` | `def add(a, b): return a + b` |
| `const add = (a, b) => a + b` | 短逻辑可用 `lambda`（见后文） |
| 无返回 → `undefined` | 无 `return` → 返回 `None` |

---

### 2.2 没有 return 会怎样？

#### 为什么这一点特别重要？

很多人会以为「打印了就等于返回了」。这是初学函数时最常见的误会。

#### 怎么写 / 跑一下

```python
def log_hi(name: str) -> None:
    print(f"hi, {name}")


result = log_hi("Alice")
print(result)  # None
```

屏幕上你会看到：

```text
hi, Alice
None
```

第一行来自 `print`；第二行才是「函数真正交出来的值」——`None`。

#### 易错点

> `print` 只是把内容显示出来；真正交给调用方的，只有 `return` 的值。

调用「只做事、不产结果」的函数时，不要拿返回值做计算。  
约定：副作用型函数可以标注 `-> None`，让意图更清楚。

错误连锁示例：

```python
def bad_add(a, b):
    print(a + b)   # 只打印，不 return

x = bad_add(2, 3)  # x 是 None
# print(x + 1)     → TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
```

---

### 2.3 返回多个值：其实是 tuple

#### 为什么需要「一次返回多个」？

比如拆姓名、同时拿「商和余数」、同时返回「结果 + 是否成功」。Python 允许一次 `return` 多个值。

#### 怎么写 / 跑一下

```python
def split_name(full: str) -> tuple[str, str]:
    first, last = full.split(" ", 1)
    return first, last


a, b = split_name("Ada Lovelace")
print(a, b)  # Ada Lovelace
```

也可以先看清它其实是 tuple：

```python
pair = split_name("Ada Lovelace")
print(pair)        # ('Ada', 'Lovelace')
print(type(pair))  # <class 'tuple'>
```

#### 易错点

- `return first, last` 等价于 `return (first, last)`
- 接收个数必须对得上：`a, b, c = split_name(...)` 会 `ValueError`
- 只要一个整体时，直接 `pair = split_name(...)` 即可，不必强行解包

#### JS 对照

```javascript
function splitName(full) {
  const [first, last] = full.split(" ");
  return [first, last];  // 常用数组
}
```

Python 更常返回 tuple；用法上和解构赋值很像。

---

### 2.4 参数：位置、关键字、默认值

#### 为什么需要多种传参方式？

参数少时靠位置就够；参数一多，靠位置容易「第 3 个到底是啥」。关键字参数让调用可读；默认值让「常用情况少传参」。

#### 怎么写

```python
def create_message(role: str, content: str, name: str | None = None) -> dict:
    msg = {"role": role, "content": content}
    if name is not None:
        msg["name"] = name
    return msg
```

#### 跑一下

```python
print(create_message("user", "你好"))
# {'role': 'user', 'content': '你好'}

print(create_message(role="assistant", content="你好！"))
# {'role': 'assistant', 'content': '你好！'}

print(create_message("tool", "ok", name="search"))
# {'role': 'tool', 'content': 'ok', 'name': 'search'}
```

三种调用：

| 写法 | 含义 |
| --- | --- |
| 位置参数 | 按定义顺序塞：`("user", "你好")` |
| 关键字参数 | 按名字塞：`role="assistant", content="你好！"` |
| 默认参数 | 不传 `name` 时用 `None` |

#### 易错点（先记三条）

1. **有默认值的参数必须放在后面**  
   `def f(a=1, b):` → `SyntaxError`
2. 混用时：位置参数要在关键字参数前面  
   `create_message(role="user", "你好")` → `SyntaxError`
3. 默认值只求值一次（§9.1 可变默认值会专门打脸）

关键字参数的好处是可读：看到 `top_k=5` 就知道含义，不用靠位置猜。

#### JS 对照

```javascript
function createMessage(role, content, name = null) { ... }
createMessage("user", "你好");
createMessage("tool", "ok", "search");
```

JS 近年也有具名参数习惯（传一个 options 对象）；Python 直接支持 `name="search"` 这种关键字写法。

---

### 2.5 提前返回，减少嵌套

#### 为什么需要提前返回？

深层 `if/else` 会把「正常路径」挤到屏幕右边，难读也难改。无效输入尽早 `return`，主路径保持扁平。

#### 怎么写 / 跑一下

```python
def normalize_content(content: str | None) -> str | None:
    if content is None:
        return None
    text = content.strip()
    if not text:
        return None
    return text


print(normalize_content(None))      # None
print(normalize_content("  hi  "))  # hi
print(normalize_content("   "))     # None
```

对比「层层嵌套」版（不推荐当主力）：

```python
def normalize_content_nested(content: str | None) -> str | None:
    if content is not None:
        text = content.strip()
        if text:
            return text
        else:
            return None
    else:
        return None
```

#### 易错点 / 口诀

> 无效输入尽快离开，有效路径保持扁平。

Agent 工具函数里非常常见：先校验 role / content，不合法立刻 `raise` 或 `return`，再组装结果。

---

## 3. 必掌握：`*args` 与 `**kwargs`

先别被名字吓到。可以先这样理解：

> `*args`：把多余的位置参数收进一个 tuple  
> `**kwargs`：把多余的关键字参数收进一个 dict

### 3.1 `*args`：多余位置参数 → tuple

#### 为什么需要它？

有时参数个数不固定：打多个标签、求和任意个数、收集一批文件名。不想写 `a, b, c, d, e...`。

#### 怎么写 / 跑一下

```python
def tag_all(*items: str) -> list[str]:
    return [f"#{item}" for item in items]


print(tag_all("python", "agent"))       # ['#python', '#agent']
print(tag_all("rag"))                   # ['#rag']
print(tag_all())                        # []
print(tag_all("a", "b", "c"))           # ['#a', '#b', '#c']
```

函数内部把 `items` 当普通 tuple/序列用即可。

#### 易错点

- 名字不必叫 `args`，`*items` 也行；`*` 才是关键
- `*items` 收到的是 **tuple**，不是 list
- 若还有普通参数，普通参数要写在 `*args` 前面：`def f(prefix, *items)`

#### JS 对照

```javascript
function tagAll(...items) {
  return items.map((item) => `#${item}`);
}
```

Python 的 `*args` ≈ JS 的 rest 参数 `...items`。

---

### 3.2 `**kwargs`：多余关键字参数 → dict

#### 为什么需要它？

工具参数字段不固定：`query=...`、`top_k=...`、`url=...`。用 `**kwargs` 可以把「叫得上名字的多余参数」收成字典。

#### 怎么写 / 跑一下

```python
def build_tool_call(name: str, **arguments) -> dict:
    return {"name": name, "arguments": arguments}


print(build_tool_call("search", query="RAG", top_k=5))
# {'name': 'search', 'arguments': {'query': 'RAG', 'top_k': 5}}

print(build_tool_call("calc", expression="1+2"))
# {'name': 'calc', 'arguments': {'expression': '1+2'}}
```

这和「LLM tool calling 的 arguments 对象」几乎一一对应。

#### 易错点

- 名字不必叫 `kwargs`，`**arguments` 也行；`**` 才是关键
- `**arguments` 收到的是 **dict**
- 不能既按位置又按同名关键字传同一个参数

#### JS 对照

JS 没有完全相同的语法，常见等价是收一个 options 对象：

```javascript
function buildToolCall(name, arguments = {}) {
  return { name, arguments };
}
buildToolCall("search", { query: "RAG", top_k: 5 });
```

---

### 3.3 同时出现时的顺序

#### 为什么顺序有规定？

参数种类一多，解析规则必须固定，否则「谁吃位置参数、谁必须写关键字」会乱。

#### 怎么写

定义时推荐顺序：

```text
必选参数 → 默认参数 → *args → 仅关键字参数 → **kwargs
```

```python
def call_api(url: str, *args, method: str = "GET", timeout: float = 30.0, **kwargs):
    print("url =", url)
    print("method =", method)
    print("args =", args)
    print("timeout =", timeout)
    print("kwargs =", kwargs)
```

#### 跑一下

```python
call_api("https://api.example.com", method="POST", timeout=10, retry=True)
```

可能输出：

```text
url = https://api.example.com
method = POST
args = ()
timeout = 10
kwargs = {'retry': True}
```

注意：`method` / `timeout` 写在 `*args` 后面，属于**仅关键字参数**。  
调用必须写成 `method="POST"`，不能靠位置塞。

#### 易错点

```python
# 想靠位置传 method —— 做不到，会进 *args
call_api("https://x", "POST")
# method 仍是默认 "GET"；args == ("POST",)
```

这是故意设计：强制你把重要选项写清楚。

---

### 3.4 拆包：调用时把容器「打开」

#### 为什么需要拆包？

一边是「收集」：定义处用 `*` / `**` 收拢。  
另一边是「展开」：手里已有 list/dict，想一次性喂给函数。

#### 怎么写 / 跑一下

```python
def add(a, b, c):
    return a + b + c


nums = [1, 2, 3]
print(add(*nums))  # 等价 add(1, 2, 3) → 6

options = {"a": 1, "b": 2, "c": 3}
print(add(**options))  # 等价 add(a=1, b=2, c=3) → 6
```

包装函数（转发参数）时非常常见：

```python
def logged_call(fn, *args, **kwargs):
    print(f"calling {fn.__name__}")
    return fn(*args, **kwargs)


print(logged_call(add, 1, 2, 3))
# calling add
# 6
```

#### 心智模型

```text
定义处 *args/**kwargs  → 收拢
调用处 *list/**dict     → 展开
```

#### 易错点

| 错法 | 结果 |
| --- | --- |
| `add(nums)` | 只传了一个 list，不是三个数 |
| `add(*options)` | dict 按 key 迭代，通常不是你想要的 |
| `add(**nums)` | list 不能 `**` 展开 |

#### JS 对照

```javascript
add(...nums);           // 类似 *nums
add(...Object.values(options)); // 没有完全等同 **options 的日常写法
```

---

## 4. 必掌握：作用域与闭包

### 4.1 LEGB 规则（先记住这张图）

#### 为什么需要作用域？

同名变量可以出现在全局、外层函数、内层函数。Python 必须有一套「先找谁」的规则，否则你不知道读到的是哪一个。

#### 怎么理解

查一个名字时，按这个顺序找：

```text
L  Local       当前函数内
E  Enclosing   外层函数（闭包）
G  Global      当前模块全局
B  Built-in    内置（len / print 等）
```

#### 跑一下（对照输出想一遍）

```python
name = "global"


def outer():
    name = "enclosing"

    def inner():
        name = "local"
        print(name)

    inner()
    print(name)


outer()
print(name)
```

输出：

```text
local
enclosing
global
```

#### 易错点

`inner` 里的 `name` 不会改掉 `outer` 的 `name`；`outer` 也不会改掉全局的 `name`。  
每一层有自己的「小房间」。

图示：

```text
Global:   name = "global"
Outer:      name = "enclosing"
Inner:        name = "local"   ← inner 里的 print 先看到这个
```

---

### 4.2 函数内赋值会创建局部变量

#### 为什么这一点反直觉？

你可能以为：右边读全局，左边写回去。Python 不是这样判断的。

#### 跑一下（先看报错）

```python
count = 0


def bump():
    count = count + 1  # UnboundLocalError！
    return count
```

#### 规则

> 函数里只要对某个名字**赋值**，这个名字在整个函数里都被当成**局部变量**。

于是右边读 `count` 时，局部还没绑定，直接报错。

#### 若真要改全局（多数情况不推荐）

```python
count = 0


def bump() -> int:
    global count
    count = count + 1
    return count


print(bump())  # 1
print(bump())  # 2
print(count)   # 2
```

#### 易错点 / 更好做法

- 只**读取**全局、不赋值 → 通常不需要 `global`
- 更好：把状态当参数传入，或放进对象/字典里再返回
- 少用 `global`，否则状态会散落在模块各处，难测也难跟

---

### 4.3 闭包：内层函数「记住」外层变量

#### 为什么需要闭包？

你想生成「已经配置好的函数」：固定倍率、固定 api_key、固定 top_k。调用时只传变化的那部分。

#### 怎么写 / 跑一下

```python
def make_multiplier(n: int):
    def multiply(x: int) -> int:
        return x * n  # n 来自外层

    return multiply


double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5))  # 10
print(triple(5))  # 15
```

`multiply` 就是闭包：它携带了定义时的环境（这里的 `n`）。

流程：

```text
make_multiplier(2) 返回 multiply，其中 n 被记住为 2
double(5) → 5 * 2 → 10

make_multiplier(3) 返回另一个 multiply，n 被记住为 3
triple(5) → 5 * 3 → 15
```

#### Agent 场景：给工具注入固定配置

```python
def make_search_tool(api_key: str, top_k: int = 5):
    def search(query: str) -> dict:
        return {
            "tool": "search",
            "query": query,
            "top_k": top_k,
            "api_key_prefix": api_key[:4],
        }

    return search


search = make_search_tool("sk-xxxx", top_k=3)
print(search("langgraph"))
# {'tool': 'search', 'query': 'langgraph', 'top_k': 3, 'api_key_prefix': 'sk-x'}
```

调用 `search(...)` 时不用反复传 `api_key` / `top_k`——它们已经被「记住」了。

#### 易错点

- 闭包记住的是**变量**，不是「创建当时的一份复印件」（循环里配 lambda 时尤其容易踩坑，见 §9.2）
- 外层函数必须 `return` 内层函数，否则调用方拿不到闭包

#### JS 对照

```javascript
function makeMultiplier(n) {
  return function multiply(x) {
    return x * n;
  };
}
const double = makeMultiplier(2);
double(5); // 10
```

和 JS 闭包是同一类东西。

---

### 4.4 `nonlocal`：改外层（非全局）变量

#### 为什么需要 `nonlocal`？

闭包里如果只是**读**外层变量，通常没问题。  
一旦要**赋值修改**外层（非全局）变量，就要声明 `nonlocal`，否则又会变成「创建局部变量」。

#### 怎么写 / 跑一下

```python
def make_counter():
    count = 0

    def inc() -> int:
        nonlocal count
        count += 1
        return count

    return inc


counter = make_counter()
print(counter())  # 1
print(counter())  # 2
```

#### 没有 `nonlocal` 会怎样？

```python
def make_counter_bad():
    count = 0

    def inc():
        count += 1  # UnboundLocalError
        return count

    return inc
```

#### 选用口诀

| 你想改的是…… | 用什么 |
| --- | --- |
| 模块级变量 | `global`（尽量不用） |
| 外层函数变量 | `nonlocal` |
| 多数情况 | 返回新值，或用可变容器（如 `state = {"n": 0}`） |

可变容器技巧（有时比 `nonlocal` 更直观）：

```python
def make_counter():
    state = {"n": 0}

    def inc() -> int:
        state["n"] += 1  # 不重绑 state，只改内容，无需 nonlocal
        return state["n"]

    return inc
```

---

## 5. 必掌握：lambda

### 5.1 它是什么？

#### 为什么需要 lambda？

有时只需要一个「用一次的小函数」，例如排序时说明按哪个字段比。为它单独写 `def` 有点重，于是有了 `lambda`。

#### 怎么写 / 跑一下

```python
add = lambda a, b: a + b
print(add(1, 2))  # 3
```

等价于：

```python
def add(a, b):
    return a + b
```

限制：**只能是一个表达式**，不能写多行语句块。

---

### 5.2 最常见场景：排序的 `key`

#### 怎么写 / 跑一下

```python
chunks = [
    {"text": "b", "score": 0.2},
    {"text": "a", "score": 0.9},
]
chunks.sort(key=lambda c: c["score"], reverse=True)
print(chunks)
# [{'text': 'a', 'score': 0.9}, {'text': 'b', 'score': 0.2}]
```

读法：

> 排序时，每个元素 `c` 拿 `c["score"]` 当比较依据。

#### JS 对照

```javascript
chunks.sort((a, b) => b.score - a.score);
```

Python 更常见是 `key=lambda ...`，而不是自己写比较函数。

---

### 5.3 什么时候不该用？

#### 规则

- 适合「一行、一次性、无复杂逻辑」
- 超过一个表达式、需要语句（`if` 块、`for`）→ 写 `def`
- 需要复用、要写文档/类型注解 → 写 `def`

#### 反例与正例

```python
# 不推荐：可读性差
f = lambda x: x.strip() if isinstance(x, str) else ""

# 推荐
def clean_text(x: object) -> str:
    if isinstance(x, str):
        return x.strip()
    return ""
```

口诀：

> `lambda` 是便利贴，不是说明书。短才合适。

---

## 6. 建议掌握：高阶函数

高阶函数 = **接收函数当参数**，或 **返回函数**。

### 6.1 函数是一等公民

#### 为什么重要？

一旦函数能当参数传来传去，你就可以写「通用骨架 + 可插拔策略」——前端中间件、Agent 工具注册都是这个味道。

#### 怎么写 / 跑一下

```python
def shout(text: str) -> str:
    return text.upper()


def whisper(text: str) -> str:
    return text.lower()


def apply(fn, text: str) -> str:
    return fn(text)


print(apply(shout, "Hi"))     # HI
print(apply(whisper, "Hi"))   # hi
```

注意：`apply(shout, "Hi")` 传的是函数本身 `shout`，不是 `shout(...)`。

#### 易错点

```python
apply(shout(), "Hi")  # 错：先调用了 shout，且还缺参数
apply(shout, "Hi")    # 对：把函数对象传进去
```

#### JS 对照

```javascript
function apply(fn, text) {
  return fn(text);
}
apply((t) => t.toUpperCase(), "Hi");
```

---

### 6.2 `map` / `filter`（知道即可，推导式往往更香）

#### 怎么写

```python
nums = [1, 2, 3, 4]
squares = list(map(lambda x: x * x, nums))
evens = list(filter(lambda x: x % 2 == 0, nums))
print(squares)  # [1, 4, 9, 16]
print(evens)    # [2, 4]
```

#### 等价且通常更可读

```python
squares = [x * x for x in nums]
evens = [x for x in nums if x % 2 == 0]
```

#### 建议

工程里优先推导式；读别人代码时能认 `map`/`filter` 即可。  
上一章推导式已经练过「过滤 + 映射」，这里只是换一种写法。

---

### 6.3 简单装饰器直觉（预告）

#### 为什么现在提一嘴？

后面「装饰器」专章会展开。你已经会闭包和 `*args/**kwargs` 的话，装饰器并不神秘：**函数进、函数出**。

#### 怎么写 / 跑一下

```python
def twice(fn):
    def wrapper(*args, **kwargs):
        fn(*args, **kwargs)
        return fn(*args, **kwargs)

    return wrapper


@twice
def ping():
    print("pong")


ping()
# pong
# pong
```

`@twice` 近似于：

```python
def ping():
    print("pong")

ping = twice(ping)
```

#### 易错点

现在先混个脸熟即可，不必在本章死磕装饰器语法糖与 `functools.wraps`。

---

## 7. 建议掌握：functools 入门

只先拿两个最有用的。

### 7.1 `functools.partial`：预填部分参数

#### 为什么需要它？

闭包可以「记住配置」；`partial` 是更轻量的官方写法：把部分参数先钉死，得到参数更少的新可调用对象。

#### 怎么写 / 跑一下

```python
from functools import partial


def power(base: int, exp: int) -> int:
    return base ** exp


square = partial(power, exp=2)
print(square(5))  # 25  ← 等价 power(5, exp=2)
```

可以把它想成「半成品函数」：

```text
power(base, exp)
     ↓ partial(exp=2)
square(base)        # exp 已固定
```

#### Agent 场景

固定 `model` / `temperature`，只暴露 `prompt`：

```python
from functools import partial


def chat(model: str, prompt: str, temperature: float = 0.2) -> dict:
    return {"model": model, "prompt": prompt, "temperature": temperature}


ask_gpt = partial(chat, model="gpt-4.1-mini", temperature=0)
print(ask_gpt(prompt="用一句话解释 Agent"))
# {'model': 'gpt-4.1-mini', 'prompt': '用一句话解释 Agent', 'temperature': 0}
```

#### 易错点

- `partial` 不改变原函数，只是包一层
- 位置参数预填时要注意顺序；拿不准就用关键字预填（如上例）

#### 和闭包怎么选？

| 需求 | 更合适 |
| --- | --- |
| 只是预填参数 | `partial`（短、清晰） |
| 还要附加逻辑 / 状态 | 闭包或小工厂函数 |

---

### 7.2 `functools.lru_cache`：简单缓存

#### 为什么需要它？

相同输入会算很多次时（如递归斐波那契），缓存能把「算过的结果」记住。

#### 怎么写 / 跑一下

```python
from functools import lru_cache


@lru_cache(maxsize=128)
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


print(fib(10))  # 55
```

#### 易错点

适合**纯函数**（相同输入必相同输出、无副作用）。  
不要拿它缓存：

- 带网络请求的函数
- 依赖当前时间 / 随机数的函数
- 依赖全局可变状态的函数

否则结果可能错，也难排查。

---

## 8. 了解即可：递归与调用栈

### 8.1 递归是什么？

#### 为什么只需了解？

Agent 工程里更常见的是 **显式循环**（`for step in range(max_steps)`）。  
递归在树/图、某些算法题里重要，本章建立直觉即可。

#### 怎么写 / 跑一下

```python
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)


print(factorial(3))  # 6
```

调用栈大致像：

```text
factorial(3)
  → factorial(2)
      → factorial(1) → 1
      ← 2 * 1 = 2
  ← 3 * 2 = 6
```

#### 易错点

- 必须有明确的结束条件（base case），否则会一直调自己
- Python 默认递归深度有限（太大可能 `RecursionError`）
- 能用循环写清楚时，工程代码优先循环

本章练习不强制写复杂递归。

---

## 9. 常见坑（建议收藏）

### 9.1 可变默认参数（必背）

#### 先看「你觉得会怎样」

```python
def append_item(item, bucket=[]):  # 危险！
    bucket.append(item)
    return bucket


print(append_item(1))  # [1]
print(append_item(2))  # [1, 2]  ← 不是 [2]
```

#### 为什么不是 `[2]`？

> 默认参数在**定义时求值一次**，所有调用共享同一个 list。

图示：

```text
定义函数时：bucket ──▶ []
第一次调用：往这个 [] 里 append 1
第二次调用：还是这个 list，再 append 2
```

#### 正确写法

```python
def append_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket


print(append_item(1))  # [1]
print(append_item(2))  # [2]  ← 互不影响
```

口诀：

> 默认值里不要放 `[]` / `{}`；用 `None`，进函数再创建。

---

### 9.2 闭包 + 循环变量

#### 跑一下（先看意外结果）

```python
funcs = []
for i in range(3):
    funcs.append(lambda: i)

print([f() for f in funcs])  # [2, 2, 2]  ← 不是 0,1,2
```

#### 为什么？

lambda 捕获的是变量 `i`，不是当时的值；循环结束 `i` 已是 2。  
三个函数读到的都是「最终的 i」。

#### 修法：用默认参数「冻住」当时的值

```python
funcs = []
for i in range(3):
    funcs.append(lambda i=i: i)

print([f() for f in funcs])  # [0, 1, 2]
```

`i=i` 的意思是：定义 lambda 时，用当前的 `i` 当作默认参数存下来。

---

### 9.3 在函数里修改传入的 list/dict

#### 怎么回事？

```python
def add_role(msg: dict) -> dict:
    msg["role"] = "user"  # 直接改了外面的对象
    return msg


original = {"content": "hi"}
updated = add_role(original)
print(original)  # {'content': 'hi', 'role': 'user'}  ← 原对象也被改了
print(updated)
```

有时这是有意设计（就地更新）；有时会制造隐蔽 bug。

#### 需要「不改原对象」时

```python
def add_role(msg: dict) -> dict:
    new_msg = {**msg, "role": "user"}
    return new_msg


original = {"content": "hi"}
updated = add_role(original)
print(original)  # {'content': 'hi'}  ← 未变
print(updated)   # {'content': 'hi', 'role': 'user'}
```

#### 写函数前先问自己

> 我是在**变换出新数据**，还是在**就地改传入对象**？

两种都可以，但意图必须清楚——最好在文档字符串里写明。

---

### 9.4 把打印当返回

初学者常写 `print(result)` 却忘了 `return`，调用方拿到 `None` 再继续算就会出奇怪错误。

约定：

> **计算型函数必须 return；打印留给调用方或专门的 log 函数。**

自检三问：

1. 调用方需要这个结果吗？→ 需要就 `return`
2. 我是不是只是想看一眼？→ 用 `print` 或日志，别代替 `return`
3. 返回值是不是 `None`？→ 若意外是 `None`，先查有没有漏 `return`

---

## 10. 综合小例子：可配置的消息截断器

把本章知识点串起来——很像 Agent 里控制上下文窗口的小工具。

### 10.1 完整代码

```python
from functools import partial


def truncate_messages(
    messages: list[dict],
    *,
    max_non_system: int = 10,
    keep_system: bool = True,
) -> list[dict]:
    """截断消息历史：可选始终保留第一条 system，再保留最近 max_non_system 条。"""
    if not messages:
        return []

    if keep_system and messages[0].get("role") == "system":
        system = messages[0]
        rest = messages[1:]
        return [system] + rest[-max_non_system:]

    return messages[-max_non_system:]


def make_truncator(max_non_system: int, keep_system: bool = True):
    """闭包 / partial：生成固定策略的截断函数。"""
    return partial(
        truncate_messages,
        max_non_system=max_non_system,
        keep_system=keep_system,
    )


history = [
    {"role": "system", "content": "You are helpful."},
    *[{"role": "user", "content": f"q{i}"} for i in range(1, 8)],
]

shorten = make_truncator(max_non_system=3)
print(shorten(history))
# keep_system=True 时：1 条 system + 最近 3 条非 system = 共 4 条
# [
#   {'role': 'system', 'content': 'You are helpful.'},
#   {'role': 'user', 'content': 'q5'},
#   {'role': 'user', 'content': 'q6'},
#   {'role': 'user', 'content': 'q7'},
# ]
```

### 10.2 这里用到了什么？

```text
默认参数
  → 仅关键字参数（* 后面的 max_non_system / keep_system）
  → 提前返回（空列表）
  → 切片保留最近 N 条
  → 返回新 list（不乱改原历史）
  → partial 预配置成「固定策略截断器」
```

### 10.3 为什么 `*` 后面的参数很合适？

`truncate_messages(messages, *, max_non_system=10, ...)` 强制调用方写：

```python
truncate_messages(history, max_non_system=3)
```

而不是：

```python
truncate_messages(history, 3)  # 别人很难一眼看出 3 是什么
```

可读性在 Agent 配置代码里尤其重要。

---

## 11. 练习指引

请打开并完成：

[`exercises/01-python-basics/02-functions-scope.md`](../../exercises/01-python-basics/02-functions-scope.md)

建议代码位置：

```text
playground/01-python-basics/02-functions-scope/
```

建议路径：

1. 先做热身题 W1～W6（把 `return`、默认参数、闭包、可变默认值踩一遍）
2. 再做基础题 B1～B4（本章通过线）
3. 有余力做进阶 / 挑战

先按自己的理解写出来即可；尤其是可变默认参数和闭包题，写错一次往往比只看文档记得更牢。

---

## 12. 小结与下一站

### 你现在应该掌握的心智模型

```text
输入 → 函数（纯计算 / 有副作用）→ 输出
         ↑
    作用域决定名字从哪来
    闭包让函数带上「配置环境」
    *args/**kwargs 让参数可收可扩
```

### 自检清单

- [ ] 能写出带默认参数与类型注解的函数，并正确 `return`（清楚 print ≠ return）
- [ ] 能解释并使用 `*args` / `**kwargs` 与拆包转发
- [ ] 能说明 LEGB，会写闭包，知道 `nonlocal` / `global` 各自干什么
- [ ] 知道可变默认参数坑，能用 `None` 修复
- [ ] 会用 `lambda` 做简单排序 key，知道何时改回 `def`
- [ ] 独立完成练习基础题（建议先完成热身题）

### 下一章

[`03-modules-packages.md`](./03-modules-packages.md) —— 模块、包与导入系统。  
把多个函数组织成可维护的项目结构，而不是全塞在一个文件里。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[语法与数据结构](./01-syntax-basics.md)
- 下一章：[模块、包与导入系统](./03-modules-packages.md)
