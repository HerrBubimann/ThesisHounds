# Scientific evaluation plan

Status: protocol proposal, 2026-11-26; no participants, reference labels or outcomes yet.

Compare: single prompt (A), homogeneous agents (B), heterogeneous agents (C), guarded
dynamic/cross-review system (D), a future approved research variant, and the complete
independent-human-review/discussion workflow. Existing modes are not interchangeable
with the new criterion workflow; document and control their differences before
attributing effects to model diversity or safeguards.

Use identical documents, versioned criteria and frozen model artifacts. Start with
synthetic documents. Real approved test works require consent/data authority,
retention rules and access controls (PROD-1). Obtain two independent expert reference
reviews and adjudicate disagreements without showing AI labels. Include acceptable
alternative judgments instead of assuming one textual answer is uniquely correct.

Preregister primary outcomes (unsupported criticism rate and supported-finding
recall), budgets, sample size/power rationale, exclusions and matching procedure.
Stratify by PA1/PA2/BA and topic only after official criteria are known. Randomize
configuration order and repeat model runs. Keep prompts, outputs, failure events,
human annotations, timing and hashes in controlled research storage. CI uses only
synthetic fixtures and supplies no evidence of educational validity.

Use a separate participant experiment for automation bias; see `automation_bias.md`.
Report descriptive results and uncertainty, missingness and resource costs. Causal
claims require suitable randomized conditions and adequate experimental power.
