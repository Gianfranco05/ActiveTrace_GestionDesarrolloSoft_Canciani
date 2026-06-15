import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.tareas import (
    ComentarioCreateRequest,
    ComentarioTareaResponse,
    EstadoTarea,
    TareaCreateRequest,
    TareaDelegateRequest,
    TareaDetailResponse,
    TareaEstadoUpdateRequest,
    TareaHistorialResponse,
    TareaResponse,
    TareasListResponse,
    TareaUpdateRequest,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/tareas", tags=["tareas"])


def _build_audit_service(db: AsyncSession, tenant_id: uuid.UUID) -> AuditService:
    repo = AuditLogRepository(db, tenant_id)
    return AuditService(db, repo)


def _make_tarea_response(tarea) -> TareaResponse:
    # Extract titulo from first line of descripcion
    titulo = ""
    if tarea.descripcion:
        titulo = tarea.descripcion.split("\n")[0].strip()[:200]

    asignado_por_nombre = (
        f"{tarea.asignado_por_usuario.nombre} {tarea.asignado_por_usuario.apellidos}"
        if tarea.asignado_por_usuario else None
    )
    asignado_a_nombre = (
        f"{tarea.asignado_a_usuario.nombre} {tarea.asignado_a_usuario.apellidos}"
        if tarea.asignado_a_usuario else None
    )

    return TareaResponse(
        id=tarea.id,
        tenant_id=tarea.tenant_id,
        titulo=titulo,
        materia_id=tarea.materia_id,
        materia_nombre=tarea.materia.nombre if tarea.materia else None,
        asignado_a=tarea.asignado_a,
        asignado_a_nombre=asignado_a_nombre,
        docente_asignado_id=tarea.asignado_a,
        docente_asignado_nombre=asignado_a_nombre,
        asignado_por=tarea.asignado_por,
        asignado_por_nombre=asignado_por_nombre,
        asignador_nombre=asignado_por_nombre,
        estado=tarea.estado,
        descripcion=tarea.descripcion,
        contexto_id=tarea.contexto_id,
        comentarios_count=len(tarea.comentarios) if tarea.comentarios else 0,
        created_at=tarea.created_at,
        updated_at=tarea.updated_at,
    )


def _make_comentario_response(c) -> ComentarioTareaResponse:
    return ComentarioTareaResponse(
        id=c.id,
        tarea_id=c.tarea_id,
        autor_id=c.autor_id,
        autor_nombre=f"{c.autor.nombre} {c.autor.apellidos}" if c.autor else "",
        texto=c.texto,
        creado_at=c.creado_at,
    )


@router.post("", response_model=TareaResponse, status_code=201)
async def crear_tarea(
    body: TareaCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tarea_service import TareaService

    # Normalize: accept docente_asignado_id from frontend
    if body.docente_asignado_id and not body.asignado_a:
        body.asignado_a = body.docente_asignado_id

    # Combine titulo + descripcion + criterio_cierre into descripcion
    parts = []
    if body.titulo:
        parts.append(body.titulo)
    if body.descripcion:
        parts.append(body.descripcion)
    if body.criterio_cierre:
        parts.append(f"Criterio de cierre: {body.criterio_cierre}")
    body.descripcion = "\n\n".join(parts) if parts else "Sin descripción"

    svc = TareaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        tarea = await svc.crear_tarea(body, current_user.user_id, current_user.roles)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail="Error al crear la tarea") from err

    # Re-query with eager-loaded relationships to avoid MissingGreenlet
    from sqlalchemy import select as sa_select
    from sqlalchemy.orm import selectinload
    from app.models.tarea import Tarea

    query = (
        sa_select(Tarea)
        .options(
            selectinload(Tarea.asignado_a_usuario),
            selectinload(Tarea.asignado_por_usuario),
            selectinload(Tarea.materia),
            selectinload(Tarea.comentarios),
        )
        .where(Tarea.id == tarea.id)
    )
    result = await db.execute(query)
    tarea = result.scalar_one()
    return _make_tarea_response(tarea)


@router.get("", response_model=TareasListResponse)
async def listar_tareas(
    current_user: UserSession = Depends(require_permission_return_user("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
    asignado_a: uuid.UUID | None = Query(default=None),
    asignado_por: uuid.UUID | None = Query(default=None),
    materia_id: uuid.UUID | None = Query(default=None),
    estado: EstadoTarea | None = Query(default=None),
    contexto_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    from app.services.tarea_service import TareaService

    svc = TareaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    filtros = {
        "asignado_a": asignado_a,
        "asignado_por": asignado_por,
        "materia_id": materia_id,
        "estado": estado.value if estado else None,
        "contexto_id": contexto_id,
        "q": q,
        "offset": offset,
        "limit": limit,
    }
    items, total = await svc.listar_tareas(
        filtros, current_user.user_id, current_user.tenant_id, current_user.roles,
    )

    responses = [_make_tarea_response(t) for t in items]
    return TareasListResponse(items=responses, total=total, offset=offset, limit=limit)


@router.get("/{tarea_id}", response_model=TareaDetailResponse)
async def get_tarea(
    tarea_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tarea_service import TareaService

    svc = TareaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        tarea = await svc.get_tarea(tarea_id, current_user.user_id, current_user.tenant_id, current_user.roles)
    except HTTPException:
        raise

    base = _make_tarea_response(tarea)
    comentarios = [_make_comentario_response(c) for c in (tarea.comentarios or [])]
    return TareaDetailResponse(
        **base.model_dump(),
        comentarios=comentarios,
    )


@router.patch("/{tarea_id}", response_model=TareaResponse)
async def actualizar_tarea(
    tarea_id: uuid.UUID,
    body: TareaDelegateRequest | TareaEstadoUpdateRequest | TareaUpdateRequest,
    current_user: UserSession = Depends(require_permission_return_user("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tarea_service import TareaService

    svc = TareaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        if isinstance(body, TareaDelegateRequest):
            tarea = await svc.delegar_tarea(tarea_id, body, current_user.user_id, current_user.roles)
        elif isinstance(body, TareaEstadoUpdateRequest):
            tarea = await svc.cambiar_estado(tarea_id, body, current_user.user_id, current_user.roles)
        elif isinstance(body, TareaUpdateRequest):
            tarea = await svc.actualizar_descripcion(tarea_id, body, current_user.user_id, current_user.roles)
        else:
            raise HTTPException(status_code=422, detail="Cuerpo de petición no reconocido")
    except HTTPException:
        raise
    # Re-query with eager loads to avoid MissingGreenlet (audit_repo.create commits the session,
    # expiring the tarea — a simple refresh() breaks in async context after that second commit)
    from sqlalchemy import select as sa_select
    from sqlalchemy.orm import selectinload
    from app.models.tarea import Tarea

    query = (
        sa_select(Tarea)
        .options(
            selectinload(Tarea.asignado_a_usuario),
            selectinload(Tarea.asignado_por_usuario),
            selectinload(Tarea.materia),
            selectinload(Tarea.comentarios),
        )
        .where(Tarea.id == tarea.id)
    )
    result = await db.execute(query)
    tarea = result.scalar_one()
    return _make_tarea_response(tarea)


@router.get("/{tarea_id}/comentarios", response_model=list[ComentarioTareaResponse])
async def get_comentarios(
    tarea_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tarea_service import TareaService

    svc = TareaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    tarea = await svc._repo.get_by_id(tarea_id, current_user.tenant_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    await db.refresh(tarea, ["comentarios"])
    return [_make_comentario_response(c) for c in (tarea.comentarios or [])]


@router.post("/{tarea_id}/comentarios", response_model=ComentarioTareaResponse, status_code=201)
async def agregar_comentario(
    tarea_id: uuid.UUID,
    body: ComentarioCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tarea_service import TareaService

    # Normalize: accept contenido from frontend
    if body.contenido and not body.texto:
        body.texto = body.contenido

    svc = TareaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        comentario = await svc.agregar_comentario(tarea_id, body, current_user.user_id, current_user.roles)
    except HTTPException:
        raise
    return _make_comentario_response(comentario)


@router.get("/{tarea_id}/historial", response_model=list[TareaHistorialResponse])
async def get_historial(
    tarea_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("tareas:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tarea_service import TareaService

    svc = TareaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    return await svc.get_historial(tarea_id)
