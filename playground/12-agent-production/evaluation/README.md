# Agent Evaluation 最小 harness

对应文档：[`docs/12-agent-production/01-evaluation.md`](../../../docs/12-agent-production/01-evaluation.md)

## 跑起来

```bash
# 全绿跑通
python playground/12-agent-production/evaluation/run_eval.py --write-baseline

# 再次跑并与 baseline 对比
python playground/12-agent-production/evaluation/run_eval.py

# 故意改坏算数 → 应出现 regressions
python playground/12-agent-production/evaluation/run_eval.py --break-calc
```

## 目录

```text
evaluation/
├── cases.jsonl          # 题集（含 safety）
├── fake_agent.py        # 确定性 Agent
├── run_eval.py          # harness 入口
├── baseline.json        # --write-baseline 生成
├── reports/last_report.json
└── README.md
```

Project 5/6 请把 `run_fn` 换成你自己的 Agent，保留同一套 cases / check_* / baseline 约定。
