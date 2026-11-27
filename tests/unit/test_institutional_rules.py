from datetime import UTC, date, datetime

import pytest
from app.knowledge.formal import FormalMeasurements, check_formal, document_hash
from app.knowledge.registry import InstitutionalRegistry, fingerprint
from app.knowledge.schemas import (
    Hierarchy,
    HumanApproval,
    InstitutionalProfile,
    Rule,
    SourceDocument,
)
from app.services.document_store import Document

from tests.fixtures import CONFIG


def source(**updates):
    data = dict(
        id="mosbach-ds",
        title="Synthetic official rule fixture",
        publisher="SYNTHETIC",
        campus="Mosbach",
        faculty="Wirtschaft",
        programs=["data_science_ai"],
        cohorts=["DS25"],
        work_types=["PA1"],
        version="1",
        published_at=date(2026, 1, 1),
        valid_from=date(2026, 1, 1),
        original_url="https://example.invalid/public",
        retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
        sha256="a" * 64,
        classification="PUBLIC",
        release="APPROVED",
        binding="BINDING",
        hierarchy=Hierarchy.MOSBACH_PROGRAM,
        availability="RETRIEVED",
    )
    return SourceDocument(**(data | updates))


def rule(**updates):
    return Rule(
        **(
            dict(
                id="content-pages",
                description="Synthetic test rule",
                category="formal",
                method="content_pages",
                parameters={"min": 20, "max": 30, "basis": "CONTENT"},
                source_id="mosbach-ds",
                source_location="Synthetic section 1",
                release="APPROVED",
            )
            | updates
        )
    )


def profile(rules=None, **updates):
    return InstitutionalProfile(
        **(
            dict(
                id="ds25-pa1-v1",
                program="data_science_ai",
                cohort="DS25",
                work_type="PA1",
                version="1",
                release="APPROVED",
                rules=rules or [rule()],
            )
            | updates
        )
    )


def approval(subject, **updates):
    return HumanApproval(
        **(
            dict(
                subject_id=subject.id,
                content_sha256=fingerprint(subject),
                reviewer="synthetic-curator",
                reviewed_at=datetime.now(UTC),
                validity_confirmed=True,
                applicability_confirmed=True,
                public_provenance_confirmed=True,
            )
            | updates
        )
    )


def resolved(sources=None, p=None, **kwargs):
    sources = sources or [source()]
    p = p or profile()
    return InstitutionalRegistry(
        sources, [p], [*(approval(s) for s in sources), approval(p)]
    ).resolve("data_science_ai", "DS25", "PA1", **kwargs)


@pytest.mark.parametrize("work,cohort", [("PA1", "DS25"), ("PA2", "DS24"), ("BA", "DS23")])
def test_public_profiles_are_precisely_scoped_candidates(work, cohort):
    registry = InstitutionalRegistry.load(CONFIG / "institutions/dhbw/mosbach")
    data = registry.resolve("data_science_ai", cohort, work)
    assert data["profile"]["cohort"] == cohort
    assert data["status"] == "MANUAL_REVIEW_REQUIRED"
    assert not any(r["active"] for r in data["rules"])
    assert any(c["key"] == "page_count_basis" for c in data["conflicts"])
    assert [
        r["max_points"] for r in data["rules"] if r["id"].startswith("assessment-category-")
    ] == [20, 40, 30, 10]
    assert all(r["weight"] is None for r in data["rules"])
    assert not registry.resolve("data_science_ai", "DS26", work)["rules"]
    assert not registry.resolve("wirtschaftsinformatik", cohort, work)["rules"]


def test_approval_binds_version_digest_and_public_provenance():
    s, p = source(), profile()
    registry = InstitutionalRegistry([s], [p], [approval(s), approval(p)])
    assert registry.resolve("data_science_ai", "DS25", "PA1")["status"] == "ACTIVE"
    registry.sources[s.id].version = "2"
    assert not registry.resolve("data_science_ai", "DS25", "PA1")["rules"][0]["active"]
    # Caller mutation does not change an already loaded source.
    s.title = "changed"
    assert registry.sources[s.id].title != s.title
    registry = InstitutionalRegistry(
        [source()], [p], [approval(source(), public_provenance_confirmed=False), approval(p)]
    )
    assert registry.resolve("data_science_ai", "DS25", "PA1")["status"] != "ACTIVE"


@pytest.mark.parametrize(
    "updates",
    [
        {"valid_until": date(2026, 1, 2)},
        {"sha256": None},
        {"release": "CANDIDATE"},
        {"valid_from": None},
        {"campus": "Stuttgart", "hierarchy": Hierarchy.OTHER_CAMPUS, "binding": "ORIENTATION"},
    ],
)
def test_expired_unknown_unapproved_or_other_campus_never_activates(updates):
    data = resolved([source(**updates)], as_of=date(2026, 11, 27))
    assert data["status"] == "MANUAL_REVIEW_REQUIRED"


def test_no_latest_version_or_duplicate_approval_selection():
    p = profile()
    second = profile(id="ds25-pa1-v2", version="2")
    registry = InstitutionalRegistry([source()], [p, second])
    assert registry.resolve("data_science_ai", "DS25", "PA1")["profile"] is None
    with pytest.raises(ValueError, match="DUPLICATE"):
        InstitutionalRegistry([source(), source()], [p])
    with pytest.raises(ValueError, match="DUPLICATE_APPROVAL"):
        InstitutionalRegistry([source()], [p], [approval(p), approval(p)])


def test_conflict_needs_explicit_human_resolution_and_cannot_override_law():
    legal = source(id="law", hierarchy=Hierarchy.EXAMINATION_LAW)
    rules = [
        rule(conflict_key="pages", conflict_value="20-30"),
        rule(id="law-pages", source_id="law", conflict_key="pages", conflict_value="40-60"),
    ]
    p = profile(rules)
    data = resolved([source(), legal], p)
    assert data["status"] == "MANUAL_REVIEW_REQUIRED" and data["conflicts"][0]["status"] == "OPEN"
    for choice, status in [("content-pages", "OPEN"), ("law-pages", "HUMAN_RESOLVED")]:
        registry = InstitutionalRegistry(
            [source(), legal],
            [p],
            [
                approval(source()),
                approval(legal),
                approval(p, resolved_conflicts={"pages": choice}),
            ],
        )
        result = registry.resolve("data_science_ai", "DS25", "PA1")
        assert result["conflicts"][0]["status"] == status
        assert [r["id"] for r in result["rules"] if r["active"]] == (
            ["law-pages"] if status == "HUMAN_RESOLVED" else []
        )


def test_source_schema_rejects_unproven_delegation_and_invalid_dates():
    with pytest.raises(ValueError, match="DELEGATION"):
        source(hierarchy=Hierarchy.MOSBACH_WI_DELEGATED)
    with pytest.raises(ValueError, match="OTHER_CAMPUS"):
        source(hierarchy=Hierarchy.OTHER_CAMPUS)
    with pytest.raises(ValueError, match="VALIDITY"):
        source(valid_until=date(2025, 1, 1))
    with pytest.raises(ValueError, match="DUPLICATE"):
        profile([rule(), rule()])
    delegated = source(hierarchy=Hierarchy.MOSBACH_WI_DELEGATED, delegated_by="missing")
    assert resolved([delegated])["status"] != "ACTIVE"


def test_content_pages_are_not_pdf_total_or_unverified_measurements():
    doc = Document(document_id="synthetic", complete=True, pages={n: "Text" for n in range(1, 41)})
    data = resolved()
    assert check_formal(doc, data)["checks"][0]["status"] == "MANUAL_REVIEW_REQUIRED"
    measurements = FormalMeasurements(document_hash(doc), "fixture-reviewer", 25, "CONTENT")
    result = check_formal(doc, data, measurements)
    assert result["checks"][0]["status"] == "PASS"
    assert not result["total_pdf_pages_used_as_content_count"]
    assert (
        check_formal(doc, data, FormalMeasurements("wrong", "reviewer", 25, "CONTENT"))["checks"][
            0
        ]["status"]
        == "MANUAL_REVIEW_REQUIRED"
    )


def test_abstracts_presence_signature_and_organizational_limits():
    doc = Document(
        document_id="synthetic",
        complete=True,
        pages={
            1: "Abstract (Deutsch)\n" + "Wort " * 101 + "\n# Einleitung\nText\nInhaltsverzeichnis\n"
        },
    )
    rules = [
        rule(
            id="abstract",
            method="abstract_words",
            parameters={"language": "de", "min": 100, "max": 200},
        ),
        rule(id="contents", method="presence", parameters={"component": "contents"}),
        rule(id="signature", method="signature"),
        rule(id="expose", method="manual", scope="ORGANIZATIONAL"),
        rule(id="font", method="font_family", parameters={"expected": "Arial"}),
    ]
    data = resolved(p=profile(rules))
    measured = FormalMeasurements(document_hash(doc), "fixture-human", values={"font": "Arial"})
    rows = check_formal(doc, data, measured)["checks"]
    byid = {r["criterion_id"]: r for r in rows}
    assert byid["abstract"]["value"] == 101 and byid["abstract"]["status"] == "PASS"
    assert byid["contents"]["status"] == "PASS" and byid["font"]["status"] == "PASS"
    assert byid["signature"]["reason"] == "SIGNATURE_AUTHENTICITY_NOT_VERIFIED"
    assert byid["expose"]["reason"] == "CANNOT_BE_ESTABLISHED_FROM_DOCUMENT"
    doc = doc.model_copy(
        update={"pages": {1: "Abstract (Deutsch)\n" + "Wort " * 101, 2: "Fortsetzung"}}
    )
    assert check_formal(doc, data)["checks"][0]["value"] is None
