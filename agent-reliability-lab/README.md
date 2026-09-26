# Agent Reliability Lab

**Production-style evaluation and regression testing for AI agents.**

This lab evaluates the reliability layer added to the AWS prior-authorization agent. It is designed around a simple engineering question:

> When should an AI-assisted workflow be allowed to continue automatically, and when must it stop and ask for human review?

The first milestone is intentionally offline and reproducible. It uses synthetic prior-authorization evidence, a deterministic baseline, the current reliability gate, Promptfoo, and CI quality gates. No paid model API is required to reproduce the benchmark.

## What this demonstrates

- **A/B policy evaluation**: score-only baseline vs reliability-gate candidate.
- **44 deterministic scenarios** across clean, missing-evidence, conflict, prompt-injection, low-confidence, malformed and ambiguous inputs.
- **Selective automation metrics**: accuracy, automation rate, human-review recall and unsafe automatic decisions.
- **Promptfoo integration** through a custom Python provider and custom assertion.
- **CI regression gate** that fails if the candidate introduces unsafe automation.
- **Static dashboard** designed to become the public Vercel demo.
- **Audit traces** showing why a case was automated or escalated.

## Current benchmark

| Metric | Score-only baseline | Reliability gate |
|---|---:|---:|
| Scenarios | 44 | 44 |
| Decision accuracy | 54.55% | **100%** |
| Human-review recall | 28.57% | **100%** |
| Automation rate | 81.82% | 36.36% |
| Unsafe automatic decisions | **20** | **0** |

These are **synthetic benchmark results**, not clinical performance claims. The purpose is to test the software policy and regression behavior.

## Why the baseline is useful

The baseline represents a common failure mode: aggregate evidence into one confidence score and automate whenever the score exceeds a threshold.

That looks efficient, but a high average score can hide a critical failure such as:

- conflicting payer policy;
- prompt injection detected upstream;
- a single decision-critical field below its confidence floor;
- duplicate ambiguous evidence;
- malformed evidence values.

The candidate gate treats those conditions as hard stops.

## Architecture

```text
Synthetic scenarios
       │
       ├──────────────► score-only baseline
       │
       └──────────────► reliability-gate candidate
                               │
                               ▼
                         audit trace JSON
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              Promptfoo eval        benchmark.py
                    │                     │
                    └──────────┬──────────┘
                               ▼
                        CI quality gate
                               │
                               ▼
                         static dashboard
```

## Run the benchmark

From the repository root:

```bash
python agent-reliability-lab/scripts/benchmark.py
```

To regenerate the dashboard data:

```bash
python agent-reliability-lab/scripts/benchmark.py \
  --write agent-reliability-lab/dashboard/results.json
```

## Run Promptfoo

Requires Node.js and Python:

```bash
cd agent-reliability-lab
npx promptfoo@latest eval -c promptfooconfig.yaml
```

The Promptfoo suite uses the **candidate policy only** so CI can fail on a real regression. Baseline comparison remains visible in the deterministic benchmark.

## Dashboard

```bash
cd agent-reliability-lab/dashboard
python -m http.server 8080
```

Open http://localhost:8080.

The dashboard is static and therefore deployable to Vercel without a backend. A future live mode can call an actual agent endpoint while retaining the replay mode for recruiter-friendly, deterministic demos.

## Next milestones

- [x] Deterministic A/B benchmark
- [x] Promptfoo Python provider
- [x] Custom decision assertion
- [x] CI regression gate
- [x] Static live-demo shell
- [ ] Add recorded end-to-end agent traces
- [ ] Add tool-call success and citation-support metrics from real traces
- [ ] Add OpenTelemetry spans
- [ ] Deploy dashboard publicly
- [ ] Optional OpenLIT visualization
- [ ] Extract this branch into a dedicated `agent-reliability-lab` repository

## Scope

This project uses **synthetic data only**. It is a software-engineering and evaluation demonstration, not clinical decision support, regulatory validation or a production healthcare system.
