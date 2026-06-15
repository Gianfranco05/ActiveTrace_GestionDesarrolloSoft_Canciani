"""TDD: EquipoService — RED → GREEN → TRIANGULATE."""

import uuid
from datetime import date, timedelta

import pytest

from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.audit_repository import AuditLogRepository
from app.services.audit_service import AuditService
from app.services.equipo_service import EquipoService
from app.schemas.asignaciones import (
    AsignacionMasivaRequest,
    ClonarRequest,
    VigenciaUpdateRequest,
)
from app.core.security import hash_password


async def _create_auth_user(db_session, tenant, email):
    au = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password("Secure123"),
    )
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    return au


async def _create_usuario(db_session, tenant, nombre="EquipoSvc", apellidos="Test", legajo=None):
    au = await _create_auth_user(db_session, tenant, f"{nombre.lower()}.{apellidos.lower()}.{uuid.uuid4().hex[:6]}@test.com")
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


async def _create_materia(db_session, tenant, cod="MAT-SVC"):
    m = Materia(codigo=cod, nombre="Test Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _create_carrera(db_session, tenant, cod="CAR-SVC"):
    c = Carrera(codigo=cod, nombre="Test Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


async def _create_cohorte(db_session, tenant, carrera, nombre="COH-SVC"):
    c = Cohorte(carrera_id=carrera.id, nombre=nombre, anio=2026, vig_desde=date.today(), tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


@pytest.fixture
def equipo_service(db_session, tenant):
    audit_repo = AuditLogRepository(db_session, tenant.id)
    audit_svc = AuditService(db_session, audit_repo)
    return EquipoService(session=db_session, audit_service=audit_svc, tenant_id=tenant.id)


@pytest.mark.asyncio
async def test_listar_mis_equipos_returns_user_asignaciones(db_session, tenant, equipo_service):
    """RED 3.1: listar_mis_equipos returns filtered Asignaciones for user."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)

    a1 = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, vig_desde=date.today() - timedelta(days=10))
    a2 = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, vig_desde=date.today() + timedelta(days=10))
    db_session.add_all([a1, a2])
    await db_session.commit()
    await db_session.refresh(a1)
    await db_session.refresh(a2)

    result = await equipo_service.listar_mis_equipos(u.id, tenant.id, {"estado": "Vigente"})
    assert len(result) >= 1
    assert result[0].usuario_id == u.id


@pytest.mark.asyncio
async def test_listar_mis_equipos_filter_by_estado(db_session, tenant, equipo_service):
    """TRIANGULATE: filter by estado."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)

    a1 = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, vig_desde=date.today() - timedelta(days=30), vig_hasta=date.today() - timedelta(days=1))
    db_session.add(a1)
    await db_session.commit()

    result_vencida = await equipo_service.listar_mis_equipos(u.id, tenant.id, {"estado": "Vencida"})
    assert len(result_vencida) >= 1

    result_vigente = await equipo_service.listar_mis_equipos(u.id, tenant.id, {"estado": "Vigente"})
    vencida_ids = {a.id for a in result_vencida}
    vigente_ids = {a.id for a in result_vigente}
    assert a1.id in vencida_ids
    assert a1.id not in vigente_ids


@pytest.mark.asyncio
async def test_listar_mis_equipos_todos(db_session, tenant, equipo_service):
    """TRIANGULATE: estado=Todos returns all."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)

    a1 = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, vig_desde=date.today() - timedelta(days=30), vig_hasta=date.today() - timedelta(days=1))
    db_session.add(a1)
    await db_session.commit()

    result = await equipo_service.listar_mis_equipos(u.id, tenant.id, {"estado": "Todos"})
    assert len(result) >= 1


@pytest.mark.asyncio
async def test_listar_mis_equipos_empty(db_session, tenant, equipo_service):
    """TRIANGULATE: user without assignments returns empty."""
    u = await _create_usuario(db_session, tenant, nombre="NoAsig")
    result = await equipo_service.listar_mis_equipos(u.id, tenant.id, {"estado": "Vigente"})
    assert result == []


@pytest.mark.asyncio
async def test_listar_equipos_returns_grouped(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: listar_equipos returns grouped EquipoResponse."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    for _ in range(3):
        a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today())
        db_session.add(a)
    await db_session.commit()

    result = await equipo_service.listar_equipos(tenant.id)
    assert len(result) >= 1
    eq = next(e for e in result if e.materia_id == mat.id)
    assert eq.total_asignaciones == 3


@pytest.mark.asyncio
async def test_asignacion_masiva_creates_all(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: asignacion_masiva creates N asignaciones."""
    users = [await _create_usuario(db_session, tenant, nombre=f"User{i}") for i in range(3)]
    r = await _create_rol(db_session, tenant)
    actor = await _create_usuario(db_session, tenant, nombre="Actor")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    req = AsignacionMasivaRequest(
        materia_id=mat.id,
        carrera_id=car.id,
        cohorte_id=coh.id,
        rol_id=r.id,
        usuario_ids=[u.id for u in users],
        vig_desde=date.today(),
    )
    result = await equipo_service.asignacion_masiva(req, actor.id)
    assert len(result) == 3
    assert all(a.materia_id == mat.id for a in result)


@pytest.mark.asyncio
async def test_asignacion_masiva_rollback_on_missing_usuario(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: rolls back when usuario does not exist."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    actor = await _create_usuario(db_session, tenant, nombre="Actor2")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    req = AsignacionMasivaRequest(
        materia_id=mat.id,
        carrera_id=car.id,
        cohorte_id=coh.id,
        rol_id=r.id,
        usuario_ids=[u.id, uuid.uuid4()],
        vig_desde=date.today(),
    )
    with pytest.raises(Exception):
        await equipo_service.asignacion_masiva(req, actor.id)

    repo = AsignacionRepository(db_session, tenant.id)
    all_asig = await repo.list()
    assert len(all_asig) == 0


@pytest.mark.asyncio
async def test_clonar_equipo_duplicates_assignments(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: clonar duplicates active assignments."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)
    dst_mat = await _create_materia(db_session, tenant, cod="MAT-DST")
    dst_car = await _create_carrera(db_session, tenant, cod="CAR-DST")
    dst_coh = await _create_cohorte(db_session, tenant, dst_car, nombre="COH-DST")
    actor = await _create_usuario(db_session, tenant, nombre="Actor3")

    for _ in range(2):
        a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today() - timedelta(days=30))
        db_session.add(a)
    await db_session.commit()

    req = ClonarRequest(
        origen_materia_id=mat.id,
        origen_carrera_id=car.id,
        origen_cohorte_id=coh.id,
        destino_materia_id=dst_mat.id,
        destino_carrera_id=dst_car.id,
        destino_cohorte_id=dst_coh.id,
        nueva_vig_desde=date.today(),
    )
    result = await equipo_service.clonar_equipo(req, actor.id)
    assert len(result.asignaciones) == 2
    assert result.materia_id == dst_mat.id


@pytest.mark.asyncio
async def test_clonar_equipo_only_vigente(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: only clones vigente assignments."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)
    dst_mat = await _create_materia(db_session, tenant, cod="MAT-DST2")
    dst_car = await _create_carrera(db_session, tenant, cod="CAR-DST2")
    dst_coh = await _create_cohorte(db_session, tenant, dst_car, nombre="COH-DST2")
    actor = await _create_usuario(db_session, tenant, nombre="Actor4")

    vigente = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today() - timedelta(days=30))
    vencida = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today() - timedelta(days=60), vig_hasta=date.today() - timedelta(days=1))
    db_session.add_all([vigente, vencida])
    await db_session.commit()

    req = ClonarRequest(
        origen_materia_id=mat.id,
        origen_carrera_id=car.id,
        origen_cohorte_id=coh.id,
        destino_materia_id=dst_mat.id,
        destino_carrera_id=dst_car.id,
        destino_cohorte_id=dst_coh.id,
        nueva_vig_desde=date.today(),
    )
    result = await equipo_service.clonar_equipo(req, actor.id)
    assert len(result.asignaciones) == 1


@pytest.mark.asyncio
async def test_clonar_equipo_responsable_resolution(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: responsable_id is resolved when responsable is also cloned."""
    u_resp = await _create_usuario(db_session, tenant, nombre="Responsable")
    u_sub = await _create_usuario(db_session, tenant, nombre="Subordinado")
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)
    dst_mat = await _create_materia(db_session, tenant, cod="MAT-DST3")
    dst_car = await _create_carrera(db_session, tenant, cod="CAR-DST3")
    dst_coh = await _create_cohorte(db_session, tenant, dst_car, nombre="COH-DST3")
    actor = await _create_usuario(db_session, tenant, nombre="Actor5")

    a_resp = Asignacion(tenant_id=tenant.id, usuario_id=u_resp.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today() - timedelta(days=30))
    db_session.add(a_resp)
    await db_session.commit()
    await db_session.refresh(a_resp)

    a_sub = Asignacion(tenant_id=tenant.id, usuario_id=u_sub.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today() - timedelta(days=30), responsable_id=a_resp.id)
    db_session.add(a_sub)
    await db_session.commit()
    await db_session.refresh(a_sub)

    req = ClonarRequest(
        origen_materia_id=mat.id,
        origen_carrera_id=car.id,
        origen_cohorte_id=coh.id,
        destino_materia_id=dst_mat.id,
        destino_carrera_id=dst_car.id,
        destino_cohorte_id=dst_coh.id,
        nueva_vig_desde=date.today(),
    )
    result = await equipo_service.clonar_equipo(req, actor.id)
    assert len(result.asignaciones) == 2

    cloned_sub = next(a for a in result.asignaciones if a.usuario_id == u_sub.id)
    assert cloned_sub.responsable_id is not None
    assert cloned_sub.responsable_id != a_resp.id


@pytest.mark.asyncio
async def test_modificar_vigencia_updates_all(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: modificar_vigencia updates equipo."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    for _ in range(2):
        a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date(2020, 1, 1), vig_hasta=date(2020, 12, 31))
        db_session.add(a)
    await db_session.commit()

    req = VigenciaUpdateRequest(vig_desde=date(2025, 1, 1), vig_hasta=date(2025, 12, 31))
    result = await equipo_service.modificar_vigencia(mat.id, car.id, coh.id, req, u.id)

    assert len(result.asignaciones) == 2
    assert all(a.vig_desde == date(2025, 1, 1) for a in result.asignaciones)
    assert all(a.vig_hasta == date(2025, 12, 31) for a in result.asignaciones)


@pytest.mark.asyncio
async def test_modificar_vigencia_invalid_dates(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: invalid date range raises error."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, vig_desde=date.today())
    db_session.add(a)
    await db_session.commit()

    req = VigenciaUpdateRequest(vig_desde=date(2025, 12, 31), vig_hasta=date(2025, 1, 1))
    with pytest.raises(ValueError, match="vig_desde must be before vig_hasta"):
        await equipo_service.modificar_vigencia(mat.id, car.id, coh.id, req, u.id)


@pytest.mark.asyncio
async def test_exportar_equipo_generates_csv(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: exportar_equipo generates CSV string."""
    u = await _create_usuario(db_session, tenant, nombre="Juan", apellidos="Pérez")
    r = await _create_rol(db_session, tenant, nombre="PROFESOR")
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id, comisiones="A1", vig_desde=date(2025, 1, 1))
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    csv_output = await equipo_service.exportar_equipo(mat.id, car.id, coh.id)
    assert "usuario_id" in csv_output
    assert "nombre" in csv_output
    assert "rol" in csv_output
    assert len(csv_output.splitlines()) >= 2


@pytest.mark.asyncio
async def test_buscar_usuarios_returns_matches(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: buscar_usuarios finds by name."""
    u = Usuario(tenant_id=tenant.id, nombre="Martín", apellidos="García")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    result = await equipo_service.buscar_usuarios("Martín", tenant.id, 20)
    assert len(result) >= 1
    assert result[0].nombre == "Martín"


@pytest.mark.asyncio
async def test_buscar_usuarios_empty(db_session, tenant, equipo_service):
    """TRIANGULATE 3.4: buscar_usuarios returns empty for no match."""
    result = await equipo_service.buscar_usuarios("XXXXXXXXXX", tenant.id, 20)
    assert result == []
