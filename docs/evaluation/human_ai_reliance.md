# Human–AI reliance experiment protocol

Status: designed, not run with human participants. Synthetic software tests validate
metric calculation and access controls; they are not an empirical automation-bias
study. Connects to the original ThesisHounds second-review objective and
[research rationale](../research/automation_bias.md).

| Condition | Controlled research presentation |
|---|---|
| A_EARLY_AI | AI judgment before participant assessment |
| B_EVIDENCE | Early AI judgment with original evidence |
| C_HUMAN_FIRST | Separate submitted human assessment before AI disclosure |
| D_DISCUSSION | Human-first plus evidence discussion and explicit conflict decisions |

A/B are potentially bias-inducing research conditions, never modes of the assessment
API. No override flag or endpoint opens the production gate. A separate approved
study interface, ethics/data review where required, informed consent and protocol
approval are prerequisites. Only synthetic or explicitly approved research test data
may be used. Real examination decisions are excluded from this controlled study.

Preregister hypotheses, primary outcomes, exclusions, missing-data handling and an
analysis plan. Obtain reference findings adjudicated by multiple competent reviewers,
document disagreements and retain source evidence. Balance correct AI suggestions,
incorrect suggestions, unsupported criticism and abstentions across relevant
criteria/work types. Do not present fabricated criticism as an actual student's fault.

Randomize participants to conditions and counterbalance matched documents; avoid
showing the same work repeatedly to the same person. Stratify relevant expertise and
estimate sample size from a pilot/power analysis rather than inventing a sufficient
N. Separate model quality from interface effects. Blind final-quality adjudicators
to condition and examine participant/document clustering and uncertainty intervals.

Primary measures: adoption of correct AI findings and adoption of false findings,
each with its own opportunity denominator; rejection of unsupported criticism;
reference-based final-quality ratings; changes in initial/final judgments where a
pre-AI initial judgment exists. A/B do not retrospectively acquire an independent
baseline: missing baselines stay missing. Record content changes separately from
correctness changes. Also assess elapsed task time, usability, perceived control,
traceability and professional acceptance with specified instruments. Do not infer
professor performance or attention from ordinary workflow logs.

`app.evaluation.metrics.RelianceTrial` and `reliance_metrics` provide offline
descriptive calculations, strict booleans, bounded ratings, finite elapsed times,
duplicate-trial checks, required protocol references and human-validated reference
IDs. Empty denominators return null. Approval/reference identifiers are supplied
research evidence, not cryptographic proof of an ethics approval. Subjective raw
ratings remain visible; no favorable composite score is invented.

Tests use explicitly synthetic reference IDs, not scientific ground truth. Current
outputs always state `empirical_effectiveness_established: false`. Similarity or high
agreement alone cannot establish automation bias; low adoption alone cannot establish
better judgment. Descriptive rates cannot identify individual bias or prove causality.
