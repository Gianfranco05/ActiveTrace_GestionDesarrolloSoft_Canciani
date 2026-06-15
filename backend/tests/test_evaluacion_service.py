import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.asignacion import Asignacion
from app.models.rol import Rol
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.models.padron import VersionPadron, EntradaPadron
from app.repositories.audit_repository import AuditLogRepository
from app.services.audit_service import AuditService
from app.services.evaluacion_service import EvaluacionService
from app.services.resultado_evaluacion_service import ResultadoEvaluacionService
from app.services.evaluacion_admin_service import EvaluacionAdminService
from app.schemas.evaluaciones import (
    CupoPorDia,
    EvaluacionCreateRequest,
    EvaluacionUpdateRequest,
    ImportarAlumnosRequest,
    ReservaRequest,
    ResultadoRequest,
    EvaluacionResponse,
    EvaluacionDetailResponse,
)


def _make_audit_svc(db_session, tenant_id):
    repo = AuditLogRepository(db_session, tenant_id)
    return AuditService(db_session, repo)


async def _make_actor(db_session, tenant_id) -> uuid.UUID:
    auth = AuthUser(tenant_id=tenant_id, email=f"actor+{str(uuid.uuid4())[:8]}@test.com", password_hash="hashed")
    db_session.add(auth)
    await db_session.flush()
    return auth.id


@pytest.fixture
async def materia(db_session, tenant):
    m = Materia(tenant_id=tenant.id, codigo=f"SVC-{uuid.uuid4().hex[:6]}", nombre="Servicio Materia", estado="Activa")
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.fixture
async def carrera(db_session, tenant):
    c = Carrera(tenant_id=tenant.id, codigo=f"SVC-{uuid.uuid4().hex[:6]}", nombre="Servicio Carrera", estado="Activa")
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.fixture
async def cohorte(db_session, tenant, carrera):
    c = Cohorte(tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026-S", anio=2026, vig_desde=date(2026, 1, 1), estado="Activa")
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.fixture
async def actor(db_session, tenant):
    return await _make_actor(db_session, tenant.id)


async def _make_usuario(db_session, tenant, nombre="Alumno", apellidos="Test", legajo=None, with_roles=None):
    idx = str(uuid.uuid4())[:8]
    auth = AuthUser(tenant_id=tenant.id, email=f"svc+{idx}@test.com", password_hash="hashed")
    db_session.add(auth)
    await db_session.flush()
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos, legajo=legajo or f"LS{idx}")
    db_session.add(u)
    await db_session.flush()
    if with_roles:
        for role_name in with_roles:
            rol_q = select(Rol).where(Rol.nombre == role_name, Rol.tenant_id == tenant.id, Rol.deleted_at.is_(None))
            r = await db_session.execute(rol_q)
            rol = r.scalar_one_or_none()
            if not rol:
                rol = Rol(tenant_id=tenant.id, nombre=role_name)
                db_session.add(rol)
                await db_session.flush()
            a = Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=rol.id, vig_desde=date(2024, 1, 1))
            db_session.add(a)
        await db_session.flush()
    return u


def make_create_request(materia_id, cohorte_id) -> EvaluacionCreateRequest:
    return EvaluacionCreateRequest(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        tipo="Coloquio",
        instancia="Primer cuatrimestre 2026",
        cupos_por_dia=[CupoPorDia(fecha=date(2026, 6, 15), cupo=5)],
    )


# ──── Group 6: Crear ────

async def test_crear_convocatoria(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, cohorte.id)

    result = await svc.crear(req, actor)
    assert result.id is not None
    assert result.materia_nombre == materia.nombre
    assert result.cohorte_nombre == cohorte.nombre
    assert result.tipo == "Coloquio"
    assert result.activa is True
    assert result.total_convocados == 0
    assert result.cupos_libres == 5


async def test_crear_convocatoria_rejects_materia_inexistente(db_session, tenant, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(uuid.uuid4(), cohorte.id)
    with pytest.raises(HTTPException) as exc:
        await svc.crear(req, actor)
    assert exc.value.status_code == 404


async def test_crear_convocatoria_rejects_cohorte_inexistente(db_session, tenant, materia, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        await svc.crear(req, actor)
    assert exc.value.status_code == 404


async def test_crear_convocatoria_rejects_duplicate_dates(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = EvaluacionCreateRequest(
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="TP",
        instancia="Test",
        cupos_por_dia=[
            CupoPorDia(fecha=date(2026, 6, 15), cupo=5),
            CupoPorDia(fecha=date(2026, 6, 15), cupo=3),
        ],
    )
    with pytest.raises(HTTPException) as exc:
        await svc.crear(req, actor)
    assert exc.value.status_code == 422


async def test_crear_convocatoria_generates_audit(db_session, tenant, materia, cohorte, actor):
    audit_svc = _make_audit_svc(db_session, tenant.id)
    svc = EvaluacionService(db_session, tenant.id, audit_svc)
    req = make_create_request(materia.id, cohorte.id)

    await svc.crear(req, actor)

    from app.models.audit_log import AuditLog
    q = select(AuditLog).where(AuditLog.tenant_id == tenant.id)
    r = await db_session.execute(q)
    logs = list(r.scalars().all())
    assert len(logs) >= 1


# ──── Group 7: Actualizar y Obtener ────

async def test_actualizar_convocatoria(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, cohorte.id)
    ev = await svc.crear(req, actor)

    upd = EvaluacionUpdateRequest(instancia="Nueva instancia")
    result = await svc.actualizar(ev.id, upd, actor)
    assert result.instancia == "Nueva instancia"


async def test_actualizar_convocatoria_inexistente(db_session, tenant, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    upd = EvaluacionUpdateRequest(instancia="Nope")
    with pytest.raises(HTTPException) as exc:
        await svc.actualizar(uuid.uuid4(), upd, actor)
    assert exc.value.status_code == 404


async def test_actualizar_convocatoria_parcial(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, cohorte.id)
    ev = await svc.crear(req, actor)

    upd = EvaluacionUpdateRequest(activa=False)
    result = await svc.actualizar(ev.id, upd, actor)
    assert result.activa is False
    assert result.instancia == "Primer cuatrimestre 2026"


async def test_obtener_convocatoria_con_alumnos(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, cohorte.id)
    ev = await svc.crear(req, actor)

    alumno1 = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    alumno2 = await _make_usuario(db_session, tenant, legajo="AL02", with_roles=["ALUMNO"])
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno1.id, alumno2.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)

    detail = await svc.obtener(ev.id)
    assert len(detail.alumnos_convocados) == 2
    assert str(alumno1.id) in detail.alumnos_convocados


async def test_obtener_convocatoria_inexistente(db_session, tenant):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    with pytest.raises(HTTPException) as exc:
        await svc.obtener(uuid.uuid4())
    assert exc.value.status_code == 404


# ──── Group 8: Listar y Metricas ────

async def test_listar_convocatorias(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, cohorte.id)
    await svc.crear(req, actor)

    items, total = await svc.listar({})
    assert total == 1
    assert len(items) == 1
    assert items[0]["materia_nombre"] == materia.nombre


async def test_listar_convocatorias_filtro_materia(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, cohorte.id)
    await svc.crear(req, actor)

    items, total = await svc.listar({"materia_id": materia.id})
    assert total == 1
    items2, total2 = await svc.listar({"materia_id": uuid.uuid4()})
    assert total2 == 0


async def test_listar_convocatorias_filtro_activas(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = make_create_request(materia.id, cohorte.id)
    ev = await svc.crear(req, actor)
    await svc.actualizar(ev.id, EvaluacionUpdateRequest(activa=False), actor)

    items, total = await svc.listar({"activa": False})
    assert total == 1


async def test_listar_convocatorias_vacio(db_session, tenant):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    items, total = await svc.listar({})
    assert total == 0


async def test_metricas_convocatoria_sin_reservas(db_session, tenant, materia, cohorte, actor):
    admin_svc = EvaluacionAdminService(db_session, tenant.id)
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    met = await admin_svc.metricas_convocatoria(ev.id)
    assert met.total_convocados == 0
    assert met.total_reservas == 0


async def test_metricas_convocatoria_inexistente(db_session, tenant):
    admin_svc = EvaluacionAdminService(db_session, tenant.id)
    with pytest.raises(HTTPException) as exc:
        await admin_svc.metricas_convocatoria(uuid.uuid4())
    assert exc.value.status_code == 404


async def test_metricas_panel_con_datos(db_session, tenant, materia, cohorte, actor):
    admin_svc = EvaluacionAdminService(db_session, tenant.id)
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    p = await admin_svc.metricas_panel()
    assert p.total_convocatorias_activas == 1
    assert p.total_resultados == 0


async def test_metricas_panel_vacio(db_session, tenant):
    admin_svc = EvaluacionAdminService(db_session, tenant.id)
    p = await admin_svc.metricas_panel()
    assert p.total_convocatorias_activas == 0
    assert p.tasa_aprobacion is None


# ──── Group 9: Importar Alumnos ────

async def test_importar_alumnos_manual(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])

    req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    result = await resultado_svc.importar_alumnos(ev.id, req, actor)
    assert len(result.alumnos_convocados) == 1
    assert str(alumno.id) in result.alumnos_convocados


async def test_importar_alumnos_manual_rejects_no_alumno_role(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    usuario = await _make_usuario(db_session, tenant)
    req = ImportarAlumnosRequest(modo="manual", usuario_ids=[usuario.id])
    with pytest.raises(HTTPException) as exc:
        await resultado_svc.importar_alumnos(ev.id, req, actor)
    assert exc.value.status_code == 400


async def test_importar_alumnos_manual_rejects_inexistente_usuario(db_session, tenant, materia, cohorte, actor):
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    req = ImportarAlumnosRequest(modo="manual", usuario_ids=[uuid.uuid4()])
    with pytest.raises(HTTPException) as exc:
        await resultado_svc.importar_alumnos(ev.id, req, actor)
    assert exc.value.status_code == 404


async def test_importar_alumnos_padron_sin_datos(db_session, tenant, materia, cohorte, actor):
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    req = ImportarAlumnosRequest(modo="padron", materia_id=materia.id, cohorte_id=cohorte.id)
    with pytest.raises(HTTPException) as exc:
        await resultado_svc.importar_alumnos(ev.id, req, actor)
    assert exc.value.status_code == 400


async def test_importar_alumnos_evaluacion_inactiva(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)
    await svc.actualizar(ev.id, EvaluacionUpdateRequest(activa=False), actor)

    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    with pytest.raises(HTTPException) as exc:
        await resultado_svc.importar_alumnos(ev.id, req, actor)
    assert exc.value.status_code == 400


# ──── Group 10: Reservar Turno ────

async def test_reservar_turno_exitoso(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Reserva test",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 7, 1), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)

    result = await svc.reservar_turno(
        ev.id, datetime(2026, 7, 1, 14, 0, tzinfo=timezone.utc), actor, alumno.id,
    )
    assert result.estado == "Activa"
    assert result.evaluacion_id == ev.id
    assert result.alumno_id == alumno.id


async def test_reservar_no_convocado(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="No convocado",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 7, 1), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])

    with pytest.raises(HTTPException) as exc:
        await svc.reservar_turno(ev.id, datetime(2026, 7, 1, 14, 0, tzinfo=timezone.utc), actor, alumno.id)
    assert exc.value.status_code == 403


async def test_reservar_fecha_no_disponible(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Fecha no disp",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 7, 1), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)

    with pytest.raises(HTTPException) as exc:
        await svc.reservar_turno(ev.id, datetime(2026, 7, 2, 14, 0, tzinfo=timezone.utc), actor, alumno.id)
    assert exc.value.status_code == 400


async def test_reservar_cupo_lleno(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Cupo lleno",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 8, 1), cupo=1)],
        ),
        actor,
    )
    alumno1 = await _make_usuario(db_session, tenant, nombre="A1", legajo="L01", with_roles=["ALUMNO"])
    alumno2 = await _make_usuario(db_session, tenant, nombre="A2", legajo="L02", with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno1.id, alumno2.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)

    await svc.reservar_turno(ev.id, datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc), actor, alumno1.id)
    with pytest.raises(HTTPException) as exc:
        await svc.reservar_turno(ev.id, datetime(2026, 8, 1, 15, 0, tzinfo=timezone.utc), actor, alumno2.id)
    assert exc.value.status_code == 409


async def test_reservar_duplicado(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Duplicado",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 9, 1), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)

    await svc.reservar_turno(ev.id, datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc), actor, alumno.id)
    with pytest.raises(HTTPException) as exc:
        await svc.reservar_turno(ev.id, datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc), actor, alumno.id)
    assert exc.value.status_code == 409


async def test_reservar_evaluacion_inactiva(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Inactiva",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 10, 1), cupo=5)],
        ),
        actor,
    )
    await svc.actualizar(ev.id, EvaluacionUpdateRequest(activa=False), actor)
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])

    with pytest.raises(HTTPException) as exc:
        await svc.reservar_turno(ev.id, datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc), actor, alumno.id)
    assert exc.value.status_code == 400


# ──── Group 11: Cancelar y Mis Reservas ────

async def test_cancelar_reserva_exitoso(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Cancel test",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 11, 1), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    reserva = await svc.reservar_turno(
        ev.id, datetime(2026, 11, 1, 14, 0, tzinfo=timezone.utc), actor, alumno.id,
    )

    result = await svc.cancelar_reserva(reserva.id, actor, alumno.id)
    assert result.estado == "Cancelada"


async def test_cancelar_reserva_ajena_rechazado(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Ajena",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 11, 15), cupo=5)],
        ),
        actor,
    )
    alumno1 = await _make_usuario(db_session, tenant, nombre="A1", legajo="L11", with_roles=["ALUMNO"])
    alumno2 = await _make_usuario(db_session, tenant, nombre="A2", legajo="L12", with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno1.id, alumno2.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    reserva = await svc.reservar_turno(
        ev.id, datetime(2026, 11, 15, 14, 0, tzinfo=timezone.utc), actor, alumno1.id,
    )

    with pytest.raises(HTTPException) as exc:
        await svc.cancelar_reserva(reserva.id, actor, alumno2.id)
    assert exc.value.status_code == 403


async def test_cancelar_reserva_ya_cancelada(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Ya cancelada",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 11, 20), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    reserva = await svc.reservar_turno(
        ev.id, datetime(2026, 11, 20, 14, 0, tzinfo=timezone.utc), actor, alumno.id,
    )
    await svc.cancelar_reserva(reserva.id, actor, alumno.id)

    with pytest.raises(HTTPException) as exc:
        await svc.cancelar_reserva(reserva.id, actor, alumno.id)
    assert exc.value.status_code == 409


async def test_cancelar_reserva_inexistente(db_session, tenant, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    with pytest.raises(HTTPException) as exc:
        await svc.cancelar_reserva(uuid.uuid4(), actor, uuid.uuid4())
    assert exc.value.status_code == 404


async def test_listar_mis_reservas_activas(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Mis activas",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 12, 1), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    await svc.reservar_turno(ev.id, datetime(2026, 12, 1, 14, 0, tzinfo=timezone.utc), actor, alumno.id)

    reservas = await svc.listar_mis_reservas(alumno.id)
    assert len(reservas) == 1
    assert reservas[0].estado == "Activa"


async def test_listar_mis_reservas_canceladas(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Mis canceladas",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 12, 5), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    reserva = await svc.reservar_turno(
        ev.id, datetime(2026, 12, 5, 14, 0, tzinfo=timezone.utc), actor, alumno.id,
    )
    await svc.cancelar_reserva(reserva.id, actor, alumno.id)

    canceladas = await svc.listar_mis_reservas(alumno.id, "Cancelada")
    assert len(canceladas) == 1


async def test_listar_mis_reservas_vacio(db_session, tenant):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    reservas = await svc.listar_mis_reservas(uuid.uuid4())
    assert len(reservas) == 0


# ──── Group 12: Resultados ────

async def test_registrar_resultado(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])

    req = ResultadoRequest(alumno_id=alumno.id, nota_final="8.5")
    result = await resultado_svc.registrar_resultado(ev.id, req, actor)
    assert result.nota_final == "8.5"
    assert result.alumno_nombre == alumno.nombre


async def test_registrar_resultado_reemplaza_anterior(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])

    await resultado_svc.registrar_resultado(ev.id, ResultadoRequest(alumno_id=alumno.id, nota_final="4.0"), actor)
    result = await resultado_svc.registrar_resultado(ev.id, ResultadoRequest(alumno_id=alumno.id, nota_final="9.0"), actor)
    assert result.nota_final == "9.0"


async def test_registrar_resultado_alumno_inexistente(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    req = ResultadoRequest(alumno_id=uuid.uuid4(), nota_final="7.0")
    with pytest.raises(HTTPException) as exc:
        await resultado_svc.registrar_resultado(ev.id, req, actor)
    assert exc.value.status_code == 404


async def test_registrar_resultado_evaluacion_inexistente(db_session, tenant, actor):
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    req = ResultadoRequest(alumno_id=uuid.uuid4(), nota_final="7.0")
    with pytest.raises(HTTPException) as exc:
        await resultado_svc.registrar_resultado(uuid.uuid4(), req, actor)
    assert exc.value.status_code == 404


# ──── Group 13: Admin Global ────

async def test_agenda_reservas(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Agenda test",
            cupos_por_dia=[CupoPorDia(fecha=date(2027, 1, 1), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    await svc.reservar_turno(ev.id, datetime(2027, 1, 1, 14, 0, tzinfo=timezone.utc), actor, alumno.id)

    items, total = await svc.agenda_reservas({})
    assert total == 1
    assert items[0]["materia_nombre"] == materia.nombre


async def test_agenda_reservas_filtro_materia(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Agenda filtro",
            cupos_por_dia=[CupoPorDia(fecha=date(2027, 1, 5), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    await svc.reservar_turno(ev.id, datetime(2027, 1, 5, 14, 0, tzinfo=timezone.utc), actor, alumno.id)

    items, total = await svc.agenda_reservas({"materia_id": uuid.uuid4()})
    assert total == 0


async def test_agenda_reservas_filtro_fechas(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(
        EvaluacionCreateRequest(
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Coloquio", instancia="Agenda fechas",
            cupos_por_dia=[CupoPorDia(fecha=date(2027, 1, 10), cupo=5)],
        ),
        actor,
    )
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    import_req = ImportarAlumnosRequest(modo="manual", usuario_ids=[alumno.id])
    await resultado_svc.importar_alumnos(ev.id, import_req, actor)
    await svc.reservar_turno(ev.id, datetime(2027, 1, 10, 14, 0, tzinfo=timezone.utc), actor, alumno.id)

    items, total = await svc.agenda_reservas({"fecha_desde": date(2027, 1, 15)})
    assert total == 0


async def test_agenda_reservas_vacia(db_session, tenant):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    items, total = await svc.agenda_reservas({})
    assert total == 0


async def test_consolidado_filtro_materia(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    await resultado_svc.registrar_resultado(ev.id, ResultadoRequest(alumno_id=alumno.id, nota_final="7.5"), actor)

    items, total = await resultado_svc.consolidado({"materia_id": uuid.uuid4()})
    assert total == 0


async def test_consolidado_filtro_alumno(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)
    alumno = await _make_usuario(db_session, tenant, with_roles=["ALUMNO"])
    await resultado_svc.registrar_resultado(ev.id, ResultadoRequest(alumno_id=alumno.id, nota_final="6.0"), actor)

    items, total = await resultado_svc.consolidado({"alumno_id": alumno.id})
    assert total == 1


async def test_consolidado_vacio(db_session, tenant):
    resultado_svc = ResultadoEvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    items, total = await resultado_svc.consolidado({})
    assert total == 0


async def test_admin_convocatorias_incluye_inactivas(db_session, tenant, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    admin_svc = EvaluacionAdminService(db_session, tenant.id)
    ev = await svc.crear(make_create_request(materia.id, cohorte.id), actor)
    await svc.actualizar(ev.id, EvaluacionUpdateRequest(activa=False), actor)

    items, total = await admin_svc.admin_convocatorias({"incluir_inactivas": True})
    assert total == 1
    assert items[0]["activa"] is False


async def test_admin_convocatorias_tenant_isolation(db_session, tenant, tenant_a, materia, cohorte, actor):
    svc = EvaluacionService(db_session, tenant.id, _make_audit_svc(db_session, tenant.id))
    admin_svc_a = EvaluacionAdminService(db_session, tenant_a.id)
    await svc.crear(make_create_request(materia.id, cohorte.id), actor)

    items, total = await admin_svc_a.admin_convocatorias({})
    assert total == 0
