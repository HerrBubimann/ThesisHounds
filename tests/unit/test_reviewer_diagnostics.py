from uuid import uuid4

import pytest
from app.assessments.comparison import balanced_findings, finding_groups, reviewer_questions
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.routine_checks import numerical_consistency
from app.assessments.schemas import AssessmentFinding
from app.assessments.scientific_consistency import applied_method_candidates, reproducibility_report
from app.evaluation.metrics import HumanReferenceSet, digest, review_tool_metrics
from app.llm.errors import LLMError
from app.services.context_management import LocalContextIndex
from app.services.document_intelligence import structure_document
from app.services.document_store import Document

from tests.fixtures import CONFIG

CONTEXT = "Experiment E1; Modell M1; Datensatz D1; Split test: "


def document(first="Accuracy = 90 %.", second="Accuracy = 92 %."):
    return Document(
        document_id="synthetic",
        analysis_id="scope",
        classification="PUBLIC",
        pages={1: "1 Ergebnisse\n\n" + CONTEXT + first, 2: "2 Fazit\n\n" + CONTEXT + second},
    )


def profile():
    return ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")


def finding(doc, **updates):
    values = dict(
        assessment_id=doc.analysis_id,
        criterion_id="methodology",
        category="methodology",
        model_id="qwen",
        manufacturer="Alibaba",
        agent_id="synthetic",
        judgment="MIXED",
        kind="WEAKNESS",
        description="Die Stichprobe ist klein.",
        rationale="Die kleine Stichprobe begrenzt die Übertragbarkeit.",
        page=1,
        quote=doc.pages[1],
        evidence_status="QUOTE_MATCHED",
        data_classification="PUBLIC",
    )
    return AssessmentFinding(**{**values, **updates})


@pytest.mark.parametrize(
    "first,second,status",
    [
        ("Accuracy = 90 %.", "Accuracy = 92 %.", "NUMERIC_CONFLICT_CANDIDATE"),
        ("Accuracy = 90,0 %.", "Accuracy = 0.900.", "VALUE_AGREEMENT"),
        ("Accuracy = 90 %.", "Accuracy = 90.4 %.", "ROUNDING_COMPATIBLE"),
        ("RMSE = 2 s.", "RMSE = 2000 ms.", "VALUE_AGREEMENT"),
    ],
)
def test_numbers_use_context_decimal_units_and_rounding(first, second, status):
    doc = document(first, second)
    result = numerical_consistency(doc)
    assert len(result["claims"]) == 2
    assert result["comparisons"][0]["status"] == status
    assert result["comparisons"][0]["sections"] == ["Ergebnisse", "Fazit"]
    for row in result["claims"]:
        assert doc.pages[row["page"]][row["start"] : row["end"]] == row["quote"]
    assert not result["automatic_grade_effect"]


@pytest.mark.parametrize(
    "change", ["experiment", "model", "dataset", "split", "missing_context", "missing_unit"]
)
def test_different_or_incomplete_experiment_context_is_not_compared(change):
    doc = document()
    if change == "missing_unit":
        doc.pages[2] = CONTEXT + "Accuracy = 92."
    elif change == "missing_context":
        doc.pages[2] = "Accuracy = 92 %."
    else:
        old, new = {
            "experiment": ("E1", "E2"),
            "model": ("M1", "M2"),
            "dataset": ("D1", "D2"),
            "split": ("test", "train"),
        }[change]
        doc.pages[2] = doc.pages[2].replace(old, new)
    assert numerical_consistency(doc)["comparisons"] == []


@pytest.mark.parametrize(
    "text,status",
    [
        ("80 von 100 entsprechen 90 %", "ARITHMETIC_MISMATCH_CANDIDATE"),
        ("1 von 3 sind 33,3 %", "ARITHMETIC_MATCH"),
        ("1 von 0 sind 0 %", "NOT_ASSESSABLE_INVALID_DENOMINATOR"),
    ],
)
def test_percent_calculations_do_not_claim_experimental_truth(text, status):
    doc = document(text, "Keine zweite Zahlenangabe.")
    row = numerical_consistency(doc)["arithmetic"][0]
    assert row["status"] == status and not row["experimental_truth_verified"]
    assert doc.pages[row["page"]][row["start"] : row["end"]] == row["quote"]


def test_table_values_and_figures_are_preserved_as_unverified_text():
    doc = document()
    doc.pages[2] = "Tabelle 1: " + CONTEXT + "\nAccuracy | 92 %\n\nSiehe Abbildung 9."
    result = numerical_consistency(doc)
    assert result["comparisons"][0]["status"] == "UNVERIFIED_EXTRACTION_REQUIRES_HUMAN"
    assert result["objects"][0]["kind"] == "TABLE"
    assert not result["objects"][0]["visual_extraction_verified"]
    assert any(r["status"] == "NOT_LOCATED_IN_EXTRACTED_TEXT" for r in result["object_references"])
    assert not result["absence_proven"]


def test_quoted_values_and_code_do_not_become_own_experimental_claims():
    doc = document()
    doc.pages[1] = '"' + CONTEXT + 'Accuracy = 90 %."'
    doc.pages[2] = "```\n" + CONTEXT + "Accuracy = 92 %.\n```"
    assert not numerical_consistency(doc)["claims"]


def test_method_checklist_requires_applied_method_and_original_evidence():
    doc = document()
    doc.pages[1] = (
        "Methodik\n\nWir verwenden Random Forest mit Datensatz D1, Python 3.12 und Seed 42."
    )
    method = {
        "family": "MACHINE_LEARNING",
        "criterion_id": "methodology",
        "use": "APPLIED",
        "origin": "HUMAN_CONFIRMED",
        "evidence": [{"page": 1, "quote": "Wir verwenden Random Forest"}],
    }
    result = reproducibility_report(doc, profile(), [method])
    checks = {r["aspect"]: r for r in result["methods"][0]["checks"]}
    assert checks["random_seeds"]["status"] == "TEXT_MENTION_REQUIRES_HUMAN"
    assert checks["hyperparameters"]["status"] == "NOT_LOCATED_IN_METHOD_CONTEXT"
    assert not checks["hyperparameters"]["missing_information_proven"]
    assert not result["experiment_reproduced"] and not result["official_criterion"]
    assert reproducibility_report(doc, profile(), [{**method, "use": "MENTIONED"}])["methods"] == []
    with pytest.raises(ValueError, match="SCOPE"):
        reproducibility_report(doc, profile(), [{**method, "criterion_id": "foreign"}])
    with pytest.raises(ValueError, match="EVIDENCE"):
        reproducibility_report(
            doc, profile(), [{**method, "evidence": [{"page": 2, "quote": "invented"}]}]
        )
    qualitative = reproducibility_report(
        doc, profile(), [{**method, "family": "EXPERT_INTERVIEWS"}]
    )
    assert "random_seeds" not in {r["aspect"] for r in qualitative["methods"][0]["checks"]}


def test_reuse_of_applied_semantic_plan_revalidates_original_chunks():
    doc = document()
    first = finding(doc)
    with LocalContextIndex(doc) as index:
        chunk = index.chunks[0]
    plan = {
        "status": "VALIDATED_PROPOSAL",
        "understanding": {
            "procedures": [
                {
                    "family": "STATISTICS",
                    "use": "APPLIED",
                    "evidence": [{"span_id": chunk.id, "quote": chunk.text}],
                },
                {"family": "MACHINE_LEARNING", "use": "MENTIONED", "evidence": []},
            ]
        },
    }
    first.provenance["adaptive_planning"] = plan
    result = applied_method_candidates(doc, profile(), [first])
    assert len(result) == 1 and result[0]["origin"] == "VALIDATED_MODEL_PROPOSAL"
    plan["understanding"]["procedures"][0]["evidence"][0]["quote"] = "invented"
    assert applied_method_candidates(doc, profile(), [first]) == []


def test_duplicates_preserve_conflicts_and_distinct_scientific_perspectives():
    doc = document()
    first = finding(doc)
    duplicate = first.model_copy(
        deep=True, update={"finding_id": str(uuid4()), "model_id": "mistral"}
    )
    first.supplemental = [duplicate]
    result = finding_groups(doc, [first])
    assert result["redundancy_candidates"] == 1 and result["groups"][0]["exact_duplicates"]
    assert result["deleted_findings"] == 0
    duplicate.conflict = True
    assert finding_groups(doc, [first])["redundancy_candidates"] == 0
    duplicate.conflict = False
    duplicate.kind = "STRENGTH"
    assert finding_groups(doc, [first])["redundancy_candidates"] == 0
    duplicate.kind = first.kind
    duplicate.description = "Die Hardwareumgebung ist nicht beschrieben."
    assert finding_groups(doc, [first])["redundancy_candidates"] == 0
    duplicate.assessment_id = "foreign"
    with pytest.raises(ValueError, match="SCOPE"):
        finding_groups(doc, [first])


def test_questions_balanced_evidence_and_expert_only_tool_metrics():
    doc = document("80 von 100 entsprechen 90 %", "Keine weitere Zahl.")
    first = finding(doc, conflict=True, kind="STRENGTH", evidence_status="UNVERIFIED")
    result = balanced_findings([first])
    assert result["positive_evidence_pending"] == [first.finding_id]
    assert not result["forced_balance"] and result["minimum_criticism_count"] == 0
    questions = reviewer_questions(doc, profile(), [first], {}, numerical_consistency(doc))
    assert {q["reason"] for q in questions} >= {
        "CONFLICT",
        "INSUFFICIENT_EVIDENCE",
        "OPEN_CRITERION",
    }
    measured = review_tool_metrics(doc, profile(), [first])
    assert all(value is None for value in measured["quality"].values())
    labels = {key: True for values in measured["prediction_ids"].values() for key in values}
    reference = HumanReferenceSet(
        dataset_sha256=digest(doc.pages),
        profile_sha256=digest(profile().model_dump()),
        adjudicated_by=["SYNTHETIC_TEST_NOT_EXPERT_STUDY"],
        reference_ids=[],
        adjudications=[],
        review_tool_adjudications=labels,
    )
    scored = review_tool_metrics(doc, profile(), [first], reference)
    assert scored["quality"]["numerical"] == 1
    assert scored["human_time_saved_seconds"] is None
    reference.dataset_sha256 = "0" * 64
    assert (
        review_tool_metrics(doc, profile(), [first], reference)["reference_status"]
        == "REFERENCE_SCOPE_MISMATCH"
    )


def test_document_structure_limits_are_bounded():
    doc = document()
    doc.pages[1] = "x\n\n" * 4097
    with pytest.raises(LLMError, match="TOO_LARGE"):
        structure_document(doc)


@pytest.mark.parametrize(
    "extra_first,extra_second",
    [("; Seed 42", "; Seed 43"), ("; Run 1", "; Run 2"), ("; Fold 1", "; Fold 2")],
)
def test_repeats_seeds_and_folds_are_not_mixed(extra_first, extra_second):
    doc = document()
    doc.pages[1] = CONTEXT + "Accuracy = 90 %" + extra_first
    doc.pages[2] = CONTEXT + "Accuracy = 92 %" + extra_second
    assert not numerical_consistency(doc)["comparisons"]


def test_metric_averaging_and_uncertainty_are_not_treated_as_fixed_value_errors():
    doc = document("macro Accuracy = 90 %.", "micro Accuracy = 92 %.")
    assert not numerical_consistency(doc)["comparisons"]
    doc = document("Accuracy = 90 % ± 5 %.", "Accuracy = 92 %.")
    assert numerical_consistency(doc)["comparisons"][0]["status"] == "UNCERTAINTY_REQUIRES_HUMAN"


def test_word_overlap_does_not_merge_negated_perspectives():
    doc = document()
    first = finding(doc)
    duplicate = first.model_copy(
        deep=True,
        update={"finding_id": str(uuid4()), "description": "Die Stichprobe ist nicht klein."},
    )
    first.supplemental = [duplicate]
    assert finding_groups(doc, [first])["redundancy_candidates"] == 0


def test_grobid_table_figure_and_formula_outputs_remain_unverified():
    from app.services.grobid import parse_tei

    raw = b"""<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>
    <figure type="table" xml:id="tab1" coords="1,0,0,10,10"><head>Synthetic</head>
    <table><row><cell>Accuracy</cell><cell>90%</cell></row></table></figure>
    <figure xml:id="fig1"><head>Synthetic chart</head></figure>
    <formula xml:id="eq1">a=b</formula></body></text></TEI>"""
    objects = parse_tei(raw)["objects"]
    assert [o["kind"] for o in objects] == ["TABLE", "FIGURE", "FORMULA"]
    assert objects[0]["rows"] == [["Accuracy", "90%"]]
    assert not any(o["extraction_verified"] or o["mapping_verified"] for o in objects)


@pytest.mark.parametrize("value", ["0.90e-1", "0.90–0.95", "0.90/0.95", "0.90abc"])
def test_partial_numeric_notation_never_becomes_a_fixed_metric_value(value):
    doc = document("Accuracy = " + value, "Accuracy = 90 %.")
    result = numerical_consistency(doc)
    assert not result["comparisons"]
    assert len(result["claims"]) == 1
    candidate = result["unparsed_candidates"][0]
    assert candidate["status"] == "UNSUPPORTED_NUMERIC_NOTATION_REQUIRES_HUMAN"
    assert value in candidate["quote"]
    assert doc.pages[candidate["page"]][candidate["start"] : candidate["end"]] == candidate["quote"]


@pytest.mark.parametrize(
    "text", ["Accuracy = 90 % wurde nicht erreicht.", "Accuracy = 90 % wäre gut."]
)
def test_negated_or_hypothetical_results_require_interpretation(text):
    result = numerical_consistency(document(text, "Accuracy = 92 %."))
    assert result["comparisons"][0]["status"] == "UNCERTAINTY_REQUIRES_HUMAN"


def test_reproducibility_negated_documentation_generates_a_grounded_question():
    doc = document()
    doc.pages[1] = "Wir verwenden Random Forest. Hyperparameter sind nicht dokumentiert."
    method = {
        "family": "MACHINE_LEARNING",
        "criterion_id": "methodology",
        "use": "APPLIED",
        "origin": "HUMAN_CONFIRMED",
        "evidence": [{"page": 1, "quote": "Wir verwenden Random Forest"}],
    }
    reproduction = reproducibility_report(doc, profile(), [method])
    check = next(
        c for c in reproduction["methods"][0]["checks"] if c["aspect"] == "hyperparameters"
    )
    assert check["status"] == "DOCUMENTATION_UNCERTAINTY_REQUIRES_HUMAN"
    assert not check["missing_information_proven"]
    assert "NEGATION_OR_UNCERTAINTY_CUE" in check["passages"][0]["review_reasons"]
    questions = reviewer_questions(doc, profile(), [], reproduction, {})
    question = next(q for q in questions if q["reason"] == "REPRODUCIBILITY_CONTEXT")
    assert "Hyperparameter" in question["text"]
    assert question["passages"] == method["evidence"]


def test_reproducibility_long_block_context_includes_the_actual_match():
    doc = document()
    doc.pages[1] = "Wir verwenden Random Forest. " + "Synthetischer Kontext. " * 80 + "Seed 42."
    method = {
        "family": "MACHINE_LEARNING",
        "criterion_id": "methodology",
        "use": "APPLIED",
        "origin": "HUMAN_CONFIRMED",
        "evidence": [{"page": 1, "quote": "Wir verwenden Random Forest"}],
    }
    report = reproducibility_report(doc, profile(), [method])
    check = next(c for c in report["methods"][0]["checks"] if c["aspect"] == "random_seeds")
    passage = check["passages"][0]
    assert "Seed 42" in passage["context"]
    assert (
        doc.pages[1][passage["context_start"] : passage["context_start"] + len(passage["context"])]
        == passage["context"]
    )


@pytest.mark.parametrize("difference", ["relationship", "claim", "strengths", "support"])
def test_equal_wording_does_not_hide_distinct_perspectives(difference):
    from app.assessments.schemas import EvidencePassage, ScientificClaim, ScientificRelationship

    doc = document()
    first = finding(doc)
    duplicate = first.model_copy(deep=True, update={"finding_id": str(uuid4())})
    evidence = EvidencePassage(page=1, quote=doc.pages[1])
    if difference == "relationship":
        first.relationships = [
            ScientificRelationship(
                source="RESULTS",
                target="CONCLUSION",
                relation="ALIGNED",
                rationale="Synthetic",
                passages=[evidence],
            )
        ]
        duplicate.relationships = [
            first.relationships[0].model_copy(update={"relation": "POSSIBLE_CONTRADICTION"})
        ]
    elif difference == "claim":
        first.scientific_claims = [
            ScientificClaim(
                category="CONCLUSION",
                statement="Synthetic claim",
                passage=evidence,
                rationale="Synthetic",
                concern="NONE",
            )
        ]
        duplicate.scientific_claims = [
            first.scientific_claims[0].model_copy(update={"concern": "OVERGENERALIZATION"})
        ]
    elif difference == "strengths":
        duplicate.strengths = "Synthetic separate positive perspective"
    else:
        duplicate.supporting_passages = [evidence]
    first.supplemental = [duplicate]
    result = finding_groups(doc, [first])
    assert result["redundancy_candidates"] == 0
    assert not any(g["exact_duplicates"] for g in result["groups"])


def test_arithmetic_conflicts_generate_questions_with_original_evidence():
    doc = document("80 von 100 entsprechen 90 %", "Keine weitere Zahlenangabe.")
    questions = reviewer_questions(doc, profile(), [], {}, numerical_consistency(doc))
    question = next(q for q in questions if q["reason"] == "NUMERICAL_ARITHMETIC")
    assert question["criterion_id"] == next(
        c.id for c in profile().criteria if c.category == "content"
    )
    assert question["passages"] == [{"page": 1, "quote": "80 von 100 entsprechen 90 %"}]
    assert "80" in question["text"] and not question["automatic_exam"]


def test_attached_known_units_are_still_compared_without_truncation():
    result = numerical_consistency(document("RMSE = 2s", "RMSE = 2000ms"))
    assert result["comparisons"][0]["status"] == "VALUE_AGREEMENT"
    assert not result["unparsed_candidates"]


def test_negated_arithmetic_is_not_presented_as_an_asserted_calculation():
    doc = document("80 von 100 entsprechen 90 % wäre eine falsche Rechnung.", "Keine Zahl.")
    result = numerical_consistency(doc)
    assert result["arithmetic"][0]["status"] == "UNCERTAINTY_REQUIRES_HUMAN"
    questions = reviewer_questions(doc, profile(), [], {}, result)
    assert not any(q["reason"] == "NUMERICAL_ARITHMETIC" for q in questions)
