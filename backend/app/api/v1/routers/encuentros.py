import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.encuentros import (
    EncuentroItemResponse,
    EncuentroListResponse,
    EncuentrosListResponse,
    HtmlResponse,
    InstanciaEncuentroResponse,
    InstanciaUnicaCreateRequest,
    InstanciaUpdateRequest,
    SlotEncuentroResponse,
    SlotRecurrenteCreateRequest,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/encuentros", tags=["encuentros"])


@router.get("", response_model=EncuentroListResponse)
async def listar_encuentros(
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    materia_id: uuid.UUID | None = Query(default=None),
    docente_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None, alias="q", description="Buscar por nombre de docente o título"),
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
):
    """Lista combinada de slots e instancias únicas para el frontend."""
    import sqlalchemy as sa
    from sqlalchemy.orm import selectinload

    from app.models.asignacion import Asignacion
    from app.models.instancia_encuentro import InstanciaEncuentro
    from app.models.materia import Materia
    from app.models.slot_encuentro import SlotEncuentro
    from app.models.usuario import Usuario
    from app.schemas.encuentros import EncuentroItemResponse

    limit = 20
    offset = (page - 1) * limit
    rows: list[dict] = []

    # ── Instancias únicas (sin slot) ──
    query_inst = (
        sa.select(
            InstanciaEncuentro.id,
            InstanciaEncuentro.materia_id,
            Materia.nombre.label("materia_nombre"),
            Asignacion.usuario_id.label("docente_id"),
            Usuario.nombre.label("docente_nombre"),
            InstanciaEncuentro.fecha,
            InstanciaEncuentro.hora,
            InstanciaEncuentro.titulo,
            InstanciaEncuentro.estado,
            InstanciaEncuentro.meet_url,
            InstanciaEncuentro.video_url,
            InstanciaEncuentro.comentario,
            InstanciaEncuentro.created_at,
            sa.literal(False).label("es_recurrente"),
        )
        .select_from(InstanciaEncuentro)
        .outerjoin(Materia, Materia.id == InstanciaEncuentro.materia_id)
        .outerjoin(Asignacion, Asignacion.id == InstanciaEncuentro.asignacion_id)
        .outerjoin(Usuario, Usuario.id == Asignacion.usuario_id)
        .where(
            InstanciaEncuentro.tenant_id == current_user.tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
            InstanciaEncuentro.slot_id.is_(None),
        )
    )
    if materia_id:
        query_inst = query_inst.where(InstanciaEncuentro.materia_id == materia_id)

    r = await db.execute(query_inst)
    for row in r.all():
        rows.append({
            "id": row[0], "materia_id": row[1], "materia_nombre": row[2] or "",
            "docente_id": row[3], "docente_nombre": row[4] or "",
            "fecha": row[5], "horario": row[6].strftime("%H:%M") if row[6] else "",
            "titulo": row[7], "estado": (row[8] or "programado").lower(),
            "enlace": row[9], "grabacion": row[10], "comentario": row[11],
            "created_at": row[12], "es_recurrente": False,
        })

    # ── Slots recurrentes ──
    q2 = (
        sa.select(
            SlotEncuentro.id,
            SlotEncuentro.materia_id,
            Materia.nombre.label("materia_nombre"),
            Asignacion.usuario_id.label("docente_id"),
            Usuario.nombre.label("docente_nombre"),
            SlotEncuentro.fecha_inicio.label("fecha"),
            SlotEncuentro.hora,
            SlotEncuentro.titulo,
            sa.literal("Programado").label("estado"),
            SlotEncuentro.meet_url,
            sa.literal(None).label("video_url"),
            sa.literal(None).label("comentario"),
            SlotEncuentro.created_at,
            sa.literal(True).label("es_recurrente"),
        )
        .select_from(SlotEncuentro)
        .outerjoin(Materia, Materia.id == SlotEncuentro.materia_id)
        .outerjoin(Asignacion, Asignacion.id == SlotEncuentro.asignacion_id)
        .outerjoin(Usuario, Usuario.id == Asignacion.usuario_id)
        .where(
            SlotEncuentro.tenant_id == current_user.tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        )
    )
    if materia_id:
        q2 = q2.where(SlotEncuentro.materia_id == materia_id)

    r2 = await db.execute(q2)
    for row in r2.all():
        rows.append({
            "id": row[0], "materia_id": row[1], "materia_nombre": row[2] or "",
            "docente_id": row[3], "docente_nombre": row[4] or "",
            "fecha": row[5], "horario": row[6].strftime("%H:%M") if row[6] else "",
            "titulo": row[7], "estado": "programado",
            "enlace": row[9], "grabacion": None, "comentario": None,
            "created_at": row[12], "es_recurrente": True,
        })

    # Apply post-query filters
    if docente_id:
        rows = [r for r in rows if r["docente_id"] == docente_id]
    if search:
        search_lower = search.lower()
        rows = [r for r in rows if search_lower in (r["docente_nombre"] or "").lower() or search_lower in (r["titulo"] or "").lower()]
    if fecha_desde:
        rows = [r for r in rows if r["fecha"] and r["fecha"] >= fecha_desde]
    if fecha_hasta:
        rows = [r for r in rows if r["fecha"] and r["fecha"] <= fecha_hasta]

    # Sort by fecha desc
    rows.sort(key=lambda r: r["fecha"] or date.min, reverse=True)

    total = len(rows)
    paged = rows[offset:offset + limit]
    return {
        "data": [EncuentroItemResponse(**r) for r in paged],
        "total": total,
        "page": page,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


def _build_audit_service(db: AsyncSession, tenant_id: uuid.UUID) -> AuditService:
    repo = AuditLogRepository(db, tenant_id)
    return AuditService(db, repo)


@router.post("/slots", response_model=SlotEncuentroResponse, status_code=201)
async def crear_slot_recurrente(
    body: SlotRecurrenteCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.models.asignacion import Asignacion
    from app.services.slot_service import SlotService

    # Normalize semanas → cant_semanas (frontend compat)
    if body.semanas:
        body.cant_semanas = body.semanas

    # Auto-resolve asignacion_id
    if not body.asignacion_id:
        # First try: user's own asignacion for this materia
        result = await db.execute(
            select(Asignacion.id).where(
                Asignacion.usuario_id == current_user.user_id,
                Asignacion.materia_id == body.materia_id,
                Asignacion.tenant_id == current_user.tenant_id,
                Asignacion.deleted_at.is_(None),
            ).limit(1)
        )
        row = result.first()

        # If not found and user is ADMIN/COORDINADOR, use any active asignacion
        if not row and ("ADMIN" in current_user.roles or "COORDINADOR" in current_user.roles):
            result = await db.execute(
                select(Asignacion.id).where(
                    Asignacion.materia_id == body.materia_id,
                    Asignacion.tenant_id == current_user.tenant_id,
                    Asignacion.deleted_at.is_(None),
                ).limit(1)
            )
            row = result.first()

        if row:
            body.asignacion_id = row[0]
        else:
            raise HTTPException(
                status_code=422,
                detail="No hay asignaciones vigentes para esta materia. Asigná un docente primero desde Equipos Docentes.",
            )

    svc = SlotService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    slot = await svc.crear_slot_recurrente(body, current_user.user_id, current_user.roles)
    await db.refresh(slot)
    return SlotEncuentroResponse.model_validate(slot)


@router.post("/instancias", response_model=InstanciaEncuentroResponse, status_code=201)
async def crear_instancia_unica(
    body: InstanciaUnicaCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.models.asignacion import Asignacion
    from app.services.encuentro_service import EncuentroService

    # Auto-resolve asignacion_id if not provided
    if not body.asignacion_id:
        # First try: user's own asignacion
        result = await db.execute(
            select(Asignacion.id).where(
                Asignacion.usuario_id == current_user.user_id,
                Asignacion.materia_id == body.materia_id,
                Asignacion.tenant_id == current_user.tenant_id,
                Asignacion.deleted_at.is_(None),
            ).limit(1)
        )
        row = result.first()

        # If not found and user is ADMIN/COORDINADOR, use any active asignacion
        if not row and ("ADMIN" in current_user.roles or "COORDINADOR" in current_user.roles):
            result = await db.execute(
                select(Asignacion.id).where(
                    Asignacion.materia_id == body.materia_id,
                    Asignacion.tenant_id == current_user.tenant_id,
                    Asignacion.deleted_at.is_(None),
                ).limit(1)
            )
            row = result.first()

        if row:
            body.asignacion_id = row[0]
        else:
            raise HTTPException(
                status_code=422,
                detail="No hay asignaciones vigentes para esta materia. Asigná un docente primero desde Equipos Docentes.",
            )

    svc = EncuentroService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        instancia = await svc.crear_instancia_unica(body, current_user.user_id)
        await db.refresh(instancia)
        return InstanciaEncuentroResponse.model_validate(instancia)
    except Exception as err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el encuentro: {err}") from err


@router.get("/slots", response_model=EncuentrosListResponse)
async def listar_slots(
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    import sqlalchemy as sa

    from app.models.instancia_encuentro import InstanciaEncuentro
    from app.services.slot_service import SlotService

    svc = SlotService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    slots, total = await svc.listar_slots(
        materia_id, current_user.user_id, current_user.tenant_id,
        current_user.roles, offset, limit,
    )

    for slot in slots:
        q = sa.select(InstanciaEncuentro).where(
            InstanciaEncuentro.slot_id == slot.id,
            InstanciaEncuentro.tenant_id == current_user.tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
        ).order_by(InstanciaEncuentro.fecha)
        result = await db.execute(q)
        instancias = result.scalars().all()
        slot.instancias = list(instancias)

    return EncuentrosListResponse(
        items=[SlotEncuentroResponse.model_validate(s) for s in slots],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/instancias", response_model=EncuentrosListResponse)
async def listar_instancias(
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    slot_id: uuid.UUID | None = Query(default=None),
    estado: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    from app.services.encuentro_service import EncuentroService

    svc = EncuentroService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    items, total = await svc.listar_instancias(
        materia_id, slot_id, estado,
        current_user.user_id, current_user.tenant_id, current_user.roles,
        offset, limit,
    )
    return EncuentrosListResponse(
        items=[InstanciaEncuentroResponse.model_validate(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.patch("/instancias/{instancia_id}", response_model=InstanciaEncuentroResponse)
async def editar_instancia(
    instancia_id: uuid.UUID,
    body: InstanciaUpdateRequest,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.encuentro_service import EncuentroService

    try:
        svc = EncuentroService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
        instancia = await svc.editar_instancia(
            instancia_id, body, current_user.user_id, current_user.roles,
        )
    except HTTPException:
        raise
    if instancia is None:
        raise HTTPException(status_code=404, detail="Instancia no encontrada")
    await db.refresh(instancia)
    return InstanciaEncuentroResponse.model_validate(instancia)


@router.get("/{materia_id}/contenido-aula")
async def get_contenido_aula(
    materia_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    """Genera contenido HTML del aula virtual para una materia (slots + instancias)."""
    from app.services.encuentro_service import EncuentroService

    svc = EncuentroService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    html = await svc.generar_html_materia(materia_id, current_user.tenant_id)
    if html is None:
        html = "<p>No hay encuentros programados para esta materia.</p>"
    return {"contenido": html}


@router.get("/slots/{slot_id}/html", response_model=HtmlResponse)
async def generar_html_slot(
    slot_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.encuentro_service import EncuentroService

    svc = EncuentroService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    html = await svc.generar_html_slot(slot_id, current_user.tenant_id)
    if html is None:
        raise HTTPException(status_code=404, detail="Slot no encontrado")
    return HtmlResponse(html=html)


@router.delete("/slots/{slot_id}", status_code=204)
async def eliminar_slot(
    slot_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.slot_service import SlotService

    svc = SlotService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    deleted = await svc.soft_delete_slot(
        slot_id, current_user.tenant_id, current_user.user_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Slot no encontrado")
