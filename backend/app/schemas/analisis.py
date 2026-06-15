from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlumnoAtrasado(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    email: str | None = None
    comision: str | None = None
    motivo: str
    actividades_faltantes: list[str]
    actividades_reprobadas: list[str]


class AtrasadosResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    items: list[AlumnoAtrasado]
    total: int
    sin_datos: bool = False
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None


class RankingRow(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    posicion: int
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    aprobadas: int
    total_actividades: int
    porcentaje: Decimal


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    items: list[RankingRow]
    total_aprobados: int
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None


class NotaFinalRow(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    nota_promedio: Decimal | None = None
    actividades_aprobadas: int
    total_actividades: int
    estado: str


class NotasFinalesResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    items: list[NotaFinalRow]
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None


class ReporteMateria(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID | None = None
    cohorte_nombre: str = ""
    total_alumnos: int
    alumnos_con_nota: int
    alumnos_aprobados: int
    alumnos_atrasados: int
    pct_aprobados: Decimal
    pct_atrasados: Decimal
    actividades_count: int
    ultima_importacion: datetime | None = None
    sin_datos: bool = False


class TPSinCorregirRow(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    actividad: str
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    email: str | None = None
    comision: str | None = None


class MonitorGeneralRow(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID | None = None
    cohorte_nombre: str
    total_alumnos: int
    aprobados: int
    atrasados: int
    pct_aprobacion: Decimal


class MonitorSeguimientoRow(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    email: str | None = None
    comision: str | None = None
    actividades_aprobadas: int
    actividades_reprobadas: int
    actividades_faltantes: int
    nota_promedio: Decimal | None = None
    estado: str


class MonitorCoordinacionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID | None = None
    cohorte_nombre: str
    total_alumnos: int
    aprobados: int
    atrasados: int
    pct_aprobacion: Decimal
    period_desde: datetime | None = None
    period_hasta: datetime | None = None
