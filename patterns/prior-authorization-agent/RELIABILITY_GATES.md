# Prior Authorization Reliability Gates

This contribution adds a deterministic **human-review gate** to the prior
authorization workflow.

The original agent can gather evidence, evaluate payer policy, and generate
FHIR PAS resources. This layer answers a different question:

> Is the evidence quality strong enough for an automated authorization decision,
> or should the case be escalated to a human reviewer?

## Why this matters

An AI system can produce a syntactically valid decision while still relying on
missing, contradictory, weak, or adversarial evidence. In healthcare workflows,
that distinction matters more than raw response quality.

The gate scores:

- required-field completeness;
- confidence of extracted evidence;
- corroboration across multiple sources;
- critical conflicts such as identity mismatch or contradictory payer policy;
- explicit safety signals such as detected prompt injection.

## Output

The module returns:

- `safe_to_auto_decide`
- `score`
- human-readable `reasons`
- `missing_fields`
- `conflict_flags`

Example:

```json
{
  "safe_to_auto_decide": false,
  "score": 0.71,
  "reasons": [
    "Critical evidence missing: coverage",
    "Reliability score 0.71 is below threshold 0.80"
  ],
  "missing_fields": ["coverage"],
  "conflict_flags": []
}
```

## Design principle

The gate is intentionally deterministic. Model-generated reasoning can still be
used elsewhere in the workflow, but escalation policy should remain explicit,
testable, and auditable.

## Test coverage

The included tests cover:

- high-quality evidence that can proceed automatically;
- missing critical coverage evidence;
- prompt-injection safety flags;
- low-confidence evidence requiring escalation.

The synthetic scenarios in `tests/reliability_scenarios.json` provide a small
seed dataset for future selective-accuracy and abstention experiments.
