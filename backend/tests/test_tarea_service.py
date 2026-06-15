import uuid

import pytest
from fastapi import HTTPException

from app.models.auth_user import AuthUser
from app.models.materia import Materia
from app.models.tarea import Tarea
from app.models.usuario import Usuario
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.tareas import (
    ComentarioCreateRequest,
    EstadoTarea,
    TareaCreateRequest,
    TareaDelegateRequest,
    TareaEstadoUpdateRequest,
    TareaUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.tarea_service import TareaService


async def _crear_usuario(db_session, tenant, nombre="Test", apellidos="User", email=None):
    uid = str(uuid.uuid4())[:8]
    auth = AuthUser(tenant_id=tenant.id, email=email or f"svc+{uid}@test.com", password_hash="hashed")
    db_session.add(auth)
    await db_session.flush()
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos)
    db_session.add(u)
    await db_session.flush()
    return u


async def _crear_materia(db_session, tenant):
    m = Materia(tenant_id=tenant.id, codigo=f"SVC-{str(uuid.uuid4())[:6]}", nombre="Svc Materia")
    db_session.add(m)
    await db_session.flush()
    return m


def _svc(db_session, tenant):
    audit_repo = AuditLogRepository(db_session, tenant.id)
    audit_svc = AuditService(db_session, audit_repo)
    return TareaService(db_session, tenant.id, audit_svc)


COORD = ["COORDINADOR"]
PROFE = ["PROFESOR"]


@pytest.mark.asyncio
async def test_crear_tarea_asigna_estado_pendiente(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_docente = await _crear_usuario(db_session, tenant, "Docente")
    svc = _svc(db_session, tenant)

    req = TareaCreateRequest(asignado_a=u_docente.id, descripcion="Revisar notas")
    tarea = await svc.crear_tarea(req, u_coord.id, COORD)

    assert tarea.estado == "Pendiente"
    assert tarea.asignado_por == u_coord.id
    assert tarea.asignado_a == u_docente.id
    assert tarea.descripcion == "Revisar notas"


@pytest.mark.asyncio
async def test_crear_tarea_sin_materia_institucional(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_docente = await _crear_usuario(db_session, tenant, "Docente")
    svc = _svc(db_session, tenant)

    req = TareaCreateRequest(asignado_a=u_docente.id, descripcion="Sin materia")
    tarea = await svc.crear_tarea(req, u_coord.id, COORD)

    assert tarea.materia_id is None
    assert tarea.estado == "Pendiente"


@pytest.mark.asyncio
async def test_crear_tarea_profesor_403(db_session, tenant):
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    u_docente = await _crear_usuario(db_session, tenant, "Otro")
    svc = _svc(db_session, tenant)

    req = TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test")
    with pytest.raises(HTTPException) as exc_info:
        await svc.crear_tarea(req, u_profe.id, PROFE)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_crear_tarea_audit(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_docente = await _crear_usuario(db_session, tenant, "Docente")
    svc = _svc(db_session, tenant)

    req = TareaCreateRequest(asignado_a=u_docente.id, descripcion="Audit test")
    tarea = await svc.crear_tarea(req, u_coord.id, COORD)

    logs = await AuditLogRepository(db_session, tenant.id).list(accion="TAREA_CREAR")
    assert any("tarea_id" in (l.detalle or {}) and l.detalle.get("tarea_id") == str(tarea.id) for l in logs)


@pytest.mark.asyncio
async def test_delegar_tarea_cambia_asignado_a_y_por(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_docente = await _crear_usuario(db_session, tenant, "Docente")
    u_docente2 = await _crear_usuario(db_session, tenant, "Docente2")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_docente.id, descripcion="Original"), u_coord.id, COORD,
    )

    req = TareaDelegateRequest(asignado_a=u_docente2.id)
    updated = await svc.delegar_tarea(tarea.id, req, u_coord.id, COORD)

    assert updated.asignado_a == u_docente2.id
    assert updated.asignado_por == u_coord.id


@pytest.mark.asyncio
async def test_delegar_tarea_mismo_usuario_422(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_docente = await _crear_usuario(db_session, tenant, "Docente")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_docente.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = TareaDelegateRequest(asignado_a=u_docente.id)
    with pytest.raises(HTTPException) as exc_info:
        await svc.delegar_tarea(tarea.id, req, u_coord.id, COORD)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_delegar_tarea_profesor_403(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_docente = await _crear_usuario(db_session, tenant, "Docente")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = TareaDelegateRequest(asignado_a=u_docente.id)
    with pytest.raises(HTTPException) as exc_info:
        await svc.delegar_tarea(tarea.id, req, u_profe.id, PROFE)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_delegar_tarea_audit(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_docente = await _crear_usuario(db_session, tenant, "Docente")
    u_docente2 = await _crear_usuario(db_session, tenant, "Docente2")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_docente.id, descripcion="Deleg audit"), u_coord.id, COORD,
    )

    req = TareaDelegateRequest(asignado_a=u_docente2.id)
    await svc.delegar_tarea(tarea.id, req, u_coord.id, COORD)

    logs = await AuditLogRepository(db_session, tenant.id).list(accion="TAREA_ASIGNAR")
    assert any(l.detalle.get("asignado_anterior") == str(u_docente.id) for l in logs if l.detalle)


@pytest.mark.asyncio
async def test_cambiar_estado_pendiente_a_en_progreso(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO)
    updated = await svc.cambiar_estado(tarea.id, req, u_profe.id, PROFE)
    assert updated.estado == "En progreso"


@pytest.mark.asyncio
async def test_cambiar_estado_en_progreso_a_resuelta(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO), u_profe.id, PROFE)

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.RESUELTA)
    updated = await svc.cambiar_estado(tarea.id, req, u_profe.id, PROFE)
    assert updated.estado == "Resuelta"


@pytest.mark.asyncio
async def test_cambiar_estado_resuelta_a_en_progreso_coordinador(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO), u_profe.id, PROFE)
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.RESUELTA), u_profe.id, PROFE)

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO)
    updated = await svc.cambiar_estado(tarea.id, req, u_coord.id, COORD)
    assert updated.estado == "En progreso"


@pytest.mark.asyncio
async def test_cambiar_estado_resuelta_a_en_progreso_profesor_403(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO), u_profe.id, PROFE)
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.RESUELTA), u_profe.id, PROFE)

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO)
    with pytest.raises(HTTPException) as exc_info:
        await svc.cambiar_estado(tarea.id, req, u_profe.id, PROFE)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cambiar_estado_pendiente_a_cancelada_coordinador(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.CANCELADA)
    updated = await svc.cambiar_estado(tarea.id, req, u_coord.id, COORD)
    assert updated.estado == "Cancelada"


@pytest.mark.asyncio
async def test_cambiar_estado_pendiente_a_cancelada_profesor_403(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.CANCELADA)
    with pytest.raises(HTTPException) as exc_info:
        await svc.cambiar_estado(tarea.id, req, u_profe.id, PROFE)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cambiar_estado_transicion_invalida_422(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO), u_profe.id, PROFE)
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.RESUELTA), u_profe.id, PROFE)

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.PENDIENTE)
    with pytest.raises(HTTPException) as exc_info:
        await svc.cambiar_estado(tarea.id, req, u_coord.id, COORD)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_cambiar_estado_cancelada_inmutable(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.CANCELADA), u_coord.id, COORD)

    req = TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO)
    with pytest.raises(HTTPException) as exc_info:
        await svc.cambiar_estado(tarea.id, req, u_coord.id, COORD)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_cambiar_estado_audit(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Audit estado"), u_coord.id, COORD,
    )
    await svc.cambiar_estado(tarea.id, TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO), u_profe.id, PROFE)

    logs = await AuditLogRepository(db_session, tenant.id).list(accion="TAREA_ESTADO")
    assert any(
        l.detalle.get("estado_anterior") == "Pendiente" and l.detalle.get("estado_nuevo") == "En progreso"
        for l in logs if l.detalle
    )


@pytest.mark.asyncio
async def test_agregar_comentario_profesor_su_tarea(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = ComentarioCreateRequest(texto="Revisando el caso")
    c = await svc.agregar_comentario(tarea.id, req, u_profe.id, PROFE)
    assert c.autor_id == u_profe.id
    assert c.texto == "Revisando el caso"


@pytest.mark.asyncio
async def test_agregar_comentario_profesor_tarea_ajena_403(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    u_profe2 = await _crear_usuario(db_session, tenant, "Profe2")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = ComentarioCreateRequest(texto="Comentario ajeno")
    with pytest.raises(HTTPException) as exc_info:
        await svc.agregar_comentario(tarea.id, req, u_profe2.id, PROFE)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_agregar_comentario_coordinador_cualquiera(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Test"), u_coord.id, COORD,
    )

    req = ComentarioCreateRequest(texto="Coordinador comenta")
    c = await svc.agregar_comentario(tarea.id, req, u_coord.id, COORD)
    assert c.texto == "Coordinador comenta"


@pytest.mark.asyncio
async def test_agregar_comentario_audit(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Audit comment"), u_coord.id, COORD,
    )
    await svc.agregar_comentario(tarea.id, ComentarioCreateRequest(texto="Audit"), u_profe.id, PROFE)

    logs = await AuditLogRepository(db_session, tenant.id).list(accion="COMENTARIO_TAREA")
    assert any(l.detalle.get("tarea_id") == str(tarea.id) for l in logs if l.detalle)


@pytest.mark.asyncio
async def test_listar_tareas_scope_profesor(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    u_profe2 = await _crear_usuario(db_session, tenant, "Profe2")
    svc = _svc(db_session, tenant)

    await svc.crear_tarea(TareaCreateRequest(asignado_a=u_profe.id, descripcion="T1"), u_coord.id, COORD)
    await svc.crear_tarea(TareaCreateRequest(asignado_a=u_profe2.id, descripcion="T2"), u_coord.id, COORD)

    items, total = await svc.listar_tareas({}, u_profe.id, tenant.id, PROFE)
    assert total == 1
    assert items[0].asignado_a == u_profe.id


@pytest.mark.asyncio
async def test_listar_tareas_scope_coordinador(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    u_profe2 = await _crear_usuario(db_session, tenant, "Profe2")
    svc = _svc(db_session, tenant)

    await svc.crear_tarea(TareaCreateRequest(asignado_a=u_profe.id, descripcion="T1"), u_coord.id, COORD)
    await svc.crear_tarea(TareaCreateRequest(asignado_a=u_profe2.id, descripcion="T2"), u_coord.id, COORD)

    items, total = await svc.listar_tareas({}, u_coord.id, tenant.id, COORD)
    assert total == 2


@pytest.mark.asyncio
async def test_listar_tareas_filtros_combinados(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    await svc.crear_tarea(TareaCreateRequest(asignado_a=u_profe.id, descripcion="Urgente"), u_coord.id, COORD)
    t2 = await svc.crear_tarea(TareaCreateRequest(asignado_a=u_profe.id, descripcion="Normal"), u_coord.id, COORD)
    await svc.cambiar_estado(t2.id, TareaEstadoUpdateRequest(estado=EstadoTarea.EN_PROGRESO), u_profe.id, PROFE)

    items, total = await svc.listar_tareas(
        {"estado": "En progreso", "asignado_a": u_profe.id}, u_coord.id, tenant.id, COORD,
    )
    assert total == 1
    assert items[0].estado == "En progreso"


@pytest.mark.asyncio
async def test_get_tarea_con_comentarios(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Con comentarios"), u_coord.id, COORD,
    )
    await svc.agregar_comentario(tarea.id, ComentarioCreateRequest(texto="C1"), u_profe.id, PROFE)
    await svc.agregar_comentario(tarea.id, ComentarioCreateRequest(texto="C2"), u_coord.id, COORD)

    result = await svc.get_tarea(tarea.id, u_profe.id, tenant.id, PROFE)
    assert len(result.comentarios) == 2


@pytest.mark.asyncio
async def test_get_tarea_profesor_ajena_403(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    u_profe2 = await _crear_usuario(db_session, tenant, "Profe2")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Ajena"), u_coord.id, COORD,
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.get_tarea(tarea.id, u_profe2.id, tenant.id, PROFE)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_actualizar_descripcion_coordinador(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Original"), u_coord.id, COORD,
    )

    updated = await svc.actualizar_descripcion(
        tarea.id, TareaUpdateRequest(descripcion="Actualizada"), u_coord.id, COORD,
    )
    assert updated.descripcion == "Actualizada"


@pytest.mark.asyncio
async def test_actualizar_descripcion_profesor_403(db_session, tenant):
    u_coord = await _crear_usuario(db_session, tenant, "Coord")
    u_profe = await _crear_usuario(db_session, tenant, "Profe")
    svc = _svc(db_session, tenant)

    tarea = await svc.crear_tarea(
        TareaCreateRequest(asignado_a=u_profe.id, descripcion="Original"), u_coord.id, COORD,
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.actualizar_descripcion(
            tarea.id, TareaUpdateRequest(descripcion="Nueva"), u_profe.id, PROFE,
        )
    assert exc_info.value.status_code == 403
