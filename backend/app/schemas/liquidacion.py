"""Pydantic v2 schemas for liquidaciones y honorarios — C-18."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ── SalarioBase ──────────────────────────────────────────────────────────────

class SalarioBaseCreate(BaseModel):
    rol: str = Field(min_length=1, max_length=30)
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(extra="forbid")


class SalarioBaseUpdate(BaseModel):
    rol: str | None = Field(default=None, min_length=1, max_length=30)
    monto: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    vig_desde: date | None = None
    vig_hasta: date | None = None
    model_config = ConfigDict(extra="forbid")


class SalarioBaseResponse(BaseModel):
    id: uuid.UUID
    rol: str
    monto: Decimal
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ── SalarioPlus ──────────────────────────────────────────────────────────────

class SalarioPlusCreate(BaseModel):
    grupo: str = Field(min_length=1, max_length=50)
    rol: str = Field(min_length=1, max_length=30)
    descripcion: str = Field(min_length=1, max_length=200)
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(extra="forbid")


class SalarioPlusUpdate(BaseModel):
    grupo: str | None = Field(default=None, min_length=1, max_length=50)
    rol: str | None = Field(default=None, min_length=1, max_length=30)
    descripcion: str | None = Field(default=None, min_length=1, max_length=200)
    monto: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    vig_desde: date | None = None
    vig_hasta: date | None = None
    model_config = ConfigDict(extra="forbid")


class SalarioPlusResponse(BaseModel):
    id: uuid.UUID
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ── GrupoMateria ─────────────────────────────────────────────────────────────

class GrupoMateriaCreate(BaseModel):
    grupo: str = Field(min_length=1, max_length=50)
    materia_id: uuid.UUID
    model_config = ConfigDict(extra="forbid")


class GrupoMateriaResponse(BaseModel):
    id: uuid.UUID
    grupo: str
    materia_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ── Liquidacion ──────────────────────────────────────────────────────────────

class CalcularLiquidacionRequest(BaseModel):
    cohorte_id: uuid.UUID
    periodo: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    model_config = ConfigDict(extra="forbid")


class CerrarLiquidacionRequest(BaseModel):
    cohorte_id: uuid.UUID
    periodo: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    model_config = ConfigDict(extra="forbid")


class LiquidacionResponse(BaseModel):
    id: uuid.UUID
    cohorte_id: uuid.UUID
    periodo: str
    usuario_id: uuid.UUID
    rol: str
    comisiones: str | None = None
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    docente_nombre: str | None = None
    docente_apellidos: str | None = None
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LiquidacionKPIs(BaseModel):
    total_general: Decimal
    total_sin_factura: Decimal
    total_nexo: Decimal
    total_facturantes: int
    total_docentes: int
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LiquidacionListResponse(BaseModel):
    liquidaciones: list[LiquidacionResponse]
    kpis: LiquidacionKPIs
    docentes_excluidos: list[dict] = []
    model_config = ConfigDict(extra="forbid")


class LiquidacionHistorialResponse(BaseModel):
    liquidaciones: list[LiquidacionResponse]
    model_config = ConfigDict(extra="forbid")


# ── Factura ──────────────────────────────────────────────────────────────────

class FacturaCreate(BaseModel):
    usuario_id: uuid.UUID
    cohorte_id: uuid.UUID | None = None
    periodo: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    detalle: str = Field(min_length=1)
    referencia_archivo: str | None = None
    tamano_kb: Decimal | None = None
    model_config = ConfigDict(extra="forbid")


class FacturaUpdate(BaseModel):
    detalle: str | None = Field(default=None, min_length=1)
    referencia_archivo: str | None = None
    tamano_kb: Decimal | None = None
    estado: str | None = None
    model_config = ConfigDict(extra="forbid")


class FacturaResponse(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    cohorte_id: uuid.UUID | None = None
    periodo: str
    detalle: str
    referencia_archivo: str | None = None
    tamano_kb: Decimal | None = None
    estado: str
    cargada_at: datetime
    abonada_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True, extra="forbid")
