# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reliability_gate import assess_reliability


BASE_EVIDENCE = [
    {"field": "diagnosis", "present": True, "source_count": 2, "confidence": 0.98},
    {"field": "procedure_code", "present": True, "source_count": 2, "confidence": 0.99},
    {"field": "coverage", "present": True, "source_count": 2, "confidence": 0.97},
    {"field": "payer_policy", "present": True, "source_count": 2, "confidence": 0.96},
]
REQUIRED = ["diagnosis", "procedure_code", "coverage", "payer_policy"]


def assess(evidence=BASE_EVIDENCE, **kwargs):
    return assess_reliability(evidence_items=evidence, required_fields=REQUIRED, **kwargs)


def test_high_quality_case_can_auto_decide():
    result = assess()
    assert result.safe_to_auto_decide is True
    assert result.score >= 0.80


def test_missing_coverage_forces_human_review():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    for item in evidence:
        if item["field"] == "coverage":
            item["present"] = False

    result = assess(evidence)
    assert result.safe_to_auto_decide is False
    assert "coverage" in result.missing_fields


def test_prompt_injection_flag_forces_human_review():
    result = assess(conflict_flags=["prompt_injection_detected"])
    assert result.safe_to_auto_decide is False


def test_low_confidence_case_is_escalated():
    weak = [{**item, "confidence": 0.30, "source_count": 1} for item in BASE_EVIDENCE]
    result = assess(weak)
    assert result.safe_to_auto_decide is False
    assert result.score < 0.80


def test_nan_confidence_fails_closed():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    evidence[0]["confidence"] = float("nan")
    result = assess(evidence)
    assert result.safe_to_auto_decide is False
    assert result.score == result.score  # score itself must never become NaN
    assert any("Malformed reliability evidence: diagnosis" in r for r in result.reasons)


def test_infinite_confidence_fails_closed():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    evidence[1]["confidence"] = float("inf")
    result = assess(evidence)
    assert result.safe_to_auto_decide is False
    assert any("Malformed reliability evidence: procedure_code" in r for r in result.reasons)


def test_non_numeric_confidence_fails_closed_instead_of_crashing():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    evidence[2]["confidence"] = "high"
    result = assess(evidence)
    assert result.safe_to_auto_decide is False
    assert any("Malformed reliability evidence: coverage" in r for r in result.reasons)


def test_negative_source_count_fails_closed():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    evidence[3]["source_count"] = -1
    result = assess(evidence)
    assert result.safe_to_auto_decide is False
    assert any("Malformed reliability evidence: payer_policy" in r for r in result.reasons)


def test_fractional_source_count_fails_closed_instead_of_truncating():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    evidence[0]["source_count"] = 1.5
    result = assess(evidence)
    assert result.safe_to_auto_decide is False
    assert any("Malformed reliability evidence: diagnosis" in r for r in result.reasons)


def test_duplicate_required_field_fails_closed():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    evidence.append({
        "field": "coverage",
        "present": False,
        "source_count": 0,
        "confidence": 0.0,
    })
    result = assess(evidence)
    assert result.safe_to_auto_decide is False
    assert any("Ambiguous duplicate evidence: coverage" in r for r in result.reasons)


def test_duplicate_field_order_cannot_change_automation_decision():
    conflicting_duplicate = {
        "field": "payer_policy",
        "present": False,
        "source_count": 0,
        "confidence": 0.0,
    }
    first = assess([conflicting_duplicate, *[dict(item) for item in BASE_EVIDENCE]])
    last = assess([*[dict(item) for item in BASE_EVIDENCE], conflicting_duplicate])
    assert first.safe_to_auto_decide is False
    assert last.safe_to_auto_decide is False
    assert any("Ambiguous duplicate evidence: payer_policy" in r for r in first.reasons)
    assert any("Ambiguous duplicate evidence: payer_policy" in r for r in last.reasons)


def test_negative_min_score_cannot_disable_global_threshold():
    result = assess(min_score=-1)
    assert result.safe_to_auto_decide is False
    assert any("Invalid reliability configuration: min_score" in r for r in result.reasons)


def test_nan_min_score_fails_closed_with_auditable_reason():
    result = assess(min_score=float("nan"))
    assert result.safe_to_auto_decide is False
    assert any("Invalid reliability configuration: min_score" in r for r in result.reasons)


def test_invalid_field_confidence_floor_cannot_weaken_guardrail():
    weak = [dict(item) for item in BASE_EVIDENCE]
    weak[0]["confidence"] = 0.10
    result = assess(weak, min_field_confidence=-1)
    assert result.safe_to_auto_decide is False
    assert any(
        "Invalid reliability configuration: min_field_confidence" in r
        for r in result.reasons
    )


def test_thresholds_above_one_fail_closed():
    result = assess(min_score=1.01, min_field_confidence=1.01)
    assert result.safe_to_auto_decide is False
    assert any(
        "Invalid reliability configuration: min_score, min_field_confidence" in r
        for r in result.reasons
    )
