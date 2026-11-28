# Run the independent reviewer workflow

Current supported workflow, 2026-11-28. Start the
[local mock setup](../setup.md); installed model weights are unnecessary for the
default in-process mock. Select **Neue Begutachtung** in Streamlit and complete
the document/catalog/privacy wizard. The PA1/PA2/BA EXAMPLE profiles are deliberately
similar and are not official DHBW rubrics.

1. Choose work type, program/cohort, an admitted document and a server-offered catalog.
   A registered public pilot requires separate operator evidence; arbitrary upload is unavailable.
2. Read extracted document text. Registered originals without security indicators may
   be displayed in the local PDF viewer. The three-page text fixture has no original PDF.
3. Enter observations, strengths, weaknesses, rationale and questions for each criterion.
   Select NOT_ASSESSABLE where needed. Explicit session draft saving is temporary and
   is not a released backend review. Structured JSON import is optional.
4. Explicitly freeze the complete human first review. Independently start AI review;
   it may run while the human branch is open and receives no human review data.
5. Once both branches finish and any required document-security review is resolved,
   explicitly open comparison. Findings and local diagnostics share the server embargo.
6. Inspect neutral human/AI comparisons, original evidence, source checks and reviewer
   questions. Structured feedback and notes are versioned. Free discussion content is
   RESTRICTED and model forwarding is currently blocked; documented human review without
   model discussion is available.
7. Record a human conclusion/rationale per criterion and explicitly include or reject
   AI findings and approved notes. Read the deterministic draft and explicitly finalize.
   Local TXT/Markdown downloads are available; PDF/DOCX report export is not connected.

The AI branch uses mandatory coverage, bounded context, controlled specialist planning
and model verification. Scientific review, formal/citation checks, language, retrieval,
citation style and numeric diagnostics execute as bounded sibling tasks. Optional
artifact/service gaps stay visible; model consensus is not academic proof.
A missing optional AI result can remain unassessed; mandatory failure cannot be
published as successful complete coverage.

## API sequence and first-review import

Create with `POST /api/v1/assessments` and
`{"work_type":"PA1","profile_id":"pa1-example"}`.
Use the returned UUID for the case-scoped endpoints:

| Method / suffix | Purpose |
|---|---|
| GET base; GET `/document`, `/original-pdf` | Safe status, assigned text and conditionally admitted original |
| POST `/human-review`; POST `/ai-review` | Freeze complete first review; start independent async branch |
| POST `/release` | `{"confirmed":true}` after both branches; disclose results |
| GET `/comparison`, `/provenance`, `/findings/{finding_id}/evidence` | Released results, history and original references |
| POST `/finding-feedback`, `/reviewer-notes` | Versioned finding response and private notes |
| POST `/discussion`; POST `/manual-review` | Privacy-gated model discussion; explicit human-only review |
| POST `/decisions` | Criterion, include decision, conclusion and rationale |
| GET `/draft`; POST `/finalize` | Human decisions required; explicit final approval |
| POST `/cancel`; DELETE base | Cancel work; remove the assigned volatile case |

The collection also exposes metadata listing, admitted profiles/pilot documents and
a validated rules preview. Full methods, scope and other diagnostic endpoints:
[API contracts](../setup.md#assessment-api).
No endpoint grants institutional/model approval or admits arbitrary private files.

Example JSON first review for the shipped three-criterion profiles.
The UI still requires explicit release confirmation:

```json
{
  "release": true,
  "criteria": [
    {"criterion_id":"literature","judgment":"NOT_ASSESSABLE","observations":"Keine Literatur im Testauszug.","rationale":"Keine Quellenprüfung möglich."},
    {"criterion_id":"methodology","judgment":"MIXED","observations":"Sechs Fälle ohne Randomisierung.","rationale":"Deskriptive Analyse möglich; keine Kausalität."},
    {"criterion_id":"structure","judgment":"POSITIVE","observations":"Frage, Methode und Ergebnisse erkennbar.","rationale":"Nachvollziehbarer Textaufbau."}
  ]
}
```

## Controlled pilot and lifecycle

The API accepts the fixed text fixture or a registered reviewed-public/synthetic
pilot PDF subject to the existing PA1/program/catalog gates. The offline operator
CLI and actual local-pilot configuration are documented in
[setup](../setup.md#kontrollierter-public-pilot).
Changing EXAMPLE to EXPERIMENT without independent evidence is not approval.

Rubric import resets approval to CANDIDATE. Real private work, official grading,
durable recovery and university identities remain blocked. ACL checks are present,
but DEVELOPMENT shares one synthetic principal across browser sessions.
Case UUIDs are not an authentication mechanism.

Assessment results are not legacy `/runs` objects and cannot be exposed through
legacy lists. Stores are volatile and single-process with bounded histories/TTL.
Deleting a case does not delete the separately curated public pilot catalog.
Create a new case after a failed AI branch; no fallback silently publishes partial results.
