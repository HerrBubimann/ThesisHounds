# Review access control and residual risk

ThesisHounds' original role is an independent second reviewer under human authority.
Privacy classification and review disclosure are separate controls: a PUBLIC test
document does not authorize exposing its AI assessment before human release.

`AccessControl` checks object assignment and action permission. Client identity,
classification and role headers do not establish authority. DEVELOPMENT still uses
one shared synthetic principal; it is not authenticated multi-user university access.
Technical users gain no extra assessment-content route through agent APIs.

Every protected content operation resolves the assigned assessment and checks its
document/catalog binding and review integrity. The central release gate additionally
requires independent human and AI snapshots, complete mandatory coverage and explicit
release. Failed, cancelled, missing or mismatched reviews remain inaccessible. The
manual-only finalization path checks human submission and rejects AI functions.

Release/submission/decision mutations contain no await and execute atomically within
the supported single event loop. Two concurrent HTTP releases produce one success
and one conflict, with one release event. Local import parsing runs off the event
loop; after it finishes, ownership, object existence, source binding and writable
state are checked again before retaining the preview. Replaced previews get new IDs;
old or foreign confirmations fail. Original human submission is accepted once only.

This is not a multi-worker transaction design. Multiple workers, durable resume,
verified examiner identities and production examinations remain unsupported. On
timeout/error the AI review fails closed; cancelled records cannot resume. A restart
clears cases, tasks and object assignments; stale identifiers return 404. Restarting
requires a new case, catalog confirmation and independent review. Retention/delete
removes scoped human content, imports, snapshots, discussions and ledger together;
the separately managed public source catalog follows its existing lifecycle.
An authorized deletion remains possible even when the case fails integrity checks;
this deletion path returns no protected contents and still enforces object ownership.

Existing local-model allowlists, information-flow labels, tool/network restrictions,
Sperrvermerk checks, production-readiness blocks and telemetry disabling remain in
place. Review/import/discussion data are RESTRICTED. No human text is used for
independent AI planning or training. No external model fallback is introduced.
New import routes do not authorize confidential document ingestion in DEVELOPMENT.

Bounded imports reuse the existing subprocess PDF preflight and guarded OOXML parser:
no macros, embedded execution, external fetch, OCR or layout completeness guarantee.
HTTP bodies remain limited to 1 MiB; base64 limits mean the assessment importer
accepts smaller documents than the operator library parser. Invalid inputs produce
content-free error codes. Parser hardening/host isolation still require deployment
acceptance. Hashes detect local content changes but are not signed archival evidence.

Open DHBW requirements: applicable PA1/PA2/BA catalogs and cohort rules; legitimate
required human-form fields; authorized profile approvers; scoring/discussion policy;
verified identities/roles; retention and deletion periods; lawful processing and AI
Act applicability; private import approval; model/infrastructure acceptance; and an
approved human reliance study. No legal compliance or bias-elimination claim is made.
