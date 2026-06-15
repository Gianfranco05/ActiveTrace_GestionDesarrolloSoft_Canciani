"""Tests for panel-interacciones endpoints (C-19)."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserSession, get_current_user, get_db
from app.main import create_app
from app.models.asignacion import Asignacion
from app.models.audit_log import AuditLog
from app.models.auth_user import AuthUser
from app.models.comunicacion import Comunicacion
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from datetime import date as _date


def _safe_now():
    """Return noon UTC of today's local date — safe for date.today() range queries."""
    return datetime.combine(_date.today(), datetime.min.time().replace(hour=12), tzinfo=timezone.utc)


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    application = create_app()

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
) -> AuditLog:
    if fecha is None:
        fecha = _safe_now()
    al = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        accion=accion,
        materia_id=materia_id,
        fecha_hora=fecha,
        detalle=detalle,
        ip=ip,
        user_agent=user_agent,
    )
    db_session.add(al)
    await db_session.commit()
    return al


async def _create_comunicacion(
    db_session: AsyncSession,
    tenant: Tenant,
    enviado_por: uuid.UUID,
    materia_id: uuid.UUID | None,
    estado: str,
    lote_id: uuid.UUID | None = None,
) -> Comunicacion:
    c = Comunicacion(
        tenant_id=tenant.id,
        lote_id=lote_id or uuid.uuid4(),
        enviado_por=enviado_por,
        materia_id=materia_id,
        destinatario="test@example.com",
        asunto="Test subject",
        cuerpo="Test body",
        estado=estado,
        created_at=_safe_now(),
    )
    db_session.add(c)
    await db_session.commit()
    return c


def _override_user(app: FastAPI, usuario: Usuario, roles: list[str]):
    app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=usuario.id,
        tenant_id=usuario.tenant_id,
        roles=roles,
    )


# ============================================================
# 5.1 — acciones_por_dia
# ============================================================

class TestAccionesPorDia:

    @pytest.mark.asyncio
    async def test_default_30_days(
        self, client, app, db_session, tenant
    ):
        user, _ = await _create_user(
            db_session, tenant, "a1@test.com", "Uno", "Test", "COORDINADOR"
        )
        _override_user(app, user, ["COORDINADOR"])

        await _create_audit_log(db_session, tenant.id, user.id, "login")
        await _create_audit_log(db_session, tenant.id, user.id, "view")

        resp = await client.get("/api/auditoria/panel/acciones-por-dia")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1
        assert "desde" in data
        assert "hasta" in data
        for item in data["items"]:
            assert "dia" in item
            assert "total_acciones" in item
            assert isinstance(item["total_acciones"], int)

    @pytest.mark.asyncio
    async def test_custom_range(
        self, client, app, db_session, tenant
    ):
        user, _ = await _create_user(
            db_session, tenant, "a2@test.com", "Dos", "Test", "COORDINADOR"
        )
        _override_user(app, user, ["COORDINADOR"])

        dentro = _safe_now()
        await _create_audit_log(db_session, tenant.id, user.id, "login", fecha=dentro)

        fuera = _safe_now() - timedelta(days=60)
        await _create_audit_log(db_session, tenant.id, user.id, "old", fecha=fuera)

        desde = (date.today() - timedelta(days=7)).isoformat()
        hasta = date.today().isoformat()
        resp = await client.get(
            "/api/auditoria/panel/acciones-por-dia",
            params={"fecha_desde": desde, "fecha_hasta": hasta},
        )
        assert resp.status_code == 200
        data = resp.json()
        all_total = sum(item["total_acciones"] for item in data["items"])
        assert all_total >= 1

    @pytest.mark.asyncio
    async def test_coord_scope_filtered(
        self, client, app, db_session, tenant
    ):
        user_a, _ = await _create_user(
            db_session, tenant, "ca@test.com", "CoordA", "Test", "COORDINADOR"
        )
        user_b, _ = await _create_user(
            db_session, tenant, "cb@test.com", "CoordB", "Test", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, user_a.id, "login")
        await _create_audit_log(db_session, tenant.id, user_b.id, "view")

        _override_user(app, user_a, ["COORDINADOR"])

        resp = await client.get("/api/auditoria/panel/acciones-por-dia")
        assert resp.status_code == 200
        data = resp.json()
        all_total = sum(item["total_acciones"] for item in data["items"])
        assert all_total == 1

    @pytest.mark.asyncio
    async def test_admin_global_scope(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "ad@test.com", "Admin", "User", "ADMIN"
        )
        user_b, _ = await _create_user(
            db_session, tenant, "b2@test.com", "B", "Two", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, admin.id, "login")
        await _create_audit_log(db_session, tenant.id, user_b.id, "view")

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/acciones-por-dia")
        assert resp.status_code == 200
        data = resp.json()
        all_total = sum(item["total_acciones"] for item in data["items"])
        assert all_total == 2

    @pytest.mark.asyncio
    async def test_empty_data(
        self, client, app, db_session, tenant
    ):
        user, _ = await _create_user(
            db_session, tenant, "e1@test.com", "Empty", "Test", "COORDINADOR"
        )
        _override_user(app, user, ["COORDINADOR"])

        resp = await client.get("/api/auditoria/panel/acciones-por-dia")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert "desde" in data
        assert "hasta" in data


# ============================================================
# 5.1b — CRITICAL: cross-user scope isolation across ALL panel endpoints
# ============================================================

class TestScopeIsolationAllEndpoints:

    @pytest.mark.asyncio
    async def test_coord_sees_only_own_acciones_por_dia(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "iso-a@test.com", "IsoA", "Test", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "iso-b@test.com", "IsoB", "Test", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, coord.id, "login")
        await _create_audit_log(db_session, tenant.id, other.id, "view")

        _override_user(app, coord, ["COORDINADOR"])
        resp = await client.get("/api/auditoria/panel/acciones-por-dia")
        assert resp.status_code == 200
        total = sum(i["total_acciones"] for i in resp.json()["items"])
        assert total == 1

        await _ensure_rol_permiso(db_session, tenant, "ADMIN", "auditoria:ver")
        _override_user(app, other, ["ADMIN"])
        resp = await client.get("/api/auditoria/panel/acciones-por-dia")
        assert resp.status_code == 200
        total = sum(i["total_acciones"] for i in resp.json()["items"])
        assert total == 2

    @pytest.mark.asyncio
    async def test_coord_sees_only_own_interacciones(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "iso2-a@test.com", "Iso2A", "Test", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "iso2-b@test.com", "Iso2B", "Test", "COORDINADOR"
        )
        mat = await _create_materia(db_session, tenant, "M1", "Matemática")

        await _create_audit_log(db_session, tenant.id, coord.id, "calificar", materia_id=mat.id)
        await _create_audit_log(db_session, tenant.id, other.id, "calificar", materia_id=mat.id)

        _override_user(app, coord, ["COORDINADOR"])
        resp = await client.get("/api/auditoria/panel/interacciones")
        assert resp.status_code == 200
        total = sum(i["cantidad"] for i in resp.json()["items"])
        assert total == 1

        await _ensure_rol_permiso(db_session, tenant, "ADMIN", "auditoria:ver")
        _override_user(app, other, ["ADMIN"])
        resp = await client.get("/api/auditoria/panel/interacciones")
        assert resp.status_code == 200
        total = sum(i["cantidad"] for i in resp.json()["items"])
        assert total == 2

    @pytest.mark.asyncio
    async def test_coord_sees_only_own_ultimas_acciones(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "iso3-a@test.com", "Iso3A", "Test", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "iso3-b@test.com", "Iso3B", "Test", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, coord.id, "login")
        await _create_audit_log(db_session, tenant.id, other.id, "view")

        _override_user(app, coord, ["COORDINADOR"])
        resp = await client.get("/api/auditoria/panel/ultimas-acciones")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

        await _ensure_rol_permiso(db_session, tenant, "ADMIN", "auditoria:ver")
        _override_user(app, other, ["ADMIN"])
        resp = await client.get("/api/auditoria/panel/ultimas-acciones")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 2

    @pytest.mark.asyncio
    async def test_coord_sees_only_own_estado_comunicaciones(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "iso4-a@test.com", "Iso4A", "Test", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "iso4-b@test.com", "Iso4B", "Test", "COORDINADOR"
        )
        mat = await _create_materia(db_session, tenant, "MC", "Comunicación")

        lote_a = uuid.uuid4()
        lote_b = uuid.uuid4()
        await _create_comunicacion(db_session, tenant, coord.id, mat.id, "Pendiente", lote_id=lote_a)
        await _create_comunicacion(db_session, tenant, other.id, mat.id, "Enviado", lote_id=lote_b)

        _override_user(app, coord, ["COORDINADOR"])
        resp = await client.get("/api/auditoria/panel/estado-comunicaciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["usuario_nombre"] == "Iso4A Test"

        await _ensure_rol_permiso(db_session, tenant, "ADMIN", "auditoria:ver")
        _override_user(app, coord, ["ADMIN"])
        resp = await client.get("/api/auditoria/panel/estado-comunicaciones")
        assert resp.status_code == 200
        data = resp.json()
        total_pendientes = sum(item["pendiente"] for item in data["items"])
        total_enviados = sum(item["enviado"] for item in data["items"])
        assert total_pendientes + total_enviados == 2

    @pytest.mark.asyncio
    async def test_coord_sees_only_own_log(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "iso5-a@test.com", "Iso5A", "Test", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "iso5-b@test.com", "Iso5B", "Test", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, coord.id, "login")
        await _create_audit_log(db_session, tenant.id, other.id, "view")

        _override_user(app, coord, ["COORDINADOR"])
        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        await _ensure_rol_permiso(db_session, tenant, "ADMIN", "auditoria:ver")
        _override_user(app, coord, ["ADMIN"])
        resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2


# ============================================================
# 5.2 — estado_comunicaciones_por_docente
# ============================================================

class TestEstadoComunicaciones:

    async def _setup_comms(self, db_session, tenant, mat, user) -> list[int]:
        await _create_comunicacion(db_session, tenant, user.id, mat.id, "Pendiente", lote_id=uuid.uuid4())
        await _create_comunicacion(db_session, tenant, user.id, mat.id, "Enviado", lote_id=uuid.uuid4())
        await _create_comunicacion(db_session, tenant, user.id, mat.id, "Pendiente", lote_id=uuid.uuid4())
        await _create_comunicacion(db_session, tenant, user.id, mat.id, "Error", lote_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_no_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "ec1@test.com", "EC1", "Test", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "MAT_RTA", "Matemática")

        await self._setup_comms(db_session, tenant, mat, admin)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/estado-comunicaciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        row = data["items"][0]
        assert row["pendiente"] == 2
        assert row["enviado"] == 1
        assert row["error"] == 1
        assert row["usuario_nombre"] == "EC1 Test"
        assert row["materia_nombre"] == "Matemática"

    @pytest.mark.asyncio
    async def test_filtered_by_materia(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "ec2@test.com", "EC2", "Test", "ADMIN"
        )
        mat_a = await _create_materia(db_session, tenant, "MA", "Primera")
        mat_b = await _create_materia(db_session, tenant, "MB", "Segunda")

        await _create_comunicacion(db_session, tenant, admin.id, mat_a.id, "Pendiente", lote_id=uuid.uuid4())
        await _create_comunicacion(db_session, tenant, admin.id, mat_b.id, "Enviado", lote_id=uuid.uuid4())

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get(
            "/api/auditoria/panel/estado-comunicaciones",
            params={"materia_id": str(mat_a.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["pendiente"] == 1
        assert data["items"][0]["enviado"] == 0

    @pytest.mark.asyncio
    async def test_coord_scope(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "ec3a@test.com", "Coord", "A", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "ec3b@test.com", "Other", "B", "COORDINADOR"
        )
        mat = await _create_materia(db_session, tenant, "MCS", "MateriaScope")

        await _create_comunicacion(db_session, tenant, coord.id, mat.id, "Pendiente", lote_id=uuid.uuid4())
        await _create_comunicacion(db_session, tenant, other.id, mat.id, "Enviado", lote_id=uuid.uuid4())

        _override_user(app, coord, ["COORDINADOR"])

        resp = await client.get("/api/auditoria/panel/estado-comunicaciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        row = data["items"][0]
        assert row["pendiente"] == 1
        assert row["enviado"] == 0

    @pytest.mark.asyncio
    async def test_admin_scope(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "ec4a@test.com", "Admin", "User", "ADMIN"
        )
        other, _ = await _create_user(
            db_session, tenant, "ec4b@test.com", "Other", "User", "COORDINADOR"
        )
        mat = await _create_materia(db_session, tenant, "MAD", "AdminScope")

        await _create_comunicacion(db_session, tenant, admin.id, mat.id, "Pendiente", lote_id=uuid.uuid4())
        await _create_comunicacion(db_session, tenant, other.id, mat.id, "Enviado", lote_id=uuid.uuid4())

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/estado-comunicaciones")
        assert resp.status_code == 200
        data = resp.json()
        all_pends = sum(item["pendiente"] for item in data["items"])
        all_sents = sum(item["enviado"] for item in data["items"])
        assert all_pends + all_sents == 2

    @pytest.mark.asyncio
    async def test_empty_data(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "ec5@test.com", "Empty", "Comms", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/estado-comunicaciones")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# ============================================================
# 5.3 — interacciones_por_docente_materia
# ============================================================

class TestInteraccionesPorDocenteMateria:

    @pytest.mark.asyncio
    async def test_correct_grouping(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "i1@test.com", "I1", "Test", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "INT_TEST", "Interacción")

        await _create_audit_log(db_session, tenant.id, admin.id, "calificar", materia_id=mat.id)
        await _create_audit_log(db_session, tenant.id, admin.id, "calificar", materia_id=mat.id)
        await _create_audit_log(db_session, tenant.id, admin.id, "revisar", materia_id=mat.id)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/interacciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        acc_calificar = [i for i in data["items"] if i["accion"] == "calificar"]
        acc_revisar = [i for i in data["items"] if i["accion"] == "revisar"]
        assert len(acc_calificar) == 1
        assert acc_calificar[0]["cantidad"] == 2
        assert len(acc_revisar) == 1
        assert acc_revisar[0]["cantidad"] == 1

    @pytest.mark.asyncio
    async def test_coord_scope(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "i2a@test.com", "IC", "A", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "i2b@test.com", "IC", "B", "COORDINADOR"
        )
        mat = await _create_materia(db_session, tenant, "IS_A", "ScopeA")

        await _create_audit_log(db_session, tenant.id, coord.id, "login", materia_id=mat.id)
        await _create_audit_log(db_session, tenant.id, other.id, "login", materia_id=mat.id)

        _override_user(app, coord, ["COORDINADOR"])

        resp = await client.get("/api/auditoria/panel/interacciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["usuario_nombre"] == "IC A"
        total = sum(i["cantidad"] for i in data["items"])
        assert total == 1

    @pytest.mark.asyncio
    async def test_admin_scope(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "i3a@test.com", "Admin", "I", "ADMIN"
        )
        other, _ = await _create_user(
            db_session, tenant, "i3b@test.com", "Other", "I", "COORDINADOR"
        )
        mat = await _create_materia(db_session, tenant, "ISA2", "ScopeAdmin")

        await _create_audit_log(db_session, tenant.id, admin.id, "login", materia_id=mat.id)
        await _create_audit_log(db_session, tenant.id, other.id, "login", materia_id=mat.id)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/interacciones")
        assert resp.status_code == 200
        data = resp.json()
        total = sum(i["cantidad"] for i in data["items"])
        assert total == 2

    @pytest.mark.asyncio
    async def test_empty_data(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "i4@test.com", "Empty", "I", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/interacciones")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# ============================================================
# 5.4 — ultimas_acciones
# ============================================================

class TestUltimasAcciones:

    async def _seed_actions(
        self, db_session, tenant, user, mat
    ) -> list[AuditLog]:
        logs = []
        for i in range(5):
            fecha = _safe_now() - timedelta(hours=i)
            al = await _create_audit_log(
                db_session, tenant.id, user.id,
                f"accion_{i}", materia_id=mat.id, fecha=fecha,
                ip=f"10.0.0.{i}", user_agent=f"agent_{i}",
                detalle={"step": i},
            )
            logs.append(al)
        return logs

    @pytest.mark.asyncio
    async def test_default_limit_200(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "u1@test.com", "U1", "Test", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "UL1", "Limits")

        await self._seed_actions(db_session, tenant, admin, mat)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/ultimas-acciones")
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_registros"] == 200
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_custom_limit(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "u2@test.com", "U2", "Test", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "UL2", "CustomLimit")

        await self._seed_actions(db_session, tenant, admin, mat)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get(
            "/api/auditoria/panel/ultimas-acciones",
            params={"limit": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_registros"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_cap_1000(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "u3@test.com", "U3", "Test", "ADMIN"
        )
        _override_user(app, admin, ["ADMIN"])

        resp = await client.get(
            "/api/auditoria/panel/ultimas-acciones",
            params={"limit": 1000},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_registros"] == 1000

    @pytest.mark.asyncio
    async def test_date_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "u4@test.com", "U4", "Test", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "UL4", "DateFilter")

        in_range = _safe_now() - timedelta(days=2)
        out_range = _safe_now() - timedelta(days=60)
        await _create_audit_log(db_session, tenant.id, admin.id, "reciente", materia_id=mat.id, fecha=in_range)
        await _create_audit_log(db_session, tenant.id, admin.id, "antigua", materia_id=mat.id, fecha=out_range)

        _override_user(app, admin, ["ADMIN"])

        desde = (date.today() - timedelta(days=7)).isoformat()
        hasta = date.today().isoformat()
        resp = await client.get(
            "/api/auditoria/panel/ultimas-acciones",
            params={"fecha_desde": desde, "fecha_hasta": hasta},
        )
        assert resp.status_code == 200
        data = resp.json()
        acciones = [i["accion"] for i in data["items"]]
        assert "reciente" in acciones
        assert "antigua" not in acciones

    @pytest.mark.asyncio
    async def test_user_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "u5a@test.com", "U5A", "Test", "ADMIN"
        )
        other, _ = await _create_user(
            db_session, tenant, "u5b@test.com", "U5B", "Test", "COORDINADOR"
        )
        mat = await _create_materia(db_session, tenant, "UL5", "UserFilter")

        await _create_audit_log(db_session, tenant.id, admin.id, "admin_action", materia_id=mat.id)
        await _create_audit_log(db_session, tenant.id, other.id, "other_action", materia_id=mat.id)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get(
            "/api/auditoria/panel/ultimas-acciones",
            params={"usuario_id": str(other.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["actor_nombre"] == "U5B Test"

    @pytest.mark.asyncio
    async def test_materia_filter(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "u6@test.com", "U6", "Test", "ADMIN"
        )
        mat_a = await _create_materia(db_session, tenant, "MA_F", "Física")
        mat_b = await _create_materia(db_session, tenant, "MB_Q", "Química")

        await _create_audit_log(db_session, tenant.id, admin.id, "a1", materia_id=mat_a.id)
        await _create_audit_log(db_session, tenant.id, admin.id, "a2", materia_id=mat_b.id)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get(
            "/api/auditoria/panel/ultimas-acciones",
            params={"materia_id": str(mat_a.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["materia_nombre"] == "Física"

    @pytest.mark.asyncio
    async def test_coord_scope(
        self, client, app, db_session, tenant
    ):
        coord, _ = await _create_user(
            db_session, tenant, "u7a@test.com", "Coord", "U", "COORDINADOR"
        )
        other, _ = await _create_user(
            db_session, tenant, "u7b@test.com", "Other", "U", "COORDINADOR"
        )

        await _create_audit_log(db_session, tenant.id, coord.id, "mine")
        await _create_audit_log(db_session, tenant.id, other.id, "theirs")

        _override_user(app, coord, ["COORDINADOR"])

        resp = await client.get("/api/auditoria/panel/ultimas-acciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["accion"] == "mine"

    @pytest.mark.asyncio
    async def test_name_resolution(
        self, client, app, db_session, tenant
    ):
        admin, _ = await _create_user(
            db_session, tenant, "u8@test.com", "Nombre", "Completo", "ADMIN"
        )
        mat = await _create_materia(db_session, tenant, "RESNAME", "Resolución Nombres")

        await _create_audit_log(db_session, tenant.id, admin.id, "test", materia_id=mat.id)

        _override_user(app, admin, ["ADMIN"])

        resp = await client.get("/api/auditoria/panel/ultimas-acciones")
        assert resp.status_code == 200
        data = resp.json()
        item = data["items"][0]
        assert item["actor_nombre"] == "Nombre Completo"
        assert item["materia_nombre"] == "Resolución Nombres"
