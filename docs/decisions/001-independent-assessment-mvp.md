# ADR 001: Independent assessment as a separate bounded workflow

Date: 2026-11-26. Status: accepted for synthetic MVP; production authorization pending.

The baseline LangGraph implements AI-only experiments A–D and exposes their results
through `/runs`. It cannot safely hold a hidden second review without changing those
experiments and their API contracts.

Decision: add `/assessments` with a separate server-owned store and explicit state
guards. Reuse the existing model registry, local gateway, policy and concurrency
limits. Human first reviews are not passed to AISecondReviewer. Every profile
criterion is processed deterministically through its configured category supervisor
model; the model cannot choose which criteria to skip. `NOT_ASSESSABLE` records a
completed attempt, not a substantive judgment. Any failed criterion fails the whole
AI branch without publishing partial findings.

LangGraph remains the existing experimental orchestrator. A small explicit state
machine is sufficient for this MVP's human API transitions; no second orchestration
framework or duplicated agent factory is added. Dynamic specialists and cross-model
review remain in A–D and will need criterion coverage integration before reuse here.

Human release freezes the first review. After both reviews finish, explicit release
opens comparison for human evidence validation. Per-criterion decisions separately
approve or reject AI material; discussion responses cannot mutate original reviews.
Decision revisions append. Final synthesis is deterministic from human conclusions
and explicitly included AI findings; no LLM adds criticism during finalization.

This is a single-assessor, single-process, synthetic-only session store. State expires
after the existing retention period, is lost on restart and is cleared on shutdown.
It is not durable audit storage or tenant authentication. No real document ingress
is added before PROD-1. Status APIs project an allowlist, never serialize records.
Legacy endpoints have no reference to assessment review objects. Legacy A–D remain
an explicitly labeled experimental AI demo, not the independent reviewer workflow.

Tradeoff: coarse comparison labels cannot establish semantic agreement. Every
criterion's original observations, rationale, evidence status and uncertainty are
shown side by side. `HUMAN_ONLY`/`AI_ONLY` are reserved for future optional criteria;
this MVP requires complete coverage on both sides and never creates those states.

## Implementation follow-up, 2026-11-28

The original factory/cross-review limitation above describes the 2026-11-26 decision
baseline. The current assessment reuses the guarded Factory/Registry/ExecutionEngine,
mandatory coverage, semantic specialist planning and bounded adversarial review.
The current API also admits registered reviewed-public/synthetic pilot PDFs under
strict operator/catalog/model gates. Optional AI criteria have explicit execution states.
Durable storage, real university identities and private work remain blocked.
[Current delivery](../architecture/implementation_status.md) ·
[Supported workflow](../architecture/assessment_mvp.md).
