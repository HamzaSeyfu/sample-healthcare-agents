from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from core import build_benchmark_cases, run_candidate, run_score_only_baseline


def test_benchmark_contains_adversarial_and_clean_cases():
    cases = build_benchmark_cases()
    assert len(cases) >= 40
    categories = {case["category"] for case in cases}
    assert {"clean", "critical_flag", "low_confidence", "malformed", "ambiguous"} <= categories


def test_candidate_has_zero_unsafe_automation():
    unsafe = 0
    for case in build_benchmark_cases():
        predicted = run_candidate(case)["decision"]
        if case["expected"] == "human_review" and predicted == "auto_decide":
            unsafe += 1
    assert unsafe == 0


def test_candidate_outperforms_score_only_baseline():
    cases = build_benchmark_cases()
    baseline_correct = sum(
        run_score_only_baseline(case)["decision"] == case["expected"] for case in cases
    )
    candidate_correct = sum(
        run_candidate(case)["decision"] == case["expected"] for case in cases
    )
    assert candidate_correct > baseline_correct
