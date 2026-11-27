# ADR 005: Source spans and offline verification before enabling richer parsers

Status: accepted for synthetic engineering MVP, 2026-11-26. OFF-3/4/5.

Problem: page numbers/quotes can be invented, absence claims require context,
and bibliographic metadata does not prove that a source supports an argument.

Decision: use one shared deterministic evidence function, exact local text spans
and conservative section/block metadata. Expose source navigation only through the
existing assessment authorization and result embargo. Offer local snapshot-based
DOI/version/retraction/quotation checks with explicit inspection scope. Never infer
semantic support or source irrelevance from age. Public research remains closed.

Consequences: typed PDF objects may still be unreliable; this release has no new
PDF/OCR ingress. Docling/PyMuPDF are researched candidates, not installed or approved
parsers. Operator-provided snapshots need independent provenance review and refresh.
No external research request is derived from confidential thesis contents.
