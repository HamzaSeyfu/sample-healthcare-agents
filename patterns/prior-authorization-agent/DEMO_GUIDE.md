# Prior Authorization Reliability Gate — Demo Guide

🔗 **Live demo:** https://prior-auth-reliability-demo.vercel.app/

This guide explains the interactive demo for the reliability and human-review contribution added to the prior-authorization agent.

## Quick walkthrough

1. Select a scenario.
2. Review or edit evidence presence, confidence, and source count.
3. Toggle critical reliability flags if needed.
4. Adjust the automation threshold.
5. Click **Evaluate reliability**.
6. Inspect the decision, score, metrics, audit trace, and JSON output.

## Recommended scenarios

| Scenario | Expected outcome | Why |
|---|---|---|
| Clean MRI request | SAFE TO AUTO-DECIDE | Complete, high-confidence, corroborated evidence |
| Missing coverage | HUMAN REVIEW REQUIRED | Critical evidence is absent |
| Conflicting payer policy | HUMAN REVIEW REQUIRED | Hard conflict blocks automation |
| Injected clinical note | HUMAN REVIEW REQUIRED | Prompt-injection flag forces escalation |
| Low-confidence extraction | HUMAN REVIEW REQUIRED | Required evidence is below confidence floor |

## What this contribution adds

- Deterministic reliability scoring
- Human-review escalation
- Critical missing-evidence checks
- Low-confidence safeguards
- Conflict and prompt-injection flags
- Synthetic benchmark scenarios
- CI tests for unsafe automation
- Structured, auditable decision output
- Interactive browser demo

## Reliability policy

The global score combines:

- 50% completeness
- 35% mean evidence confidence
- 15% corroboration

However, hard safety conditions override the global score. A case cannot be automatically decided if a critical field is missing, a critical conflict is present, or a required field is below the configured confidence floor.

## Architecture

```text
Clinical + payer evidence
          ↓
AI-assisted extraction
          ↓
Deterministic reliability gate
      ↙             ↘
Auto decision     Human review
      ↓
FHIR ClaimResponse
```

## Scope and limitations

This demonstration uses **synthetic data only**.

It is intended to demonstrate software-engineering, evaluation, and reliability design. It is not a clinical product and is not intended for real patient data or production medical decision-making.

## Related files

- `reliability_gate.py` — deterministic gate implementation
- `RELIABILITY_GATES.md` — technical design
- `tests/test_reliability_gate.py` — unit tests
- `tests/benchmark_reliability.py` — synthetic selective-automation benchmark
- `demo/` — interactive browser demo
