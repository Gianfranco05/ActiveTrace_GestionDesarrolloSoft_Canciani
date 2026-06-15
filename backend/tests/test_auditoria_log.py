"""Tests for GET /log endpoint (C-19 auditoria log)."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auditoria import router as auditoria_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.asignacion import Asignacion
from app.models.audit_log import AuditLog
from app.models.auth_user import AuthUser
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.usuario import Usuario


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    application = FastAPI()
    application.include_router(auditoria_router)

    async def _get_db_override():
        yield db_session

    application.dependency_overrides[get_db] = _get_db_override
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _ensure_rol_permiso(
    db_session: AsyncSession,
    tenant: Tenant,
    role_name: str,
    permiso_codigo: str,
) -> Rol:
    from sqlalchemy import select as _select

    result = await db_session.execute(
        _select(Rol).where(
            Rol.nombre == role_name,
            Rol.tenant_id == tenant.id,
            Rol.deleted_at.is_(None),
        )
    )
    rol = result.scalar_one_or_none()
    if rol is None:
        rol = Rol(nombre=role_name, tenant_id=tenant.id)
        db_session.add(rol)
        await db_session.flush()

    result = await db_session.execute(
        _select(Permiso).where(Permiso.codigo == permiso_codigo)
    )
    permiso = result.scalar_one_or_none()
    if permiso is None:
        permiso = Permiso(codigo=permiso_codigo)
        db_session.add(permiso)
        await db_session.flush()

    result = await db_session.execute(
        _select(RolPermiso).where(
            RolPermiso.rol_id == rol.id,
            RolPermiso.permiso_id == permiso.id,
        )
    )
    rp = result.scalar_one_or_none()
    if rp is None:
        rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
        db_session.add(rp)

    await db_session.commit()
    return rol


async def _create_user(
    db_session: AsyncSession,
    tenant: Tenant,
    email: str,
    nombre: str,
    apellidos: str,
    role_name: str,
    permiso_codigo: str = "auditoria:ver",
) -> tuple:
    rol = await _ensure_rol_permiso(db_session, tenant, role_name, permiso_codigo)

    au = AuthUser(tenant_id=tenant.id, email=email, password_hash="x")
    db_session.add(au)
    await db_session.flush()

    u = Usuario(id=au.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos)
    db_session.add(u)
    await db_session.flush()

    asignacion = Asignacion(
        usuario_id=u.id,
        rol_id=rol.id,
        tenant_id=tenant.id,
        vig_desde=date.today(),
    )
    db_session.add(asignacion)
    await db_session.commit()
    return u, rol


async def _create_materia(
    db_session: AsyncSession, tenant: Tenant, codigo: str, nombre: str
) -> Materia:
    m = Materia(codigo=codigo, nombre=nombre, tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    return m


async def _create_audit_log(
    db_session: AsyncSession,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    accion: str,
    materia_id: uuid.UUID | None = None,
    fecha: datetime | None = None,
    detalle: dict | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    filas_afectadas: int = 0,
) -> AuditLog:
    if fecha is None:
        fecha = datetime.now(timezone.utc)
    al = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        accion=accion,
        materia_id=materia_id,
        fecha_hora=fecha,
        detalle=detalle,
        ip=ip,
        user_agent=user_agent,
        filas_afectadas=filas_afectadas,
    )
    db_session.add(al)
    await db_session.commit()
    return al


def _override_user(app: FastAPI, usuario: Usuario, roles: list[str]):
    app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=usuario.id,
        tenant_id=usuario.tenant_id,
        roles=roles,
    )


def _no_auth(app: FastAPI):
    async def _raises_401():
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")

    app.dependency_overrides[get_current_user] = _raises_401


# ============================================================
# 6.1 — GET /log endpoint
# ============================================================

class TestLogSinFiltros:

    @pytest.mark.asyncio
    async def test_no_filters_default_pagination(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log1@test.com", "Log", "One", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "login")
        await _create_audit_log(db_session, tenant.id, admin.id, "view")

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] == 2
        assert data["offset"] == 0
        assert data["limit"] == 50
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_date_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log2@test.com", "Date", "Filter", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        now = datetime.now(timezone.utc)
        old = now - timedelta(days=60)
        await _create_audit_log(db_session, tenant.id, admin.id, "reciente", fecha=now)
        await _create_audit_log(db_session, tenant.id, admin.id, "antigua", fecha=old)

        desde = (now - timedelta(days=7)).isoformat()
        hasta = (now + timedelta(days=1)).isoformat()
        resp = await client.get(
            "/api/auditoria/log",
            params={"fecha_desde": desde, "fecha_hasta": hasta},
        )
        assert resp.status_code == 200
        data = resp.json()
        acciones = [i["accion"] for i in data["items"]]
        assert "reciente" in acciones
        assert "antigua" not in acciones

    @pytest.mark.asyncio
    async def test_materia_id_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log3@test.com", "Mat", "Filtro", "ADMIN"
        )
        mat_a = await _create_materia(db_session, tenant, "LF1", "Filtro Uno")
        mat_b = await _create_materia(db_session, tenant, "LF2", "Filtro Dos")

        await _create_audit_log(db_session, tenant.id, admin.id, "a1", materia_id=mat_a.id)
        await _create_audit_log(db_session, tenant.id, admin.id, "a2", materia_id=mat_b.id)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get(
            "/api/auditoria/log",
            params={"materia_id": str(mat_a.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["accion"] == "a1"

    @pytest.mark.asyncio
    async def test_usuario_id_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log4a@test.com", "Admin", "UF", "ADMIN"
        )
        other, _ = await _create_user(
            db_session, tenant, "log4b@test.com", "Other", "UF", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, admin.id, "admin_act")
        await _create_audit_log(db_session, tenant.id, other.id, "other_act")

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get(
            "/api/auditoria/log",
            params={"usuario_id": str(other.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["actor_id"] == str(other.id)

    @pytest.mark.asyncio
    async def test_accion_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log5@test.com", "Acc", "Filter", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "login")
        await _create_audit_log(db_session, tenant.id, admin.id, "calificar")
        await _create_audit_log(db_session, tenant.id, admin.id, "logout")

        resp = await client.get(
            "/api/auditoria/log",
            params={"accion": "calificar"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["accion"] == "calificar"

    @pytest.mark.asyncio
    async def test_ip_partial_match(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log6@test.com", "IP", "Match", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "a", ip="192.168.1.100")
        await _create_audit_log(db_session, tenant.id, admin.id, "b", ip="10.0.0.1")

        resp = await client.get(
            "/api/auditoria/log",
            params={"ip": "192.168"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["ip"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_combined_filters(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log7@test.com", "Comb", "Filters", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "COMB", "Combinado")
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "login", materia_id=mat.id)
        await _create_audit_log(db_session, tenant.id, admin.id, "view", materia_id=mat.id)

        resp = await client.get(
            "/api/auditoria/log",
            params={
                "accion": "login",
                "materia_id": str(mat.id),
                "usuario_id": str(admin.id),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["accion"] == "login"

    @pytest.mark.asyncio
    async def test_offset_limit(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log8@test.com", "Page", "Test", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        for i in range(5):
            fecha = datetime.now(timezone.utc) - timedelta(hours=i)
            await _create_audit_log(db_session, tenant.id, admin.id, f"acc_{i}", fecha=fecha)

        resp = await client.get(
            "/api/auditoria/log",
            params={"offset": 1, "limit": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["offset"] == 1
        assert data["limit"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_coord_scope(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "log9a@test.com", "Coord", "Log", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "log9b@test.com", "Other", "Log", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, coord.id, "mine")
        await _create_audit_log(db_session, tenant.id, other.id, "theirs")

        _override_user(app, coord, ["COORDINADOR"])

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["accion"] == "mine"

    @pytest.mark.asyncio
    async def test_admin_scope(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log10a@test.com", "Admin", "Log", "ADMIN"
        )
        other, _ = await _create_user(
            db_session, tenant, "log10b@test.com", "Other", "Log", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, admin.id, "admin")
        await _create_audit_log(db_session, tenant.id, other.id, "other")

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_403_sin_permiso(
        self, client, app, db_session, tenant
    ):
        user, _ = await _create_user(
            db_session, tenant, "log11@test.com", "No", "Perm", "ALUMNO", "otro:permiso"
        )
        _override_user(app, user, ["ALUMNO"])

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_405_post_put_delete(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "log12@test.com", "Method", "Check", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        resp = await client.post("/api/auditoria/log")
        assert resp.status_code == 405

        resp = await client.put("/api/auditoria/log")
        assert resp.status_code == 405

        resp = await client.delete("/api/auditoria/log")
        assert resp.status_code == 405


# ============================================================
# 6.2 — Name resolution
# ============================================================

class TestLogNameResolution:

    @pytest.mark.asyncio
    async def test_actor_nombre_present(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "nr1@test.com", "Nombre", "Resuelto", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "test")

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["actor_nombre"] == "Nombre Resuelto"

    @pytest.mark.asyncio
    async def test_materia_nombre_present(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "nr2@test.com", "Mat", "Nombre", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "NMR", "Nombre Resuelto Mat")
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "test", materia_id=mat.id)

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["materia_nombre"] == "Nombre Resuelto Mat"

    @pytest.mark.asyncio
    async def test_deleted_actor_null_name(
        self, client, app, db_session, tenant
    ):
        """When actor is soft-deleted, actor_nombre is null (spec requirement)."""
        admin, _ = await _create_user(
            db_session, tenant, "nr3@test.com", "Deleted", "Actor", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "test")

        from sqlalchemy import update
        stmt = update(AuthUser).where(AuthUser.id == admin.id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        await db_session.commit()

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["actor_nombre"] is None

    @pytest.mark.asyncio
    async def test_null_materia_null_name(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "nr4@test.com", "Null", "Materia", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "test", materia_id=None)

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["materia_nombre"] is None
        assert data["items"][0]["materia_id"] is None

    @pytest.mark.asyncio
    async def test_deleted_materia_null_name(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "nr5@test.com", "DelMat", "Name", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "DMN", "Materia Borrada")
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, admin.id, "test", materia_id=mat.id)

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["materia_nombre"] == "Materia Borrada"

        from sqlalchemy import update
        stmt = update(Materia).where(Materia.id == mat.id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        await db_session.commit()

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["materia_nombre"] is None

    @pytest.mark.asyncio
    async def test_actor_sin_perfil_usuario_null_name(
        self, client, app, db_session, tenant
    ):
        for_email = f"nr6-{uuid.uuid4().hex[:8]}@test.com"
        au = AuthUser(tenant_id=tenant.id, email=for_email, password_hash="x")
        db_session.add(au)
        await db_session.flush()
        await db_session.commit()

        admin, _ = await _create_user(
            db_session, tenant, "nr6a@test.com", "Admin", "SPU", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        await _create_audit_log(db_session, tenant.id, au.id, "test")

        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        found = [i for i in data["items"] if i["actor_id"] == str(au.id)]
        assert len(found) == 1
        assert found[0]["actor_nombre"] is None
