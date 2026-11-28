# State of the art: scoped engineering review

## Scientific engineering update (2026-11-26)

The new implementation hypotheses are documented in ADRs 003–006. Public primary
sources were checked independently of all thesis processing. The following recent
papers were inspected at abstract/metadata level; their full methods and results
were not independently reproduced, and preprints are not treated as accepted facts.

- Li et al., [LLM-as-a-Reviewer: Benchmarking Their Ability, Divergence, and Prompt
  Injection Resistance as Paper Reviewers](https://arxiv.org/abs/2605.25415),
  2026-05-25, arXiv v1: reports divergence from human reviewers and vulnerability to
  hidden instructions. This motivates explicit adversarial/security evaluation;
  it establishes no accuracy guarantee for ThesisHounds or its configured local tags.
- Amirshahi et al., [Judging a Review by its Cover](https://arxiv.org/abs/2609.23264),
  2026-09-20, arXiv v1 (page states accepted at CIKM 2026): reports sensitivity of
  review metrics to wording changes that preserve judgment. This motivates separate
  validity and consistency measurements and expert adjudication rather than style-based
  automatic quality scores.
- Yang et al., [Can We Believe AI Peer Review?](https://arxiv.org/abs/2610.19339),
  2026-10-14, arXiv v1: examines repeated reviews and cross-model judgments of revisions.
  Reported variability motivates repeated local trials; agreement among models is
  not assumed to establish academic correctness.

Earlier primary work remains relevant: [Zheng et al., MT-Bench](https://arxiv.org/abs/2306.05685)
discusses LLM judging and biases; [Du et al., Multiagent Debate](https://arxiv.org/abs/2305.14325)
motivates controlled tests of multiagent review rather than a blanket claim that debate
improves scientific assessment. The project's A-E comparison is an engineering
experiment derived from these concerns, not a replication or externally proven design.

For document engineering, [Docling's official documentation](https://docling-project.github.io/docling/)
describes local/air-gapped execution, a structured document representation and PDF
layout/table/code/formula capabilities. It is a candidate for a later isolated parser
study, not a dependency or validated capability in this release. [PyMuPDF's own
documentation](https://pymupdf.readthedocs.io/en/latest/about.html) describes PDF
processing and AGPL/commercial licensing; licensing and parser threat boundaries need
review before adoption. The current implementation additionally accepts controlled registered public PDFs
through the bounded pypdf worker and provides a protected local original viewer.
Docling/PyMuPDF and private OCR remain unapproved. A browser-rendered page is not
an independent server-side security raster comparison.

[Crossref's Retraction Watch documentation](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/)
describes public update/retraction metadata and a downloadable dataset; it also notes
that correction coverage is less comprehensive than retraction coverage. Therefore
snapshot absence never means "not retracted". The runtime uses no public API:
operator-provided local snapshots carry explicit provenance, version and inspection
scope. A bibliographic match cannot establish that the source supports a thesis claim.

## Original scoped review

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
