from dataclasses import replace

import pytest
from app.security.classification import Classification
from app.security.privacy_policy_engine import (
    Decision,
    PrivacyPolicyEngine,
    ProcessingContext,
    SecurityMode,
)


@pytest.mark.parametrize("level", list(Classification))
def test_external_processing_is_never_enabled_by_ordinary_approval(level):
    context = ProcessingContext(
        classification=level,
        mode=SecurityMode.UNIVERSITY_SECURE,
        authorized=True,
        local_boundary_verified=True,
        target_approved=True,
        production_ready=True,
        external=True,
    )
    assert PrivacyPolicyEngine().decide(context) == Decision.DENY


def test_sensitive_processing_requires_an_independent_production_release():
    context = ProcessingContext(
        classification="RESTRICTED",
        mode=SecurityMode.UNIVERSITY_SECURE,
        authorized=True,
        local_boundary_verified=True,
        target_approved=True,
        external=False,
    )
    engine = PrivacyPolicyEngine()
    assert engine.decide(context) == Decision.REQUIRE_AUTHORIZED_APPROVAL
    assert engine.decide(replace(context, mode=SecurityMode.DEVELOPMENT)) == Decision.DENY
    assert engine.decide(replace(context, authorized=False)) == Decision.DENY
    assert engine.decide(replace(context, action="training")) == Decision.DENY
    assert engine.decide(replace(context, local_boundary_verified=False)) == Decision.DENY
    for mode in (SecurityMode.PUBLIC_RESEARCH, SecurityMode.EXPERIMENTAL_PUBLIC):
        assert engine.decide(replace(context, classification="PUBLIC", mode=mode)) == Decision.DENY
