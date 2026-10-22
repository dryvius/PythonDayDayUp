# 练习：网络与 HTTP

> 对应文档：[`docs/04-systems-basics/02-network-http.md`](../../docs/04-systems-basics/02-network-http.md)  
> 状态：`已完成出题`  
> 建议用时：50～80 分钟（含热身）

## 练习说明

1. 先读完文档「必掌握」：状态码、JSON API、超时直觉；「建议掌握」含重试与幂等。
2. 题目分档：**热身（建议先做） / 基础（必做） / 进阶（建议） / 挑战（可选）**。
3. 建议目录：

```text
playground/04-systems-basics/02-network-http/
```

4. Python ≥ 3.11；不要在日志里打印 Authorization / API Key。
5. 先做题再看文末答案。

---

## 热身题（建议先做）

### W1. 方法直觉

**要求**：Chat Completions 这类「提交一段 messages 让模型生成」通常用哪种 HTTP 方法？

**验收**：答 `POST`。

---

### W2. 401 vs 403

**要求**：各用一句话区分 401 与 403（Agent 调 API 场景）。

**验收**：401 偏「未认证/密钥错」；403 偏「认证了但没权限」。

---

### W3. 客户端超时 ≠ 408

**要求**：你在 httpx 里设的 `timeout=` 触发后，通常表现为「客户端异常」，还是「HTTP 408 响应」？

**验收**：客户端异常（如 `TimeoutException`）；不要与服务端 408 混为一谈。

---

### W4. 幂等直觉

**要求**：为什么对「创建工单」这类 POST，盲目重试比 GET 更危险？

**验收**：可能重复创建副作用；需要幂等键或业务去重。

---

## 基础题（必做）

### B1. 状态码速查表（书面）

自制表格：`200 / 401 / 403 / 404 / 429 / 500 / 502 / 503`  
每项写：**含义 + Agent 侧第一反应**。

**验收**：`b1_notes.md` 表格完整；429 必须提到退避 / 尊重限流。

---

### B2. 手写 JSON 请求体

构造一个「假 Chat Completions」请求 dict，至少含 `model` 与 `messages`，`json.dumps` 后写到文件，再读回断言结构一致。

**验收**：文件存在；`assert` 验证 `model` 与 `messages` 往返一致。

---

### B3. 解析错误响应

给定假响应：

```python
{"error": {"message": "Rate limit", "type": "rate_limit", "code": 429}}
```

写函数返回 `(code, message)`；再映射成自定义 `RateLimitError`（可极简）。

**验收**：能解析；遇到该结构可 `raise RateLimitError`；有 assert。

---

### B4. Timeout 政策（书面）

写清：

1. 连接超时 vs 读取超时为什么都要关心
2. LLM 调用你会设大概多少秒（给一个合理起点即可）

**验收**：`b4_notes.md` 两问都有完整段落。

---

## 进阶题（建议至少做 1 题）

### A1. 重试决策函数

实现：

```python
def should_retry(status_code: int, method: str) -> bool:
    ...
```

规则自定但要合理，例如：

- `429` / `503` 可重试
- `400` / `401` 不重试
- `POST` 是否重试要在注释里说明（幂等风险）

写若干 assert。

---

### A2. 公开 GET（可选联网）

用 `httpx` 或 `requests` 打 `https://httpbin.org/get`，打印 `status_code`。  
公司网络受限则改用 mock 响应，并注明。

**验收**：有真实 status 或明确的 mock 路径。

---

## 挑战题（可选）

### C1. Tool API 幂等策略

为一个「创建工单」POST 工具写约 10 行方案：幂等键怎么传、重试如何避免重复创建。

**验收**：`c1_notes.md` 有完整方案，不是一句话。

---

## 验收标准（本章通过线）

- [ ] （建议）W1～W2
- [ ] **通过线**：B1～B4 完成
- [ ] （建议）A1 或 A2
- [ ] （可选）C1

---

## 提示与参考答案（先做题再看）

### W1 参考答案

通常用 **POST**（提交 JSON body：model、messages 等）。

### W2 参考答案

- **401**：身份未通过（缺/错 API Key、Bearer 过期）→ 先修密钥，不要盲重试烧配额。  
- **403**：身份可能有效但无权限（scope/ACL）→ 查权限配置，重试通常无意义。

---

### B1 思路 + 参考答案

**`b1_notes.md` 完整参考作答**

```markdown
# B1 状态码速查（Agent 侧）

| 码 | 含义 | Agent 侧第一反应 |
|----|------|------------------|
| 200 | 成功 | 解析 JSON；校验必要字段 |
| 401 | 未认证 | 检查 API Key / Bearer；**不要**盲重试 |
| 403 | 禁止 | 查 ACL/配额权限；通常不重试 |
| 404 | 不存在 | 查 URL/模型名/资源 id；修参数 |
| 429 | 限流 | 退避；尊重 `Retry-After`；降并发 |
| 500 | 服务端错误 | 有限次退避重试；仍失败则报错给用户 |
| 502 | 坏网关 | 常为瞬时；有限退避重试 |
| 503 | 不可用 | 有限退避重试；检查服务状态页 |
```

---

### B2 思路 + 参考答案

```python
# b2_chat_body.py
import json
from pathlib import Path


def build_chat_request(model: str, user_text: str) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0,
    }


def main() -> None:
    req = build_chat_request("gpt-4.1-mini", "what is RAG")
    path = Path("chat_request.json")
    path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["model"] == req["model"]
    assert loaded["messages"] == req["messages"]
    print("ok", path)


if __name__ == "__main__":
    main()
```

---

### B3 思路 + 参考答案

```python
# b3_errors.py
from typing import Any


class RateLimitError(Exception):
    def __init__(self, message: str, code: int = 429) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def parse_error_payload(payload: dict[str, Any]) -> tuple[int, str]:
    err = payload["error"]
    code = int(err["code"])
    message = str(err["message"])
    return code, message


def raise_for_provider_error(payload: dict[str, Any]) -> None:
    code, message = parse_error_payload(payload)
    if code == 429 or err_type_is_rate_limit(payload):
        raise RateLimitError(message, code=code)
    raise RuntimeError(f"provider error {code}: {message}")


def err_type_is_rate_limit(payload: dict[str, Any]) -> bool:
    return payload.get("error", {}).get("type") == "rate_limit"


if __name__ == "__main__":
    sample = {
        "error": {
            "message": "Rate limit",
            "type": "rate_limit",
            "code": 429,
        }
    }
    assert parse_error_payload(sample) == (429, "Rate limit")
    try:
        raise_for_provider_error(sample)
        raise AssertionError("should have raised")
    except RateLimitError as exc:
        assert exc.code == 429
        assert "Rate limit" in exc.message
    print("ok")
```

---

### B4 思路 + 参考答案

**`b4_notes.md` 完整参考作答**

```markdown
# B4 Timeout 政策

## 1. 为什么 connect 与 read 都要关心

- **连接超时（connect）**：控制「多久内必须建连成功」。DNS 失败、防火墙黑洞、对端不接受连接时，如果 connect 不设上限，线程/并发名额会被挂死。Agent 里可设较短（例如 3～10 秒）。
- **读取超时（read）**：控制「两次读到数据之间最多等多久」。LLM 生成可能很慢，流式场景中途也可能长时间无 chunk。read 太短会误杀正常慢请求；太长或永不超时，真故障时会拖垮 worker。

二者解决的故障模式不同：一个偏「根本连不上」，一个偏「连上了但响应拖死」。客户端库超时以异常形式出现，**不等于** HTTP 408。

## 2. LLM 调用的合理起点（示例）

非流式教学起点可设：

- connect：5s
- read：60s～120s（按模型与 max_tokens 调整）

流式可把「首 token」与「chunk 间隔」分开思考；若只有单一 read 超时，应明显长于常见首 token 延迟，并配合整体 deadline。  
重要：超时后是否重试，要结合幂等与是否已产生部分计费/副作用。
```

---

### A1 思路 + 参考答案

```python
# a1_retry.py
def should_retry(status_code: int, method: str) -> bool:
    """
    教学用粗规则：
    - 429/502/503：可重试（需配合退避；429 尊重 Retry-After）
    - 408/504：可谨慎重试
    - 400/401/403/404：不重试（修参数/密钥/权限）
    - POST：仅对明显「可安全重试」的瞬时码返回 True；
      若 POST 会创建资源且服务端无幂等键，调用方必须自行保证不重复下单。
    """
    method = method.upper()
    if status_code in {401, 403, 400, 404}:
        return False
    if status_code in {429, 502, 503}:
        return True
    if status_code in {408, 504}:
        return True
    if status_code >= 500 and method == "GET":
        return True
    # POST 的 500：默认 False，避免重复创建；有幂等键时可在上层打开
    return False


assert should_retry(429, "POST") is True
assert should_retry(503, "GET") is True
assert should_retry(401, "POST") is False
assert should_retry(400, "POST") is False
assert should_retry(500, "POST") is False
assert should_retry(500, "GET") is True
print("ok")
```

---

### A2 思路 + 参考答案

**联网版**

```python
# a2_http_get.py
import httpx


def main() -> None:
    r = httpx.get("https://httpbin.org/get", timeout=10.0)
    print("status_code =", r.status_code)
    assert r.status_code == 200


if __name__ == "__main__":
    main()
```

**无网 mock 版**

```python
from unittest.mock import Mock


def main() -> None:
    # 网络不可用时的替代路径
    response = Mock(status_code=200)
    print("status_code =", response.status_code, "(mocked)")
    assert response.status_code == 200


if __name__ == "__main__":
    main()
```

---

### C1 思路 + 参考答案

**`c1_notes.md` 完整参考作答**

```markdown
# C1 创建工单 POST 的幂等策略

1. **客户端生成幂等键**：每次「用户意图上的一次创建」生成 `Idempotency-Key`（UUID），同一意图重试复用同一键，新意图用新键。
2. **传递方式**：HTTP 头 `Idempotency-Key: <uuid>`，或 body 字段 `client_request_id`（与后端约定一种即可）。
3. **服务端行为**：若键已见过，直接返回第一次的工单 id / 结果，不再新建。
4. **重试条件**：仅对连接失败、429/502/503 等瞬时错误重试；对 400 校验失败不重试。
5. **退避**：指数退避 + 抖动；尊重 `Retry-After`。
6. **超时后的不确定**：若请求可能已到达服务端但客户端超时，必须用同一幂等键重放，而不是换新键再 POST。
7. **日志**：记录 `idempotency_key` 与最终 `ticket_id`，不记录 API Key。
8. **Agent 工具层**：把幂等键纳入 tool args 或由运行时注入，避免模型每次乱生成新键导致重复建单。
```

---

### W3 参考答案

库超时一般以**客户端异常**形式抛出（httpx: `TimeoutException`），**不会** magically 变成响应体里的 HTTP 408。  
HTTP 408 是服务端状态码（较少见）；504 则是网关等上游超时——排障用语要分开。

### W4 参考答案

GET 常被假定可安全重试；「创建工单」POST 若已到达服务端但客户端超时，再发一次可能新建第二张单。  
所以要么服务端支持幂等键，要么业务层用 `client_request_id` 去重，否则超时后的重试策略必须保守。

---

### 常见坑（自检清单）

| 错法 | 后果 |
|------|------|
| 401/403 仍疯狂重试 | 烧配额、锁账号、日志爆炸 |
| 429 不退避 / 不理 `Retry-After` | 雪崩式重试，更限流 |
| 超时设成永不 | worker / 线程被拖死 |
| 超时短于正常生成时间 | 误杀慢请求，重试加倍烧 token |
| 把 HTML 错误页当 JSON 解析 | 二次异常掩盖真相 |
| 日志打印 `Authorization` | 密钥泄漏 |

**补充：错误响应转译的最小断言集**

```python
sample_401 = {"error": {"message": "Invalid API key", "type": "auth", "code": 401}}
code, msg = parse_error_payload(sample_401)
assert code == 401
assert "key" in msg.lower() or "Invalid" in msg
```

**补充：假 Chat Completions 最小字段**

```python
req = {
    "model": "gpt-4.1-mini",
    "messages": [{"role": "user", "content": "hi"}],
}
assert "model" in req and isinstance(req["messages"], list)
assert req["messages"][0]["role"] in {"system", "user", "assistant", "tool"}
```

**httpx Timeout 拆分示意（不必联网）**

```python
import httpx

# 连接短、读长：LLM 常见起点
timeout = httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0)
assert timeout.connect == 5.0
assert timeout.read == 60.0
```

---

### 本章速查

| 主题 | 记住 |
|------|------|
| 状态码 | 401 修密钥；429 退避；5xx 有限重试 |
| JSON | dumps/loads 往返要测 |
| 超时 | connect 短、read 按 LLM 加长；库超时 ≠ 408 |
| 重试 | 与幂等绑定；POST 创建尤其危险 |
| 安全 | 日志不打 Authorization / API Key |
