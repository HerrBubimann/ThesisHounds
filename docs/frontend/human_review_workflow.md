# Human-first review workspace

The existing Streamlit workspace implements the original professor-feedback workflow:

1. Select a server-authorized document.
2. Inspect and explicitly confirm the current catalog and mode in the creation wizard.
3. Enter an independent human review or extract a local import preview.
4. Check criterion mappings, complete required judgments and expressly submit.
5. Finish independent AI execution; it may run alongside step 3.
6. Explicitly release both completed, matching reviews.
7. Compare original human and independent AI judgments with original evidence.
8. Discuss evidence if privacy policy permits, or expressly perform human examination.
9. Record criterion-specific human conclusions and conflict decisions.
10. Inspect the deterministic draft and explicitly finalize it as a human.

The server enforces these prerequisites. Before release, the UI shows neutral AI
execution status and explains why findings remain locked. It does not display model
plans, partial findings, source judgments or points. Status refresh starts no new
analysis. Judgment and inclusion controls have no preselected answer. The comparison
warns that matching categories are not semantic agreement or scientific validation.

JSON/YAML/PDF/DOCX import uses a bounded local preview with extracted original text,
exact mappings, unknown/ambiguous content and missing required criteria. JSON/YAML
values can seed editable fields; PDF/DOCX narrative text is manually structured.
The reviewer must confirm both the imported material and the completed submission.
A preview can be discarded to continue manually. No missing rating is AI-generated.
Current development imports are limited to synthetic/authorized public test material.

Human weaknesses and strengths are optional. Explain NOT_ASSESSABLE or not-applicable
judgments; no criticism quota, reading timer, minimum word count or behavioral
monitoring is used. The UI cannot verify that someone read or understood a thesis.

MANUAL_ONLY is selected when creating a case. It supports independent human input,
criterion decisions, draft/export and human finalization without any model call.
AI execution/release/comparison/discussion remain denied for that case. The existing
post-release 'Ohne KI-Diskussion menschlich prüfen' is a separate human examination
choice in assisted cases, not an embargo bypass.

Original submissions and human decision history remain scoped and inspectable.
Draft export uses the same protected draft endpoint and includes only explicit
decisions/selected findings. Session drafts and backend records are volatile;
restart/recovery and university SSO are not implemented. Confidential discussion
remains blocked by the existing gateway policy; no external-model fallback is added.
