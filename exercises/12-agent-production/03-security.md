# 练习：Agent Security

> 对应章节：[`docs/12-agent-production/03-security.md`](../../docs/12-agent-production/03-security.md)  
> 建议时间：60～90 分钟  
> 难度：★★★★★

## 目标

做最小安全护栏：注入样例检测、工具 ACL、敏感信息脱敏。

## 任务清单

### A. Prompt Injection 样例集（必做）

在 `playground/12-agent-production/security/injection_cases.md` 列出 ≥6 条攻击样例（中文即可），例如：

- 忽略上文指令
- 假装系统管理员
- 要求泄露系统 Prompt
- 诱导执行危险工具

对每条标注：期望行为（拒绝 / 不执行工具 / 不泄露）。

### B. 工具 ACL + 参数级授权（必做）

实现：

```python
def authorize(role: str, tool: str, args: dict) -> tuple[bool, str]: ...
```

至少覆盖：

1. 工具名白名单（`viewer` 不能调 `shell` / `delete_file`）  
2. `fetch_url`：仅允许白名单 host  
3. `read_file`（若有）：路径前缀限制，拒绝 `..`  

Agent 在真正调用工具前必须过 ACL；拒绝时返回明确错误，不得静默跳过审计。附单测。

### C. 脱敏（必做）

写 `redact(text: str) -> str`：

- 手机号、邮箱、疑似 API Key（如 `sk-...`）打码
- 用于日志与部分对外响应

附 ≥5 条单测。

### D. 沙箱边界说明（建议）

写一页 `sandbox_notes.md`：你当前工具哪些有副作用、如何限制路径/超时/参数白名单。

## 验收标准

- [ ] 注入样例 + 期望行为文档齐全
- [ ] ACL 有测试且默认拒绝未知工具
- [ ] redact 有测试
- [ ] 危险操作有明确拒绝路径

## 提示

- 「检测」不等于「万能」；ACL + 最小权限比纯关键词过滤更重要
- 不要在练习里实现真实破坏性操作
