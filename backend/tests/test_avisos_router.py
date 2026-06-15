import uuid
from datetime import date, datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.avisos import router as avisos_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.asignacion import Asignacion
from app.models.auth_user import AuthUser
from app.models.aviso import Aviso
from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.usuario import Usuario


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(avisos_router)

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


async def _setup_coordinator(db_session, tenant):
    """Create a coordinator user with avisos:publicar and aviso:confirmar permissions."""
    auth = AuthUser(
        tenant_id=tenant.id,
        email=f"coord_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="pw",
    )
    db_session.add(auth)
    await db_session.flush()

    usuario = Usuario(
        id=auth.id, tenant_id=tenant.id, nombre="Coord", apellidos="Test",
    )
    db_session.add(usuario)
    await db_session.flush()

    rol = Rol(nombre=f"COORDINADOR_{uuid.uuid4().hex[:4]}", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.flush()

    p_publicar = Permiso(codigo="avisos:publicar")
    db_session.add(p_publicar)
    p_confirmar = Permiso(codigo="aviso:confirmar")
    db_session.add(p_confirmar)
    await db_session.flush()

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p_publicar.id))
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p_confirmar.id))
    await db_session.commit()

    return auth, usuario, rol


async def _setup_profesor(db_session, tenant, materia, cohorte):
    """Create a profesor with aviso:confirmar and assignments."""
    auth = AuthUser(
        tenant_id=tenant.id,
        email=f"prof_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="pw",
    )
    db_session.add(auth)
    await db_session.flush()

    usuario = Usuario(
        id=auth.id, tenant_id=tenant.id, nombre="Prof", apellidos="Test",
    )
    db_session.add(usuario)
    await db_session.flush()

    rol = Rol(nombre=f"PROFESOR_{uuid.uuid4().hex[:4]}", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.flush()

    p_confirmar = Permiso(codigo="aviso:confirmar")
    db_session.add(p_confirmar)
    await db_session.flush()

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p_confirmar.id))
    await db_session.flush()

    asign = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(asign)
    await db_session.commit()

    return auth, usuario, rol


async def _setup_alumno(db_session, tenant, cohorte):
    """Create an alumno with aviso:confirmar and cohort assignment."""
    auth = AuthUser(
        tenant_id=tenant.id,
        email=f"alum_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="pw",
    )
    db_session.add(auth)
    await db_session.flush()

    usuario = Usuario(
        id=auth.id, tenant_id=tenant.id, nombre="Alum", apellidos="Test",
    )
    db_session.add(usuario)
    await db_session.flush()

    rol = Rol(nombre=f"ALUMNO_{uuid.uuid4().hex[:4]}", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.flush()

    p_confirmar = Permiso(codigo="aviso:confirmar")
    db_session.add(p_confirmar)
    await db_session.flush()

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p_confirmar.id))
    await db_session.flush()

    asign = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        cohorte_id=cohorte.id,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(asign)
    await db_session.commit()

    return auth, usuario, rol


# 7.1
@pytest.mark.asyncio
async def test_post_aviso_coordinador_201(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    payload = {
        "alcance": "Global",
        "severidad": "Info",
        "titulo": "Bienvenida",
        "cuerpo": "Bienvenidos al cuatrimestre",
        "inicio_en": "2026-06-01T00:00:00Z",
        "fin_en": "2026-12-31T23:59:59Z",
    }
    response = await http_client.post("/api/avisos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Bienvenida"
    assert data["alcance"] == "Global"
    assert data["activo"] is True
    assert "id" in data


# 7.2
@pytest.mark.asyncio
async def test_post_aviso_sin_permisos_403(db_session, tenant, http_client, test_app):
    auth = AuthUser(
        tenant_id=tenant.id,
        email=f"noperm_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="pw",
    )
    db_session.add(auth)
    await db_session.commit()

    _mock_user(auth, tenant, ["SIN_PERMISO"], test_app)

    payload = {
        "alcance": "Global",
        "severidad": "Info",
        "titulo": "Test",
        "cuerpo": "Body",
        "inicio_en": "2026-06-01T00:00:00Z",
        "fin_en": "2026-12-31T23:59:59Z",
    }
    response = await http_client.post("/api/avisos", json=payload)
    assert response.status_code == 403


# 7.3
@pytest.mark.asyncio
async def test_put_aviso_update_200(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Original",
        cuerpo="Cuerpo original",
        inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    payload = {"titulo": "Actualizado", "activo": False}
    response = await http_client.put(f"/api/avisos/{aviso.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["titulo"] == "Actualizado"
    assert data["activo"] is False


# 7.4
@pytest.mark.asyncio
async def test_delete_aviso_204_and_then_404(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Para borrar",
        cuerpo="Cuerpo",
        inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    response = await http_client.delete(f"/api/avisos/{aviso.id}")
    assert response.status_code == 204

    response = await http_client.get(f"/api/avisos/{aviso.id}")
    assert response.status_code == 404


# 7.5
@pytest.mark.asyncio
async def test_get_avisos_profesor_ve_solo_suyos(db_session, tenant, http_client, test_app):
    carrera = Carrera(tenant_id=tenant.id, codigo="CARR-PROF", nombre="Carrera Prof")
    db_session.add(carrera)
    await db_session.flush()

    cohorte_own = Cohorte(
        tenant_id=tenant.id, carrera_id=carrera.id, nombre="COH-OWN",
        anio=2026, vig_desde=date(2026, 1, 1),
    )
    db_session.add(cohorte_own)
    await db_session.flush()

    materia_own = Materia(tenant_id=tenant.id, codigo="MAT-OWN", nombre="Materia Own")
    db_session.add(materia_own)
    await db_session.flush()

    cohorte_other = Cohorte(
        tenant_id=tenant.id, carrera_id=carrera.id, nombre="COH-OTHER",
        anio=2026, vig_desde=date(2026, 1, 1),
    )
    db_session.add(cohorte_other)
    await db_session.flush()

    materia_other = Materia(tenant_id=tenant.id, codigo="MAT-OTHER", nombre="Materia Other")
    db_session.add(materia_other)
    await db_session.flush()

    auth, usuario, rol = await _setup_profesor(db_session, tenant, materia_own, cohorte_own)

    # Global (visible to all)
    aviso_global = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Global", cuerpo="Global",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_global)

    # PorMateria own (visible)
    aviso_materia_own = Aviso(
        tenant_id=tenant.id, alcance="PorMateria", materia_id=materia_own.id,
        severidad="Info", titulo="Materia Own", cuerpo="Own",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_materia_own)

    # PorMateria other (NOT visible)
    aviso_materia_other = Aviso(
        tenant_id=tenant.id, alcance="PorMateria", materia_id=materia_other.id,
        severidad="Info", titulo="Materia Other", cuerpo="Other",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_materia_other)

    # PorCohorte own (visible)
    aviso_cohorte_own = Aviso(
        tenant_id=tenant.id, alcance="PorCohorte", cohorte_id=cohorte_own.id,
        severidad="Info", titulo="Cohorte Own", cuerpo="Own",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_cohorte_own)

    # PorRol PROFESOR (visible)
    aviso_rol = Aviso(
        tenant_id=tenant.id, alcance="PorRol", rol_destino=rol.nombre,
        severidad="Info", titulo="Rol Prof", cuerpo="Prof",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_rol)
    await db_session.commit()

    _mock_user(auth, tenant, [rol.nombre], test_app)

    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    titulos = [item["titulo"] for item in data["items"]]
    assert "Global" in titulos
    assert "Materia Own" in titulos
    assert "Cohorte Own" in titulos
    assert "Rol Prof" in titulos
    assert "Materia Other" not in titulos


# 7.6
@pytest.mark.asyncio
async def test_get_avisos_alumno_ve_solo_suyos(db_session, tenant, http_client, test_app):
    carrera = Carrera(tenant_id=tenant.id, codigo="CARR-ALU", nombre="Carrera Alu")
    db_session.add(carrera)
    await db_session.flush()

    cohorte_own = Cohorte(
        tenant_id=tenant.id, carrera_id=carrera.id, nombre="COH-ALU",
        anio=2026, vig_desde=date(2026, 1, 1),
    )
    db_session.add(cohorte_own)
    await db_session.flush()

    materia = Materia(tenant_id=tenant.id, codigo="MAT-ALU", nombre="Materia Alu")
    db_session.add(materia)
    await db_session.flush()

    auth, usuario, rol = await _setup_alumno(db_session, tenant, cohorte_own)

    aviso_global = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Global", cuerpo="Global",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_global)

    aviso_cohorte = Aviso(
        tenant_id=tenant.id, alcance="PorCohorte", cohorte_id=cohorte_own.id,
        severidad="Info", titulo="Cohorte Alu", cuerpo="Alu",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_cohorte)

    aviso_rol = Aviso(
        tenant_id=tenant.id, alcance="PorRol", rol_destino=rol.nombre,
        severidad="Info", titulo="Rol Alu", cuerpo="Alu",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_rol)

    aviso_materia = Aviso(
        tenant_id=tenant.id, alcance="PorMateria", materia_id=materia.id,
        severidad="Info", titulo="Materia Alu", cuerpo="Alu",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_materia)
    await db_session.commit()

    _mock_user(auth, tenant, [rol.nombre], test_app)

    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    titulos = [item["titulo"] for item in data["items"]]
    assert "Global" in titulos
    assert "Cohorte Alu" in titulos
    assert "Rol Alu" in titulos
    assert "Materia Alu" not in titulos


# 7.7
@pytest.mark.asyncio
async def test_get_avisos_no_muestra_fuera_vigencia(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso_futuro = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Futuro", cuerpo="Futuro",
        inicio_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2031, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_futuro)

    aviso_pasado = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Pasado", cuerpo="Pasado",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2020, 6, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_pasado)
    await db_session.commit()

    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    titulos = [item["titulo"] for item in data["items"]]
    assert "Futuro" not in titulos
    assert "Pasado" not in titulos


# 7.8
@pytest.mark.asyncio
async def test_get_avisos_no_muestra_ack_confirmados(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Con Ack", cuerpo="Ack",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    # Before ack, visible
    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    ack = AcknowledgmentAviso(aviso_id=aviso.id, usuario_id=usuario.id)
    db_session.add(ack)
    await db_session.commit()

    # After ack, excluded
    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0


# 7.9
@pytest.mark.asyncio
async def test_post_ack_confirma_201_then_200(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Con Ack", cuerpo="Ack",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    response = await http_client.post(f"/api/avisos/{aviso.id}/ack")
    assert response.status_code == 201
    data = response.json()
    assert data["aviso_id"] == str(aviso.id)

    response2 = await http_client.post(f"/api/avisos/{aviso.id}/ack")
    assert response2.status_code == 200


# 7.10
@pytest.mark.asyncio
async def test_post_ack_sin_requiere_ack_422(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Sin Ack", cuerpo="Sin Ack",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=False,
    )
    db_session.add(aviso)
    await db_session.commit()

    response = await http_client.post(f"/api/avisos/{aviso.id}/ack")
    assert response.status_code == 422


# 7.11
@pytest.mark.asyncio
async def test_post_ack_fuera_vigencia_404(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Futuro", cuerpo="Futuro",
        inicio_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2031, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    response = await http_client.post(f"/api/avisos/{aviso.id}/ack")
    assert response.status_code == 404


# 7.12
@pytest.mark.asyncio
async def test_post_ack_no_visible_por_scope_404(db_session, tenant, http_client, test_app):
    carrera = Carrera(tenant_id=tenant.id, codigo="CARR-SCP", nombre="Carrera Scp")
    db_session.add(carrera)
    await db_session.flush()

    cohorte_other = Cohorte(
        tenant_id=tenant.id, carrera_id=carrera.id, nombre="COH-SCP",
        anio=2026, vig_desde=date(2026, 1, 1),
    )
    db_session.add(cohorte_other)
    await db_session.flush()

    # Coordinator with no asignation to that cohort
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="PorCohorte", cohorte_id=cohorte_other.id,
        severidad="Info", titulo="Otra Cohorte", cuerpo="Otra",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    response = await http_client.post(f"/api/avisos/{aviso.id}/ack")
    assert response.status_code == 404


# 7.13
@pytest.mark.asyncio
async def test_get_aviso_stats_200(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Stats", cuerpo="Stats",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    ack = AcknowledgmentAviso(aviso_id=aviso.id, usuario_id=usuario.id)
    db_session.add(ack)
    await db_session.commit()

    response = await http_client.get(f"/api/avisos/{aviso.id}/ack/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["aviso_id"] == str(aviso.id)
    assert data["total_views"] == 1
    assert data["total_acks"] == 1
    assert data["pendientes_ack"] == 0


# 7.14
@pytest.mark.asyncio
async def test_get_aviso_stats_sin_permisos_403(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Stats", cuerpo="Stats",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    _mock_user(auth, tenant, ["SIN_PERMISO"], test_app)

    response = await http_client.get(f"/api/avisos/{aviso.id}/ack/stats")
    assert response.status_code == 403


# 7.15
@pytest.mark.asyncio
async def test_get_avisos_admin_ve_fuera_vigencia(db_session, tenant, http_client, test_app):
    """Admin param should show avisos outside vigencia (future/past/inactive)."""
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso_futuro = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Futuro Admin", cuerpo="Futuro",
        inicio_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2031, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso_futuro)

    aviso_inactivo = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Inactivo Admin", cuerpo="Inactivo",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        activo=False,
    )
    db_session.add(aviso_inactivo)
    await db_session.commit()

    # Without admin, not visible
    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    titulos = [item["titulo"] for item in data["items"]]
    assert "Futuro Admin" not in titulos
    assert "Inactivo Admin" not in titulos

    # With admin=true, visible
    response = await http_client.get("/api/avisos?admin=true")
    assert response.status_code == 200
    data = response.json()
    titulos = [item["titulo"] for item in data["items"]]
    assert "Futuro Admin" in titulos
    assert "Inactivo Admin" in titulos


# 7.16
@pytest.mark.asyncio
async def test_get_avisos_admin_ve_ack_confirmados(db_session, tenant, http_client, test_app):
    """Admin param should show avisos even if acknowledged."""
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="Con Ack Admin", cuerpo="Ack",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    ack = AcknowledgmentAviso(aviso_id=aviso.id, usuario_id=usuario.id)
    db_session.add(ack)
    await db_session.commit()

    # Without admin, excluded
    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0

    # With admin, visible
    response = await http_client.get("/api/avisos?admin=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["titulo"] == "Con Ack Admin"


# 7.17
@pytest.mark.asyncio
async def test_avisos_ordenados_por_prioridad(db_session, tenant, http_client, test_app):
    auth, usuario, rol = await _setup_coordinator(db_session, tenant)
    _mock_user(auth, tenant, [rol.nombre], test_app)

    aviso_a = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="A", cuerpo="A",
        inicio_en=datetime(2026, 6, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        orden=10,
    )
    aviso_b = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="B", cuerpo="B",
        inicio_en=datetime(2026, 6, 3, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        orden=5,
    )
    aviso_c = Aviso(
        tenant_id=tenant.id, alcance="Global", severidad="Info",
        titulo="C", cuerpo="C",
        inicio_en=datetime(2026, 5, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        orden=10,
    )
    db_session.add_all([aviso_a, aviso_b, aviso_c])
    await db_session.commit()

    response = await http_client.get("/api/avisos")
    assert response.status_code == 200
    data = response.json()
    titulos = [item["titulo"] for item in data["items"]]
    assert titulos == ["A", "C", "B"]
