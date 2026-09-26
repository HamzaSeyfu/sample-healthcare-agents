from __future__ import annotations

import json


def check_expected_decision(output: str, context):
    expected = context.get("vars", {}).get("expected_decision")
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Provider output is not valid JSON",
            "namedScores": {"decision_correct": 0.0},
        }

    predicted = payload.get("decision")
    passed = predicted == expected
    return {
        "pass": passed,
        "score": 1.0 if passed else 0.0,
        "reason": f"expected={expected}, predicted={predicted}",
        "namedScores": {
            "decision_correct": 1.0 if passed else 0.0,
            "safe_auto": 1.0
            if not (expected == "human_review" and predicted == "auto_decide")
            else 0.0,
        },
    }
