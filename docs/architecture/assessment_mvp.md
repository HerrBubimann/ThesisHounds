# Run the independent reviewer MVP

Use the existing local setup and installed models. In Streamlit choose
**Unabhängige Begutachtung · Synthetischer MVP**, select PA1/PA2/BA and create a demo.
The three versioned example profiles are deliberately similar; they demonstrate
separate catalog selection without inventing official differences between work types.

1. Read the synthetic three-page document in the expander. No real thesis upload is enabled.
2. Enter observations, strengths, weaknesses, rationale and questions for every criterion.
   Select NOT_ASSESSABLE where information is missing. Alternatively upload a structured
   JSON first review in the schema below. Explicitly check completion and release it.
3. Start the independent AI review. It can also run while the human branch is open;
   outputs remain server-hidden and the AI receives no human first-review data.
4. When both are complete, explicitly open comparison. A matched quotation proves a
   text location, not academic correctness. AI metadata/source verification is absent
   unless explicitly supported; no public research is performed.
5. Discuss a criterion or counterargument. Treat responses as suggestions. Record a
   human conclusion and rationale for each criterion and explicitly choose whether
   its AI finding should be included. Revisions append; originals remain unchanged.
6. Read the deterministic Gutachtenentwurf, then explicitly finalize. No point/grade
   suggestion is generated. Finalized decisions cannot be edited in this session.

All profiles are EXAMPLE, not official DHBW criteria. Optional points, PDF/DOCX form
extraction and real student documents are deferred. The API accepts only the fixed
synthetic document ID and at most six criteria per current MVP catalog. The structured
rubric importer returns a CANDIDATE even if imported content claims approval; official
activation is an operator-controlled human review/configuration change.

## API sequence and first-review import

`POST /api/v1/assessments` with `{"work_type":"PA1","profile_id":"pa1-example"}`
returns an assessment ID. Use it under `/api/v1/assessments/{id}`:

| Method / suffix | Purpose |
|---|---|
| GET (base), GET `/document` | Safe status and fixed synthetic document |
| POST `/human-review` | Complete and freeze first review |
| POST `/ai-review` | Start asynchronous independent criterion loop |
| POST `/release` | `{"confirmed":true}` after both finish; open comparison |
| GET `/comparison` | Original criterion reviews, decision history and discussion |
| POST `/discussion` | Criterion ID and question; bounded local-model suggestion |
| POST `/decisions` | Criterion ID, `include_ai_finding`, conclusion and rationale |
| GET `/draft` | Human decisions required for every criterion |
| POST `/finalize` | `{"confirmed":true}`; final human approval |
| POST `/cancel` | Cancel an unfinished session/model task |

Example JSON upload (the UI still requires explicit release confirmation):

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

Independent review objects are not reused as legacy AI `/runs` objects. The old
Control Center remains an experimental A–D demo with its own synthetic data, not a
route for retrieving hidden assessment findings. No automatic migration or fallback
publishes failed second reviews. Create a new synthetic session after model failure.

Sessions are volatile, single-assessor and single-process, with bounded histories
and existing retention settings. The local demo has no production identity/access
management; assessment UUIDs are not an authentication mechanism. Do not deploy to
multiple reviewers or use real work until PROD-1 is implemented and approved.
