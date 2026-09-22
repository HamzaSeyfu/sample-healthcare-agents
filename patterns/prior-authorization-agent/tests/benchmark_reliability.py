# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Synthetic benchmark for the prior-authorization reliability gate.

The benchmark measures selective automation: how often the gate can safely
auto-decide while escalating risky cases to human review.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reliability_gate import assess_reliability

REQUIRED = ["diagnosis", "procedure_code", "coverage", "payer_policy"]


def _evidence(confidence: float = 0.95, source_count: int = 2) -> list[dict]:
    return [
        {"field": field, "present": True, "source_count": source_count, "confidence": confidence}
        for field in REQUIRED
    ]


def build_cases() -> list[dict]:
    cases = []

    # 12 clean, well-corroborated cases expected to remain automated.
    for i in range(12):
        cases.append({
            "id": f"clean_{i:02d}",
            "expected": "auto_decide",
            "evidence": _evidence(confidence=0.90 + (i % 5) * 0.015, source_count=2),
            "flags": [],
        })

    # Missing decision-critical evidence.
    for i, field in enumerate(REQUIRED):
        for variant in range(2):
            evidence = _evidence(confidence=0.96, source_count=2)
            for item in evidence:
                if item["field"] == field:
                    item["present"] = False
                    item["source_count"] = 0
                    item["confidence"] = 0.0
            cases.append({
                "id": f"missing_{field}_{variant}",
                "expected": "human_review",
                "evidence": evidence,
                "flags": [],
            })

    # High-confidence but unsafe conflicts. Score alone must never override these.
    critical_flags = [
        "missing_coverage",
        "missing_policy",
        "conflicting_identity",
        "conflicting_policy",
        "prompt_injection_detected",
    ]
    for flag in critical_flags:
        cases.append({
            "id": f"flag_{flag}",
            "expected": "human_review",
            "evidence": _evidence(confidence=0.99, source_count=3),
            "flags": [flag],
        })

    # Weak extraction confidence / poor corroboration.
    for i, confidence in enumerate([0.20, 0.35, 0.50, 0.60, 0.68]):
        cases.append({
            "id": f"weak_confidence_{i}",
            "expected": "human_review",
            "evidence": _evidence(confidence=confidence, source_count=1),
            "flags": [],
        })

    return cases


def run_benchmark() -> dict:
    cases = build_cases()
    outcomes = []

    for case in cases:
        assessment = assess_reliability(
            evidence_items=case["evidence"],
            required_fields=REQUIRED,
            conflict_flags=case["flags"],
        )
        predicted = "auto_decide" if assessment.safe_to_auto_decide else "human_review"
        outcomes.append({
            "id": case["id"],
            "expected": case["expected"],
            "predicted": predicted,
            "score": assessment.score,
            "correct": predicted == case["expected"],
        })

    total = len(outcomes)
    correct = sum(o["correct"] for o in outcomes)
    review_expected = [o for o in outcomes if o["expected"] == "human_review"]
    review_caught = sum(o["predicted"] == "human_review" for o in review_expected)
    automated = [o for o in outcomes if o["predicted"] == "auto_decide"]
    unsafe_auto = sum(o["expected"] == "human_review" for o in automated)

    return {
        "cases": total,
        "accuracy": round(correct / total, 4),
        "automation_rate": round(len(automated) / total, 4),
        "human_review_recall": round(review_caught / len(review_expected), 4),
        "unsafe_auto_decisions": unsafe_auto,
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    report = run_benchmark()
    print(json.dumps(report, indent=2))
