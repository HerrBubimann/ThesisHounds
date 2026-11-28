# Human decision ledger

The ledger is part of the existing assessment record, with the same ACL, retention
and authorized deletion lifecycle. It is never an application log, telemetry stream,
training dataset, cross-professor comparison or automatically exported study record.

Each entry includes sequence, origin, actor, timestamp, source binding, previous
entry hash, minimum relevant decision content and an integrity digest. Development
actors are explicitly `identity_verified: false`: `synthetic-demo` is not SSO.

Origins distinguish HUMAN_INITIAL_REVIEW, AI_INDEPENDENT_REVIEW,
HUMAN_FINAL_REVIEW, DISCUSSION, HUMAN_FINDING_FEEDBACK, HUMAN_REVIEWER_NOTE,
HUMAN_ACADEMIC_DECISION and FINAL_HUMAN_APPROVAL. Independent entries reference
their separate full snapshots. Final decisions retain the original criterion
assessment, associated AI snapshot/finding IDs, criterion-specific discussion
sequence references and the human rationale. Original AI evidence remains in the
independent snapshot and evidence explorer, avoiding duplicate evidence copies.

Final decisions are appended; a new decision supersedes the displayed decision
for that criterion without replacing history. Supported resolution labels:
KEEP_HUMAN, ADOPT_AI, MERGE, CORRECT_AI, REJECT_AI, FURTHER_REVIEW, LEAVE_OPEN.
The explicit include decision remains required and is never preselected. Reasoned
disagreement may remain open; rejecting every AI proposal still permits finalization.
Decisions with unresolved rejection/insufficient-evidence feedback cannot incorporate
those findings. The draft contains only explicitly selected findings and human text;
no model runs during final synthesis. All substantive criterion decisions require
a rationale, not individual typographic edits in draft text.

`GET /api/v1/assessments/{id}/decision-ledger` is disclosure-gated in assisted mode.
Manual-only cases expose only their human history after initial submission. Returned
values are copies. `GET .../human-review` allows the authorized reviewer to inspect
their own original submission even before AI release.

The chain provides local change detection and traceability, not a legal audit trail,
signed identity or immutable external storage. A restart destroys it. Persistent
transactional storage, university identity, retention requirements and a tested
restoration procedure remain production blockers.
