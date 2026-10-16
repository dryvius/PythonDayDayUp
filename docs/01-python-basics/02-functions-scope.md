# 函数与作用域

> 所属模块：`01-python-basics` · Python 语言基础  
> 状态：`已完成正文`  
> 建议学时：3～5 小时（有 JS/TS 基础可更快）  
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
|------|------|----------|
| **必掌握** | 函数定义与返回值、`*args/**kwargs`、作用域与闭包、lambda | 能写、能讲、能做题 |
| **建议掌握** | 高阶函数、functools 入门 | 会用 `map`/`filter`/`partial` 等常见模式 |
| **了解即可** | 递归与调用栈直觉 | 建立地图，算法题再深挖 |

---

## 1. 为什么要学（和 Agent 有什么关系）

没有函数时，你的代码往往是一条长脚本：

```text
读配置 → 拼 prompt → 调 LLM → 解析 JSON → 写日志 → 再调一次……
```

有了函数，Agent 代码通常长这样：

```text
build_prompt(messages) → call_llm(prompt) → parse_tool_calls(resp)
                                           → run_tool(name, args)
                                           → append_message(history, ...)
```

本章要练的能力：

1. **封装**：把重复逻辑收成函数（清洗、截断、重试）
2. **组合**：函数当参数传来传去（钩子、中间件、工具注册）
3. **边界清晰**：输入是什么、输出是什么、副作用是什么

---

## 2. 必掌握：函数定义与返回值

### 2.1 最基本的形态

```python
def add(a: int, b: int) -> int:
    """返回两数之和。"""
    return a + b


print(add(2, 3))  # 5
```

说明：

- `def` 定义函数；函数名用 `snake_case`
- 类型注解（`a: int`、`-> int`）**现在先当文档用**，运行时默认不强制检查；后面类型系统章会系统讲
- 文档字符串 `"""..."""` 写在函数体第一行，养成习惯

和 JS 对照：

| JavaScript | Python |
|------------|--------|
| `function add(a, b) { return a + b }` | `def add(a, b): return a + b` |
| `const add = (a, b) => a + b` | 短逻辑可用 `lambda`（见后文） |
| 无返回 → `undefined` | 无 `return` → 返回 `None` |

### 2.2 没有 return 会怎样？

```python
def log_hi(name: str) -> None:
    print(f"hi, {name}")


result = log_hi("Alice")
print(result)  # None
```

调用「只做事、不产结果」的函数时，不要拿返回值做计算。  
约定：副作用型函数可以标注 `-> None`，让意图更清楚。

### 2.3 返回多个值：其实是 tuple

```python
def split_name(full: str) -> tuple[str, str]:
    first, last = full.split(" ", 1)
    return first, last


a, b = split_name("Ada Lovelace")
print(a, b)  # Ada Lovelace
```

`return first, last` 等价于 `return (first, last)`，常用解包接收。

### 2.4 参数：位置、关键字、默认值

```python
def create_message(role: str, content: str, name: str | None = None) -> dict:
    msg = {"role": role, "content": content}
    if name is not None:
        msg["name"] = name
    return msg


create_message("user", "你好")
create_message(role="assistant", content="你好！")
create_message("tool", "ok", name="search")
```

规则（先记这三条）：

1. **有默认值的参数必须放在后面**
2. 调用时可混用位置参数 + 关键字参数，但位置参数要在前
3. 默认值只求值一次（见常见坑：可变默认值）

### 2.5 提前返回，减少嵌套

```python
def normalize_content(content: str | None) -> str | None:
    if content is None:
        return None
    text = content.strip()
    if not text:
        return None
    return text
```

这比层层 `if/else` 嵌套更易读，Agent 工具函数里很常见。

---

## 3. 必掌握：`*args` 与 `**kwargs`

把它们理解成：「把多余的位置参数 / 关键字参数收进容器」。

### 3.1 `*args`：多余位置参数 → tuple

```python
def tag_all(*items: str) -> list[str]:
    return [f"#{item}" for item in items]


print(tag_all("python", "agent"))  # ['#python', '#agent']
```

### 3.2 `**kwargs`：多余关键字参数 → dict

```python
def build_tool_call(name: str, **arguments) -> dict:
    return {"name": name, "arguments": arguments}


print(build_tool_call("search", query="RAG", top_k=5))
# {'name': 'search', 'arguments': {'query': 'RAG', 'top_k': 5}}
```

这和「LLM tool calling 的 arguments 对象」几乎一一对应。

### 3.3 同时出现时的顺序

定义时推荐顺序：

```text
必选参数 → 默认参数 → *args → 仅关键字参数 → **kwargs
```

```python
def call_api(url: str, *args, method: str = "GET", timeout: float = 30.0, **kwargs):
    print(url, method, args, timeout, kwargs)
```

说明：`method` / `timeout` 在 `*args` 之后，属于**仅关键字参数**，调用必须写成  
`call_api(url, method="POST", timeout=10)`，不能靠位置塞进 `*args`。

### 3.4 拆包：调用时把容器「打开」

```python
def add(a, b, c):
    return a + b + c


nums = [1, 2, 3]
print(add(*nums))  # 等价 add(1, 2, 3)

options = {"a": 1, "b": 2, "c": 3}
print(add(**options))  # 等价 add(a=1, b=2, c=3)
```

转发场景（包装函数）非常常见：

```python
def logged_call(fn, *args, **kwargs):
    print(f"calling {fn.__name__}")
    return fn(*args, **kwargs)
```

---

## 4. 必掌握：作用域与闭包

### 4.1 LEGB 规则（先记住这张图）

查一个名字时，Python 按这个顺序找：

```text
L  Local       当前函数内
E  Enclosing   外层函数（闭包）
G  Global      当前模块全局
B  Built-in    内置（len / print 等）
```

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
# local
# enclosing
# global
```

### 4.2 函数内赋值会创建局部变量

```python
count = 0


def bump():
    count = count + 1  # UnboundLocalError！
    return count
```

原因：函数里出现了对 `count` 的赋值，Python 把 `count` 当成**局部变量**；右边读取时局部还没绑定，就报错。

若真要改全局（多数情况不推荐）：

```python
count = 0


def bump() -> int:
    global count
    count = count + 1
    return count
```

更好的做法：把状态当参数传入、或放进对象/字典里返回，少用 `global`。

### 4.3 闭包：内层函数「记住」外层变量

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

Agent 场景例：给工具注入固定配置：

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
```

### 4.4 `nonlocal`：改外层（非全局）变量

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

没有 `nonlocal`，`count += 1` 会被当成给局部 `count` 赋值，再次踩到 UnboundLocalError 同类问题。

**选用口诀**：

- 改模块级变量 → `global`（尽量不用）
- 改外层函数变量 → `nonlocal`
- 多数情况 → 返回新值 / 用可变容器（如 `state = {"n": 0}`）传递状态

---

## 5. 必掌握：lambda

`lambda` 用来写**只有一个表达式**的匿名函数。

```python
add = lambda a, b: a + b
print(add(1, 2))  # 3
```

最常见场景：排序的 `key`

```python
chunks = [
    {"text": "b", "score": 0.2},
    {"text": "a", "score": 0.9},
]
chunks.sort(key=lambda c: c["score"], reverse=True)
```

规则：

- 适合「一行、一次性、无复杂逻辑」
- 超过一个表达式、需要语句（`if` 块、`for`）→ 写 `def`
- 需要复用、要写文档/类型注解 → 写 `def`

```python
# 不推荐：可读性差
f = lambda x: x.strip() if isinstance(x, str) else ""

# 推荐
def clean_text(x: object) -> str:
    if isinstance(x, str):
        return x.strip()
    return ""
```

---

## 6. 建议掌握：高阶函数

高阶函数 = **接收函数当参数**，或 **返回函数**。

### 6.1 函数是一等公民

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

这和前端把回调、中间件传来传去一样。

### 6.2 `map` / `filter`（知道即可，推导式往往更香）

```python
nums = [1, 2, 3, 4]
squares = list(map(lambda x: x * x, nums))
evens = list(filter(lambda x: x % 2 == 0, nums))
```

等价且通常更可读：

```python
squares = [x * x for x in nums]
evens = [x for x in nums if x % 2 == 0]
```

工程里优先推导式；读别人代码时能认 `map`/`filter` 即可。

### 6.3 简单装饰器直觉（预告）

后面「装饰器」专章会展开。这里先混个脸熟：

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

本质就是：函数进、函数出。

---

## 7. 建议掌握：functools 入门

只先拿两个最有用的。

### 7.1 `functools.partial`：预填部分参数

```python
from functools import partial


def power(base: int, exp: int) -> int:
    return base ** exp


square = partial(power, exp=2)
print(square(5))  # 25
```

Agent 场景：固定 `model` / `temperature`，只暴露 `prompt`：

```python
from functools import partial


def chat(model: str, prompt: str, temperature: float = 0.2) -> dict:
    return {"model": model, "prompt": prompt, "temperature": temperature}


ask_gpt = partial(chat, model="gpt-4.1-mini", temperature=0)
print(ask_gpt(prompt="用一句话解释 Agent"))
```

### 7.2 `functools.lru_cache`：简单缓存

```python
from functools import lru_cache


@lru_cache(maxsize=128)
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


print(fib(10))
```

适合**纯函数**（相同输入必相同输出、无副作用）。  
不要拿它缓存「带网络请求、依赖当前时间」的函数——结果可能错，也难排查。

---

## 8. 了解即可：递归与调用栈

递归 = 函数调用自己。先建立直觉即可：

```python
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

调用栈大致像：

```text
factorial(3)
  → factorial(2)
      → factorial(1) → 1
      ← 2 * 1
  ← 3 * 2
```

注意：

- Python 默认递归深度有限（太大可能 `RecursionError`）
- Agent 工程里更常见的是 **显式循环**（`for step in range(max_steps)`），而不是深递归
- 树/图遍历、某些算法题才会真正依赖递归

本章练习不强制写复杂递归。

---

## 9. 常见坑（建议收藏）

### 9.1 可变默认参数（必背）

```python
def append_item(item, bucket=[]):  # 危险！
    bucket.append(item)
    return bucket


print(append_item(1))  # [1]
print(append_item(2))  # [1, 2]  ← 不是 [2]
```

默认参数在**定义时求值一次**，所有调用共享同一个 list。

正确写法：

```python
def append_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

### 9.2 闭包 + 循环变量

```python
funcs = []
for i in range(3):
    funcs.append(lambda: i)

print([f() for f in funcs])  # [2, 2, 2]  ← 不是 0,1,2
```

原因：lambda 捕获的是变量 `i`，不是当时的值；循环结束 `i` 已是 2。

修法：用默认参数「冻住」当时的值：

```python
funcs = []
for i in range(3):
    funcs.append(lambda i=i: i)

print([f() for f in funcs])  # [0, 1, 2]
```

### 9.3 在函数里修改传入的 list/dict

```python
def add_role(msg: dict) -> dict:
    msg["role"] = "user"  # 直接改了外面的对象
    return msg
```

有时这是有意设计（就地更新）；有时会制造隐蔽 bug。  
需要「不改原对象」时，先拷贝：

```python
def add_role(msg: dict) -> dict:
    new_msg = {**msg, "role": "user"}
    return new_msg
```

### 9.4 把打印当返回

初学者常写 `print(result)` 却忘了 `return`，调用方拿到 `None` 再继续算就会出奇怪错误。  
约定：**计算型函数必须 return；打印留给调用方或专门的 log 函数。**

---

## 10. 综合小例子：可配置的消息截断器

把本章知识点串起来——很像 Agent 里控制上下文窗口的小工具：

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

这里用到了：默认参数、仅关键字参数（`*` 后面）、返回新 list、`partial` 预配置。

---

## 11. 练习指引

请打开并完成：

[`exercises/01-python-basics/02-functions-scope.md`](../../exercises/01-python-basics/02-functions-scope.md)

建议代码位置：

```text
playground/01-python-basics/02-functions-scope/
```

---

## 12. 小结与下一站

### 你现在应该掌握的心智模型

```text
输入 → 函数（纯计算 / 有副作用）→ 输出
         ↑
    作用域决定名字从哪来
    闭包让函数带上「配置环境」
```

### 自检清单

- [ ] 能写出带默认参数与类型注解的函数，并正确 `return`
- [ ] 能解释并使用 `*args` / `**kwargs` 与拆包
- [ ] 能说明 LEGB，会写闭包，知道 `nonlocal` 干什么
- [ ] 知道可变默认参数坑，能用 `None` 修复
- [ ] 独立完成练习基础题

### 下一章

[`03-modules-packages.md`](./03-modules-packages.md) —— 模块、包与导入系统。  
把多个函数组织成可维护的项目结构，而不是全塞在一个文件里。

## 导航

- 返回模块：[README](./README.md)
- 返回总览：[../../README.md](../../README.md)
- 上一章：[语法与数据结构](./01-syntax-basics.md)
- 下一章：[模块、包与导入系统](./03-modules-packages.md)
