# Reliability Gate Demo

Interactive static demo for the prior-authorization reliability contribution.

## Run locally

No build step is required.

```bash
cd patterns/prior-authorization-agent/demo
python -m http.server 8000
```

Then open `http://localhost:8000`.

The demo contains **synthetic data only** and mirrors the deterministic scoring
and escalation behavior implemented in `reliability_gate.py`.

## Deployment

The repository includes a GitHub Pages workflow in
`.github/workflows/prior-auth-demo-pages.yml`.

Once GitHub Pages is configured to use **GitHub Actions** as its source, pushes
to `main` publish this directory as a public demo.
