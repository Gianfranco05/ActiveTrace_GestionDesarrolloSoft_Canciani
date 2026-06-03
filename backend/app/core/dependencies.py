import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Depends, HTTPException, Request
from jose import JWTError as _JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import session_factory
from app.core.security import verify_access_token
from app.core.tenancy import get_tenant_id as _get_tenant_id_raw


@dataclass
class UserSession:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str] = field(default_factory=list)

    def has_role(self, role_name: str) -> bool:
        return role_name in self.roles


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()


async def get_tenant_id(request: Request) -> uuid.UUID:
    return await _get_tenant_id_raw(request)


async def get_current_user(request: Request) -> UserSession:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.removeprefix("Bearer ")
    try:
        payload = verify_access_token(token)
    except _JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_session = UserSession(
        user_id=uuid.UUID(payload["sub"]),
        tenant_id=uuid.UUID(payload["tenant_id"]),
        roles=payload.get("roles", []),
    )
    request.state.user = user_session
    return user_session


async def get_tenant(current_user: UserSession = Depends(get_current_user)) -> uuid.UUID:
    return current_user.tenant_id


# C-04: require_permission guard — RBAC authorization

def require_permission(codigo: str) -> Callable:
    async def dependency(
        current_user: UserSession = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        if not current_user.roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        from app.repositories.rbac_repository import RbacRepository
        effective = await RbacRepository.get_effective_permissions(
            db, current_user.roles,
        )
        if codigo not in effective:
            raise HTTPException(status_code=403, detail="Forbidden")

    return dependency


def require_permission_return_user(codigo: str) -> Callable:
    async def dependency(
        current_user: UserSession = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> UserSession:
        if not current_user.roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        from app.repositories.rbac_repository import RbacRepository
        effective = await RbacRepository.get_effective_permissions(
            db, current_user.roles,
        )
        if codigo not in effective:
            raise HTTPException(status_code=403, detail="Forbidden")

        return current_user

    return dependency
