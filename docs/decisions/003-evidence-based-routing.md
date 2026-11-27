# ADR 003: Privacy-first empirical model routing with explicit manual fallback

Status: accepted for synthetic engineering MVP, 2026-11-26. OFF-2/3/5.

Problem: model family names and developer preferences do not establish scientific
assessment ability. Provider choice must not weaken privacy or hide unavailable hardware.

Decision: extend the existing gateway with a deterministic router. Apply policy,
role, availability, optional inference-resource limits and reviewer exclusion first.
Only reviewed, nonmock capability evidence matching the exact observed digest and
task may rank remaining models. With no eligible evidence, preserve the operator's
assignment and record MANUAL_DEFAULT. Do not fabricate scores from schema success.

Consequences: useful defaults work before a scientific study, while every choice
remains auditable. Incorrect operator attestations remain a trust assumption. No
real model ranking is delivered yet; the empty capability registry states that fact.
Deployment privacy gates and the absence of external fallbacks remain unchanged.
