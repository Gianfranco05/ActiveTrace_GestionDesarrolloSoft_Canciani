import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_aware import get_tenant_scoped
from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.aviso import Aviso
from app.repositories.base import BaseRepository


class AvisoRepository(BaseRepository[Aviso]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        super().__init__(session, tenant_id, Aviso)

    async def create_aviso(self, aviso_data: dict) -> Aviso:
        return await self.create(aviso_data)

    async def get_by_id(self, aviso_id: uuid.UUID) -> Aviso | None:
        return await self.get(aviso_id)

    async def update_aviso(self, aviso_id: uuid.UUID, data: dict) -> Aviso | None:
        return await self.update(aviso_id, data)

    async def soft_delete_aviso(self, aviso_id: uuid.UUID) -> bool:
        return await self.soft_delete(aviso_id)

    async def list_visibles(
        self,
        usuario_id: uuid.UUID,
        offset: int,
        limit: int,
        activo: bool | None = None,
        alcance: str | None = None,
        busqueda: str | None = None,
        admin: bool = False,
    ) -> tuple[list[Aviso], int]:
        now = datetime.now(UTC)

        conditions = [Aviso.tenant_id == self._tenant_id, Aviso.deleted_at.is_(None)]

        if activo is not None:
            conditions.append(Aviso.activo.is_(activo))
        elif not admin:
            conditions.extend([Aviso.activo.is_(True), Aviso.inicio_en <= now, Aviso.fin_en >= now])

        if alcance:
            conditions.append(Aviso.alcance == alcance)
        if busqueda:
            conditions.append(Aviso.titulo.ilike(f"%{busqueda}%"))

        base_query = select(Aviso).where(and_(*conditions))

        if admin:
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await self._session.execute(count_query)
            total = count_result.scalar_one()

            paged_query = base_query.order_by(
                Aviso.orden.desc(),
                Aviso.inicio_en.desc(),
            ).offset(offset).limit(limit)

            result = await self._session.execute(paged_query)
            items = list(result.scalars().all())

            return items, total

        from app.models.asignacion import Asignacion as AsignacionModel
        from app.models.rol import Rol

        materia_ids_sub = (
            select(AsignacionModel.materia_id)
            .where(
                AsignacionModel.usuario_id == usuario_id,
                AsignacionModel.tenant_id == self._tenant_id,
                AsignacionModel.deleted_at.is_(None),
                AsignacionModel.materia_id.isnot(None),
                AsignacionModel.vig_desde <= func.current_date(),
                or_(
                    AsignacionModel.vig_hasta.is_(None),
                    AsignacionModel.vig_hasta >= func.current_date(),
                ),
            )
            .distinct()
            .scalar_subquery()
        )

        cohorte_ids_sub = (
            select(AsignacionModel.cohorte_id)
            .where(
                AsignacionModel.usuario_id == usuario_id,
                AsignacionModel.tenant_id == self._tenant_id,
                AsignacionModel.deleted_at.is_(None),
                AsignacionModel.cohorte_id.isnot(None),
                AsignacionModel.vig_desde <= func.current_date(),
                or_(
                    AsignacionModel.vig_hasta.is_(None),
                    AsignacionModel.vig_hasta >= func.current_date(),
                ),
            )
            .distinct()
            .scalar_subquery()
        )

        rol_nombres_sub = (
            select(Rol.nombre)
            .select_from(AsignacionModel)
            .join(Rol, AsignacionModel.rol_id == Rol.id)
            .where(
                AsignacionModel.usuario_id == usuario_id,
                AsignacionModel.tenant_id == self._tenant_id,
                AsignacionModel.deleted_at.is_(None),
                AsignacionModel.vig_desde <= func.current_date(),
                or_(
                    AsignacionModel.vig_hasta.is_(None),
                    AsignacionModel.vig_hasta >= func.current_date(),
                ),
            )
            .distinct()
            .scalar_subquery()
        )

        visibility_filter = or_(
            Aviso.alcance == "Global",
            and_(
                Aviso.alcance == "PorMateria",
                Aviso.materia_id.in_(materia_ids_sub),
            ),
            and_(
                Aviso.alcance == "PorCohorte",
                Aviso.cohorte_id.in_(cohorte_ids_sub),
            ),
            and_(
                Aviso.alcance == "PorRol",
                Aviso.rol_destino.in_(rol_nombres_sub),
            ),
        )

        ack_sub = (
            select(AcknowledgmentAviso.id)
            .where(
                AcknowledgmentAviso.aviso_id == Aviso.id,
                AcknowledgmentAviso.usuario_id == usuario_id,
            )
            .correlate(Aviso)
            .scalar_subquery()
        )

        exclude_ack = ~and_(
            Aviso.requiere_ack.is_(True),
            exists(ack_sub),
        )

        visible_query = base_query.where(visibility_filter).where(exclude_ack)

        count_query = select(func.count()).select_from(visible_query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        paged_query = visible_query.order_by(
            Aviso.orden.desc(),
            Aviso.inicio_en.desc(),
        ).offset(offset).limit(limit)

        result = await self._session.execute(paged_query)
        items = list(result.scalars().all())

        return items, total

    async def is_visible_by_scope(
        self, aviso_id: uuid.UUID, usuario_id: uuid.UUID,
    ) -> bool:
        """Check if aviso is visible to user by scope and vigencia, ignoring ack status."""
        now = datetime.now(UTC)

        from app.models.asignacion import Asignacion as AsignacionModel
        from app.models.rol import Rol

        aviso = await get_tenant_scoped(self._session, Aviso, aviso_id, self._tenant_id)
        if aviso is None or aviso.deleted_at is not None:
            return False
        if aviso.tenant_id != self._tenant_id:
            return False
        if not aviso.activo:
            return False
        if aviso.inicio_en > now or aviso.fin_en < now:
            return False

        if aviso.alcance == "Global":
            return True

        materia_ids_sub = (
            select(AsignacionModel.materia_id)
            .where(
                AsignacionModel.usuario_id == usuario_id,
                AsignacionModel.tenant_id == self._tenant_id,
                AsignacionModel.deleted_at.is_(None),
                AsignacionModel.materia_id.isnot(None),
                AsignacionModel.vig_desde <= func.current_date(),
                or_(
                    AsignacionModel.vig_hasta.is_(None),
                    AsignacionModel.vig_hasta >= func.current_date(),
                ),
            )
            .distinct()
            .scalar_subquery()
        )

        if aviso.alcance == "PorMateria":
            result = await self._session.execute(
                select(func.count()).where(
                    Aviso.materia_id == aviso.materia_id,
                    Aviso.materia_id.in_(materia_ids_sub),
                ),
            )
            return result.scalar_one() > 0

        cohorte_ids_sub = (
            select(AsignacionModel.cohorte_id)
            .where(
                AsignacionModel.usuario_id == usuario_id,
                AsignacionModel.tenant_id == self._tenant_id,
                AsignacionModel.deleted_at.is_(None),
                AsignacionModel.cohorte_id.isnot(None),
                AsignacionModel.vig_desde <= func.current_date(),
                or_(
                    AsignacionModel.vig_hasta.is_(None),
                    AsignacionModel.vig_hasta >= func.current_date(),
                ),
            )
            .distinct()
            .scalar_subquery()
        )

        if aviso.alcance == "PorCohorte":
            result = await self._session.execute(
                select(func.count()).where(
                    Aviso.cohorte_id == aviso.cohorte_id,
                    Aviso.cohorte_id.in_(cohorte_ids_sub),
                ),
            )
            return result.scalar_one() > 0

        if aviso.alcance == "PorRol":
            rol_nombres_sub = (
                select(Rol.nombre)
                .select_from(AsignacionModel)
                .join(Rol, AsignacionModel.rol_id == Rol.id)
                .where(
                    AsignacionModel.usuario_id == usuario_id,
                    AsignacionModel.tenant_id == self._tenant_id,
                    AsignacionModel.deleted_at.is_(None),
                    AsignacionModel.vig_desde <= func.current_date(),
                    or_(
                        AsignacionModel.vig_hasta.is_(None),
                        AsignacionModel.vig_hasta >= func.current_date(),
                    ),
                )
                .distinct()
                .scalar_subquery()
            )
            result = await self._session.execute(
                select(func.count()).where(
                    Aviso.rol_destino == aviso.rol_destino,
                    Aviso.rol_destino.in_(rol_nombres_sub),
                ),
            )
            return result.scalar_one() > 0

        return False

    async def get_ack(
        self, aviso_id: uuid.UUID, usuario_id: uuid.UUID,
    ) -> AcknowledgmentAviso | None:
        query = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.usuario_id == usuario_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create_ack(
        self, ack: AcknowledgmentAviso,
    ) -> AcknowledgmentAviso | None:
        import uuid as uuid_mod

        from sqlalchemy.exc import IntegrityError

        ack.id = uuid_mod.uuid4()
        self._session.add(ack)
        try:
            await self._session.commit()
            return await self.get_ack(ack.aviso_id, ack.usuario_id)
        except IntegrityError:
            await self._session.rollback()
            return None

    async def count_acks(self, aviso_id: uuid.UUID) -> int:
        query = select(func.count()).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_distinct_users(self, aviso_id: uuid.UUID) -> int:
        query = select(
            func.count(func.distinct(AcknowledgmentAviso.usuario_id)),
        ).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def get_aviso_detail(
        self, aviso_id: uuid.UUID,
    ) -> Aviso | None:
        query = select(Aviso).where(
            Aviso.id == aviso_id,
            Aviso.tenant_id == self._tenant_id,
            Aviso.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_acks(
        self, aviso_id: uuid.UUID,
    ) -> list[dict]:
        from app.models.usuario import Usuario

        query = (
            select(
                AcknowledgmentAviso.id,
                AcknowledgmentAviso.aviso_id,
                AcknowledgmentAviso.usuario_id,
                (Usuario.nombre + " " + Usuario.apellidos).label("usuario_nombre"),
                AcknowledgmentAviso.confirmado_at,
            )
            .select_from(AcknowledgmentAviso)
            .outerjoin(
                Usuario,
                (AcknowledgmentAviso.usuario_id == Usuario.id) & (Usuario.deleted_at.is_(None)),
            )
            .where(AcknowledgmentAviso.aviso_id == aviso_id)
            .order_by(AcknowledgmentAviso.confirmado_at.desc())
        )
        result = await self._session.execute(query)
        return [
            {
                "id": row.id,
                "aviso_id": row.aviso_id,
                "usuario_id": row.usuario_id,
                "usuario_nombre": row.usuario_nombre or "",
                "confirmado": True,
                "confirmado_at": row.confirmado_at,
            }
            for row in result.all()
        ]
