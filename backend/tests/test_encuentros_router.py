"""TDD: Encuentros router integration tests."""

import uuid
from datetime import date, time

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.encuentros import router as encuentros_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.permiso import Permiso
from tests.helpers_encuentros import create_asignacion_chain


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(encuentros_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


def _mock_user(auth_user, tenant, roles, test_app):
    user = UserSession(user_id=auth_user.id, tenant_id=tenant.id, roles=roles)
    async def _override():
        return user
    test_app.dependency_overrides[get_current_user] = _override
    return user


async def _setup_user_with_permiso(db_session, tenant, permiso_codigo="encuentros:gestionar"):
    """Creates asignacion chain + gives permiso to the chain's auth_user."""
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    from app.models.asignacion import Asignacion
    a_obj = await db_session.get(Asignacion, a.id)
    au = await db_session.get(AuthUser, a_obj.usuario_id)

    suid = uuid.uuid4().hex[:4]
    rol = Rol(nombre=f"RT-{suid}", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo=permiso_codigo)
    db_session.add(p)
    await db_session.flush()
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()
    return au, rol, a, m, c, coh


@pytest.mark.asyncio
async def test_crear_slot_recurrente_201(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    payload = {
        "materia_id": str(m.id),
        "asignacion_id": str(a.id),
        "titulo": "Clase Router",
        "hora": "14:00:00",
        "dia_semana": "Lunes",
        "fecha_inicio": "2026-06-08",
        "cant_semanas": 2,
    }
    response = await http_client.post("/api/encuentros/slots", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Clase Router"
    assert len(data["instancias"]) == 2


@pytest.mark.asyncio
async def test_crear_slot_recurrente_403_sin_permiso(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant, permiso_codigo="estructura:gestionar")
    _mock_user(au, tenant, [rol.nombre], test_app)

    payload = {
        "materia_id": str(m.id), "asignacion_id": str(a.id), "titulo": "Test",
        "hora": "14:00:00", "dia_semana": "Lunes", "fecha_inicio": "2026-06-08",
        "cant_semanas": 1,
    }
    response = await http_client.post("/api/encuentros/slots", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_crear_encuentro_unico_201(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    payload = {
        "materia_id": str(m.id), "asignacion_id": str(a.id),
        "titulo": "Unico", "fecha": "2026-07-01", "hora": "15:00:00",
    }
    response = await http_client.post("/api/encuentros/instancias", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["slot_id"] is None


@pytest.mark.asyncio
async def test_listar_slots_200(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    response = await http_client.get(f"/api/encuentros/slots?materia_id={m.id}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_listar_instancias_filtro_estado(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    response = await http_client.get(f"/api/encuentros/instancias?materia_id={m.id}&estado=Programado")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_editar_instancia_200(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    from app.models.instancia_encuentro import InstanciaEncuentro
    inst = InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        fecha=date(2026, 6, 8), hora=time(14, 0), titulo="Editar",
    )
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    payload = {"estado": "Realizado"}
    response = await http_client.patch(
        f"/api/encuentros/instancias/{inst.id}", json=payload,
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "Realizado"


@pytest.mark.asyncio
async def test_editar_instancia_404(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    payload = {"estado": "Realizado"}
    response = await http_client.patch(
        f"/api/encuentros/instancias/{uuid.uuid4()}", json=payload,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generar_html_200(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    from app.models.slot_encuentro import SlotEncuentro
    from app.models.instancia_encuentro import InstanciaEncuentro
    slot = SlotEncuentro(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        titulo="HTML", hora=time(14, 0),
    )
    db_session.add(slot)
    await db_session.flush()
    db_session.add(InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        slot_id=slot.id, fecha=date(2026, 6, 8), hora=time(14, 0),
        titulo="C0",
    ))
    await db_session.commit()

    response = await http_client.get(f"/api/encuentros/slots/{slot.id}/html")
    assert response.status_code == 200
    assert "html" in response.json()


@pytest.mark.asyncio
async def test_generar_html_404(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    response = await http_client.get(f"/api/encuentros/slots/{uuid.uuid4()}/html")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_slot_204(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    from app.models.slot_encuentro import SlotEncuentro
    slot = SlotEncuentro(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        titulo="Borrar", hora=time(14, 0),
    )
    db_session.add(slot)
    await db_session.commit()
    await db_session.refresh(slot)

    response = await http_client.delete(f"/api/encuentros/slots/{slot.id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_slot_404(db_session, tenant, http_client, test_app):
    au, rol, a, m, _, _ = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    response = await http_client.delete(f"/api/encuentros/slots/{uuid.uuid4()}")
    assert response.status_code == 404
