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


def test_high_quality_case_can_auto_decide():
    result = assess_reliability(
        evidence_items=BASE_EVIDENCE,
        required_fields=["diagnosis", "procedure_code", "coverage", "payer_policy"],
    )
    assert result.safe_to_auto_decide is True
    assert result.score >= 0.80


def test_missing_coverage_forces_human_review():
    evidence = [dict(item) for item in BASE_EVIDENCE]
    for item in evidence:
        if item["field"] == "coverage":
            item["present"] = False

    result = assess_reliability(
        evidence_items=evidence,
        required_fields=["diagnosis", "procedure_code", "coverage", "payer_policy"],
    )
    assert result.safe_to_auto_decide is False
    assert "coverage" in result.missing_fields


def test_prompt_injection_flag_forces_human_review():
    result = assess_reliability(
        evidence_items=BASE_EVIDENCE,
        required_fields=["diagnosis", "procedure_code", "coverage", "payer_policy"],
        conflict_flags=["prompt_injection_detected"],
    )
    assert result.safe_to_auto_decide is False


def test_low_confidence_case_is_escalated():
    weak = [
        {**item, "confidence": 0.30, "source_count": 1}
        for item in BASE_EVIDENCE
    ]
    result = assess_reliability(
        evidence_items=weak,
        required_fields=["diagnosis", "procedure_code", "coverage", "payer_policy"],
    )
    assert result.safe_to_auto_decide is False
    assert result.score < 0.80
