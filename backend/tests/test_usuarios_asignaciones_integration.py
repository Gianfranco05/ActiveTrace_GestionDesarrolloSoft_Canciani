"""Integration test: User → Asignacion → Auth → PII whole flow."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.v1.routers.usuarios import router as usuarios_router
from app.api.v1.routers.asignaciones import router as asignaciones_router
from app.api.v1.routers.auth import router as auth_router, _get_auth_service
from app.core.dependencies import UserSession, get_current_user, get_db
from app.core.rate_limiter import RateLimiter
from app.core.security import verify_access_token
from app.repositories.auth_repository import AuthRepository, RefreshTokenRepository, ResetTokenRepository
from app.services.auth_service import AuthService
from app.services.role_resolver import RoleResolver
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from datetime import date, timedelta


@pytest.fixture
def test_app(db_session, tenant):
    app = FastAPI()
    app.include_router(usuarios_router)
    app.include_router(asignaciones_router)
    app.include_router(auth_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override

    auth_repo = AuthRepository(db_session, tenant.id)
    refresh_repo = RefreshTokenRepository(db_session, tenant.id)
    reset_repo = ResetTokenRepository(db_session, tenant.id)
    role_resolver = RoleResolver(db_session, tenant.id)

    async def _override_auth_service():
        return AuthService(
            session=db_session,
            auth_repo=auth_repo,
            refresh_repo=refresh_repo,
            reset_repo=reset_repo,
            rate_limiter=RateLimiter(max_attempts=10, window_seconds=60),
            role_resolver=role_resolver,
        )

    app.dependency_overrides[_get_auth_service] = _override_auth_service
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_roles_and_permissions(db_session, tenant) -> tuple[Rol, Rol]:
    admin_rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    prof_rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add_all([admin_rol, prof_rol])

    permiso = Permiso(codigo="usuarios:gestionar")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(admin_rol)
    await db_session.refresh(prof_rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=admin_rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()

    return admin_rol, prof_rol


def _admin_session(tenant) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["ADMIN"],
    )


@pytest.mark.asyncio
async def test_full_flow_create_asignacion_and_verify_role_in_token(
    http_client, test_app, db_session, tenant,
):
    """End-to-end: create user → assign role → login → verify role in JWT."""
    admin_rol, prof_rol = await _seed_roles_and_permissions(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    # Create usuario via API
    create_resp = await http_client.post(
        "/api/v1/admin/usuarios",
        json={
            "email": "integracion@test.com",
            "password": "Secure123",
            "nombre": "Integra",
            "apellidos": "Test",
            "dni": "87654321",
            "cuil": "20-87654321-0",
        },
    )
    assert create_resp.status_code == 201
    usuario_id = create_resp.json()["id"]

    # Create asignacion assigning PROFESOR role
    asignacion_resp = await http_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": usuario_id,
            "rol_id": str(prof_rol.id),
            "vig_desde": (date.today() - timedelta(days=1)).isoformat(),
            "vig_hasta": (date.today() + timedelta(days=365)).isoformat(),
        },
    )
    assert asignacion_resp.status_code == 201

    # Login and verify the token contains the resolved role
    login_resp = await http_client.post(
        "/api/auth/login",
        json={"email": "integracion@test.com", "password": "Secure123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    payload = verify_access_token(token)
    assert "roles" in payload
    assert "PROFESOR" in payload["roles"]


@pytest.mark.asyncio
async def test_pii_encrypted_in_db_and_safe_response_excludes_pii(
    http_client, test_app, db_session, tenant,
):
    """Verify PII is encrypted at rest and safe endpoint omits it."""
    admin_rol, _ = await _seed_roles_and_permissions(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    create_resp = await http_client.post(
        "/api/v1/admin/usuarios",
        json={
            "email": "pii_check@test.com",
            "password": "Secure456",
            "nombre": "Pii",
            "apellidos": "Checker",
            "dni": "11223344",
            "cuil": "20-11223344-5",
            "cbu": "0123456789012345678901",
        },
    )
    assert create_resp.status_code == 201

    # Verify PII is encrypted in DB (raw query)
    auth_user = (
        await db_session.execute(
            select(AuthUser).where(AuthUser.email == "pii_check@test.com"),
        )
    ).scalar_one()

    usuario_db = (
        await db_session.execute(
            select(Usuario).where(Usuario.id == auth_user.id),
        )
    ).scalar_one()
    assert usuario_db.dni != "11223344"
    assert usuario_db.cuil != "20-11223344-5"
    assert usuario_db.cbu != "0123456789012345678901"

    # Safe list endpoint excludes PII
    list_resp = await http_client.get("/api/v1/admin/usuarios")
    assert list_resp.status_code == 200
    item = list_resp.json()["items"][0]
    assert "dni" not in item
    assert "cuil" not in item
    assert "cbu" not in item
    assert item["nombre"] == "Pii"
