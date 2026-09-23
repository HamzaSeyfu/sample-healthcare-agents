# Prior Authorization Reliability Gates

This contribution adds a deterministic **human-review gate** to the prior
authorization workflow.

The original agent can gather evidence, evaluate payer policy, and generate
FHIR PAS resources. This layer answers a different question:

> Is the evidence quality strong enough for an automated authorization decision,
> or should the case be escalated to a human reviewer?

## Why this matters

An AI system can produce a syntactically valid decision while still relying on
missing, contradictory, weak, malformed, or adversarial evidence. In healthcare
workflows, that distinction matters more than raw response quality.

The gate scores:

- required-field completeness;
- confidence of extracted evidence;
- corroboration across multiple sources;
- critical conflicts such as identity mismatch or contradictory payer policy;
- explicit safety signals such as detected prompt injection.

## Normalized evidence contract

The gate expects **one normalized item per logical field**. Each present item
contains a finite confidence in `[0, 1]` and a non-negative integer
`source_count`. Multiple underlying records or documents should be reconciled
upstream and represented through `source_count`; they should not be passed as
multiple items with the same logical field name.

This distinction is deliberate. Silently choosing the first or last duplicate
could make an automation decision depend on input ordering and hide conflicting
evidence. Duplicate required fields therefore fail closed and are routed to
human review. Malformed confidence/source-count values also fail closed.

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

Hard safety conditions override the aggregate score. A high score cannot make a
case eligible for automatic decisioning when critical evidence is missing,
malformed, duplicated ambiguously, below the field confidence floor, or carries
a critical reliability flag.

## Test coverage

The included tests cover:

- high-quality evidence that can proceed automatically;
- missing critical coverage evidence;
- prompt-injection safety flags;
- low-confidence evidence requiring escalation;
- non-finite and non-numeric confidence values;
- negative and fractional source counts;
- ambiguous duplicate required fields, including order independence.

The synthetic scenarios in `tests/reliability_scenarios.json` provide a small
seed dataset for future selective-accuracy and abstention experiments.
