"""TDD: Guardias router integration tests."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.guardias import router as guardias_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.auth_user import AuthUser
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.permiso import Permiso
from tests.helpers_encuentros import create_asignacion_chain


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(guardias_router)

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
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    from app.models.asignacion import Asignacion
    a_obj = await db_session.get(Asignacion, a.id)
    au = await db_session.get(AuthUser, a_obj.usuario_id)

    suid = uuid.uuid4().hex[:4]
    rol = Rol(nombre=f"GRT-{suid}", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo=permiso_codigo)
    db_session.add(p)
    await db_session.flush()
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()
    return au, rol, a, m, c, coh


@pytest.mark.asyncio
async def test_registrar_guardia_201(db_session, tenant, http_client, test_app):
    au, rol, a, m, c, coh = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    payload = {
        "asignacion_id": str(a.id), "materia_id": str(m.id),
        "carrera_id": str(c.id), "cohorte_id": str(coh.id),
        "dia": "Lunes", "horario": "14:00–14:45",
        "comentarios": "Test",
    }
    response = await http_client.post("/api/guardias", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "Pendiente"


@pytest.mark.asyncio
async def test_registrar_guardia_403_sin_permiso(db_session, tenant, http_client, test_app):
    au, rol, a, m, c, coh = await _setup_user_with_permiso(db_session, tenant, permiso_codigo="estructura:gestionar")
    _mock_user(au, tenant, [rol.nombre], test_app)

    payload = {
        "asignacion_id": str(a.id), "materia_id": str(m.id),
        "carrera_id": str(c.id), "cohorte_id": str(coh.id),
        "dia": "Lunes", "horario": "14:00–14:45",
    }
    response = await http_client.post("/api/guardias", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_registrar_guardia_422_faltan_campos(db_session, tenant, http_client, test_app):
    au, rol, a, m, c, coh = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    response = await http_client.post("/api/guardias", json={"dia": "Lunes"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_listar_guardias_200(db_session, tenant, http_client, test_app):
    au, rol, a, m, c, coh = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    response = await http_client.get("/api/guardias")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_editar_guardia_200(db_session, tenant, http_client, test_app):
    au, rol, a, m, c, coh = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    from app.models.guardia import Guardia
    g = Guardia(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id, dia="Lunes", horario="14:00–14:45",
    )
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    payload = {"estado": "Realizada"}
    response = await http_client.patch(f"/api/guardias/{g.id}", json=payload)
    assert response.status_code == 200
    assert response.json()["estado"] == "Realizada"


@pytest.mark.asyncio
async def test_export_guardias_csv(db_session, tenant, http_client, test_app):
    au, rol, a, m, c, coh = await _setup_user_with_permiso(db_session, tenant)
    _mock_user(au, tenant, [rol.nombre], test_app)

    from app.models.guardia import Guardia
    g = Guardia(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id, dia="Lunes", horario="14:00–14:45",
    )
    db_session.add(g)
    await db_session.commit()

    response = await http_client.get("/api/guardias/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
