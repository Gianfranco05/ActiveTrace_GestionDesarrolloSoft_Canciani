import uuid

from app.core.dependencies import UserSession


def test_has_role_returns_true_when_role_present():
    session = UserSession(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        roles=["admin", "profesor"],
    )
    assert session.has_role("admin") is True
    assert session.has_role("profesor") is True


def test_has_role_returns_false_when_role_absent():
    session = UserSession(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        roles=["alumno"],
    )
    assert session.has_role("admin") is False


def test_has_role_returns_false_for_empty_roles():
    session = UserSession(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        roles=[],
    )
    assert session.has_role("admin") is False


def test_has_role_is_case_sensitive():
    session = UserSession(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        roles=["Admin"],
    )
    assert session.has_role("Admin") is True
    assert session.has_role("admin") is False
