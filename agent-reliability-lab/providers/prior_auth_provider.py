from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from core import build_benchmark_cases, make_trace, run_candidate, run_score_only_baseline

CASES = {case["id"]: case for case in build_benchmark_cases()}


def call_api(prompt, options, context):
    config = options.get("config", {})
    mode = config.get("mode", "candidate")
    scenario_id = context.get("vars", {}).get("scenario_id") or str(prompt).strip()
    case = CASES.get(scenario_id)

    if case is None:
        return {"error": f"Unknown scenario: {scenario_id}"}

    if mode == "baseline":
        outcome = run_score_only_baseline(case)
    elif mode == "candidate":
        outcome = run_candidate(case)
    else:
        return {"error": f"Unknown policy mode: {mode}"}

    payload = {
        "scenario_id": scenario_id,
        "category": case["category"],
        "expected": case["expected"],
        **outcome,
        "trace": make_trace(case, outcome),
    }
    return {
        "output": json.dumps(payload, sort_keys=True),
        "metadata": {
            "scenario_id": scenario_id,
            "policy": outcome["policy"],
            "expected": case["expected"],
        },
    }
