"""TDD: AuthService role resolution integration."""

from datetime import date

import pytest
from jose import jwt as _jwt

from app.core.rate_limiter import RateLimiter
from app.core.security import hash_password
from app.core.config import Settings
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.asignacion import Asignacion
from app.repositories.auth_repository import (
    AuthRepository,
    RefreshTokenRepository,
    ResetTokenRepository,
)
from app.services.auth_service import AuthService
from app.services.role_resolver import RoleResolver


@pytest.fixture
def auth_service(db_session, tenant) -> AuthService:
    auth_repo = AuthRepository(db_session, tenant.id)
    refresh_repo = RefreshTokenRepository(db_session, tenant.id)
    reset_repo = ResetTokenRepository(db_session, tenant.id)
    rate_limiter = RateLimiter(max_attempts=10, window_seconds=60)
    return AuthService(
        session=db_session,
        auth_repo=auth_repo,
        refresh_repo=refresh_repo,
        reset_repo=reset_repo,
        rate_limiter=rate_limiter,
    )


@pytest.fixture
def auth_service_with_resolver(db_session, tenant) -> AuthService:
    auth_repo = AuthRepository(db_session, tenant.id)
    refresh_repo = RefreshTokenRepository(db_session, tenant.id)
    reset_repo = ResetTokenRepository(db_session, tenant.id)
    rate_limiter = RateLimiter(max_attempts=10, window_seconds=60)
    role_resolver = RoleResolver(db_session, tenant.id)
    return AuthService(
        session=db_session,
        auth_repo=auth_repo,
        refresh_repo=refresh_repo,
        reset_repo=reset_repo,
        rate_limiter=rate_limiter,
        role_resolver=role_resolver,
    )


async def _create_user_with_role(db_session, tenant, email, rol_nombre):
    auth_user = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password("Secure123"),
    )
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(
        id=auth_user.id,
        tenant_id=tenant.id,
        nombre="AuthRole",
        apellidos="Test",
        dni="dni",
        cuil="cuil",
    )
    db_session.add(usuario)
    await db_session.commit()

    rol = Rol(nombre=rol_nombre, tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    asignacion = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2020, 1, 1),
    )
    db_session.add(asignacion)
    await db_session.commit()

    return auth_user


def _decode_token(token):
    settings = Settings()
    return _jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


@pytest.mark.asyncio
async def test_2fa_pending_token_includes_roles(db_session, tenant):
    auth_repo = AuthRepository(db_session, tenant.id)
    refresh_repo = RefreshTokenRepository(db_session, tenant.id)
    reset_repo = ResetTokenRepository(db_session, tenant.id)
    role_resolver = RoleResolver(db_session, tenant.id)
    rate_limiter = RateLimiter(max_attempts=10, window_seconds=60)
    svc = AuthService(
        session=db_session,
        auth_repo=auth_repo,
        refresh_repo=refresh_repo,
        reset_repo=reset_repo,
        rate_limiter=rate_limiter,
        role_resolver=role_resolver,
    )

    await _create_user_with_role(db_session, tenant, "2fa_roles@test.com", "CONTADOR")

    from sqlalchemy import select as _select
    au = (await db_session.execute(_select(AuthUser).where(AuthUser.email == "2fa_roles@test.com"))).scalar_one()
    au.is_2fa_enabled = True
    au.otp_secret = "JBSWY3DPEHPK3PXP"
    await db_session.commit()

    result = await svc.login("2fa_roles@test.com", "Secure123", "127.0.0.1")
    assert "requires_2fa" in result
    assert result["requires_2fa"] is True

    session_token = result["session_token"]
    from app.core.security import verify_access_token
    payload = verify_access_token(session_token)
    assert "roles" in payload
    assert "CONTADOR" in payload["roles"]
    assert payload.get("type") == "2fa_pending"


@pytest.mark.asyncio
async def test_login_includes_resolved_roles(db_session, tenant, auth_service_with_resolver):
    await _create_user_with_role(db_session, tenant, "login_roles@test.com", "PROFESOR")

    result = await auth_service_with_resolver.login(
        "login_roles@test.com", "Secure123", "127.0.0.1",
    )
    payload = _decode_token(result["access_token"])
    assert "PROFESOR" in payload.get("roles", [])


@pytest.mark.asyncio
async def test_login_without_role_resolver_returns_empty_roles(
    db_session, tenant, auth_service,
):
    await _create_user_with_role(db_session, tenant, "login_noresolver@test.com", "ADMIN")

    result = await auth_service.login(
        "login_noresolver@test.com", "Secure123", "127.0.0.1",
    )
    payload = _decode_token(result["access_token"])
    assert payload.get("roles", []) == []


@pytest.mark.asyncio
async def test_refresh_includes_resolved_roles(db_session, tenant, auth_service_with_resolver):
    await _create_user_with_role(db_session, tenant, "refresh_roles@test.com", "TUTOR")

    login_result = await auth_service_with_resolver.login(
        "refresh_roles@test.com", "Secure123", "127.0.0.1",
    )
    refresh_result = await auth_service_with_resolver.refresh(
        login_result["refresh_token"],
    )
    payload = _decode_token(refresh_result["access_token"])
    assert "TUTOR" in payload.get("roles", [])
