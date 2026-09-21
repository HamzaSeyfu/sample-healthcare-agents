# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Reliability gate for prior-authorization decisions.

This module adds a deterministic human-review layer in front of automatic
authorization decisions. It does not replace clinical or payer-policy logic.
Instead, it inspects the quality and consistency of the evidence used to make
a decision and decides whether automation is safe enough to proceed.
"""

from dataclasses import dataclass, asdict
from typing import Iterable


CRITICAL_FLAGS = {
    "missing_coverage",
    "missing_policy",
    "missing_patient",
    "conflicting_identity",
    "conflicting_policy",
    "prompt_injection_detected",
}

DECISION_CRITICAL_FIELDS = {
    "diagnosis",
    "procedure_code",
    "coverage",
    "payer_policy",
}


@dataclass(frozen=True)
class ReliabilityAssessment:
    safe_to_auto_decide: bool
    score: float
    reasons: list[str]
    missing_fields: list[str]
    conflict_flags: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def assess_reliability(
    *,
    evidence_items: Iterable[dict],
    required_fields: Iterable[str],
    conflict_flags: Iterable[str] = (),
    min_score: float = 0.80,
) -> ReliabilityAssessment:
    """Assess whether a prior-auth case should be automated or escalated.

    Each evidence item may contain:
      - field: logical field name
      - present: bool
      - source_count: int
      - confidence: float in [0, 1]

    The score combines completeness, confidence, and corroboration. Any
    critical conflict forces human review regardless of score.
    """

    evidence = list(evidence_items)
    required = list(dict.fromkeys(required_fields))
    flags = sorted(set(conflict_flags))

    by_field = {item.get("field"): item for item in evidence if item.get("field")}
    missing = [
        field
        for field in required
        if not by_field.get(field, {}).get("present", False)
    ]

    confidence_values = []
    corroboration_values = []

    for field in required:
        item = by_field.get(field, {})
        if not item.get("present", False):
            continue

        confidence = float(item.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
        confidence_values.append(confidence)

        source_count = int(item.get("source_count", 1))
        corroboration_values.append(1.0 if source_count >= 2 else 0.5)

    completeness = 1.0 if not required else (len(required) - len(missing)) / len(required)
    mean_confidence = (
        sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    )
    mean_corroboration = (
        sum(corroboration_values) / len(corroboration_values)
        if corroboration_values
        else 0.0
    )

    # Weighted for safety: missing required evidence hurts more than weak
    # corroboration, while model/source confidence still matters materially.
    score = round(
        0.50 * completeness + 0.35 * mean_confidence + 0.15 * mean_corroboration,
        4,
    )

    reasons: list[str] = []
    critical_missing = sorted(set(missing) & DECISION_CRITICAL_FIELDS)
    critical_flags = sorted(set(flags) & CRITICAL_FLAGS)

    if critical_missing:
        reasons.append(
            "Critical evidence missing: " + ", ".join(critical_missing)
        )
    if critical_flags:
        reasons.append(
            "Critical reliability flags: " + ", ".join(critical_flags)
        )
    if score < min_score:
        reasons.append(
            f"Reliability score {score:.2f} is below threshold {min_score:.2f}"
        )

    safe = not critical_missing and not critical_flags and score >= min_score

    if safe:
        reasons.append("Evidence quality is sufficient for automated decisioning")

    return ReliabilityAssessment(
        safe_to_auto_decide=safe,
        score=score,
        reasons=reasons,
        missing_fields=missing,
        conflict_flags=flags,
    )
