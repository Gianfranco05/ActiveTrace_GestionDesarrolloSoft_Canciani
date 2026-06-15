import uuid

import pytest
from jose import JWTError as JoseJWTError

from app.core.security import create_access_token, verify_access_token


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


def test_create_access_token(user_id, tenant_id):
    roles = ["admin"]
    token = create_access_token(
        user_id=str(user_id),
        tenant_id=str(tenant_id),
        roles=roles,
    )
    assert isinstance(token, str)
    assert len(token.split(".")) == 3


def test_verify_valid_token(user_id, tenant_id):
    roles = ["admin"]
    token = create_access_token(
        user_id=str(user_id),
        tenant_id=str(tenant_id),
        roles=roles,
    )
    payload = verify_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["roles"] == roles
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_claims_match_input(user_id, tenant_id):
    token = create_access_token(
        user_id=str(user_id),
        tenant_id=str(tenant_id),
        roles=[],
    )
    payload = verify_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["roles"] == []


def test_tampered_token_rejected(user_id, tenant_id):
    token = create_access_token(
        user_id=str(user_id),
        tenant_id=str(tenant_id),
        roles=[],
    )
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1] + ".invalidsignature"
    with pytest.raises(JoseJWTError):
        verify_access_token(tampered)
