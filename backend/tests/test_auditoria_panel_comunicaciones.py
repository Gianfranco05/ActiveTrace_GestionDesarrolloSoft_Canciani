"""Tests for GET /api/auditoria/panel/estado-comunicaciones (Task 18 / 5.2)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.auditoria import router as auditoria_router
from app.core.dependencies import UserSession, get_current_user, get_db
from datetime import date as _date


def _safe_now():
    """Return noon UTC of today's local date — safe for date.today() range queries."""
    return datetime.combine(_date.today(), datetime.min.time().replace(hour=12), tzinfo=timezone.utc)


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(auditoria_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_perm(db_session, tenant):
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso

    rol = Rol(nombre="AUDITOR_TEST", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="auditoria:ver")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    return rol


async def _seed_comunicacion_data(db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.usuario import Usuario
    from app.models.materia import Materia
    from app.models.comunicacion import Comunicacion

    user_a = AuthUser(tenant_id=tenant.id, email="doc_a@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant.id, email="doc_b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    profile_a = Usuario(tenant_id=tenant.id, id=user_a.id, nombre="Doc", apellidos="Alpha")
    profile_b = Usuario(tenant_id=tenant.id, id=user_b.id, nombre="Doc", apellidos="Beta")
    db_session.add_all([profile_a, profile_b])

    mat = Materia(tenant_id=tenant.id, codigo="COM101", nombre="Comunicaciones I")
    db_session.add(mat)
    await db_session.commit()
    await db_session.refresh(mat)

    now = _safe_now()
    lote_id = uuid.uuid4()

    c1 = Comunicacion(
        tenant_id=tenant.id, lote_id=lote_id,
        enviado_por=user_a.id, materia_id=mat.id,
        destinatario="alumno1@test.com", asunto="Asunto 1", cuerpo="Cuerpo 1",
        estado="Enviado", created_at=now,
    )
    c2 = Comunicacion(
        tenant_id=tenant.id, lote_id=lote_id,
        enviado_por=user_a.id, materia_id=mat.id,
        destinatario="alumno2@test.com", asunto="Asunto 2", cuerpo="Cuerpo 2",
        estado="Pendiente", created_at=now,
    )
    c3 = Comunicacion(
        tenant_id=tenant.id, lote_id=lote_id,
        enviado_por=user_b.id, materia_id=mat.id,
        destinatario="alumno3@test.com", asunto="Asunto 3", cuerpo="Cuerpo 3",
        estado="Error", created_at=now,
    )
    db_session.add_all([c1, c2, c3])
    await db_session.commit()
    return user_a, user_b, mat


# ─── ALL TEACHERS IN RANGE ────────────────────────────────────────

@pytest.mark.asyncio
async def test_all_teachers_in_date_range(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, mat = await _seed_comunicacion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/estado-comunicaciones")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2

    user_a_item = next(i for i in data["items"] if i["usuario_id"] == str(user_a.id))
    user_b_item = next(i for i in data["items"] if i["usuario_id"] == str(user_b.id))

    assert user_a_item["enviado"] == 1
    assert user_a_item["pendiente"] == 1
    assert user_b_item["error"] == 1


# ─── FILTER BY MATERIA_ID ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_materia_id(http_client, test_app, db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.usuario import Usuario
    from app.models.materia import Materia
    from app.models.comunicacion import Comunicacion

    await _seed_perm(db_session, tenant)
    user = AuthUser(tenant_id=tenant.id, email="matfilt@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    profile = Usuario(tenant_id=tenant.id, id=user.id, nombre="Mat", apellidos="Filter")
    db_session.add(profile)

    mat_a = Materia(tenant_id=tenant.id, codigo="MATA", nombre="Materia A")
    mat_b = Materia(tenant_id=tenant.id, codigo="MATB", nombre="Materia B")
    db_session.add_all([mat_a, mat_b])
    await db_session.commit()
    await db_session.refresh(mat_a)
    await db_session.refresh(mat_b)

    now = _safe_now()
    lote = uuid.uuid4()
    c1 = Comunicacion(tenant_id=tenant.id, lote_id=lote, enviado_por=user.id,
                      materia_id=mat_a.id, destinatario="a@t.com",
                      asunto="A", cuerpo="A", estado="Enviado", created_at=now)
    c2 = Comunicacion(tenant_id=tenant.id, lote_id=lote, enviado_por=user.id,
                      materia_id=mat_b.id, destinatario="b@t.com",
                      asunto="B", cuerpo="B", estado="Pendiente", created_at=now)
    db_session.add_all([c1, c2])
    await db_session.commit()

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get(
        "/api/auditoria/panel/estado-comunicaciones",
        params={"materia_id": str(mat_a.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["materia_id"] == str(mat_a.id)


# ─── COORDINADOR SCOPE ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_coordinador_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_comunicacion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/panel/estado-comunicaciones")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["usuario_id"] == str(user_a.id)


# ─── ADMIN SCOPE ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_comunicacion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/estado-comunicaciones")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2


# ─── NO COMMUNICATION DATA ────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_communication_data_empty(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="nocom@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/estado-comunicaciones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


# ─── COMUNICACION TABLE NOT AVAILABLE ─────────────────────────────

@pytest.mark.asyncio
async def test_comunicacion_import_error_returns_empty(tenant):
    """Test graceful degradation when Comunicacion model cannot be imported."""
    from app.services.auditoria.metrics_service import MetricsService
    from sqlalchemy.ext.asyncio import AsyncSession

    from unittest.mock import AsyncMock

    mock_session = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    svc = MetricsService(
        session=mock_session,
        tenant_id=tenant.id,
        user_id=user_id,
        is_global_scope=True,
    )

    import builtins as _bi
    _real_import = _bi.__import__

    def _import_mock(name, *args, **kwargs):
        if name == "app.models.comunicacion":
            raise ImportError("No module")
        return _real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=_import_mock):
        result = await svc.estado_comunicaciones_por_docente()
        assert len(result.items) == 0


@pytest.mark.asyncio
async def test_comunicacion_model_none_returns_empty(tenant):
    """Test graceful degradation when Comunicacion attribute is None."""
    from app.services.auditoria.metrics_service import MetricsService
    from sqlalchemy.ext.asyncio import AsyncSession
    from unittest.mock import AsyncMock, MagicMock

    mock_session = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()

    svc = MetricsService(
        session=mock_session,
        tenant_id=tenant.id,
        user_id=user_id,
        is_global_scope=True,
    )

    fake_mod = MagicMock()
    fake_mod.Comunicacion = None

    import builtins as _bi
    _real_import = _bi.__import__

    def _import_mock(name, *args, **kwargs):
        if name == "app.models.comunicacion":
            return fake_mod
        return _real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=_import_mock):
        result = await svc.estado_comunicaciones_por_docente()
        assert len(result.items) == 0
