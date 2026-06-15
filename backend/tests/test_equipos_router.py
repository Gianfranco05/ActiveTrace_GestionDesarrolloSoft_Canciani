"""TDD: Equipos router integration tests — RED → GREEN → TRIANGULATE."""

import uuid
from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.equipos import router as equipos_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.asignacion import Asignacion
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.core.security import hash_password


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(equipos_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_rol_con_permiso(db_session, tenant, rol_nombre, permiso_codigo) -> Rol:
    rol = Rol(nombre=rol_nombre, tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo=permiso_codigo)
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)
    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    return rol


async def _create_usuario(db_session, tenant, nombre="Test", apellidos="User", legajo=None):
    au = AuthUser(
        tenant_id=tenant.id,
        email=f"{nombre.lower()}.{apellidos.lower()}.{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Secure123"),
    )
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    u = Usuario(
        id=au.id, tenant_id=tenant.id,
        nombre=nombre, apellidos=apellidos, legajo=legajo,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _create_rol(db_session, tenant, nombre="PROFESOR"):
    r = Rol(tenant_id=tenant.id, nombre=nombre)
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    return r


async def _create_materia(db_session, tenant, cod="MAT-RTR"):
    m = Materia(codigo=cod, nombre="Test Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _create_carrera(db_session, tenant, cod="CAR-RTR"):
    c = Carrera(codigo=cod, nombre="Test Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


async def _create_cohorte(db_session, tenant, carrera, nombre="COH-RTR"):
    c = Cohorte(carrera_id=carrera.id, nombre=nombre, anio=2026, vig_desde=date.today(), tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


def _coord_session(tenant, user_id=None, roles=None) -> UserSession:
    return UserSession(
        user_id=user_id or uuid.uuid4(),
        tenant_id=tenant.id,
        roles=roles or ["COORDINADOR"],
    )


def _prof_session(tenant, user_id=None) -> UserSession:
    return UserSession(
        user_id=user_id or uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["PROFESOR"],
    )


# ===== 4. Mis Equipos =====

@pytest.mark.asyncio
async def test_mis_equipos_returns_own_assignments(http_client, test_app, db_session, tenant):
    """RED 4.1: GET /api/equipos/mis-equipos returns user's Asignaciones."""
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-ME1")
    u = await _create_usuario(db_session, tenant)

    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, vig_desde=date.today() - timedelta(days=10))
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.get("/api/equipos/mis-equipos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["usuario_id"] == str(u.id)


@pytest.mark.asyncio
async def test_mis_equipos_returns_empty_for_no_assignments(http_client, test_app, db_session, tenant):
    """TRIANGULATE 4.4: empty for user with no assignments."""
    u = await _create_usuario(db_session, tenant, nombre="Empty")
    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get("/api/equipos/mis-equipos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_mis_equipos_401_without_auth(http_client, test_app, db_session, tenant):
    """TRIANGULATE 4.4: 401 without auth."""
    resp = await http_client.get("/api/equipos/mis-equipos")
    assert resp.status_code == 401


# ===== 5. List & Detail =====

@pytest.mark.asyncio
async def test_list_equipos_returns_grouped(http_client, test_app, db_session, tenant):
    """RED 5.1: GET /api/equipos returns grouped EquipoResponse."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-LIST", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordList")
    u = await _create_usuario(db_session, tenant, nombre="ProfList")
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-LIST")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-LIST"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    for _ in range(2):
        a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today())
        db_session.add(a)
    await db_session.commit()

    resp = await http_client.get("/api/equipos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    eq = next((e for e in data["items"] if e["materia_id"] == str(mat.id)), None)
    assert eq is not None
    assert eq["total_asignaciones"] == 2


@pytest.mark.asyncio
async def test_list_equipos_403_without_permission(http_client, test_app, db_session, tenant):
    """TRIANGULATE 5.4: 403 without equipos:asignar."""
    u = await _create_usuario(db_session, tenant)
    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get("/api/equipos")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_equipo_detail_returns_asignaciones(http_client, test_app, db_session, tenant):
    """TRIANGULATE 5.4: GET /api/equipos/detail returns asignaciones."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-DET", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordDet")
    u = await _create_usuario(db_session, tenant, nombre="ProfDet")
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-DET")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-DET"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today())
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.get(f"/api/equipos/detail?materia_id={mat.id}&carrera_id={car.id}&cohorte_id={coh.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["asignaciones"]) == 1
    assert data["materia_id"] == str(mat.id)


@pytest.mark.asyncio
async def test_get_equipo_detail_404_not_found(http_client, test_app, db_session, tenant):
    """TRIANGULATE 5.4: 404 when equipo not found."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-DNF", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordDNF")
    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-DNF"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get(f"/api/equipos/detail?materia_id={uuid.uuid4()}&carrera_id={uuid.uuid4()}&cohorte_id={uuid.uuid4()}")
    assert resp.status_code == 404


# ===== 6. Asignación Masiva =====

@pytest.mark.asyncio
async def test_asignacion_masiva_201(http_client, test_app, db_session, tenant):
    """RED 6.1: POST /api/equipos/masiva creates N asignaciones."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-MAS", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordMas")
    users = [await _create_usuario(db_session, tenant, nombre=f"Masiva{n}") for n in range(2)]
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-MAS")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-MAS"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.post(
        "/api/equipos/masiva",
        json={
            "materia_id": str(mat.id),
            "carrera_id": str(car.id),
            "cohorte_id": str(coh.id),
            "rol_id": str(r.id),
            "usuario_ids": [str(u.id) for u in users],
            "vig_desde": "2025-01-01",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_asignacion_masiva_404_missing_usuario(http_client, test_app, db_session, tenant):
    """TRIANGULATE 6.4: 404 when usuario not found."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-MNF", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordMNF")
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-MNF")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-MNF"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.post(
        "/api/equipos/masiva",
        json={
            "materia_id": str(mat.id),
            "carrera_id": str(car.id),
            "cohorte_id": str(coh.id),
            "rol_id": str(r.id),
            "usuario_ids": [str(uuid.uuid4())],
            "vig_desde": "2025-01-01",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_asignacion_masiva_422_too_many_users(http_client, test_app, db_session, tenant):
    """TRIANGULATE 6.4: 422 when >100 usuarios."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-422", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="Coord422")
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-422")
    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-422"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.post(
        "/api/equipos/masiva",
        json={
            "materia_id": str(uuid.uuid4()),
            "carrera_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "rol_id": str(r.id),
            "usuario_ids": [str(uuid.uuid4()) for _ in range(101)],
            "vig_desde": "2025-01-01",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_asignacion_masiva_403_without_permission(http_client, test_app, db_session, tenant):
    """TRIANGULATE 6.4: 403 without equipos:asignar."""
    u = await _create_usuario(db_session, tenant)
    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.post(
        "/api/equipos/masiva",
        json={
            "materia_id": str(uuid.uuid4()),
            "carrera_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "rol_id": str(uuid.uuid4()),
            "usuario_ids": [str(uuid.uuid4())],
            "vig_desde": "2025-01-01",
        },
    )
    assert resp.status_code == 403


# ===== 7. Clonar =====

@pytest.mark.asyncio
async def test_clonar_equipo_201(http_client, test_app, db_session, tenant):
    """RED 7.1: POST /api/equipos/clonar duplicates equipo."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-CLN", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordCln")
    u = await _create_usuario(db_session, tenant, nombre="ProfCln")
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-CLN")
    mat = await _create_materia(db_session, tenant, cod="MAT-ORIG")
    car = await _create_carrera(db_session, tenant, cod="CAR-ORIG")
    coh = await _create_cohorte(db_session, tenant, car, nombre="COH-ORIG")
    dst_mat = await _create_materia(db_session, tenant, cod="MAT-DST")
    dst_car = await _create_carrera(db_session, tenant, cod="CAR-DST")
    dst_coh = await _create_cohorte(db_session, tenant, dst_car, nombre="COH-DST")

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-CLN"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    for _ in range(2):
        a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today() - timedelta(days=30))
        db_session.add(a)
    await db_session.commit()

    resp = await http_client.post(
        "/api/equipos/clonar",
        json={
            "origen_materia_id": str(mat.id),
            "origen_carrera_id": str(car.id),
            "origen_cohorte_id": str(coh.id),
            "destino_materia_id": str(dst_mat.id),
            "destino_carrera_id": str(dst_car.id),
            "destino_cohorte_id": str(dst_coh.id),
            "nueva_vig_desde": "2025-01-01",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["materia_id"] == str(dst_mat.id)
    assert len(data["asignaciones"]) == 2


@pytest.mark.asyncio
async def test_clonar_equipo_404_empty_origen(http_client, test_app, db_session, tenant):
    """TRIANGULATE 7.4: 404 when origen has no active assignments."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-CNF", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordCNF")
    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-CNF"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.post(
        "/api/equipos/clonar",
        json={
            "origen_materia_id": str(uuid.uuid4()),
            "origen_carrera_id": str(uuid.uuid4()),
            "origen_cohorte_id": str(uuid.uuid4()),
            "destino_materia_id": str(uuid.uuid4()),
            "destino_carrera_id": str(uuid.uuid4()),
            "destino_cohorte_id": str(uuid.uuid4()),
            "nueva_vig_desde": "2025-01-01",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_clonar_equipo_403_without_permission(http_client, test_app, db_session, tenant):
    """TRIANGULATE 7.4: 403 without equipos:asignar."""
    u = await _create_usuario(db_session, tenant)
    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.post(
        "/api/equipos/clonar",
        json={
            "origen_materia_id": str(uuid.uuid4()),
            "origen_carrera_id": str(uuid.uuid4()),
            "origen_cohorte_id": str(uuid.uuid4()),
            "destino_materia_id": str(uuid.uuid4()),
            "destino_carrera_id": str(uuid.uuid4()),
            "destino_cohorte_id": str(uuid.uuid4()),
            "nueva_vig_desde": "2025-01-01",
        },
    )
    assert resp.status_code == 403


# ===== 8. Vigencia =====

@pytest.mark.asyncio
async def test_modificar_vigencia_200(http_client, test_app, db_session, tenant):
    """RED 8.1: PATCH /api/equipos/vigencia updates equipo."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-VIG", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordVig")
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-VIG")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-VIG"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date(2020, 1, 1))
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.patch(
        f"/api/equipos/vigencia?materia_id={mat.id}&carrera_id={car.id}&cohorte_id={coh.id}",
        json={"vig_desde": "2025-06-01", "vig_hasta": "2025-12-31"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["asignaciones"][0]["vig_desde"] == "2025-06-01"
    assert data["asignaciones"][0]["vig_hasta"] == "2025-12-31"


@pytest.mark.asyncio
async def test_modificar_vigencia_422_invalid_dates(http_client, test_app, db_session, tenant):
    """TRIANGULATE 8.4: 422 when vig_desde > vig_hasta."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-VINV", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordVInv")
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-VINV")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-VINV"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date(2020, 1, 1))
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.patch(
        f"/api/equipos/vigencia?materia_id={mat.id}&carrera_id={car.id}&cohorte_id={coh.id}",
        json={"vig_desde": "2025-12-31", "vig_hasta": "2025-01-01"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_modificar_vigencia_404_not_found(http_client, test_app, db_session, tenant):
    """TRIANGULATE 8.4: 404 when equipo not found."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-VNF", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordVNF")
    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-VNF"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.patch(
        f"/api/equipos/vigencia?materia_id={uuid.uuid4()}&carrera_id={uuid.uuid4()}&cohorte_id={uuid.uuid4()}",
        json={"vig_desde": "2025-01-01"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_modificar_vigencia_403_without_permission(http_client, test_app, db_session, tenant):
    """TRIANGULATE 8.4: 403 without equipos:asignar."""
    u = await _create_usuario(db_session, tenant)
    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.patch(
        f"/api/equipos/vigencia?materia_id={uuid.uuid4()}&carrera_id={uuid.uuid4()}&cohorte_id={uuid.uuid4()}",
        json={"vig_desde": "2025-01-01"},
    )
    assert resp.status_code == 403


# ===== 9. Export =====

@pytest.mark.asyncio
async def test_export_equipo_200_csv(http_client, test_app, db_session, tenant):
    """RED 9.1: GET /api/equipos/export returns CSV."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-EXP", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordExp")
    u = await _create_usuario(db_session, tenant, nombre="Juan", apellidos="Pérez")
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-EXP")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-EXP"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, comisiones="A1", vig_desde=date(2025, 1, 1))
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.get(f"/api/equipos/export?materia_id={mat.id}&carrera_id={car.id}&cohorte_id={coh.id}")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_export_csv_includes_header_and_data(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: CSV includes header and data."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-EXD", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordExD")
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant, nombre="PROFESOR-EXD")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-EXD"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date(2025, 1, 1))
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.get(f"/api/equipos/export?materia_id={mat.id}&carrera_id={car.id}&cohorte_id={coh.id}")
    text = resp.text
    lines = text.strip().splitlines()
    assert len(lines) >= 2
    header = lines[0]
    assert "usuario_id" in header
    assert "nombre" in header
    assert "rol" in header


@pytest.mark.asyncio
async def test_export_equipo_404_not_found(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: 404 when equipo not found."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-EXN", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordExN")
    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-EXN"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get(f"/api/equipos/export?materia_id={uuid.uuid4()}&carrera_id={uuid.uuid4()}&cohorte_id={uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_equipo_403_without_permission(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: 403 without equipos:asignar."""
    u = await _create_usuario(db_session, tenant)
    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get(f"/api/equipos/export?materia_id={uuid.uuid4()}&carrera_id={uuid.uuid4()}&cohorte_id={uuid.uuid4()}")
    assert resp.status_code == 403


# ===== 10. Usuario Search =====

@pytest.mark.asyncio
async def test_search_usuarios_returns_matches(http_client, test_app, db_session, tenant):
    """RED 10.1: GET /api/equipos/usuarios/search returns matches."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-SRC", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordSrc")
    u = Usuario(tenant_id=tenant.id, nombre="Martín", apellidos="García")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-SRC"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get("/api/equipos/usuarios/search?q=Martín")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["nombre"] == "Martín"


@pytest.mark.asyncio
async def test_search_usuarios_by_legajo(http_client, test_app, db_session, tenant):
    """TRIANGULATE 10.4: search by legajo."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-LGJ", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordLgj")
    u = Usuario(tenant_id=tenant.id, nombre="Laura", apellidos="Pérez", legajo="LEG-001")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-LGJ"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get("/api/equipos/usuarios/search?q=LEG-001")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["legajo"] == "LEG-001"


@pytest.mark.asyncio
async def test_search_usuarios_empty_no_match(http_client, test_app, db_session, tenant):
    """TRIANGULATE 10.4: empty when no match."""
    await _seed_rol_con_permiso(db_session, tenant, "COORDINADOR-EMP", "equipos:asignar")
    coord_user = await _create_usuario(db_session, tenant, nombre="CoordEmp")
    session = _coord_session(tenant, user_id=coord_user.id, roles=["COORDINADOR-EMP"])
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get("/api/equipos/usuarios/search?q=XXXXXXXXXX")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_search_usuarios_403_without_permission(http_client, test_app, db_session, tenant):
    """TRIANGULATE 10.4: 403 without equipos:asignar."""
    u = await _create_usuario(db_session, tenant)
    session = _prof_session(tenant, user_id=u.id)
    test_app.dependency_overrides[get_current_user] = lambda: session

    resp = await http_client.get("/api/equipos/usuarios/search?q=test")
    assert resp.status_code == 403
