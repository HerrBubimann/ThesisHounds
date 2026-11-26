# State of the art: scoped engineering review

Research date: 2026-11-26. Source metadata, inspection scope and limitations are in
[references.md](references.md). Evidence below is separated from design judgments.

LLM-as-a-Judge is a useful research paradigm, but preference agreement is not an
academic validity certificate. S1 describes judge biases; recent peer-review studies
S6–S8 report instability, generic criticism, grounding limitations and confounding.
No cited study establishes that the configured local 7–8B models can reliably assess
PA1, PA2 or BA work in German. Automated academic assessment requires criterion-level
validation against domain experts and distinguishes review assistance from grading.

Multi-agent debate (S2) motivates experiments with different orchestration modes.
It does not establish that more agents, manufacturers or majority votes improve
ThesisHounds. Shared training data, templates and reasoning failures can correlate
errors across models. Maintain original dissent and uncertainty rather than equating
consensus with truth. Existing A–D experiments provide a starting point, not results.

RAG (S4) separates retrieval from generation. Agentic RAG adds query/tool decisions
and therefore additional authorization and failure boundaries. For scientific
literature retrieval, metadata services P1–P4 can help establish identity, version
and dates. They cannot alone verify whether a quotation supports a claim. Track
UNVERIFIED, METADATA, ABSTRACT and FULLTEXT inspection independently of correction/
retraction status. Unknown retraction status is not proof of absence. Older standard
works are not automatically inferior to recent publications.

Human-AI collaboration needs interaction evaluation: S3 supports testing cognitive
forcing interventions, while anchoring and automation bias remain plausible risks.
The independent-first-review embargo is our design hypothesis, not a proven causal
effect. No AI grade or preselected AI agreement appears in the new workflow.

Prompt injection (S5) makes thesis text, bibliography, external abstracts and PDF
metadata untrusted. A detector and prompt wording are insufficient alone. Tool
allowlists, strict schemas, no shell execution, bounded calls and isolated networks
must be enforced outside the model. Hidden PDF layers/white text cannot be reliably
detected from plain extracted text; that remains a parser/security evaluation task.

Local/sovereign AI is a deployment property, not a model-family guarantee. University
inference must include approved networking, verified TLS, identity, access logs,
retention, supply-chain controls and cloud disablement. Local hosting alone does
not eliminate bias, model backdoors or document access risks.

**Architecture choices derived by the team:** retain the existing gateway and
LangGraph experiments; add a fixed criterion loop for the independent MVP; freeze
first reviews and append human decisions; synthesize only approved material;
leave public research and scoring closed until their technical/fachliche approvals.
See ADRs 001–002. None of these choices is represented as an externally proven result.
