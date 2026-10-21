# 语法与数据结构

> 所属模块：`01-python-basics` · Python 语言基础  
> 状态：`已完成正文`  
> 建议学时：4～8 小时（有 JS/TS 基础可更快；容器与控制流建议动手敲一遍）  
> 对应练习：`[exercises/01-python-basics/01-syntax-basics.md](../../exercises/01-python-basics/01-syntax-basics.md)`

## 本章定位

- **模块目标**：能用 Python 写正常程序，而不是只会零散脚本。
- **本章角色**：搭好 Python 的「砖块」——变量、容器、分支循环、读写文件。后面所有 Agent / 后端代码都建立在这些砖块上。
- **你的优势**：若你熟悉 JS/TS，本章多数概念可「对照迁移」；重点盯住差异，而不是把语法书从头背完。

## 学习目标（学完应能做到）

1. 说清 Python 常见类型，并正确做类型转换、真假判断与基础运算。
2. 熟练使用 `list` / `tuple` / `dict` / `set`，知道各自适合什么场景。
3. 用 `if` / `for` / `while` 写出可读的控制流，并会用推导式简化「过滤 + 映射」。
4. 用 `pathlib` 或基础 `open` 完成文本文件读写。
5. 完成课后练习，并分清哪些是「必掌握」、哪些可以先跳过。

## 重点分级

| 级别 | 内容 | 学习要求 |
| --- | --- | --- |
| **必掌握** | 变量与类型、运算符、四大容器、控制流、推导式、文件读写 | 能写、能讲、能做题 |
| **建议掌握** | 切片技巧、常用内置函数 | 会用即可，不必背全表 |
| **了解即可** | bytes 与编码细节 | 建立地图，遇到乱码再深挖 |

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

### 2.1 变量到底是什么

你可以先把变量理解为：

> 给一个数据起名字，方便后续反复使用。

例如：

```python
name = "Alice"
age = 20

print(name)
print(age)
```

这里的 `=` **不是**数学里的「等于」，而是**赋值**：把右边的值绑到左边的名字上。

和 JS 最大的体感差异：Python 通常不需要 `let` / `const` / `var`，直接写：

```python
name = "Alice"
```

即可。后面改值也是同一个写法：

```python
age = 20
age = 21  # 重新赋值
```

### 2.2 动态类型，但类型仍然重要

Python 变量不用先声明类型，但**值是有类型的**：

```python
name = "Alice"          # str
age = 20                # int
score = 95.5            # float
is_active = True        # bool
nothing = None          # NoneType，表示「没有值」
```

目前先把这几类摸熟：

| 类型 | Python 类型 | 示例 |
| --- | --- | --- |
| 整数 | `int` | `20`、`-5` |
| 浮点数 | `float` | `95.5`、`3.14` |
| 字符串 | `str` | `"Alice"`、`'hi'` |
| 布尔值 | `bool` | `True`、`False`（首字母大写） |
| 空值 | `NoneType` | `None` |

查看类型：

```python
print(type(name))              # <class 'str'>
print(isinstance(age, int))    # True
```

和 JS 对照一下，容易一次对齐：

| 概念 | JavaScript | Python |
| --- | --- | --- |
| 空值 | `null` / `undefined` | 基本只用 `None` |
| 布尔 | `true` / `false` | `True` / `False`（首字母大写） |
| 字符串 | `'a'` / `"a"` / `` `a` `` | `'a'` / `"a"`，模板字符串改用 f-string |
| 整数 | `Number`（易混浮点） | `int` 任意精度，和 `float` 分开 |
| 类型检查 | `typeof age` | `type(age)` / `isinstance(...)` |

### 2.3 为什么数据类型这么重要

看看这段：

```python
a = "10"
b = "20"
print(a + b)
```

你觉得结果是 `30` 吗？

不是。实际是：

```text
1020
```

因为 `"10"` 和 `"20"` 是字符串。字符串的 `+` 表示**拼接**，不是数学加法。

如果希望做数学运算，需要先转换：

```python
a = int("10")
b = int("20")
print(a + b)  # 30
```

从 LLM / HTTP / `input()` 拿到的常常是字符串。记住一句：

> **先确认类型，再运算。**

### 2.4 类型转换

常见转换函数：

```python
int("42")        # 42
float("3.14")    # 3.14
str(42)          # "42"
bool(1)          # True
bool("")         # False
```

也常直接写：

```python
age = int("18")
price = float("19.9")
text = str(age)
```

常见失败（先混个脸熟，遇到别慌）：

```python
# int("3.14")   → ValueError（小数文本不能直接变 int）
# int("abc")    → ValueError
```

需要「字符串小数 → 整数」时，通常先 `float` 再 `int`，或先确认输入格式。

### 2.5 f-string：拼字符串的首选方式

JS 里你可能写：

```javascript
console.log(`${user} used ${tokens} tokens`);
```

Python 对应写法是 f-string：在字符串前加 `f`，用 `{}` 嵌入变量或表达式。

```python
user = "Bob"
tokens = 1280
print(f"{user} used {tokens} tokens")
# Bob used 1280 tokens
```

`{}` 里也可以放表达式：

```python
price = 19.9
count = 3
print(f"总价：{price * count} 元")
# 总价：59.7 元
```

对比一下旧写法（不推荐当主力）：

```python
print(user + " used " + str(tokens) + " tokens")
```

又啰嗦又容易忘 `str()`。Agent 场景里拼 prompt、打日志，几乎都会用 f-string。

### 2.6 真假值（Truthy / Falsy）——必掌握且易踩坑

在 `if` 里，下列值被视为「假」：

```python
False, None, 0, 0.0, "", [], {}, set()
```

其余多为「真」。于是你会经常写：

```python
messages = []
if messages:
    print("有消息")
else:
    print("无消息")  # 会走这里
```

**坑 1**：判断「是否为空」，优先 `if messages:` / `if not messages:`，不要习惯性写 `if messages == []`。

**坑 2**：若要区分 `None`（未初始化）和 `[]`（已初始化但为空），必须显式判断：

```python
if history is None:
    history = []
```

判断是否为 `None`，用 `is` / `is not`，不要用 `==`。  
（Python 没有 JS 的 `===`；内容比较用 `==`，身份比较用 `is`，而 `is` 几乎只该用在 `None` 上。）

### 2.7 算术运算符

你大概已经用过 `+ - * /`。完整一点看：

| 运算符 | 含义 | 示例 | 结果 |
| --- | --- | --- | --- |
| `+` | 加 | `10 + 3` | `13` |
| `-` | 减 | `10 - 3` | `7` |
| `*` | 乘 | `10 * 3` | `30` |
| `/` | 除 | `10 / 3` | `3.333...` |
| `//` | 整除 | `10 // 3` | `3` |
| `%` | 取余 | `10 % 3` | `1` |
| `**` | 幂 | `10 ** 3` | `1000` |

三个特别值得盯住：

**`//` 整除**：只保留商。

```python
10 // 3  # 3
```

**`%` 取余**：拿余数。以后判断偶数会写：

```python
num = 10
print(num % 2)       # 0
print(num % 2 == 0)  # True → 偶数
```

`//` 和 `%` 经常成对出现。例如把秒数拆成「分 + 秒」：

```python
total = 125
minutes = total // 60   # 2
seconds = total % 60    # 5
print(f"{minutes} 分 {seconds} 秒")
# 2 分 5 秒
```

因为：

```text
125 ÷ 60 = 2 …… 5
         ↑         ↑
         //        %
```

**`**` 幂**：

```python
2 ** 3   # 8
10 ** 2  # 100
```

还有一个容易忽略的点：

```python
result = 10 / 2
print(result)       # 5.0
print(type(result)) # <class 'float'>
```

在 Python 3 里，`/` 的结果通常是 `float`，即使除得尽。需要整数商时用 `//`。

### 2.8 运算符优先级与赋值简写

优先级和数学基本一致：先乘除，后加减。

```python
result = 2 + 3 * 4   # 14，不是 20
result = (2 + 3) * 4 # 20
```

实际开发里不必死背复杂优先级表：

> 有一点拿不准，就直接加括号。可读性通常比「炫技式优先级」更重要。

赋值也可以简写（循环里会大量出现）：

```python
money = 100
money += 20   # 等价于 money = money + 20
money -= 20
money *= 2
money /= 2
```

### 2.9 第一次接触比较运算符

```python
>
<
>=
<=
==
!=
```

例如：

```python
age = 18
print(age > 10)   # True
print(age == 18)  # True
```

务必分清：

```python
age = 18   # 赋值
age == 18  # 判断是否相等
```

这是初学阶段最容易写错的地方之一。JS 里你可能写 `age === 18`；Python 用 `==` 即可。

---

## 3. 必掌握：四大容器

把容器想成「数据的收纳盒」。Agent 代码里 90% 的数据结构都落在它们上面。  
这一节会刻意写细一点——尤其是 `list`，因为它是后面循环、切片、推导式、消息历史的共同底座。

### 3.1 list：有序、可变、可重复

#### 为什么需要列表？

之前我们这样保存数据：

```python
name = "张三"
age = 18
score = 95
```

如果现在有 100 个学生：

```python
name1 = "张三"
name2 = "李四"
name3 = "王五"
# ...
```

显然很麻烦。于是可以把**一组同类数据**放进一个列表：

```python
names = ["张三", "李四", "王五"]
```

从这里开始，Python 逐渐从「处理单个值」进入「处理一组数据」。

#### 创建列表

最基本：

```python
names = ["张三", "李四", "王五"]
numbers = [10, 20, 30, 40, 50]
```

技术上也可以混合类型：

```python
data = ["张三", 18, 95.5, True]
```

但实际开发里，通常让一个列表里的元素**语义相近**：

```python
students = ["张三", "李四", "王五"]
scores = [88, 92, 76, 95]
```

Agent 里常见的是「消息列表」「工具名列表」「检索片段列表」：

```python
tools = ["search", "calc", "read_file"]

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你好"},
]
```

#### 索引：从 0 开始

这是列表最重要的概念之一。

```python
names = ["张三", "李四", "王五"]
```

对应关系：

```text
        0       1       2
      ┌─────┬─────┬─────┐
      │ 张三 │ 李四 │ 王五 │
      └─────┴─────┴─────┘
```

所以：

```python
print(names[0])  # 张三
print(names[1])  # 李四
print(names[2])  # 王五
```

⚠️ **Python 的索引从 0 开始。**  
你有前端背景的话，这和 JavaScript 数组完全一样：

```javascript
const names = ["张三", "李四", "王五"]
console.log(names[0])  // 张三
```

越界会怎样？

```python
print(names[3])  # IndexError: list index out of range
```

先建立直觉：合法索引范围是 `0` 到 `len(names) - 1`。

#### 负数索引

Python 很方便的一点：可以从右边数。

```python
names = ["张三", "李四", "王五"]
print(names[-1])  # 王五
print(names[-2])  # 李四
```

对照图：

```text
正向：  0      1      2
       张三    李四    王五

反向： -3     -2     -1
       张三    李四    王五
```

口诀：

> `names[-1]` = 最后一个；`names[-2]` = 倒数第二个。

Agent 里超级常见：拿「最近一条消息」就是 `messages[-1]`。

#### 修改元素

列表是**可变的**（mutable）：

```python
names = ["张三", "李四", "王五"]
names[1] = "赵六"
print(names)  # ['张三', '赵六', '王五']
```

和 JS 一样：

```javascript
names[1] = "赵六"
```

#### 添加元素

**`append()`**：在末尾追加一个元素（最常用）。

```python
names = ["张三", "李四"]
names.append("王五")
print(names)  # ['张三', '李四', '王五']
```

对应 JS 的 `push`：

```javascript
names.push("王五")
```

Agent 场景几乎每天都在 append：

```python
messages.append({"role": "assistant", "content": "你好！"})
```

**`insert()`**：指定位置插入。

```python
names = ["张三", "王五"]
names.insert(1, "李四")
print(names)  # ['张三', '李四', '王五']
```

日常更常用 `append`；需要「插到中间」时才用 `insert`。

还有一个相关方法：`extend` 用于追加「另一组」元素：

```python
a = [1, 2]
a.extend([3, 4])
print(a)  # [1, 2, 3, 4]
```

注意别和 `append` 搞混：

```python
a = [1, 2]
a.append([3, 4])
print(a)  # [1, 2, [3, 4]]  ← 多了一个嵌套 list
```

#### 删除元素

**`remove(值)`**：按**值**删除（删第一个匹配项）。

```python
names = ["张三", "李四", "王五"]
names.remove("李四")
print(names)  # ['张三', '王五']
```

如果值不存在会 `ValueError`。不确定时先判断：

```python
if "李四" in names:
    names.remove("李四")
```

**`pop(索引)`**：按**索引**删除，并返回被删掉的值。

```python
names = ["张三", "李四", "王五"]
removed = names.pop(1)
print(removed)  # 李四
print(names)    # ['张三', '王五']
```

不传参数时，默认删最后一个（很像栈的 pop）：

```python
names.pop()  # 删除并返回最后一个
```

#### 长度与成员判断

```python
names = ["张三", "李四", "王五"]
print(len(names))       # 3
print("张三" in names)  # True
print("赵六" in names)  # False
```

对照 JS：

| 需求 | Python | JavaScript |
| --- | --- | --- |
| 长度 | `len(names)` | `names.length` |
| 是否包含 | `"张三" in names` | `names.includes("张三")` |

也可以直接写进条件：

```python
if "张三" in names:
    print("张三在列表中")
```

#### 切片（list 版入门）

切片非常重要。先用列表把它吃透；§7 还会补 `step`、反转等技巧。

```python
numbers = [10, 20, 30, 40, 50]
print(numbers[1:4])  # [20, 30, 40]
```

规律：

```python
list[start:stop]   # 含 start，不含 stop（左闭右开）
```

也就是 `numbers[1:4]` 取的是索引 `1、2、3`，**不包含**索引 `4`。

常用省略写法：

```python
numbers[:3]   # 从开头到索引 3 之前 → [10, 20, 30]
numbers[2:]   # 从索引 2 到末尾     → [30, 40, 50]
numbers[:]    # 浅拷贝整个列表
numbers[-2:]  # 最后两个             → [40, 50]
```

Agent 高频用法：只保留最近 N 条消息：

```python
history = history[-10:]
```

#### 列表 + 循环（先建立组合直觉）

`for` 的正式语法在 §4，但列表真正开始「有用」，往往是和循环一起出现：

```python
names = ["张三", "李四", "王五"]

for name in names:
    print(name)
```

输出：

```text
张三
李四
王五
```

先记住这个分工：

> **列表负责保存一组数据，循环负责逐个处理这些数据。**

以后写后端、数据处理、Agent，这种写法会大量出现。

#### 和 JavaScript 对照（list）

| Python | JavaScript |
| --- | --- |
| `list` | `Array` |
| `append()` | `push()` |
| `pop()` | `pop()` |
| `len(list)` | `array.length` |
| `list[index]` | `array[index]` |
| `x in list` | `array.includes(x)` |
| `for item in list` | `for (const item of array)` |

```python
users = ["Tom", "Jack", "Lucy"]
for user in users:
    print(user)
```

```javascript
const users = ["Tom", "Jack", "Lucy"]
for (const user of users) {
  console.log(user)
}
```

你会发现心智模型非常接近；差异主要在方法名和 `len(...)` 这种函数式写法。

---

### 3.2 tuple：有序、不可变

如果你已经会用 list，tuple 可以先这样理解：

> 长得像 list，但**不能改槽位**的「固定一组值」。

#### 创建与读取

```python
point = (10, 20)
print(point[0])   # 10
print(point[-1])  # 20
```

只有一个元素时，必须加逗号，否则就不是 tuple：

```python
not_tuple = (10)    # 这只是整数 10
a_tuple = (10,)     # 这才是单元素 tuple
```

#### 为什么说「不可变」？

```python
point = (10, 20)
# point[0] = 1  → TypeError：不能改「槽位」本身
```

注意一个反直觉点：

> tuple 不可变 ≠ 里面的对象也不能变。

```python
t = ([],)
t[0].append(1)  # 合法：改的是里面的 list，不是重绑 t[0]
print(t)        # ([1],)
```

#### 解包：一次拆成多个变量

```python
width, height = (1920, 1080)
print(width, height)  # 1920 1080
```

函数返回多个值时，底层其实就是返回 tuple（下一章函数会再用到）：

```python
def split_name(full: str) -> tuple[str, str]:
    first, last = full.split(" ", 1)
    return first, last
```

#### 和 list 怎么选？

- 要改内容、要增删 → `list`
- 表示「一组固定字段」、不想被误改槽位 → `tuple`
- 要当 `dict` 的 key → 通常用 `tuple`（list 不行）

---

### 3.3 dict：键值映射（你最该练熟的）

如果你写过 JS 对象 / JSON，dict 会非常亲切：

> 不是「第几个」，而是「叫什么名字」。

#### 创建与读取

```python
user = {
    "name": "Alice",
    "age": 20,
    "roles": ["admin", "editor"],
}

print(user["name"])  # Alice
```

适合：JSON 对象、配置、一条 tool call、一条 HTTP 响应体。

```python
tool_call = {
    "name": "search",
    "arguments": {"query": "langgraph memory", "top_k": 5},
}
```

#### 写入、修改、判断 key

```python
user["email"] = "a@example.com"  # 没有就新增，有就覆盖
print("age" in user)             # True（查的是 key，不是 value）
```

#### `[]` vs `.get()`：最重要的坑

```python
print(user["email"])        # 有 email 时正常
print(user["phone"])        # KeyError：没有这个 key
print(user.get("phone"))    # None（不会抛错）
print(user.get("phone", "N/A"))  # "N/A"（可给默认值）
```

口诀：

> 确定一定有 → `user["key"]`  
> 不确定 → `user.get("key")` / `user.get("key", default)`

#### 遍历 dict

默认遍历的是 **key**，不是「键值对」：

```python
for key in user:
    print(key, user[key])
```

更常见、也更清楚的写法：

```python
for key, value in user.items():
    print(key, value)
```

只要 key：`user.keys()`；只要 value：`user.values()`。日常优先记 `.items()`。

#### 和 JS 对象对照

| 需求 | Python | JavaScript |
| --- | --- | --- |
| 取值 | `user["name"]` | `user.name` / `user["name"]` |
| 安全取值 | `user.get("x")` | `user.x`（没有是 `undefined`） |
| 是否有 key | `"age" in user` | `"age" in user` / `hasOwnProperty` |
| 遍历键值 | `for k, v in user.items()` | `Object.entries(user)` |

---

### 3.4 set：去重、成员检测快

set 可以先这样理解：

> 一袋不重复的东西；最关心「有没有」，不太关心「第几个」。

#### 创建与去重

```python
tags = {"python", "agent", "rag", "python"}
print(tags)  # 重复的 python 只保留一份；顺序不保证
```

注意：空集合不能写 `{}`（那是空 dict），要写 `set()`：

```python
empty = set()
```

#### 增删与成员判断

```python
tags.add("llm")
tags.discard("rag")      # 没有也不会报错
print("agent" in tags)   # True，平均 O(1)
```

#### 集合运算

```python
a = {"search", "calc"}
b = {"calc", "browse"}

print(a | b)  # 并集：{'search', 'calc', 'browse'}
print(a & b)  # 交集：{'calc'}
print(a - b)  # 差集：{'search'}
```

适合：已调用过的工具名去重、权限集合、停用词表。  
看见「要不要重复」「在不在集合里」——优先想到 `set`。

#### 和 list 怎么选？

| 你更关心…… | 用什么 |
| --- | --- |
| 顺序、第几个、可重复 | `list` |
| 去重、快速判断在不在 | `set` |

---

### 3.5 怎么选容器（速查）

| 需求 | 用什么 | 一句话直觉 |
| --- | --- | --- |
| 有序列表、要改 | `list` | 消息历史、工具列表 |
| 固定一组值、不改 | `tuple` | 坐标、返回多个值 |
| 按名字取值（JSON 味） | `dict` | 配置、tool call、用户对象 |
| 去重 / 快速判断在不在 | `set` | 已调用工具、权限集合 |

---

## 4. 必掌握：控制流

容器负责「存数据」，控制流负责「按条件/按次序处理数据」。  
上一节你已经见过 `for name in names`；这里把它讲透。

### 4.1 为什么需要 if？

现实逻辑很少只有一条路。例如 Agent 调工具后：

```text
成功 → 把结果写进消息历史
重试 → 再调一次
失败 → 记录日志并停止
```

这就需要分支。

### 4.2 if / elif / else

```python
status = "error"

if status == "ok":
    print("继续")
elif status == "retry":
    print("重试")
else:
    print("失败，记录日志")
```

执行规则：

1. 先看 `if`，成立就进这个块，后面的 `elif/else` 都跳过
2. 不成立再看下一个 `elif`
3. 都不成立才走 `else`（`else` 可省略）

条件部分用的就是 §2.9 的比较运算符，以及 §2.6 的真假值：

```python
score = 75

if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("不及格")
```

#### 缩进就是代码块

Python **没有** `{}`，用缩进表示「属于哪个分支」（通常 4 个空格）：

```python
if True:
    print("在 if 里面")
    print("还在 if 里面")
print("已经出来了")
```

缩进错了，轻则逻辑错，重则直接 `IndentationError`。  
和 JS 对照：

```javascript
if (status === "ok") {
  console.log("继续");
} else if (status === "retry") {
  console.log("重试");
} else {
  console.log("失败");
}
```

Python 把花括号换成了缩进 + `:`。

#### 常见写法：`if` + `in`

```python
role = "user"
if role in {"system", "user", "assistant", "tool"}:
    print("合法角色")
```

### 4.3 for：遍历的主力

多数时候，你不是在「数次数」，而是在「逐个处理容器里的东西」。

```python
tools = ["search", "calc", "read_file"]

for tool in tools:
    print(tool)
```

输出：

```text
search
calc
read_file
```

心智模型：

```text
取出 tools[0] → 赋给 tool → 执行循环体
取出 tools[1] → 赋给 tool → 执行循环体
取出 tools[2] → 赋给 tool → 执行循环体
结束
```

#### 需要下标时用 `enumerate`

```python
for i, tool in enumerate(tools):
    print(i, tool)
# 0 search
# 1 calc
# 2 read_file
```

有 JS 背景可以这样映射：

| Python | JavaScript |
| --- | --- |
| `for x in arr:` | `for (const x of arr)` |
| `for i, x in enumerate(arr):` | `arr.forEach((x, i) => ...)` |
| 少写 `for (let i=0; i<n; i++)` | 经典下标循环 |

#### 遍历 dict

```python
tool_call = {
    "name": "search",
    "arguments": {"query": "RAG", "top_k": 5},
}

for key, value in tool_call["arguments"].items():
    print(key, value)
```

只写 `for key in tool_call:` 默认遍历的是 key——这点 §3.3 提过，这里再强调一次。

#### for + if：筛选

```python
scores = [88, 59, 92, 45, 76]
for score in scores:
    if score >= 60:
        print(score)
```

这就是「列表负责存，循环负责处理，if 负责过滤」。

### 4.4 while：少用，但要会

`while` 在「不知道要循环几次、只知道停止条件」时有用：

```python
retries = 3
while retries > 0:
    print("尝试调用 API")
    retries -= 1
```

流程：

```text
retries=3 → 打印 → retries=2
retries=2 → 打印 → retries=1
retries=1 → 打印 → retries=0
retries=0 → 条件不成立 → 结束
```

⚠️ 忘记修改循环变量，就会变成死循环。

Agent 的「最多循环 N 轮 tool calling」更常见、也更安全的是：

```python
max_steps = 5
for _ in range(max_steps):
    ...
```

`_` 表示「这个变量我不用，只是要循环 N 次」。  
比裸 `while True` 更安全——天然带上限。

### 4.5 break / continue

```python
docs = ["a", "", "b", None, "c"]
cleaned = []

for doc in docs:
    if doc is None:
        continue          # 跳过本次，进入下一轮
    if doc == "":
        continue
    cleaned.append(doc)
    if len(cleaned) >= 2:
        break             # 立刻结束整个 for
```

结果：`cleaned == ["a", "b"]`（遇到第 2 个有效文档就停，后面的 `"c"` 不会处理）。

口诀：

- `continue`：跳过**这一轮**剩下的代码
- `break`：结束**整个**循环

写复杂逻辑时，优先「不满足条件就 skip / return」，而不是层层嵌套 `if`。

### 4.6 range：按次数循环

```python
for i in range(3):         # 0, 1, 2
    print(i)

for i in range(1, 4):      # 1, 2, 3
    print(i)

for i in range(0, 10, 2):  # 0, 2, 4, 6, 8
    print(i)
```

记住：`range(start, stop)` 的 `stop` **不含**。和切片一样，都是「左闭右开」。

什么时候用 `for x in list`，什么时候用 `range`？

| 你想…… | 用什么 |
| --- | --- |
| 逐个处理已有列表 | `for x in items` |
| 单纯重复 N 次 / 需要数字序列 | `for i in range(n)` |

---

## 5. 必掌握：推导式（List / Dict Comprehension）

推导式用来把「循环 + 过滤 + 转换」写成更短、更清晰的表达。  
有 JS 经验可以把它想成更强、更紧凑的 `map` + `filter`。

### 5.1 为什么需要推导式？

上一节你已经会写：

```python
scores = [88, 59, 92, 45, 76]
passed = []
for score in scores:
    if score >= 60:
        passed.append(score)
```

这种「新建一个列表 → for → if → append」在 Python 里太常见了，所以有了缩写。

### 5.2 列表推导式：从长写法到短写法

先看完整版：

```python
users = [
    {"name": "Alice", "age": 20},
    {"name": "Bob", "age": 15},
    {"name": "Carol", "age": 25},
]

adult_names = []
for u in users:
    if u["age"] >= 18:
        adult_names.append(u["name"])
```

同一件事，推导式写成：

```python
adult_names = [u["name"] for u in users if u["age"] >= 18]
# ["Alice", "Carol"]
```

#### 怎么读？建议拆成三步

```text
[  u["name"]   for u in users   if u["age"] >= 18 ]
   ↑ 转换         ↑ 遍历            ↑ 过滤（可省略）
```

也可以只做转换、不做过滤：

```python
names = [u["name"] for u in users]
# ["Alice", "Bob", "Carol"]
```

或只做过滤：

```python
adults = [u for u in users if u["age"] >= 18]
```

#### Agent 场景

从检索结果里抽出高分正文：

```python
chunks = [
    {"text": "hello", "score": 0.9},
    {"text": "world", "score": 0.4},
]
high = [c["text"] for c in chunks if c["score"] >= 0.5]
# ["hello"]
```

### 5.3 字典推导式

当你已经有一批 key，想批量生成「key → 配置」：

```python
names = ["search", "calc"]
tool_map = {name: {"enabled": True} for name in names}
# {"search": {"enabled": True}, "calc": {"enabled": True}}
```

读法同样是：

```text
{  name: {"enabled": True}   for name in names }
   ↑ 每个 key 对应的 value      ↑ 遍历
```

再比如：把分数列表变成「索引 → 分数」：

```python
scores = [88, 92, 76]
index_map = {i: s for i, s in enumerate(scores)}
# {0: 88, 1: 92, 2: 76}
```

### 5.4 和 JS 对照

```javascript
const adultNames = users
  .filter((u) => u.age >= 18)
  .map((u) => u.name);
```

```python
adult_names = [u["name"] for u in users if u["age"] >= 18]
```

一件事一行搞定；但代价是「太长会难读」。

### 5.5 什么时候不要用推导式

- 逻辑超过两行条件、嵌套很深 → 写回普通 `for`，可读性优先
- 有副作用（打印、写文件、发请求）→ 不要塞进推导式
- 你自己都读不顺 → 说明该拆开了

推导式是「表达转换」，不是「塞任何循环」的地方。

---

## 6. 必掌握：文件读写

程序不能永远只活在内存里。Agent 经常要：

```text
读提示词模板 / 配置
写会话历史
存检索结果、评测样本
```

所以文件读写是必掌握。

### 6.1 为什么推荐 `with open`？

最基本的写文件：

```python
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("first line\n")
    f.write("second line\n")
```

读全部：

```python
with open("notes.txt", "r", encoding="utf-8") as f:
    content = f.read()
print(content)
```

按行读：

```python
with open("notes.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
# lines 是 list[str]，通常每行末尾带 \n
```

逐行处理（大文件更省内存）：

```python
with open("notes.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
```

#### 模式字符先记三个

| 模式 | 含义 |
| --- | --- |
| `"r"` | 读（文件必须存在） |
| `"w"` | 写（文件不存在就创建；**存在则清空重写**） |
| `"a"` | 追加到末尾 |

#### 为什么要 `with`？

`with` 会在代码块结束时**自动关闭文件**，即使中途出错也一样。  
后面「上下文管理器」章会讲原理；现在先当成固定写法记住：

```python
with open(...) as f:
    ...
# 离开这里后，文件已经关好了
```

#### 务必写 `encoding="utf-8"`

Windows 上默认编码不一定是 UTF-8。显式写上，能少很多乱码：

```python
with open("notes.txt", "r", encoding="utf-8") as f:
    ...
```

### 6.2 更现代：`pathlib`

工程代码里更推荐 `pathlib`：路径对象比裸字符串好用，跨 Windows / macOS 也更省心。

```python
from pathlib import Path

path = Path("notes.txt")
path.write_text("hello\n", encoding="utf-8")
text = path.read_text(encoding="utf-8")
print(text)
```

路径拼接用 `/`（不是字符串加号）：

```python
data_dir = Path("data")
file_path = data_dir / "messages.json"
print(file_path)  # data/messages.json（Windows 上显示也可能是反斜杠，但用法一样）
```

常用判断：

```python
if file_path.exists():
    print("文件在")
```

对照直觉：

| 需求 | `open` | `pathlib` |
| --- | --- | --- |
| 读文本 | `f.read()` | `path.read_text(...)` |
| 写文本 | `f.write(...)` | `path.write_text(...)` |
| 拼路径 | 字符串拼接（易错） | `dir / "a.json"` |

两种都会一点；新代码优先 `pathlib`。

### 6.3 读写 JSON（超高频）

Agent 的会话历史、工具定义、评测数据集，大量都是 JSON 文件。

```python
import json
from pathlib import Path

messages = [
    {"role": "user", "content": "你好"},
]

path = Path("messages.json")

# Python 对象 → JSON 字符串 → 写入文件
path.write_text(
    json.dumps(messages, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

# 读回：文件 → JSON 字符串 → Python 对象
loaded = json.loads(path.read_text(encoding="utf-8"))
print(loaded[0]["role"])  # user
```

两个参数务必记住：

1. **`ensure_ascii=False`**：否则中文会变成 `\u4f60\u597d`，人难看、日志也难看
2. **`indent=2`**：让文件可读；调试时很重要

`json.dumps` / `json.loads` 处理的是**字符串**；  
若直接对文件对象，也可以用 `json.dump` / `json.load`（多一个字母 p）：

```python
with path.open("w", encoding="utf-8") as f:
    json.dump(messages, f, ensure_ascii=False, indent=2)

with path.open("r", encoding="utf-8") as f:
    loaded = json.load(f)
```

两种都对；先任选一种练熟即可。

### 6.4 最小心智模型

```text
内存里的 list/dict
    ↓ json.dumps / 直接写文本
磁盘上的文件
    ↓ json.loads / read_text
内存里的 list/dict
```

先把「往返读得回来、中文不乱码」做稳，再谈更复杂的存储。

---

## 7. 建议掌握：切片技巧

§3.1 已经讲过 list 切片入门：`list[start:stop]`（含 start，不含 stop）。  
这里补三件「进阶但很实用」的事。

### 7.1 完整形态：`start:stop:step`

```python
nums = [0, 1, 2, 3, 4, 5]

nums[1:4]      # [1, 2, 3]   ← 你已经会了
nums[::2]      # [0, 2, 4]   ← 每隔一个取一个
nums[::-1]     # [5, 4, 3, 2, 1, 0]  ← 反转
```

`step` 为负数时从右往左走；最常见就是 ` [::-1]` 反转。

### 7.2 Agent / 后端高频用法

```python
# 只保留最近 10 条消息，防止 prompt 爆掉
history = history[-10:]

# 复制一份 list（浅拷贝）
copy = history[:]
```

记住：`history[-10:]` 和 `history[:]` 比死背一堆切片组合更值得先练熟。

### 7.3 字符串也能切片

```python
"hello"[1:4]   # "ell"
"hello"[-2:]   # "lo"
```

list / str / tuple 都支持同一套切片语法；先在 list 上练熟，再迁移即可。

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
看见「按 score 从高到低排」，就想到 `sorted(..., key=..., reverse=True)`。

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
2. **`dict` 的 key 必须可哈希**  
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
6. **把 JS 的 `===` 惯性带过来**  
   Python 用 `==` 比内容，`is` 比身份（几乎只用于 `None`）。
7. **字符串看起来像数字，但还是字符串**  
   `"10" + "20"` 得到 `"1020"`；要算数先 `int()` / `float()`。

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

这里已经能看到一条真实流水线的影子：

```text
原始数据
  ↓ 清洗 / 过滤 / 去重
  ↓ 排序 / 截断
  ↓ 拼进 prompt
  ↓ 写入文件
```

这很接近 RAG 里「检索后处理」的一小段。

---

## 12. 练习指引

请打开并完成：

`[exercises/01-python-basics/01-syntax-basics.md](../../exercises/01-python-basics/01-syntax-basics.md)`

建议代码位置（可自建）：

```text
playground/01-python-basics/01-syntax-basics/
```

完成标准以练习文档中的验收清单为准。  
先按自己的理解写出来即可，不必一开始就追求「标准答案长相」。

---

## 13. 小结与下一站

### 你现在应该掌握的心智模型

```text
值有类型 → 放进合适容器 → 用控制流处理 → 必要时读写文件
```

### 自检清单

- [ ] 能说明 `=` 与 `==`、`/` 与 `//` 的区别
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
