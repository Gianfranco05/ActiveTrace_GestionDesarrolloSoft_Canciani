"""Tenant resolution utilities.

Reads tenant_id from request.state (set by C-03 auth middleware).
For testing, dependency override injects tenant_id directly.
"""

import uuid

from fastapi import Request

from app.core.exceptions import TenantNotFoundError


def get_tenant_id_from_request(request: Request) -> uuid.UUID:
    """Extract tenant_id from request.state.

    The auth middleware (C-03) sets request.state.tenant_id during
    token validation. Until C-03 is implemented, tests use dependency
    overrides.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise TenantNotFoundError(
            "tenant_id not found in request.state — "
            "auth middleware (C-03) must set it before this dependency is used",
        )
    return uuid.UUID(str(tenant_id))


async def get_tenant_id(request: Request) -> uuid.UUID:
    """FastAPI dependency that resolves the current tenant ID.

    Usage in routers:
        @router.get("/items")
        async def list_items(tenant_id: uuid.UUID = Depends(get_tenant_id)):
            ...
    """
    return get_tenant_id_from_request(request)
