from uuid import uuid4

import pytest
from app.llm.errors import LLMError
from app.security.access_control import AccessControl, Principal, current_principal


def test_roles_alone_never_grant_content_and_assignment_is_required():
    access = AccessControl()
    key = str(uuid4())
    alice = Principal("alice", frozenset({"reviewer"}), frozenset({"read", "process"}))
    token = current_principal.set(alice)
    try:
        access.create(key)
        access.require(key)
        for role in [
            "reviewer",
            "authorized_second_reviewer",
            "administrator",
            "infrastructure_owner",
            "developer",
        ]:
            current_principal.set(Principal("bob", frozenset({role}), alice.permissions))
            with pytest.raises(LLMError) as denied:
                access.require(key)
            assert denied.value.status_code == 404
        current_principal.set(Principal("alice", frozenset({"reviewer"})))
        assert not access.allows(key)
        current_principal.set(None)
        with pytest.raises(LLMError):
            access.create(str(uuid4()))
    finally:
        current_principal.reset(token)


def test_assignment_never_implies_delete_or_review_permission():
    access = AccessControl()
    key = str(uuid4())
    access.create(key)
    from app.security.access_control import DEMO_PRINCIPAL

    token = current_principal.set(
        Principal(DEMO_PRINCIPAL.subject, permissions=frozenset({"read"}))
    )
    try:
        access.require(key)
        for action in ("review", "delete", "process"):
            with pytest.raises(LLMError):
                access.require(key, action)
    finally:
        current_principal.reset(token)
