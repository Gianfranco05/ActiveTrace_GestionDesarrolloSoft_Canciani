import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.inbox import router as inbox_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.core.security import hash_password
from app.models.auth_user import AuthUser
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.usuario import Usuario


@pytest.fixture
def i_app(db_session):
    app = FastAPI()
    app.include_router(inbox_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def i_client(i_app):
    transport = ASGITransport(app=i_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_mensajeria_permiso(db_session, tenant):
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="mensajeria:usar")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)
    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    return rol


async def _create_usuario(db_session, tenant, email, nombre):
    auth = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password("Test1234!"),
    )
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos="Test")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return auth, u


def _session(user_id, tenant):
    return UserSession(user_id=user_id, tenant_id=tenant.id, roles=["PROFESOR"])


@pytest.mark.asyncio
async def test_post_inbox_201(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    sender_auth, sender = await _create_usuario(db_session, tenant, "sender@test.com", "Sender")
    recip_auth, recip = await _create_usuario(db_session, tenant, "recip@test.com", "Recipient")

    i_app.dependency_overrides[get_current_user] = lambda: _session(sender_auth.id, tenant)
    resp = await i_client.post("/api/inbox", json={
        "recipient_id": str(recip.id),
        "asunto": "Test mensaje",
        "cuerpo": "Cuerpo del mensaje",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["asunto"] == "Test mensaje"
    assert data["cuerpo"] == "Cuerpo del mensaje"
    assert data["sender_id"] == str(sender.id)
    assert data["parent_id"] is None
    assert data["leido"] is False


@pytest.mark.asyncio
async def test_get_inbox_lista_hilos(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    sender_auth, sender = await _create_usuario(db_session, tenant, "inbox_sender@test.com", "Sender")
    recip_auth, recip = await _create_usuario(db_session, tenant, "inbox_recip@test.com", "Recipient")

    i_app.dependency_overrides[get_current_user] = lambda: _session(sender_auth.id, tenant)
    await i_client.post("/api/inbox", json={
        "recipient_id": str(recip.id),
        "asunto": "Hilo 1",
        "cuerpo": "Cuerpo 1",
    })

    await i_client.post("/api/inbox", json={
        "recipient_id": str(recip.id),
        "asunto": "Hilo 2",
        "cuerpo": "Cuerpo 2",
    })

    i_app.dependency_overrides[get_current_user] = lambda: _session(recip_auth.id, tenant)
    resp = await i_client.get("/api/inbox")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_inbox_sin_auth_401(i_client, i_app, db_session, tenant):
    resp = await i_client.get("/api/inbox")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_inbox_vacio(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    recip_auth, recip = await _create_usuario(db_session, tenant, "empty_inbox@test.com", "Empty")

    i_app.dependency_overrides[get_current_user] = lambda: _session(recip_auth.id, tenant)
    resp = await i_client.get("/api/inbox")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_thread_detail(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    sender_auth, sender = await _create_usuario(db_session, tenant, "td_sender@test.com", "S")
    recip_auth, recip = await _create_usuario(db_session, tenant, "td_recip@test.com", "R")

    i_app.dependency_overrides[get_current_user] = lambda: _session(sender_auth.id, tenant)
    post_resp = await i_client.post("/api/inbox", json={
        "recipient_id": str(recip.id),
        "asunto": "Thread detail",
        "cuerpo": "Root message",
    })
    thread_id = post_resp.json()["id"]

    i_app.dependency_overrides[get_current_user] = lambda: _session(recip_auth.id, tenant)
    resp = await i_client.get(f"/api/inbox/{thread_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["thread"]["id"] == thread_id
    assert data["thread"]["asunto"] == "Thread detail"


@pytest.mark.asyncio
async def test_get_thread_detail_ajeno_404(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    sender_auth, sender = await _create_usuario(db_session, tenant, "aj_sender@test.com", "S")
    recip_auth, recip = await _create_usuario(db_session, tenant, "aj_recip@test.com", "R")
    stranger_auth, stranger = await _create_usuario(db_session, tenant, "aj_stranger@test.com", "X")

    i_app.dependency_overrides[get_current_user] = lambda: _session(sender_auth.id, tenant)
    post_resp = await i_client.post("/api/inbox", json={
        "recipient_id": str(recip.id),
        "asunto": "Ajeno",
        "cuerpo": "Body",
    })
    thread_id = post_resp.json()["id"]

    i_app.dependency_overrides[get_current_user] = lambda: _session(stranger_auth.id, tenant)
    resp = await i_client.get(f"/api/inbox/{thread_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_post_reply(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    sender_auth, sender = await _create_usuario(db_session, tenant, "rp_sender@test.com", "S")
    recip_auth, recip = await _create_usuario(db_session, tenant, "rp_recip@test.com", "R")

    i_app.dependency_overrides[get_current_user] = lambda: _session(sender_auth.id, tenant)
    post_resp = await i_client.post("/api/inbox", json={
        "recipient_id": str(recip.id),
        "asunto": "Reply test",
        "cuerpo": "Root",
    })
    thread_id = post_resp.json()["id"]

    i_app.dependency_overrides[get_current_user] = lambda: _session(recip_auth.id, tenant)
    resp = await i_client.post(f"/api/inbox/{thread_id}/reply", json={"cuerpo": "Mi respuesta"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["parent_id"] == thread_id
    assert data["cuerpo"] == "Mi respuesta"
    assert data["sender_id"] == str(recip.id)
    assert data["recipient_id"] == str(sender.id)


@pytest.mark.asyncio
async def test_post_reply_hilo_inexistente(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    auth, u = await _create_usuario(db_session, tenant, "reply_nonexist@test.com", "U")

    i_app.dependency_overrides[get_current_user] = lambda: _session(auth.id, tenant)
    resp = await i_client.post(f"/api/inbox/{uuid.uuid4()}/reply", json={"cuerpo": "Reply"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_inbox_tenant_isolation(i_client, i_app, db_session, tenant):
    await _seed_mensajeria_permiso(db_session, tenant)
    sender_auth, sender = await _create_usuario(db_session, tenant, "iso_s@test.com", "S")
    recip_auth, recip = await _create_usuario(db_session, tenant, "iso_r@test.com", "R")

    i_app.dependency_overrides[get_current_user] = lambda: _session(sender_auth.id, tenant)
    post_resp = await i_client.post("/api/inbox", json={
        "recipient_id": str(recip.id),
        "asunto": "Iso test",
        "cuerpo": "Body",
    })
    thread_id = post_resp.json()["id"]

    other_tenant = uuid.uuid4()
    i_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=recip_auth.id, tenant_id=other_tenant, roles=["PROFESOR"],
    )
    resp = await i_client.get(f"/api/inbox/{thread_id}")
    assert resp.status_code == 404
