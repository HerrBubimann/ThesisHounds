import pytest
from app.security.sperrvermerk_detector import TERMS, detect_sperrvermerk


@pytest.mark.parametrize("term", TERMS)
@pytest.mark.parametrize("location", ["cover", "body", "metadata", "ocr"])
def test_local_detector_checks_every_provided_source(term, location):
    kwargs = {
        "cover": {"pages": {1: term.upper()}},
        "body": {"pages": {37: term}},
        "metadata": {"metadata": {"subject": term}},
        "ocr": {"ocr": [term]},
    }[location]
    result = detect_sperrvermerk(**kwargs)
    assert result.detected and result.classification == "RESTRICTED"
    assert result.requires_authorized_review


def test_no_match_or_expiry_never_releases_a_document():
    assert detect_sperrvermerk({1: "Synthetische wissenschaftliche Arbeit"}).classification == (
        "RESTRICTED"
    )
    result = detect_sperrvermerk({1: "Sperr\u200bvermerk, abgelaufen am 01.01.2000"})
    assert result.detected and result.classification == "RESTRICTED"
