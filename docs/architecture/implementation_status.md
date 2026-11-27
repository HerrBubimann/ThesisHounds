# Professor feedback delivery status

Security update 2026-11-26: the current application defaults to an in-process mock,
blocks real content/network inference and refuses UNIVERSITY_SECURE startup.
The following original delivery table does not authorize production use or override
the current [privacy architecture](../security/privacy_architecture.md),
[production blockers](../security/production_readiness.md) or
[observed test results](../security/privacy_test_results.md).

2026-11-26. This records the incremental delivery after the initial
[gap analysis/backlog](professor_feedback_gap.md). It is not a claim that all
production Definition-of-Done items or stakeholder decisions are complete.

| Backlog | Delivered | Remaining |
|---|---|---|
| INF-1 | Local defaults retained; university HTTPS host allowlist, verified TLS/custom CA and bearer support, timeout/model aliases, concurrency limit, standalone university Compose and static CI validation | IT-provided network/auth/CA, hardware and privacy release; no live university test |
| INF-2 | HF provenance/revision/hash/license/format/capability metadata and enabled-artifact approval validation; provisioning runbook | Actual artifact review/import/conversion and license decisions |
| RUB-1 | Separate PA1/PA2/BA EXAMPLE YAML profiles; strict registry; bounded JSON/YAML candidate import with approval reset | Official documents, per-program criteria, Palleduhn extraction and human promotion workflow |
| MVP-1 | Isolated volatile session store; frozen human review; safe status projection, dual release, API embargo and bypass tests | Durable version/audit storage and owner/tenant authorization |
| MVP-2 | Fixed per-criterion AI review using existing category model assignments, page/quote checks, coarse comparison, grounded local discussion, append-only human decisions, deterministic draft, explicit final release, cancellation, Streamlit UI | Dynamic factory/cross-review integration in the new criterion workflow, richer progress/tree, optional criteria semantics, real document import |
| SEC-1 | Strict no-score/tool outputs, heuristic injection signals, closed gateway contract, PUBLIC-label rejection, shared model-call semaphore and active-run admission, scoped lifetime budgets, retention and history bounds | PDF/metadata detection, identity masking, advanced red-team outcome evaluation, production network enforcement |
| Routine checks (phase 3 start) | Deterministic DOI candidate inventory before model calls, repeated mentions counted, explicitly UNVERIFIED | Bibliography/citation matching, reference metadata completeness, chapter and numbering checks need reliable extraction and approved criteria |
| EVAL-1 | Runnable synthetic gateway probe for model IDs/repeats, schema/errors/latency/tokens/resource snapshots; study protocol and metrics | Real-model results, GPU telemetry, digest/hardware snapshot completeness, expert quality labels, tool-calling and participant study |
| DOC-1 | Source register and targeted current research, framework comparison, ADRs, deployment/provisioning docs, risk register/threat model, stakeholder questions and validation record | Full-text systematic literature synthesis and actual stakeholder decisions |
| RES-1 | ResearchQuery and ResearchEvidence contracts; no external client/provider or document-store reference | Isolated service, approved query workflow, provider auth/terms/rates/response validation and internal scoped index |
| SCORE-1 | Disabled; activation fails closed, no model scoring/grade fields or target-grade optimizer | Official scoring/scale decisions and justified deterministic implementation |

Production blockers: official catalogs/scales, university IT information, approved
document and research data handling, reviewer identity/authorization, durable audit,
PDF/DOCX parsing review and scientific validation. Example findings and mocked test
responses do not establish real model performance or reduced automation bias.
