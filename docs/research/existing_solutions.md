# Existing solutions and selection

Original research review: 2026-11-26. Implementation follow-up: 2026-11-28. See [source register T1–T8/P1–P4](references.md) for authors,
dates, URLs, inspection limits and findings. Comparisons are engineering judgments,
not benchmark results. No new framework dependency was installed for this review.

| Option | Potential fit | Cost / risk and current decision |
|---|---|---|
| LangGraph (already installed) | Fixed AI stage graph, future durable human checkpoints | Keep existing graph; persistence and authorization need explicit application design. |
| Haystack | Modular approved-document retrieval pipelines | Revisit for RES-1 if a scoped internal corpus is approved; avoid a second orchestration stack now. |
| LlamaIndex | Loading/indexing, structured extraction and local retrieval | Revisit for internal retrieval; inspect loader egress, hosted-service defaults and per-analysis filters first. |
| AutoGen | Historical agent conversation research | The dated source review reported archived/unmaintained status; support status was not rechecked during documentation maintenance. Do not add to this sensitive-data stack. |
| CrewAI | Task/crew abstractions and flows | Adds overlapping coordination; no evaluated benefit over existing AgentFactory and LangGraph. |
| Crossref | DOI/bibliographic metadata | Offline metadata adapter and reviewed snapshots implemented; document-derived online calls remain blocked. |
| OpenAlex | Literature discovery and linked metadata | Offline metadata import implemented; no API key, billing or document-derived online discovery. |
| Semantic Scholar | Graph metadata/abstract discovery | Current detailed docs not fully accessible in this session; do not infer quotas or permissions. |
| arXiv API | Preprint discovery, version metadata | Carefully preserve version and publication type; usage policy/full-text reuse review pending. |

No listed framework supplies trustworthy academic judgments, privacy approval,
safe query declassification or tenant isolation just by being installed. Evaluate
with identical synthetic cases before introducing additional dependencies.

Future selection gate: pinned supported release, verified license, dependency/CVE
scan, telemetry disabled, offline operation, parser sandboxing, analysis-scoped
retrieval, deterministic workflow hooks and measurable improvement over baseline.
Open-source peer-review systems and agentic-RAG benchmarks need a separate full-code
and dataset licensing review; none is claimed as an adopted production solution.
