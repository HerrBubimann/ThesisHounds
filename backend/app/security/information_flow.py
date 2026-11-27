"""Immutable metadata, independent of model output. No declassification operation."""

from dataclasses import dataclass

from app.security.classification import Classification, classify, combine


@dataclass(frozen=True)
class InformationLabel:
    classification: Classification = Classification.RESTRICTED
    analysis_id: str = ""
    document_ids: frozenset[str] = frozenset()
    synthetic: bool = False

    def __post_init__(self):
        object.__setattr__(self, "classification", classify(self.classification))
        object.__setattr__(self, "document_ids", frozenset(self.document_ids))

    def derive(self, *others: "InformationLabel") -> "InformationLabel":
        sources = (self, *others)
        if not self.analysis_id or any(s.analysis_id != self.analysis_id for s in sources):
            raise PermissionError("FLOW_SCOPE_DENIED")
        return InformationLabel(
            combine(*(s.classification for s in sources)),
            self.analysis_id,
            frozenset().union(*(s.document_ids for s in sources)),
            all(s.synthetic for s in sources),
        )
