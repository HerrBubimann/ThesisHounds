# Metrics and denominators

| Metric | Definition / limitation |
|---|---|
| Precision | Expert-supported matched AI findings / all adjudicated AI findings; unmatched criticism counts as FP. |
| Recall | Expert reference findings matched by AI / all reference findings; agree on semantic matching rules in advance. |
| Hallucination rate | Fabricated factual claims / all adjudicated factual claims; record denominator and uncertainty. |
| False-positive criticism | Unsupported negative findings / all negative findings; separate from benign questions. |
| Citation correctness | Correctly identified/used citations / adjudicated citations; report metadata, abstract and fulltext checks separately. |
| Source quality | Expert rubric for relevance, authority, version and suitability; never recency alone. |
| Coverage | Attempted criteria / configured criteria; separately count substantive, NOT_ASSESSABLE, failed and skipped. |
| Human-AI agreement | Coarse judgment confusion matrix and rationale agreement; not correctness. Optionally weighted kappa with justified weights. |
| Time saved | Human active review time under controlled condition versus baseline; include verification/discussion effort. |
| Resources | Latency distribution, failures, calls, observed/reserved tokens, backend RSS, inference-host RAM and VRAM peak. Missing telemetry is null. |
| Injection robustness | Authorized task success and attacker success per attack family; detector hit rate alone is insufficient. |
| Decision change | Pre/post-discussion criterion decisions; distinguish beneficial correction from adoption of wrong AI advice against references. |

Undefined ratios (zero denominator) are null, never zero. Report sample counts,
model/revision/configuration, paired confidence intervals and case clustering.
The current probe v3 implements schema/timing/token plumbing, bounded dispatch and
optional first-content-fragment timing. Exact TTFT and per-model peaks remain unknown.
The lab/reference interfaces can calculate quality metrics only from complete matching
human adjudications. Reviewer session elapsed time is not attention or measured time saved.
No such missing scientific measurement is reported as a real model result.
