"""TDD: Facturas API integration tests."""

import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.facturas import router as facturas_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.services.factura_service import FacturaService
from app.schemas.liquidacion import FacturaCreate


@pytest_asyncio.fixture
async def facturador_user(db_session, tenant):
    auth = AuthUser(
        id=uuid.uuid4(), email="fapi@test.com",
        password_hash="test_hash", tenant_id=tenant.id,
    )
    db_session.add(auth)
    await db_session.flush()
    user = Usuario(
        id=auth.id, tenant_id=tenant.id,
        nombre="Fact", apellidos="Api", legajo="FA001", facturador=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def no_facturador_user(db_session, tenant):
    auth = AuthUser(
        id=uuid.uuid4(), email="nfapi@test.com",
        password_hash="test_hash", tenant_id=tenant.id,
    )
    db_session.add(auth)
    await db_session.flush()
    user = Usuario(
        id=auth.id, tenant_id=tenant.id,
        nombre="No", apellidos="FactApi", legajo="NFA001", facturador=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


def _finanzas_session(tenant):
    return UserSession(user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["FINANZAS"])


async def _seed_perms(db_session, tenant):
    perm_codes = [
        "liquidaciones:ver", "liquidaciones:calcular",
        "liquidaciones:cerrar", "liquidaciones:exportar",
        "liquidaciones:configurar-salarios",
    ]
    for code in perm_codes:
        db_session.add(Permiso(codigo=code, descripcion=f"Test {code}"))
    rol = Rol(tenant_id=tenant.id, nombre="FINANZAS", descripcion="Financial role")
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    from sqlalchemy import select
    for code in perm_codes:
        result = await db_session.execute(select(Permiso).where(Permiso.codigo == code))
        p = result.scalar_one_or_none()
        if p:
            db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()


@pytest.mark.asyncio
class TestFacturasAPI:
    @pytest.fixture
    def f_app(self, db_session):
        app = FastAPI()
        app.include_router(facturas_router)

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override
        return app

    @pytest.fixture
    async def f_client(self, f_app):
        transport = ASGITransport(app=f_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_create_factura_success(self, f_client, f_app, db_session, tenant, facturador_user):
        await _seed_perms(db_session, tenant)
        f_app.dependency_overrides[get_current_user] = lambda: _finanzas_session(tenant)

        resp = await f_client.post("/api/facturas", json={
            "usuario_id": str(facturador_user.id),
            "periodo": "2025-06",
            "detalle": "Factura API test",
            "referencia_archivo": "facturas/test.pdf",
            "tamano_kb": 120.0,
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["estado"] == "Pendiente"
        assert data["detalle"] == "Factura API test"

    async def test_create_factura_no_facturador(self, f_client, f_app, db_session, tenant, no_facturador_user):
        await _seed_perms(db_session, tenant)
        f_app.dependency_overrides[get_current_user] = lambda: _finanzas_session(tenant)

        resp = await f_client.post("/api/facturas", json={
            "usuario_id": str(no_facturador_user.id),
            "periodo": "2025-06",
            "detalle": "No deberia crearse",
        })
        assert resp.status_code == 409, resp.text
        assert "facturador" in resp.text.lower()

    async def test_get_factura_by_id(self, f_client, f_app, db_session, tenant, facturador_user):
        await _seed_perms(db_session, tenant)
        f_app.dependency_overrides[get_current_user] = lambda: _finanzas_session(tenant)

        fact_svc = FacturaService(db_session, tenant.id)
        created = await fact_svc.create(FacturaCreate(
            usuario_id=facturador_user.id, periodo="2025-06", detalle="Get by id test",
        ))

        resp = await f_client.get(f"/api/facturas/{created.id}")
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == str(created.id)

    async def test_abonar_and_reabrir(self, f_client, f_app, db_session, tenant, facturador_user):
        await _seed_perms(db_session, tenant)
        f_app.dependency_overrides[get_current_user] = lambda: _finanzas_session(tenant)

        fact_svc = FacturaService(db_session, tenant.id)
        created = await fact_svc.create(FacturaCreate(
            usuario_id=facturador_user.id, periodo="2025-06", detalle="Abonar/reabrir test",
        ))

        resp = await f_client.put(f"/api/facturas/{created.id}/abonar")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["estado"] == "Abonada"
        assert data["abonada_at"] is not None

        resp = await f_client.put(f"/api/facturas/{created.id}/reabrir")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["estado"] == "Pendiente"
        assert data["abonada_at"] is None

    async def test_soft_delete_factura(self, f_client, f_app, db_session, tenant, facturador_user):
        await _seed_perms(db_session, tenant)
        f_app.dependency_overrides[get_current_user] = lambda: _finanzas_session(tenant)

        fact_svc = FacturaService(db_session, tenant.id)
        created = await fact_svc.create(FacturaCreate(
            usuario_id=facturador_user.id, periodo="2025-06", detalle="Delete test",
        ))

        resp = await f_client.delete(f"/api/facturas/{created.id}")
        assert resp.status_code == 200, resp.text

        resp = await f_client.get(f"/api/facturas/{created.id}")
        assert resp.status_code == 404, resp.text
