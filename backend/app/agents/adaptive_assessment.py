"""Fixed topic templates use the existing factory; they never replace mandatory criteria."""

import re

from app.schemas.domain import AgentRecord, AgentSpec

TEMPLATES = (
    (
        "statistics",
        "Statistical Analysis",
        r"statist|stichprobe|randomis|regression",
        "methodology",
    ),
    ("interview", "Expert Interview", r"interview|qualitativ|kodierung", "methodology"),
    (
        "ml",
        "Machine Learning Methodology",
        r"machine learning|neuron|trainingsdaten|cross.validation",
        "methodology",
    ),
    (
        "architecture",
        "Software Architecture",
        r"softwarearchitektur|microservice|architekturmuster",
        "content",
    ),
    (
        "literature",
        "Literature Review",
        r"systematisch.{0,30}literatur|prisma|literaturreview",
        "content",
    ),
)


def adaptive_specs(document, profile, *, limit=2):
    text = "\n".join(document.pages.values())
    selected = []
    for key, name, pattern, category in TEMPLATES:
        if re.search(pattern, text, re.I) and any(c.category == category for c in profile.criteria):
            selected.append(
                {"key": key, "name": name, "category": category, "work_type": profile.work_type}
            )
    return selected[: max(0, min(limit, 2))]


def create_adaptive_agent(factory, document, profile, template, model_id, manufacturer):
    parent = factory.registry.register(
        AgentRecord(
            agent_id=f"{document.analysis_id}_{template['key']}_supervisor",
            run_id=document.analysis_id,
            name="Mandatory assessment supervisor",
            role=template["category"],
            model_id=model_id,
            manufacturer=manufacturer,
            task="Bounded supplemental criterion analysis",
            depth=1,
            can_delegate=True,
            data_classification=document.classification,
            allowed_models=frozenset({model_id}),
            allowed_documents=frozenset({document.document_id}),
        )
    )
    return factory.create(
        AgentSpec(
            agent_id=template["key"] + "_specialist",
            name=template["name"],
            description="Controlled topic-specific supplement for " + profile.work_type,
            task="Examine counterarguments and limitations for the assigned criterion only.",
            category=template["category"],
            model_id=model_id,
            supervisor_id=parent.agent_id,
        ),
        parent,
    )[0]
