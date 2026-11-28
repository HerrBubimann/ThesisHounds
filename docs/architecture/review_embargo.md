# Review embargo

`AssessmentWorkflow.released()` remains the central content-disclosure policy.
It rechecks object authorization, full document/catalog binding, both snapshot
integrities, human completeness, AI completion/coverage, nonfailed/noncancelled
state, assisted mode and explicit human release. Merely setting `ai_released` is
insufficient. `status()` validates a purported release before projecting analysis.

| Surface | Before release |
|---|---|
| Assessment list/status | Neutral execution state and approved catalog metadata; no model text, error details, findings, grades, dynamic plan or finding counts |
| Original document | Authorized source only; no generated annotations |
| Human snapshot/import | Scoped human input only; never AI content |
| Comparison, provenance, local academic/source checks | HTTP 409 |
| Evidence explorer, discussion, feedback, notes and review-method tools | HTTP 409 |
| Draft/download source and finalization | HTTP 409 |
| Decision ledger | HTTP 409 in assisted mode; no AI IDs before release |
| Generic chat | Fixed connectivity fixture only; arbitrary assessment text blocked |
| Legacy run/agent routes | Separate synthetic diagnostic objects; assessment IDs have no legacy object/grant |
| SSE/WebSocket/export endpoints | Not implemented; absent routes do not expose results |

Legacy diagnostics accept only a server-owned synthetic fixture; local-pilot mode
disables legacy execution. They cannot ingest a thesis, initial human review or
assessment ID. The diagnostic demo is not an authorized examination workflow.
Assessment AI agents are not registered in the generic runtime agent views.

The middleware applies `Cache-Control: no-store, max-age=0` and `Pragma: no-cache`
to successful and failed requests, and suppresses raw exception/input text. No
assessment content is placed in general logs or external telemetry. Server caches
remain internal to the scoped workflow record, not separate access paths. Streamlit
loads generated content only after server release; hiding controls is not the gate.

Mutation checks cover synthetic documents as well as registered pilot PDFs. A
changed document, catalog, initial human record or AI output blocks all subsequent
disclosure; no stale scientific comparison is presented as current. A failed AI
review cannot be released. Timeouts fail closed and cancellations remain terminal.
This one-process gate is not a defense against a malicious server administrator
with arbitrary memory access; hashes are not keyed authenticity proofs.
