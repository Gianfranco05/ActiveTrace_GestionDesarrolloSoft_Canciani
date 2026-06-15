"""TDD: Comunicacion router integration tests."""

from datetime import date
import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserSession, get_current_user, get_db
from app.main import create_app
from app.models.auth_user import AuthUser
from app.models.padron import EntradaPadron, VersionPadron
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.models.asignacion import Asignacion
from app.models.materia import Materia
from app.models.tenant import Tenant


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


async def _seed_user(db_session, tenant, permisos_codigos):
    au = AuthUser(tenant_id=tenant.id, email="rtr@test.com", password_hash="x")
    db_session.add(au)
    await db_session.flush()
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Rtr", apellidos="T")
    db_session.add(u)
    await db_session.flush()
    rol = Rol(nombre="COM_ROLE", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.flush()

    for codigo in permisos_codigos:
        p = Permiso(codigo=codigo)
        db_session.add(p)
        await db_session.flush()
        db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))

    db_session.add(Asignacion(
        usuario_id=u.id, rol_id=rol.id,
        tenant_id=tenant.id, vig_desde=date.today(),
    ))
    await db_session.commit()
    return u


@pytest.fixture
async def seed_user_enviar(db_session, tenant):
    return await _seed_user(db_session, tenant, ["comunicacion:enviar", "comunicacion:ver"])


@pytest.fixture
async def seed_user_ver(db_session, tenant):
    return await _seed_user(db_session, tenant, ["comunicacion:ver"])


@pytest.fixture
async def seed_user_aprobar(db_session, tenant):
    return await _seed_user(db_session, tenant, [
        "comunicacion:enviar", "comunicacion:aprobar", "comunicacion:ver",
    ])


async def _setup_padron(db_session, tenant, count=3):
    vp = VersionPadron(tenant_id=tenant.id, activa=True)
    db_session.add(vp)
    await db_session.flush()
    for i in range(count):
        db_session.add(EntradaPadron(
            tenant_id=tenant.id, version_id=vp.id,
            nombre=f"N{i}", apellidos=f"A{i}", email=f"s{i}@t.com",
        ))
    await db_session.commit()


def _override_user(app, usuario, roles=None):
    app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=usuario.id,
        tenant_id=usuario.tenant_id,
        roles=roles or ["COM_ROLE"],
    )


@pytest.mark.asyncio
async def test_preview_endpoint_returns_200(
    client: AsyncClient, db_session: AsyncSession, tenant: Tenant,
    app: FastAPI, seed_user_enviar: Usuario,
):
    _override_user(app, seed_user_enviar)
    await _setup_padron(db_session, tenant)

    materia = Materia(codigo="T1", nombre="Test", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()

    resp = await client.post(
        "/api/comunicaciones/preview",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola {{nombre}}",
            "template_asunto": "Nota",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "preview_token" in data
    assert data["total_estimado"] == 3


@pytest.mark.asyncio
async def test_preview_without_permiso_returns_403(
    client: AsyncClient, db_session: AsyncSession, tenant: Tenant,
    app: FastAPI, seed_user_ver: Usuario,
):
    _override_user(app, seed_user_ver)

    resp = await client.post(
        "/api/comunicaciones/preview",
        json={
            "materia_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola",
            "template_asunto": "Nota",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_enqueue_endpoint_full_flow(
    client: AsyncClient, db_session: AsyncSession, tenant: Tenant,
    app: FastAPI, seed_user_enviar: Usuario,
):
    _override_user(app, seed_user_enviar)
    await _setup_padron(db_session, tenant, count=2)

    materia = Materia(codigo="T2", nombre="Test2", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()

    preview = await client.post(
        "/api/comunicaciones/preview",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola {{nombre}}",
            "template_asunto": "S",
        },
    )
    assert preview.status_code == 200
    pdata = preview.json()

    enq = await client.post(
        "/api/comunicaciones/enviar",
        json={
            "preview_token": pdata["preview_token"],
            "preview_token_timestamp": pdata["preview_token_timestamp"],
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola {{nombre}}",
            "template_asunto": "S",
        },
    )
    assert enq.status_code == 200
    edata = enq.json()
    assert edata["creados"] == 2
    assert len(edata["lote_id"]) > 0


@pytest.mark.asyncio
async def test_list_endpoint_returns_comunicaciones(
    client: AsyncClient, db_session: AsyncSession, tenant: Tenant,
    app: FastAPI, seed_user_enviar: Usuario,
):
    _override_user(app, seed_user_enviar)
    await _setup_padron(db_session, tenant, count=1)

    materia = Materia(codigo="T3", nombre="Test3", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()

    preview = await client.post(
        "/api/comunicaciones/preview",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola",
            "template_asunto": "S",
        },
    )
    pdata = preview.json()
    await client.post(
        "/api/comunicaciones/enviar",
        json={
            "preview_token": pdata["preview_token"],
            "preview_token_timestamp": pdata["preview_token_timestamp"],
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola",
            "template_asunto": "S",
        },
    )

    resp = await client.get(
        "/api/comunicaciones?estado=Pendiente",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_approve_and_cancel_lote_flow(
    client: AsyncClient, db_session: AsyncSession, tenant: Tenant,
    app: FastAPI, seed_user_aprobar: Usuario,
):
    _override_user(app, seed_user_aprobar)
    await _setup_padron(db_session, tenant, count=2)

    materia = Materia(codigo="T4", nombre="Test4", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()

    preview = await client.post(
        "/api/comunicaciones/preview",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola",
            "template_asunto": "S",
        },
    )
    pdata = preview.json()
    enq = await client.post(
        "/api/comunicaciones/enviar",
        json={
            "preview_token": pdata["preview_token"],
            "preview_token_timestamp": pdata["preview_token_timestamp"],
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola",
            "template_asunto": "S",
        },
    )
    lote_id = enq.json()["lote_id"]

    apr = await client.post(f"/api/comunicaciones/lote/{lote_id}/aprobar")
    assert apr.status_code == 200
    assert apr.json()["aprobados"] == 2

    can = await client.post(f"/api/comunicaciones/lote/{lote_id}/cancelar")
    assert can.status_code == 200
    assert can.json()["cancelados"] == 2


@pytest.mark.asyncio
async def test_get_detail_endpoint(
    client: AsyncClient, db_session: AsyncSession, tenant: Tenant,
    app: FastAPI, seed_user_enviar: Usuario,
):
    _override_user(app, seed_user_enviar)
    await _setup_padron(db_session, tenant, count=1)

    materia = Materia(codigo="T5", nombre="Test5", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()

    preview = await client.post(
        "/api/comunicaciones/preview",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola",
            "template_asunto": "S",
        },
    )
    pdata = preview.json()
    await client.post(
        "/api/comunicaciones/enviar",
        json={
            "preview_token": pdata["preview_token"],
            "preview_token_timestamp": pdata["preview_token_timestamp"],
            "materia_id": str(materia.id),
            "cohorte_id": str(uuid.uuid4()),
            "template_body": "Hola",
            "template_asunto": "S",
        },
    )

    list_resp = await client.get("/api/comunicaciones")
    assert list_resp.status_code == 200
    com_id = list_resp.json()["items"][0]["id"]

    detail = await client.get(f"/api/comunicaciones/{com_id}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["id"] == com_id
    assert data["estado"] == "Pendiente"
