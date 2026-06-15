import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.comentario_tarea import ComentarioTarea
from app.models.tarea import Tarea
from app.repositories.comentario_tarea_repository import ComentarioTareaRepository
from app.repositories.tarea_repository import TareaRepository
from app.schemas.tareas import (
    ComentarioCreateRequest,
    EstadoTarea,
    TareaCreateRequest,
    TareaDelegateRequest,
    TareaEstadoUpdateRequest,
    TareaHistorialResponse,
    TareaUpdateRequest,
)
from app.services.audit_service import AuditService

ESTADO_TRANSICIONES = {
    EstadoTarea.PENDIENTE: [EstadoTarea.EN_PROGRESO, EstadoTarea.CANCELADA],
    EstadoTarea.EN_PROGRESO: [EstadoTarea.RESUELTA, EstadoTarea.CANCELADA],
    EstadoTarea.RESUELTA: [EstadoTarea.EN_PROGRESO],
    EstadoTarea.CANCELADA: [],
}


def _tiene_rol(roles: list[str], *nombres: str) -> bool:
    return any(n in roles for n in nombres)


def _solo_scope_propio(roles: list[str]) -> bool:
    return not _tiene_rol(roles, "COORDINADOR", "ADMIN")


class TareaService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        audit_service: AuditService,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._repo = TareaRepository(session, tenant_id)
        self._comentario_repo = ComentarioTareaRepository(session, tenant_id)
        self._audit = audit_service

    async def crear_tarea(
        self,
        request: TareaCreateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> Tarea:
        from fastapi import HTTPException

        if not _tiene_rol(roles, "COORDINADOR", "ADMIN"):
            raise HTTPException(status_code=403, detail="Solo COORDINADOR y ADMIN pueden crear tareas")

        tarea = Tarea(
            tenant_id=self._tenant_id,
            materia_id=request.materia_id,
            asignado_a=request.asignado_a,
            asignado_por=actor_id,
            descripcion=request.descripcion,
            contexto_id=request.contexto_id,
            estado=EstadoTarea.PENDIENTE.value,
        )
        await self._repo.create(tarea)
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.TAREA_CREAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "tarea_id": str(tarea.id),
                "asignado_a": str(request.asignado_a),
            },
        )
        return tarea

    async def delegar_tarea(
        self,
        tarea_id: uuid.UUID,
        request: TareaDelegateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> Tarea:
        from fastapi import HTTPException

        if not _tiene_rol(roles, "COORDINADOR", "ADMIN"):
            raise HTTPException(status_code=403, detail="Solo COORDINADOR y ADMIN pueden delegar tareas")

        tarea = await self._repo.get_for_update(tarea_id, self._tenant_id)
        if tarea is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        if tarea.asignado_a == request.asignado_a:
            raise HTTPException(
                status_code=422,
                detail="La tarea ya está asignada a este usuario",
            )

        anterior = tarea.asignado_a
        tarea.asignado_a = request.asignado_a
        tarea.asignado_por = actor_id
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.TAREA_ASIGNAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "tarea_id": str(tarea_id),
                "asignado_anterior": str(anterior),
                "asignado_nuevo": str(request.asignado_a),
            },
        )
        return tarea

    async def cambiar_estado(
        self,
        tarea_id: uuid.UUID,
        request: TareaEstadoUpdateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> Tarea:
        from fastapi import HTTPException

        tarea = await self._repo.get_for_update(tarea_id, self._tenant_id)
        if tarea is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        estado_actual = EstadoTarea(tarea.estado)
        nuevo = request.estado

        if estado_actual == EstadoTarea.CANCELADA:
            raise HTTPException(
                status_code=422,
                detail="Una tarea cancelada no puede cambiar de estado",
            )

        # Only COORD/ADMIN can cancel or reopen
        if nuevo == EstadoTarea.CANCELADA:
            if not _tiene_rol(roles, "COORDINADOR", "ADMIN"):
                raise HTTPException(status_code=403, detail="Solo COORDINADOR y ADMIN pueden cancelar tareas")
        if estado_actual == EstadoTarea.RESUELTA and nuevo == EstadoTarea.EN_PROGRESO:
            if not _tiene_rol(roles, "COORDINADOR", "ADMIN"):
                raise HTTPException(status_code=403, detail="Solo COORDINADOR y ADMIN pueden reabrir tareas")

        # PROFESOR/TUTOR: only their own tasks
        if _solo_scope_propio(roles) and tarea.asignado_a != actor_id:
            raise HTTPException(status_code=403, detail="No puedes cambiar el estado de esta tarea")

        validos = ESTADO_TRANSICIONES.get(estado_actual, [])
        if nuevo not in validos:
            raise HTTPException(
                status_code=422,
                detail=f"Transición inválida. Desde {estado_actual.value} solo se puede pasar a: {[v.value for v in validos]}",
            )

        anterior = tarea.estado
        tarea.estado = nuevo.value
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.TAREA_ESTADO,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "tarea_id": str(tarea_id),
                "estado_anterior": anterior,
                "estado_nuevo": nuevo.value,
            },
        )
        return tarea

    async def actualizar_descripcion(
        self,
        tarea_id: uuid.UUID,
        request: TareaUpdateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> Tarea:
        from fastapi import HTTPException

        if not _tiene_rol(roles, "COORDINADOR", "ADMIN"):
            raise HTTPException(status_code=403, detail="Solo COORDINADOR y ADMIN pueden actualizar la descripción")

        tarea = await self._repo.update(
            tarea_id, self._tenant_id, descripcion=request.descripcion,
        )
        if tarea is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        await self._session.commit()
        return tarea

    async def agregar_comentario(
        self,
        tarea_id: uuid.UUID,
        request: ComentarioCreateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> ComentarioTarea:
        from fastapi import HTTPException

        tarea = await self._repo.get_by_id(tarea_id, self._tenant_id)
        if tarea is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        if _solo_scope_propio(roles) and tarea.asignado_a != actor_id:
            raise HTTPException(status_code=403, detail="No puedes comentar en esta tarea")

        comentario = ComentarioTarea(
            tenant_id=self._tenant_id,
            tarea_id=tarea_id,
            autor_id=actor_id,
            texto=request.texto,
        )
        await self._comentario_repo.create(comentario)
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.COMENTARIO_TAREA,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "tarea_id": str(tarea_id),
                "comentario_id": str(comentario.id),
            },
        )
        return comentario

    async def listar_tareas(
        self,
        filtros: dict,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        roles: list[str],
    ) -> tuple[list[Tarea], int]:
        asignado_a_filtro = filtros.get("asignado_a")
        if _solo_scope_propio(roles):
            asignado_a_filtro = actor_id

        return await self._repo.list_by_filters(
            tenant_id,
            asignado_a=asignado_a_filtro,
            asignado_por=filtros.get("asignado_por"),
            materia_id=filtros.get("materia_id"),
            estado=filtros.get("estado"),
            contexto_id=filtros.get("contexto_id"),
            q=filtros.get("q"),
            offset=filtros.get("offset", 0),
            limit=filtros.get("limit", 20),
        )

    async def get_historial(
        self,
        tarea_id: uuid.UUID,
    ) -> list[TareaHistorialResponse]:
        from app.models.audit_log import AuditLog
        from app.models.auth_user import AuthUser
        from app.models.usuario import Usuario
        from sqlalchemy import select, cast, String

        query = (
            select(
                AuditLog.id,
                AuditLog.detalle["tarea_id"].as_string().label("detalle_tarea_id"),
                AuditLog.detalle["estado_anterior"].as_string().label("detalle_estado_anterior"),
                AuditLog.detalle["estado_nuevo"].as_string().label("detalle_estado_nuevo"),
                AuditLog.actor_id,
                (Usuario.nombre + " " + Usuario.apellidos).label("usuario_nombre"),
                AuditLog.created_at,
            )
            .select_from(AuditLog)
            .outerjoin(AuthUser, AuditLog.actor_id == AuthUser.id)
            .outerjoin(Usuario, (AuthUser.id == Usuario.id) & (Usuario.deleted_at.is_(None)))
            .where(
                AuditLog.tenant_id == self._tenant_id,
                AuditLog.accion == "TAREA_ESTADO",
                AuditLog.detalle["tarea_id"].as_string() == str(tarea_id),
            )
            .order_by(AuditLog.created_at.desc())
        )
        result = await self._session.execute(query)
        rows = result.all()
        return [
            TareaHistorialResponse(
                id=row.id,
                tarea_id=uuid.UUID(str(row.detalle_tarea_id).strip('"')),
                estado_anterior=str(row.detalle_estado_anterior).strip('"'),
                estado_nuevo=str(row.detalle_estado_nuevo).strip('"'),
                usuario_id=row.actor_id,
                usuario_nombre=row.usuario_nombre or "",
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def get_tarea(
        self,
        tarea_id: uuid.UUID,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        roles: list[str],
    ) -> Tarea:
        from fastapi import HTTPException

        tarea = await self._repo.get_by_id(tarea_id, tenant_id)
        if tarea is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        if _solo_scope_propio(roles) and tarea.asignado_a != actor_id:
            raise HTTPException(status_code=403, detail="No puedes ver esta tarea")

        return tarea
