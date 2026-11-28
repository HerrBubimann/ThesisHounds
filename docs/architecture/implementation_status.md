# Professor feedback delivery status

Verified against the repository on 2026-11-28. This table describes implemented
software and remaining evidence, not stakeholder approval. The initial
[gap analysis](professor_feedback_gap.md) remains a historical baseline.
The original project slides, primary meeting record and approved detailed rubric
are not available; OFF/G identifiers are inherited mappings, not newly confirmed requirements.

| Backlog | Delivered in the current code | Remaining / blocked |
|---|---|---|
| INF-1 | Pinned local transport, exact university HTTPS host/IP/TLS controls and standalone university Compose configuration | University identity/network/storage acceptance; UNIVERSITY_SECURE deliberately refuses startup |
| INF-2 | Registry provenance, full artifact digest and license/security gates; separate provisioning lifecycle | Actual model approvals, verified artifacts and a successful real-model run |
| RUB-1 | Versioned PA1/PA2/BA examples, bounded candidate importer, cohort-specific Mosbach candidates and conflict handling | Authoritative catalog, Palleduhn original, validity and independent institutional promotion |
| MVP-1 | Separate volatile assessment store, ACL checks, immutable human first release, safe list/status projections and server embargo | Real university identities, tenant isolation, durable audit/storage and recovery |
| MVP-2 | Mandatory coverage, scoped context retrieval, semantic specialist proposals, bounded adversarial review, neutral comparison, feedback, human decisions and deterministic final draft | Measured academic value, private-document acceptance, authorized RESTRICTED discussion |
| SEC-1 | PDF preflight/worker limits, injection indicators, owner/tool/model scope, IFC, request/response bounds, quarantine and human security decisions | Complete OS parser sandbox, OCR/image attack coverage, target-host/SSO/organizational release |
| Routine checks | Offline bibliography/identifier checks, formal candidates, conservative numeric comparisons and method-bound reproducibility questions | Reliable visual extraction, complete source corpus, active official rules and expert validation |
| Reviewer productivity | Local finding groups, original evidence, reviewer questions, versioned notes and explicitly measured review sessions | Validated usefulness, attention/time-savings evidence and real expert references |
| Frontend | Dashboard, guided creation, case list, criteria/document/finding workspace, source and Mosbach views, model/security/system pages, protected original PDF and TXT/Markdown export | Evaluation-report API, assessment-agent live events, synchronized PDF geometry, full accessibility acceptance |
| EVAL-1/2 | CLI A–E lab, paired variants/ablations, reference interfaces, model benchmark v3 with bounded parallelism and optional stream metrics | Real-model results, exact TTFT, per-model peaks, human quality/bias study |
| DOC-1 | Source register, ADRs, architecture, workflow and security docs, risks and current validation record | Full systematic literature review and actual stakeholder decisions |
| RES-1 | Offline public provider adapters, SQLite/FTS5 snapshots, controlled library exports and separate public dataset sync | Document-derived online research, private institutional index, approved query service |
| SCORE-1 | Disabled at startup and output boundaries; no model grades or target-grade optimizer | Approved scales, policy decision and defensible implementation |

The default is DEVELOPMENT with in-process mock inference. A separately configured
local pilot may process registered synthetic/reviewed-public PDFs through approved
Ollama artifacts. That exception does not admit confidential student work.
Source parsing and proposal existence never establish academic truth.

Latest software evidence: **956 tests, 87.06% combined coverage** in the reviewer-tool
refinement run on 2026-11-28. Numeric interpretation guards, perspective-preserving
deduplication and infrastructure metric aggregates extend the existing components.
Local image builds, mock container E2E and browser checks refer to the preceding
frontend iteration; they were not rerun for these refinements.
[Validation](../validation.md) · [Frontend limitations](../frontend/limitations.md) ·
[Production blockers](../security/production_readiness.md)
