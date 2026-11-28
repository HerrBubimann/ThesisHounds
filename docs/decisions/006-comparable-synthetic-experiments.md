# ADR 006: Shared A-E experiment inputs and explicit missing human references

Status: accepted for synthetic engineering MVP, 2026-11-26. OFF-5.

Problem: legacy A-D modes differ in several controls, so their results cannot be
silently interpreted as a clean model-diversity experiment. LLM opinions are not gold labels.

Decision: run A-E through the same criterion-review implementation, fixed synthetic
fixture and catalog. Preserve common safety/quote audits in all arms. Record input,
prompt, configuration and model-digest provenance; separate repeats from single-factor
variations. Quality metrics require explicitly human-adjudicated prediction matches
bound to document/catalog hashes. Export actual local synthetic results as JSON/CSV.

Consequences: CI demonstrates orchestration and safety with mocks, not scientific
quality. Missing/incomplete adjudication yields null quality metrics. Real model,
hardware and human-subject studies remain separate prerequisites. No administrator
or university management feature is introduced.

## Implementation follow-up, 2026-11-28

The CLI lab additionally accepts registered, independently reviewed public test PDFs
through the controlled pilot catalog, and records their exact input hashes. Mock and
real-provider conditions remain distinct; a successful real-model study is not supplied.
Model probes v3 add bounded parallel dispatch and optional stream-fragment timing;
these do not manufacture quality labels or exact TTFT.
[Current evaluation](../evaluation.md).
