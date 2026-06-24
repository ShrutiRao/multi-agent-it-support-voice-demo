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

### Failure Notes Template

Use this when reviewing each failed trace in LangSmith:

| Case ID | Expected | Observed | Why It Failed | Cluster | Fix Idea |
|---|---|---|---|---|---|
| H11 | route_to_verification | ask_clarifying_question | Overly cautious on a specific access issue | Overly cautious ambiguity detection | Treat named resource + recent usage as enough signal to route |

Keep the golden label unchanged unless you decide the label itself was wrong. The note is for pattern finding, not for rescoring the dataset.

### Current Failure Clusters

| Cluster | Cases | What happened | Likely fix |
|---|---|---|---|
| Overly eager routing on ambiguous sign-in or access issues | F26, E14, E19 | The agent routed to verification when it should have asked one clarifying question first. | Tighten the ambiguity policy so vague sign-in/access requests stay in intake until one clarifier is asked. |
| Overly cautious ambiguity detection | H11 | The agent asked for clarification even though the issue was specific enough to route. | Teach the agent that named resources plus recent usage often count as enough detail to route. |
| Prompt injection or misleading request handling | A30 | The agent was asked to fabricate a support condition and route accordingly. | Reinforce that fabricated or manipulated context must be ignored. |
| Potential label or scoring anomaly | H03 | The example appears to be a clear verification case, so confirm whether the trace was truly a failure or just a comparison/reporting mismatch. | Verify the LangSmith row and scoring result before treating it as a model failure. |

### First Improvement

The first fix should target **overly eager routing on ambiguous sign-in or access issues**.

Change:
- tighten the intake routing prompt so `I can't sign in` or `I cannot access` does not automatically route to verification
- require one clarifying question unless the caller names a specific resource or gives recent context
- lower routing temperature to keep this decision consistent

Expected effect:
- improve `intake_hold_safety`
- recover some `route_accuracy`
- leave cost roughly flat
- slightly improve consistency across repeated runs

### Post-Improvement Snapshot

- Date of run: June 24, 2026
- LangSmith project: `multi-agent-it-support-intake-eval`
- Dataset version: `intake-routing-golden-v1`
- Target mode: `llm`
- Run count: `30`
- LangSmith experiment link: https://smith.langchain.com/o/8512d3fc-b1cd-4248-a3e7-a219ab23b792/datasets/6663d81d-bd5f-405b-9538-aec25b4d9dba/compare?selectedSessions=1965f09a-806b-4510-9b05-11923cf81da4

### Metrics

- route_accuracy: `0.9000`
- intake_hold_safety: `0.9333`
- p50_latency_s: `3.1727`
- avg_cost_usd: `0.0008`
- avg_prompt_tokens: `306.7333`
- avg_completion_tokens: `160.6333`
- avg_total_tokens: `467.3667`

### Delta From Baseline

- route_accuracy: `+0.1000`
- intake_hold_safety: `+0.0666`
- p50_latency_s: `-0.0207`
- avg_cost_usd: `+0.0002`
- avg_prompt_tokens: `+84.0000`
- avg_completion_tokens: `+19.0666`
- avg_total_tokens: `+103.0667`

### Interpretation

The routing change moved the agent in the right direction: it is safer on ambiguous intake cases and also more accurate overall. The tradeoff is a moderate token increase, which raised cost slightly, but latency stayed effectively flat. For the cohort demo, this is a strong example of a measured improvement: one targeted prompt change, one rerun, and a clear numeric delta.

## How To Re-run

```bash
py scripts/langsmith_baseline.py --mode llm
```

Use `--mode heuristic` only for smoke testing the wiring.
