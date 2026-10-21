# B1. 函数定义与返回值：消息工厂
def create_message(role: str, content: str, *, name: str | None = None) -> dict:
    returnObj = {}
    # 仅当 name is not None 时加入 "name" 字段
    if name is not None:
        returnObj["name"] = name
    # content 先 .strip()；若 strip 后为空，抛出 ValueError("content empty")
    contentCleaned = content.strip()
    if not contentCleaned:
        raise ValueError("content empty")
    returnObj["content"] = contentCleaned
    # role 只允许："system" / "user" / "assistant" / "tool"，否则抛出 ValueError
    if role not in ["system", "user", "assistant", "tool"]:
        raise ValueError(f"Invalid role: {role}")
    returnObj["role"] = role
    return returnObj

print(create_message("user", "Hello, world!"))
print(create_message("user", "Hello, world!", name="John"))
try:
    print(create_message("worker", "Hello, world!", name="John"))
except ValueError as e:
    print(e)
try:
    print(create_message("user", "   ", name="John"))
except ValueError as e:
    print(e)
print(create_message("user", "Hello, world!", name="John"))



# B2. *args / **keywords：工具调用构建与转发
def build_tool_call(name: str, **arguments) -> dict:
    ### 返回 { "name": name, "arguments": arguments } ###
    return {
        "name": name,
        "arguments": arguments, # arguments 就是一个 dict
    }

def run_tool(tool_call: dict, registry: dict) -> dict:
    ###
    按 registry 查找并调用工具
    - 成功：
    { "name": name, "result": ..., "ok": True }
    - 失败：
    { "name": name, "result": ..., "ok": False }
    ###
    name = tool_call["name"]
    arguments = tool_call.get("arguments", {})

    # 工具不存在
    fn = registry.get(name)
    if fn is None:
        return {
            "name": name,
            "result": f"{name} 未找到（未注册）",
            "ok": False,
        }
    
    # 工具存在或异常
    try:
        result = fn(**arguments)
        return {
            "name": name,
            "result": result,
            "ok": True,
        }
    except Exception as e:
        return {
            "name": name,
            "result": str(e),
            "ok": False,
        }

# 案例工具
def search(query: str, top_k: int = 5) -> list[str]:
    return [f"doc:{query}:{i}" for i in range(top_k)]

def calc(expression: str) -> float:
    # 极简安全实现：只认白名单表达式，避免 eval
    table = {"1+2": 3.0, "10/2": 5.0, "3*4": 12.0}
    if expression not in table:
        raise ValueError(f"Invalid expression: {expression}")
    return table[expression]

# 工具注册
registry = {
    "search": search,
    "calc": calc,
}

# 成功
call1 = build_tool_call("search", query="RAG", top_k=3)
assert run_tool(call1, registry)["ok"] is True
assert run_tool(call1, registry)["result"] == ["doc:RAG:0", "doc:RAG:1", "doc:RAG:2"]

# 未知工具
call2 = build_tool_call("browse", url="https://x")
assert run_tool(call2, registry)["ok"] is False

# 工具抛错
call3 = build_tool_call("calc", expression="1/0")
assert run_tool(call3, registry)["ok"] is False



# B3. 作用域与闭包：计数器与限流器
from collections.abc import Callable
# 实现 make_counter(start: int = 0)，返回一个无参函数；每调用一次返回递增后的值
def make_counter(start: int = 0) -> Callable[[], int]:
    count = start
    def fn() -> int:
        nonlocal count
        count += 1
        return count
    return fn
# 实现 make_rate_limiter(max_calls: int)，返回函数 allow() -> bool：
# - 前 max_calls 次调用返回 True
# - 之后返回 False
# - 内部用闭包计数（需要 nonlocal）
def make_rate_limiter(max_calls: int) -> Callable[[], bool]:
    count = 0
    def fn() -> bool:
        nonlocal count
        count += 1
        return count <= max_calls
    return fn



# B4. lambda 与排序
