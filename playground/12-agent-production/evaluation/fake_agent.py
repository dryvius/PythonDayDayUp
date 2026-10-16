"""确定性 Fake Agent：供 harness 离线跑通（对齐 CONVENTIONS 思想）。"""

from __future__ import annotations

from typing import Any


def run_agent(user_input: str, *, role: str = "viewer") -> dict[str, Any]:
    """返回 {answer, trace, usage}，trace 可供 check_trace 使用。"""
    _ = role
    trace: list[dict[str, Any]] = [{"type": "llm", "step": 1}]
    text = user_input.strip()
    compact = text.replace(" ", "")

    # 注入 / 危险意图：拒绝且不调 shell
    if any(k in text for k in ("忽略", "shell", "导出密钥", "rm -rf", "管理员")):
        return {
            "answer": "无法执行该请求：禁止危险工具与越权操作。",
            "trace": trace,
            "usage": {"total_tokens": 20},
        }

    if "密码策略" in text or "Orion" in text:
        trace.append({"type": "tool_call", "name": "search_kb", "step": 1})
        trace.append({"type": "tool_result", "name": "search_kb", "ok": True, "step": 1})
        return {
            "answer": "根据资料[1]，Orion 项目密码至少 12 位并启用 MFA。",
            "trace": trace,
            "usage": {"total_tokens": 80},
        }

    if "财报" in text or "没有的" in text:
        return {
            "answer": "资料不足，我不知道。",
            "trace": trace,
            "usage": {"total_tokens": 30},
        }

    if "RAG" in text or "rag" in text.lower():
        return {
            "answer": "RAG 是检索增强生成：先检索资料再让模型基于材料回答。",
            "trace": trace,
            "usage": {"total_tokens": 40},
        }

    if "3+5*2" in compact:
        trace.append({"type": "tool_call", "name": "calculator", "step": 1})
        trace.append({"type": "tool_result", "name": "calculator", "ok": True, "step": 1})
        trace.append({"type": "llm", "step": 2})
        return {"answer": "计算结果是 13", "trace": trace, "usage": {"total_tokens": 50}}

    if "10-4" in compact:
        trace.append({"type": "tool_call", "name": "calculator", "step": 1})
        trace.append({"type": "tool_result", "name": "calculator", "ok": True, "step": 1})
        trace.append({"type": "llm", "step": 2})
        return {"answer": "计算结果是 6", "trace": trace, "usage": {"total_tokens": 50}}

    return {
        "answer": f"ECHO:{text}",
        "trace": trace,
        "usage": {"total_tokens": 10},
    }
