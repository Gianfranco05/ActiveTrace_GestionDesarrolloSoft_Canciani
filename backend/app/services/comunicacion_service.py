import hashlib
import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.comunicacion import EstadoComunicacion
from app.models.padron import EntradaPadron
from app.models.tenant import Tenant
from app.repositories.audit_repository import AuditLogRepository
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.services.audit_service import AuditService
from app.services.template_engine import TemplateVariables, render_template

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    EstadoComunicacion.PENDIENTE.value: [
        EstadoComunicacion.ENVIANDO.value,
        EstadoComunicacion.CANCELADO.value,
    ],
    EstadoComunicacion.ENVIANDO.value: [
        EstadoComunicacion.ENVIADO.value,
        EstadoComunicacion.ERROR.value,
    ],
    EstadoComunicacion.ENVIADO.value: [],
    EstadoComunicacion.ERROR.value: [],
    EstadoComunicacion.CANCELADO.value: [],
}


class InvalidStateTransitionError(ValueError):
    pass


class ComunicacionService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        current_user_id: uuid.UUID,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._current_user_id = current_user_id
        self._repo = ComunicacionRepository(session, tenant_id)
        self._audit = AuditService(
            session,
            AuditLogRepository(session, tenant_id),
        )

    @staticmethod
    def validate_transition(current: str, target: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise InvalidStateTransitionError(
                f"Invalid transition: {current} -> {target}",
            )

    def _make_preview_token(self, materia_id: uuid.UUID, timestamp: datetime) -> str:
        raw = f"{self._tenant_id}:{materia_id}:{timestamp.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _validate_preview_token(
        self, token: str, materia_id: uuid.UUID, token_timestamp: datetime,
    ) -> None:
        expected = self._make_preview_token(materia_id, token_timestamp)
        if token != expected:
            raise HTTPException(status_code=400, detail="Preview required before enqueue")
        delta = (datetime.now(UTC) - token_timestamp).total_seconds()
        if delta > 900:
            raise HTTPException(status_code=400, detail="Preview token expired")

    async def _check_tenant_aprobacion_flag(self) -> bool:
        result = await self._session.execute(
            select(Tenant).where(Tenant.id == self._tenant_id),
        )
        t = result.scalar_one_or_none()
        if t is not None:
            await self._session.refresh(t)
        return bool(t.requiere_aprobacion_comunicaciones) if t else False

    async def preview(
        self,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        template_body: str,
        template_asunto: str,
    ) -> dict:
        result = await self._session.execute(
            select(EntradaPadron).where(
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            ),
        )
        all_entries = result.scalars().all()

        if not all_entries:
            raise HTTPException(status_code=400, detail="No recipients found")

        total = len(all_entries)
        sample = [
            {
                "nombre": e.nombre,
                "apellidos": e.apellidos,
                "email": e.email,
                "asunto": render_template(
                    template_asunto,
                    TemplateVariables(nombre=e.nombre, apellidos=e.apellidos),
                ),
                "cuerpo": render_template(
                    template_body,
                    TemplateVariables(nombre=e.nombre, apellidos=e.apellidos),
                ),
            }
            for e in all_entries[:5]
        ]

        ts = datetime.now(UTC)
        preview_token = self._make_preview_token(materia_id, ts)

        await self._audit.log(
            accion=AuditAction.COMUNICACION_PREVIEW,
            actor_id=self._current_user_id,
            tenant_id=self._tenant_id,
            detalle={
                "materia_id": str(materia_id),
                "cohorte_id": str(cohorte_id),
                "total_estimado": total,
            },
        )

        return {
            "sample": sample,
            "total_estimado": total,
            "preview_token": preview_token,
            "preview_token_timestamp": ts.isoformat(),
        }

    async def enqueue(
        self,
        preview_token: str,
        preview_token_timestamp: str,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        template_body: str,
        template_asunto: str,
        template_id: uuid.UUID | None = None,
    ) -> dict:
        token_ts = datetime.fromisoformat(preview_token_timestamp)
        self._validate_preview_token(preview_token, materia_id, token_ts)

        requiere_aprobacion = await self._check_tenant_aprobacion_flag()
        lote_id = uuid.uuid4()

        result = await self._session.execute(
            select(EntradaPadron).where(
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            ),
        )
        entries = result.scalars().all()

        if not entries:
            raise HTTPException(status_code=400, detail="No recipients found")

        created = 0
        for entry in entries:
            vars = TemplateVariables(
                nombre=entry.nombre or "",
                apellidos=entry.apellidos or "",
                email=entry.email or "",
            )
            rendered_asunto = render_template(template_asunto, vars)
            rendered_cuerpo = render_template(template_body, vars)

            await self._repo.create({
                "lote_id": lote_id,
                "enviado_por": self._current_user_id,
                "materia_id": materia_id,
                "entrada_padron_id": entry.id,
                "destinatario": entry.email or "",
                "asunto": rendered_asunto,
                "cuerpo": rendered_cuerpo,
                "template_id": template_id,
                "variables": vars.model_dump(exclude_none=True),
                "estado": EstadoComunicacion.PENDIENTE.value,
                "requiere_aprobacion": requiere_aprobacion,
            })
            created += 1

        await self._audit.log(
            accion=AuditAction.COMUNICACION_ENVIAR,
            actor_id=self._current_user_id,
            tenant_id=self._tenant_id,
            detalle={
                "lote_id": str(lote_id),
                "materia_id": str(materia_id),
                "total_creados": created,
            },
            filas_afectadas=created,
        )

        return {"lote_id": str(lote_id), "creados": created}

    async def approve(
        self, lote_id: uuid.UUID | None = None, comunicacion_id: uuid.UUID | None = None,
    ) -> dict:
        if lote_id:
            count = await self._repo.bulk_set_aprobado(lote_id, self._current_user_id)
            if count == 0:
                existing = await self._repo.list_by_lote(lote_id)
                if not existing:
                    raise HTTPException(status_code=404, detail="Lote not found")
        elif comunicacion_id:
            c = await self._repo.get_by_id(comunicacion_id)
            if c is None:
                raise HTTPException(status_code=404, detail="Comunicacion not found")
            if c.aprobado_por is not None:
                count = 0
            else:
                c.aprobado_por = self._current_user_id
                c.aprobado_at = datetime.now(UTC)
                await self._session.commit()
                count = 1
        else:
            raise HTTPException(status_code=400, detail="lote_id or comunicacion_id required")

        await self._audit.log(
            accion=AuditAction.COMUNICACION_APROBAR,
            actor_id=self._current_user_id,
            tenant_id=self._tenant_id,
            detalle={
                "lote_id": str(lote_id) if lote_id else None,
                "comunicacion_id": str(comunicacion_id) if comunicacion_id else None,
                "aprobados": count,
            },
            filas_afectadas=count,
        )

        return {"aprobados": count}

    async def cancel(
        self, lote_id: uuid.UUID | None = None, comunicacion_id: uuid.UUID | None = None,
    ) -> dict:
        count = 0
        if lote_id:
            count = await self._repo.bulk_cancel_by_lote(lote_id)
            if count == 0:
                existing = await self._repo.list_by_lote(lote_id)
                if not existing:
                    raise HTTPException(status_code=404, detail="Lote not found")
        elif comunicacion_id:
            c = await self._repo.get_by_id(comunicacion_id)
            if c is None:
                raise HTTPException(status_code=404, detail="Comunicacion not found")
            if c.estado != EstadoComunicacion.PENDIENTE.value:
                count = 0
            else:
                c.estado = EstadoComunicacion.CANCELADO.value
                await self._session.commit()
                count = 1
        else:
            raise HTTPException(status_code=400, detail="lote_id or comunicacion_id required")

        await self._audit.log(
            accion=AuditAction.COMUNICACION_CANCELAR,
            actor_id=self._current_user_id,
            tenant_id=self._tenant_id,
            detalle={
                "lote_id": str(lote_id) if lote_id else None,
                "comunicacion_id": str(comunicacion_id) if comunicacion_id else None,
                "cancelados": count,
            },
            filas_afectadas=count,
        )

        return {"cancelados": count}
