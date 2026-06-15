"""Liquidacion service — calculation engine, close, segmentation, export."""

import csv
import io
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.asignacion import Asignacion
from app.models.audit_log import AuditLog
from app.models.liquidacion import Liquidacion
from app.models.materia import Materia
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.repositories.salario_repository import (
    GrupoMateriaRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)


class LiquidacionCerradaError(Exception):
    pass


class LiquidacionNotFoundError(Exception):
    pass


class LiquidacionService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self._db = db
        self._tenant_id = tenant_id
        self._salario_base_repo = SalarioBaseRepository(db, tenant_id)
        self._salario_plus_repo = SalarioPlusRepository(db, tenant_id)
        self._grupo_materia_repo = GrupoMateriaRepository(db, tenant_id)
        self._liq_repo = LiquidacionRepository(db, tenant_id)

    @staticmethod
    def _parse_periodo(periodo: str) -> tuple[date, date]:
        year, month = int(periodo[:4]), int(periodo[5:7])
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return date(year, month, 1), date(next_year, next_month, 1)

    async def calcular_liquidacion(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> dict:
        existing = await self._liq_repo.get_by_cohorte_periodo(
            cohorte_id, periodo
        )
        if existing and any(liq.estado == "Cerrada" for liq in existing):
            raise LiquidacionCerradaError("Cannot recalculate closed liquidation")

        mes_start, mes_end = self._parse_periodo(periodo)

        query = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.usuario_id.isnot(None),
                Asignacion.vig_desde <= mes_start,
                or_(
                    Asignacion.vig_hasta.is_(None),
                    Asignacion.vig_hasta >= mes_start,
                ),
            )
        )
        result = await self._db.execute(query)
        asignaciones = list(result.scalars().all())

        docentes = defaultdict(lambda: {"asignaciones": []})
        for a in asignaciones:
            docentes[a.usuario_id]["asignaciones"].append(a)

        usuarios = {}
        if docentes:
            user_ids = list(docentes.keys())
            user_query = select(Usuario).where(
                Usuario.id.in_(user_ids),
                Usuario.tenant_id == self._tenant_id,
                Usuario.deleted_at.is_(None),
            )
            res = await self._db.execute(user_query)
            for u in res.scalars().all():
                usuarios[u.id] = u

        liquidaciones = []
        docentes_excluidos = []

        for usuario_id, data in docentes.items():
            usuario = usuarios.get(usuario_id)
            if not usuario:
                docentes_excluidos.append({
                    "usuario_id": str(usuario_id),
                    "motivo": "usuario_no_encontrado",
                })
                continue

            if not usuario.cbu and not usuario.alias_cbu:
                docentes_excluidos.append({
                    "usuario_id": str(usuario_id),
                    "nombre": f"{usuario.nombre} {usuario.apellidos}",
                    "motivo": "datos_bancarios_incompletos",
                })
                continue

            a_roles = defaultdict(list)
            for a in data["asignaciones"]:
                a_roles[a.rol_id].append(a)

            rol_ids = list(a_roles.keys())
            if not rol_ids:
                continue

            roles_query = select(Rol).where(
                Rol.id.in_(rol_ids),
                Rol.tenant_id == self._tenant_id,
            )
            res = await self._db.execute(roles_query)
            roles_map = {r.id: r for r in res.scalars().all()}

            for rol_id, comisiones_asig in a_roles.items():
                rol = roles_map.get(rol_id)
                if not rol:
                    continue
                rol_nombre = rol.nombre
                es_nexo = rol_nombre == "NEXO"
                excluido = bool(usuario.facturador)

                salario_base = await self._salario_base_repo.get_active_for_period(
                    rol_nombre, mes_start
                )

                comision_nombres = []
                for a in comisiones_asig:
                    if a.comisiones:
                        comision_nombres.extend(a.comisiones.split(", "))

                if not salario_base and not es_nexo and not excluido:
                    docentes_excluidos.append({
                        "usuario_id": str(usuario_id),
                        "nombre": f"{usuario.nombre} {usuario.apellidos}",
                        "motivo": "sin_salario_base_vigente",
                    })
                    continue

                monto_base = salario_base.monto if salario_base else Decimal("0")
                monto_plus = Decimal("0")

                if not es_nexo and not excluido and salario_base:
                    materia_ids = set()
                    for a in comisiones_asig:
                        if a.materia_id:
                            materia_ids.add(a.materia_id)

                    if materia_ids:
                        mat_query = select(Materia.id, Materia.grupo_plus).where(
                            Materia.tenant_id == self._tenant_id,
                            Materia.id.in_(materia_ids),
                            Materia.grupo_plus.isnot(None),
                            Materia.deleted_at.is_(None),
                        )
                        mat_res = await self._db.execute(mat_query)
                        materia_grupo = {row.id: row.grupo_plus for row in mat_res.all()}

                        grupos_count = defaultdict(int)
                        for a in comisiones_asig:
                            if a.materia_id and a.materia_id in materia_grupo:
                                g = materia_grupo[a.materia_id]
                                if a.comisiones:
                                    grupos_count[g] += len(a.comisiones.split(", "))
                                else:
                                    grupos_count[g] += 1

                        for grupo, n_comisiones in grupos_count.items():
                            plus = await self._salario_plus_repo.get_active_for_period(
                                grupo, rol_nombre, mes_start
                            )
                            if plus:
                                monto_plus += plus.monto * n_comisiones

                total = monto_base + monto_plus

                liquidaciones.append({
                    "cohorte_id": cohorte_id,
                    "periodo": periodo,
                    "usuario_id": usuario_id,
                    "rol": rol_nombre,
                    "comisiones": ", ".join(comision_nombres) if comision_nombres else None,
                    "monto_base": monto_base,
                    "monto_plus": monto_plus,
                    "total": total,
                    "es_nexo": es_nexo,
                    "excluido_por_factura": excluido,
                    "estado": "Abierta",
                })

        await self._liq_repo.upsert_bulk(liquidaciones)
        return {
            "docentes_excluidos": docentes_excluidos,
            "count": len(liquidaciones),
        }

    async def cerrar_liquidacion(
        self, cohorte_id: uuid.UUID, periodo: str, actor_id: uuid.UUID
    ) -> list[Liquidacion]:
        existing = await self._liq_repo.get_by_cohorte_periodo(
            cohorte_id, periodo
        )
        if not existing:
            raise LiquidacionNotFoundError("No liquidaciones found for this period")
        if any(liq.estado == "Cerrada" for liq in existing):
            raise LiquidacionCerradaError("Liquidacion already closed")

        closed = await self._liq_repo.close_by_cohorte_periodo(
            cohorte_id, periodo
        )

        audit_entry = AuditLog(
            tenant_id=self._tenant_id,
            accion=AuditAction.LIQUIDACION_CERRAR.value,
            actor_id=actor_id,
            detalle={
                "cohorte_id": str(cohorte_id),
                "periodo": periodo,
                "filas_afectadas": len(closed),
            },
            filas_afectadas=len(closed),
        )
        self._db.add(audit_entry)
        await self._db.commit()

        return closed

    async def get_liquidacion_view(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> dict:
        rows = await self._liq_repo.get_by_cohorte_periodo_with_users(
            cohorte_id, periodo
        )

        liquidaciones = []
        total_general = Decimal("0")
        total_sin_factura = Decimal("0")
        total_nexo = Decimal("0")
        total_facturantes = 0

        for r in rows:
            liquidaciones.append(r)
            total_general += r["total"]
            if r["excluido_por_factura"]:
                total_facturantes += 1
            else:
                total_sin_factura += r["total"]
            if r["es_nexo"]:
                total_nexo += r["total"]

        return {
            "liquidaciones": liquidaciones,
            "kpis": {
                "total_general": total_general,
                "total_sin_factura": total_sin_factura,
                "total_nexo": total_nexo,
                "total_facturantes": total_facturantes,
                "total_docentes": len(liquidaciones),
            },
        }

    async def get_historial(
        self, cohorte_id: uuid.UUID
    ) -> list[dict]:
        liquidaciones = await self._liq_repo.get_history(cohorte_id)
        return [
            {
                "id": liq.id,
                "cohorte_id": liq.cohorte_id,
                "periodo": liq.periodo,
                "usuario_id": liq.usuario_id,
                "rol": liq.rol,
                "comisiones": liq.comisiones,
                "monto_base": liq.monto_base,
                "monto_plus": liq.monto_plus,
                "total": liq.total,
                "es_nexo": liq.es_nexo,
                "excluido_por_factura": liq.excluido_por_factura,
                "estado": liq.estado,
            }
            for liq in liquidaciones
        ]

    async def exportar_liquidacion(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> str:
        rows = await self._liq_repo.get_by_cohorte_periodo_with_users(
            cohorte_id, periodo
        )

        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow([
            "docente_nombre", "docente_apellidos", "rol", "periodo",
            "monto_base", "monto_plus", "total",
            "es_nexo", "excluido_por_factura", "estado",
        ])
        for r in rows:
            writer.writerow([
                r["docente_nombre"],
                r["docente_apellidos"],
                r["rol"],
                r["periodo"],
                str(r["monto_base"]),
                str(r["monto_plus"]),
                str(r["total"]),
                str(r["es_nexo"]),
                str(r["excluido_por_factura"]),
                r["estado"],
            ])

        return output.getvalue()
