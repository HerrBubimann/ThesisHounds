# Professor feedback: gap analysis and delivery scope

Assessment date: 2026-11-26. Baseline: clean working tree, repository version 0.2.0.
This is an implementation audit, not stakeholder approval. Requirement numbers refer
to the supplied professor feedback request. The initial audit precedes implementation;
see `implementation_status.md` for delivered changes and remaining work.

| Requirement | Initial classification | Evidence / gap |
|---|---|---|
| 1–2 Human-controlled second reviewer | Partially implemented | Human acceptance of individual findings exists; independent first review absent. |
| 3 Scientific and framework research | Not implemented | Existing architecture docs have no source register or comparative research. |
| 4 Local / university inference | Partially implemented; university infrastructure dependent | Local-only host validation; no remote internal endpoint, TLS/auth or university approval. |
| 5 HF registry and controlled provisioning | Not implemented | Registry has manufacturer, roles, memory estimates; no artifact provenance or approval. |
| 6 Empirical model assignment | Partially implemented | A–D execution modes exist; no task capability benchmark; assignments are configuration defaults. |
| 7 PA1/PA2/BA catalogs | Not implemented; stakeholder dependent | RunRequest accepts free text criteria; no official criteria supplied. |
| 8 Rubric / Palleduhn import | Not implemented; stakeholder dependent | Document and approved weights unavailable. |
| 9 Fixed assessment workflow | Partially implemented | Fixed LangGraph for AI analysis; no independent human branch or comparison gate. |
| 10 Independent human first review | Not implemented | Existing human review happens after AI disclosure. |
| 11 Criterion-wise AI second review | Partially implemented | Three supervisors and dynamic factory exist; planner may omit criteria. |
| 12 Deterministic routine checks | Partially implemented | Quote/page validation exists; bibliography tooling absent. |
| 13 Public/internal research | Not implemented; stakeholder dependent | Only document.read is allowed; no provider integrations. |
| 14 Isolated research gateway | Not implemented | Public egress denied by Docker networks; no query review service. |
| 15 Citation verification | Not implemented | Document evidence validation is not bibliographic verification. |
| 16 Structured findings | Partially implemented | IDs, pages, quotes, models, evidence, human status exist; criterion/source metadata absent. |
| 17 Bias mitigation | Not implemented | No server-side independent review embargo. |
| 18 Criterion comparison | Not implemented | Conflict detection compares AI findings only. |
| 19 Discussion | Not implemented | Generic chat is not linked to released assessments. |
| 20 Optional late scoring | Not implemented; stakeholder dependent | No official catalog or grade scale supplied. |
| 21 Human-controlled synthesis | Partially implemented | Final report uses accepted findings; LLM draft appears before human decisions. |
| 22 Injection/security | Partially implemented | Validated agent specs, tool allowlist, budgets, local policy; no document injection detector. |
| 23 Streamlit workflow | Partially implemented | Status, graph, model assignments and AI reviews; independent review UI absent. |
| 24 Incremental architecture | Already implemented in part | Modular backend and isolated Docker services; extend existing gateway, not replace it. |
| 25 Server-side assessment states | Partially implemented | AI run states only, in-memory single-process runtime. |
| 26 Tests and CI | Already implemented in part | Unit/integration/security jobs and required thesishounds-ci-gate; new safety tests needed. |
| 27 Scientific evaluation | Partially implemented | A–D modes and resources, initial docs; no human reference study. |
| 28 Risk register / threat model | Partially implemented | General security doc; no structured register. |
| 29 Stakeholder questions | Not implemented; stakeholder dependent | No answers or approval may be inferred. |
| 30 Vertical MVP | Partially implemented | Synthetic AI demo exists; human → AI → comparison → discussion absent. |
| 31 Definition of done | Partially implemented | Full production criteria require official catalogs, university configuration and evaluation. |
| 32 Audit, backlog, ADRs, validation | Not implemented for this feedback | This document starts the requested incremental delivery. |

## Prioritized implementation plan / backlog

| ID | Priority / phase | Deliverable and acceptance | Dependencies |
|---|---|---|---|
| INF-1 | P0 / 1 | Explicit university endpoint allowlist, verified TLS/auth configuration, env aliases; local defaults unchanged | Network/DNS/CA approval before deployment |
| INF-2 | P0 / 1 | HF artifact metadata and fail-closed approval check; no automatic downloads/code | License, provenance and compatibility review |
| RUB-1 | P0 / 1 | Versioned PA1/PA2/BA **example** profiles and human-reviewed structured import | Official catalogs remain unavailable |
| MVP-1 | P0 / 2 | Synthetic-only separate assessment store; immutable human release; no AI content in status/legacy APIs | Single assessor / one process |
| MVP-2 | P0 / 2–4 | Every criterion attempted, evidence statuses, explicit AI release, comparison, grounded discussion, decisions, draft and final release | Existing configured local models |
| SEC-1 | P0 / 5 | API disclosure/regression tests, injection signals, closed research/scoring defaults, retained CI gate | Synthetic fixtures only |
| EVAL-1 | P1 / 5 | Reproducible local gateway benchmark, recorded configuration, metrics and human study protocol | Real model execution / reference judgments pending |
| DOC-1 | P0 / all | Research/source register, ADRs, risk register, threat model and stakeholder questions | Document access limitations explicitly |
| PROD-1 | P1 / 2 | Authenticated owner/tenant isolation, durable transactional storage, retention/deletion, audit integrity | University identity/privacy decisions; blocks real thesis uploads |
| RUB-2 | P1 / 1 | PDF/DOCX extraction → source locations → reviewed candidate → official approval | Palleduhn document and rubric owner |
| RES-1 | P1 / 3 | Separate egress service, approved query queue, provider contracts, rate limits/timeouts, scoped internal index | Provider terms/auth, network/privacy approval |
| SCORE-1 | P2 / 4 | Approved scales and justified deterministic bottom-up scoring; top-down feasibility | Official scales, evidence constraints and stakeholder approval |
| EVAL-2 | P1 / 5 | German capability, tool calling, injection and human bias experiments across A–D + research variants | Hardware, licenses, approved study data and consent |

No real student documents, external research or production scoring are authorized by
this MVP's synthetic data interface. Example catalogs are not official DHBW rubrics.
