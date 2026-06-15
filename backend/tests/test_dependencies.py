import uuid

import pytest
from fastapi import HTTPException

from app.core.dependencies import UserSession, get_current_user
from app.core.security import create_access_token


class MockRequest:
    def __init__(self, auth_header: str | None = None):
        self._headers = {}
        self.state = type("obj", (object,), {})()
        if auth_header:
            self._headers["Authorization"] = auth_header

    def headers(self, name: str) -> str | None:
        return self._headers.get(name)


def test_usersession_construction():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    session = UserSession(user_id=uid, tenant_id=tid, roles=["admin"])
    assert session.user_id == uid
    assert session.tenant_id == tid
    assert session.roles == ["admin"]


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    token = create_access_token(
        user_id=str(uid), tenant_id=str(tid), roles=["admin"],
    )
    request = type("obj", (object,), {
        "headers": {"Authorization": f"Bearer {token}"},
        "state": type("obj", (object,), {})(),
    })()

    result = await get_current_user(request)
    assert result.user_id == uid
    assert result.tenant_id == tid
    assert result.roles == ["admin"]
    assert request.state.user == result


@pytest.mark.asyncio
async def test_get_current_user_no_header():
    request = type("obj", (object,), {
        "headers": {},
        "state": type("obj", (object,), {})(),
    })()
    with pytest.raises(HTTPException) as exc:
        await get_current_user(request)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_non_bearer():
    request = type("obj", (object,), {
        "headers": {"Authorization": "Basic token123"},
        "state": type("obj", (object,), {})(),
    })()
    with pytest.raises(HTTPException) as exc:
        await get_current_user(request)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_tampered():
    request = type("obj", (object,), {
        "headers": {"Authorization": "Bearer invalid.token.here"},
        "state": type("obj", (object,), {})(),
    })()
    with pytest.raises(HTTPException) as exc:
        await get_current_user(request)
    assert exc.value.status_code == 401
