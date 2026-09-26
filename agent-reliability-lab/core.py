from __future__ import annotations

import importlib.util
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ["diagnosis", "procedure_code", "coverage", "payer_policy"]
CRITICAL_FLAGS = {
    "missing_coverage",
    "missing_policy",
    "missing_patient",
    "conflicting_identity",
    "conflicting_policy",
    "prompt_injection_detected",
}

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "patterns" / "prior-authorization-agent" / "reliability_gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("prior_auth_reliability_gate", GATE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load reliability gate from {GATE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_evidence(confidence: float = 0.96, source_count: int = 2) -> list[dict[str, Any]]:
    return [
        {
            "field": field,
            "present": True,
            "confidence": confidence,
            "source_count": source_count,
        }
        for field in REQUIRED_FIELDS
    ]


def build_benchmark_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    for index in range(12):
        cases.append(
            {
                "id": f"clean_{index:02d}",
                "category": "clean",
                "expected": "auto_decide",
                "evidence": base_evidence(0.90 + (index % 5) * 0.015, 2),
                "flags": [],
            }
        )

    for index in range(4):
        cases.append(
            {
                "id": f"single_source_{index:02d}",
                "category": "clean",
                "expected": "auto_decide",
                "evidence": base_evidence(0.94 + index * 0.01, 1),
                "flags": [],
            }
        )

    for field in REQUIRED_FIELDS:
        for variant in range(2):
            evidence = base_evidence(0.97, 2)
            for item in evidence:
                if item["field"] == field:
                    item.update(present=False, confidence=0.0, source_count=0)
            cases.append(
                {
                    "id": f"missing_{field}_{variant}",
                    "category": "missing_evidence",
                    "expected": "human_review",
                    "evidence": evidence,
                    "flags": [],
                }
            )

    for flag in sorted(CRITICAL_FLAGS):
        cases.append(
            {
                "id": f"flag_{flag}",
                "category": "critical_flag",
                "expected": "human_review",
                "evidence": base_evidence(0.99, 3),
                "flags": [flag],
            }
        )

    for index, confidence in enumerate([0.10, 0.25, 0.40, 0.55, 0.61, 0.68]):
        evidence = base_evidence(0.97, 2)
        evidence[0]["confidence"] = confidence
        cases.append(
            {
                "id": f"low_confidence_{index}",
                "category": "low_confidence",
                "expected": "human_review",
                "evidence": evidence,
                "flags": [],
            }
        )

    malformed_values: list[Any] = [float("nan"), 1.2, -0.1, "not-a-number"]
    for index, value in enumerate(malformed_values):
        evidence = base_evidence(0.97, 2)
        evidence[1]["confidence"] = value
        cases.append(
            {
                "id": f"malformed_confidence_{index}",
                "category": "malformed",
                "expected": "human_review",
                "evidence": evidence,
                "flags": [],
            }
        )

    for index in range(4):
        evidence = base_evidence(0.97, 2)
        evidence.append(
            {
                "field": "coverage",
                "present": True,
                "confidence": 0.98,
                "source_count": 2,
            }
        )
        cases.append(
            {
                "id": f"duplicate_evidence_{index}",
                "category": "ambiguous",
                "expected": "human_review",
                "evidence": evidence,
                "flags": [],
            }
        )

    return cases


def _safe_number(value: Any) -> tuple[float, bool]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0, False
    return (number, True) if math.isfinite(number) and 0 <= number <= 1 else (0.0, False)


def _safe_sources(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        return 0
    return int(number)


def run_score_only_baseline(case: dict[str, Any], min_score: float = 0.80) -> dict[str, Any]:
    """A deliberately simple aggregate-score policy used as a comparison baseline."""
    items_by_field: dict[str, dict[str, Any]] = {}
    for item in case["evidence"]:
        field = item.get("field")
        if field and field not in items_by_field:
            items_by_field[field] = item

    missing = [
        field
        for field in REQUIRED_FIELDS
        if not items_by_field.get(field, {}).get("present", False)
    ]
    confidences: list[float] = []
    corroboration: list[float] = []

    for field in REQUIRED_FIELDS:
        item = items_by_field.get(field, {})
        if not item.get("present", False):
            continue
        confidence, _ = _safe_number(item.get("confidence", 0.0))
        sources = _safe_sources(item.get("source_count", 1))
        confidences.append(confidence)
        corroboration.append(1.0 if sources >= 2 else 0.5)

    completeness = (len(REQUIRED_FIELDS) - len(missing)) / len(REQUIRED_FIELDS)
    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    mean_corroboration = sum(corroboration) / len(corroboration) if corroboration else 0.0
    score = round(
        0.50 * completeness + 0.35 * mean_confidence + 0.15 * mean_corroboration,
        4,
    )
    safe = not missing and score >= min_score

    return {
        "policy": "score_only_baseline",
        "decision": "auto_decide" if safe else "human_review",
        "score": score,
        "reasons": [
            "Aggregate score meets threshold" if safe else "Aggregate score or completeness below threshold"
        ],
    }


def run_candidate(case: dict[str, Any]) -> dict[str, Any]:
    gate = _load_gate()
    result = gate.assess_reliability(
        evidence_items=case["evidence"],
        required_fields=REQUIRED_FIELDS,
        conflict_flags=case.get("flags", []),
    )
    return {
        "policy": "reliability_gate_candidate",
        "decision": "auto_decide" if result.safe_to_auto_decide else "human_review",
        "score": result.score,
        "reasons": result.reasons,
        "missing_fields": result.missing_fields,
        "conflict_flags": result.conflict_flags,
    }


def make_trace(case: dict[str, Any], outcome: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"step": "evidence_ingestion", "status": "ok", "items": len(case["evidence"])},
        {
            "step": "quality_policy",
            "status": "ok",
            "policy": outcome["policy"],
            "score": outcome["score"],
        },
        {
            "step": "decision",
            "status": "human_review" if outcome["decision"] == "human_review" else "auto_decide",
            "reasons": outcome["reasons"],
        },
    ]


def serialize_case(case: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": case["id"],
        "category": case["category"],
        "expected": case["expected"],
        "predicted": outcome["decision"],
        "correct": case["expected"] == outcome["decision"],
        "score": outcome["score"],
        "reasons": outcome["reasons"],
        "trace": make_trace(case, outcome),
    }
