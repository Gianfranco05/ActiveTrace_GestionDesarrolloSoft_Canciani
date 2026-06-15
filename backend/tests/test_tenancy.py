import uuid

import pytest
from fastapi import FastAPI, Request

from app.core.tenancy import get_tenant_id


@pytest.mark.asyncio
async def test_get_tenant_id_with_override():
    app = FastAPI()
    expected_tid = uuid.uuid4()

    async def override_tenant():
        return expected_tid

    app.dependency_overrides[get_tenant_id] = override_tenant

    async def _test():
        request = Request({"type": "http", "method": "GET", "path": "/test"})
        request.state.tenant_id = expected_tid
        result = await get_tenant_id(request)
        return result

    result = await _test()
    assert result == expected_tid
