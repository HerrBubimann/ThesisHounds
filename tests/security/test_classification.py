from dataclasses import FrozenInstanceError

import pytest
from app.security.classification import Classification, classify, combine
from app.security.information_flow import InformationLabel
from app.services.document_store import Document


@pytest.mark.parametrize("value", [None, "", "unknown", "public", "SYNTHETIC", 12, {}, []])
def test_missing_or_invalid_labels_are_restricted(value):
    assert classify(value) == Classification.RESTRICTED
    assert Document(document_id="synthetic", pages={}, classification=value).classification == (
        Classification.RESTRICTED
    )


def test_new_document_and_empty_combination_default_restricted():
    assert Document(document_id="synthetic", pages={}).classification == "RESTRICTED"
    assert combine() == "RESTRICTED"


@pytest.mark.parametrize("artifact", ["summary", "embedding", "prompt", "response", "export"])
def test_derived_artifacts_cannot_downgrade_or_cross_analyses(artifact):
    source = InformationLabel(Classification.RESTRICTED, "analysis", frozenset({"document"}))
    result = source.derive(InformationLabel(Classification.PUBLIC, "analysis"))
    assert result.classification == "RESTRICTED" and result.document_ids == source.document_ids
    with pytest.raises(FrozenInstanceError):
        result.classification = Classification.PUBLIC
    with pytest.raises(PermissionError):
        source.derive(InformationLabel(Classification.PUBLIC, "different"))


@pytest.mark.parametrize("a", list(Classification))
@pytest.mark.parametrize("b", list(Classification))
def test_mixed_sources_inherit_highest_class(a, b):
    order = list(Classification)
    assert order.index(combine(a, b)) == max(order.index(a), order.index(b))
