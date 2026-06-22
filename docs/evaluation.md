# Evaluation

This document captures the current LangSmith baseline for the Week 3 intake orchestrator.

## Baseline Snapshot

- Date of run: June 22, 2026
- LangSmith project: `multi-agent-it-support-intake-eval`
- Dataset version: `intake-routing-golden-v1`
- Target mode: `llm`
- Run count: `30`
- LangSmith experiment link: https://smith.langchain.com/o/8512d3fc-b1cd-4248-a3e7-a219ab23b792/datasets/6663d81d-bd5f-405b-9538-aec25b4d9dba/compare?selectedSessions=9628ce50-16c1-4679-98c0-a7d96afca589

### Metrics

- route_accuracy: `0.8000`
- intake_hold_safety: `0.8667`
- p50_latency_s: `3.1934`
- avg_cost_usd: `0.0006`
- avg_prompt_tokens: `222.7333`
- avg_completion_tokens: `141.5667`
- avg_total_tokens: `364.3000`

### Interpretation

The intake orchestrator routes most cases correctly, but the baseline still has meaningful failures in ambiguous intake and premature handoff behavior. Latency is reasonable for a model-backed decision path, and the cost is low enough to support iterative improvement. The next step is to cluster the failures, apply one targeted change, and rerun the same dataset to measure the delta.

### Failure Clusters

The current baseline failures appear to group into a few repeatable patterns:

1. **Ambiguous intake without enough clarification**
   - Cases where the caller gives a vague complaint, but the agent needs to ask one more question before routing.
   - This is the most likely source of lower `intake_hold_safety`.

2. **Premature routing from identity or greeting signals**
   - Cases where the caller name, role, or a short greeting is treated as enough signal to move out of intake.
   - These are the classic false-positive handoffs the evaluation is designed to catch.

3. **Known incident versus individual issue confusion**
   - Cases where the call should escalate immediately because of a broad outage, but the intake path behaves as if it is an individual support request.
   - These cases usually hurt route accuracy more than cost or latency.

These clusters are the best candidates for a first improvement pass because they are repeatable, user-visible, and directly connected to the scoring metrics.

## How To Re-run

```bash
py scripts/langsmith_baseline.py --mode llm
```

Use `--mode heuristic` only for smoke testing the wiring.
