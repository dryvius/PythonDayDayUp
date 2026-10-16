"""最小 Eval harness：cases.jsonl → Fake Agent → report / baseline。

用法（仓库根目录）：
  python playground/12-agent-production/evaluation/run_eval.py
  python playground/12-agent-production/evaluation/run_eval.py --write-baseline
  python playground/12-agent-production/evaluation/run_eval.py --break-calc
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable

from fake_agent import run_agent

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases.jsonl"
REPORTS = ROOT / "reports"
BASELINE = ROOT / "baseline.json"


def check_trace(trace: list[dict], forbidden_tools: set[str], max_llm_calls: int = 8) -> list[str]:
    errors: list[str] = []
    for event in trace:
        if event.get("type") == "tool_call" and event.get("name") in forbidden_tools:
            errors.append(f"forbidden tool: {event['name']}")
    llm_calls = len([e for e in trace if e.get("type") == "llm"])
    if llm_calls > max_llm_calls:
        errors.append(f"too many llm calls: {llm_calls}")
    return errors


def check_answer(answer: str, expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for needle in expected.get("answer_contains") or []:
        if needle not in answer:
            errors.append(f"missing: {needle!r}")
    for needle in expected.get("must_not_contain") or []:
        if needle in answer:
            errors.append(f"forbidden text: {needle!r}")
    if expected.get("must_cite") and "[" not in answer and "来源" not in answer:
        errors.append("missing citation")
    return errors


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


RunFn = Callable[[str], dict[str, Any]]


def run_eval(cases: list[dict[str, Any]], run_fn: RunFn) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        t0 = time.perf_counter()
        out = run_fn(case["input"])
        latency_ms = (time.perf_counter() - t0) * 1000
        expected = case.get("expected") or {}
        forbidden = set(expected.get("forbidden_tools") or [])
        errors = check_answer(out.get("answer") or "", expected)
        errors += check_trace(out.get("trace") or [], forbidden)
        rows.append(
            {
                "id": case["id"],
                "ok": not errors,
                "errors": errors,
                "latency_ms": round(latency_ms, 1),
                "steps": len([e for e in (out.get("trace") or []) if e.get("type") == "llm"]),
                "tokens": (out.get("usage") or {}).get("total_tokens"),
                "tags": case.get("tags") or [],
                "answer": out.get("answer"),
            }
        )
    passed = sum(1 for r in rows if r["ok"])
    return {
        "total": len(rows),
        "passed": passed,
        "accuracy": passed / len(rows) if rows else 0.0,
        "avg_latency_ms": round(sum(r["latency_ms"] for r in rows) / len(rows), 1) if rows else 0.0,
        "avg_steps": round(sum(r["steps"] for r in rows) / len(rows), 2) if rows else 0.0,
        "rows": rows,
    }


def compare_baseline(report: dict[str, Any], baseline_path: Path) -> None:
    if not baseline_path.exists():
        print("no baseline yet; pass --write-baseline after a green run")
        return
    base = json.loads(baseline_path.read_text(encoding="utf-8"))
    print(f"accuracy {report['accuracy']:.2%} (baseline {base.get('accuracy', 0):.2%})")
    base_ok = {r["id"] for r in base.get("rows", []) if r.get("ok")}
    now_fail = [r["id"] for r in report["rows"] if not r["ok"] and r["id"] in base_ok]
    if now_fail:
        print("regressions:", ", ".join(now_fail))
    else:
        print("regressions: (none)")


def broken_calc_agent(user_input: str) -> dict[str, Any]:
    """演示回归：算数题故意答错。"""
    out = run_agent(user_input)
    if "计算" in user_input or "算" in user_input:
        out["answer"] = "计算结果是 0"
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--break-calc", action="store_true", help="故意改坏算数答案以演示回归")
    args = parser.parse_args()

    cases = load_cases(CASES)
    run_fn: RunFn = broken_calc_agent if args.break_calc else run_agent
    report = run_eval(cases, run_fn)

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "last_report.json"
    # 报表可不带完整 answer，此处保留便于排障
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"passed {report['passed']}/{report['total']} accuracy={report['accuracy']:.2%}")
    print(f"avg_steps={report['avg_steps']} avg_latency_ms={report['avg_latency_ms']}")
    for row in report["rows"]:
        if not row["ok"]:
            print(f"  FAIL {row['id']}: {row['errors']}")

    if args.write_baseline:
        # baseline 不存 answer，减小噪音
        slim = {
            **report,
            "rows": [{k: v for k, v in r.items() if k != "answer"} for r in report["rows"]],
        }
        BASELINE.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {BASELINE}")
    else:
        compare_baseline(report, BASELINE)


if __name__ == "__main__":
    main()
