# Risk register

Review: 2026-11-26. Ratings are qualitative initial engineering judgments, not
measured probabilities. Owners below are proposed **roles**, not assigned individuals
or stakeholder acceptance. A passing regression test is not proof of eliminated risk.

| Risk | Likelihood / impact | Controls | Test method / result | Residual risk | Proposed owner / status |
|---|---|---|---|---|---|
| Prompt injection | High / high | Untrusted-data prompts, strict output/agent schemas, no shell, allowlisted tools and networks | New signal/schema regressions and existing agent guardrails pass; real adversarial model evaluation pending | Semantic manipulation, hidden layers and indirect attacks remain | Security engineer / open |
| Automation/anchoring bias | High / high | Independent first review, server embargo, no preselected agreement, late scoring | API/UI release-gate tests pass; participant effect unmeasured | Human anchoring and persuasive discussion | HAI researcher / study pending |
| Hallucinations | High / high | Page/quote checks, uncertainty labels, human criterion decisions | Quote matching and invalid-output tests pass; expert factual-quality evaluation pending | A real quote can support a false interpretation | Evaluation lead / open |
| Unjustified criticism | High / high | Evidence distinction, original reviews, human approval | Finalization tests exclude rejected AI material | Expert may still approve erroneous criticism | Academic rubric owner / open |
| Identity bias | Medium / high | Review prompt excludes identity cues; synthetic-only document input | Identity manipulation signal test passes; counterfactual outcome study pending | Names/affiliations inferred from content; no real-document anonymizer implemented | Evaluation lead / open |
| Query exfiltration | High / high | Public research closed; no provider client; caller PUBLIC label insufficient | All query classes denied in tests | Future egress service/declassification design needed | Privacy/security owner / blocked for production |
| Other students' documents | Medium / high | Fixed synthetic fixture, assessment-scoped state; no arbitrary paths or internal corpus | Upload/path spoofing rejected; legacy endpoint bypass tests pass | No identity/tenant system exists; UUID is not authorization | Backend/IT / real uploads blocked |
| False/invented sources | High / high | No generated references in final synthesis; source verification levels explicit | Evidence schema defaults UNVERIFIED; no provider execution | Metadata note alone is not external proof; future verifier needs trusted provenance | Research engineer / open |
| Stale model information | High / medium | Pinned HF revisions, reviewer attestations, empirical probe | Candidate HF enablement rejected in tests | Existing tags mutable, capabilities not empirically validated | Model steward / review pending |
| Uncontrolled agent creation | Medium / high | Existing AgentFactory limits and strict tool/spec allowlists; fixed MVP criterion loop | Existing delegation-limit tests pass | Configuration/operator compromise; no arbitrary delegation in MVP | Backend/security / mitigated in demo |
| Unreliable scoring | High / high | No scoring path; enable flag fails closed | Startup rejects scoring activation; score fields rejected | Official scales/weights and deterministic module not delivered | Academic owner / disabled |
| Target-grade manipulation | Medium / high | No top-down optimizer or early numerical results | Score/grade fields rejected by qualitative schemas | Human pressure or qualitative goal-seeking still possible | Academic owner / disabled |
| Resource overload | Medium / medium | Shared active-run gate, model semaphore, bounded profiles, history, calls/tokens/timeouts | Shared-limit/cancellation tests pass | Inference-host quotas and multi-worker limits not evaluated | IT/backend / production quotas pending |
| University unavailable | Medium / medium | Local mode independent; no external fallback | Mocked offline workflows pass | No university GPU, VPN or connectivity tested | University IT / information pending |
| Unsafe models/dependencies | Medium / high | Reviewed metadata, no remote code execution, locked dependencies and existing security CI | Registry gates pass; local Bandit/scan status in validation report | Metadata attestations are not artifact verification; runtime vulnerabilities possible | Model steward/DevOps / ongoing |
| Volatile state/audit loss | High / medium | Explicit synthetic-only session scope and retention | Cleanup/cancellation/frozen-review tests pass | Restart loses reviews; audit not tamper-evident or durable | Backend / PROD-1 required |

No risk owner, university access, privacy release or official rubric approval is
asserted here. Detailed current verification is in
`../architecture/implementation_status.md` and `../validation-professor-feedback.md`.
